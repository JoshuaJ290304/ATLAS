from uuid import UUID

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    password = "StrongPass123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_malformed_password_hash_fails_closed() -> None:
    assert verify_password("StrongPass123!", "not-a-valid-password-hash") is False


def test_access_token_contains_required_security_claims() -> None:
    token = create_access_token("test-user-id", session_version=4)
    payload = decode_access_token(token)

    assert payload["sub"] == "test-user-id"
    assert payload["iss"] == "atlas-api"
    assert payload["aud"] == "atlas-frontend"
    assert payload["sv"] == 4
    UUID(payload["jti"])
    assert {"iat", "nbf", "exp"}.issubset(payload)


def test_production_configuration_rejects_default_secrets() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            ENABLE_API_DOCS=False,
            DATABASE_URL="postgresql+asyncpg://atlas:secure@postgres:5432/atlas_db",
        )


def test_production_configuration_accepts_hardened_values() -> None:
    configured = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        ENABLE_API_DOCS=False,
        DEBUG=False,
        JWT_SECRET_KEY="a-unique-production-secret-value-that-is-longer-than-48-characters",
        DATABASE_URL="postgresql+asyncpg://atlas:secure@postgres:5432/atlas_db",
        CORS_ORIGINS="https://atlas.example.com",
        TRUSTED_HOSTS="atlas.example.com,api.atlas.example.com",
    )
    assert configured.ENVIRONMENT == "production"
    assert configured.cors_origins == ["https://atlas.example.com"]
