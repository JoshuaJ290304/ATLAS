from __future__ import annotations

from typing import Any

from app.models.release_readiness import QualityGateStatus, ReleaseReadinessLabel

GATE_WEIGHTS: dict[str, int] = {
    "active_baseline": 12,
    "approved_requirements": 16,
    "critical_ambiguities": 10,
    "traceability_coverage": 14,
    "approved_test_coverage": 16,
    "high_risk_impacts": 12,
    "overdue_reviews": 8,
    "rejected_artifacts": 5,
    "document_processing": 4,
    "ai_index_freshness": 3,
}

CRITICAL_GATES = {
    "active_baseline",
    "approved_requirements",
    "traceability_coverage",
    "approved_test_coverage",
    "high_risk_impacts",
}


def _gate(
    key: str,
    name: str,
    status: QualityGateStatus,
    measured_value: float | int | str | None,
    threshold: float | int | str | None,
    message: str,
    evidence: dict[str, object] | None = None,
    recommendation: str | None = None,
) -> dict[str, object]:
    return {
        "key": key,
        "name": name,
        "status": status.value,
        "critical": key in CRITICAL_GATES,
        "score_weight": GATE_WEIGHTS[key],
        "measured_value": measured_value,
        "threshold": threshold,
        "message": message,
        "evidence": evidence or {},
        "recommendation": recommendation,
    }


