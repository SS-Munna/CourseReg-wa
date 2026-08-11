from dataclasses import dataclass
from itertools import combinations
import re
from typing import Mapping
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.registration import Registration, RegistrationStatus
from app.schemas.schedule_conflict import (
    ScheduleConflict,
    ScheduleConflictCourse,
    ScheduleConflictValidation,
)


ACTIVE_SCHEDULE_STATUSES = (
    RegistrationStatus.DRAFT.value,
    RegistrationStatus.PENDING.value,
    RegistrationStatus.APPROVED.value,
)
SCHEDULE_TIME_PATTERN = re.compile(
    r"^(?P<hour>[01]\d|2[0-3]):(?P<minute>[0-5]\d)$"
)


class ScheduleConflictRepositoryError(RuntimeError):
    """Raised when schedule conflicts cannot be calculated safely."""


class ScheduleConflictError(ValueError):
    def __init__(self, validation: ScheduleConflictValidation):
        super().__init__(validation.message)
        self.validation = validation


@dataclass(frozen=True)
class _ScheduleMeeting:
    day: str
    normalized_day: str
    start_time: str
    end_time: str
    start_minutes: int
    end_minutes: int


def active_schedule_query(
    db: Session,
    *,
    student_id: UUID,
):
    return (
        db.query(Registration, Course)
        .join(Course, Registration.section_id == Course.id)
        .filter(
            Registration.student_id == student_id,
            Registration.registration_status.in_(
                ACTIVE_SCHEDULE_STATUSES
            ),
        )
    )


def _normalized_label(value: str) -> str:
    return " ".join(value.split()).casefold()


def _parse_time(value: object, *, field_name: str) -> tuple[str, int]:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()
    match = SCHEDULE_TIME_PATTERN.fullmatch(normalized)

    if match is None:
        raise ValueError(f"{field_name} must use 24-hour HH:MM format")

    hours = int(match.group("hour"))
    minutes = int(match.group("minute"))
    return normalized, (hours * 60) + minutes


def _parse_schedule(course: Course) -> list[_ScheduleMeeting]:
    schedule = course.schedule or []

    if not isinstance(schedule, list):
        raise ValueError("course schedule must be a list")

    meetings = []

    for index, entry in enumerate(schedule):
        if not isinstance(entry, Mapping):
            raise ValueError(
                f"schedule entry {index} must be an object"
            )

        day_value = entry.get("day")

        if not isinstance(day_value, str) or not day_value.strip():
            raise ValueError(
                f"schedule entry {index} requires a class day"
            )

        day = " ".join(day_value.split())
        start_time, start_minutes = _parse_time(
            entry.get("start_time"),
            field_name=f"schedule entry {index} start_time",
        )
        end_time, end_minutes = _parse_time(
            entry.get("end_time"),
            field_name=f"schedule entry {index} end_time",
        )

        if start_minutes >= end_minutes:
            raise ValueError(
                f"schedule entry {index} must end after it starts"
            )

        meetings.append(
            _ScheduleMeeting(
                day=day,
                normalized_day=_normalized_label(day),
                start_time=start_time,
                end_time=end_time,
                start_minutes=start_minutes,
                end_minutes=end_minutes,
            )
        )

    return meetings


def _same_semester(first: Course, second: Course) -> bool:
    return _normalized_label(first.semester) == _normalized_label(
        second.semester
    )


def _meeting_overlap(
    first: _ScheduleMeeting,
    second: _ScheduleMeeting,
) -> tuple[int, int] | None:
    if first.normalized_day != second.normalized_day:
        return None

    if (
        first.start_minutes >= second.end_minutes
        or first.end_minutes <= second.start_minutes
    ):
        return None

    return (
        max(first.start_minutes, second.start_minutes),
        min(first.end_minutes, second.end_minutes),
    )


def _format_time(total_minutes: int) -> str:
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours:02d}:{minutes:02d}"


def _course_details(
    course: Course,
    *,
    registration_status: str,
    meeting: _ScheduleMeeting,
) -> ScheduleConflictCourse:
    return ScheduleConflictCourse(
        course_id=course.course_id,
        code=course.code,
        title=course.title,
        section=course.section,
        registration_status=registration_status,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
    )


