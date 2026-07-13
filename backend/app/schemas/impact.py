from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.artifact import ArtifactType
from app.models.impact import ImpactSeverity, RequirementChangeType
from app.models.requirement import RequirementStatus, RequirementType
from app.models.trace_link import TraceLinkType


class RequirementVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    requirement_id: UUID
    version: int
    title: str
    description: str
    requirement_type: RequirementType
    non_functional_category: str | None
    status: RequirementStatus
    ambiguity_score: int
    ambiguity_flags: list[str]
    created_at: datetime


class RequirementVersionComparisonRead(BaseModel):
    requirement_id: UUID
    requirement_code: str
    baseline: RequirementVersionRead
    target: RequirementVersionRead
    change_type: RequirementChangeType
    changed_fields: list[str]
    text_similarity: float
    change_ratio: float
    added_terms: list[str]
    removed_terms: list[str]
    unified_diff: list[str]
    field_changes: dict[str, dict[str, object]]


class ImpactAnalysisCreate(BaseModel):
    requirement_id: UUID
    baseline_version: int | None = Field(default=None, ge=1)
    target_version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_versions(self) -> "ImpactAnalysisCreate":
        if (
            self.baseline_version is not None
            and self.target_version is not None
            and self.baseline_version >= self.target_version
        ):
            raise ValueError("baseline_version must be lower than target_version")
        return self


class ImpactArtifactRead(BaseModel):
    id: UUID
    code: str
    name: str
    artifact_type: ArtifactType
    link_type: TraceLinkType
    confidence_score: float
    path: list[str]


class RiskFactorRead(BaseModel):
    key: str
    label: str
    points: int
    maximum: int
    explanation: str


class ImpactAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    requirement_id: UUID | None
    requirement_code: str
    requirement_title: str
    baseline_version: int
    target_version: int
    change_type: RequirementChangeType
    risk_score: int
    severity: ImpactSeverity
    change_summary: str
    differences: dict[str, object]
    direct_artifacts: list[ImpactArtifactRead]
    transitive_artifacts: list[ImpactArtifactRead]
    risk_factors: list[RiskFactorRead]
    created_at: datetime
    updated_at: datetime


class ImpactSummaryRead(BaseModel):
    total: int
    low: int
    medium: int
    high: int
    critical: int
    latest_risk_score: int | None
    latest_severity: ImpactSeverity | None
