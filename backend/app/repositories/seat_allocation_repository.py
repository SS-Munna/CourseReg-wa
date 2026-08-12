from contextlib import nullcontext
from threading import RLock
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.registration import Registration, RegistrationStatus
from app.schemas.seat_allocation import SeatAllocationResult


_SQLITE_ALLOCATION_MUTEX = RLock()


class SeatAllocationRepositoryError(RuntimeError):
    """Raised when a seat cannot be allocated safely in the database."""


class RegistrationNotFoundError(LookupError):
    """Raised when the requested registration does not exist."""


class RegistrationNotPendingError(ValueError):
    def __init__(self, registration_status: str):
        super().__init__("Only a pending registration can receive a seat.")
        self.registration_status = registration_status


class SectionFullError(ValueError):
    def __init__(
        self,
        *,
        course_id: str,
        capacity: int,
        approved_enrollment: int,
    ):
        super().__init__("The course section has no available seats.")
        self.course_id = course_id
        self.capacity = capacity
        self.approved_enrollment = approved_enrollment


def locked_section_for_registration_query(
    db: Session,
    *,
    registration_id: UUID,
):
    """Build the section query that serializes seat allocation writes."""

    return (
        db.query(Course)
        .join(Registration, Registration.section_id == Course.id)
        .filter(Registration.id == registration_id)
        .populate_existing()
        .with_for_update(of=Course)
    )


def _locked_registration(
    db: Session,
    *,
    registration_id: UUID,
) -> Registration | None:
    return (
        db.query(Registration)
        .filter(Registration.id == registration_id)
        .populate_existing()
        .with_for_update(of=Registration)
        .one_or_none()
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


def _allocation_result(
    *,
    registration: Registration,
    course: Course,
    approved_enrollment: int,
    newly_allocated: bool,
) -> SeatAllocationResult:
    return SeatAllocationResult(
        registration_id=registration.id,
        student_id=registration.student_id,
        course_id=course.course_id,
        code=course.code,
        section=course.section,
        registration_status=RegistrationStatus.APPROVED.value,
        newly_allocated=newly_allocated,
        capacity=course.capacity,
        approved_enrollment=approved_enrollment,
        available_seats=max(
            course.capacity - approved_enrollment,
            0,
        ),
    )


def _allocation_guard(db: Session):
    """Provide SQLite's local equivalent of the section-row lock."""

    if db.get_bind().dialect.name == "sqlite":
        return _SQLITE_ALLOCATION_MUTEX

    return nullcontext()


def _allocate_registration_seat(
    db: Session,
    *,
    registration_id: UUID,
) -> SeatAllocationResult:
    try:
        course = locked_section_for_registration_query(
            db,
            registration_id=registration_id,
        ).one_or_none()

        if course is None:
            raise RegistrationNotFoundError(registration_id)

        registration = _locked_registration(
            db,
            registration_id=registration_id,
        )

        if registration is None:
            raise RegistrationNotFoundError(registration_id)

        if registration.section_id != course.id:
            raise SeatAllocationRepositoryError(
                "The registration section changed during allocation."
            )

        approved_enrollment = _approved_enrollment(
            db,
            section_id=course.id,
        )

        if (
            registration.registration_status
            == RegistrationStatus.APPROVED.value
        ):
            result = _allocation_result(
                registration=registration,
                course=course,
                approved_enrollment=approved_enrollment,
                newly_allocated=False,
            )
            db.commit()
            return result

        if (
            registration.registration_status
            != RegistrationStatus.PENDING.value
        ):
            raise RegistrationNotPendingError(
                registration.registration_status
            )

        if approved_enrollment >= course.capacity:
            raise SectionFullError(
                course_id=course.course_id,
                capacity=course.capacity,
                approved_enrollment=approved_enrollment,
            )

        registration.registration_status = (
            RegistrationStatus.APPROVED.value
        )
        db.flush()

        result = _allocation_result(
            registration=registration,
            course=course,
            approved_enrollment=approved_enrollment + 1,
            newly_allocated=True,
        )
        db.commit()
        return result

    except (
        RegistrationNotFoundError,
        RegistrationNotPendingError,
        SectionFullError,
    ):
        db.rollback()
        raise
    except SeatAllocationRepositoryError:
        db.rollback()
        raise
    except Exception as error:
        db.rollback()
        raise SeatAllocationRepositoryError(str(error)) from error


def allocate_registration_seat(
    db: Session,
    *,
    registration_id: UUID,
) -> SeatAllocationResult:
    """Approve one pending registration without exceeding capacity.

    The section row is locked before enrollment is counted. PostgreSQL
    therefore serializes allocators targeting the same section, and each
    waiting transaction recounts approved registrations after it acquires
    the lock. SQLite ignores ``FOR UPDATE``, so local/test transactions are
    serialized in-process while the allocation is counted, flushed, and
    committed.
    """

    with _allocation_guard(db):
        return _allocate_registration_seat(
            db,
            registration_id=registration_id,
        )
