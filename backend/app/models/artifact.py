from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ArtifactType(StrEnum):
    API = "api"
    DATABASE_TABLE = "database_table"
    TEST_CASE = "test_case"
    UML_COMPONENT = "uml_component"


class Artifact(TimestampMixin, Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        UniqueConstraint("project_id", "code", name="uq_artifacts_project_code"),
        Index("ix_artifacts_project_type", "project_id", "artifact_type"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(
            ArtifactType,
            name="artifact_type",
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    technical_details: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    project = relationship("Project", back_populates="artifacts")
    trace_links = relationship(
        "TraceLink",
        back_populates="artifact",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
