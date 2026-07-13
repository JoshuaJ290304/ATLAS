"""Create requirement versions and impact analyses.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    impact_severity = postgresql.ENUM(
        "low",
        "medium",
        "high",
        "critical",
        name="impact_severity",
    )
    requirement_change_type = postgresql.ENUM(
        "modified",
        "reclassified",
        "status_changed",
        "complex",
        name="requirement_change_type",
    )
    bind = op.get_bind()
    impact_severity.create(bind, checkfirst=True)
    requirement_change_type.create(bind, checkfirst=True)

    op.create_table(
        "requirement_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
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
        ),
        sa.Column("ambiguity_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "ambiguity_flags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
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
        sa.UniqueConstraint(
            "requirement_id",
            "version",
            name="uq_requirement_versions_requirement_version",
        ),
    )
    op.create_index(
        "ix_requirement_versions_project_id",
        "requirement_versions",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_requirement_versions_requirement_id",
        "requirement_versions",
        ["requirement_id"],
        unique=False,
    )
    op.create_index(
        "ix_requirement_versions_project_requirement",
        "requirement_versions",
        ["project_id", "requirement_id"],
        unique=False,
    )

    op.create_table(
        "impact_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requirement_code", sa.String(length=32), nullable=False),
        sa.Column("requirement_title", sa.String(length=180), nullable=False),
        sa.Column("baseline_version", sa.Integer(), nullable=False),
        sa.Column("target_version", sa.Integer(), nullable=False),
        sa.Column(
            "change_type",
            postgresql.ENUM(
                "modified",
                "reclassified",
                "status_changed",
                "complex",
                name="requirement_change_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column(
            "severity",
            postgresql.ENUM(
                "low",
                "medium",
                "high",
                "critical",
                name="impact_severity",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("change_summary", sa.Text(), nullable=False),
        sa.Column(
            "differences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "direct_artifacts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "transitive_artifacts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "risk_factors",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
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
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_impact_analyses_project_id",
        "impact_analyses",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_impact_analyses_requirement_id",
        "impact_analyses",
        ["requirement_id"],
        unique=False,
    )
    op.create_index(
        "ix_impact_analyses_project_created",
        "impact_analyses",
        ["project_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_impact_analyses_project_severity",
        "impact_analyses",
        ["project_id", "severity"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_impact_analyses_project_severity", table_name="impact_analyses")
    op.drop_index("ix_impact_analyses_project_created", table_name="impact_analyses")
    op.drop_index("ix_impact_analyses_requirement_id", table_name="impact_analyses")
    op.drop_index("ix_impact_analyses_project_id", table_name="impact_analyses")
    op.drop_table("impact_analyses")

    op.drop_index(
        "ix_requirement_versions_project_requirement",
        table_name="requirement_versions",
    )
    op.drop_index(
        "ix_requirement_versions_requirement_id",
        table_name="requirement_versions",
    )
    op.drop_index(
        "ix_requirement_versions_project_id",
        table_name="requirement_versions",
    )
    op.drop_table("requirement_versions")

    bind = op.get_bind()
    postgresql.ENUM(name="requirement_change_type").drop(bind, checkfirst=True)
    postgresql.ENUM(name="impact_severity").drop(bind, checkfirst=True)
