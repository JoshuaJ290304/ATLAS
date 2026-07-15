from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact, ArtifactType
from app.models.assistant import (
    AssistantConversation,
    AssistantIndex,
    AssistantIndexStatus,
    AssistantMessage,
)
from app.models.document import Document, DocumentStatus
from app.models.impact import ImpactAnalysis, ImpactSeverity
from app.models.project import Project
from app.models.requirement import Requirement, RequirementStatus, RequirementType
from app.models.trace_link import TraceLink, TraceLinkStatus
from app.schemas.analytics import (
    ArtifactAnalytics,
    AssistantAnalytics,
    DistributionItem,
    DocumentAnalytics,
    ImpactAnalytics,
    ProjectAnalyticsRead,
    ProjectHealthFactor,
    ProjectHealthRead,
    RecentActivityItem,
    RequirementAnalytics,
    TraceabilityAnalytics,
)


@dataclass(frozen=True)
class HealthInputs:
    document_total: int
    document_extracted: int
    requirement_total: int
    reviewed_or_approved: int
    ambiguous: int
    artifact_total: int
    requirement_coverage: float
    artifact_coverage: float
    impact_total: int
    high_or_critical_impacts: int
    assistant_index_ready: bool


def _percent(value: int | float, total: int | float) -> float:
    if total <= 0:
        return 0.0
    return round((value / total) * 100, 1)


def _distribution(
    counts: Counter[str], labels: dict[str, str], *, include_zero: bool = True
) -> list[DistributionItem]:
    total = sum(counts.values())
    items: list[DistributionItem] = []
    for key, label in labels.items():
        count = counts.get(key, 0)
        if count == 0 and not include_zero:
            continue
        items.append(
            DistributionItem(
                key=key,
                label=label,
                count=count,
                percent=_percent(count, total),
            )
        )
    unknown = sorted(set(counts) - set(labels))
    for key in unknown:
        count = counts[key]
        items.append(
            DistributionItem(
                key=key,
                label=key.replace("_", " ").title(),
                count=count,
                percent=_percent(count, total),
            )
        )
    return items


def calculate_project_health(values: HealthInputs) -> ProjectHealthRead:
    factors: list[ProjectHealthFactor] = []

    document_ratio = (
        values.document_extracted / values.document_total if values.document_total else 0
    )
    document_score = round(15 * document_ratio, 1)
    factors.append(
        ProjectHealthFactor(
            key="documentation",
            label="Document readiness",
            score=document_score,
            maximum=15,
            status=_factor_status(document_score, 15),
            explanation=(
                f"{values.document_extracted} of {values.document_total} document(s) have "
                "successfully extracted text."
                if values.document_total
                else "Upload and extract at least one project document."
            ),
        )
    )

    if values.requirement_total:
        review_ratio = values.reviewed_or_approved / values.requirement_total
        ambiguity_quality = 1 - (values.ambiguous / values.requirement_total)
        requirement_score = round(8 + (7 * review_ratio) + (5 * ambiguity_quality), 1)
    else:
        requirement_score = 0.0
    factors.append(
        ProjectHealthFactor(
            key="requirements",
            label="Requirement quality",
            score=requirement_score,
            maximum=20,
            status=_factor_status(requirement_score, 20),
            explanation=(
                f"{values.reviewed_or_approved} reviewed/approved requirement(s); "
                f"{values.ambiguous} currently carry ambiguity warnings."
                if values.requirement_total
                else "Extract or create requirements to establish the project baseline."
            ),
        )
    )

    traceability_score = round(
        15 * (values.requirement_coverage / 100)
        + 15 * (values.artifact_coverage / 100),
        1,
    )
    factors.append(
        ProjectHealthFactor(
            key="traceability",
            label="Traceability coverage",
            score=traceability_score,
            maximum=30,
            status=_factor_status(traceability_score, 30),
            explanation=(
                f"Requirement coverage is {values.requirement_coverage:.1f}% and artifact "
                f"coverage is {values.artifact_coverage:.1f}%."
                if values.requirement_total or values.artifact_total
                else "Create artifacts and accepted trace links to measure coverage."
            ),
        )
    )

    if values.impact_total == 0:
        impact_score = 0.0
        impact_explanation = "Generate at least one impact analysis after changing a requirement."
    else:
        penalty = min(5, values.high_or_critical_impacts * 1.5)
        impact_score = round(max(5, 15 - penalty), 1)
        impact_explanation = (
            f"{values.impact_total} report(s) generated; "
            f"{values.high_or_critical_impacts} are high or critical risk."
        )
    factors.append(
        ProjectHealthFactor(
            key="impact_analysis",
            label="Impact discipline",
            score=impact_score,
            maximum=15,
            status=_factor_status(impact_score, 15),
            explanation=impact_explanation,
        )
    )

    artifact_score = 10.0 if values.artifact_total >= 4 else round(values.artifact_total * 2.5, 1)
    factors.append(
        ProjectHealthFactor(
            key="artifacts",
            label="Artifact inventory",
            score=artifact_score,
            maximum=10,
            status=_factor_status(artifact_score, 10),
            explanation=(
                f"{values.artifact_total} software artifact(s) are registered."
                if values.artifact_total
                else "Register APIs, database tables, test cases, or UML components."
            ),
        )
    )

    assistant_score = 10.0 if values.assistant_index_ready else 0.0
    factors.append(
        ProjectHealthFactor(
            key="assistant",
            label="Knowledge index",
            score=assistant_score,
            maximum=10,
            status=_factor_status(assistant_score, 10),
            explanation=(
                "The AI project knowledge index is ready."
                if values.assistant_index_ready
                else "Build the AI project index to enable grounded search and answers."
            ),
        )
    )

    score = int(round(min(100, sum(item.score for item in factors))))
    if score >= 85:
        grade, label = "excellent", "Excellent"
    elif score >= 70:
        grade, label = "good", "Good"
    elif score >= 50:
        grade, label = "fair", "Fair"
    else:
        grade, label = "needs_attention", "Needs attention"

    weakest = min(factors, key=lambda factor: factor.score / factor.maximum)
    summary = (
        f"Project health is {label.lower()}. The largest improvement opportunity is "
        f"{weakest.label.lower()}."
    )
    return ProjectHealthRead(
        score=score,
        grade=grade,
        label=label,
        summary=summary,
        factors=factors,
    )


