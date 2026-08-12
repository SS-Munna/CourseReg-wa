from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.registration import Registration, RegistrationStatus
from app.repositories.course_repository import (
    approved_enrollment_expression,
    course_to_response,
)
from app.repositories.registration_period_repository import (
    current_drop_periods_by_semester,
    normalize_semester_label,
)
from app.repositories.waitlist_repository import (
    WaitlistRepositoryError,
    list_active_waitlist_entries,
)
from app.schemas.registration_status import (
    DropEligibility,
    RegistrationStatusOverview,
    StudentRegistrationStatus,
    StudentWaitlistStatus,
)


class RegistrationStatusRepositoryError(RuntimeError):
    """Raised when student registration history cannot be read safely."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _drop_eligibility(
    registration: Registration,
    course: Course,
    *,
    drop_periods,
    current_time: datetime,
) -> DropEligibility:
    period = drop_periods.get(normalize_semester_label(course.semester))
    drop_deadline = period.drop_deadline if period is not None else None

    if (
        registration.registration_status
        != RegistrationStatus.APPROVED.value
    ):
        return DropEligibility(
            eligible=False,
            drop_deadline=drop_deadline,
            reason="registration_not_approved",
            message="Only an approved registration can be dropped.",
        )

    if period is None:
        return DropEligibility(
            eligible=False,
            reason="drop_period_not_configured",
            message=(
                "No opened registration period is configured for this "
                "course semester."
            ),
        )

    if current_time.date() > period.drop_deadline:
        return DropEligibility(
            eligible=False,
            drop_deadline=period.drop_deadline,
            reason="drop_deadline_passed",
            message="The configured course-drop deadline has passed.",
        )

    return DropEligibility(
        eligible=True,
        drop_deadline=period.drop_deadline,
        reason="eligible",
        message="This approved registration can be dropped.",
    )


def list_student_registration_statuses(
    db: Session,
    *,
    student_id: UUID,
    registration_status: str,
) -> RegistrationStatusOverview:
    try:
        current_time = datetime.now(timezone.utc)
        registration_rows = []

        if registration_status != "waitlisted":
            enrollment = approved_enrollment_expression()
            query = (
                db.query(
                    Registration,
                    Course,
                    enrollment.label("approved_enrollment"),
                )
                .join(Course, Registration.section_id == Course.id)
                .filter(Registration.student_id == student_id)
            )

            if registration_status != "all":
                query = query.filter(
                    Registration.registration_status
                    == registration_status
                )

            registration_rows = query.order_by(
                Registration.updated_at.desc(),
                Course.semester.desc(),
                Course.code,
                Course.section,
                Registration.id,
            ).all()

        drop_periods = current_drop_periods_by_semester(
            db,
            semester_labels={row[1].semester for row in registration_rows},
            current_time=current_time,
        )
        registrations = [
            StudentRegistrationStatus(
                registration_id=registration.id,
                registration_status=registration.registration_status,
                submitted_at=(
                    _as_utc(registration.submitted_at)
                    if registration.submitted_at is not None
                    else None
                ),
                reviewed_at=(
                    _as_utc(registration.reviewed_at)
                    if registration.reviewed_at is not None
                    else None
                ),
                reviewed_by_advisor_id=registration.reviewed_by,
                advisor_comment=registration.advisor_comment,
                updated_at=_as_utc(registration.updated_at),
                course=course_to_response(
                    course,
                    enrollment=int(approved_enrollment),
                ),
                drop_eligibility=_drop_eligibility(
                    registration,
                    course,
                    drop_periods=drop_periods,
                    current_time=current_time,
                ),
            )
            for registration, course, approved_enrollment in registration_rows
        ]
        waitlist_entries: list[StudentWaitlistStatus] = []

        if registration_status in ("all", "waitlisted"):
            waitlist_entries = [
                StudentWaitlistStatus(**entry.model_dump())
                for entry in list_active_waitlist_entries(
                    db,
                    student_id=student_id,
                )
            ]

        return RegistrationStatusOverview(
            registrations=registrations,
            waitlist_entries=waitlist_entries,
        )

    except RegistrationStatusRepositoryError:
        raise
    except WaitlistRepositoryError as error:
        raise RegistrationStatusRepositoryError(str(error)) from error
    except Exception as error:
        raise RegistrationStatusRepositoryError(str(error)) from error
