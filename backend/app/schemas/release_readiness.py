from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.release_readiness import (
    QualityGateStatus,
    ReleaseCandidateStatus,
    ReleaseReadinessLabel,
)


class ReleaseCandidateCreate(BaseModel):
    name: str = Field(min_length=3, max_length=180)
    version_label: str = Field(min_length=1, max_length=40, pattern=r"^[0-9A-Za-z][0-9A-Za-z._+-]*$")
    description: str | None = Field(default=None, max_length=5000)
    target_date: date | None = None
    release_owner: str = Field(min_length=2, max_length=160)
    baseline_id: UUID | None = None
    selected_requirement_ids: list[UUID] = Field(min_length=1, max_length=1000)
    selected_test_case_ids: list[UUID] = Field(default_factory=list, max_length=2000)
    minimum_traceability_percent: float = Field(default=80.0, ge=0, le=100)
    minimum_test_coverage_percent: float = Field(default=80.0, ge=0, le=100)
    maximum_high_risk_impacts: int = Field(default=0, ge=0, le=10000)
    maximum_overdue_reviews: int = Field(default=0, ge=0, le=10000)
    require_active_baseline: bool = True
    require_approved_requirements: bool = True

    @model_validator(mode="after")
    def unique_selections(self):
        if len(set(self.selected_requirement_ids)) != len(self.selected_requirement_ids):
            raise ValueError("Requirement selection contains duplicates")
        if len(set(self.selected_test_case_ids)) != len(self.selected_test_case_ids):
            raise ValueError("Test case selection contains duplicates")
        return self


class ReleaseCandidateUpdate(ReleaseCandidateCreate):
    status: ReleaseCandidateStatus | None = None


class GateResultRead(BaseModel):
    key: str
    name: str
    status: QualityGateStatus
    critical: bool
    score_weight: int
    measured_value: float | int | str | None = None
    threshold: float | int | str | None = None
    message: str
    evidence: dict[str, object] = Field(default_factory=dict)
    recommendation: str | None = None


class ReleaseEvaluationRead(BaseModel):
    id: UUID | None = None
    readiness_score: float
    readiness_label: ReleaseReadinessLabel
    gate_results: list[GateResultRead]
    evidence: dict[str, object]
    blockers: list[dict[str, object]]
    recommendations: list[str]
    created_at: datetime | None = None


class ReleaseCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    created_by_id: UUID
    baseline_id: UUID | None
    name: str
    version_label: str
    description: str | None
    target_date: date | None
    release_owner: str
    status: ReleaseCandidateStatus
    selected_requirement_ids: list[str]
    selected_test_case_ids: list[str]
    minimum_traceability_percent: float
    minimum_test_coverage_percent: float
    maximum_high_risk_impacts: int
    maximum_overdue_reviews: int
    require_active_baseline: bool
    require_approved_requirements: bool
    readiness_score: float
    readiness_label: ReleaseReadinessLabel
    gate_summary: dict[str, object]
    blockers: list[dict[str, object]]
    recommendations: list[str]
    evaluated_at: datetime | None
    reviewer_name: str | None
    review_comments: str | None
    decision_reason: str | None
    signed_off_at: datetime | None
    locked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReleaseDecisionCreate(BaseModel):
    approved: bool
    reviewer_name: str = Field(min_length=2, max_length=160)
    review_comments: str | None = Field(default=None, max_length=5000)
    decision_reason: str = Field(min_length=5, max_length=5000)


class ReleaseComparisonCreate(BaseModel):
    source_release_id: UUID
    target_release_id: UUID

    @model_validator(mode="after")
    def different_releases(self):
        if self.source_release_id == self.target_release_id:
            raise ValueError("Choose two different release candidates")
        return self


class ReleaseComparisonRead(BaseModel):
    source_release_id: UUID
    target_release_id: UUID
    requirements_added: list[str]
    requirements_removed: list[str]
    test_cases_added: list[str]
    test_cases_removed: list[str]
    readiness_score_change: float
    readiness_label_change: str
    gate_changes: list[dict[str, object]]


class ReleaseWorkspaceSummary(BaseModel):
    total: int
    draft: int
    in_review: int
    ready: int
    blocked: int
    released: int
    average_readiness_score: float
