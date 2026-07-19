from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RequirementReview(TimestampMixin, Base):
    __tablename__ = "requirement_reviews"
    __table_args__ = (
        Index("ix_requirement_reviews_project_status", "project_id", "status"),
        Index("ix_requirement_reviews_requirement_created", "requirement_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requirement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    reviewer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    requested_by_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(
            ReviewStatus,
            name="governance_review_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=ReviewStatus.PENDING,
        nullable=False,
    )
    request_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="requirement_reviews")
    requirement = relationship("Requirement", back_populates="reviews")
    reviewer = relationship(
        "User",
        foreign_keys=[reviewer_id],
        back_populates="assigned_requirement_reviews",
    )
    requested_by = relationship(
        "User",
        foreign_keys=[requested_by_id],
        back_populates="requested_requirement_reviews",
    )


class RequirementComment(TimestampMixin, Base):
    __tablename__ = "requirement_comments"
    __table_args__ = (
        Index("ix_requirement_comments_requirement_created", "requirement_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requirement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    author_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    project = relationship("Project", back_populates="requirement_comments")
    requirement = relationship("Requirement", back_populates="comments")
    author = relationship("User", back_populates="requirement_comments")


class ProjectBaseline(TimestampMixin, Base):
    __tablename__ = "project_baselines"
    __table_args__ = (
        UniqueConstraint("project_id", "version_label", name="uq_project_baselines_version"),
        Index("ix_project_baselines_project_created", "project_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    created_by_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    version_label: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirement_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    project = relationship("Project", back_populates="baselines")
    created_by = relationship("User", back_populates="created_baselines")
    items = relationship(
        "BaselineRequirement",
        back_populates="baseline",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="BaselineRequirement.code",
    )


class BaselineRequirement(Base):
    __tablename__ = "baseline_requirements"
    __table_args__ = (
        UniqueConstraint("baseline_id", "code", name="uq_baseline_requirements_code"),
        Index("ix_baseline_requirements_baseline_code", "baseline_id", "code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    baseline_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("project_baselines.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requirement_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirements.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    requirement_version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_data: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    baseline = relationship("ProjectBaseline", back_populates="items")
    requirement = relationship("Requirement", back_populates="baseline_items")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_project_created", "project_id", "created_at"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    actor_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    details: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project = relationship("Project", back_populates="audit_logs")
    actor = relationship("User", back_populates="audit_logs")
