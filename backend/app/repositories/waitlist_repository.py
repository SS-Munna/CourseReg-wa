from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from threading import RLock
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database_errors import get_constraint_name
from app.models.course import Course
from app.models.registration import Registration, RegistrationStatus
from app.models.waitlist_entry import WaitlistEntry, WaitlistStatus
from app.repositories.course_repository import (
    approved_enrollment_expression,
    course_to_response,
    section_availability_to_response,
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
from app.schemas.course import SectionAvailability
from app.schemas.waitlist import (
    WaitlistEntryDetails,
    WaitlistLeaveResult,
)


_SQLITE_WAITLIST_MUTEX = RLock()


class WaitlistRepositoryError(RuntimeError):
    """Raised when waiting-list data cannot be persisted safely."""


class SectionNotFoundError(LookupError):
    """Raised when a public course-section identifier does not exist."""


class SectionNotFullError(ValueError):
    def __init__(self, availability: SectionAvailability):
        super().__init__("The section still has a direct-registration seat.")
        self.availability = availability


class DuplicateRegistrationError(ValueError):
    def __init__(self, registration_status: str):
        super().__init__(
            "The student already has a registration for the section."
        )
        self.registration_status = registration_status


class DuplicateWaitlistEntryError(ValueError):
    def __init__(
        self,
        waitlist_status: str,
        queue_position: int | None = None,
    ):
        super().__init__(
            "The student already has an active waiting-list entry."
        )
        self.waitlist_status = waitlist_status
        self.queue_position = queue_position


class WaitlistEntryNotJoinableError(ValueError):
    def __init__(self, waitlist_status: str):
        super().__init__("The existing waiting-list entry cannot be reactivated.")
        self.waitlist_status = waitlist_status


class WaitlistEntryNotFoundError(LookupError):
    """Raised when the student has no waiting-list entry for a section."""


class WaitlistEntryNotActiveError(ValueError):
    def __init__(self, waitlist_status: str):
        super().__init__("Only an active waiting-list entry can be left.")
        self.waitlist_status = waitlist_status


def locked_waitlist_section_query(
    db: Session,
    *,
    course_id: str,
):
    """Lock one section before checking seats or changing its queue."""

    return (
        db.query(Course)
        .filter(Course.course_id == course_id)
        .populate_existing()
        .with_for_update(of=Course)
    )


def active_waitlist_queue_subquery(db: Session):
    """Return deterministic live positions without storing row numbers."""

    return (
        db.query(
            WaitlistEntry.id.label("waitlist_entry_id"),
            WaitlistEntry.section_id.label("section_id"),
            func.row_number()
            .over(
                partition_by=WaitlistEntry.section_id,
                order_by=(
                    WaitlistEntry.joined_at.asc(),
                    WaitlistEntry.id.asc(),
                ),
            )
            .label("queue_position"),
            func.count(WaitlistEntry.id)
            .over(partition_by=WaitlistEntry.section_id)
            .label("total_waiting"),
        )
        .filter(
            WaitlistEntry.waitlist_status == WaitlistStatus.ACTIVE.value
        )
        .subquery()
    )


def active_waitlist_entry_query(
    db: Session,
    *,
    student_id: UUID,
):
    queue = active_waitlist_queue_subquery(db)
    enrollment = approved_enrollment_expression()

    return (
        db.query(
            WaitlistEntry,
            Course,
            queue.c.queue_position,
            queue.c.total_waiting,
            enrollment.label("approved_enrollment"),
        )
        .join(
            queue,
            queue.c.waitlist_entry_id == WaitlistEntry.id,
        )
        .join(Course, WaitlistEntry.section_id == Course.id)
        .filter(WaitlistEntry.student_id == student_id)
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _entry_to_response(
    entry: WaitlistEntry,
    course: Course,
    *,
    queue_position: int,
    total_waiting: int,
    approved_enrollment: int,
) -> WaitlistEntryDetails:
    return WaitlistEntryDetails(
        waitlist_entry_id=entry.id,
        waitlist_status=WaitlistStatus.ACTIVE.value,
        joined_at=_as_utc(entry.joined_at),
        queue_position=queue_position,
        total_waiting=total_waiting,
        course=course_to_response(
            course,
            enrollment=approved_enrollment,
        ),
    )


def _response_for_entry(
    db: Session,
    *,
    student_id: UUID,
    waitlist_entry_id: UUID,
) -> WaitlistEntryDetails:
    row = (
        active_waitlist_entry_query(db, student_id=student_id)
        .filter(WaitlistEntry.id == waitlist_entry_id)
        .one_or_none()
    )

    if row is None:
        raise WaitlistRepositoryError(
            "The active waiting-list entry could not be read after mutation."
        )

    entry, course, position, total_waiting, enrollment = row
    return _entry_to_response(
        entry,
        course,
        queue_position=int(position),
        total_waiting=int(total_waiting),
        approved_enrollment=int(enrollment),
    )


def list_active_waitlist_entries(
    db: Session,
    *,
    student_id: UUID,
) -> list[WaitlistEntryDetails]:
    try:
        rows = (
            active_waitlist_entry_query(db, student_id=student_id)
            .order_by(
                Course.semester,
                Course.code,
                Course.section,
                WaitlistEntry.joined_at,
                WaitlistEntry.id,
            )
            .all()
        )

        return [
            _entry_to_response(
                entry,
                course,
                queue_position=int(position),
                total_waiting=int(total_waiting),
                approved_enrollment=int(enrollment),
            )
            for entry, course, position, total_waiting, enrollment in rows
        ]

    except Exception as error:
        raise WaitlistRepositoryError(str(error)) from error


def _waitlist_guard(db: Session):
    if db.get_bind().dialect.name == "sqlite":
        return _SQLITE_WAITLIST_MUTEX

    return nullcontext()


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


def _next_joined_at(
    db: Session,
    *,
    section_id: int,
) -> datetime:
    current_time = datetime.now(timezone.utc)
    latest = (
        db.query(func.max(WaitlistEntry.joined_at))
        .filter(
            WaitlistEntry.section_id == section_id,
            WaitlistEntry.waitlist_status == WaitlistStatus.ACTIVE.value,
        )
        .scalar()
    )

    if latest is None:
        return current_time

    latest_utc = _as_utc(latest)
    if current_time <= latest_utc:
        return latest_utc + timedelta(microseconds=1)

    return current_time


def _existing_waitlist_entry(
    db: Session,
    *,
    student_id: UUID,
    section_id: int,
) -> WaitlistEntry | None:
    return (
        db.query(WaitlistEntry)
        .filter(
            WaitlistEntry.student_id == student_id,
            WaitlistEntry.section_id == section_id,
        )
        .populate_existing()
        .with_for_update(of=WaitlistEntry)
        .one_or_none()
    )


def _active_queue_position(
    db: Session,
    *,
    student_id: UUID,
    waitlist_entry_id: UUID,
) -> int | None:
    row = (
        active_waitlist_entry_query(db, student_id=student_id)
        .filter(WaitlistEntry.id == waitlist_entry_id)
        .one_or_none()
    )
    return None if row is None else int(row[2])


def _join_waitlist(
    db: Session,
    *,
    student_id: UUID,
    course_id: str,
) -> WaitlistEntryDetails:
    try:
        course = locked_waitlist_section_query(
            db,
            course_id=course_id,
        ).one_or_none()

        if course is None:
            raise SectionNotFoundError(course_id)

        approved_enrollment = _approved_enrollment(
            db,
            section_id=course.id,
        )
        availability = section_availability_to_response(
            course,
            enrollment=approved_enrollment,
        )

        if not availability.is_full:
            raise SectionNotFullError(availability)

        registration = (
            db.query(Registration)
            .filter(
                Registration.student_id == student_id,
                Registration.section_id == course.id,
            )
            .one_or_none()
        )

        if registration is not None:
            raise DuplicateRegistrationError(
                registration.registration_status
            )

        existing = _existing_waitlist_entry(
            db,
            student_id=student_id,
            section_id=course.id,
        )

        if (
            existing is not None
            and existing.waitlist_status == WaitlistStatus.ACTIVE.value
        ):
            raise DuplicateWaitlistEntryError(
                existing.waitlist_status,
                _active_queue_position(
                    db,
                    student_id=student_id,
                    waitlist_entry_id=existing.id,
                ),
            )

        if (
            existing is not None
            and existing.waitlist_status == WaitlistStatus.PROMOTED.value
        ):
            raise WaitlistEntryNotJoinableError(existing.waitlist_status)

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

        joined_at = _next_joined_at(db, section_id=course.id)

        if existing is None:
            entry = WaitlistEntry(
                student_id=student_id,
                section_id=course.id,
                waitlist_status=WaitlistStatus.ACTIVE.value,
                joined_at=joined_at,
            )
            db.add(entry)
        else:
            entry = existing
            entry.waitlist_status = WaitlistStatus.ACTIVE.value
            entry.joined_at = joined_at
            entry.promoted_at = None
            entry.removed_at = None

        db.flush()
        response = _response_for_entry(
            db,
            student_id=student_id,
            waitlist_entry_id=entry.id,
        )
        db.commit()
        return response

    except (
        DuplicateRegistrationError,
        DuplicateWaitlistEntryError,
        PrerequisitesNotMetError,
        ScheduleConflictError,
        SectionNotFoundError,
        SectionNotFullError,
        WaitlistEntryNotJoinableError,
    ):
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()

        if get_constraint_name(error) == "uq_waitlist_student_section":
            raise DuplicateWaitlistEntryError(
                WaitlistStatus.ACTIVE.value
            ) from error

        raise WaitlistRepositoryError(str(error)) from error
    except (
        PrerequisiteRepositoryError,
        ScheduleConflictRepositoryError,
    ) as error:
        db.rollback()
        raise WaitlistRepositoryError(str(error)) from error
    except Exception as error:
        db.rollback()
        raise WaitlistRepositoryError(str(error)) from error


def join_waitlist(
    db: Session,
    *,
    student_id: UUID,
    course_id: str,
) -> WaitlistEntryDetails:
    with _waitlist_guard(db):
        return _join_waitlist(
            db,
            student_id=student_id,
            course_id=course_id,
        )


def _leave_waitlist(
    db: Session,
    *,
    student_id: UUID,
    course_id: str,
) -> WaitlistLeaveResult:
    try:
        course = locked_waitlist_section_query(
            db,
            course_id=course_id,
        ).one_or_none()

        if course is None:
            raise WaitlistEntryNotFoundError(course_id)

        entry = _existing_waitlist_entry(
            db,
            student_id=student_id,
            section_id=course.id,
        )

        if entry is None:
            raise WaitlistEntryNotFoundError(course_id)

        if entry.waitlist_status != WaitlistStatus.ACTIVE.value:
            raise WaitlistEntryNotActiveError(entry.waitlist_status)

        previous_position = _active_queue_position(
            db,
            student_id=student_id,
            waitlist_entry_id=entry.id,
        )

        if previous_position is None:
            raise WaitlistRepositoryError(
                "The active waiting-list position could not be read."
            )

        removed_at = datetime.now(timezone.utc)
        entry.waitlist_status = WaitlistStatus.REMOVED.value
        entry.removed_at = removed_at
        db.flush()

        remaining_waiting = int(
            db.query(func.count(WaitlistEntry.id))
            .filter(
                WaitlistEntry.section_id == course.id,
                WaitlistEntry.waitlist_status
                == WaitlistStatus.ACTIVE.value,
            )
            .scalar()
            or 0
        )
        response = WaitlistLeaveResult(
            waitlist_entry_id=entry.id,
            course_id=course.course_id,
            waitlist_status=WaitlistStatus.REMOVED.value,
            removed_at=removed_at,
            previous_queue_position=previous_position,
            remaining_waiting=remaining_waiting,
        )
        db.commit()
        return response

    except (
        WaitlistEntryNotActiveError,
        WaitlistEntryNotFoundError,
    ):
        db.rollback()
        raise
    except Exception as error:
        db.rollback()
        raise WaitlistRepositoryError(str(error)) from error


def leave_waitlist(
    db: Session,
    *,
    student_id: UUID,
    course_id: str,
) -> WaitlistLeaveResult:
    with _waitlist_guard(db):
        return _leave_waitlist(
            db,
            student_id=student_id,
            course_id=course_id,
        )
