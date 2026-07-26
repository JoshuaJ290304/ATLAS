from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
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


class ReleaseCandidateStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    READY = "ready"
    BLOCKED = "blocked"
    RELEASED = "released"
    ARCHIVED = "archived"


class ReleaseReadinessLabel(StrEnum):
    READY = "ready"
    AT_RISK = "at_risk"
    BLOCKED = "blocked"
    NOT_EVALUATED = "not_evaluated"


class QualityGateStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_EVALUATED = "not_evaluated"


class ReleaseCandidate(TimestampMixin, Base):
    __tablename__ = "release_candidates"
    __table_args__ = (
        UniqueConstraint("project_id", "version_label", name="uq_release_candidates_version"),
        Index("ix_release_candidates_project_status", "project_id", "status"),
        Index("ix_release_candidates_project_updated", "project_id", "updated_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    baseline_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("project_baselines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    version_label: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    release_owner: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[ReleaseCandidateStatus] = mapped_column(
        Enum(
            ReleaseCandidateStatus,
            name="release_candidate_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=ReleaseCandidateStatus.DRAFT,
        nullable=False,
    )

    selected_requirement_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    selected_test_case_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    minimum_traceability_percent: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    minimum_test_coverage_percent: Mapped[float] = mapped_column(
        Float, default=80.0, nullable=False
    )
    maximum_high_risk_impacts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    maximum_overdue_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    require_active_baseline: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    require_approved_requirements: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    readiness_label: Mapped[ReleaseReadinessLabel] = mapped_column(
        Enum(
            ReleaseReadinessLabel,
            name="release_readiness_label",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=ReleaseReadinessLabel.NOT_EVALUATED,
        nullable=False,
    )
    gate_summary: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)
    blockers: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reviewer_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    review_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    signed_off_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    release_snapshot: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)

    project = relationship("Project", back_populates="release_candidates")
    baseline = relationship("ProjectBaseline")
    evaluations = relationship(
        "ReleaseGateEvaluation",
        back_populates="release_candidate",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ReleaseGateEvaluation.created_at",
    )


class ReleaseGateEvaluation(Base):
    __tablename__ = "release_gate_evaluations"
    __table_args__ = (
        Index(
            "ix_release_gate_evaluations_candidate_created", "release_candidate_id", "created_at"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    release_candidate_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("release_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evaluated_by_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    readiness_score: Mapped[float] = mapped_column(Float, nullable=False)
    readiness_label: Mapped[ReleaseReadinessLabel] = mapped_column(
        Enum(
            ReleaseReadinessLabel,
            name="release_readiness_label",
            values_callable=lambda values: [value.value for value in values],
            create_type=False,
        ),
        nullable=False,
    )
    gate_results: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    evidence: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)
    blockers: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    release_candidate = relationship("ReleaseCandidate", back_populates="evaluations")
