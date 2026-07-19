from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda values: [v.value for v in values]),
        default=UserRole.USER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    projects = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True
    )

    assistant_conversations = relationship(
        "AssistantConversation",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    assigned_requirement_reviews = relationship(
        "RequirementReview",
        foreign_keys="RequirementReview.reviewer_id",
        back_populates="reviewer",
        passive_deletes=True,
    )

    requested_requirement_reviews = relationship(
        "RequirementReview",
        foreign_keys="RequirementReview.requested_by_id",
        back_populates="requested_by",
        passive_deletes=True,
    )

    requirement_comments = relationship(
        "RequirementComment",
        back_populates="author",
        passive_deletes=True,
    )

    created_baselines = relationship(
        "ProjectBaseline",
        back_populates="created_by",
        passive_deletes=True,
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="actor",
        passive_deletes=True,
    )
