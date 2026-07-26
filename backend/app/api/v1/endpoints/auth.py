from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.admin import AuditSeverity
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    PasswordRecoveryMessage,
    ResetPasswordRequest,
    Token,
)
from app.schemas.user import UserCreate, UserRead
from app.services.admin import get_platform_settings, write_platform_audit
from app.services.auth import (
    authenticate_user,
    create_password_reset_request,
    get_user_by_email,
    reset_password_with_token,
)
from app.services.email import send_password_reset_email
from app.services.rate_limit import (
    clear_rate_limit_events,
    enforce_rate_limit,
    prune_rate_limit_events,
    record_rate_limit_event,
)

router = APIRouter(prefix="/auth", tags=["authentication"])

PASSWORD_RESET_REQUEST_MESSAGE = (
    "If an active ATLAS account uses that email address, a password-reset link has been sent."
)


def _client_identifier(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, request: Request, db: DbSession) -> User:
    client_identifier = _client_identifier(request)
    await enforce_rate_limit(
        db,
        scope="registration_ip",
        identifier=client_identifier,
        limit=settings.REGISTRATION_RATE_LIMIT_ATTEMPTS,
        window_seconds=settings.REGISTRATION_RATE_LIMIT_WINDOW_SECONDS,
    )
    await record_rate_limit_event(
        db,
        scope="registration_ip",
        identifier=client_identifier,
    )
    await prune_rate_limit_events(db)
    await db.commit()

    platform = await get_platform_settings(db)
    if not platform.registration_enabled:
        raise HTTPException(
            status_code=403,
            detail="New account registration is currently disabled",
        )

    normalized_email = payload.email.lower()
    if await get_user_by_email(db, normalized_email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(
        name=payload.name.strip(),
        email=normalized_email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        await db.flush()
        await write_platform_audit(
            db,
            action="account.registered",
            actor_id=user.id,
            target_user_id=user.id,
            ip_address=client_identifier,
            details={"email": user.email},
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="An account with this email already exists"
        ) from None
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    normalized_email = form_data.username.strip().lower()
    email_too_large = len(normalized_email) > 320
    login_identifier = normalized_email[:320] or "invalid-email"
    requested_ip = _client_identifier(request)

    await enforce_rate_limit(
        db,
        scope="login_email",
        identifier=login_identifier,
        limit=settings.LOGIN_RATE_LIMIT_ATTEMPTS,
        window_seconds=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    )
    await enforce_rate_limit(
        db,
        scope="login_ip",
        identifier=requested_ip,
        limit=settings.LOGIN_RATE_LIMIT_ATTEMPTS * 3,
        window_seconds=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    )

    credentials_too_large = email_too_large or len(form_data.password) > 128
    user = None
    if not credentials_too_large:
        user = await authenticate_user(db, normalized_email, form_data.password)

    if user is None:
        await record_rate_limit_event(
            db,
            scope="login_email",
            identifier=login_identifier,
        )
        await record_rate_limit_event(
            db,
            scope="login_ip",
            identifier=requested_ip,
        )
        await prune_rate_limit_events(db)
        known_user = None
        if not email_too_large:
            known_user = await get_user_by_email(db, normalized_email)
        await write_platform_audit(
            db,
            action="auth.login_failed",
            target_user_id=known_user.id if known_user else None,
            severity=AuditSeverity.WARNING,
            ip_address=requested_ip,
            details={"email": login_identifier},
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await clear_rate_limit_events(
        db,
        scope="login_email",
        identifier=login_identifier,
    )
    user.last_login_at = datetime.now(UTC)
    await write_platform_audit(
        db,
        action="auth.login_succeeded",
        actor_id=user.id,
        target_user_id=user.id,
        ip_address=requested_ip,
    )
    platform = await get_platform_settings(db)
    await db.commit()
    return Token(
        access_token=create_access_token(
            str(user.id),
            expires_delta=timedelta(minutes=platform.session_duration_minutes),
            password_changed_at=user.password_changed_at,
            session_version=user.session_version,
        )
    )


@router.post("/forgot-password", response_model=PasswordRecoveryMessage)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> PasswordRecoveryMessage:
    requested_ip = _client_identifier(request)
    await enforce_rate_limit(
        db,
        scope="password_reset_email",
        identifier=payload.email,
        limit=settings.PASSWORD_RESET_RATE_LIMIT_ATTEMPTS,
        window_seconds=settings.PASSWORD_RESET_RATE_LIMIT_WINDOW_SECONDS,
    )
    await enforce_rate_limit(
        db,
        scope="password_reset_ip",
        identifier=requested_ip,
        limit=settings.PASSWORD_RESET_RATE_LIMIT_ATTEMPTS * 3,
        window_seconds=settings.PASSWORD_RESET_RATE_LIMIT_WINDOW_SECONDS,
    )
    await record_rate_limit_event(
        db,
        scope="password_reset_email",
        identifier=payload.email,
    )
    await record_rate_limit_event(
        db,
        scope="password_reset_ip",
        identifier=requested_ip,
    )
    await prune_rate_limit_events(db)
    # Commit rate-limit evidence for both known and unknown email addresses.
    await db.commit()

    delivery = await create_password_reset_request(db, payload.email, requested_ip)
    if delivery is not None:
        user, raw_token = delivery
        await write_platform_audit(
            db,
            action="auth.password_reset_requested",
            actor_id=user.id,
            target_user_id=user.id,
            ip_address=requested_ip,
        )
        await db.commit()
        background_tasks.add_task(send_password_reset_email, user.email, user.name, raw_token)
    return PasswordRecoveryMessage(message=PASSWORD_RESET_REQUEST_MESSAGE)


@router.post("/reset-password", response_model=PasswordRecoveryMessage)
async def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: DbSession,
) -> PasswordRecoveryMessage:
    requested_ip = _client_identifier(request)
    await enforce_rate_limit(
        db,
        scope="password_reset_confirm_ip",
        identifier=requested_ip,
        limit=settings.PASSWORD_RESET_CONFIRM_RATE_LIMIT_ATTEMPTS,
        window_seconds=settings.PASSWORD_RESET_CONFIRM_RATE_LIMIT_WINDOW_SECONDS,
    )
    await enforce_rate_limit(
        db,
        scope="password_reset_token",
        identifier=payload.token,
        limit=3,
        window_seconds=settings.PASSWORD_RESET_CONFIRM_RATE_LIMIT_WINDOW_SECONDS,
    )
    await record_rate_limit_event(
        db,
        scope="password_reset_confirm_ip",
        identifier=requested_ip,
    )
    await record_rate_limit_event(
        db,
        scope="password_reset_token",
        identifier=payload.token,
    )
    await prune_rate_limit_events(db)
    await db.commit()

    user = await reset_password_with_token(db, payload.token, payload.new_password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password-reset link is invalid, expired, or has already been used.",
        )
    await clear_rate_limit_events(
        db,
        scope="password_reset_token",
        identifier=payload.token,
    )
    await write_platform_audit(
        db,
        action="auth.password_reset_completed",
        actor_id=user.id,
        target_user_id=user.id,
        ip_address=requested_ip,
    )
    await db.commit()
    return PasswordRecoveryMessage(
        message="Your password has been reset. Sign in using the new password."
    )


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: CurrentUser) -> User:
    return current_user
