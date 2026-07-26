from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.dependencies import get_current_admin
from app.core.security import create_access_token, decode_access_token
from app.models.user import User, UserRole
from app.schemas.admin import AdminStatusUpdate, PlatformSettingsUpdate


def user(role: UserRole) -> User:
    return User(
        id=uuid4(),
        name="Existing ATLAS User",
        email=f"{uuid4().hex}@example.com",
        password_hash="not-exposed",
        role=role,
        is_active=True,
        session_version=7,
    )


@pytest.mark.asyncio
async def test_admin_dependency_rejects_normal_users() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin(user(UserRole.USER))
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_dependency_accepts_admin_users() -> None:
    admin = user(UserRole.ADMIN)
    assert await get_current_admin(admin) is admin


def test_access_token_contains_session_version() -> None:
    token = create_access_token(str(uuid4()), session_version=9)
    assert decode_access_token(token)["sv"] == 9


def test_status_payload_supports_suspension_reason() -> None:
    payload = AdminStatusUpdate(status="suspended", reason="  Security review required.  ")
    assert payload.reason == "Security review required."


def test_platform_settings_enforce_supported_document_types() -> None:
    payload = PlatformSettingsUpdate(
        registration_enabled=True,
        maintenance_mode=False,
        maintenance_message=None,
        ai_generation_enabled=True,
        session_duration_minutes=60,
        password_reset_expiry_minutes=30,
        max_upload_size_mb=10,
        allowed_document_extensions=["pdf", ".docx", ".PDF"],
    )
    assert payload.allowed_document_extensions == [".pdf", ".docx"]

    with pytest.raises(ValidationError):
        PlatformSettingsUpdate(
            registration_enabled=True,
            maintenance_mode=False,
            maintenance_message=None,
            ai_generation_enabled=True,
            session_duration_minutes=60,
            password_reset_expiry_minutes=30,
            max_upload_size_mb=10,
            allowed_document_extensions=[".exe"],
        )
