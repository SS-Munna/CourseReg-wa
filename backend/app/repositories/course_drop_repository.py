from datetime import date, datetime, timezone
import json
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.course import Course
from app.models.notification import Notification
from app.models.registration import Registration, RegistrationStatus
from app.repositories.course_repository import course_to_response
from app.repositories.registration_period_repository import (
    current_drop_period_for_semester,
)
from app.repositories.section_transaction import section_transaction_guard
from app.repositories.waitlist_promotion_repository import (
    WaitlistPromotionRepositoryError,
    promote_next_waitlisted_student_in_locked_section,
)
from app.schemas.registration_status import CourseDropResult


class CourseDropRepositoryError(RuntimeError):
    """Raised when a course drop cannot be persisted safely."""


class DroppableRegistrationNotFoundError(LookupError):
    """Raised for both missing and non-owned registration identifiers."""


class RegistrationNotDroppableError(ValueError):
    def __init__(self, registration_status: str):
        super().__init__("Only an approved registration can be dropped.")
        self.registration_status = registration_status


class DropPeriodNotConfiguredError(ValueError):
    def __init__(self, semester: str):
        super().__init__("No opened drop period is configured for the term.")
        self.semester = semester


class DropDeadlinePassedError(ValueError):
    def __init__(self, *, drop_deadline: date, current_date: date):
        super().__init__("The configured course-drop deadline has passed.")
        self.drop_deadline = drop_deadline
        self.current_date = current_date


def locked_drop_section_query(
    db: Session,
    *,
    registration_id: UUID,
    student_id: UUID,
):
    """Lock an owned registration's section before its registration row."""

    return (
        db.query(Course)
        .join(Registration, Registration.section_id == Course.id)
        .filter(
            Registration.id == registration_id,
            Registration.student_id == student_id,
        )
        .populate_existing()
        .with_for_update(of=Course)
    )


def locked_owned_registration_query(
    db: Session,
    *,
    registration_id: UUID,
    student_id: UUID,
):
    return (
        db.query(Registration)
        .filter(
            Registration.id == registration_id,
            Registration.student_id == student_id,
        )
        .populate_existing()
        .with_for_update(of=Registration)
    )


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


def _drop_notification(*, actor_user_id: UUID, course: Course) -> Notification:
    return Notification(
        user_id=actor_user_id,
        notification_type="course_drop",
        title="Course dropped",
        message=(
            f"{course.code}, Section {course.section} was dropped from "
            "your active registration."
        ),
    )


def _drop_audit_log(
    *,
    actor_user_id: UUID,
    registration: Registration,
    course: Course,
    dropped_at: datetime,
    drop_deadline: date,
) -> AuditLog:
    details = {
        "course_id": course.course_id,
        "drop_deadline": drop_deadline.isoformat(),
        "dropped_at": dropped_at.isoformat(),
        "new_registration_status": RegistrationStatus.DROPPED.value,
        "previous_registration_status": RegistrationStatus.APPROVED.value,
        "registration_id": str(registration.id),
        "section": course.section,
        "student_id": str(registration.student_id),
    }
    return AuditLog(
        user_id=actor_user_id,
        action_type="student_course_drop",
        entity_type="registration",
        entity_id=registration.id,
        action_details=json.dumps(details, sort_keys=True),
    )


def _drop_approved_registration(
    db: Session,
    *,
    registration_id: UUID,
    student_id: UUID,
    actor_user_id: UUID,
) -> CourseDropResult:
    try:
        course = locked_drop_section_query(
            db,
            registration_id=registration_id,
            student_id=student_id,
        ).one_or_none()

        if course is None:
            raise DroppableRegistrationNotFoundError(registration_id)

        registration = locked_owned_registration_query(
            db,
            registration_id=registration_id,
            student_id=student_id,
        ).one_or_none()

        if registration is None or registration.section_id != course.id:
            raise DroppableRegistrationNotFoundError(registration_id)

        if (
            registration.registration_status
            != RegistrationStatus.APPROVED.value
        ):
            raise RegistrationNotDroppableError(
                registration.registration_status
            )

        dropped_at = datetime.now(timezone.utc)
        period = current_drop_period_for_semester(
            db,
            semester_label=course.semester,
            current_time=dropped_at,
        )

        if period is None:
            raise DropPeriodNotConfiguredError(course.semester)

        current_date = dropped_at.date()

        if current_date > period.drop_deadline:
            raise DropDeadlinePassedError(
                drop_deadline=period.drop_deadline,
                current_date=current_date,
            )

        registration.registration_status = RegistrationStatus.DROPPED.value
        notification = _drop_notification(
            actor_user_id=actor_user_id,
            course=course,
        )
        audit_log = _drop_audit_log(
            actor_user_id=actor_user_id,
            registration=registration,
            course=course,
            dropped_at=dropped_at,
            drop_deadline=period.drop_deadline,
        )
        db.add_all([notification, audit_log])
        db.flush()

        promotion = promote_next_waitlisted_student_in_locked_section(
            db,
            course=course,
        )
        approved_enrollment = _approved_enrollment(
            db,
            section_id=course.id,
        )
        result = CourseDropResult(
            registration_id=registration.id,
            student_id=student_id,
            registration_status=RegistrationStatus.DROPPED.value,
            dropped_at=dropped_at,
            drop_deadline=period.drop_deadline,
            course=course_to_response(
                course,
                enrollment=approved_enrollment,
            ),
            notification_id=notification.id,
            audit_log_id=audit_log.id,
            waitlist_promotion=promotion,
            message=(
                f"{course.code}, Section {course.section} was dropped "
                "successfully."
            ),
        )
        db.commit()
        return result

    except (
        DroppableRegistrationNotFoundError,
        RegistrationNotDroppableError,
        DropPeriodNotConfiguredError,
        DropDeadlinePassedError,
    ):
        db.rollback()
        raise
    except CourseDropRepositoryError:
        db.rollback()
        raise
    except WaitlistPromotionRepositoryError as error:
        db.rollback()
        raise CourseDropRepositoryError(str(error)) from error
    except Exception as error:
        db.rollback()
        raise CourseDropRepositoryError(str(error)) from error


def drop_approved_registration(
    db: Session,
    *,
    registration_id: UUID,
    student_id: UUID,
    actor_user_id: UUID,
) -> CourseDropResult:
    """Atomically drop one owned approval and process its released seat."""

    with section_transaction_guard(db):
        return _drop_approved_registration(
            db,
            registration_id=registration_id,
            student_id=student_id,
            actor_user_id=actor_user_id,
        )
