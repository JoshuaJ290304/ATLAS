from app.models.requirement import RequirementType
from app.services.requirements import (
    analyze_ambiguity,
    classify_requirement,
    extract_requirement_candidates,
    make_title,
    normalize_for_comparison,
)


def test_extracts_numbered_and_modal_requirements() -> None:
    text = """
    1. Introduction
    FR-01 The system shall allow a registered user to sign in using email and password.
    - The administrator must be able to deactivate a user account.
    Project overview and background
    """

    candidates = extract_requirement_candidates(text)

    assert len(candidates) == 2
    assert candidates[0].requirement_type == RequirementType.FUNCTIONAL
    assert candidates[0].confidence_score >= 0.8


def test_classifies_non_functional_security_requirement() -> None:
    requirement_type, category = classify_requirement(
        "The system shall encrypt personal data and enforce access control."
    )

    assert requirement_type == RequirementType.NON_FUNCTIONAL
    assert category == "security"


def test_flags_vague_non_functional_requirement() -> None:
    score, flags = analyze_ambiguity(
        "The application should provide a fast and user-friendly interface.",
        RequirementType.NON_FUNCTIONAL,
    )

    assert score >= 60
    assert "Uses subjective or unverifiable wording" in flags
    assert "Uses a weak modal instead of a binding obligation" in flags
    assert "Non-functional requirement lacks a measurable target" in flags


def test_measurable_non_functional_requirement_avoids_measurement_flag() -> None:
    _, flags = analyze_ambiguity(
        "The system shall respond within 2 seconds for 500 concurrent users.",
        RequirementType.NON_FUNCTIONAL,
    )

    assert "Non-functional requirement lacks a measurable target" not in flags


def test_normalization_and_title_are_stable() -> None:
    assert normalize_for_comparison("User shall Login!") == "user shall login"
    assert make_title("The system shall allow users to export reports.") == (
        "Allow users to export reports"
    )
