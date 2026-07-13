from types import SimpleNamespace
from uuid import uuid4

from app.models.artifact import ArtifactType
from app.models.impact import ImpactSeverity, RequirementChangeType
from app.models.requirement import RequirementStatus, RequirementType
from app.models.trace_link import TraceLinkStatus, TraceLinkType
from app.services.impact import (
    assess_risk,
    build_change_summary,
    build_impact_graph,
    compare_versions,
)


def version(**overrides):
    values = {
        "version": 1,
        "title": "Reset forgotten password",
        "description": "The system shall allow a registered user to reset a forgotten password.",
        "requirement_type": RequirementType.FUNCTIONAL,
        "non_functional_category": None,
        "status": RequirementStatus.REVIEWED,
        "ambiguity_score": 0,
        "ambiguity_flags": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_compare_versions_detects_text_change_and_terms() -> None:
    baseline = version()
    target = version(
        version=2,
        description=(
            "The system shall allow a registered user to reset a forgotten password "
            "using a secure token that expires after 15 minutes."
        ),
    )

    comparison = compare_versions(baseline, target)

    assert comparison.change_type == RequirementChangeType.MODIFIED
    assert comparison.changed_fields == ["description"]
    assert comparison.change_ratio > 0
    assert {"secure", "token", "15", "minutes"}.issubset(comparison.added_terms)
    assert comparison.unified_diff


def test_compare_versions_detects_reclassification() -> None:
    baseline = version()
    target = version(
        version=2,
        requirement_type=RequirementType.NON_FUNCTIONAL,
        non_functional_category="security",
    )

    comparison = compare_versions(baseline, target)

    assert comparison.change_type == RequirementChangeType.RECLASSIFIED
    assert "requirement_type" in comparison.changed_fields
    assert "non_functional_category" in comparison.changed_fields


def test_build_impact_graph_finds_direct_and_transitive_artifacts() -> None:
    changed = SimpleNamespace(id=uuid4(), code="REQ-0001", title="Password reset")
    bridge = SimpleNamespace(id=uuid4(), code="REQ-0002", title="Authentication audit")
    api = SimpleNamespace(
        id=uuid4(),
        code="ART-0001",
        name="Password reset API",
        artifact_type=ArtifactType.API,
    )
    table = SimpleNamespace(
        id=uuid4(),
        code="ART-0002",
        name="Audit log table",
        artifact_type=ArtifactType.DATABASE_TABLE,
    )
    links = [
        SimpleNamespace(
            requirement_id=changed.id,
            artifact_id=api.id,
            status=TraceLinkStatus.ACCEPTED,
            link_type=TraceLinkType.IMPLEMENTS,
            confidence_score=0.9,
        ),
        SimpleNamespace(
            requirement_id=bridge.id,
            artifact_id=api.id,
            status=TraceLinkStatus.ACCEPTED,
            link_type=TraceLinkType.IMPLEMENTS,
            confidence_score=0.8,
        ),
        SimpleNamespace(
            requirement_id=bridge.id,
            artifact_id=table.id,
            status=TraceLinkStatus.ACCEPTED,
            link_type=TraceLinkType.STORES,
            confidence_score=1.0,
        ),
    ]

    graph = build_impact_graph(changed.id, [changed, bridge], [api, table], links)

    assert [item["code"] for item in graph.direct_artifacts] == ["ART-0001"]
    assert [item["code"] for item in graph.transitive_artifacts] == ["ART-0002"]
    assert graph.transitive_artifacts[0]["path"] == [
        "REQ-0001",
        "ART-0001",
        "REQ-0002",
        "ART-0002",
    ]


def test_suggested_links_do_not_enter_impact_graph() -> None:
    changed = SimpleNamespace(id=uuid4(), code="REQ-0001", title="Export report")
    artifact = SimpleNamespace(
        id=uuid4(),
        code="ART-0001",
        name="Report API",
        artifact_type=ArtifactType.API,
    )
    link = SimpleNamespace(
        requirement_id=changed.id,
        artifact_id=artifact.id,
        status=TraceLinkStatus.SUGGESTED,
        link_type=TraceLinkType.IMPLEMENTS,
        confidence_score=0.8,
    )

    graph = build_impact_graph(changed.id, [changed], [artifact], [link])

    assert graph.direct_artifacts == []
    assert graph.transitive_artifacts == []


def test_risk_assessment_is_reproducible() -> None:
    comparison = compare_versions(
        version(),
        version(
            version=2,
            description=(
                "The system shall encrypt password reset tokens and expire them "
                "in 15 minutes."
            ),
            requirement_type=RequirementType.NON_FUNCTIONAL,
            non_functional_category="security",
            status=RequirementStatus.APPROVED,
        ),
    )
    direct = [
        {"artifact_type": "api"},
        {"artifact_type": "database_table"},
        {"artifact_type": "test_case"},
    ]
    transitive = [{"artifact_type": "uml_component"}, {"artifact_type": "test_case"}]

    first = assess_risk(comparison, version(
        version=2,
        requirement_type=RequirementType.NON_FUNCTIONAL,
        non_functional_category="security",
        status=RequirementStatus.APPROVED,
        ambiguity_score=2,
    ), direct, transitive)
    second = assess_risk(comparison, version(
        version=2,
        requirement_type=RequirementType.NON_FUNCTIONAL,
        non_functional_category="security",
        status=RequirementStatus.APPROVED,
        ambiguity_score=2,
    ), direct, transitive)

    assert first == second
    assert first.risk_score >= 50
    assert first.severity in {ImpactSeverity.HIGH, ImpactSeverity.CRITICAL}
    assert sum(item["points"] for item in first.factors) == first.risk_score


def test_change_summary_contains_versions_counts_and_risk() -> None:
    comparison = compare_versions(version(), version(version=2, title="Secure password reset"))
    risk = assess_risk(comparison, version(version=2), [], [])

    summary = build_change_summary("REQ-0001", 1, 2, comparison, 2, 1, risk)

    assert "version 1 to 2" in summary
    assert "2 directly affected" in summary
    assert "1 transitive" in summary
    assert f"{risk.risk_score}/100" in summary
