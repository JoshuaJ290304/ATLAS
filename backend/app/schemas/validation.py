import re

WHITESPACE = re.compile(r"\s+")


def clean_required_text(value: str, field_label: str) -> str:
    cleaned = WHITESPACE.sub(" ", value).strip()
    if not cleaned:
        raise ValueError(f"{field_label} cannot be blank")
    return cleaned


def clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = WHITESPACE.sub(" ", value).strip()
    return cleaned or None


def validate_password_strength(value: str) -> str:
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain a lowercase letter")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain an uppercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain a number")
    return value
