import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.completed_course import CompletionStatus, CompletedCourse
from app.models.course import Course
from app.models.notification import Notification
from app.models.program import Program
from app.models.registration import Registration, RegistrationStatus
from app.models.student import Student
from app.models.waitlist_entry import WaitlistEntry, WaitlistStatus
from app.repositories.credit_repository import selected_credit_total_query
from app.repositories.prerequisite_repository import (
    PrerequisiteRepositoryError,
    PrerequisitesNotMetError,
    normalize_course_code,
    require_prerequisites_met,
)
from app.repositories.schedule_conflict_repository import (
    ScheduleConflictError,
    ScheduleConflictRepositoryError,
    require_no_schedule_conflict_for_course,
)
from app.repositories.seat_allocation_repository import (
    SeatAllocationRepositoryError,
    approve_pending_registration_in_locked_section,
)
from app.repositories.section_transaction import section_transaction_guard
from app.schemas.waitlist_promotion import WaitlistPromotionResult


ACTIVE_REGISTRATION_STATUSES = (
    RegistrationStatus.DRAFT.value,
    RegistrationStatus.PENDING.value,
    RegistrationStatus.APPROVED.value,
)


class WaitlistPromotionRepositoryError(RuntimeError):
    """Raised when a promotion transaction cannot be completed safely."""


class PromotionSectionNotFoundError(LookupError):
    """Raised when the requested public section identifier does not exist."""


def locked_promotion_section_query(
    db: Session,
    *,
    course_id: str,
):
    """Lock the section before recounting enrollment or changing its queue."""

    return (
        db.query(Course)
        .filter(Course.course_id == course_id)
        .populate_existing()
        .with_for_update(of=Course)
    )


