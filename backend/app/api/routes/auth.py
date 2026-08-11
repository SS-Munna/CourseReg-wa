from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.user_repository import (
    create_user,
    find_user_by_email,
    find_user_by_id,
    verify_user_credentials,
)
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.security import (
    AccessTokenError,
    create_access_token,
    get_user_id_from_access_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_student(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = find_user_by_email(db, payload.email)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = create_user(
        db=db,
        name=payload.name,
        email=payload.email,
        password=payload.password,
    )

    return AuthResponse(
        token=create_access_token(user.id),
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
        ),
    )


@router.post("/login", response_model=AuthResponse)
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
            detail="Invalid email or password.",
        )

    return AuthResponse(
        token=create_access_token(user.id),
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_current_student(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise unauthorized_exception(
            "A Bearer access token is required."
        )

    try:
        user_id = get_user_id_from_access_token(
            credentials.credentials
        )
    except AccessTokenError as error:
        raise unauthorized_exception(
            "The access token is invalid or expired."
        ) from error

    user = find_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )