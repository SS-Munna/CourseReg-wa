from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.errors import (
    REQUEST_VALIDATION_ERROR_RESPONSE,
    STANDARD_ERROR_RESPONSE,
)
from app.authorization import UserRole, require_roles
from app.database import get_db
from app.models.user import User
from app.repositories.course_drop_repository import (
    CourseDropRepositoryError,
    DropDeadlinePassedError,
    DropPeriodNotConfiguredError,
    DroppableRegistrationNotFoundError,
    RegistrationNotDroppableError,
    drop_approved_registration,
)
from app.repositories.credit_repository import InvalidCreditLoadError
from app.repositories.prerequisite_repository import (
    PrerequisitesNotMetError,
)
from app.repositories.registration_submission_repository import (
    DuplicateCourseSelectionsError,
    NoDraftSelectionsError,
    PreviouslyCompletedCoursesError,
    RegistrationSubmissionRepositoryError,
    SubmissionSectionsFullError,
    submit_final_registration,
)
from app.repositories.registration_status_repository import (
    RegistrationStatusRepositoryError,
    list_student_registration_statuses,
)
from app.repositories.schedule_conflict_repository import (
    ScheduleConflictError,
)
from app.schemas.registration_submission import (
    FinalRegistrationSubmissionResponse,
)
from app.schemas.registration_status import (
    CourseDropResponse,
    RegistrationStatusOverviewResponse,
)


router = APIRouter(prefix="/api/registrations", tags=["Registrations"])
require_student = require_roles(UserRole.STUDENT)


def _student_id_or_404(current_user: User):
    if current_user.student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "STUDENT_PROFILE_NOT_FOUND",
                "message": (
                    "The authenticated account has no student profile."
                ),
            },
        )

    return current_user.student.id


def _repository_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "code": "DATABASE_OPERATION_FAILED",
            "message": (
                "Unable to manage registrations in the database."
            ),
        },
    )


def _schedule_conflict_error(
    error: ScheduleConflictError,
) -> HTTPException:
    first_conflict = error.validation.conflicts[0]
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "SCHEDULE_CONFLICT",
            "message": first_conflict.message,
            "details": error.validation.model_dump(mode="json"),
        },
    )


@router.get(
    "",
    response_model=RegistrationStatusOverviewResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def get_registration_statuses(
    registration_status: Literal[
        "draft",
        "pending",
        "approved",
        "rejected",
        "dropped",
        "waitlisted",
        "all",
    ] = Query(default="all", alias="status"),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        overview = list_student_registration_statuses(
            db,
            student_id=student_id,
            registration_status=registration_status,
        )
        return RegistrationStatusOverviewResponse(data=overview)

    except RegistrationStatusRepositoryError as error:
        raise _repository_error() from error


@router.post(
    "/submit",
    response_model=FinalRegistrationSubmissionResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_409_CONFLICT: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: STANDARD_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def submit_registration(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        submission = submit_final_registration(
            db,
            student_id=student_id,
        )
        return FinalRegistrationSubmissionResponse(data=submission)

    except NoDraftSelectionsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "NO_DRAFT_SELECTIONS",
                "message": "There are no draft course selections to submit.",
            },
        ) from error
    except DuplicateCourseSelectionsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_COURSE_SELECTIONS",
                "message": (
                    "Remove duplicate course selections before final "
                    "submission."
                ),
                "details": {
                    "duplicates": [
                        duplicate.model_dump(mode="json")
                        for duplicate in error.duplicates
                    ]
                },
            },
        ) from error
    except PreviouslyCompletedCoursesError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "COURSE_ALREADY_COMPLETED",
                "message": (
                    "A previously completed course cannot be submitted "
                    "without a retake-permission record."
                ),
                "details": {
                    "courses": [
                        conflict.model_dump(mode="json")
                        for conflict in error.conflicts
                    ]
                },
            },
        ) from error
    except PrerequisitesNotMetError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "PREREQUISITES_NOT_MET",
                "message": (
                    "Final submission is blocked because prerequisite "
                    "requirements are not met."
                ),
                "details": error.validation.model_dump(mode="json"),
            },
        ) from error
    except InvalidCreditLoadError as error:
        validation = error.validation
        code = (
            "CREDIT_LOAD_BELOW_MINIMUM"
            if validation.validation_status == "below_minimum"
            else "CREDIT_LOAD_ABOVE_MAXIMUM"
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": code,
                "message": validation.message,
                "details": validation.model_dump(mode="json"),
            },
        ) from error
    except ScheduleConflictError as error:
        raise _schedule_conflict_error(error) from error
    except SubmissionSectionsFullError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SECTION_FULL",
                "message": (
                    "One or more selected sections are full. Remove them "
                    "or join the waiting list."
                ),
                "details": {
                    "sections": [
                        section.model_dump(mode="json")
                        for section in error.sections
                    ]
                },
            },
        ) from error
    except RegistrationSubmissionRepositoryError as error:
        raise _repository_error() from error


@router.post(
    "/{registration_id}/drop",
    response_model=CourseDropResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_409_CONFLICT: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def drop_registration(
    registration_id: UUID = Path(
        ...,
        description="Owned approved registration UUID to drop",
    ),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        dropped = drop_approved_registration(
            db,
            registration_id=registration_id,
            student_id=student_id,
            actor_user_id=current_user.id,
        )
        return CourseDropResponse(data=dropped)

    except DroppableRegistrationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "REGISTRATION_NOT_FOUND",
                "message": (
                    "No owned registration was found for the supplied ID."
                ),
            },
        ) from error
    except RegistrationNotDroppableError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "REGISTRATION_NOT_DROPPABLE",
                "message": "Only an approved registration can be dropped.",
                "details": {
                    "registration_status": error.registration_status,
                },
            },
        ) from error
    except DropPeriodNotConfiguredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DROP_PERIOD_NOT_CONFIGURED",
                "message": (
                    "No opened registration period is configured for this "
                    "course semester."
                ),
                "details": {
                    "semester": error.semester,
                },
            },
        ) from error
    except DropDeadlinePassedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DROP_DEADLINE_PASSED",
                "message": "The configured course-drop deadline has passed.",
                "details": {
                    "drop_deadline": error.drop_deadline,
                    "current_date": error.current_date,
                },
            },
        ) from error
    except CourseDropRepositoryError as error:
        raise _repository_error() from error
