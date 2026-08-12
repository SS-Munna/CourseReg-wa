from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.errors import (
    REQUEST_VALIDATION_ERROR_RESPONSE,
    STANDARD_ERROR_RESPONSE,
)
from app.authorization import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import (
    create_user,
    find_user_by_email,
    verify_user_credentials,
)
from app.schemas.auth import (
    AuthData,
    AuthResponse,
    CurrentUserResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.security import create_access_token


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
    },
)
def register_student(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = find_user_by_email(db, payload.email)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "EMAIL_ALREADY_REGISTERED",
                "message": (
                    "An account with this email already exists."
                ),
            },
        )

    user = create_user(
        db=db,
        name=payload.name,
        email=payload.email,
        password=payload.password,
    )

    return AuthResponse(
        data=AuthData(
            token=create_access_token(user.id),
            user=UserResponse(
                id=user.id,
                name=user.full_name,
                email=user.email,
                role=user.role,
            ),
        ),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
    },
)
def login_student(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = verify_user_credentials(
        db=db,
        email=payload.email,
        password=payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
            },
        )

    if getattr(user, "account_status", "active") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCOUNT_NOT_ACTIVE",
                "message": (
                    "This account is not active. Contact an administrator "
                    "if you believe access should be restored."
                ),
            },
        )

    return AuthResponse(
        data=AuthData(
            token=create_access_token(user.id),
            user=UserResponse(
                id=user.id,
                name=user.full_name,
                email=user.email,
                role=user.role,
            ),
        ),
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
    },
)
def get_current_student(
    current_user: User = Depends(get_current_user),
):
    return CurrentUserResponse(
        data=UserResponse(
            id=current_user.id,
            name=current_user.full_name,
            email=current_user.email,
            role=current_user.role,
        )
    )
