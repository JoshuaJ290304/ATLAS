from app.services.analytics import HealthInputs, calculate_project_health


def test_health_score_rewards_complete_project() -> None:
    health = calculate_project_health(
        HealthInputs(
            document_total=2,
            document_extracted=2,
            requirement_total=10,
            reviewed_or_approved=10,
            ambiguous=0,
            artifact_total=5,
            requirement_coverage=100,
            artifact_coverage=100,
            impact_total=3,
            high_or_critical_impacts=0,
            assistant_index_ready=True,
        )
    )
    assert health.score == 100
    assert health.grade == "excellent"
    assert len(health.factors) == 6


def test_health_score_identifies_missing_foundations() -> None:
    health = calculate_project_health(
        HealthInputs(
            document_total=0,
            document_extracted=0,
            requirement_total=0,
            reviewed_or_approved=0,
            ambiguous=0,
            artifact_total=0,
            requirement_coverage=0,
            artifact_coverage=0,
            impact_total=0,
            high_or_critical_impacts=0,
            assistant_index_ready=False,
        )
    )
    assert health.score == 0
    assert health.grade == "needs_attention"
    assert "document" in health.summary.lower()


def test_health_score_penalizes_ambiguity_and_high_risk() -> None:
    healthy = calculate_project_health(HealthInputs(1, 1, 10, 10, 0, 4, 100, 100, 2, 0, True))
    weaker = calculate_project_health(HealthInputs(1, 1, 10, 4, 7, 4, 50, 25, 2, 2, False))
    assert weaker.score < healthy.score
    assert weaker.factors[1].score < healthy.factors[1].score
