from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.admin import AuditSeverity
from app.models.project import ProjectStatus
from app.models.user import UserRole
from app.schemas.validation import clean_required_text


class AdminDashboardRead(BaseModel):
    total_users: int
    active_users: int
    suspended_users: int
    administrators: int
    total_projects: int
    active_projects: int
    archived_projects: int
    total_documents: int
    processed_documents: int
    failed_documents: int
    total_requirements: int
    total_test_cases: int
    total_release_candidates: int
    recent_registrations: list["AdminUserSummary"]
    recent_actions: list["PlatformAuditRead"]


class AdminUserSummary(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    account_status: Literal["active", "suspended"]
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
    suspended_at: datetime | None = None
    suspension_reason: str | None = None
    session_version: int
    project_count: int = 0
    document_count: int = 0
    requirement_count: int = 0
    test_case_count: int = 0
    release_candidate_count: int = 0


class AdminUserProjectRead(BaseModel):
    id: UUID
    name: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    document_count: int = 0
    requirement_count: int = 0
    test_case_count: int = 0
    release_candidate_count: int = 0


class AdminUserDetail(AdminUserSummary):
    projects: list[AdminUserProjectRead] = Field(default_factory=list)
    recent_activity: list["PlatformAuditRead"] = Field(default_factory=list)


class AdminRoleUpdate(BaseModel):
    role: UserRole


class AdminStatusUpdate(BaseModel):
    status: Literal["active", "suspended"]
    reason: str | None = Field(default=None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None


class AdminProjectTransfer(BaseModel):
    new_owner_id: UUID
    reason: str = Field(min_length=3, max_length=1000)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        return clean_required_text(value, "Transfer reason")


class AdminProjectStatusUpdate(BaseModel):
    status: ProjectStatus
    reason: str | None = Field(default=None, max_length=1000)


class AdminProjectSummary(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    status: ProjectStatus
    owner_id: UUID
    owner_name: str
    owner_email: EmailStr
    created_at: datetime
    updated_at: datetime
    document_count: int = 0
    failed_document_count: int = 0
    requirement_count: int = 0
    test_case_count: int = 0
    release_candidate_count: int = 0
    high_risk_impact_count: int = 0


class PlatformAuditRead(BaseModel):
    id: UUID
    actor_id: UUID | None = None
    actor_name: str | None = None
    actor_email: EmailStr | None = None
    target_user_id: UUID | None = None
    target_user_name: str | None = None
    project_id: UUID | None = None
    project_name: str | None = None
    action: str
    severity: AuditSeverity
    ip_address: str | None = None
    details: dict[str, object]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlatformAuditPage(BaseModel):
    items: list[PlatformAuditRead]
    total: int
    limit: int
    offset: int


class SystemServiceRead(BaseModel):
    key: str
    label: str
    status: Literal["healthy", "warning", "unavailable"]
    message: str


class AdminSystemRead(BaseModel):
    application_version: str
    alembic_revision: str | None
    database_status: str
    services: list[SystemServiceRead]
    storage_usage_bytes: int
    upload_storage_bytes: int
    vector_storage_bytes: int
    model_storage_bytes: int
    failed_document_count: int
    ready_ai_index_count: int
    total_ai_index_count: int
    recent_critical_event_count: int


class PlatformSettingsRead(BaseModel):
    id: UUID
    registration_enabled: bool
    maintenance_mode: bool
    maintenance_message: str | None = None
    ai_generation_enabled: bool
    session_duration_minutes: int
    password_reset_expiry_minutes: int
    max_upload_size_mb: int
    allowed_document_extensions: list[str]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlatformSettingsUpdate(BaseModel):
    registration_enabled: bool
    maintenance_mode: bool
    maintenance_message: str | None = Field(default=None, max_length=1000)
    ai_generation_enabled: bool
    session_duration_minutes: int = Field(ge=5, le=10080)
    password_reset_expiry_minutes: int = Field(ge=5, le=1440)
    max_upload_size_mb: int = Field(ge=1, le=100)
    allowed_document_extensions: list[str] = Field(min_length=1, max_length=10)

    @field_validator("allowed_document_extensions")
    @classmethod
    def normalize_extensions(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            item = value.strip().lower()
            if not item:
                continue
            if not item.startswith("."):
                item = f".{item}"
            if not item[1:].isalnum():
                raise ValueError("Document extensions may contain letters and numbers only")
            if item not in {".pdf", ".docx"}:
                raise ValueError("ATLAS currently supports only .pdf and .docx documents")
            if item not in normalized:
                normalized.append(item)
        if not normalized:
            raise ValueError("At least one document extension is required")
        return normalized

    @field_validator("maintenance_message")
    @classmethod
    def clean_maintenance_message(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None


class AdminActionMessage(BaseModel):
    message: str


AdminUserDetail.model_rebuild()
AdminDashboardRead.model_rebuild()
