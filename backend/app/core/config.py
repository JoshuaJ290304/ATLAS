from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ATLAS API"
    APP_VERSION: str = "1.0.0-rc.2"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    DEBUG: bool = False
    ENABLE_API_DOCS: bool = True
    SECURITY_HEADERS_ENABLED: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://atlas:atlas_change_me@localhost:5432/atlas_db"

    JWT_SECRET_KEY: str = Field(
        default="development-only-change-me-use-at-least-32-bytes", min_length=32
    )
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    JWT_ISSUER: str = "atlas-api"
    JWT_AUDIENCE: str = "atlas-frontend"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=5, le=10080)

    CORS_ORIGINS: str = "http://localhost:5173"
    TRUSTED_HOSTS: str = "localhost,127.0.0.1,testserver"

    FRONTEND_URL: str = "http://localhost:5173"
    PASSWORD_RESET_EXPIRE_MINUTES: int = Field(default=30, ge=5, le=1440)
    PASSWORD_RESET_COOLDOWN_SECONDS: int = Field(default=60, ge=0, le=3600)

    LOGIN_RATE_LIMIT_ATTEMPTS: int = Field(default=5, ge=1, le=100)
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=900, ge=30, le=86400)
    REGISTRATION_RATE_LIMIT_ATTEMPTS: int = Field(default=5, ge=1, le=100)
    REGISTRATION_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=3600, ge=60, le=86400)
    PASSWORD_RESET_RATE_LIMIT_ATTEMPTS: int = Field(default=5, ge=1, le=100)
    PASSWORD_RESET_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=3600, ge=60, le=86400)
    PASSWORD_RESET_CONFIRM_RATE_LIMIT_ATTEMPTS: int = Field(default=10, ge=1, le=100)
    PASSWORD_RESET_CONFIRM_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=900, ge=30, le=86400)
    RATE_LIMIT_RETENTION_HOURS: int = Field(default=48, ge=1, le=720)

    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = Field(default=1025, ge=1, le=65535)
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@atlas.local"
    SMTP_FROM_NAME: str = "ATLAS"
    SMTP_STARTTLS: bool = False
    SMTP_USE_SSL: bool = False
    SMTP_TIMEOUT_SECONDS: float = Field(default=10.0, ge=1, le=60)

    UPLOAD_ROOT: str = "storage/uploads"
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, ge=1, le=100)
    ALLOWED_DOCUMENT_EXTENSIONS: str = ".pdf,.docx"
    MAX_DOCX_UNCOMPRESSED_MB: int = Field(default=50, ge=1, le=500)
    MAX_DOCX_COMPRESSION_RATIO: int = Field(default=100, ge=5, le=1000)
    MAX_EXTRACTED_TEXT_CHARS: int = Field(default=5_000_000, ge=10_000, le=50_000_000)
    DOCUMENT_EXTRACTION_TIMEOUT_SECONDS: int = Field(default=60, ge=5, le=600)

    CHROMA_PERSIST_ROOT: str = "storage/vector"
    CHROMA_COLLECTION: str = "atlas_project_knowledge"
    MODEL_CACHE_ROOT: str = "storage/models"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = Field(default=24, ge=1, le=128)
    ASSISTANT_CHUNK_SIZE: int = Field(default=900, ge=300, le=4000)
    ASSISTANT_CHUNK_OVERLAP: int = Field(default=120, ge=0, le=1000)

    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "qwen3:4b-instruct"
    OLLAMA_TIMEOUT_SECONDS: float = Field(default=3.0, ge=0.5, le=30)
    OLLAMA_GENERATION_TIMEOUT_SECONDS: float = Field(default=180.0, ge=10, le=600)
    OLLAMA_TEMPERATURE: float = Field(default=0.1, ge=0, le=1)
    OLLAMA_CONTEXT_WINDOW: int = Field(default=8192, ge=2048, le=131072)
    ASSISTANT_ALLOW_RETRIEVAL_FALLBACK: bool = True

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def reject_blank_secret(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("JWT_SECRET_KEY cannot be blank")
        return value

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        if "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS cannot contain '*' when credentials are enabled")

        if self.ENVIRONMENT == "production":
            weak_markers = (
                "development-only",
                "change-me",
                "change_me",
                "replace_with",
            )
            secret = self.JWT_SECRET_KEY.lower()
            if len(self.JWT_SECRET_KEY) < 48 or any(marker in secret for marker in weak_markers):
                raise ValueError(
                    "Production JWT_SECRET_KEY must be a unique random value "
                    "of at least 48 characters"
                )
            if "atlas_change_me" in self.DATABASE_URL.lower():
                raise ValueError("Production DATABASE_URL must not use the default password")
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if self.ENABLE_API_DOCS:
                raise ValueError("ENABLE_API_DOCS must be false in production")

        return self

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]

    @property
    def trusted_hosts(self) -> list[str]:
        return [host.strip() for host in self.TRUSTED_HOSTS.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
