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
from app.models.requirement import RequirementStatus, RequirementType


class ImpactSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementChangeType(StrEnum):
    MODIFIED = "modified"
    RECLASSIFIED = "reclassified"
    STATUS_CHANGED = "status_changed"
    COMPLEX = "complex"


class RequirementVersion(Base):
    __tablename__ = "requirement_versions"
    __table_args__ = (
        UniqueConstraint(
            "requirement_id",
            "version",
            name="uq_requirement_versions_requirement_version",
        ),
        Index("ix_requirement_versions_project_requirement", "project_id", "requirement_id"),
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
    version: Mapped[int] = mapped_column(Integer, nullable=False)
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
        nullable=False,
    )
    ambiguity_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ambiguity_flags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project = relationship("Project", back_populates="requirement_versions")
    requirement = relationship("Requirement", back_populates="versions")


class ImpactAnalysis(TimestampMixin, Base):
    __tablename__ = "impact_analyses"
    __table_args__ = (
        Index("ix_impact_analyses_project_created", "project_id", "created_at"),
        Index("ix_impact_analyses_project_severity", "project_id", "severity"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requirement_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("requirements.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    requirement_code: Mapped[str] = mapped_column(String(32), nullable=False)
    requirement_title: Mapped[str] = mapped_column(String(180), nullable=False)
    baseline_version: Mapped[int] = mapped_column(Integer, nullable=False)
    target_version: Mapped[int] = mapped_column(Integer, nullable=False)
    change_type: Mapped[RequirementChangeType] = mapped_column(
        Enum(
            RequirementChangeType,
            name="requirement_change_type",
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[ImpactSeverity] = mapped_column(
        Enum(
            ImpactSeverity,
            name="impact_severity",
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    differences: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)
    direct_artifacts: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    transitive_artifacts: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    risk_factors: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, default=list, nullable=False
    )

    project = relationship("Project", back_populates="impact_analyses")
    requirement = relationship("Requirement", back_populates="impact_analyses")
