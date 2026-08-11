from collections.abc import Callable, Collection
from enum import Enum

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import find_user_by_id
from app.security import (
    AccessTokenError,
    get_user_id_from_access_token,
)


class UserRole(str, Enum):
    STUDENT = "student"
    ADVISOR = "advisor"
    DEPARTMENT_ADMIN = "department-admin"
    SYSTEM_ADMIN = "system-admin"


bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized_exception(
    detail: str,
    *,
    code: str = "UNAUTHORIZED",
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": code,
            "message": detail,
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_exception(
    detail: str = "You do not have permission to access this resource.",
    *,
    code: str = "INSUFFICIENT_PERMISSIONS",
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": code,
            "message": detail,
        },
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise unauthorized_exception(
            "A Bearer access token is required.",
            code="AUTHENTICATION_REQUIRED",
        )

    try:
        user_id = get_user_id_from_access_token(
            credentials.credentials
        )
    except AccessTokenError as error:
        raise unauthorized_exception(
            "The access token is invalid or expired.",
            code="INVALID_ACCESS_TOKEN",
        ) from error

    user = find_user_by_id(db, user_id)

    if user is None:
        raise unauthorized_exception(
            "The access token does not identify an existing user.",
            code="TOKEN_USER_NOT_FOUND",
        )

    return user


def get_validated_role(user: User) -> UserRole:
    try:
        return UserRole(user.role)
    except (TypeError, ValueError) as error:
        raise forbidden_exception(
            "The account does not have a valid role.",
            code="INVALID_ACCOUNT_ROLE",
        ) from error


def require_roles(
    *allowed_roles: UserRole,
) -> Callable[..., User]:
    if not allowed_roles:
        raise ValueError("At least one allowed role is required.")

    allowed_role_set = frozenset(allowed_roles)

    def role_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        current_role = get_validated_role(current_user)

        if current_role not in allowed_role_set:
            raise forbidden_exception()

        return current_user

    return role_dependency


def ensure_owner_or_roles(
    current_user: User,
    *,
    is_owner: bool,
    allowed_roles: Collection[UserRole] = (),
) -> User:
    current_role = get_validated_role(current_user)

    if is_owner or current_role in frozenset(allowed_roles):
        return current_user

    raise forbidden_exception()