def locked_active_waitlist_query(
    db: Session,
    *,
    section_id: int,
):
    """Lock active candidates in deterministic first-come order."""

    return (
        db.query(WaitlistEntry, Student)
        .join(Student, WaitlistEntry.student_id == Student.id)
        .filter(
            WaitlistEntry.section_id == section_id,
            WaitlistEntry.waitlist_status == WaitlistStatus.ACTIVE.value,
        )
        .order_by(
            WaitlistEntry.joined_at.asc(),
            WaitlistEntry.id.asc(),
        )
        .populate_existing()
        .with_for_update(of=WaitlistEntry)
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


def _has_any_registration_for_section(
    db: Session,
    *,
    student_id: UUID,
    section_id: int,
) -> bool:
    return (
        db.query(Registration.id)
        .filter(
            Registration.student_id == student_id,
            Registration.section_id == section_id,
        )
        .first()
        is not None
    )


def _has_active_equivalent_course(
    db: Session,
    *,
    student_id: UUID,
    course_code: str,
) -> bool:
    normalized_code = normalize_course_code(course_code)
    rows = (
        db.query(Course.code)
        .join(Registration, Registration.section_id == Course.id)
        .filter(
            Registration.student_id == student_id,
            Registration.registration_status.in_(
                ACTIVE_REGISTRATION_STATUSES
            ),
        )
        .all()
    )
    return any(
        normalize_course_code(row.code) == normalized_code for row in rows
    )


def _has_completed_equivalent_course(
    db: Session,
    *,
    student_id: UUID,
    course_code: str,
) -> bool:
    normalized_code = normalize_course_code(course_code)
    rows = (
        db.query(Course.code)
        .join(CompletedCourse, CompletedCourse.course_id == Course.id)
        .filter(
            CompletedCourse.student_id == student_id,
            CompletedCourse.completion_status
            == CompletionStatus.COMPLETED.value,
            func.upper(func.trim(CompletedCourse.grade)) != "F",
        )
        .all()
    )
    return any(
        normalize_course_code(row.code) == normalized_code for row in rows
    )


def _fits_program_maximum(
    db: Session,
    *,
    student_id: UUID,
    added_credits: int,
) -> bool:
    maximum_credit = (
        db.query(Program.maximum_credit)
        .select_from(Student)
        .join(Program, Student.program_id == Program.id)
        .filter(Student.id == student_id)
        .scalar()
    )

    if maximum_credit is None:
        raise WaitlistPromotionRepositoryError(
            "The student program credit limit is unavailable."
        )

    selected_credits = int(
        selected_credit_total_query(
            db,
            student_id=student_id,
        ).scalar()
        or 0
    )
    return selected_credits + added_credits <= int(maximum_credit)


def _candidate_is_eligible(
    db: Session,
    *,
    student: Student,
    course: Course,
) -> bool:
    if _has_any_registration_for_section(
        db,
        student_id=student.id,
        section_id=course.id,
    ):
        return False

    if _has_active_equivalent_course(
        db,
        student_id=student.id,
        course_code=course.code,
    ):
        return False

    if _has_completed_equivalent_course(
        db,
        student_id=student.id,
        course_code=course.code,
    ):
        return False

    if not _fits_program_maximum(
        db,
        student_id=student.id,
        added_credits=course.credits,
    ):
        return False

    try:
        require_prerequisites_met(
            db,
            student_id=student.id,
            course_id=course.course_id,
        )
        require_no_schedule_conflict_for_course(
            db,
            student_id=student.id,
            candidate_course=course,
        )
    except (PrerequisitesNotMetError, ScheduleConflictError):
        return False

    return True


def _base_result(
    course: Course,
    *,
    outcome: str,
    approved_enrollment: int,
    expired_entry_ids: list[UUID],
) -> WaitlistPromotionResult:
    return WaitlistPromotionResult(
        course_id=course.course_id,
        code=course.code,
        section=course.section,
        promoted=False,
        outcome=outcome,
        capacity=course.capacity,
        approved_enrollment=approved_enrollment,
        available_seats=max(
            course.capacity - approved_enrollment,
            0,
        ),
        expired_waitlist_entry_ids=expired_entry_ids,
    )


def _promotion_notification(
    *,
    student: Student,
    course: Course,
) -> Notification:
    return Notification(
        user_id=student.user_id,
        notification_type="waitlist_promotion",
        title="Waiting-list seat confirmed",
        message=(
            f"A seat became available in {course.code}, Section "
            f"{course.section}. Your registration is now approved."
        ),
    )


def _promotion_audit_log(
    *,
    student: Student,
    course: Course,
    entry: WaitlistEntry,
    registration: Registration,
) -> AuditLog:
    details = {
        "course_id": course.course_id,
        "registration_id": str(registration.id),
        "registration_status": RegistrationStatus.APPROVED.value,
        "section": course.section,
        "student_id": str(student.id),
        "waitlist_entry_id": str(entry.id),
        "waitlist_status": WaitlistStatus.PROMOTED.value,
    }
    return AuditLog(
        user_id=student.user_id,
        action_type="automatic_waitlist_promotion",
        entity_type="waitlist_entry",
        entity_id=entry.id,
        action_details=json.dumps(details, sort_keys=True),
    )


def _promote_next_waitlisted_student(
    db: Session,
    *,
    course_id: str,
) -> WaitlistPromotionResult:
    try:
        course = locked_promotion_section_query(
            db,
            course_id=course_id,
        ).one_or_none()

        if course is None:
            raise PromotionSectionNotFoundError(course_id)

        approved_enrollment = _approved_enrollment(
            db,
            section_id=course.id,
        )

        if approved_enrollment >= course.capacity:
            result = _base_result(
                course,
                outcome="section_full",
                approved_enrollment=approved_enrollment,
                expired_entry_ids=[],
            )
            db.commit()
            return result

        candidates = locked_active_waitlist_query(
            db,
            section_id=course.id,
        ).all()

        if not candidates:
            result = _base_result(
                course,
                outcome="queue_empty",
                approved_enrollment=approved_enrollment,
                expired_entry_ids=[],
            )
            db.commit()
            return result

        promoted_at = datetime.now(timezone.utc)
        expired_entry_ids = []

        for entry, student in candidates:
            if not _candidate_is_eligible(
                db,
                student=student,
                course=course,
            ):
                entry.waitlist_status = WaitlistStatus.EXPIRED.value
                entry.removed_at = promoted_at
                expired_entry_ids.append(entry.id)
                continue

            registration = Registration(
                student_id=student.id,
                section_id=course.id,
                registration_status=RegistrationStatus.PENDING.value,
                submitted_at=promoted_at,
            )
            db.add(registration)
            db.flush()

            allocation = approve_pending_registration_in_locked_section(
                registration=registration,
                course=course,
                approved_enrollment=approved_enrollment,
            )
            entry.waitlist_status = WaitlistStatus.PROMOTED.value
            entry.promoted_at = promoted_at
            entry.removed_at = None
            notification = _promotion_notification(
                student=student,
                course=course,
            )
            audit_log = _promotion_audit_log(
                student=student,
                course=course,
                entry=entry,
                registration=registration,
            )
            db.add_all([notification, audit_log])
            db.flush()

            result = WaitlistPromotionResult(
                course_id=course.course_id,
                code=course.code,
                section=course.section,
                promoted=True,
                outcome="promoted",
                capacity=course.capacity,
                approved_enrollment=allocation.approved_enrollment,
                available_seats=allocation.available_seats,
                expired_waitlist_entry_ids=expired_entry_ids,
                waitlist_entry_id=entry.id,
                student_id=student.id,
                registration_id=registration.id,
                registration_status=RegistrationStatus.APPROVED.value,
                waitlist_status=WaitlistStatus.PROMOTED.value,
                promoted_at=promoted_at,
                notification_id=notification.id,
                audit_log_id=audit_log.id,
            )
            db.commit()
            return result

        db.flush()
        result = _base_result(
            course,
            outcome="no_eligible_student",
            approved_enrollment=approved_enrollment,
            expired_entry_ids=expired_entry_ids,
        )
        db.commit()
        return result

    except PromotionSectionNotFoundError:
        db.rollback()
        raise
    except WaitlistPromotionRepositoryError:
        db.rollback()
        raise
    except (
        PrerequisiteRepositoryError,
        ScheduleConflictRepositoryError,
        SeatAllocationRepositoryError,
    ) as error:
        db.rollback()
        raise WaitlistPromotionRepositoryError(str(error)) from error
    except Exception as error:
        db.rollback()
        raise WaitlistPromotionRepositoryError(str(error)) from error


def promote_next_waitlisted_student(
    db: Session,
    *,
    course_id: str,
) -> WaitlistPromotionResult:
    """Atomically approve the first currently eligible waiting student.

    One invocation fills at most one available seat. Callers that release one
    seat, such as the course-drop workflow, can invoke this operation inside
    their section-sensitive workflow without risking over-enrollment.
    """

    with section_transaction_guard(db):
        return _promote_next_waitlisted_student(
            db,
            course_id=course_id,
        )
