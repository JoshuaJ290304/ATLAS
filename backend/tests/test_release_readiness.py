from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.release_readiness import ReleaseReadinessLabel
from app.schemas.release_readiness import ReleaseCandidateCreate, ReleaseComparisonCreate
from app.services.release_readiness import compare_release_snapshots, evaluate_release_evidence


def healthy_evidence() -> dict[str, object]:
    return {
        "baseline_selected": True,
        "baseline_active": True,
        "selected_requirement_count": 4,
        "approved_requirement_count": 4,
        "unapproved_requirement_codes": [],
        "critical_ambiguity_count": 0,
        "critical_ambiguity_codes": [],
        "traceability_percent": 100.0,
        "untraced_requirement_codes": [],
        "approved_test_coverage_percent": 100.0,
        "untested_requirement_codes": [],
        "high_risk_impact_count": 0,
        "high_risk_requirement_codes": [],
        "overdue_review_count": 0,
        "overdue_review_codes": [],
        "rejected_artifact_count": 0,
        "rejected_artifact_codes": [],
        "document_count": 2,
        "processed_document_count": 2,
        "failed_document_count": 0,
        "ai_index_ready": True,
        "ai_index_fresh": True,
    }


def evaluate(evidence: dict[str, object]):
    return evaluate_release_evidence(
        evidence,
        minimum_traceability_percent=80,
        minimum_test_coverage_percent=80,
        maximum_high_risk_impacts=0,
        maximum_overdue_reviews=0,
        require_active_baseline=True,
        require_approved_requirements=True,
    )


def test_complete_evidence_is_release_ready() -> None:
    result = evaluate(healthy_evidence())

    assert result["readiness_label"] == ReleaseReadinessLabel.READY.value
    assert result["readiness_score"] == 100.0
    assert result["blockers"] == []
    assert result["gate_summary"]["passed"] == 10


def test_missing_baseline_and_low_coverage_block_release() -> None:
    evidence = healthy_evidence()
    evidence.update(
        {
            "baseline_selected": False,
            "baseline_active": False,
            "traceability_percent": 25.0,
            "untraced_requirement_codes": ["REQ-0002", "REQ-0003", "REQ-0004"],
            "approved_test_coverage_percent": 50.0,
            "untested_requirement_codes": ["REQ-0003", "REQ-0004"],
        }
    )

    result = evaluate(evidence)

    assert result["readiness_label"] == ReleaseReadinessLabel.BLOCKED.value
    blocker_keys = {blocker["gate"] for blocker in result["blockers"]}
    assert {"active_baseline", "traceability_coverage", "approved_test_coverage"} <= blocker_keys
    assert result["readiness_score"] < 80


def test_near_threshold_coverage_is_warning_not_blocker() -> None:
    evidence = healthy_evidence()
    evidence["traceability_percent"] = 75.0

    result = evaluate(evidence)
    trace_gate = next(gate for gate in result["gate_results"] if gate["key"] == "traceability_coverage")

    assert trace_gate["status"] == "warning"
    assert not any(blocker["gate"] == "traceability_coverage" for blocker in result["blockers"])
    assert result["readiness_label"] == ReleaseReadinessLabel.AT_RISK.value


def test_release_payload_requires_unique_requirement_selection() -> None:
    requirement_id = uuid4()

    with pytest.raises(ValidationError):
        ReleaseCandidateCreate(
            name="ATLAS Release Candidate",
            version_label="1.0.0-rc.1",
            release_owner="Joshua J",
            selected_requirement_ids=[requirement_id, requirement_id],
        )


def test_release_comparison_requires_two_distinct_candidates() -> None:
    release_id = uuid4()

    with pytest.raises(ValidationError):
        ReleaseComparisonCreate(source_release_id=release_id, target_release_id=release_id)


def test_release_comparison_reports_selection_and_gate_changes() -> None:
    source = {
        "selected_requirement_ids": ["r1", "r2"],
        "selected_test_case_ids": ["t1"],
        "readiness_score": 62.5,
        "readiness_label": "blocked",
        "gate_results": [{"key": "coverage", "name": "Coverage", "status": "failed", "measured_value": 50}],
    }
    target = {
        "selected_requirement_ids": ["r1", "r2", "r3"],
        "selected_test_case_ids": ["t1", "t2"],
        "readiness_score": 90.0,
        "readiness_label": "ready",
        "gate_results": [{"key": "coverage", "name": "Coverage", "status": "passed", "measured_value": 100}],
    }

    comparison = compare_release_snapshots(source, target)

    assert comparison["requirements_added"] == ["r3"]
    assert comparison["test_cases_added"] == ["t2"]
    assert comparison["readiness_score_change"] == 27.5
    assert comparison["gate_changes"][0]["source_status"] == "failed"
    assert comparison["gate_changes"][0]["target_status"] == "passed"
