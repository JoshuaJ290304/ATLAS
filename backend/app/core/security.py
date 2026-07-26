from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        # Corrupted or unsupported hashes must fail closed rather than exposing a 500 error.
        return False


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    password_changed_at: datetime | None = None,
    session_version: int = 1,
) -> str:
    now = datetime.now(UTC)
    expires_at = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "jti": str(uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "sv": session_version,
    }
    if password_changed_at is not None:
        payload["pwd"] = int(password_changed_at.timestamp() * 1_000_000)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        audience=settings.JWT_AUDIENCE,
        issuer=settings.JWT_ISSUER,
        leeway=5,
        options={
            "require": ["sub", "iat", "nbf", "exp", "jti", "iss", "aud", "sv"],
        },
    )
