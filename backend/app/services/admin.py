from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.admin import AuditSeverity, PlatformAuditLog, PlatformSettings
from app.models.assistant import AssistantIndex, AssistantIndexStatus
from app.models.document import Document, DocumentStatus
from app.models.impact import ImpactAnalysis, ImpactSeverity
from app.models.project import Project, ProjectStatus
from app.models.release_readiness import ReleaseCandidate
from app.models.requirement import Requirement
from app.models.test_case import TestCase
from app.models.user import User, UserRole


async def get_platform_settings(db: AsyncSession, *, for_update: bool = False) -> PlatformSettings:
    query = select(PlatformSettings).order_by(PlatformSettings.created_at.asc()).limit(1)
    if for_update:
        query = query.with_for_update()
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if item is None:
        item = PlatformSettings(
            registration_enabled=True,
            maintenance_mode=False,
            ai_generation_enabled=True,
            session_duration_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            password_reset_expiry_minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES,
            max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
            allowed_document_extensions=[
                extension.strip().lower()
                for extension in settings.ALLOWED_DOCUMENT_EXTENSIONS.split(",")
                if extension.strip()
            ],
        )
        db.add(item)
        await db.flush()
    return item


async def write_platform_audit(
    db: AsyncSession,
    *,
    action: str,
    actor_id: UUID | None = None,
    target_user_id: UUID | None = None,
    project_id: UUID | None = None,
    severity: AuditSeverity = AuditSeverity.INFO,
    ip_address: str | None = None,
    details: dict[str, object] | None = None,
) -> PlatformAuditLog:
    entry = PlatformAuditLog(
        actor_id=actor_id,
        target_user_id=target_user_id,
        project_id=project_id,
        action=action,
        severity=severity,
        ip_address=ip_address,
        details=details or {},
    )
    db.add(entry)
    await db.flush()
    return entry


async def aggregate_counts_by_owner(db: AsyncSession) -> dict[str, dict[UUID, int]]:
    result: dict[str, dict[UUID, int]] = {}
    specifications = {
        "projects": select(Project.owner_id, func.count(Project.id)).group_by(Project.owner_id),
        "documents": select(Project.owner_id, func.count(Document.id))
        .join(Document, Document.project_id == Project.id)
        .group_by(Project.owner_id),
        "requirements": select(Project.owner_id, func.count(Requirement.id))
        .join(Requirement, Requirement.project_id == Project.id)
        .group_by(Project.owner_id),
        "test_cases": select(Project.owner_id, func.count(TestCase.id))
        .join(TestCase, TestCase.project_id == Project.id)
        .group_by(Project.owner_id),
        "releases": select(Project.owner_id, func.count(ReleaseCandidate.id))
        .join(ReleaseCandidate, ReleaseCandidate.project_id == Project.id)
        .group_by(Project.owner_id),
    }
    for key, query in specifications.items():
        rows = (await db.execute(query)).all()
        result[key] = {owner_id: int(count) for owner_id, count in rows}
    return result


async def aggregate_counts_by_project(db: AsyncSession) -> dict[str, dict[UUID, int]]:
    result: dict[str, dict[UUID, int]] = {}
    specifications = {
        "documents": select(Document.project_id, func.count(Document.id)).group_by(Document.project_id),
        "failed_documents": select(Document.project_id, func.count(Document.id))
        .where(Document.status == DocumentStatus.FAILED)
        .group_by(Document.project_id),
        "requirements": select(Requirement.project_id, func.count(Requirement.id)).group_by(Requirement.project_id),
        "test_cases": select(TestCase.project_id, func.count(TestCase.id)).group_by(TestCase.project_id),
        "releases": select(ReleaseCandidate.project_id, func.count(ReleaseCandidate.id)).group_by(ReleaseCandidate.project_id),
        "high_risk": select(ImpactAnalysis.project_id, func.count(ImpactAnalysis.id))
        .where(ImpactAnalysis.severity.in_([ImpactSeverity.HIGH, ImpactSeverity.CRITICAL]))
        .group_by(ImpactAnalysis.project_id),
    }
    for key, query in specifications.items():
        rows = (await db.execute(query)).all()
        result[key] = {project_id: int(count) for project_id, count in rows}
    return result


def directory_size(path_value: str) -> int:
    path = Path(path_value)
    if not path.exists():
        return 0
    total = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total += item.stat().st_size
                except OSError:
                    continue
    except OSError:
        return total
    return total


async def check_ollama() -> tuple[str, str]:
    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            response.raise_for_status()
        return "healthy", "Ollama is reachable."
    except Exception:
        return "unavailable", "Ollama is not reachable from the backend."


async def check_smtp() -> tuple[str, str]:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(settings.SMTP_HOST, settings.SMTP_PORT), timeout=3
        )
        writer.close()
        await writer.wait_closed()
        del reader
        return "healthy", f"SMTP service is reachable on port {settings.SMTP_PORT}."
    except Exception:
        return "unavailable", "The configured SMTP service is not reachable."


async def read_alembic_revision(db: AsyncSession) -> str | None:
    try:
        return (await db.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))).scalar_one_or_none()
    except Exception:
        return None


async def platform_totals(db: AsyncSession) -> dict[str, int]:
    queries = {
        "users": select(func.count(User.id)),
        "active_users": select(func.count(User.id)).where(User.is_active.is_(True)),
        "administrators": select(func.count(User.id)).where(User.role == UserRole.ADMIN),
        "projects": select(func.count(Project.id)),
        "active_projects": select(func.count(Project.id)).where(Project.status == ProjectStatus.ACTIVE),
        "documents": select(func.count(Document.id)),
        "processed_documents": select(func.count(Document.id)).where(Document.status == DocumentStatus.EXTRACTED),
        "failed_documents": select(func.count(Document.id)).where(Document.status == DocumentStatus.FAILED),
        "requirements": select(func.count(Requirement.id)),
        "test_cases": select(func.count(TestCase.id)),
        "release_candidates": select(func.count(ReleaseCandidate.id)),
        "ready_ai_indexes": select(func.count(AssistantIndex.id)).where(AssistantIndex.status == AssistantIndexStatus.READY),
        "ai_indexes": select(func.count(AssistantIndex.id)),
        "critical_events": select(func.count(PlatformAuditLog.id)).where(
            PlatformAuditLog.severity == AuditSeverity.CRITICAL,
            PlatformAuditLog.created_at >= datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0),
        ),
    }
    totals: dict[str, int] = {}
    for key, query in queries.items():
        totals[key] = int((await db.execute(query)).scalar_one() or 0)
    totals["suspended_users"] = totals["users"] - totals["active_users"]
    totals["archived_projects"] = totals["projects"] - totals["active_projects"]
    return totals
