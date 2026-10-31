import hashlib
import hmac
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.config import settings


_password_hasher = PasswordHash.recommended()
_legacy_password_hash = re.compile(r"[0-9a-f]{64}")


class AccessTokenError(Exception):
    """Raised when a JWT access token cannot be validated."""


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if _legacy_password_hash.fullmatch(password_hash):
        # Compatibility only: never create a new SHA-256 password record.
        legacy_digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_digest, password_hash)

    try:
        return _password_hasher.verify(password, password_hash)
    except UnknownHashError:
        return False


def verify_and_update_password(
    password: str, password_hash: str,
) -> tuple[bool, str | None]:
    """Return a replacement hash only after successful verification."""
    if _legacy_password_hash.fullmatch(password_hash):
        if verify_password(password, password_hash):
            return True, hash_password(password)
        return False, None

    try:
        return _password_hasher.verify_and_update(password, password_hash)
    except UnknownHashError:
        return False, None


def create_access_token(
    user_id: UUID,
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


def get_user_id_from_access_token(token: str) -> UUID:
    payload = decode_access_token(token)

    try:
        return UUID(str(payload["sub"]))
    except (KeyError, TypeError, ValueError) as error:
        raise AccessTokenError(
            "The access token subject is invalid."
        ) from error