def evaluate_release_evidence(
    evidence: dict[str, Any],
    *,
    minimum_traceability_percent: float,
    minimum_test_coverage_percent: float,
    maximum_high_risk_impacts: int,
    maximum_overdue_reviews: int,
    require_active_baseline: bool,
    require_approved_requirements: bool,
) -> dict[str, object]:
    gates: list[dict[str, object]] = []

    baseline_selected = bool(evidence.get("baseline_selected"))
    baseline_active = bool(evidence.get("baseline_active"))
    if not require_active_baseline:
        gates.append(
            _gate(
                "active_baseline",
                "Active baseline",
                QualityGateStatus.NOT_EVALUATED,
                "optional",
                "active baseline required",
                "Active baseline enforcement is disabled.",
            )
        )
    elif baseline_selected and baseline_active:
        gates.append(
            _gate(
                "active_baseline",
                "Active baseline",
                QualityGateStatus.PASSED,
                "active",
                "active",
                "The selected release baseline is active.",
            )
        )
    else:
        gates.append(
            _gate(
                "active_baseline",
                "Active baseline",
                QualityGateStatus.FAILED,
                "missing" if not baseline_selected else "archived",
                "active",
                "Select an active project baseline before release.",
                recommendation=(
                    "Create or select an active baseline containing the release requirements."
                ),
            )
        )

    selected_requirements = int(evidence.get("selected_requirement_count", 0))
    approved_requirements = int(evidence.get("approved_requirement_count", 0))
    unapproved_codes = list(evidence.get("unapproved_requirement_codes", []))
    if not require_approved_requirements:
        gates.append(
            _gate(
                "approved_requirements",
                "Approved requirements",
                QualityGateStatus.NOT_EVALUATED,
                approved_requirements,
                selected_requirements,
                "Mandatory requirement approval is disabled.",
            )
        )
    elif selected_requirements > 0 and approved_requirements == selected_requirements:
        gates.append(
            _gate(
                "approved_requirements",
                "Approved requirements",
                QualityGateStatus.PASSED,
                approved_requirements,
                selected_requirements,
                "Every included requirement is approved.",
            )
        )
    else:
        gates.append(
            _gate(
                "approved_requirements",
                "Approved requirements",
                QualityGateStatus.FAILED,
                approved_requirements,
                selected_requirements,
                (
                    f"{selected_requirements - approved_requirements} included "
                    "requirement(s) are not approved."
                ),
                {"unapproved_codes": unapproved_codes},
                "Review and approve every included requirement or remove it from this release.",
            )
        )

    critical_ambiguities = int(evidence.get("critical_ambiguity_count", 0))
    ambiguous_codes = list(evidence.get("critical_ambiguity_codes", []))
    gates.append(
        _gate(
            "critical_ambiguities",
            "Critical ambiguity",
            QualityGateStatus.PASSED if critical_ambiguities == 0 else QualityGateStatus.FAILED,
            critical_ambiguities,
            0,
            "No included requirement has a critical ambiguity score."
            if critical_ambiguities == 0
            else f"{critical_ambiguities} requirement(s) have critical ambiguity.",
            {"requirement_codes": ambiguous_codes},
            None
            if critical_ambiguities == 0
            else "Resolve ambiguity findings and re-run requirement analysis.",
        )
    )

    traceability = float(evidence.get("traceability_percent", 0.0))
    trace_status = (
        QualityGateStatus.PASSED
        if traceability >= minimum_traceability_percent
        else QualityGateStatus.WARNING
        if traceability >= max(0, minimum_traceability_percent - 10)
        else QualityGateStatus.FAILED
    )
    gates.append(
        _gate(
            "traceability_coverage",
            "Requirement traceability",
            trace_status,
            round(traceability, 1),
            minimum_traceability_percent,
            f"Accepted traceability covers {traceability:.1f}% of included requirements.",
            {"uncovered_codes": list(evidence.get("untraced_requirement_codes", []))},
            None
            if trace_status == QualityGateStatus.PASSED
            else "Add or accept trace links for uncovered requirements.",
        )
    )

    test_coverage = float(evidence.get("approved_test_coverage_percent", 0.0))
    test_status = (
        QualityGateStatus.PASSED
        if test_coverage >= minimum_test_coverage_percent
        else QualityGateStatus.WARNING
        if test_coverage >= max(0, minimum_test_coverage_percent - 10)
        else QualityGateStatus.FAILED
    )
    gates.append(
        _gate(
            "approved_test_coverage",
            "Approved test coverage",
            test_status,
            round(test_coverage, 1),
            minimum_test_coverage_percent,
            f"Approved included tests cover {test_coverage:.1f}% of release requirements.",
            {"untested_codes": list(evidence.get("untested_requirement_codes", []))},
            None
            if test_status == QualityGateStatus.PASSED
            else "Approve test cases for uncovered release requirements.",
        )
    )

    high_risk = int(evidence.get("high_risk_impact_count", 0))
    impact_status = (
        QualityGateStatus.PASSED
        if high_risk <= maximum_high_risk_impacts
        else QualityGateStatus.FAILED
    )
    gates.append(
        _gate(
            "high_risk_impacts",
            "High-risk impacts",
            impact_status,
            high_risk,
            maximum_high_risk_impacts,
            f"{high_risk} current high or critical impact item(s) affect the release.",
            {"requirement_codes": list(evidence.get("high_risk_requirement_codes", []))},
            None
            if impact_status == QualityGateStatus.PASSED
            else "Resolve or explicitly accept high-risk impact findings before sign-off.",
        )
    )

    overdue = int(evidence.get("overdue_review_count", 0))
    overdue_status = (
        QualityGateStatus.PASSED if overdue <= maximum_overdue_reviews else QualityGateStatus.FAILED
    )
    gates.append(
        _gate(
            "overdue_reviews",
            "Overdue reviews",
            overdue_status,
            overdue,
            maximum_overdue_reviews,
            f"{overdue} pending included requirement review(s) are overdue.",
            {"requirement_codes": list(evidence.get("overdue_review_codes", []))},
            None
            if overdue_status == QualityGateStatus.PASSED
            else "Complete or reschedule overdue requirement reviews.",
        )
    )

    rejected = int(evidence.get("rejected_artifact_count", 0))
    gates.append(
        _gate(
            "rejected_artifacts",
            "Rejected artifacts",
            QualityGateStatus.PASSED if rejected == 0 else QualityGateStatus.FAILED,
            rejected,
            0,
            "No rejected requirements or test cases are included."
            if rejected == 0
            else f"{rejected} rejected artifact(s) are included.",
            {"artifact_codes": list(evidence.get("rejected_artifact_codes", []))},
            None
            if rejected == 0
            else "Remove rejected artifacts or return them to review and approve them.",
        )
    )

    document_total = int(evidence.get("document_count", 0))
    document_ready = int(evidence.get("processed_document_count", 0))
    document_failed = int(evidence.get("failed_document_count", 0))
    if document_total == 0:
        document_status = QualityGateStatus.WARNING
        document_message = "No source documents are attached to this project."
    elif document_failed > 0 or document_ready < document_total:
        document_status = QualityGateStatus.FAILED
        document_message = (
            f"{document_total - document_ready} of {document_total} "
            "document(s) are not successfully extracted."
        )
    else:
        document_status = QualityGateStatus.PASSED
        document_message = "All project documents are successfully processed."
    gates.append(
        _gate(
            "document_processing",
            "Document processing",
            document_status,
            document_ready,
            document_total,
            document_message,
            {"failed_count": document_failed},
            None
            if document_status == QualityGateStatus.PASSED
            else "Process or replace incomplete source documents.",
        )
    )

    ai_ready = bool(evidence.get("ai_index_ready"))
    ai_fresh = bool(evidence.get("ai_index_fresh"))
    if ai_ready and ai_fresh:
        ai_status = QualityGateStatus.PASSED
        ai_message = "The AI project index is ready and current."
    elif ai_ready:
        ai_status = QualityGateStatus.WARNING
        ai_message = "The AI index is ready but older than the latest project evidence."
    else:
        ai_status = QualityGateStatus.WARNING
        ai_message = "The AI project index is not ready."
    gates.append(
        _gate(
            "ai_index_freshness",
            "AI index freshness",
            ai_status,
            "fresh" if ai_ready and ai_fresh else "stale" if ai_ready else "not_ready",
            "fresh",
            ai_message,
            recommendation=None
            if ai_status == QualityGateStatus.PASSED
            else "Re-index the project knowledge base before final release review.",
        )
    )

    evaluable = [gate for gate in gates if gate["status"] != QualityGateStatus.NOT_EVALUATED.value]
    possible_weight = sum(int(gate["score_weight"]) for gate in evaluable)
    earned_weight = 0.0
    for gate in evaluable:
        status = gate["status"]
        weight = int(gate["score_weight"])
        if status == QualityGateStatus.PASSED.value:
            earned_weight += weight
        elif status == QualityGateStatus.WARNING.value:
            earned_weight += weight * 0.5
    score = round((earned_weight / possible_weight) * 100, 1) if possible_weight else 0.0

    blockers = [
        {
            "gate": gate["key"],
            "name": gate["name"],
            "message": gate["message"],
        }
        for gate in gates
        if gate["status"] == QualityGateStatus.FAILED.value and gate["critical"]
    ]
    failed_any = any(gate["status"] == QualityGateStatus.FAILED.value for gate in gates)
    warnings_any = any(gate["status"] == QualityGateStatus.WARNING.value for gate in gates)

    if blockers:
        label = ReleaseReadinessLabel.BLOCKED
    elif score >= 80 and not failed_any and not warnings_any:
        label = ReleaseReadinessLabel.READY
    else:
        label = ReleaseReadinessLabel.AT_RISK

    recommendations = list(
        dict.fromkeys(
            str(gate["recommendation"])
            for gate in gates
            if gate.get("recommendation")
            and gate["status"] in {QualityGateStatus.FAILED.value, QualityGateStatus.WARNING.value}
        )
    )

    status_counts = {
        status.value: sum(1 for gate in gates if gate["status"] == status.value)
        for status in QualityGateStatus
    }
    return {
        "readiness_score": score,
        "readiness_label": label.value,
        "gate_results": gates,
        "blockers": blockers,
        "recommendations": recommendations,
        "gate_summary": status_counts,
        "has_warnings": warnings_any,
    }


