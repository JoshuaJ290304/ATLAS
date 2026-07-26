from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.security import SecurityRateLimitEvent


@dataclass(frozen=True)
class RateLimitState:
    allowed: bool
    retry_after_seconds: int
    attempts: int


def normalize_rate_limit_identifier(value: str | None) -> str:
    normalized = (value or "unknown").strip().lower()
    return normalized or "unknown"


def hash_rate_limit_key(scope: str, identifier: str) -> str:
    normalized = normalize_rate_limit_identifier(identifier)
    payload = f"{scope}:{normalized}".encode()
    return hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


async def inspect_rate_limit(
    db: AsyncSession,
    *,
    scope: str,
    identifier: str,
    limit: int,
    window_seconds: int,
    now: datetime | None = None,
) -> RateLimitState:
    current = now or datetime.now(UTC)
    window_start = current - timedelta(seconds=window_seconds)
    key_hash = hash_rate_limit_key(scope, identifier)

    attempts = int(
        (
            await db.execute(
                select(func.count(SecurityRateLimitEvent.id)).where(
                    SecurityRateLimitEvent.scope == scope,
                    SecurityRateLimitEvent.key_hash == key_hash,
                    SecurityRateLimitEvent.created_at >= window_start,
                )
            )
        ).scalar_one()
        or 0
    )

    if attempts < limit:
        return RateLimitState(allowed=True, retry_after_seconds=0, attempts=attempts)

    oldest = (
        await db.execute(
            select(SecurityRateLimitEvent.created_at)
            .where(
                SecurityRateLimitEvent.scope == scope,
                SecurityRateLimitEvent.key_hash == key_hash,
                SecurityRateLimitEvent.created_at >= window_start,
            )
            .order_by(SecurityRateLimitEvent.created_at.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    retry_after = window_seconds
    if oldest is not None:
        retry_after = max(
            1,
            int((oldest + timedelta(seconds=window_seconds) - current).total_seconds()),
        )
    return RateLimitState(
        allowed=False,
        retry_after_seconds=retry_after,
        attempts=attempts,
    )


async def enforce_rate_limit(
    db: AsyncSession,
    *,
    scope: str,
    identifier: str,
    limit: int,
    window_seconds: int,
) -> None:
    state = await inspect_rate_limit(
        db,
        scope=scope,
        identifier=identifier,
        limit=limit,
        window_seconds=window_seconds,
    )
    if not state.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait before trying again.",
            headers={"Retry-After": str(state.retry_after_seconds)},
        )


async def record_rate_limit_event(
    db: AsyncSession,
    *,
    scope: str,
    identifier: str,
) -> None:
    db.add(
        SecurityRateLimitEvent(
            scope=scope,
            key_hash=hash_rate_limit_key(scope, identifier),
        )
    )
    await db.flush()


async def clear_rate_limit_events(
    db: AsyncSession,
    *,
    scope: str,
    identifier: str,
) -> None:
    await db.execute(
        delete(SecurityRateLimitEvent).where(
            SecurityRateLimitEvent.scope == scope,
            SecurityRateLimitEvent.key_hash == hash_rate_limit_key(scope, identifier),
        )
    )


async def prune_rate_limit_events(db: AsyncSession) -> None:
    cutoff = datetime.now(UTC) - timedelta(hours=settings.RATE_LIMIT_RETENTION_HOURS)
    await db.execute(
        delete(SecurityRateLimitEvent).where(SecurityRateLimitEvent.created_at < cutoff)
    )
