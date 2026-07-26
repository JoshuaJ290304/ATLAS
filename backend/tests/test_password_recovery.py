from urllib.parse import parse_qs, urlparse

import pytest
from pydantic import ValidationError

from app.schemas.auth import ResetPasswordRequest
from app.services.email import build_password_reset_url
from app.services.password_recovery import (
    generate_password_reset_token,
    hash_password_reset_token,
)


def test_reset_tokens_are_random_and_only_hashes_are_persistable() -> None:
    first = generate_password_reset_token()
    second = generate_password_reset_token()

    assert first != second
    assert len(first) >= 43
    assert hash_password_reset_token(first) != first
    assert len(hash_password_reset_token(first)) == 64
    assert hash_password_reset_token(first) == hash_password_reset_token(first)


def test_reset_password_payload_enforces_password_strength() -> None:
    payload = ResetPasswordRequest(token="x" * 48, new_password="StrongPass123!")
    assert payload.new_password == "StrongPass123!"

    with pytest.raises(ValidationError):
        ResetPasswordRequest(token="x" * 48, new_password="weak")


def test_reset_url_contains_token_as_query_parameter() -> None:
    token = "secure-token-value"
    parsed = urlparse(build_password_reset_url(token))

    assert parsed.path == "/reset-password"
    assert parse_qs(parsed.query)["token"] == [token]
