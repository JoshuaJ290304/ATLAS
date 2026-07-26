from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher, unified_diff
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ArtifactType
from app.models.impact import (
    ImpactSeverity,
    RequirementChangeType,
    RequirementVersion,
)
from app.models.requirement import Requirement, RequirementStatus, RequirementType
from app.models.trace_link import TraceLinkStatus

WORD_PATTERN = re.compile(r"[a-z0-9]+")
HIGH_RISK_NFR_CATEGORIES = {"security", "availability", "performance", "reliability"}


class RequirementVersionLike(Protocol):
    version: int
    title: str
    description: str
    requirement_type: RequirementType
    non_functional_category: str | None
    status: RequirementStatus
    ambiguity_score: int
    ambiguity_flags: list[str]


class RequirementLike(Protocol):
    id: UUID
    code: str
    title: str


class ArtifactLike(Protocol):
    id: UUID
    code: str
    name: str
    artifact_type: ArtifactType


class TraceLinkLike(Protocol):
    requirement_id: UUID
    artifact_id: UUID
    status: TraceLinkStatus
    link_type: object
    confidence_score: float


@dataclass(frozen=True)
class VersionComparison:
    change_type: RequirementChangeType
    changed_fields: list[str]
    text_similarity: float
    change_ratio: float
    added_terms: list[str]
    removed_terms: list[str]
    unified_diff: list[str]
    field_changes: dict[str, dict[str, object]]


@dataclass(frozen=True)
class ImpactGraph:
    direct_artifacts: list[dict[str, object]]
    transitive_artifacts: list[dict[str, object]]


@dataclass(frozen=True)
class RiskAssessment:
    risk_score: int
    severity: ImpactSeverity
    factors: list[dict[str, object]]


def requirement_version_from_model(requirement: Requirement) -> RequirementVersion:
    return RequirementVersion(
        project_id=requirement.project_id,
        requirement_id=requirement.id,
        version=requirement.version,
        title=requirement.title,
        description=requirement.description,
        requirement_type=requirement.requirement_type,
        non_functional_category=requirement.non_functional_category,
        status=requirement.status,
        ambiguity_score=requirement.ambiguity_score,
        ambiguity_flags=list(requirement.ambiguity_flags or []),
    )