def _factor_status(score: float, maximum: float) -> str:
    ratio = score / maximum if maximum else 0
    if ratio >= 0.85:
        return "strong"
    if ratio >= 0.65:
        return "good"
    if ratio > 0:
        return "attention"
    return "missing"


async def build_project_analytics(
    db: AsyncSession, project: Project
) -> ProjectAnalyticsRead:
    documents = list(
        (
            await db.execute(
                select(Document).where(Document.project_id == project.id)
            )
        )
        .scalars()
        .all()
    )
    requirements = list(
        (
            await db.execute(
                select(Requirement).where(Requirement.project_id == project.id)
            )
        )
        .scalars()
        .all()
    )
    artifacts = list(
        (
            await db.execute(select(Artifact).where(Artifact.project_id == project.id))
        )
        .scalars()
        .all()
    )
    links = list(
        (
            await db.execute(select(TraceLink).where(TraceLink.project_id == project.id))
        )
        .scalars()
        .all()
    )
    impacts = list(
        (
            await db.execute(
                select(ImpactAnalysis).where(ImpactAnalysis.project_id == project.id)
            )
        )
        .scalars()
        .all()
    )
    conversations = list(
        (
            await db.execute(
                select(AssistantConversation).where(
                    AssistantConversation.project_id == project.id
                )
            )
        )
        .scalars()
        .all()
    )
    conversation_ids = [item.id for item in conversations]
    messages: list[AssistantMessage] = []
    if conversation_ids:
        messages = list(
            (
                await db.execute(
                    select(AssistantMessage).where(
                        AssistantMessage.conversation_id.in_(conversation_ids)
                    )
                )
            )
            .scalars()
            .all()
        )
    index_result = await db.execute(
        select(AssistantIndex).where(AssistantIndex.project_id == project.id)
    )
    assistant_index = index_result.scalar_one_or_none()

    extracted = sum(item.status == DocumentStatus.EXTRACTED for item in documents)
    uploaded = sum(item.status == DocumentStatus.UPLOADED for item in documents)
    failed = sum(item.status == DocumentStatus.FAILED for item in documents)

    functional = sum(item.requirement_type == RequirementType.FUNCTIONAL for item in requirements)
    non_functional = len(requirements) - functional
    ambiguous = sum(item.ambiguity_score > 0 for item in requirements)
    reviewed_or_approved = sum(
        item.status in {RequirementStatus.REVIEWED, RequirementStatus.APPROVED}
        for item in requirements
    )

    status_counts = Counter(item.status.value for item in requirements)
    category_counts = Counter(
        item.non_functional_category or "uncategorized"
        for item in requirements
        if item.requirement_type == RequirementType.NON_FUNCTIONAL
    )
    artifact_counts = Counter(item.artifact_type.value for item in artifacts)
    severity_counts = Counter(item.severity.value for item in impacts)

    accepted = [item for item in links if item.status == TraceLinkStatus.ACCEPTED]
    linked_requirements = len({item.requirement_id for item in accepted})
    linked_artifacts = len({item.artifact_id for item in accepted})
    requirement_coverage = _percent(linked_requirements, len(requirements))
    artifact_coverage = _percent(linked_artifacts, len(artifacts))

    risk_scores = [item.risk_score for item in impacts]
    assistant_ready = bool(
        assistant_index and assistant_index.status == AssistantIndexStatus.READY
    )

    health = calculate_project_health(
        HealthInputs(
            document_total=len(documents),
            document_extracted=extracted,
            requirement_total=len(requirements),
            reviewed_or_approved=reviewed_or_approved,
            ambiguous=ambiguous,
            artifact_total=len(artifacts),
            requirement_coverage=requirement_coverage,
            artifact_coverage=artifact_coverage,
            impact_total=len(impacts),
            high_or_critical_impacts=sum(
                item.severity in {ImpactSeverity.HIGH, ImpactSeverity.CRITICAL}
                for item in impacts
            ),
            assistant_index_ready=assistant_ready,
        )
    )

    activity: list[RecentActivityItem] = []
    activity.extend(
        RecentActivityItem(
            kind="document",
            title=item.original_filename,
            detail=f"Document {item.status.value}",
            occurred_at=item.updated_at,
        )
        for item in documents
    )
    activity.extend(
        RecentActivityItem(
            kind="requirement",
            title=f"{item.code} · {item.title}",
            detail=f"Requirement {item.status.value}, version {item.version}",
            occurred_at=item.updated_at,
        )
        for item in requirements
    )
    activity.extend(
        RecentActivityItem(
            kind="artifact",
            title=f"{item.code} · {item.name}",
            detail=item.artifact_type.value.replace("_", " ").title(),
            occurred_at=item.updated_at,
        )
        for item in artifacts
    )
    activity.extend(
        RecentActivityItem(
            kind="impact",
            title=f"{item.requirement_code} impact report",
            detail=f"{item.severity.value.title()} risk · score {item.risk_score}",
            occurred_at=item.created_at,
        )
        for item in impacts
    )
    activity.extend(
        RecentActivityItem(
            kind="assistant",
            title=item.title,
            detail="AI assistant conversation",
            occurred_at=item.updated_at,
        )
        for item in conversations
    )
    activity.sort(key=lambda item: item.occurred_at, reverse=True)

    return ProjectAnalyticsRead(
        project_id=str(project.id),
        project_name=project.name,
        generated_at=datetime.now(UTC),
        documents=DocumentAnalytics(
            total=len(documents),
            extracted=extracted,
            uploaded=uploaded,
            failed=failed,
            pages=sum(item.page_count or 0 for item in documents),
            characters=sum(item.character_count for item in documents),
            extraction_rate_percent=_percent(extracted, len(documents)),
        ),
        requirements=RequirementAnalytics(
            total=len(requirements),
            functional=functional,
            non_functional=non_functional,
            ambiguous=ambiguous,
            ambiguity_rate_percent=_percent(ambiguous, len(requirements)),
            reviewed_or_approved=reviewed_or_approved,
            review_rate_percent=_percent(reviewed_or_approved, len(requirements)),
            type_distribution=_distribution(
                Counter(
                    {
                        "functional": functional,
                        "non_functional": non_functional,
                    }
                ),
                {
                    "functional": "Functional",
                    "non_functional": "Non-functional",
                },
            ),
            status_distribution=_distribution(
                status_counts,
                {
                    "draft": "Draft",
                    "reviewed": "Reviewed",
                    "approved": "Approved",
                    "rejected": "Rejected",
                },
            ),
            category_distribution=_distribution(
                category_counts,
                {},
                include_zero=False,
            ),
        ),
        artifacts=ArtifactAnalytics(
            total=len(artifacts),
            type_distribution=_distribution(
                artifact_counts,
                {
                    ArtifactType.API.value: "API",
                    ArtifactType.DATABASE_TABLE.value: "Database table",
                    ArtifactType.TEST_CASE.value: "Test case",
                    ArtifactType.UML_COMPONENT.value: "UML component",
                },
            ),
        ),
        traceability=TraceabilityAnalytics(
            total_links=len(links),
            accepted=sum(item.status == TraceLinkStatus.ACCEPTED for item in links),
            suggested=sum(item.status == TraceLinkStatus.SUGGESTED for item in links),
            rejected=sum(item.status == TraceLinkStatus.REJECTED for item in links),
            linked_requirements=linked_requirements,
            linked_artifacts=linked_artifacts,
            requirement_coverage_percent=requirement_coverage,
            artifact_coverage_percent=artifact_coverage,
        ),
        impacts=ImpactAnalytics(
            total=len(impacts),
            average_risk_score=(
                round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else 0
            ),
            maximum_risk_score=max(risk_scores, default=0),
            low=severity_counts.get("low", 0),
            medium=severity_counts.get("medium", 0),
            high=severity_counts.get("high", 0),
            critical=severity_counts.get("critical", 0),
            severity_distribution=_distribution(
                severity_counts,
                {
                    "low": "Low",
                    "medium": "Medium",
                    "high": "High",
                    "critical": "Critical",
                },
            ),
        ),
        assistant=AssistantAnalytics(
            index_status=(
                assistant_index.status.value
                if assistant_index
                else AssistantIndexStatus.NOT_INDEXED.value
            ),
            indexed_sources=assistant_index.source_count if assistant_index else 0,
            indexed_chunks=assistant_index.chunk_count if assistant_index else 0,
            conversations=len(conversations),
            messages=len(messages),
        ),
        health=health,
        recent_activity=activity[:12],
    )
