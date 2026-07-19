from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(
            ProjectStatus,
            name="project_status",
            values_callable=lambda values: [v.value for v in values],
        ),
        default=ProjectStatus.ACTIVE,
        nullable=False,
    )

    owner = relationship("User", back_populates="projects")
    documents = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    requirements = relationship(
        "Requirement",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    artifacts = relationship(
        "Artifact",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    requirement_versions = relationship(
        "RequirementVersion",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    impact_analyses = relationship(
        "ImpactAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    trace_links = relationship(
        "TraceLink",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    knowledge_chunks = relationship(
        "KnowledgeChunk",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    assistant_index = relationship(
        "AssistantIndex",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    assistant_conversations = relationship(
        "AssistantConversation",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    requirement_reviews = relationship(
        "RequirementReview",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    requirement_comments = relationship(
        "RequirementComment",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    baselines = relationship(
        "ProjectBaseline",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
