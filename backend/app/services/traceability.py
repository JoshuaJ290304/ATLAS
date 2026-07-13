from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.models.artifact import ArtifactType
from app.models.trace_link import TraceLinkStatus, TraceLinkType

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "shall",
    "should",
    "system",
    "that",
    "the",
    "to",
    "using",
    "user",
    "users",
    "will",
    "with",
}

ARTIFACT_CUES: dict[ArtifactType, tuple[str, ...]] = {
    ArtifactType.API: ("api", "endpoint", "request", "response", "route", "service"),
    ArtifactType.DATABASE_TABLE: (
        "database",
        "table",
        "record",
        "store",
        "persist",
        "data",
    ),
    ArtifactType.TEST_CASE: ("test", "verify", "validate", "scenario", "expected"),
    ArtifactType.UML_COMPONENT: (
        "uml",
        "component",
        "class",
        "module",
        "diagram",
        "architecture",
    ),
}

LINK_TYPE_BY_ARTIFACT: dict[ArtifactType, TraceLinkType] = {
    ArtifactType.API: TraceLinkType.IMPLEMENTS,
    ArtifactType.DATABASE_TABLE: TraceLinkType.STORES,
    ArtifactType.TEST_CASE: TraceLinkType.VERIFIES,
    ArtifactType.UML_COMPONENT: TraceLinkType.REPRESENTS,
}


class RequirementLike(Protocol):
    id: UUID
    code: str
    title: str
    description: str


class ArtifactLike(Protocol):
    id: UUID
    code: str
    name: str
    description: str
    artifact_type: ArtifactType


class TraceLinkLike(Protocol):
    requirement_id: UUID
    artifact_id: UUID
    status: TraceLinkStatus


@dataclass(frozen=True)
class TraceScore:
    confidence_score: float
    link_type: TraceLinkType
    shared_terms: list[str]
    artifact_type_cues: list[str]
    rationale: str


def tokenize(value: str) -> set[str]:
    return {
        token
        for token in TOKEN_PATTERN.findall(value.lower())
        if len(token) > 1 and token not in STOP_WORDS
    }


def infer_link_type(artifact_type: ArtifactType) -> TraceLinkType:
    return LINK_TYPE_BY_ARTIFACT.get(artifact_type, TraceLinkType.RELATES_TO)


def score_trace_candidate(
    requirement_text: str,
    artifact_name: str,
    artifact_description: str,
    artifact_type: ArtifactType,
) -> TraceScore:
    requirement_tokens = tokenize(requirement_text)
    artifact_tokens = tokenize(f"{artifact_name} {artifact_description}")
    shared_terms = sorted(requirement_tokens & artifact_tokens)

    if requirement_tokens and artifact_tokens:
        overlap = len(shared_terms) / math.sqrt(
            len(requirement_tokens) * len(artifact_tokens)
        )
    else:
        overlap = 0.0

    lowered_requirement = requirement_text.lower()
    artifact_type_cues = [
        cue for cue in ARTIFACT_CUES[artifact_type] if cue in lowered_requirement
    ]
    cue_bonus = min(0.2, len(artifact_type_cues) * 0.06)

    name_tokens = tokenize(artifact_name)
    name_overlap = len(name_tokens & requirement_tokens) / max(1, len(name_tokens))
    name_bonus = min(0.25, name_overlap * 0.25)

    if not shared_terms and not artifact_type_cues and name_overlap == 0:
        confidence = 0.0
    else:
        confidence = min(0.99, 0.08 + overlap * 0.62 + cue_bonus + name_bonus)

    confidence = round(confidence, 2)
    rationale_parts: list[str] = []
    if shared_terms:
        rationale_parts.append(f"Shared terms: {', '.join(shared_terms[:8])}")
    if artifact_type_cues:
        rationale_parts.append(
            f"{artifact_type.value.replace('_', ' ').title()} cues: "
            f"{', '.join(artifact_type_cues[:5])}"
        )
    if name_overlap:
        rationale_parts.append("Artifact name overlaps the requirement")
    rationale = "; ".join(rationale_parts) or "No meaningful lexical evidence"

    return TraceScore(
        confidence_score=confidence,
        link_type=infer_link_type(artifact_type),
        shared_terms=shared_terms,
        artifact_type_cues=artifact_type_cues,
        rationale=rationale,
    )


def calculate_coverage(
    requirements: list[RequirementLike],
    artifacts: list[ArtifactLike],
    links: list[TraceLinkLike],
) -> dict[str, object]:
    accepted = [link for link in links if link.status == TraceLinkStatus.ACCEPTED]
    linked_requirement_ids = {link.requirement_id for link in accepted}
    linked_artifact_ids = {link.artifact_id for link in accepted}

    uncovered_requirements = [
        requirement
        for requirement in requirements
        if requirement.id not in linked_requirement_ids
    ]
    uncovered_artifacts = [
        artifact for artifact in artifacts if artifact.id not in linked_artifact_ids
    ]

    requirement_total = len(requirements)
    artifact_total = len(artifacts)
    linked_requirements = requirement_total - len(uncovered_requirements)
    linked_artifacts = artifact_total - len(uncovered_artifacts)

    return {
        "requirement_total": requirement_total,
        "linked_requirements": linked_requirements,
        "uncovered_requirements": len(uncovered_requirements),
        "requirement_coverage_percent": round(
            linked_requirements / requirement_total * 100 if requirement_total else 0,
            2,
        ),
        "artifact_total": artifact_total,
        "linked_artifacts": linked_artifacts,
        "uncovered_artifacts": len(uncovered_artifacts),
        "artifact_coverage_percent": round(
            linked_artifacts / artifact_total * 100 if artifact_total else 0,
            2,
        ),
        "suggested_links": sum(
            1 for link in links if link.status == TraceLinkStatus.SUGGESTED
        ),
        "accepted_links": len(accepted),
        "rejected_links": sum(
            1 for link in links if link.status == TraceLinkStatus.REJECTED
        ),
        "uncovered_requirement_codes": [item.code for item in uncovered_requirements],
        "uncovered_artifact_codes": [item.code for item in uncovered_artifacts],
    }
