from types import SimpleNamespace
from uuid import uuid4

from app.models.artifact import ArtifactType
from app.models.trace_link import TraceLinkStatus, TraceLinkType
from app.services.traceability import (
    calculate_coverage,
    infer_link_type,
    score_trace_candidate,
    tokenize,
)


def test_tokenize_removes_common_requirement_words() -> None:
    tokens = tokenize("The system shall allow users to reset a forgotten password")

    assert "system" not in tokens
    assert "shall" not in tokens
    assert {"reset", "forgotten", "password"}.issubset(tokens)


def test_infers_link_type_from_artifact_type() -> None:
    assert infer_link_type(ArtifactType.API) == TraceLinkType.IMPLEMENTS
    assert infer_link_type(ArtifactType.DATABASE_TABLE) == TraceLinkType.STORES
    assert infer_link_type(ArtifactType.TEST_CASE) == TraceLinkType.VERIFIES
    assert infer_link_type(ArtifactType.UML_COMPONENT) == TraceLinkType.REPRESENTS


def test_scores_related_api_above_unrelated_component() -> None:
    related = score_trace_candidate(
        "Allow a customer to reset a forgotten password using a reset endpoint",
        "Password reset API",
        "POST endpoint that issues reset tokens and accepts a new password",
        ArtifactType.API,
    )
    unrelated = score_trace_candidate(
        "Allow a customer to reset a forgotten password using a reset endpoint",
        "Invoice table",
        "Stores invoice totals and payment dates",
        ArtifactType.DATABASE_TABLE,
    )

    assert related.confidence_score >= 0.5
    assert related.confidence_score > unrelated.confidence_score
    assert "password" in related.shared_terms


def test_unrelated_pair_has_zero_confidence() -> None:
    result = score_trace_candidate(
        "The application shall export financial reports",
        "Authentication component",
        "Handles session login and access tokens",
        ArtifactType.UML_COMPONENT,
    )

    assert result.confidence_score == 0


def test_coverage_counts_only_accepted_links() -> None:
    requirement_one = SimpleNamespace(id=uuid4(), code="REQ-0001")
    requirement_two = SimpleNamespace(id=uuid4(), code="REQ-0002")
    artifact_one = SimpleNamespace(id=uuid4(), code="ART-0001")
    artifact_two = SimpleNamespace(id=uuid4(), code="ART-0002")
    links = [
        SimpleNamespace(
            requirement_id=requirement_one.id,
            artifact_id=artifact_one.id,
            status=TraceLinkStatus.ACCEPTED,
        ),
        SimpleNamespace(
            requirement_id=requirement_two.id,
            artifact_id=artifact_two.id,
            status=TraceLinkStatus.SUGGESTED,
        ),
    ]

    coverage = calculate_coverage(
        [requirement_one, requirement_two],
        [artifact_one, artifact_two],
        links,
    )

    assert coverage["requirement_coverage_percent"] == 50.0
    assert coverage["artifact_coverage_percent"] == 50.0
    assert coverage["accepted_links"] == 1
    assert coverage["suggested_links"] == 1
    assert coverage["uncovered_requirement_codes"] == ["REQ-0002"]