async def ensure_requirement_snapshot(
    db: AsyncSession,
    requirement: Requirement,
) -> RequirementVersion:
    result = await db.execute(
        select(RequirementVersion).where(
            RequirementVersion.requirement_id == requirement.id,
            RequirementVersion.version == requirement.version,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    snapshot = requirement_version_from_model(requirement)
    db.add(snapshot)
    await db.flush()
    return snapshot


def _terms(value: str) -> set[str]:
    return set(WORD_PATTERN.findall(value.lower()))


def compare_versions(
    baseline: RequirementVersionLike,
    target: RequirementVersionLike,
) -> VersionComparison:
    fields = (
        "title",
        "description",
        "requirement_type",
        "non_functional_category",
        "status",
        "ambiguity_score",
        "ambiguity_flags",
    )
    field_changes: dict[str, dict[str, object]] = {}
    for field in fields:
        before = getattr(baseline, field)
        after = getattr(target, field)
        before_value = before.value if hasattr(before, "value") else before
        after_value = after.value if hasattr(after, "value") else after
        if before_value != after_value:
            field_changes[field] = {"before": before_value, "after": after_value}

    baseline_text = f"{baseline.title}\n{baseline.description}".strip()
    target_text = f"{target.title}\n{target.description}".strip()
    similarity = round(SequenceMatcher(None, baseline_text, target_text).ratio(), 3)
    change_ratio = round(1 - similarity, 3)

    baseline_terms = _terms(baseline_text)
    target_terms = _terms(target_text)
    added_terms = sorted(target_terms - baseline_terms)
    removed_terms = sorted(baseline_terms - target_terms)
    diff_lines = list(
        unified_diff(
            baseline_text.splitlines(),
            target_text.splitlines(),
            fromfile=f"version-{baseline.version}",
            tofile=f"version-{target.version}",
            lineterm="",
        )
    )

    changed_fields = list(field_changes)
    if "requirement_type" in field_changes or "non_functional_category" in field_changes:
        change_type = RequirementChangeType.RECLASSIFIED
    elif changed_fields == ["status"]:
        change_type = RequirementChangeType.STATUS_CHANGED
    elif len(changed_fields) > 2:
        change_type = RequirementChangeType.COMPLEX
    else:
        change_type = RequirementChangeType.MODIFIED

    return VersionComparison(
        change_type=change_type,
        changed_fields=changed_fields,
        text_similarity=similarity,
        change_ratio=change_ratio,
        added_terms=added_terms,
        removed_terms=removed_terms,
        unified_diff=diff_lines,
        field_changes=field_changes,
    )


def build_impact_graph(
    changed_requirement_id: UUID,
    requirements: list[RequirementLike],
    artifacts: list[ArtifactLike],
    links: list[TraceLinkLike],
) -> ImpactGraph:
    accepted = [link for link in links if link.status == TraceLinkStatus.ACCEPTED]
    requirement_by_id = {item.id: item for item in requirements}
    artifact_by_id = {item.id: item for item in artifacts}

    direct_links = [link for link in accepted if link.requirement_id == changed_requirement_id]
    direct_artifact_ids = {link.artifact_id for link in direct_links}
    direct_artifacts = [
        _impact_artifact(
            artifact_by_id[link.artifact_id],
            link,
            [requirement_by_id[changed_requirement_id].code, artifact_by_id[link.artifact_id].code],
        )
        for link in direct_links
        if link.artifact_id in artifact_by_id and changed_requirement_id in requirement_by_id
    ]

    requirements_touching_direct = {
        link.requirement_id
        for link in accepted
        if link.artifact_id in direct_artifact_ids and link.requirement_id != changed_requirement_id
    }

    transitive: dict[UUID, dict[str, object]] = {}
    for bridge_requirement_id in requirements_touching_direct:
        bridge_requirement = requirement_by_id.get(bridge_requirement_id)
        if bridge_requirement is None:
            continue
        bridge_direct_links = [
            link
            for link in accepted
            if link.requirement_id == bridge_requirement_id
            and link.artifact_id in direct_artifact_ids
        ]
        bridge_artifact_links = [
            link
            for link in accepted
            if link.requirement_id == bridge_requirement_id
            and link.artifact_id not in direct_artifact_ids
        ]
        for link in bridge_artifact_links:
            artifact = artifact_by_id.get(link.artifact_id)
            if artifact is None:
                continue
            direct_code = (
                artifact_by_id[bridge_direct_links[0].artifact_id].code
                if bridge_direct_links and bridge_direct_links[0].artifact_id in artifact_by_id
                else "linked artifact"
            )
            candidate = _impact_artifact(
                artifact,
                link,
                [
                    requirement_by_id[changed_requirement_id].code,
                    direct_code,
                    bridge_requirement.code,
                    artifact.code,
                ],
            )
            existing = transitive.get(artifact.id)
            if existing is None or candidate["confidence_score"] > existing["confidence_score"]:
                transitive[artifact.id] = candidate

    return ImpactGraph(
        direct_artifacts=sorted(direct_artifacts, key=lambda item: str(item["code"])),
        transitive_artifacts=sorted(transitive.values(), key=lambda item: str(item["code"])),
    )


def _impact_artifact(
    artifact: ArtifactLike,
    link: TraceLinkLike,
    path: list[str],
) -> dict[str, object]:
    link_type = link.link_type.value if hasattr(link.link_type, "value") else str(link.link_type)
    artifact_type = (
        artifact.artifact_type.value
        if hasattr(artifact.artifact_type, "value")
        else str(artifact.artifact_type)
    )
    return {
        "id": str(artifact.id),
        "code": artifact.code,
        "name": artifact.name,
        "artifact_type": artifact_type,
        "link_type": link_type,
        "confidence_score": round(float(link.confidence_score), 2),
        "path": path,
    }


def assess_risk(
    comparison: VersionComparison,
    target: RequirementVersionLike,
    direct_artifacts: list[dict[str, object]],
    transitive_artifacts: list[dict[str, object]],
) -> RiskAssessment:
    magnitude_points = min(30, round(comparison.change_ratio * 30))
    direct_points = min(30, len(direct_artifacts) * 7)
    critical_types = {"api", "database_table"}
    critical_count = sum(
        1 for item in direct_artifacts if item.get("artifact_type") in critical_types
    )
    direct_points = min(30, direct_points + critical_count * 3)
    transitive_points = min(15, len(transitive_artifacts) * 4)
    lifecycle_points = {
        RequirementStatus.APPROVED: 10,
        RequirementStatus.REVIEWED: 7,
        RequirementStatus.DRAFT: 3,
        RequirementStatus.REJECTED: 0,
    }[target.status]

    quality_points = min(10, target.ambiguity_score)
    if (
        target.requirement_type == RequirementType.NON_FUNCTIONAL
        and (target.non_functional_category or "").lower() in HIGH_RISK_NFR_CATEGORIES
    ):
        quality_points = min(10, quality_points + 5)

    if not direct_artifacts:
        uncertainty_points = 5
        uncertainty_explanation = (
            "No accepted direct trace link exists for the changed requirement."
        )
    else:
        average_confidence = sum(
            float(item.get("confidence_score", 1)) for item in direct_artifacts
        ) / len(direct_artifacts)
        uncertainty_points = 3 if average_confidence < 0.75 else 0
        uncertainty_explanation = (
            f"Average direct-link confidence is {round(average_confidence * 100)}%."
        )

    factors = [
        {
            "key": "change_magnitude",
            "label": "Change magnitude",
            "points": magnitude_points,
            "maximum": 30,
            "explanation": (
                f"{round(comparison.change_ratio * 100)}% textual change across versions."
            ),
        },
        {
            "key": "direct_artifacts",
            "label": "Directly affected artifacts",
            "points": direct_points,
            "maximum": 30,
            "explanation": (
                f"{len(direct_artifacts)} accepted-linked artifact(s), including "
                f"{critical_count} API/table artifact(s)."
            ),
        },
        {
            "key": "transitive_artifacts",
            "label": "Transitive impact",
            "points": transitive_points,
            "maximum": 15,
            "explanation": (
                f"{len(transitive_artifacts)} artifact(s) reached through shared trace paths."
            ),
        },
        {
            "key": "lifecycle",
            "label": "Requirement lifecycle",
            "points": lifecycle_points,
            "maximum": 10,
            "explanation": f"Target version status is {target.status.value}.",
        },
        {
            "key": "quality",
            "label": "Quality and ambiguity",
            "points": quality_points,
            "maximum": 10,
            "explanation": "Includes ambiguity and high-risk non-functional category signals.",
        },
        {
            "key": "traceability_uncertainty",
            "label": "Traceability uncertainty",
            "points": uncertainty_points,
            "maximum": 5,
            "explanation": uncertainty_explanation,
        },
    ]
    score = min(100, sum(int(item["points"]) for item in factors))
    if score >= 75:
        severity = ImpactSeverity.CRITICAL
    elif score >= 50:
        severity = ImpactSeverity.HIGH
    elif score >= 25:
        severity = ImpactSeverity.MEDIUM
    else:
        severity = ImpactSeverity.LOW
    return RiskAssessment(risk_score=score, severity=severity, factors=factors)


def build_change_summary(
    requirement_code: str,
    baseline_version: int,
    target_version: int,
    comparison: VersionComparison,
    direct_count: int,
    transitive_count: int,
    risk: RiskAssessment,
) -> str:
    fields = ", ".join(field.replace("_", " ") for field in comparison.changed_fields)
    field_text = fields or "no persisted fields"
    return (
        f"{requirement_code} changed from version {baseline_version} to {target_version}. "
        f"Changed fields: {field_text}. The trace graph identifies {direct_count} directly "
        f"affected artifact(s) and {transitive_count} transitive artifact(s). "
        f"Risk is {risk.severity.value} ({risk.risk_score}/100)."
    )
