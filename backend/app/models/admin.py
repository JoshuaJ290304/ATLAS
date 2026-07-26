from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AuditSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PlatformAuditLog(Base):
    __tablename__ = "platform_audit_logs"
    __table_args__ = (
        Index("ix_platform_audit_created", "created_at"),
        Index("ix_platform_audit_actor", "actor_id", "created_at"),
        Index("ix_platform_audit_target_user", "target_user_id", "created_at"),
        Index("ix_platform_audit_project", "project_id", "created_at"),
        Index("ix_platform_audit_action", "action", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    actor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    target_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[AuditSeverity] = mapped_column(
        Enum(
            AuditSeverity,
            name="platform_audit_severity",
            values_callable=lambda values: [value.value for value in values],
        ),
        default=AuditSeverity.INFO,
        nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PlatformSettings(TimestampMixin, Base):
    __tablename__ = "platform_settings"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    registration_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    maintenance_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_generation_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    session_duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    password_reset_expiry_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_upload_size_mb: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    allowed_document_extensions: Mapped[list[str]] = mapped_column(
        JSONB, default=lambda: [".pdf", ".docx"], nullable=False
    )
    updated_by_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
