from collections import defaultdict
from contextlib import nullcontext
from datetime import datetime, timezone
from threading import RLock
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.completed_course import CompletionStatus, CompletedCourse
from app.models.course import Course
from app.models.registration import Registration, RegistrationStatus
from app.repositories.course_repository import course_to_response
from app.repositories.credit_repository import (
    CreditRepositoryError,
    InvalidCreditLoadError,
    require_valid_credit_load,
)
from app.repositories.prerequisite_repository import (
    PrerequisiteRepositoryError,
    PrerequisitesNotMetError,
    normalize_course_code,
    require_prerequisites_met,
)
from app.repositories.schedule_conflict_repository import (
    ScheduleConflictError,
    ScheduleConflictRepositoryError,
    require_no_schedule_conflicts,
)
from app.schemas.registration_submission import (
    CompletedCourseConflict,
    DuplicateCourseSelection,
    FinalRegistrationSubmission,
    FullSection,
    SubmissionCourse,
    SubmittedRegistration,
)


ACTIVE_SUBMISSION_STATUSES = (
    RegistrationStatus.DRAFT.value,
    RegistrationStatus.PENDING.value,
    RegistrationStatus.APPROVED.value,
)
_SQLITE_SUBMISSION_MUTEX = RLock()


class RegistrationSubmissionRepositoryError(RuntimeError):
    """Raised when a final submission cannot be persisted safely."""


class NoDraftSelectionsError(ValueError):
    """Raised when a student has no draft registrations to submit."""


class DuplicateCourseSelectionsError(ValueError):
    def __init__(self, duplicates: list[DuplicateCourseSelection]):
        super().__init__(
            "The active registration load contains duplicate courses."
        )
        self.duplicates = duplicates


class PreviouslyCompletedCoursesError(ValueError):
    def __init__(self, conflicts: list[CompletedCourseConflict]):
        super().__init__(
            "The draft selection contains a previously completed course."
        )
        self.conflicts = conflicts


class SubmissionSectionsFullError(ValueError):
    def __init__(self, sections: list[FullSection]):
        super().__init__(
            "One or more selected course sections have no available seats."
        )
        self.sections = sections


def locked_draft_sections_query(
    db: Session,
    *,
    student_id: UUID,
):
    """Lock selected sections in a deterministic order before validation."""

    return (
        db.query(Course)
        .join(Registration, Registration.section_id == Course.id)
        .filter(
            Registration.student_id == student_id,
            Registration.registration_status
            == RegistrationStatus.DRAFT.value,
        )
        .order_by(Course.id)
        .populate_existing()
        .with_for_update(of=Course)
    )


def locked_draft_registrations_query(
    db: Session,
    *,
    student_id: UUID,
):
    return (
        db.query(Registration)
        .filter(
            Registration.student_id == student_id,
            Registration.registration_status
            == RegistrationStatus.DRAFT.value,
        )
        .order_by(Registration.id)
        .populate_existing()
        .with_for_update(of=Registration)
    )


def _submission_guard(db: Session):
    if db.get_bind().dialect.name == "sqlite":
        return _SQLITE_SUBMISSION_MUTEX

    return nullcontext()


def _submission_course(
    registration: Registration,
    course: Course,
) -> SubmissionCourse:
    return SubmissionCourse(
        course_id=course.course_id,
        code=course.code,
        title=course.title,
        semester=course.semester,
        section=course.section,
        registration_status=registration.registration_status,
    )


def _active_registration_rows(
    db: Session,
    *,
    student_id: UUID,
) -> list[tuple[Registration, Course]]:
    return (
        db.query(Registration, Course)
        .join(Course, Registration.section_id == Course.id)
        .filter(
            Registration.student_id == student_id,
            Registration.registration_status.in_(
                ACTIVE_SUBMISSION_STATUSES
            ),
        )
        .order_by(
            Course.code,
            Course.semester,
            Course.section,
            Registration.id,
        )
        .all()
    )


def _require_no_duplicate_courses(
    rows: list[tuple[Registration, Course]],
) -> None:
    rows_by_code = defaultdict(list)

    for registration, course in rows:
        rows_by_code[normalize_course_code(course.code)].append(
            (registration, course)
        )

    duplicates = []

    for normalized_code, grouped_rows in rows_by_code.items():
        if len(grouped_rows) < 2:
            continue

        if not any(
            registration.registration_status
            == RegistrationStatus.DRAFT.value
            for registration, _ in grouped_rows
        ):
            continue

        duplicates.append(
            DuplicateCourseSelection(
                code=normalized_code,
                selections=[
                    _submission_course(registration, course)
                    for registration, course in grouped_rows
                ],
            )
        )

    if duplicates:
        raise DuplicateCourseSelectionsError(duplicates)


def _require_no_completed_courses(
    db: Session,
    *,
    student_id: UUID,
    draft_rows: list[tuple[Registration, Course]],
) -> None:
    selected_by_code = defaultdict(list)

    for registration, course in draft_rows:
        selected_by_code[normalize_course_code(course.code)].append(
            (registration, course)
        )

    completed_rows = (
        db.query(CompletedCourse)
        .options(joinedload(CompletedCourse.course))
        .filter(
            CompletedCourse.student_id == student_id,
            CompletedCourse.completion_status
            == CompletionStatus.COMPLETED.value,
            func.upper(func.trim(CompletedCourse.grade)) != "F",
        )
        .order_by(CompletedCourse.completed_at, CompletedCourse.id)
        .all()
    )
    conflicts = []

    for completed in completed_rows:
        completed_course = completed.course
        normalized_code = normalize_course_code(completed_course.code)

        for registration, selected_course in selected_by_code.get(
            normalized_code,
            [],
        ):
            conflicts.append(
                CompletedCourseConflict(
                    selected_course=_submission_course(
                        registration,
                        selected_course,
                    ),
                    completed_course_id=completed_course.course_id,
                    completed_code=completed_course.code,
                    completed_title=completed_course.title,
                    completed_semester=completed_course.semester,
                    grade=completed.grade,
                    completed_at=completed.completed_at,
                )
            )

    if conflicts:
        raise PreviouslyCompletedCoursesError(conflicts)


