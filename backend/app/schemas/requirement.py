from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.requirement import (
    RequirementSource,
    RequirementStatus,
    RequirementType,
)


class RequirementCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=10, max_length=10000)
    requirement_type: RequirementType
    non_functional_category: str | None = Field(default=None, max_length=80)
    status: RequirementStatus = RequirementStatus.DRAFT

    @model_validator(mode="after")
    def validate_category(self) -> "RequirementCreate":
        if self.requirement_type == RequirementType.FUNCTIONAL:
            self.non_functional_category = None
        return self


class RequirementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=180)
    description: str | None = Field(default=None, min_length=10, max_length=10000)
    requirement_type: RequirementType | None = None
    non_functional_category: str | None = Field(default=None, max_length=80)
    status: RequirementStatus | None = None


class RequirementExtractionRequest(BaseModel):
    document_id: UUID
    replace_existing: bool = False


class RequirementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    source_document_id: UUID | None
    code: str
    title: str
    description: str
    requirement_type: RequirementType
    non_functional_category: str | None
    status: RequirementStatus
    source: RequirementSource
    source_excerpt: str | None
    source_position: int | None
    confidence_score: float
    ambiguity_score: int
    ambiguity_flags: list[str]
    version: int
    created_at: datetime
    updated_at: datetime


class RequirementExtractionRead(BaseModel):
    document_id: UUID
    detected_count: int
    created_count: int
    skipped_duplicate_count: int
    requirements: list[RequirementRead]


class RequirementSummaryRead(BaseModel):
    total: int
    functional: int
    non_functional: int
    ambiguous: int
    draft: int
    reviewed: int
    approved: int
    rejected: int
    categories: dict[str, int]
