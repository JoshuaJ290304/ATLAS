from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectDeleteConfirm


def test_project_delete_confirmation_normalizes_outer_whitespace():
    payload = ProjectDeleteConfirm(project_name="  SecureBank Online Banking  ")
    assert payload.project_name == "SecureBank Online Banking"


def test_project_delete_confirmation_rejects_blank_value():
    with pytest.raises(ValidationError):
        ProjectDeleteConfirm(project_name="   ")


def test_project_delete_confirmation_requires_a_string():
    with pytest.raises(ValidationError):
        ProjectDeleteConfirm(project_name=uuid4())
