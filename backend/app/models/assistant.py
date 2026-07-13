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


class KnowledgeSourceType(StrEnum):
    DOCUMENT = "document"
    REQUIREMENT = "requirement"
    ARTIFACT = "artifact"
    IMPACT_ANALYSIS = "impact_analysis"


class AssistantIndexStatus(StrEnum):
    NOT_INDEXED = "not_indexed"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class AssistantMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("vector_id", name="uq_knowledge_chunks_vector_id"),
        UniqueConstraint(
            "project_id",
            "source_type",
            "source_id",
            "chunk_index",
            name="uq_knowledge_chunks_source_chunk",
        ),
        Index("ix_knowledge_chunks_project_source", "project_id", "source_type", "source_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source_type: Mapped[KnowledgeSourceType] = mapped_column(
        Enum(
            KnowledgeSourceType,
            name="knowledge_source_type",
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    source_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    source_label: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_id: Mapped[str] = mapped_column(String(96), nullable=False)
    source_metadata: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project = relationship("Project", back_populates="knowledge_chunks")


class AssistantIndex(TimestampMixin, Base):
    __tablename__ = "assistant_indexes"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    status: Mapped[AssistantIndexStatus] = mapped_column(
        Enum(
            AssistantIndexStatus,
            name="assistant_index_status",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=AssistantIndexStatus.NOT_INDEXED,
        nullable=False,
    )
    source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="assistant_index")


class AssistantConversation(TimestampMixin, Base):
    __tablename__ = "assistant_conversations"
    __table_args__ = (
        Index("ix_assistant_conversations_project_updated", "project_id", "updated_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    owner_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)

    project = relationship("Project", back_populates="assistant_conversations")
    owner = relationship("User", back_populates="assistant_conversations")
    messages = relationship(
        "AssistantMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AssistantMessage.created_at",
    )


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"
    __table_args__ = (
        Index("ix_assistant_messages_conversation_created", "conversation_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[AssistantMessageRole] = mapped_column(
        Enum(
            AssistantMessageRole,
            name="assistant_message_role",
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversation = relationship("AssistantConversation", back_populates="messages")
