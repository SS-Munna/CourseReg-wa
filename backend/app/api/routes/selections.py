from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.errors import (
    REQUEST_VALIDATION_ERROR_RESPONSE,
    STANDARD_ERROR_RESPONSE,
)
from app.authorization import UserRole, require_roles
from app.database import get_db
from app.models.user import User
from app.repositories.credit_repository import (
    CreditRepositoryError,
    InvalidCreditLoadError,
    get_credit_load_validation,
    require_valid_credit_load,
)
from app.repositories.prerequisite_repository import (
    PrerequisitesNotMetError,
)
from app.repositories.selection_repository import (
    DuplicateSelectionError,
    SectionNotFoundError,
    SelectionNotDraftError,
    SelectionRepositoryError,
    add_draft_selection,
    list_draft_selections,
    remove_draft_selection,
)
from app.repositories.schedule_conflict_repository import (
    ScheduleConflictError,
    ScheduleConflictRepositoryError,
    get_schedule_conflict_validation,
    require_no_schedule_conflicts,
)
from app.schemas.credit import CreditLoadValidationResponse
from app.schemas.schedule_conflict import (
    ScheduleConflictValidationResponse,
)
from app.schemas.selection import (
    DraftSelectionCreate,
    DraftSelectionListResponse,
    DraftSelectionRemovedResponse,
    DraftSelectionResponse,
)

router = APIRouter(prefix="/api/selections", tags=["Selections"])
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
                "Unable to manage draft course selections in the "
                "database."
            ),
        },
    )


def _credit_repository_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "code": "DATABASE_OPERATION_FAILED",
            "message": (
                "Unable to calculate the selected credit load in the "
                "database."
            ),
        },
    )


def _schedule_repository_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "code": "DATABASE_OPERATION_FAILED",
            "message": (
                "Unable to validate selected course schedules in the "
                "database."
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
    response_model=DraftSelectionListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def get_draft_selections(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        selections = list_draft_selections(
            db,
            student_id=student_id,
        )
        credit_validation = get_credit_load_validation(
            db,
            student_id=student_id,
        )
        return DraftSelectionListResponse(
            data=selections,
            credit_validation=credit_validation,
        )

    except CreditRepositoryError as error:
        raise _credit_repository_error() from error
    except SelectionRepositoryError as error:
        raise _repository_error() from error


@router.get(
    "/credit-validation",
    response_model=CreditLoadValidationResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def get_selected_credit_validation(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        validation = get_credit_load_validation(
            db,
            student_id=student_id,
        )
        return CreditLoadValidationResponse(data=validation)

    except CreditRepositoryError as error:
        raise _credit_repository_error() from error


@router.post(
    "/credit-validation",
    response_model=CreditLoadValidationResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: STANDARD_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def validate_final_credit_load(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        validation = require_valid_credit_load(
            db,
            student_id=student_id,
        )
        return CreditLoadValidationResponse(data=validation)

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
    except CreditRepositoryError as error:
        raise _credit_repository_error() from error


@router.get(
    "/schedule-conflict-validation",
    response_model=ScheduleConflictValidationResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def get_selected_schedule_conflict_validation(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        validation = get_schedule_conflict_validation(
            db,
            student_id=student_id,
        )
        return ScheduleConflictValidationResponse(data=validation)

    except ScheduleConflictRepositoryError as error:
        raise _schedule_repository_error() from error


@router.post(
    "/schedule-conflict-validation",
    response_model=ScheduleConflictValidationResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_409_CONFLICT: STANDARD_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def validate_final_schedule_conflicts(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        validation = require_no_schedule_conflicts(
            db,
            student_id=student_id,
        )
        return ScheduleConflictValidationResponse(data=validation)

    except ScheduleConflictError as error:
        raise _schedule_conflict_error(error) from error
    except ScheduleConflictRepositoryError as error:
        raise _schedule_repository_error() from error


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DraftSelectionResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_409_CONFLICT: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: STANDARD_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def create_draft_selection(
    payload: DraftSelectionCreate,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        selection, credit_validation = add_draft_selection(
            db,
            student_id=student_id,
            course_id=payload.course_id,
        )
        return DraftSelectionResponse(
            data=selection,
            credit_validation=credit_validation,
        )

    except SectionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SECTION_NOT_FOUND",
                "message": "The requested course section was not found.",
            },
        ) from error
    except DuplicateSelectionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_SELECTION",
                "message": (
                    "This course section is already selected or "
                    "registered."
                ),
                "details": {
                    "registration_status": error.registration_status,
                },
            },
        ) from error
    except PrerequisitesNotMetError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "PREREQUISITES_NOT_MET",
                "message": (
                    "The course section cannot be selected because "
                    "prerequisite requirements are not met."
                ),
                "details": error.validation.model_dump(mode="json"),
            },
        ) from error
    except ScheduleConflictError as error:
        raise _schedule_conflict_error(error) from error
    except SelectionRepositoryError as error:
        raise _repository_error() from error


@router.delete(
    "/{course_id}",
    response_model=DraftSelectionRemovedResponse,
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
def delete_draft_selection(
    course_id: str = Path(
        ...,
        min_length=1,
        max_length=255,
        pattern=r".*\S.*",
        description="Public identifier of the selected offering",
    ),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student_id = _student_id_or_404(current_user)

    try:
        removed, credit_validation = remove_draft_selection(
            db,
            student_id=student_id,
            course_id=course_id,
        )
        return DraftSelectionRemovedResponse(
            data=removed,
            credit_validation=credit_validation,
        )

    except SectionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DRAFT_SELECTION_NOT_FOUND",
                "message": "The requested draft selection was not found.",
            },
        ) from error
    except SelectionNotDraftError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SELECTION_NOT_DRAFT",
                "message": "Only draft course selections can be removed.",
                "details": {
                    "registration_status": error.registration_status,
                },
            },
        ) from error
    except SelectionRepositoryError as error:
        raise _repository_error() from error
