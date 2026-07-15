from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DbSession
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.assistant import delete_project_vectors
from app.services.documents import remove_project_upload_directory

router = APIRouter(prefix="/projects", tags=["projects"])


async def get_owned_project(db: DbSession, project_id: UUID, owner_id: UUID) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Project:
    duplicate = await db.execute(
        select(Project.id).where(
            Project.owner_id == current_user.id,
            func.lower(Project.name) == payload.name.lower(),
        )
    )
    if duplicate.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="A project with this name already exists")

    project = Project(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
async def list_projects(db: DbSession, current_user: CurrentUser) -> list[Project]:
    result = await db.execute(
        select(Project)
        .where(Project.owner_id == current_user.id)
        .order_by(Project.updated_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{project_id}", response_model=ProjectRead)
async def read_project(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Project:
    return await get_owned_project(db, project_id, current_user.id)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Project:
    project = await get_owned_project(db, project_id, current_user.id)
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"] is not None:
        duplicate = await db.execute(
            select(Project.id).where(
                Project.owner_id == current_user.id,
                Project.id != project.id,
                func.lower(Project.name) == updates["name"].lower(),
            )
        )
        if duplicate.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="A project with this name already exists")
    for field, value in updates.items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    project = await get_owned_project(db, project_id, current_user.id)
    await delete_project_vectors(project_id)
    await db.delete(project)
    await db.commit()
    remove_project_upload_directory(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
