from app.services.governance import compare_baseline_snapshots


def test_baseline_comparison_identifies_all_change_types() -> None:
    baseline = [
        {
            "code": "REQ-0001",
            "title": "Login",
            "description": "The system shall allow login.",
            "requirement_type": "functional",
            "non_functional_category": None,
            "status": "approved",
            "version": 1,
        },
        {
            "code": "REQ-0002",
            "title": "Export",
            "description": "The system shall export reports.",
            "requirement_type": "functional",
            "non_functional_category": None,
            "status": "approved",
            "version": 1,
        },
        {
            "code": "REQ-0003",
            "title": "Removed",
            "description": "This requirement will be removed.",
            "requirement_type": "functional",
            "non_functional_category": None,
            "status": "approved",
            "version": 1,
        },
    ]
    current = [
        baseline[0],
        {
            **baseline[1],
            "description": "The system shall export PDF and CSV reports.",
            "version": 2,
        },
        {
            "code": "REQ-0004",
            "title": "Audit",
            "description": "The system shall retain an audit log.",
            "requirement_type": "functional",
            "non_functional_category": None,
            "status": "draft",
            "version": 1,
        },
    ]

    comparison = compare_baseline_snapshots(baseline, current)

    assert comparison["unchanged"] == ["REQ-0001"]
    assert comparison["modified"][0]["code"] == "REQ-0002"
    assert comparison["modified"][0]["changed_fields"] == ["description", "version"]
    assert comparison["removed"][0]["code"] == "REQ-0003"
    assert comparison["added"][0]["code"] == "REQ-0004"


from datetime import date, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.governance import BaselineStatus, ReviewPriority
from app.schemas.governance import (
    BaselineComparisonCreate,
    BaselineCreate,
    ReviewRequestCreate,
)


def test_review_request_accepts_priority_due_date_and_note() -> None:
    payload = ReviewRequestCreate(
        reviewer_id=uuid4(),
        priority="high",
        due_date=date.today() + timedelta(days=3),
        request_note="Verify security acceptance criteria.",
    )

    assert payload.priority == ReviewPriority.HIGH
    assert payload.due_date is not None
    assert payload.request_note == "Verify security acceptance criteria."


def test_baseline_accepts_status_and_selected_requirements() -> None:
    requirement_ids = [uuid4(), uuid4()]
    payload = BaselineCreate(
        name="Authentication Security Baseline",
        version_label="1.0.0",
        description="Approved authentication requirements.",
        status="active",
        requirement_ids=requirement_ids,
    )

    assert payload.status == BaselineStatus.ACTIVE
    assert payload.requirement_ids == requirement_ids


def test_baseline_comparison_requires_different_baselines() -> None:
    baseline_id = uuid4()

    with pytest.raises(ValidationError):
        BaselineComparisonCreate(
            source_baseline_id=baseline_id,
            target_baseline_id=baseline_id,
        )
