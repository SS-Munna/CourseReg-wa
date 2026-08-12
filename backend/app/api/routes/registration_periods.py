from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.errors import (
    REQUEST_VALIDATION_ERROR_RESPONSE,
    STANDARD_ERROR_RESPONSE,
)
from app.authorization import UserRole, require_roles
from app.database import get_db
from app.models.user import User
from app.repositories.registration_period_status_repository import (
    RegistrationPeriodStatusRepositoryError,
    get_current_registration_period_status,
)
from app.schemas.registration_period import (
    CurrentRegistrationPeriodResponse,
)


router = APIRouter(
    prefix="/api/registration-periods",
    tags=["Registration Periods"],
)
require_student = require_roles(UserRole.STUDENT)


@router.get(
    "/current",
    response_model=CurrentRegistrationPeriodResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def get_current_registration_period(
    semester: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r".*\S.*",
        description="Optional semester label, such as Fall 2026",
    ),
    _current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    try:
        period = get_current_registration_period_status(
            db,
            semester_label=semester,
            current_time=datetime.now(timezone.utc),
        )
        return CurrentRegistrationPeriodResponse(data=period)

    except RegistrationPeriodStatusRepositoryError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_OPERATION_FAILED",
                "message": (
                    "Unable to retrieve registration-period status from "
                    "the database."
                ),
            },
        ) from error
