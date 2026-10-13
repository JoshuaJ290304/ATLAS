from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import aliased

from app.api.dependencies import CurrentAdmin, DbSession
from app.core.config import settings
from app.models.admin import AuditSeverity, PlatformAuditLog
from app.models.project import Project, ProjectStatus
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminActionMessage,
    AdminDashboardRead,
    AdminProjectStatusUpdate,
    AdminProjectSummary,
    AdminProjectTransfer,
    AdminRoleUpdate,
    AdminStatusUpdate,
    AdminSystemRead,
    AdminUserDetail,
    AdminUserProjectRead,
    AdminUserSummary,
    PlatformAuditPage,
    PlatformAuditRead,
    PlatformSettingsRead,
    PlatformSettingsUpdate,
    SystemServiceRead,
)
from app.services.admin import (
    aggregate_counts_by_owner,
    aggregate_counts_by_project,
    check_ollama,
    check_smtp,
    directory_size,
    get_platform_settings,
    platform_totals,
    read_alembic_revision,
    write_platform_audit,
)
from app.services.auth import create_password_reset_request
from app.services.email import send_password_reset_email

router = APIRouter(prefix="/admin", tags=["platform administration"])


def _user_summary(user: User, counts: dict[str, dict[UUID, int]]) -> AdminUserSummary:
    return AdminUserSummary(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        account_status="active" if user.is_active else "suspended",
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
        suspended_at=user.suspended_at,
        suspension_reason=user.suspension_reason,
        session_version=user.session_version,
        project_count=counts["projects"].get(user.id, 0),
        document_count=counts["documents"].get(user.id, 0),
        requirement_count=counts["requirements"].get(user.id, 0),
        test_case_count=counts["test_cases"].get(user.id, 0),
        release_candidate_count=counts["releases"].get(user.id, 0),
    )


async def _active_admin_count(db: DbSession, *, lock_rows: bool = False) -> int:
    if lock_rows:
        # Serialize administrator lifecycle changes so two concurrent demotions/suspensions
        # cannot both observe two admins and reduce the platform to zero active admins.
        await db.execute(
            select(User.id)
            .where(User.role == UserRole.ADMIN, User.is_active.is_(True))
            .order_by(User.id)
            .with_for_update()
        )
    return int(
        (
            await db.execute(
                select(func.count(User.id)).where(
                    User.role == UserRole.ADMIN,
                    User.is_active.is_(True),
                )
            )
        ).scalar_one()
        or 0
    )


