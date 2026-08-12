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
from app.models.advisor import Advisor
from app.models.user import User
from app.repositories.advisor_review_repository import (
    AdvisorRequestAlreadyReviewedError,
    AdvisorRequestNotFoundError,
    AdvisorReviewRepositoryError,
    AdvisorReviewSectionsFullError,
    get_advisor_registration_request,
    list_advisor_registration_requests,
    review_advisor_registration_request,
)
from app.schemas.advisor_review import (
    AdvisorRegistrationRequestDetailsResponse,
    AdvisorRegistrationRequestListResponse,
    AdvisorReviewDecisionRequest,
    AdvisorReviewDecisionResponse,
)


router = APIRouter(
    prefix="/api/advisor/registration-requests",
    tags=["Advisor Registration Reviews"],
)
require_advisor = require_roles(UserRole.ADVISOR)


def _advisor_or_404(current_user: User) -> Advisor:
    if current_user.advisor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ADVISOR_PROFILE_NOT_FOUND",
                "message": (
                    "The authenticated account has no advisor profile."
                ),
            },
        )

    return current_user.advisor


def _request_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "REGISTRATION_REQUEST_NOT_FOUND",
            "message": (
                "The registration request was not found among your "
                "assigned students."
            ),
        },
    )


def _repository_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "code": "DATABASE_OPERATION_FAILED",
            "message": (
                "Unable to manage advisor registration reviews in the "
                "database."
            ),
        },
    )


@router.get(
    "",
    response_model=AdvisorRegistrationRequestListResponse,
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
def get_registration_requests(
    request_status: Literal[
        "pending",
        "approved",
        "rejected",
        "all",
    ] = Query(default="pending", alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_advisor),
    db: Session = Depends(get_db),
):
    advisor = _advisor_or_404(current_user)

    try:
        requests, pagination = list_advisor_registration_requests(
            db,
            advisor_id=advisor.id,
            request_status=request_status,
            page=page,
            page_size=page_size,
        )
        return AdvisorRegistrationRequestListResponse(
            data=requests,
            pagination=pagination,
        )

    except AdvisorReviewRepositoryError as error:
        raise _repository_error() from error


@router.get(
    "/{request_id}",
    response_model=AdvisorRegistrationRequestDetailsResponse,
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
def get_registration_request(
    request_id: UUID = Path(
        ...,
        description="Registration UUID identifying one submitted request",
    ),
    current_user: User = Depends(require_advisor),
    db: Session = Depends(get_db),
):
    advisor = _advisor_or_404(current_user)

    try:
        request = get_advisor_registration_request(
            db,
            advisor_id=advisor.id,
            request_id=request_id,
        )
        return AdvisorRegistrationRequestDetailsResponse(data=request)

    except AdvisorRequestNotFoundError as error:
        raise _request_not_found() from error
    except AdvisorReviewRepositoryError as error:
        raise _repository_error() from error


@router.post(
    "/{request_id}/decision",
    response_model=AdvisorReviewDecisionResponse,
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
def decide_registration_request(
    payload: AdvisorReviewDecisionRequest,
    request_id: UUID = Path(
        ...,
        description="Registration UUID identifying one submitted request",
    ),
    current_user: User = Depends(require_advisor),
    db: Session = Depends(get_db),
):
    advisor = _advisor_or_404(current_user)

    try:
        decision = review_advisor_registration_request(
            db,
            advisor=advisor,
            actor_user_id=current_user.id,
            request_id=request_id,
            decision=payload.decision,
            comment=payload.comment,
        )
        return AdvisorReviewDecisionResponse(data=decision)

    except AdvisorRequestNotFoundError as error:
        raise _request_not_found() from error
    except AdvisorRequestAlreadyReviewedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "REGISTRATION_REQUEST_ALREADY_REVIEWED",
                "message": (
                    "Only a pending registration request can receive a "
                    "new advisor decision."
                ),
                "details": {
                    "request_status": error.request_status,
                },
            },
        ) from error
    except AdvisorReviewSectionsFullError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SECTION_FULL",
                "message": (
                    "The request cannot be approved because one or more "
                    "sections are full."
                ),
                "details": {
                    "sections": [
                        section.model_dump(mode="json")
                        for section in error.sections
                    ]
                },
            },
        ) from error
    except AdvisorReviewRepositoryError as error:
        raise _repository_error() from error