def _conflict_message(
    first: Course,
    second: Course,
    *,
    day: str,
    overlap_start_time: str,
    overlap_end_time: str,
) -> str:
    return (
        f"Schedule conflict detected. {first.code}, Section "
        f"{first.section} overlaps with {second.code}, Section "
        f"{second.section} on {day} from {overlap_start_time} to "
        f"{overlap_end_time}. Remove one course or choose another "
        "section."
    )


def _course_pair_conflicts(
    first: Course,
    first_status: str,
    second: Course,
    second_status: str,
) -> list[ScheduleConflict]:
    if not _same_semester(first, second):
        return []

    conflicts = []

    for first_meeting in _parse_schedule(first):
        for second_meeting in _parse_schedule(second):
            overlap = _meeting_overlap(first_meeting, second_meeting)

            if overlap is None:
                continue

            overlap_start_time = _format_time(overlap[0])
            overlap_end_time = _format_time(overlap[1])
            conflicts.append(
                ScheduleConflict(
                    selected_course=_course_details(
                        first,
                        registration_status=first_status,
                        meeting=first_meeting,
                    ),
                    conflicting_course=_course_details(
                        second,
                        registration_status=second_status,
                        meeting=second_meeting,
                    ),
                    day=first_meeting.day,
                    overlap_start_time=overlap_start_time,
                    overlap_end_time=overlap_end_time,
                    message=_conflict_message(
                        first,
                        second,
                        day=first_meeting.day,
                        overlap_start_time=overlap_start_time,
                        overlap_end_time=overlap_end_time,
                    ),
                )
            )

    return conflicts


def _validation(
    conflicts: list[ScheduleConflict],
) -> ScheduleConflictValidation:
    conflict_count = len(conflicts)

    if conflict_count == 0:
        message = "No schedule conflicts were found."
    elif conflict_count == 1:
        message = "1 schedule conflict was found."
    else:
        message = f"{conflict_count} schedule conflicts were found."

    return ScheduleConflictValidation(
        has_conflicts=bool(conflicts),
        conflict_count=conflict_count,
        conflicts=conflicts,
        message=message,
    )


def get_schedule_conflict_validation(
    db: Session,
    *,
    student_id: UUID,
    candidate_course: Course | None = None,
) -> ScheduleConflictValidation:
    try:
        rows = (
            active_schedule_query(db, student_id=student_id)
            .order_by(
                Course.semester,
                Course.code,
                Course.section,
                Registration.id,
            )
            .all()
        )
        conflicts = []

        if candidate_course is not None:
            _parse_schedule(candidate_course)

            for _, course in rows:
                if _same_semester(candidate_course, course):
                    _parse_schedule(course)
        else:
            for _, course in rows:
                _parse_schedule(course)

        if candidate_course is not None:
            for registration, course in rows:
                if course.id == candidate_course.id:
                    continue

                conflicts.extend(
                    _course_pair_conflicts(
                        candidate_course,
                        RegistrationStatus.DRAFT.value,
                        course,
                        registration.registration_status,
                    )
                )
        else:
            for first_row, second_row in combinations(rows, 2):
                first_registration, first_course = first_row
                second_registration, second_course = second_row
                conflicts.extend(
                    _course_pair_conflicts(
                        first_course,
                        first_registration.registration_status,
                        second_course,
                        second_registration.registration_status,
                    )
                )

        return _validation(conflicts)

    except Exception as error:
        raise ScheduleConflictRepositoryError(str(error)) from error


def require_no_schedule_conflict_for_course(
    db: Session,
    *,
    student_id: UUID,
    candidate_course: Course,
) -> ScheduleConflictValidation:
    validation = get_schedule_conflict_validation(
        db,
        student_id=student_id,
        candidate_course=candidate_course,
    )

    if validation.has_conflicts:
        raise ScheduleConflictError(validation)

    return validation


def require_no_schedule_conflicts(
    db: Session,
    *,
    student_id: UUID,
) -> ScheduleConflictValidation:
    validation = get_schedule_conflict_validation(
        db,
        student_id=student_id,
    )

    if validation.has_conflicts:
        raise ScheduleConflictError(validation)

    return validation
