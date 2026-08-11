from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.registration import Registration, RegistrationStatus
from app.repositories.credit_repository import (
    CreditRepositoryError,
    get_credit_load_validation,
)
from app.repositories.course_repository import (
    approved_enrollment_expression,
    course_to_response,
)
from app.repositories.prerequisite_repository import (
    PrerequisiteRepositoryError,
    PrerequisitesNotMetError,
    require_prerequisites_met,
)
from app.repositories.schedule_conflict_repository import (
    ScheduleConflictError,
    ScheduleConflictRepositoryError,
    require_no_schedule_conflict_for_course,
)
from app.schemas.credit import CreditLoadValidation
from app.schemas.selection import DraftSelection, DraftSelectionRemoved


class SelectionRepositoryError(RuntimeError):
    """Raised when draft selections cannot be persisted safely."""


class SectionNotFoundError(LookupError):
    """Raised when a public course-section identifier does not exist."""


class DuplicateSelectionError(ValueError):
    def __init__(self, registration_status: str):
        super().__init__("The course section already has a registration.")
        self.registration_status = registration_status


class SelectionNotDraftError(ValueError):
    def __init__(self, registration_status: str):
        super().__init__("Only draft selections can be removed.")
        self.registration_status = registration_status


def draft_selection_query(
    db: Session,
    *,
    student_id: UUID,
):
    enrollment = approved_enrollment_expression()

    return (
        db.query(
            Registration,
            Course,
            enrollment.label("approved_enrollment"),
        )
        .join(Course, Registration.section_id == Course.id)
        .filter(
            Registration.student_id == student_id,
            Registration.registration_status
            == RegistrationStatus.DRAFT.value,
        )
    )


def selection_to_response(
    registration: Registration,
    course: Course,
    *,
    enrollment: int,
) -> DraftSelection:
    return DraftSelection(
        registration_id=registration.id,
        registration_status=RegistrationStatus.DRAFT.value,
        course=course_to_response(
            course,
            enrollment=enrollment,
        ),
    )


def list_draft_selections(
    db: Session,
    *,
    student_id: UUID,
) -> list[DraftSelection]:
    try:
        rows = (
            draft_selection_query(db, student_id=student_id)
            .order_by(Course.code, Course.section, Registration.id)
            .all()
        )

        return [
            selection_to_response(
                registration,
                course,
                enrollment=int(approved_enrollment),
            )
            for registration, course, approved_enrollment in rows
        ]

    except Exception as error:
        raise SelectionRepositoryError(str(error)) from error


def _approved_enrollment(
    db: Session,
    *,
    section_id: int,
) -> int:
    return int(
        db.query(func.count(Registration.id))
        .filter(
            Registration.section_id == section_id,
            Registration.registration_status
            == RegistrationStatus.APPROVED.value,
        )
        .scalar()
        or 0
    )


def add_draft_selection(
    db: Session,
    *,
    student_id: UUID,
    course_id: str,
) -> tuple[DraftSelection, CreditLoadValidation]:
    try:
        course = (
            db.query(Course)
            .filter(Course.course_id == course_id)
            .one_or_none()
        )

        if course is None:
            raise SectionNotFoundError(course_id)

        existing = (
            db.query(Registration)
            .filter(
                Registration.student_id == student_id,
                Registration.section_id == course.id,
            )
            .one_or_none()
        )

        if existing is not None:
            raise DuplicateSelectionError(
                existing.registration_status
            )

        require_prerequisites_met(
            db,
            student_id=student_id,
            course_id=course.course_id,
        )
        require_no_schedule_conflict_for_course(
            db,
            student_id=student_id,
            candidate_course=course,
        )

        registration = Registration(
            student_id=student_id,
            section_id=course.id,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        db.add(registration)
        db.flush()

        response = selection_to_response(
            registration,
            course,
            enrollment=_approved_enrollment(
                db,
                section_id=course.id,
            ),
        )
        credit_validation = get_credit_load_validation(
            db,
            student_id=student_id,
        )
        db.commit()

        return response, credit_validation

    except (
        DuplicateSelectionError,
        PrerequisitesNotMetError,
        ScheduleConflictError,
        SectionNotFoundError,
    ):
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise
    except (
        CreditRepositoryError,
        PrerequisiteRepositoryError,
        ScheduleConflictRepositoryError,
    ) as error:
        db.rollback()
        raise SelectionRepositoryError(str(error)) from error
    except Exception as error:
        db.rollback()
        raise SelectionRepositoryError(str(error)) from error


def remove_draft_selection(
    db: Session,
    *,
    student_id: UUID,
    course_id: str,
) -> tuple[DraftSelectionRemoved, CreditLoadValidation]:
    try:
        row = (
            db.query(Registration, Course)
            .join(Course, Registration.section_id == Course.id)
            .filter(
                Registration.student_id == student_id,
                Course.course_id == course_id,
            )
            .one_or_none()
        )

        if row is None:
            raise SectionNotFoundError(course_id)

        registration, course = row

        if (
            registration.registration_status
            != RegistrationStatus.DRAFT.value
        ):
            raise SelectionNotDraftError(
                registration.registration_status
            )

        response = DraftSelectionRemoved(
            registration_id=registration.id,
            course_id=course.course_id,
        )
        db.delete(registration)
        db.flush()
        credit_validation = get_credit_load_validation(
            db,
            student_id=student_id,
        )
        db.commit()

        return response, credit_validation

    except (SectionNotFoundError, SelectionNotDraftError):
        db.rollback()
        raise
    except Exception as error:
        db.rollback()
        raise SelectionRepositoryError(str(error)) from error
