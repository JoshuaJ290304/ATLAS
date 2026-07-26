"""create release readiness and quality gates

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-25
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    release_status = postgresql.ENUM(
        "draft",
        "in_review",
        "ready",
        "blocked",
        "released",
        "archived",
        name="release_candidate_status",
    )
    readiness_label = postgresql.ENUM(
        "ready",
        "at_risk",
        "blocked",
        "not_evaluated",
        name="release_readiness_label",
    )
    release_status.create(bind, checkfirst=True)
    readiness_label.create(bind, checkfirst=True)

    op.create_table(
        "release_candidates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "baseline_id",
            sa.Uuid(),
            sa.ForeignKey("project_baselines.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("version_label", sa.String(40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("release_owner", sa.String(160), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(name="release_candidate_status", create_type=False),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "selected_requirement_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "selected_test_case_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("minimum_traceability_percent", sa.Float(), nullable=False, server_default="80"),
        sa.Column("minimum_test_coverage_percent", sa.Float(), nullable=False, server_default="80"),
        sa.Column("maximum_high_risk_impacts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("maximum_overdue_reviews", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "require_active_baseline", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "require_approved_requirements", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("readiness_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "readiness_label",
            postgresql.ENUM(name="release_readiness_label", create_type=False),
            nullable=False,
            server_default="not_evaluated",
        ),
        sa.Column(
            "gate_summary",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "blockers", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column(
            "recommendations",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewer_name", sa.String(160), nullable=True),
        sa.Column("review_comments", sa.Text(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("signed_off_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("release_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("project_id", "version_label", name="uq_release_candidates_version"),
    )
    op.create_index("ix_release_candidates_project_id", "release_candidates", ["project_id"])
    op.create_index("ix_release_candidates_created_by_id", "release_candidates", ["created_by_id"])
    op.create_index("ix_release_candidates_baseline_id", "release_candidates", ["baseline_id"])
    op.create_index(
        "ix_release_candidates_project_status", "release_candidates", ["project_id", "status"]
    )
    op.create_index(
        "ix_release_candidates_project_updated", "release_candidates", ["project_id", "updated_at"]
    )

    op.create_table(
        "release_gate_evaluations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "release_candidate_id",
            sa.Uuid(),
            sa.ForeignKey("release_candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "evaluated_by_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("readiness_score", sa.Float(), nullable=False),
        sa.Column(
            "readiness_label",
            postgresql.ENUM(name="release_readiness_label", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "gate_results",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "blockers", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column(
            "recommendations",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_release_gate_evaluations_release_candidate_id",
        "release_gate_evaluations",
        ["release_candidate_id"],
    )
    op.create_index(
        "ix_release_gate_evaluations_evaluated_by_id",
        "release_gate_evaluations",
        ["evaluated_by_id"],
    )
    op.create_index(
        "ix_release_gate_evaluations_candidate_created",
        "release_gate_evaluations",
        ["release_candidate_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("release_gate_evaluations")
    op.drop_table("release_candidates")
    bind = op.get_bind()
    postgresql.ENUM(name="release_readiness_label").drop(bind, checkfirst=True)
    postgresql.ENUM(name="release_candidate_status").drop(bind, checkfirst=True)
