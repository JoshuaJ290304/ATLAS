"""create test case intelligence
Revision ID: 0009
Revises: 0008
Create Date: 2026-07-25
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    for enum in [
        postgresql.ENUM(
            "draft",
            "in_review",
            "approved",
            "rejected",
            "needs_review",
            "archived",
            name="test_case_status",
        ),
        postgresql.ENUM("low", "medium", "high", "critical", name="test_case_priority"),
        postgresql.ENUM(
            "functional",
            "positive",
            "negative",
            "boundary",
            "security",
            "performance",
            "integration",
            "regression",
            name="test_case_type",
        ),
        postgresql.ENUM("manual", "ai_generated", name="test_case_source"),
    ]:
        enum.create(bind, checkfirst=True)
    op.create_table(
        "test_cases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "requirement_id", sa.Uuid(), sa.ForeignKey("requirements.id", ondelete="SET NULL")
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("preconditions", sa.Text()),
        sa.Column("test_data", sa.Text()),
        sa.Column("overall_expected_result", sa.Text(), nullable=False),
        sa.Column(
            "test_type", postgresql.ENUM(name="test_case_type", create_type=False), nullable=False
        ),
        sa.Column(
            "priority",
            postgresql.ENUM(name="test_case_priority", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status", postgresql.ENUM(name="test_case_status", create_type=False), nullable=False
        ),
        sa.Column(
            "source", postgresql.ENUM(name="test_case_source", create_type=False), nullable=False
        ),
        sa.Column("generation_explanation", sa.Text()),
        sa.Column("reviewer_name", sa.String(160)),
        sa.Column("review_comments", sa.Text()),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_test_cases_project_id", "test_cases", ["project_id"])
    op.create_index("ix_test_cases_requirement_id", "test_cases", ["requirement_id"])
    op.create_index("ix_test_cases_project_status", "test_cases", ["project_id", "status"])
    op.create_table(
        "test_steps",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "test_case_id",
            sa.Uuid(),
            sa.ForeignKey("test_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("expected_result", sa.Text(), nullable=False),
    )
    op.create_index("ix_test_steps_test_case_id", "test_steps", ["test_case_id"])
    op.create_table(
        "test_case_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "test_case_id",
            sa.Uuid(),
            sa.ForeignKey("test_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("change_note", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_test_case_versions_test_case_id", "test_case_versions", ["test_case_id"])


def downgrade():
    op.drop_table("test_case_versions")
    op.drop_table("test_steps")
    op.drop_table("test_cases")
    bind = op.get_bind()
    for name in ["test_case_source", "test_case_type", "test_case_priority", "test_case_status"]:
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
