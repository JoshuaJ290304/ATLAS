from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.governance import BaselineStatus, ReviewPriority, ReviewStatus
from app.schemas.validation import clean_optional_text, clean_required_text


class UserReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str


class ReviewRequestCreate(BaseModel):
    reviewer_id: UUID
    priority: ReviewPriority = ReviewPriority.MEDIUM
    due_date: date | None = None
    request_note: str | None = Field(default=None, max_length=4000)

    @field_validator("request_note")
    @classmethod
    def clean_note(cls, value: str | None) -> str | None:
        return clean_optional_text(value)


class ReviewDecisionCreate(BaseModel):
    status: Literal["approved", "rejected"]
    decision_note: str = Field(min_length=3, max_length=4000)

    @field_validator("decision_note")
    @classmethod
    def validate_decision_note(cls, value: str) -> str:
        return clean_required_text(value, "Decision note")


class RequirementReviewRead(BaseModel):
    id: UUID
    project_id: UUID
    requirement_id: UUID
    requirement_code: str
    requirement_title: str
    reviewer: UserReference
    requested_by: UserReference
    status: ReviewStatus
    priority: ReviewPriority
    due_date: date | None
    request_note: str | None
    decision_note: str | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CommentCreate(BaseModel):
    body: str = Field(min_length=2, max_length=5000)

    @field_validator("body")
    @classmethod
    def validate_body(cls, value: str) -> str:
        return clean_required_text(value, "Comment")


class RequirementCommentRead(BaseModel):
    id: UUID
    requirement_id: UUID
    requirement_code: str
    author: UserReference
    body: str
    created_at: datetime
    updated_at: datetime


class BaselineCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    version_label: str = Field(min_length=1, max_length=40)
    description: str | None = Field(default=None, max_length=4000)
    status: BaselineStatus = BaselineStatus.ACTIVE
    requirement_ids: list[UUID] | None = Field(default=None, min_length=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return clean_required_text(value, "Baseline name")

    @field_validator("version_label")
    @classmethod
    def validate_version(cls, value: str) -> str:
        return clean_required_text(value, "Version label")

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        return clean_optional_text(value)


class BaselineComparisonCreate(BaseModel):
    source_baseline_id: UUID
    target_baseline_id: UUID

    @field_validator("target_baseline_id")
    @classmethod
    def different_baselines(cls, value: UUID, info):
        source = info.data.get("source_baseline_id")
        if source is not None and value == source:
            raise ValueError("Choose two different baselines")
        return value


class BaselineRequirementRead(BaseModel):
    id: UUID
    requirement_id: UUID | None
    code: str
    requirement_version: int
    snapshot_data: dict[str, object]
    created_at: datetime


class BaselineSummaryRead(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    version_label: str
    description: str | None
    status: BaselineStatus
    requirement_count: int
    created_by: UserReference
    created_at: datetime
    updated_at: datetime


class BaselineRead(BaselineSummaryRead):
    items: list[BaselineRequirementRead]


class BaselineChangeRead(BaseModel):
    code: str
    changed_fields: list[str] = Field(default_factory=list)
    baseline: dict[str, object] | None = None
    current: dict[str, object] | None = None


class BaselineComparisonRead(BaseModel):
    baseline_id: UUID
    baseline_name: str
    version_label: str
    target_baseline_id: UUID | None = None
    target_baseline_name: str | None = None
    target_version_label: str | None = None
    target_is_current: bool = True
    added: list[BaselineChangeRead]
    modified: list[BaselineChangeRead]
    removed: list[BaselineChangeRead]
    unchanged: list[str]
    added_count: int
    modified_count: int
    removed_count: int
    unchanged_count: int


class GovernanceSummaryRead(BaseModel):
    pending_reviews: int
    approved_requirements: int
    rejected_requirements: int
    in_review_requirements: int
    comments: int
    baselines: int
    approved_baseline_candidates: int


class AuditLogRead(BaseModel):
    id: UUID
    actor: UserReference
    action: str
    entity_type: str
    entity_id: UUID | None
    details: dict[str, object]
    created_at: datetime
