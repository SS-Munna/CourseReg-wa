from collections import defaultdict
from datetime import datetime, timezone
import json
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.advisor import Advisor
from app.models.audit_log import AuditLog
from app.models.course import Course
from app.models.notification import Notification
from app.models.program import Program
from app.models.registration import Registration, RegistrationStatus
from app.models.student import Student
from app.models.user import User
from app.repositories.course_repository import course_to_response
from app.repositories.credit_repository import build_credit_load_validation
from app.repositories.prerequisite_repository import (
    PrerequisiteRepositoryError,
    get_prerequisite_validation,
    normalize_course_code,
)
from app.repositories.schedule_conflict_repository import (
    ScheduleConflictRepositoryError,
    get_schedule_conflict_validation,
)
from app.repositories.seat_allocation_repository import (
    SeatAllocationRepositoryError,
    approve_pending_registration_in_locked_section,
)
from app.repositories.section_transaction import section_transaction_guard
from app.repositories.waitlist_repository import (
    WaitlistRepositoryError,
    list_active_waitlist_entries,
)
from app.schemas.advisor_review import (
    AdvisorRegistrationRequestDetails,
    AdvisorRegistrationRequestSummary,
    AdvisorReviewCourseDetails,
    AdvisorReviewCourseSummary,
    AdvisorReviewDecisionResult,
    AdvisorReviewStudent,
)
from app.schemas.common import PaginationMeta
from app.schemas.registration_submission import FullSection


REVIEWABLE_STATUSES = (
    RegistrationStatus.PENDING.value,
    RegistrationStatus.APPROVED.value,
    RegistrationStatus.REJECTED.value,
)


class AdvisorReviewRepositoryError(RuntimeError):
    """Raised when advisor-review data cannot be handled safely."""


class AdvisorRequestNotFoundError(LookupError):
    """Raised when an assigned advisor cannot access a request."""


class AdvisorRequestAlreadyReviewedError(ValueError):
    def __init__(self, request_status: str):
        super().__init__("Only a pending registration request can be reviewed.")
        self.request_status = request_status


class AdvisorReviewSectionsFullError(ValueError):
    def __init__(self, sections: list[FullSection]):
        super().__init__("One or more requested sections are full.")
        self.sections = sections


def locked_advisor_request_sections_query(
    db: Session,
    *,
    student_id: UUID,
    submitted_at: datetime,
):
    """Lock every request section in deterministic order."""

    return (
        db.query(Course)
        .join(Registration, Registration.section_id == Course.id)
        .filter(
            Registration.student_id == student_id,
            Registration.submitted_at == submitted_at,
            Registration.registration_status.in_(REVIEWABLE_STATUSES),
        )
        .order_by(Course.id)
        .populate_existing()
        .with_for_update(of=Course)
    )


