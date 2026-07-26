"""create persistent authentication rate limits

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "security_rate_limit_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scope", sa.String(64), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_security_rate_limit_scope_key_created",
        "security_rate_limit_events",
        ["scope", "key_hash", "created_at"],
    )
    op.create_index(
        "ix_security_rate_limit_created",
        "security_rate_limit_events",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("security_rate_limit_events")
