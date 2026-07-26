from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.admin import get_platform_settings

DbSession = Annotated[AsyncSession, Depends(get_db)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


async def get_current_user(
    db: DbSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        user_id = UUID(subject) if subject else None
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_error from None

    if user_id is None:
        raise credentials_error

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error

    if payload.get("sv", 1) != user.session_version:
        raise credentials_error

    if user.password_changed_at is not None:
        expected_password_version = int(user.password_changed_at.timestamp() * 1_000_000)
        if payload.get("pwd") != expected_password_version:
            raise credentials_error

    platform = await get_platform_settings(db)
    if platform.maintenance_mode and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=platform.maintenance_message or "ATLAS is temporarily in maintenance mode.",
        )

    return user


async def get_current_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access is required",
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
