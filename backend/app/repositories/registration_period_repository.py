from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.registration_period import RegistrationPeriod
from app.models.semester import Semester


def normalize_semester_label(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def current_drop_periods_by_semester(
    db: Session,
    *,
    semester_labels: set[str],
    current_time: datetime,
) -> dict[str, RegistrationPeriod]:
    """Resolve the most recently opened period for each requested term."""

    normalized_labels = {
        normalize_semester_label(label) for label in semester_labels
    }

    if not normalized_labels:
        return {}

    rows = (
        db.query(RegistrationPeriod, Semester)
        .join(Semester, RegistrationPeriod.semester_id == Semester.id)
        .all()
    )
    current_time_utc = _as_utc(current_time)
    selected: dict[str, RegistrationPeriod] = {}

    for period, semester in rows:
        label = normalize_semester_label(
            f"{semester.semester_name} {semester.academic_year}"
        )

        if label not in normalized_labels:
            continue

        opening_time = _as_utc(period.opening_time)

        if opening_time > current_time_utc:
            continue

        existing = selected.get(label)

        if existing is None or (
            opening_time,
            _as_utc(period.closing_time),
            str(period.id),
        ) > (
            _as_utc(existing.opening_time),
            _as_utc(existing.closing_time),
            str(existing.id),
        ):
            selected[label] = period

    return selected


def current_drop_period_for_semester(
    db: Session,
    *,
    semester_label: str,
    current_time: datetime,
) -> RegistrationPeriod | None:
    return current_drop_periods_by_semester(
        db,
        semester_labels={semester_label},
        current_time=current_time,
    ).get(normalize_semester_label(semester_label))