def compare_release_snapshots(source: dict[str, Any], target: dict[str, Any]) -> dict[str, object]:
    source_requirements = set(source.get("selected_requirement_ids", []))
    target_requirements = set(target.get("selected_requirement_ids", []))
    source_tests = set(source.get("selected_test_case_ids", []))
    target_tests = set(target.get("selected_test_case_ids", []))

    source_gates = {gate.get("key"): gate for gate in source.get("gate_results", [])}
    target_gates = {gate.get("key"): gate for gate in target.get("gate_results", [])}
    gate_changes: list[dict[str, object]] = []
    for key in sorted(set(source_gates) | set(target_gates)):
        before = source_gates.get(key, {})
        after = target_gates.get(key, {})
        if before.get("status") != after.get("status") or before.get("measured_value") != after.get(
            "measured_value"
        ):
            gate_changes.append(
                {
                    "key": key,
                    "name": after.get("name") or before.get("name") or key,
                    "source_status": before.get("status", "not_evaluated"),
                    "target_status": after.get("status", "not_evaluated"),
                    "source_value": before.get("measured_value"),
                    "target_value": after.get("measured_value"),
                }
            )

    return {
        "requirements_added": sorted(target_requirements - source_requirements),
        "requirements_removed": sorted(source_requirements - target_requirements),
        "test_cases_added": sorted(target_tests - source_tests),
        "test_cases_removed": sorted(source_tests - target_tests),
        "readiness_score_change": round(
            float(target.get("readiness_score", 0)) - float(source.get("readiness_score", 0)), 1
        ),
        "readiness_label_change": (
            f"{source.get('readiness_label', 'not_evaluated')} → "
            f"{target.get('readiness_label', 'not_evaluated')}"
        ),
        "gate_changes": gate_changes,
    }
