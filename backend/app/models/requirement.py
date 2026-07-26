from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RequirementType(StrEnum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"


class RequirementStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class RequirementSource(StrEnum):
    EXTRACTED = "extracted"
    MANUAL = "manual"


class Requirement(TimestampMixin, Base):
    __tablename__ = "requirements"
    __table_args__ = (
        UniqueConstraint("project_id", "code", name="uq_requirements_project_code"),
        Index("ix_requirements_project_type", "project_id", "requirement_type"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source_document_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_type: Mapped[RequirementType] = mapped_column(
        Enum(
            RequirementType,
            name="requirement_type",
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    non_functional_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[RequirementStatus] = mapped_column(
        Enum(
            RequirementStatus,
            name="requirement_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=RequirementStatus.DRAFT,
        nullable=False,
    )
    source: Mapped[RequirementSource] = mapped_column(
        Enum(
            RequirementSource,
            name="requirement_source",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=RequirementSource.EXTRACTED,
        nullable=False,
    )
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    ambiguity_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ambiguity_flags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    project = relationship("Project", back_populates="requirements")
    source_document = relationship("Document", back_populates="requirements")
    versions = relationship(
        "RequirementVersion",
        back_populates="requirement",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RequirementVersion.version",
    )
    impact_analyses = relationship(
        "ImpactAnalysis",
        back_populates="requirement",
        passive_deletes=True,
    )
    trace_links = relationship(
        "TraceLink",
        back_populates="requirement",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    reviews = relationship(
        "RequirementReview",
        back_populates="requirement",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RequirementReview.created_at",
    )

    comments = relationship(
        "RequirementComment",
        back_populates="requirement",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RequirementComment.created_at",
    )

    baseline_items = relationship(
        "BaselineRequirement",
        back_populates="requirement",
        passive_deletes=True,
    )


# Milestone 9 requirement-to-test traceability.
Requirement.test_cases = relationship(
    "TestCase", back_populates="requirement", passive_deletes=True
)
