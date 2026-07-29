from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.user_repository import (
    create_user,
    find_user_by_email,
    find_user_by_id,
    verify_user_credentials,
)
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def make_token(user_id: int) -> str:
    return f"demo-token-{user_id}"


def get_user_id_from_token(authorization: str | None) -> int | None:
    if authorization is None:
        return None

    token = authorization.replace("Bearer ", "").strip()

    if not token.startswith("demo-token-"):
        return None

    try:
        return int(token.replace("demo-token-", ""))
    except ValueError:
        return None


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_student(payload: RegisterRequest, db: Session = Depends(get_db)):
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
        token=make_token(user.id),
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
        ),
    )


@router.post("/login", response_model=AuthResponse)
def login_student(payload: LoginRequest, db: Session = Depends(get_db)):
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
        token=make_token(user.id),
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_current_student(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = get_user_id_from_token(authorization)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token.",
        )

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