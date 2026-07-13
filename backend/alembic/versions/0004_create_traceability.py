"""Create artifacts and trace links.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    artifact_type = postgresql.ENUM(
        "api",
        "database_table",
        "test_case",
        "uml_component",
        name="artifact_type",
    )
    trace_link_type = postgresql.ENUM(
        "implements",
        "stores",
        "verifies",
        "represents",
        "relates_to",
        name="trace_link_type",
    )
    trace_link_status = postgresql.ENUM(
        "suggested",
        "accepted",
        "rejected",
        name="trace_link_status",
    )
    trace_link_source = postgresql.ENUM(
        "manual",
        "system",
        name="trace_link_source",
    )

    bind = op.get_bind()
    artifact_type.create(bind, checkfirst=True)
    trace_link_type.create(bind, checkfirst=True)
    trace_link_status.create(bind, checkfirst=True)
    trace_link_source.create(bind, checkfirst=True)

    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column(
            "artifact_type",
            postgresql.ENUM(
                "api",
                "database_table",
                "test_case",
                "uml_component",
                name="artifact_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "technical_details",
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "code", name="uq_artifacts_project_code"),
    )
    op.create_index("ix_artifacts_project_id", "artifacts", ["project_id"], unique=False)
    op.create_index(
        "ix_artifacts_project_type",
        "artifacts",
        ["project_id", "artifact_type"],
        unique=False,
    )

    op.create_table(
        "trace_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "link_type",
            postgresql.ENUM(
                "implements",
                "stores",
                "verifies",
                "represents",
                "relates_to",
                name="trace_link_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "suggested",
                "accepted",
                "rejected",
                name="trace_link_status",
                create_type=False,
            ),
            nullable=False,
            server_default="suggested",
        ),
        sa.Column(
            "source",
            postgresql.ENUM(
                "manual",
                "system",
                name="trace_link_source",
                create_type=False,
            ),
            nullable=False,
            server_default="system",
        ),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1"),
        sa.Column(
            "evidence",
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["requirement_id"],
            ["requirements.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "project_id",
            "requirement_id",
            "artifact_id",
            name="uq_trace_links_project_requirement_artifact",
        ),
    )
    op.create_index("ix_trace_links_project_id", "trace_links", ["project_id"], unique=False)
    op.create_index(
        "ix_trace_links_requirement_id",
        "trace_links",
        ["requirement_id"],
        unique=False,
    )
    op.create_index("ix_trace_links_artifact_id", "trace_links", ["artifact_id"], unique=False)
    op.create_index(
        "ix_trace_links_project_status",
        "trace_links",
        ["project_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_trace_links_project_status", table_name="trace_links")
    op.drop_index("ix_trace_links_artifact_id", table_name="trace_links")
    op.drop_index("ix_trace_links_requirement_id", table_name="trace_links")
    op.drop_index("ix_trace_links_project_id", table_name="trace_links")
    op.drop_table("trace_links")

    op.drop_index("ix_artifacts_project_type", table_name="artifacts")
    op.drop_index("ix_artifacts_project_id", table_name="artifacts")
    op.drop_table("artifacts")

    bind = op.get_bind()
    postgresql.ENUM(name="trace_link_source").drop(bind, checkfirst=True)
    postgresql.ENUM(name="trace_link_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="trace_link_type").drop(bind, checkfirst=True)
    postgresql.ENUM(name="artifact_type").drop(bind, checkfirst=True)
