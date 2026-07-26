from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.test_case import (
    TestCasePriority as CasePriority,
)
from app.models.test_case import (
    TestCaseType as CaseType,
)
from app.schemas.test_case import (
    TestCaseCreate as CaseCreate,
)
from app.schemas.test_case import (
    TestCaseGenerateRequest as CaseGenerateRequest,
)


def valid_payload(**overrides):
    data = dict(
        requirement_id=uuid4(),
        title="Secure document upload validation",
        objective="Verify that document uploads enforce security rules.",
        preconditions="User is authenticated.",
        test_data="PDF and executable sample files.",
        overall_expected_result="Only supported safe files are accepted.",
        test_type="security",
        priority="critical",
        status="draft",
        steps=[
            {
                "action": "Upload a supported PDF.",
                "expected_result": "The PDF is accepted.",
            }
        ],
    )
    data.update(overrides)
    return CaseCreate(**data)


def test_test_case_accepts_traceability_and_steps():
    payload = valid_payload()
    assert payload.test_type == CaseType.SECURITY
    assert payload.priority == CasePriority.CRITICAL
    assert len(payload.steps) == 1


def test_rejected_test_case_requires_reason():
    with pytest.raises(ValidationError):
        valid_payload(status="rejected", rejection_reason="")


def test_generation_requires_at_least_one_scenario():
    with pytest.raises(ValidationError):
        CaseGenerateRequest(requirement_id=uuid4(), test_types=[])
