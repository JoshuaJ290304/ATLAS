"""Create requirement governance, review, baseline, and audit tables.

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    review_status = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        name="governance_review_status",
    )
    review_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "requirement_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "approved",
                "rejected",
                name="governance_review_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("request_note", sa.Text(), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_requirement_reviews_project_id", "requirement_reviews", ["project_id"])
    op.create_index(
        "ix_requirement_reviews_requirement_id",
        "requirement_reviews",
        ["requirement_id"],
    )
    op.create_index("ix_requirement_reviews_reviewer_id", "requirement_reviews", ["reviewer_id"])
    op.create_index(
        "ix_requirement_reviews_requested_by_id",
        "requirement_reviews",
        ["requested_by_id"],
    )
    op.create_index(
        "ix_requirement_reviews_project_status",
        "requirement_reviews",
        ["project_id", "status"],
    )
    op.create_index(
        "ix_requirement_reviews_requirement_created",
        "requirement_reviews",
        ["requirement_id", "created_at"],
    )

    op.create_table(
        "requirement_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_requirement_comments_project_id", "requirement_comments", ["project_id"])
    op.create_index(
        "ix_requirement_comments_requirement_id",
        "requirement_comments",
        ["requirement_id"],
    )
    op.create_index("ix_requirement_comments_author_id", "requirement_comments", ["author_id"])
    op.create_index(
        "ix_requirement_comments_requirement_created",
        "requirement_comments",
        ["requirement_id", "created_at"],
    )

    op.create_table(
        "project_baselines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("version_label", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requirement_count", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "project_id",
            "version_label",
            name="uq_project_baselines_version",
        ),
    )
    op.create_index("ix_project_baselines_project_id", "project_baselines", ["project_id"])
    op.create_index(
        "ix_project_baselines_created_by_id",
        "project_baselines",
        ["created_by_id"],
    )
    op.create_index(
        "ix_project_baselines_project_created",
        "project_baselines",
        ["project_id", "created_at"],
    )

    op.create_table(
        "baseline_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("baseline_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("requirement_version", sa.Integer(), nullable=False),
        sa.Column(
            "snapshot_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["baseline_id"],
            ["project_baselines.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requirement_id"],
            ["requirements.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "baseline_id",
            "code",
            name="uq_baseline_requirements_code",
        ),
    )
    op.create_index(
        "ix_baseline_requirements_baseline_id",
        "baseline_requirements",
        ["baseline_id"],
    )
    op.create_index(
        "ix_baseline_requirements_requirement_id",
        "baseline_requirements",
        ["requirement_id"],
    )
    op.create_index(
        "ix_baseline_requirements_baseline_code",
        "baseline_requirements",
        ["baseline_id", "code"],
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "details",
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
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_audit_logs_project_id", "audit_logs", ["project_id"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index(
        "ix_audit_logs_project_created",
        "audit_logs",
        ["project_id", "created_at"],
    )
    op.create_index(
        "ix_audit_logs_entity",
        "audit_logs",
        ["entity_type", "entity_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_index("ix_audit_logs_project_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_project_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(
        "ix_baseline_requirements_baseline_code",
        table_name="baseline_requirements",
    )
    op.drop_index(
        "ix_baseline_requirements_requirement_id",
        table_name="baseline_requirements",
    )
    op.drop_index(
        "ix_baseline_requirements_baseline_id",
        table_name="baseline_requirements",
    )
    op.drop_table("baseline_requirements")

    op.drop_index(
        "ix_project_baselines_project_created",
        table_name="project_baselines",
    )
    op.drop_index("ix_project_baselines_created_by_id", table_name="project_baselines")
    op.drop_index("ix_project_baselines_project_id", table_name="project_baselines")
    op.drop_table("project_baselines")

    op.drop_index(
        "ix_requirement_comments_requirement_created",
        table_name="requirement_comments",
    )
    op.drop_index("ix_requirement_comments_author_id", table_name="requirement_comments")
    op.drop_index(
        "ix_requirement_comments_requirement_id",
        table_name="requirement_comments",
    )
    op.drop_index("ix_requirement_comments_project_id", table_name="requirement_comments")
    op.drop_table("requirement_comments")

    op.drop_index(
        "ix_requirement_reviews_requirement_created",
        table_name="requirement_reviews",
    )
    op.drop_index(
        "ix_requirement_reviews_project_status",
        table_name="requirement_reviews",
    )
    op.drop_index("ix_requirement_reviews_requested_by_id", table_name="requirement_reviews")
    op.drop_index("ix_requirement_reviews_reviewer_id", table_name="requirement_reviews")
    op.drop_index("ix_requirement_reviews_requirement_id", table_name="requirement_reviews")
    op.drop_index("ix_requirement_reviews_project_id", table_name="requirement_reviews")
    op.drop_table("requirement_reviews")

    postgresql.ENUM(name="governance_review_status").drop(
        op.get_bind(),
        checkfirst=True,
    )
