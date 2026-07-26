"""expand governance review and baseline fields

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


review_priority = postgresql.ENUM(
    "low",
    "medium",
    "high",
    "critical",
    name="governance_review_priority",
    create_type=False,
)

baseline_status = postgresql.ENUM(
    "active",
    "archived",
    name="governance_baseline_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    review_priority.create(bind, checkfirst=True)
    baseline_status.create(bind, checkfirst=True)

    op.add_column(
        "requirement_reviews",
        sa.Column(
            "priority",
            review_priority,
            nullable=False,
            server_default="medium",
        ),
    )
    op.add_column(
        "requirement_reviews",
        sa.Column("due_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "project_baselines",
        sa.Column(
            "status",
            baseline_status,
            nullable=False,
            server_default="active",
        ),
    )

    op.alter_column("requirement_reviews", "priority", server_default=None)
    op.alter_column("project_baselines", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("project_baselines", "status")
    op.drop_column("requirement_reviews", "due_date")
    op.drop_column("requirement_reviews", "priority")

    bind = op.get_bind()
    baseline_status.drop(bind, checkfirst=True)
    review_priority.drop(bind, checkfirst=True)
