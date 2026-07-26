from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class TestCaseStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    ARCHIVED = "archived"


class TestCasePriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TestCaseType(StrEnum):
    FUNCTIONAL = "functional"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    SECURITY = "security"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    REGRESSION = "regression"


class TestCaseSource(StrEnum):
    MANUAL = "manual"
    AI_GENERATED = "ai_generated"


class TestCase(TimestampMixin, Base):
    __tablename__ = "test_cases"
    __table_args__ = (
        Index("ix_test_cases_project_status", "project_id", "status"),
        Index("ix_test_cases_requirement", "requirement_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requirement_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    preconditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_expected_result: Mapped[str] = mapped_column(Text, nullable=False)
    test_type: Mapped[TestCaseType] = mapped_column(
        Enum(TestCaseType, name="test_case_type", values_callable=lambda x: [v.value for v in x]),
        nullable=False,
    )
    priority: Mapped[TestCasePriority] = mapped_column(
        Enum(
            TestCasePriority,
            name="test_case_priority",
            values_callable=lambda x: [v.value for v in x],
        ),
        default=TestCasePriority.MEDIUM,
        nullable=False,
    )
    status: Mapped[TestCaseStatus] = mapped_column(
        Enum(
            TestCaseStatus, name="test_case_status", values_callable=lambda x: [v.value for v in x]
        ),
        default=TestCaseStatus.DRAFT,
        nullable=False,
    )
    source: Mapped[TestCaseSource] = mapped_column(
        Enum(
            TestCaseSource, name="test_case_source", values_callable=lambda x: [v.value for v in x]
        ),
        default=TestCaseSource.MANUAL,
        nullable=False,
    )
    generation_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    review_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    project = relationship("Project", back_populates="test_cases")
    requirement = relationship("Requirement", back_populates="test_cases")
    steps = relationship(
        "TestStep",
        back_populates="test_case",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TestStep.position",
    )
    versions = relationship(
        "TestCaseVersion",
        back_populates="test_case",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TestCaseVersion.version",
    )


class TestStep(Base):
    __tablename__ = "test_steps"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    test_case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[str] = mapped_column(Text, nullable=False)
    test_case = relationship("TestCase", back_populates="steps")


class TestCaseVersion(TimestampMixin, Base):
    __tablename__ = "test_case_versions"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    test_case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    change_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_case = relationship("TestCase", back_populates="versions")
