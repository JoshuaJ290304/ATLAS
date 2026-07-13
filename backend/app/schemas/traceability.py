from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.artifact import ArtifactType
from app.models.trace_link import TraceLinkSource, TraceLinkStatus, TraceLinkType


class ArtifactCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    artifact_type: ArtifactType
    description: str = Field(min_length=5, max_length=10000)
    technical_details: dict[str, object] = Field(default_factory=dict)


class ArtifactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    artifact_type: ArtifactType | None = None
    description: str | None = Field(default=None, min_length=5, max_length=10000)
    technical_details: dict[str, object] | None = None


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    code: str
    name: str
    artifact_type: ArtifactType
    description: str
    technical_details: dict[str, object]
    created_at: datetime
    updated_at: datetime


class ArtifactSummaryRead(BaseModel):
    total: int
    api: int
    database_table: int
    test_case: int
    uml_component: int


class TraceLinkCreate(BaseModel):
    requirement_id: UUID
    artifact_id: UUID
    link_type: TraceLinkType | None = None
    confidence_score: float = Field(default=1.0, ge=0, le=1)
    evidence_note: str | None = Field(default=None, max_length=1000)


class TraceLinkUpdate(BaseModel):
    status: TraceLinkStatus | None = None
    link_type: TraceLinkType | None = None


class TraceSuggestionRequest(BaseModel):
    minimum_confidence: float = Field(default=0.3, ge=0, le=1)
    replace_system_suggestions: bool = False


class TraceLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    requirement_id: UUID
    artifact_id: UUID
    link_type: TraceLinkType
    status: TraceLinkStatus
    source: TraceLinkSource
    confidence_score: float
    evidence: dict[str, object]
    created_at: datetime
    updated_at: datetime


class TraceSuggestionRead(BaseModel):
    evaluated_pairs: int
    created_count: int
    skipped_existing_count: int
    below_threshold_count: int
    links: list[TraceLinkRead]


class TraceabilitySummaryRead(BaseModel):
    requirement_total: int
    linked_requirements: int
    uncovered_requirements: int
    requirement_coverage_percent: float
    artifact_total: int
    linked_artifacts: int
    uncovered_artifacts: int
    artifact_coverage_percent: float
    suggested_links: int
    accepted_links: int
    rejected_links: int
    uncovered_requirement_codes: list[str]
    uncovered_artifact_codes: list[str]


class TraceabilityMatrixRequirement(BaseModel):
    id: UUID
    code: str
    title: str


class TraceabilityMatrixArtifact(BaseModel):
    id: UUID
    code: str
    name: str
    artifact_type: ArtifactType


class TraceabilityMatrixCell(BaseModel):
    requirement_id: UUID
    artifact_id: UUID
    trace_link_id: UUID
    link_type: TraceLinkType
    status: TraceLinkStatus
    confidence_score: float


class TraceabilityMatrixRead(BaseModel):
    requirements: list[TraceabilityMatrixRequirement]
    artifacts: list[TraceabilityMatrixArtifact]
    cells: list[TraceabilityMatrixCell]


class TraceLinkQuery(BaseModel):
    requirement_id: UUID | None = None
    artifact_id: UUID | None = None
    status: TraceLinkStatus | None = None

    @model_validator(mode="after")
    def validate_filter(self) -> "TraceLinkQuery":
        return self
