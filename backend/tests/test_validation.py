import pytest
from pydantic import ValidationError

from app.models.artifact import ArtifactType
from app.models.requirement import RequirementType
from app.schemas.assistant import AssistantAskRequest
from app.schemas.project import ProjectCreate
from app.schemas.requirement import RequirementCreate
from app.schemas.traceability import ArtifactCreate
from app.schemas.user import UserCreate


def test_project_name_is_trimmed_and_blank_is_rejected() -> None:
    assert ProjectCreate(name="  Atlas Demo  ").name == "Atlas Demo"
    with pytest.raises(ValidationError):
        ProjectCreate(name="   ")


def test_registration_requires_a_strong_password() -> None:
    with pytest.raises(ValidationError):
        UserCreate(name="Joshua", email="joshua@example.com", password="password")
    valid = UserCreate(
        name=" Joshua J ",
        email="JOSHUA@example.com",
        password="Atlas2026",
    )
    assert valid.name == "Joshua J"
    assert valid.email == "joshua@example.com"


def test_non_functional_requirement_requires_category() -> None:
    with pytest.raises(ValidationError):
        RequirementCreate(
            title="Response time",
            description="The system shall respond within two seconds.",
            requirement_type=RequirementType.NON_FUNCTIONAL,
        )


def test_artifact_and_assistant_text_are_normalized() -> None:
    artifact = ArtifactCreate(
        name="  Password API  ",
        artifact_type=ArtifactType.API,
        description="  Resets   a password securely. ",
    )
    assert artifact.name == "Password API"
    assert artifact.description == "Resets a password securely."
    assert AssistantAskRequest(question="  What   changed?  ").question == "What changed?"
