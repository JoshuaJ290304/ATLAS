"""create administration and platform operations

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-26
"""

from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    audit_severity = postgresql.ENUM(
        "info", "warning", "critical", name="platform_audit_severity"
    )
    audit_severity.create(bind, checkfirst=True)

    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "suspended_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("users", sa.Column("suspension_reason", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column("session_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "users", sa.Column("last_password_reset_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index("ix_users_last_login_at", "users", ["last_login_at"])
    op.create_index("ix_users_is_active_role", "users", ["is_active", "role"])

    op.create_table(
        "platform_audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column(
            "severity",
            postgresql.ENUM(name="platform_audit_severity", create_type=False),
            nullable=False,
            server_default="info",
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_platform_audit_created", "platform_audit_logs", ["created_at"])
    op.create_index("ix_platform_audit_actor", "platform_audit_logs", ["actor_id", "created_at"])
    op.create_index("ix_platform_audit_target_user", "platform_audit_logs", ["target_user_id", "created_at"])
    op.create_index("ix_platform_audit_project", "platform_audit_logs", ["project_id", "created_at"])
    op.create_index("ix_platform_audit_action", "platform_audit_logs", ["action", "created_at"])

    op.create_table(
        "platform_settings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("registration_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("maintenance_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("maintenance_message", sa.Text(), nullable=True),
        sa.Column("ai_generation_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("session_duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("password_reset_expiry_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("max_upload_size_mb", sa.Integer(), nullable=False, server_default="10"),
        sa.Column(
            "allowed_document_extensions",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[\".pdf\", \".docx\"]'::jsonb"),
        ),
        sa.Column("updated_by_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("session_duration_minutes BETWEEN 5 AND 10080", name="ck_platform_settings_session_duration"),
        sa.CheckConstraint("password_reset_expiry_minutes BETWEEN 5 AND 1440", name="ck_platform_settings_reset_expiry"),
        sa.CheckConstraint("max_upload_size_mb BETWEEN 1 AND 100", name="ck_platform_settings_upload_size"),
    )

    settings_table = sa.table(
        "platform_settings",
        sa.column("id", sa.Uuid()),
        sa.column("registration_enabled", sa.Boolean()),
        sa.column("maintenance_mode", sa.Boolean()),
        sa.column("ai_generation_enabled", sa.Boolean()),
        sa.column("session_duration_minutes", sa.Integer()),
        sa.column("password_reset_expiry_minutes", sa.Integer()),
        sa.column("max_upload_size_mb", sa.Integer()),
        sa.column("allowed_document_extensions", postgresql.JSONB()),
    )
    op.bulk_insert(
        settings_table,
        [
            {
                "id": uuid4(),
                "registration_enabled": True,
                "maintenance_mode": False,
                "ai_generation_enabled": True,
                "session_duration_minutes": 60,
                "password_reset_expiry_minutes": 30,
                "max_upload_size_mb": 10,
                "allowed_document_extensions": [".pdf", ".docx"],
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("platform_settings")
    op.drop_table("platform_audit_logs")
    op.drop_index("ix_users_is_active_role", table_name="users")
    op.drop_index("ix_users_last_login_at", table_name="users")
    op.drop_column("users", "last_password_reset_at")
    op.drop_column("users", "session_version")
    op.drop_column("users", "suspension_reason")
    op.drop_column("users", "suspended_by_user_id")
    op.drop_column("users", "suspended_at")
    op.drop_column("users", "last_login_at")
    bind = op.get_bind()
    postgresql.ENUM(name="platform_audit_severity").drop(bind, checkfirst=True)
