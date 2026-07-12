"""Create requirements table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    requirement_type = postgresql.ENUM(
        "functional",
        "non_functional",
        name="requirement_type",
    )
    requirement_status = postgresql.ENUM(
        "draft",
        "reviewed",
        "approved",
        "rejected",
        name="requirement_status",
    )
    requirement_source = postgresql.ENUM(
        "extracted",
        "manual",
        name="requirement_source",
    )
    bind = op.get_bind()
    requirement_type.create(bind, checkfirst=True)
    requirement_status.create(bind, checkfirst=True)
    requirement_source.create(bind, checkfirst=True)

    op.create_table(
        "requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "requirement_type",
            postgresql.ENUM(
                "functional",
                "non_functional",
                name="requirement_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("non_functional_category", sa.String(length=80), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft",
                "reviewed",
                "approved",
                "rejected",
                name="requirement_status",
                create_type=False,
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "source",
            postgresql.ENUM(
                "extracted",
                "manual",
                name="requirement_source",
                create_type=False,
            ),
            nullable=False,
            server_default="extracted",
        ),
        sa.Column("source_excerpt", sa.Text(), nullable=True),
        sa.Column("source_position", sa.Integer(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1"),
        sa.Column("ambiguity_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "ambiguity_flags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
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
            ["source_document_id"],
            ["documents.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("project_id", "code", name="uq_requirements_project_code"),
    )
    op.create_index("ix_requirements_project_id", "requirements", ["project_id"], unique=False)
    op.create_index(
        "ix_requirements_source_document_id",
        "requirements",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        "ix_requirements_project_type",
        "requirements",
        ["project_id", "requirement_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_requirements_project_type", table_name="requirements")
    op.drop_index("ix_requirements_source_document_id", table_name="requirements")
    op.drop_index("ix_requirements_project_id", table_name="requirements")
    op.drop_table("requirements")
    bind = op.get_bind()
    postgresql.ENUM(name="requirement_source").drop(bind, checkfirst=True)
    postgresql.ENUM(name="requirement_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="requirement_type").drop(bind, checkfirst=True)
