"""Create AI assistant knowledge and conversation tables.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    knowledge_source_type = postgresql.ENUM(
        "document",
        "requirement",
        "artifact",
        "impact_analysis",
        name="knowledge_source_type",
    )
    assistant_index_status = postgresql.ENUM(
        "not_indexed",
        "indexing",
        "ready",
        "failed",
        name="assistant_index_status",
    )
    assistant_message_role = postgresql.ENUM(
        "user",
        "assistant",
        name="assistant_message_role",
    )
    bind = op.get_bind()
    knowledge_source_type.create(bind, checkfirst=True)
    assistant_index_status.create(bind, checkfirst=True)
    assistant_message_role.create(bind, checkfirst=True)

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source_type",
            postgresql.ENUM(
                "document",
                "requirement",
                "artifact",
                "impact_analysis",
                name="knowledge_source_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_label", sa.String(length=255), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False),
        sa.Column("vector_id", sa.String(length=96), nullable=False),
        sa.Column(
            "source_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("vector_id", name="uq_knowledge_chunks_vector_id"),
        sa.UniqueConstraint(
            "project_id",
            "source_type",
            "source_id",
            "chunk_index",
            name="uq_knowledge_chunks_source_chunk",
        ),
    )
    op.create_index("ix_knowledge_chunks_project_id", "knowledge_chunks", ["project_id"])
    op.create_index("ix_knowledge_chunks_source_id", "knowledge_chunks", ["source_id"])
    op.create_index(
        "ix_knowledge_chunks_project_source",
        "knowledge_chunks",
        ["project_id", "source_type", "source_id"],
    )

    op.create_table(
        "assistant_indexes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "not_indexed",
                "indexing",
                "ready",
                "failed",
                name="assistant_index_status",
                create_type=False,
            ),
            nullable=False,
            server_default="not_indexed",
        ),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", name="uq_assistant_indexes_project_id"),
    )
    op.create_index("ix_assistant_indexes_project_id", "assistant_indexes", ["project_id"])

    op.create_table(
        "assistant_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_assistant_conversations_project_id",
        "assistant_conversations",
        ["project_id"],
    )
    op.create_index(
        "ix_assistant_conversations_owner_id",
        "assistant_conversations",
        ["owner_id"],
    )
    op.create_index(
        "ix_assistant_conversations_project_updated",
        "assistant_conversations",
        ["project_id", "updated_at"],
    )

    op.create_table(
        "assistant_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(
                "user",
                "assistant",
                name="assistant_message_role",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "citations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["assistant_conversations.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_assistant_messages_conversation_id",
        "assistant_messages",
        ["conversation_id"],
    )
    op.create_index(
        "ix_assistant_messages_conversation_created",
        "assistant_messages",
        ["conversation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_assistant_messages_conversation_created",
        table_name="assistant_messages",
    )
    op.drop_index("ix_assistant_messages_conversation_id", table_name="assistant_messages")
    op.drop_table("assistant_messages")

    op.drop_index(
        "ix_assistant_conversations_project_updated",
        table_name="assistant_conversations",
    )
    op.drop_index("ix_assistant_conversations_owner_id", table_name="assistant_conversations")
    op.drop_index("ix_assistant_conversations_project_id", table_name="assistant_conversations")
    op.drop_table("assistant_conversations")

    op.drop_index("ix_assistant_indexes_project_id", table_name="assistant_indexes")
    op.drop_table("assistant_indexes")

    op.drop_index("ix_knowledge_chunks_project_source", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_source_id", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_project_id", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")

    bind = op.get_bind()
    postgresql.ENUM(name="assistant_message_role").drop(bind, checkfirst=True)
    postgresql.ENUM(name="assistant_index_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="knowledge_source_type").drop(bind, checkfirst=True)
