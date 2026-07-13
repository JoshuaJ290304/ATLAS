from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Enum, Float, ForeignKey, Index, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class TraceLinkType(StrEnum):
    IMPLEMENTS = "implements"
    STORES = "stores"
    VERIFIES = "verifies"
    REPRESENTS = "represents"
    RELATES_TO = "relates_to"


class TraceLinkStatus(StrEnum):
    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TraceLinkSource(StrEnum):
    MANUAL = "manual"
    SYSTEM = "system"


class TraceLink(TimestampMixin, Base):
    __tablename__ = "trace_links"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "requirement_id",
            "artifact_id",
            name="uq_trace_links_project_requirement_artifact",
        ),
        Index("ix_trace_links_project_status", "project_id", "status"),
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
    artifact_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    link_type: Mapped[TraceLinkType] = mapped_column(
        Enum(
            TraceLinkType,
            name="trace_link_type",
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    status: Mapped[TraceLinkStatus] = mapped_column(
        Enum(
            TraceLinkStatus,
            name="trace_link_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=TraceLinkStatus.SUGGESTED,
        nullable=False,
    )
    source: Mapped[TraceLinkSource] = mapped_column(
        Enum(
            TraceLinkSource,
            name="trace_link_source",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=TraceLinkSource.SYSTEM,
        nullable=False,
    )
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    evidence: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)

    project = relationship("Project", back_populates="trace_links")
    requirement = relationship("Requirement", back_populates="trace_links")
    artifact = relationship("Artifact", back_populates="trace_links")
