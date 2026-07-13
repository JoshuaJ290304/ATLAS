from types import SimpleNamespace
from uuid import uuid4

from app.models.artifact import ArtifactType
from app.models.assistant import KnowledgeSourceType
from app.models.document import DocumentStatus
from app.models.impact import ImpactSeverity
from app.models.requirement import RequirementStatus, RequirementType
from app.services.assistant import (
    RetrievedChunk,
    build_grounded_prompt,
    build_project_drafts,
    build_retrieval_fallback,
    chunk_text,
    estimate_tokens,
    normalize_text,
)


def test_normalize_text_preserves_paragraph_boundaries() -> None:
    value = " First   line\r\ncontinues here\r\n\r\n Second paragraph "

    assert normalize_text(value) == "First line continues here\n\nSecond paragraph"


def test_chunk_text_respects_limit_and_overlap() -> None:
    text = " ".join(f"word{index}" for index in range(500))

    chunks = chunk_text(text, max_chars=320, overlap_chars=40)

    assert len(chunks) > 5
    assert all(1 <= len(item) <= 320 for item in chunks)
    assert chunks[0] != chunks[1]


def test_estimate_tokens_has_minimum_and_scales() -> None:
    assert estimate_tokens("") == 1
    assert estimate_tokens("a" * 400) == 100


def test_build_project_drafts_indexes_all_project_source_types() -> None:
    document = SimpleNamespace(
        id=uuid4(),
        original_filename="SRS.pdf",
        extracted_text="The system shall support password reset. " * 30,
        page_count=2,
        status=DocumentStatus.EXTRACTED,
    )
    requirement = SimpleNamespace(
        id=uuid4(),
        code="REQ-0001",
        title="Reset password",
        description="The user shall reset a forgotten password.",
        requirement_type=RequirementType.FUNCTIONAL,
        non_functional_category=None,
        status=RequirementStatus.APPROVED,
        ambiguity_score=0,
        version=2,
    )
    artifact = SimpleNamespace(
        id=uuid4(),
        code="ART-0001",
        name="Password Reset API",
        artifact_type=ArtifactType.API,
        description="Issues and validates reset tokens.",
        technical_details={"method": "POST", "path": "/password-reset"},
    )
    analysis = SimpleNamespace(
        id=uuid4(),
        requirement_code="REQ-0001",
        requirement_title="Reset password",
        baseline_version=1,
        target_version=2,
        severity=ImpactSeverity.HIGH,
        risk_score=72,
        change_summary="Token expiry was added.",
        direct_artifacts=[{"name": "Password Reset API"}],
        transitive_artifacts=[],
    )

    drafts = build_project_drafts([document], [requirement], [artifact], [analysis])
    types = {item.source_type for item in drafts}

    assert types == {
        KnowledgeSourceType.DOCUMENT,
        KnowledgeSourceType.REQUIREMENT,
        KnowledgeSourceType.ARTIFACT,
        KnowledgeSourceType.IMPACT_ANALYSIS,
    }
    assert len({item.vector_id for item in drafts}) == len(drafts)


def test_grounded_prompt_numbers_sources_and_preserves_history() -> None:
    citation = RetrievedChunk(
        chunk_id=uuid4(),
        source_type=KnowledgeSourceType.REQUIREMENT,
        source_id=uuid4(),
        source_label="REQ-0001 — Reset password",
        chunk_index=0,
        excerpt="The system shall expire reset tokens after 15 minutes.",
        relevance_score=0.91,
        source_metadata={"code": "REQ-0001"},
    )

    messages = build_grounded_prompt(
        "How long is the token valid?",
        [citation],
        [("user", "What is password reset?"), ("assistant", "It is REQ-0001.")],
    )

    assert messages[0]["role"] == "system"
    assert "[1] requirement: REQ-0001" in messages[0]["content"]
    assert messages[-1] == {"role": "user", "content": "How long is the token valid?"}
    assert len(messages) == 4


def test_retrieval_fallback_is_explicit_and_cited() -> None:
    citation = RetrievedChunk(
        chunk_id=uuid4(),
        source_type=KnowledgeSourceType.DOCUMENT,
        source_id=uuid4(),
        source_label="SRS.pdf",
        chunk_index=0,
        excerpt="The system shall retain audit records for one year.",
        relevance_score=0.82,
        source_metadata={},
    )

    answer = build_retrieval_fallback("How long are audit records retained?", [citation])

    assert "Ollama is unavailable" in answer
    assert "[1] SRS.pdf" in answer
    assert "one year" in answer