async def _get_user(db: DbSession, user_id: UUID, *, for_update: bool = False) -> User:
    query = select(User).where(User.id == user_id)
    if for_update:
        query = query.with_for_update()
    user = (await db.execute(query)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def _get_project(db: DbSession, project_id: UUID, *, for_update: bool = False) -> Project:
    query = select(Project).where(Project.id == project_id)
    if for_update:
        query = query.with_for_update()
    project = (await db.execute(query)).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _audit_rows(
    db: DbSession,
    *,
    search: str | None = None,
    action: str | None = None,
    severity: AuditSeverity | None = None,
    user_id: UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[PlatformAuditRead], int]:
    actor = aliased(User)
    target = aliased(User)
    base = (
        select(
            PlatformAuditLog,
            actor.name.label("actor_name"),
            actor.email.label("actor_email"),
            target.name.label("target_name"),
            Project.name.label("project_name"),
        )
        .outerjoin(actor, actor.id == PlatformAuditLog.actor_id)
        .outerjoin(target, target.id == PlatformAuditLog.target_user_id)
        .outerjoin(Project, Project.id == PlatformAuditLog.project_id)
    )
    filters = []
    if action:
        filters.append(PlatformAuditLog.action == action)
    if severity:
        filters.append(PlatformAuditLog.severity == severity)
    if user_id:
        filters.append(
            or_(PlatformAuditLog.actor_id == user_id, PlatformAuditLog.target_user_id == user_id)
        )
    if search:
        pattern = f"%{search.strip().lower()}%"
        filters.append(
            or_(
                func.lower(PlatformAuditLog.action).like(pattern),
                func.lower(func.coalesce(actor.name, "")).like(pattern),
                func.lower(func.coalesce(actor.email, "")).like(pattern),
                func.lower(func.coalesce(target.name, "")).like(pattern),
                func.lower(func.coalesce(Project.name, "")).like(pattern),
            )
        )
    if filters:
        base = base.where(*filters)

    count_query = select(func.count()).select_from(base.order_by(None).subquery())
    total = int((await db.execute(count_query)).scalar_one() or 0)
    rows = (
        await db.execute(
            base.order_by(PlatformAuditLog.created_at.desc()).limit(limit).offset(offset)
        )
    ).all()
    items = [
        PlatformAuditRead(
            id=entry.id,
            actor_id=entry.actor_id,
            actor_name=actor_name,
            actor_email=actor_email,
            target_user_id=entry.target_user_id,
            target_user_name=target_name,
            project_id=entry.project_id,
            project_name=project_name,
            action=entry.action,
            severity=entry.severity,
            ip_address=entry.ip_address,
            details=entry.details,
            created_at=entry.created_at,
        )
        for entry, actor_name, actor_email, target_name, project_name in rows
    ]
    return items, total


@router.get("/dashboard", response_model=AdminDashboardRead)
async def admin_dashboard(db: DbSession, current_admin: CurrentAdmin) -> AdminDashboardRead:
    del current_admin
    totals = await platform_totals(db)
    counts = await aggregate_counts_by_owner(db)
    recent_users = list(
        (await db.execute(select(User).order_by(User.created_at.desc()).limit(5))).scalars().all()
    )
    recent_actions, _ = await _audit_rows(db, limit=8)
    return AdminDashboardRead(
        total_users=totals["users"],
        active_users=totals["active_users"],
        suspended_users=totals["suspended_users"],
        administrators=totals["administrators"],
        total_projects=totals["projects"],
        active_projects=totals["active_projects"],
        archived_projects=totals["archived_projects"],
        total_documents=totals["documents"],
        processed_documents=totals["processed_documents"],
        failed_documents=totals["failed_documents"],
        total_requirements=totals["requirements"],
        total_test_cases=totals["test_cases"],
        total_release_candidates=totals["release_candidates"],
        recent_registrations=[_user_summary(user, counts) for user in recent_users],
        recent_actions=recent_actions,
    )


@router.get("/users", response_model=list[AdminUserSummary])
async def list_users(
    db: DbSession,
    current_admin: CurrentAdmin,
    search: str | None = Query(default=None, max_length=200),
    role: UserRole | None = None,
    account_status: Literal["active", "suspended"] | None = None,
) -> list[AdminUserSummary]:
    del current_admin
    query = select(User)
    if search:
        pattern = f"%{search.strip().lower()}%"
        query = query.where(
            or_(func.lower(User.name).like(pattern), func.lower(User.email).like(pattern))
        )
    if role:
        query = query.where(User.role == role)
    if account_status:
        query = query.where(User.is_active.is_(account_status == "active"))
    users = list((await db.execute(query.order_by(User.created_at.desc()))).scalars().all())
    counts = await aggregate_counts_by_owner(db)
    return [_user_summary(user, counts) for user in users]


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def read_user(user_id: UUID, db: DbSession, current_admin: CurrentAdmin) -> AdminUserDetail:
    del current_admin
    user = await _get_user(db, user_id)
    counts = await aggregate_counts_by_owner(db)
    project_counts = await aggregate_counts_by_project(db)
    projects = list(
        (
            await db.execute(
                select(Project)
                .where(Project.owner_id == user.id)
                .order_by(Project.updated_at.desc())
            )
        )
        .scalars()
        .all()
    )
    activity, _ = await _audit_rows(db, user_id=user.id, limit=20)
    summary = _user_summary(user, counts)
    return AdminUserDetail(
        **summary.model_dump(),
        projects=[
            AdminUserProjectRead(
                id=project.id,
                name=project.name,
                status=project.status,
                created_at=project.created_at,
                updated_at=project.updated_at,
                document_count=project_counts["documents"].get(project.id, 0),
                requirement_count=project_counts["requirements"].get(project.id, 0),
                test_case_count=project_counts["test_cases"].get(project.id, 0),
                release_candidate_count=project_counts["releases"].get(project.id, 0),
            )
            for project in projects
        ],
        recent_activity=activity,
    )


@router.patch("/users/{user_id}/role", response_model=AdminUserSummary)
async def update_user_role(
    user_id: UUID,
    payload: AdminRoleUpdate,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> AdminUserSummary:
    user = await _get_user(db, user_id, for_update=True)
    if user.role == payload.role:
        return _user_summary(user, await aggregate_counts_by_owner(db))
    if user.id == current_admin.id and payload.role == UserRole.USER:
        raise HTTPException(
            status_code=409, detail="An administrator cannot demote their own account"
        )
    if user.role == UserRole.ADMIN and payload.role == UserRole.USER:
        if user.is_active and await _active_admin_count(db, lock_rows=True) <= 1:
            raise HTTPException(
                status_code=409, detail="The final active administrator cannot be demoted"
            )
    old_role = user.role.value
    user.role = payload.role
    user.session_version += 1
    await write_platform_audit(
        db,
        action="admin.user_role_changed",
        actor_id=current_admin.id,
        target_user_id=user.id,
        ip_address=request.client.host if request.client else None,
        details={"from": old_role, "to": payload.role.value},
    )
    await db.commit()
    await db.refresh(user)
    return _user_summary(user, await aggregate_counts_by_owner(db))


@router.patch("/users/{user_id}/status", response_model=AdminUserSummary)
async def update_user_status(
    user_id: UUID,
    payload: AdminStatusUpdate,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> AdminUserSummary:
    user = await _get_user(db, user_id, for_update=True)
    activate = payload.status == "active"
    if user.is_active == activate:
        return _user_summary(user, await aggregate_counts_by_owner(db))
    if not activate and user.role == UserRole.ADMIN and await _active_admin_count(db, lock_rows=True) <= 1:
        raise HTTPException(
            status_code=409, detail="The final active administrator cannot be suspended"
        )
    if not activate and user.id == current_admin.id:
        raise HTTPException(
            status_code=409, detail="Use another administrator to suspend this account"
        )
    now = datetime.now(UTC)
    user.is_active = activate
    user.suspended_at = None if activate else now
    user.suspended_by_user_id = None if activate else current_admin.id
    user.suspension_reason = (
        None if activate else (payload.reason or "Suspended by an administrator")
    )
    user.session_version += 1
    await write_platform_audit(
        db,
        action="admin.user_activated" if activate else "admin.user_suspended",
        actor_id=current_admin.id,
        target_user_id=user.id,
        severity=AuditSeverity.INFO if activate else AuditSeverity.WARNING,
        ip_address=request.client.host if request.client else None,
        details={"reason": payload.reason},
    )
    await db.commit()
    await db.refresh(user)
    return _user_summary(user, await aggregate_counts_by_owner(db))


@router.post("/users/{user_id}/invalidate-sessions", response_model=AdminActionMessage)
async def invalidate_user_sessions(
    user_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> AdminActionMessage:
    user = await _get_user(db, user_id, for_update=True)
    user.session_version += 1
    await write_platform_audit(
        db,
        action="admin.sessions_invalidated",
        actor_id=current_admin.id,
        target_user_id=user.id,
        severity=AuditSeverity.WARNING,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return AdminActionMessage(message=f"All sessions for {user.email} were invalidated.")


@router.post("/users/{user_id}/password-reset", response_model=AdminActionMessage)
async def trigger_user_password_reset(
    user_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> AdminActionMessage:
    user = await _get_user(db, user_id)
    delivery = await create_password_reset_request(
        db, user.email, request.client.host if request.client else None
    )
    if delivery is not None:
        reset_user, raw_token = delivery
        background_tasks.add_task(
            send_password_reset_email, reset_user.email, reset_user.name, raw_token
        )
    await write_platform_audit(
        db,
        action="admin.password_reset_triggered",
        actor_id=current_admin.id,
        target_user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return AdminActionMessage(message="A password-recovery email was requested for this user.")


@router.get("/projects", response_model=list[AdminProjectSummary])
async def list_all_projects(
    db: DbSession,
    current_admin: CurrentAdmin,
    search: str | None = Query(default=None, max_length=200),
    project_status: ProjectStatus | None = None,
) -> list[AdminProjectSummary]:
    del current_admin
    query = select(Project, User).join(User, User.id == Project.owner_id)
    if search:
        pattern = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(Project.name).like(pattern),
                func.lower(User.name).like(pattern),
                func.lower(User.email).like(pattern),
            )
        )
    if project_status:
        query = query.where(Project.status == project_status)
    rows = (await db.execute(query.order_by(Project.updated_at.desc()))).all()
    counts = await aggregate_counts_by_project(db)
    return [
        AdminProjectSummary(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            owner_id=owner.id,
            owner_name=owner.name,
            owner_email=owner.email,
            created_at=project.created_at,
            updated_at=project.updated_at,
            document_count=counts["documents"].get(project.id, 0),
            failed_document_count=counts["failed_documents"].get(project.id, 0),
            requirement_count=counts["requirements"].get(project.id, 0),
            test_case_count=counts["test_cases"].get(project.id, 0),
            release_candidate_count=counts["releases"].get(project.id, 0),
            high_risk_impact_count=counts["high_risk"].get(project.id, 0),
        )
        for project, owner in rows
    ]


@router.patch("/projects/{project_id}/status", response_model=AdminProjectSummary)
async def update_project_status(
    project_id: UUID,
    payload: AdminProjectStatusUpdate,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> AdminProjectSummary:
    project = await _get_project(db, project_id, for_update=True)
    project.status = payload.status
    await write_platform_audit(
        db,
        action="admin.project_archived"
        if payload.status == ProjectStatus.ARCHIVED
        else "admin.project_restored",
        actor_id=current_admin.id,
        project_id=project.id,
        ip_address=request.client.host if request.client else None,
        details={"reason": payload.reason},
    )
    await db.commit()
    rows = await list_all_projects(db, current_admin, search=project.name)
    return next(item for item in rows if item.id == project.id)


@router.post("/projects/{project_id}/transfer", response_model=AdminProjectSummary)
async def transfer_project(
    project_id: UUID,
    payload: AdminProjectTransfer,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> AdminProjectSummary:
    project = await _get_project(db, project_id, for_update=True)
    new_owner = await _get_user(db, payload.new_owner_id)
    if not new_owner.is_active:
        raise HTTPException(
            status_code=409, detail="Project ownership cannot be transferred to a suspended user"
        )
    duplicate = await db.execute(
        select(Project.id).where(
            Project.owner_id == new_owner.id,
            Project.id != project.id,
            func.lower(Project.name) == project.name.lower(),
        )
    )
    if duplicate.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409, detail="The new owner already has a project with this name"
        )
    previous_owner_id = project.owner_id
    project.owner_id = new_owner.id
    await write_platform_audit(
        db,
        action="admin.project_ownership_transferred",
        actor_id=current_admin.id,
        target_user_id=new_owner.id,
        project_id=project.id,
        severity=AuditSeverity.WARNING,
        ip_address=request.client.host if request.client else None,
        details={
            "previous_owner_id": str(previous_owner_id),
            "new_owner_id": str(new_owner.id),
            "reason": payload.reason,
        },
    )
    await db.commit()
    rows = await list_all_projects(db, current_admin, search=project.name)
    return next(item for item in rows if item.id == project.id)


@router.get("/audit", response_model=PlatformAuditPage)
async def list_audit_events(
    db: DbSession,
    current_admin: CurrentAdmin,
    search: str | None = Query(default=None, max_length=200),
    action: str | None = Query(default=None, max_length=100),
    severity: AuditSeverity | None = None,
    user_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> PlatformAuditPage:
    del current_admin
    items, total = await _audit_rows(
        db,
        search=search,
        action=action,
        severity=severity,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return PlatformAuditPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/audit/export")
async def export_audit_events(
    db: DbSession,
    current_admin: CurrentAdmin,
    export_format: Literal["json", "csv"] = Query(default="csv", alias="format"),
) -> Response:
    del current_admin
    items, _ = await _audit_rows(db, limit=5000)
    if export_format == "json":
        return Response(
            content=PlatformAuditPage(
                items=items, total=len(items), limit=len(items), offset=0
            ).model_dump_json(indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="atlas-platform-audit.json"'},
        )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "timestamp",
            "severity",
            "action",
            "actor",
            "target_user",
            "project",
            "ip_address",
            "details",
        ]
    )
    for item in items:
        writer.writerow(
            [
                item.created_at.isoformat(),
                item.severity.value,
                item.action,
                item.actor_email or item.actor_name or "system",
                item.target_user_name or "",
                item.project_name or "",
                item.ip_address or "",
                item.details,
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="atlas-platform-audit.csv"'},
    )


@router.get("/system", response_model=AdminSystemRead)
async def system_health(db: DbSession, current_admin: CurrentAdmin) -> AdminSystemRead:
    del current_admin
    totals = await platform_totals(db)
    revision = await read_alembic_revision(db)
    ollama_status, ollama_message = await check_ollama()
    smtp_status, smtp_message = await check_smtp()
    upload_bytes = directory_size(settings.UPLOAD_ROOT)
    vector_bytes = directory_size(settings.CHROMA_PERSIST_ROOT)
    model_bytes = directory_size(settings.MODEL_CACHE_ROOT)
    return AdminSystemRead(
        application_version=settings.APP_VERSION,
        alembic_revision=revision,
        database_status="healthy",
        services=[
            SystemServiceRead(
                key="backend",
                label="Backend API",
                status="healthy",
                message="FastAPI is serving authenticated requests.",
            ),
            SystemServiceRead(
                key="database",
                label="PostgreSQL",
                status="healthy",
                message="Database connectivity is operational.",
            ),
            SystemServiceRead(
                key="ai", label="Ollama", status=ollama_status, message=ollama_message
            ),
            SystemServiceRead(
                key="email", label="Email service", status=smtp_status, message=smtp_message
            ),
        ],
        storage_usage_bytes=upload_bytes + vector_bytes + model_bytes,
        upload_storage_bytes=upload_bytes,
        vector_storage_bytes=vector_bytes,
        model_storage_bytes=model_bytes,
        failed_document_count=totals["failed_documents"],
        ready_ai_index_count=totals["ready_ai_indexes"],
        total_ai_index_count=totals["ai_indexes"],
        recent_critical_event_count=totals["critical_events"],
    )


@router.get("/settings", response_model=PlatformSettingsRead)
async def read_settings(db: DbSession, current_admin: CurrentAdmin):
    del current_admin
    item = await get_platform_settings(db)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/settings", response_model=PlatformSettingsRead)
async def update_settings(
    payload: PlatformSettingsUpdate,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    item = await get_platform_settings(db, for_update=True)
    changes: dict[str, object] = {}
    for field, value in payload.model_dump().items():
        if getattr(item, field) != value:
            changes[field] = {"from": getattr(item, field), "to": value}
            setattr(item, field, value)
    item.updated_by_id = current_admin.id
    await write_platform_audit(
        db,
        action="admin.platform_settings_updated",
        actor_id=current_admin.id,
        severity=AuditSeverity.WARNING if payload.maintenance_mode else AuditSeverity.INFO,
        ip_address=request.client.host if request.client else None,
        details={"changes": changes},
    )
    await db.commit()
    await db.refresh(item)
    return item
