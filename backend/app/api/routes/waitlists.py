from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.errors import (
    REQUEST_VALIDATION_ERROR_RESPONSE,
    STANDARD_ERROR_RESPONSE,
)
from app.authorization import UserRole, require_roles
from app.database import get_db
from app.models.user import User
from app.repositories.prerequisite_repository import (
    PrerequisitesNotMetError,
)
from app.repositories.schedule_conflict_repository import (
    ScheduleConflictError,
)
from app.repositories.waitlist_repository import (
    DuplicateRegistrationError,
    DuplicateWaitlistEntryError,
    SectionNotFoundError,
    SectionNotFullError,
    WaitlistEntryNotActiveError,
    WaitlistEntryNotFoundError,
    WaitlistEntryNotJoinableError,
    WaitlistRepositoryError,
    join_waitlist,
    leave_waitlist,
    list_active_waitlist_entries,
)
from app.schemas.waitlist import (
    WaitlistEntryResponse,
    WaitlistJoinRequest,
    WaitlistLeaveResponse,
    WaitlistListResponse,
)


router = APIRouter(prefix="/api/waitlists", tags=["Waiting Lists"])
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
                "Unable to manage waiting-list entries in the database."
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
    response_model=WaitlistListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def get_waitlist_entries(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        entries = list_active_waitlist_entries(
            db,
            student_id=student_id,
        )
        return WaitlistListResponse(data=entries)

    except WaitlistRepositoryError as error:
        raise _repository_error() from error


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=WaitlistEntryResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_409_CONFLICT: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: STANDARD_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def create_waitlist_entry(
    payload: WaitlistJoinRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        entry = join_waitlist(
            db,
            student_id=student_id,
            course_id=payload.course_id,
        )
        return WaitlistEntryResponse(data=entry)

    except SectionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SECTION_NOT_FOUND",
                "message": "The requested course section was not found.",
            },
        ) from error
    except SectionNotFullError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SECTION_NOT_FULL",
                "message": (
                    "The section still has an available seat. Select it "
                    "directly instead of joining the waiting list."
                ),
                "details": error.availability.model_dump(mode="json"),
            },
        ) from error
    except DuplicateRegistrationError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_REGISTRATION",
                "message": (
                    "This course section is already selected or registered."
                ),
                "details": {
                    "registration_status": error.registration_status,
                },
            },
        ) from error
    except DuplicateWaitlistEntryError as error:
        details: dict[str, object] = {
            "waitlist_status": error.waitlist_status
        }
        if error.queue_position is not None:
            details["queue_position"] = error.queue_position

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_WAITLIST_ENTRY",
                "message": (
                    "This course section is already on your waiting list."
                ),
                "details": details,
            },
        ) from error
    except WaitlistEntryNotJoinableError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "WAITLIST_ENTRY_NOT_JOINABLE",
                "message": (
                    "This waiting-list record has already been promoted "
                    "and cannot be rejoined."
                ),
                "details": {
                    "waitlist_status": error.waitlist_status,
                },
            },
        ) from error
    except PrerequisitesNotMetError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "PREREQUISITES_NOT_MET",
                "message": (
                    "The waiting list cannot be joined because "
                    "prerequisite requirements are not met."
                ),
                "details": error.validation.model_dump(mode="json"),
            },
        ) from error
    except ScheduleConflictError as error:
        raise _schedule_conflict_error(error) from error
    except WaitlistRepositoryError as error:
        raise _repository_error() from error


@router.delete(
    "/{course_id}",
    response_model=WaitlistLeaveResponse,
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
def delete_waitlist_entry(
    course_id: str = Path(
        ...,
        min_length=1,
        max_length=255,
        pattern=r".*\S.*",
        description="Public identifier of the waitlisted offering",
    ),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        removed = leave_waitlist(
            db,
            student_id=student_id,
            course_id=course_id,
        )
        return WaitlistLeaveResponse(data=removed)

    except WaitlistEntryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "WAITLIST_ENTRY_NOT_FOUND",
                "message": (
                    "No waiting-list entry was found for this section."
                ),
            },
        ) from error
    except WaitlistEntryNotActiveError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "WAITLIST_ENTRY_NOT_ACTIVE",
                "message": (
                    "Only an active waiting-list entry can be left."
                ),
                "details": {
                    "waitlist_status": error.waitlist_status,
                },
            },
        ) from error
    except WaitlistRepositoryError as error:
        raise _repository_error() from error
