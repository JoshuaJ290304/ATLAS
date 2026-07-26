from app.services.rate_limit import (
    hash_rate_limit_key,
    normalize_rate_limit_identifier,
)


def test_rate_limit_identifiers_are_normalized() -> None:
    assert normalize_rate_limit_identifier("  User@Example.COM ") == "user@example.com"
    assert normalize_rate_limit_identifier(None) == "unknown"


def test_rate_limit_keys_are_scoped_and_do_not_expose_identifier() -> None:
    email_key = hash_rate_limit_key("login_email", "user@example.com")
    same_email_key = hash_rate_limit_key("login_email", " USER@example.com ")
    ip_key = hash_rate_limit_key("login_ip", "user@example.com")

    assert email_key == same_email_key
    assert email_key != ip_key
    assert len(email_key) == 64
    assert "user@example.com" not in email_key