def locked_advisor_request_registrations_query(
    db: Session,
    *,
    student_id: UUID,
    submitted_at: datetime,
):
    """Lock every row in one submitted registration request."""

    return (
        db.query(Registration)
        .filter(
            Registration.student_id == student_id,
            Registration.submitted_at == submitted_at,
            Registration.registration_status.in_(REVIEWABLE_STATUSES),
        )
        .order_by(Registration.id)
        .populate_existing()
        .with_for_update(of=Registration)
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _request_id(registrations: list[Registration]) -> UUID:
    return min(
        (registration.id for registration in registrations),
        key=str,
    )


def _request_status(registrations: list[Registration]) -> str:
    statuses = {
        registration.registration_status
        for registration in registrations
    }

    if len(statuses) != 1:
        raise AdvisorReviewRepositoryError(
            "A registration request contains inconsistent statuses."
        )

    request_status = statuses.pop()

    if request_status not in REVIEWABLE_STATUSES:
        raise AdvisorReviewRepositoryError(
            "A registration request contains an unsupported status."
        )

    return request_status


def _student_response(
    student: Student,
    user: User,
    program: Program,
) -> AdvisorReviewStudent:
    return AdvisorReviewStudent(
        student_id=student.id,
        student_number=student.student_number,
        full_name=user.full_name,
        email=user.email,
        program_code=program.program_code,
        program_name=program.program_name,
        current_trimester=student.current_trimester,
        academic_status=student.academic_status,
    )


def _request_rows_query(
    db: Session,
    *,
    advisor_id: UUID,
):
    return (
        db.query(Registration, Course, Student, User, Program)
        .join(Course, Registration.section_id == Course.id)
        .join(Student, Registration.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .join(Program, Student.program_id == Program.id)
        .filter(
            Student.advisor_id == advisor_id,
            Registration.submitted_at.isnot(None),
            Registration.registration_status.in_(REVIEWABLE_STATUSES),
        )
    )


def _group_rows(rows):
    grouped = defaultdict(list)

    for row in rows:
        registration = row[0]
        grouped[(registration.student_id, registration.submitted_at)].append(
            row
        )

    return grouped


def _summary_from_rows(rows) -> AdvisorRegistrationRequestSummary:
    ordered_rows = sorted(
        rows,
        key=lambda row: (
            normalize_course_code(row[1].code),
            row[1].section,
            str(row[0].id),
        ),
    )
    registrations = [row[0] for row in ordered_rows]
    first_registration, _, student, user, program = ordered_rows[0]
    courses = [
        AdvisorReviewCourseSummary(
            registration_id=registration.id,
            course_id=course.course_id,
            code=course.code,
            title=course.title,
            semester=course.semester,
            section=course.section,
            credits=course.credits,
        )
        for registration, course, _, _, _ in ordered_rows
    ]

    return AdvisorRegistrationRequestSummary(
        request_id=_request_id(registrations),
        request_status=_request_status(registrations),
        submitted_at=_as_utc(first_registration.submitted_at),
        reviewed_at=(
            _as_utc(first_registration.reviewed_at)
            if first_registration.reviewed_at is not None
            else None
        ),
        advisor_comment=first_registration.advisor_comment,
        student=_student_response(student, user, program),
        course_count=len(courses),
        total_credits=sum(course.credits for course in courses),
        courses=courses,
    )


def list_advisor_registration_requests(
    db: Session,
    *,
    advisor_id: UUID,
    request_status: str,
    page: int,
    page_size: int,
) -> tuple[list[AdvisorRegistrationRequestSummary], PaginationMeta]:
    try:
        query = _request_rows_query(db, advisor_id=advisor_id)

        if request_status != "all":
            query = query.filter(
                Registration.registration_status == request_status
            )

        grouped_rows = _group_rows(
            query.order_by(
                Registration.submitted_at.desc(),
                Student.student_number,
                Course.code,
                Course.section,
                Registration.id,
            ).all()
        )
        summaries = [
            _summary_from_rows(rows)
            for rows in grouped_rows.values()
        ]
        summaries.sort(
            key=lambda item: (
                item.submitted_at,
                str(item.request_id),
            ),
            reverse=True,
        )
        pagination = PaginationMeta.from_total(
            page=page,
            page_size=page_size,
            total_items=len(summaries),
        )
        start = (page - 1) * page_size
        return summaries[start : start + page_size], pagination

    except AdvisorReviewRepositoryError:
        raise
    except Exception as error:
        raise AdvisorReviewRepositoryError(str(error)) from error


def _request_anchor(
    db: Session,
    *,
    advisor_id: UUID,
    request_id: UUID,
) -> tuple[Registration, Student] | None:
    return (
        db.query(Registration, Student)
        .join(Student, Registration.student_id == Student.id)
        .filter(
            Registration.id == request_id,
            Registration.submitted_at.isnot(None),
            Registration.registration_status.in_(REVIEWABLE_STATUSES),
            Student.advisor_id == advisor_id,
        )
        .one_or_none()
    )


def _request_rows_for_anchor(
    db: Session,
    *,
    advisor_id: UUID,
    anchor: Registration,
):
    return (
        _request_rows_query(db, advisor_id=advisor_id)
        .filter(
            Registration.student_id == anchor.student_id,
            Registration.submitted_at == anchor.submitted_at,
        )
        .order_by(Course.code, Course.section, Registration.id)
        .all()
    )


def _approved_enrollment_by_section(
    db: Session,
    *,
    section_ids: list[int],
) -> dict[int, int]:
    if not section_ids:
        return {}

    rows = (
        db.query(Registration.section_id, func.count(Registration.id))
        .filter(
            Registration.section_id.in_(section_ids),
            Registration.registration_status
            == RegistrationStatus.APPROVED.value,
        )
        .group_by(Registration.section_id)
        .all()
    )
    return {
        section_id: int(approved_enrollment)
        for section_id, approved_enrollment in rows
    }


def get_advisor_registration_request(
    db: Session,
    *,
    advisor_id: UUID,
    request_id: UUID,
) -> AdvisorRegistrationRequestDetails:
    try:
        anchor_row = _request_anchor(
            db,
            advisor_id=advisor_id,
            request_id=request_id,
        )

        if anchor_row is None:
            raise AdvisorRequestNotFoundError(request_id)

        anchor, _ = anchor_row
        rows = _request_rows_for_anchor(
            db,
            advisor_id=advisor_id,
            anchor=anchor,
        )

        if not rows:
            raise AdvisorRequestNotFoundError(request_id)

        summary = _summary_from_rows(rows)
        registrations = [row[0] for row in rows]
        courses = [row[1] for row in rows]
        student = rows[0][2]
        program = rows[0][4]
        enrollment_by_section = _approved_enrollment_by_section(
            db,
            section_ids=[course.id for course in courses],
        )
        course_details = []

        for registration, course, _, _, _ in rows:
            prerequisite_validation = get_prerequisite_validation(
                db,
                student_id=student.id,
                course_id=course.course_id,
            )

            if prerequisite_validation is None:
                raise AdvisorReviewRepositoryError(
                    "A request course could not be validated."
                )

            course_details.append(
                AdvisorReviewCourseDetails(
                    registration_id=registration.id,
                    registration_status=registration.registration_status,
                    course=course_to_response(
                        course,
                        enrollment=enrollment_by_section.get(course.id, 0),
                    ),
                    prerequisite_validation=prerequisite_validation,
                )
            )

        return AdvisorRegistrationRequestDetails(
            **summary.model_dump(exclude={"courses"}),
            reviewed_by_advisor_id=registrations[0].reviewed_by,
            courses=course_details,
            credit_validation=build_credit_load_validation(
                selected_credits=summary.total_credits,
                minimum_credit=program.minimum_credit,
                maximum_credit=program.maximum_credit,
            ),
            schedule_validation=get_schedule_conflict_validation(
                db,
                student_id=student.id,
            ),
            waitlist_entries=list_active_waitlist_entries(
                db,
                student_id=student.id,
            ),
        )

    except (AdvisorRequestNotFoundError, AdvisorReviewRepositoryError):
        raise
    except (
        PrerequisiteRepositoryError,
        ScheduleConflictRepositoryError,
        WaitlistRepositoryError,
    ) as error:
        raise AdvisorReviewRepositoryError(str(error)) from error
    except Exception as error:
        raise AdvisorReviewRepositoryError(str(error)) from error


def _full_sections(
    courses: list[Course],
    *,
    enrollment_by_section: dict[int, int],
) -> list[FullSection]:
    return [
        FullSection(
            course_id=course.course_id,
            code=course.code,
            title=course.title,
            semester=course.semester,
            section=course.section,
            capacity=course.capacity,
            approved_enrollment=enrollment_by_section.get(course.id, 0),
        )
        for course in courses
        if enrollment_by_section.get(course.id, 0) >= course.capacity
    ]


def _decision_notification(
    *,
    student: Student,
    decision: str,
    course_count: int,
    comment: str | None,
) -> Notification:
    decision_label = "approved" if decision == "approved" else "rejected"
    message = (
        f"Your registration request for {course_count} course"
        f"{'s' if course_count != 1 else ''} was {decision_label}."
    )

    if decision == "rejected" and comment:
        message = f"{message} Reason: {comment}"

    return Notification(
        user_id=student.user_id,
        notification_type=f"registration_{decision_label}",
        title=f"Registration request {decision_label}",
        message=message,
    )


def _decision_audit_log(
    *,
    actor_user_id: UUID,
    advisor: Advisor,
    request_id: UUID,
    registrations: list[Registration],
    courses_by_id: dict[int, Course],
    decision: str,
    comment: str | None,
) -> AuditLog:
    details = {
        "advisor_id": str(advisor.id),
        "comment": comment,
        "decision": decision,
        "registration_ids": [
            str(registration.id) for registration in registrations
        ],
        "request_id": str(request_id),
        "student_id": str(registrations[0].student_id),
        "course_ids": [
            courses_by_id[registration.section_id].course_id
            for registration in registrations
        ],
    }
    return AuditLog(
        user_id=actor_user_id,
        action_type=f"advisor_registration_{decision}",
        entity_type="registration_request",
        entity_id=request_id,
        action_details=json.dumps(details, sort_keys=True),
    )


def _review_advisor_registration_request(
    db: Session,
    *,
    advisor: Advisor,
    actor_user_id: UUID,
    request_id: UUID,
    decision: str,
    comment: str | None,
) -> AdvisorReviewDecisionResult:
    try:
        anchor_row = _request_anchor(
            db,
            advisor_id=advisor.id,
            request_id=request_id,
        )

        if anchor_row is None:
            raise AdvisorRequestNotFoundError(request_id)

        anchor, student = anchor_row
        courses = locked_advisor_request_sections_query(
            db,
            student_id=anchor.student_id,
            submitted_at=anchor.submitted_at,
        ).all()
        registrations = locked_advisor_request_registrations_query(
            db,
            student_id=anchor.student_id,
            submitted_at=anchor.submitted_at,
        ).all()

        assigned_student = (
            db.query(Student)
            .filter(
                Student.id == anchor.student_id,
                Student.advisor_id == advisor.id,
            )
            .populate_existing()
            .one_or_none()
        )

        if assigned_student is None or not registrations:
            raise AdvisorRequestNotFoundError(request_id)

        request_status = _request_status(registrations)

        if request_status != RegistrationStatus.PENDING.value:
            raise AdvisorRequestAlreadyReviewedError(request_status)

        courses_by_id = {course.id: course for course in courses}

        if len(courses_by_id) != len(registrations) or any(
            registration.section_id not in courses_by_id
            for registration in registrations
        ):
            raise AdvisorReviewRepositoryError(
                "Registration request sections changed during review."
            )

        enrollment_by_section = _approved_enrollment_by_section(
            db,
            section_ids=list(courses_by_id),
        )

        if decision == RegistrationStatus.APPROVED.value:
            full_sections = _full_sections(
                courses,
                enrollment_by_section=enrollment_by_section,
            )

            if full_sections:
                raise AdvisorReviewSectionsFullError(full_sections)

            for registration in registrations:
                course = courses_by_id[registration.section_id]
                approve_pending_registration_in_locked_section(
                    registration=registration,
                    course=course,
                    approved_enrollment=enrollment_by_section.get(
                        course.id,
                        0,
                    ),
                )
        else:
            for registration in registrations:
                registration.registration_status = (
                    RegistrationStatus.REJECTED.value
                )

        reviewed_at = datetime.now(timezone.utc)

        for registration in registrations:
            registration.reviewed_by = advisor.id
            registration.reviewed_at = reviewed_at
            registration.advisor_comment = comment

        canonical_request_id = _request_id(registrations)
        notification = _decision_notification(
            student=student,
            decision=decision,
            course_count=len(registrations),
            comment=comment,
        )
        audit_log = _decision_audit_log(
            actor_user_id=actor_user_id,
            advisor=advisor,
            request_id=canonical_request_id,
            registrations=registrations,
            courses_by_id=courses_by_id,
            decision=decision,
            comment=comment,
        )
        db.add_all([notification, audit_log])
        db.flush()
        result = AdvisorReviewDecisionResult(
            request_id=canonical_request_id,
            request_status=decision,
            registration_ids=[
                registration.id for registration in registrations
            ],
            reviewed_at=reviewed_at,
            reviewed_by_advisor_id=advisor.id,
            advisor_comment=comment,
            notification_id=notification.id,
            audit_log_id=audit_log.id,
            message=(
                "The registration request was approved."
                if decision == RegistrationStatus.APPROVED.value
                else "The registration request was rejected."
            ),
        )
        db.commit()
        return result

    except (
        AdvisorRequestAlreadyReviewedError,
        AdvisorRequestNotFoundError,
        AdvisorReviewSectionsFullError,
    ):
        db.rollback()
        raise
    except AdvisorReviewRepositoryError:
        db.rollback()
        raise
    except SeatAllocationRepositoryError as error:
        db.rollback()
        raise AdvisorReviewRepositoryError(str(error)) from error
    except Exception as error:
        db.rollback()
        raise AdvisorReviewRepositoryError(str(error)) from error


def review_advisor_registration_request(
    db: Session,
    *,
    advisor: Advisor,
    actor_user_id: UUID,
    request_id: UUID,
    decision: str,
    comment: str | None,
) -> AdvisorReviewDecisionResult:
    """Atomically approve or reject one assigned student's request."""

    with section_transaction_guard(db):
        return _review_advisor_registration_request(
            db,
            advisor=advisor,
            actor_user_id=actor_user_id,
            request_id=request_id,
            decision=decision,
            comment=comment,
        )
