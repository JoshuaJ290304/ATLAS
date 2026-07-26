from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.services.admin import get_platform_settings
from app.services.password_recovery import (
    generate_password_reset_token,
    hash_password_reset_token,
)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create_password_reset_request(
    db: AsyncSession,
    email: str,
    requested_ip: str | None,
) -> tuple[User, str] | None:
    """Create a one-use reset token without revealing whether an account exists."""

    user_result = await db.execute(
        select(User).where(User.email == email.lower()).with_for_update()
    )
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None

    now = datetime.now(UTC)
    if settings.PASSWORD_RESET_COOLDOWN_SECONDS:
        cooldown_started = now - timedelta(seconds=settings.PASSWORD_RESET_COOLDOWN_SECONDS)
        recent_result = await db.execute(
            select(PasswordResetToken.id)
            .where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.created_at >= cooldown_started,
            )
            .limit(1)
        )
        if recent_result.scalar_one_or_none() is not None:
            return None

    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    platform = await get_platform_settings(db)
    raw_token = generate_password_reset_token()
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_password_reset_token(raw_token),
        expires_at=now + timedelta(minutes=platform.password_reset_expiry_minutes),
        requested_ip=requested_ip,
    )
    db.add(reset_token)
    await db.commit()
    return user, raw_token


async def reset_password_with_token(
    db: AsyncSession,
    raw_token: str,
    new_password: str,
) -> User | None:
    now = datetime.now(UTC).replace(microsecond=0)
    token_hash = hash_password_reset_token(raw_token)

    result = await db.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
        .with_for_update()
    )
    reset_token = result.scalar_one_or_none()
    if (
        reset_token is None
        or reset_token.used_at is not None
        or reset_token.expires_at <= now
    ):
        return None

    user = await db.get(User, reset_token.user_id, with_for_update=True)
    if user is None or not user.is_active:
        return None

    user.password_hash = hash_password(new_password)
    user.password_changed_at = now
    user.last_password_reset_at = now
    user.session_version += 1
    reset_token.used_at = now

    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != reset_token.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    await db.commit()
    return user
