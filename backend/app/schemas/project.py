from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project import ProjectStatus
from app.schemas.validation import clean_optional_text, clean_required_text


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return clean_required_text(value, "Project name")

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        return clean_optional_text(value)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    status: ProjectStatus | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return clean_required_text(value, "Project name")

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        return clean_optional_text(value)


class ProjectRead(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
