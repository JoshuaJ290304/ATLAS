from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.validation import validate_password_strength


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(max_length=320)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=512)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("token")
    @classmethod
    def clean_token(cls, value: str) -> str:
        token = value.strip()
        if not token:
            raise ValueError("Reset token is required")
        return token

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_password_strength(value)


class PasswordRecoveryMessage(BaseModel):
    message: str
