from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.test_case import TestCasePriority, TestCaseSource, TestCaseStatus, TestCaseType

class TestStepCreate(BaseModel):
    action: str = Field(min_length=2, max_length=2000)
    expected_result: str = Field(min_length=2, max_length=2000)

class TestStepRead(TestStepCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    position: int

class TestCaseCreate(BaseModel):
    requirement_id: UUID | None = None
    title: str = Field(min_length=3, max_length=200)
    objective: str = Field(min_length=5, max_length=4000)
    preconditions: str | None = Field(default=None, max_length=4000)
    test_data: str | None = Field(default=None, max_length=4000)
    overall_expected_result: str = Field(min_length=3, max_length=4000)
    test_type: TestCaseType = TestCaseType.FUNCTIONAL
    priority: TestCasePriority = TestCasePriority.MEDIUM
    status: TestCaseStatus = TestCaseStatus.DRAFT
    source: TestCaseSource = TestCaseSource.MANUAL
    generation_explanation: str | None = None
    reviewer_name: str | None = Field(default=None, max_length=160)
    review_comments: str | None = None
    rejection_reason: str | None = None
    steps: list[TestStepCreate] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_review(self):
        if self.status == TestCaseStatus.REJECTED and not (self.rejection_reason or "").strip():
            raise ValueError("Rejection reason is required for rejected test cases")
        return self

class TestCaseUpdate(TestCaseCreate):
    change_note: str | None = Field(default=None, max_length=500)

class TestCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    requirement_id: UUID | None
    code: str
    title: str
    objective: str
    preconditions: str | None
    test_data: str | None
    overall_expected_result: str
    test_type: TestCaseType
    priority: TestCasePriority
    status: TestCaseStatus
    source: TestCaseSource
    generation_explanation: str | None
    reviewer_name: str | None
    review_comments: str | None
    rejection_reason: str | None
    version: int
    steps: list[TestStepRead]
    created_at: datetime
    updated_at: datetime

class TestCaseSummary(BaseModel):
    total: int
    approved: int
    in_review: int
    needs_review: int
    ai_generated: int
    requirement_count: int
    covered_requirements: int
    coverage_percent: float

class TestCaseGenerateRequest(BaseModel):
    requirement_id: UUID
    test_types: list[TestCaseType] = Field(default_factory=lambda: [TestCaseType.FUNCTIONAL], min_length=1, max_length=8)
