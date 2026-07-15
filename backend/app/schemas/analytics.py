from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DistributionItem(BaseModel):
    key: str
    label: str
    count: int = Field(ge=0)
    percent: float = Field(ge=0, le=100)


class RecentActivityItem(BaseModel):
    kind: Literal["document", "requirement", "artifact", "impact", "assistant"]
    title: str
    detail: str
    occurred_at: datetime


class ProjectHealthFactor(BaseModel):
    key: str
    label: str
    score: float = Field(ge=0)
    maximum: float = Field(gt=0)
    status: Literal["strong", "good", "attention", "missing"]
    explanation: str


class ProjectHealthRead(BaseModel):
    score: int = Field(ge=0, le=100)
    grade: Literal["excellent", "good", "fair", "needs_attention"]
    label: str
    summary: str
    factors: list[ProjectHealthFactor]


class DocumentAnalytics(BaseModel):
    total: int
    extracted: int
    uploaded: int
    failed: int
    pages: int
    characters: int
    extraction_rate_percent: float


class RequirementAnalytics(BaseModel):
    total: int
    functional: int
    non_functional: int
    ambiguous: int
    ambiguity_rate_percent: float
    reviewed_or_approved: int
    review_rate_percent: float
    type_distribution: list[DistributionItem]
    status_distribution: list[DistributionItem]
    category_distribution: list[DistributionItem]


class ArtifactAnalytics(BaseModel):
    total: int
    type_distribution: list[DistributionItem]


class TraceabilityAnalytics(BaseModel):
    total_links: int
    accepted: int
    suggested: int
    rejected: int
    linked_requirements: int
    linked_artifacts: int
    requirement_coverage_percent: float
    artifact_coverage_percent: float


class ImpactAnalytics(BaseModel):
    total: int
    average_risk_score: float
    maximum_risk_score: int
    low: int
    medium: int
    high: int
    critical: int
    severity_distribution: list[DistributionItem]


class AssistantAnalytics(BaseModel):
    index_status: str
    indexed_sources: int
    indexed_chunks: int
    conversations: int
    messages: int


class ProjectAnalyticsRead(BaseModel):
    project_id: str
    project_name: str
    generated_at: datetime
    documents: DocumentAnalytics
    requirements: RequirementAnalytics
    artifacts: ArtifactAnalytics
    traceability: TraceabilityAnalytics
    impacts: ImpactAnalytics
    assistant: AssistantAnalytics
    health: ProjectHealthRead
    recent_activity: list[RecentActivityItem]
