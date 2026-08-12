from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.registration_period import RegistrationPeriod
from app.models.semester import Semester
from app.repositories.registration_period_repository import (
    normalize_semester_label,
)
from app.schemas.registration_period import CurrentRegistrationPeriod


class RegistrationPeriodStatusRepositoryError(RuntimeError):
    """Raised when registration-period status cannot be retrieved."""


INACTIVE_PERIOD_STATES = {
    "cancelled",
    "canceled",
    "closed",
    "disabled",
    "expired",
    "inactive",
}


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _effective_status(
    period: RegistrationPeriod,
    *,
    current_time: datetime,
) -> str:
    stored_status = period.status.strip().casefold()

    if stored_status in INACTIVE_PERIOD_STATES:
        return "closed"

    if current_time < _as_utc(period.opening_time):
        return "upcoming"

    if current_time > _as_utc(period.closing_time):
        return "closed"

    return "open"


def _period_sort_key(
    item: tuple[RegistrationPeriod, Semester],
    *,
    current_time: datetime,
) -> tuple[int, float, str]:
    period, _ = item
    effective_status = _effective_status(
        period,
        current_time=current_time,
    )

    if effective_status == "open":
        return (
            0,
            -_as_utc(period.opening_time).timestamp(),
            str(period.id),
        )

    if effective_status == "upcoming":
        return (
            1,
            _as_utc(period.opening_time).timestamp(),
            str(period.id),
        )

    return (
        2,
        -_as_utc(period.closing_time).timestamp(),
        str(period.id),
    )


def get_current_registration_period_status(
    db: Session,
    *,
    semester_label: str | None = None,
    current_time: datetime | None = None,
) -> CurrentRegistrationPeriod:
    try:
        rows = (
            db.query(RegistrationPeriod, Semester)
            .join(Semester, RegistrationPeriod.semester_id == Semester.id)
            .all()
        )
        normalized_filter = (
            normalize_semester_label(semester_label)
            if semester_label
            else None
        )

        if normalized_filter:
            rows = [
                (period, semester)
                for period, semester in rows
                if normalize_semester_label(
                    f"{semester.semester_name} {semester.academic_year}"
                )
                == normalized_filter
            ]

        if not rows:
            return CurrentRegistrationPeriod(
                effective_status="not_configured",
                registration_enabled=False,
                semester=(
                    " ".join(semester_label.strip().split())
                    if semester_label
                    else None
                ),
                message=(
                    "No registration period is configured for this "
                    "semester. Course browsing remains available."
                ),
            )

        now = _as_utc(current_time or datetime.now(timezone.utc))
        period, semester = min(
            rows,
            key=lambda item: _period_sort_key(
                item,
                current_time=now,
            ),
        )
        status = _effective_status(period, current_time=now)
        messages = {
            "open": "Course registration is open for this semester.",
            "upcoming": "Course registration has not opened yet.",
            "closed": (
                "Course registration is closed. Course browsing remains "
                "available."
            ),
        }

        return CurrentRegistrationPeriod(
            effective_status=status,
            registration_enabled=status == "open",
            semester=f"{semester.semester_name} {semester.academic_year}",
            opening_time=_as_utc(period.opening_time),
            closing_time=_as_utc(period.closing_time),
            drop_deadline=period.drop_deadline,
            minimum_credit=period.minimum_credit,
            maximum_credit=period.maximum_credit,
            message=messages[status],
        )

    except Exception as error:
        raise RegistrationPeriodStatusRepositoryError(str(error)) from error