def _require_prerequisites_for_drafts(
    db: Session,
    *,
    student_id: UUID,
    courses: list[Course],
) -> None:
    for course in courses:
        require_prerequisites_met(
            db,
            student_id=student_id,
            course_id=course.course_id,
        )


def _approved_enrollment_by_section(
    db: Session,
    *,
    section_ids: list[int],
) -> dict[int, int]:
    if not section_ids:
        return {}

    rows = (
        db.query(
            Registration.section_id,
            func.count(Registration.id),
        )
        .filter(
            Registration.section_id.in_(section_ids),
            Registration.registration_status
            == RegistrationStatus.APPROVED.value,
        )
        .group_by(Registration.section_id)
        .all()
    )
    return {
        section_id: int(enrollment)
        for section_id, enrollment in rows
    }


def _require_available_sections(
    courses: list[Course],
    *,
    enrollment_by_section: dict[int, int],
) -> None:
    full_sections = []

    for course in courses:
        approved_enrollment = enrollment_by_section.get(course.id, 0)

        if approved_enrollment < course.capacity:
            continue

        full_sections.append(
            FullSection(
                course_id=course.course_id,
                code=course.code,
                title=course.title,
                semester=course.semester,
                section=course.section,
                capacity=course.capacity,
                approved_enrollment=approved_enrollment,
            )
        )

    if full_sections:
        raise SubmissionSectionsFullError(full_sections)


def _submit_final_registration(
    db: Session,
    *,
    student_id: UUID,
) -> FinalRegistrationSubmission:
    try:
        courses = locked_draft_sections_query(
            db,
            student_id=student_id,
        ).all()
        registrations = locked_draft_registrations_query(
            db,
            student_id=student_id,
        ).all()

        if not registrations:
            raise NoDraftSelectionsError(
                "There are no draft course selections to submit."
            )

        courses_by_id = {course.id: course for course in courses}

        if len(courses_by_id) != len(registrations) or any(
            registration.section_id not in courses_by_id
            for registration in registrations
        ):
            raise RegistrationSubmissionRepositoryError(
                "Draft registration sections changed during submission."
            )

        draft_rows = [
            (registration, courses_by_id[registration.section_id])
            for registration in registrations
        ]
        active_rows = _active_registration_rows(
            db,
            student_id=student_id,
        )

        _require_no_duplicate_courses(active_rows)
        _require_no_completed_courses(
            db,
            student_id=student_id,
            draft_rows=draft_rows,
        )
        _require_prerequisites_for_drafts(
            db,
            student_id=student_id,
            courses=courses,
        )
        credit_validation = require_valid_credit_load(
            db,
            student_id=student_id,
        )
        schedule_validation = require_no_schedule_conflicts(
            db,
            student_id=student_id,
        )
        enrollment_by_section = _approved_enrollment_by_section(
            db,
            section_ids=[course.id for course in courses],
        )
        _require_available_sections(
            courses,
            enrollment_by_section=enrollment_by_section,
        )

        submitted_at = datetime.now(timezone.utc)

        for registration in registrations:
            registration.registration_status = (
                RegistrationStatus.PENDING.value
            )
            registration.submitted_at = submitted_at

        db.flush()

        submitted_registrations = [
            SubmittedRegistration(
                registration_id=registration.id,
                registration_status=RegistrationStatus.PENDING.value,
                submitted_at=submitted_at,
                course=course_to_response(
                    courses_by_id[registration.section_id],
                    enrollment=enrollment_by_section.get(
                        registration.section_id,
                        0,
                    ),
                ),
            )
            for registration in sorted(
                registrations,
                key=lambda item: (
                    normalize_course_code(
                        courses_by_id[item.section_id].code
                    ),
                    courses_by_id[item.section_id].section,
                    str(item.id),
                ),
            )
        ]
        result = FinalRegistrationSubmission(
            registration_status=RegistrationStatus.PENDING.value,
            submitted_count=len(submitted_registrations),
            submitted_at=submitted_at,
            registrations=submitted_registrations,
            credit_validation=credit_validation,
            schedule_validation=schedule_validation,
            message=(
                "The final registration was submitted for advisor review."
            ),
        )
        db.commit()
        return result

    except (
        DuplicateCourseSelectionsError,
        InvalidCreditLoadError,
        NoDraftSelectionsError,
        PrerequisitesNotMetError,
        PreviouslyCompletedCoursesError,
        ScheduleConflictError,
        SubmissionSectionsFullError,
    ):
        db.rollback()
        raise
    except RegistrationSubmissionRepositoryError:
        db.rollback()
        raise
    except (
        CreditRepositoryError,
        PrerequisiteRepositoryError,
        ScheduleConflictRepositoryError,
    ) as error:
        db.rollback()
        raise RegistrationSubmissionRepositoryError(str(error)) from error
    except Exception as error:
        db.rollback()
        raise RegistrationSubmissionRepositoryError(str(error)) from error


def submit_final_registration(
    db: Session,
    *,
    student_id: UUID,
) -> FinalRegistrationSubmission:
    """Validate and atomically move every current draft to pending."""

    with _submission_guard(db):
        return _submit_final_registration(
            db,
            student_id=student_id,
        )
