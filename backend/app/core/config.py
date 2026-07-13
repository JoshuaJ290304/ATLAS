from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ATLAS API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://atlas:atlas_change_me@localhost:5432/atlas_db"

    JWT_SECRET_KEY: str = Field(
        default="development-only-change-me-use-at-least-32-bytes", min_length=32
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: str = "http://localhost:5173"

    UPLOAD_ROOT: str = "storage/uploads"
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, ge=1, le=100)
    ALLOWED_DOCUMENT_EXTENSIONS: str = ".pdf,.docx"

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

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
