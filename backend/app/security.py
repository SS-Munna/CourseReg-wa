import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config import settings


class AccessTokenError(Exception):
    """Raised when a JWT access token cannot be validated."""


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), password_hash)


def create_access_token(
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.jwt_expire_minutes
        )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + expires_delta,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "iat", "exp"]},
        )
    except jwt.InvalidTokenError as error:
        raise AccessTokenError(
            "Invalid or expired access token."
        ) from error


def get_user_id_from_access_token(token: str) -> int:
    payload = decode_access_token(token)

    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as error:
        raise AccessTokenError(
            "The access token subject is invalid."
        ) from error
