from __future__ import annotations

import re
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import delete, select

from app.api.dependencies import CurrentUser, DbSession
from app.api.v1.endpoints.projects import get_owned_project
from app.api.v1.endpoints.requirements import get_owned_requirement
from app.models.artifact import Artifact, ArtifactType
from app.models.requirement import Requirement
from app.models.trace_link import (
    TraceLink,
    TraceLinkSource,
    TraceLinkStatus,
)
from app.schemas.traceability import (
    ArtifactCreate,
    ArtifactRead,
    ArtifactSummaryRead,
    ArtifactUpdate,
    TraceabilityMatrixArtifact,
    TraceabilityMatrixCell,
    TraceabilityMatrixRead,
    TraceabilityMatrixRequirement,
    TraceabilitySummaryRead,
    TraceLinkCreate,
    TraceLinkRead,
    TraceLinkUpdate,
    TraceSuggestionRead,
    TraceSuggestionRequest,
)
from app.services.traceability import calculate_coverage, infer_link_type, score_trace_candidate

artifact_router = APIRouter(prefix="/projects/{project_id}/artifacts", tags=["artifacts"])
trace_router = APIRouter(prefix="/projects/{project_id}/trace-links", tags=["traceability"])
traceability_router = APIRouter(
    prefix="/projects/{project_id}/traceability",
    tags=["traceability"],
)
ARTIFACT_CODE_PATTERN = re.compile(r"^ART-(\d+)$")


async def get_owned_artifact(
    db: DbSession,
    project_id: UUID,
    artifact_id: UUID,
    owner_id: UUID,
) -> Artifact:
    await get_owned_project(db, project_id, owner_id)
    result = await db.execute(
        select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.project_id == project_id,
        )
    )
    artifact = result.scalar_one_or_none()
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


async def get_owned_trace_link(
    db: DbSession,
    project_id: UUID,
    trace_link_id: UUID,
    owner_id: UUID,
) -> TraceLink:
    await get_owned_project(db, project_id, owner_id)
    result = await db.execute(
        select(TraceLink).where(
            TraceLink.id == trace_link_id,
            TraceLink.project_id == project_id,
        )
    )
    trace_link = result.scalar_one_or_none()
    if trace_link is None:
        raise HTTPException(status_code=404, detail="Trace link not found")
    return trace_link


async def next_artifact_number(db: DbSession, project_id: UUID) -> int:
    result = await db.execute(select(Artifact.code).where(Artifact.project_id == project_id))
    numbers = [
        int(match.group(1))
        for code in result.scalars().all()
        if (match := ARTIFACT_CODE_PATTERN.match(code)) is not None
    ]
    return max(numbers, default=0) + 1


@artifact_router.post("", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    project_id: UUID,
    payload: ArtifactCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Artifact:
    await get_owned_project(db, project_id, current_user.id)
    sequence = await next_artifact_number(db, project_id)
    artifact = Artifact(
        project_id=project_id,
        code=f"ART-{sequence:04d}",
        name=payload.name.strip(),
        artifact_type=payload.artifact_type,
        description=payload.description.strip(),
        technical_details=payload.technical_details,
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)
    return artifact


@artifact_router.get("", response_model=list[ArtifactRead])
async def list_artifacts(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    artifact_type: ArtifactType | None = None,
) -> list[Artifact]:
    await get_owned_project(db, project_id, current_user.id)
    statement = select(Artifact).where(Artifact.project_id == project_id)
    if artifact_type is not None:
        statement = statement.where(Artifact.artifact_type == artifact_type)
    result = await db.execute(statement.order_by(Artifact.code.asc()))
    return list(result.scalars().all())


@artifact_router.get("/summary", response_model=ArtifactSummaryRead)
async def artifact_summary(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ArtifactSummaryRead:
    await get_owned_project(db, project_id, current_user.id)
    result = await db.execute(
        select(Artifact.artifact_type).where(Artifact.project_id == project_id)
    )
    types = list(result.scalars().all())
    return ArtifactSummaryRead(
        total=len(types),
        api=types.count(ArtifactType.API),
        database_table=types.count(ArtifactType.DATABASE_TABLE),
        test_case=types.count(ArtifactType.TEST_CASE),
        uml_component=types.count(ArtifactType.UML_COMPONENT),
    )


@artifact_router.get("/{artifact_id}", response_model=ArtifactRead)
async def read_artifact(
    project_id: UUID,
    artifact_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Artifact:
    return await get_owned_artifact(db, project_id, artifact_id, current_user.id)


@artifact_router.patch("/{artifact_id}", response_model=ArtifactRead)
async def update_artifact(
    project_id: UUID,
    artifact_id: UUID,
    payload: ArtifactUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Artifact:
    artifact = await get_owned_artifact(db, project_id, artifact_id, current_user.id)
    updates = payload.model_dump(exclude_unset=True)
    for field in ("name", "description"):
        if field in updates and updates[field] is not None:
            updates[field] = updates[field].strip()
    for field, value in updates.items():
        setattr(artifact, field, value)
    await db.commit()
    await db.refresh(artifact)
    return artifact


@artifact_router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(
    project_id: UUID,
    artifact_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    artifact = await get_owned_artifact(db, project_id, artifact_id, current_user.id)
    await db.delete(artifact)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@trace_router.post("", response_model=TraceLinkRead, status_code=status.HTTP_201_CREATED)
async def create_trace_link(
    project_id: UUID,
    payload: TraceLinkCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> TraceLink:
    await get_owned_project(db, project_id, current_user.id)
    await get_owned_requirement(db, project_id, payload.requirement_id, current_user.id)
    artifact = await get_owned_artifact(db, project_id, payload.artifact_id, current_user.id)

    existing_result = await db.execute(
        select(TraceLink).where(
            TraceLink.project_id == project_id,
            TraceLink.requirement_id == payload.requirement_id,
            TraceLink.artifact_id == payload.artifact_id,
        )
    )
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="This trace link already exists")

    trace_link = TraceLink(
        project_id=project_id,
        requirement_id=payload.requirement_id,
        artifact_id=payload.artifact_id,
        link_type=payload.link_type or infer_link_type(artifact.artifact_type),
        status=TraceLinkStatus.ACCEPTED,
        source=TraceLinkSource.MANUAL,
        confidence_score=payload.confidence_score,
        evidence={"note": payload.evidence_note} if payload.evidence_note else {},
    )
    db.add(trace_link)
    await db.commit()
    await db.refresh(trace_link)
    return trace_link


@trace_router.post("/suggest", response_model=TraceSuggestionRead)
async def suggest_trace_links(
    project_id: UUID,
    payload: TraceSuggestionRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> TraceSuggestionRead:
    await get_owned_project(db, project_id, current_user.id)

    if payload.replace_system_suggestions:
        await db.execute(
            delete(TraceLink).where(
                TraceLink.project_id == project_id,
                TraceLink.source == TraceLinkSource.SYSTEM,
                TraceLink.status == TraceLinkStatus.SUGGESTED,
            )
        )
        await db.flush()

    requirements_result = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id)
    )
    artifacts_result = await db.execute(select(Artifact).where(Artifact.project_id == project_id))
    requirements = list(requirements_result.scalars().all())
    artifacts = list(artifacts_result.scalars().all())

    if not requirements:
        raise HTTPException(status_code=409, detail="Create or extract requirements first")
    if not artifacts:
        raise HTTPException(status_code=409, detail="Create software artifacts first")

    existing_result = await db.execute(
        select(TraceLink.requirement_id, TraceLink.artifact_id).where(
            TraceLink.project_id == project_id
        )
    )
    existing_pairs = {
        (row.requirement_id, row.artifact_id) for row in existing_result.all()
    }
    created: list[TraceLink] = []
    skipped_existing = 0
    below_threshold = 0

    for requirement in requirements:
        requirement_text = f"{requirement.title} {requirement.description}"
        for artifact in artifacts:
            pair = (requirement.id, artifact.id)
            if pair in existing_pairs:
                skipped_existing += 1
                continue
            score = score_trace_candidate(
                requirement_text,
                artifact.name,
                artifact.description,
                artifact.artifact_type,
            )
            if score.confidence_score < payload.minimum_confidence:
                below_threshold += 1
                continue

            trace_link = TraceLink(
                project_id=project_id,
                requirement_id=requirement.id,
                artifact_id=artifact.id,
                link_type=score.link_type,
                status=TraceLinkStatus.SUGGESTED,
                source=TraceLinkSource.SYSTEM,
                confidence_score=score.confidence_score,
                evidence={
                    "shared_terms": score.shared_terms,
                    "artifact_type_cues": score.artifact_type_cues,
                    "rationale": score.rationale,
                },
            )
            db.add(trace_link)
            created.append(trace_link)
            existing_pairs.add(pair)

    await db.commit()
    for trace_link in created:
        await db.refresh(trace_link)

    return TraceSuggestionRead(
        evaluated_pairs=len(requirements) * len(artifacts),
        created_count=len(created),
        skipped_existing_count=skipped_existing,
        below_threshold_count=below_threshold,
        links=[TraceLinkRead.model_validate(item) for item in created],
    )


@trace_router.get("", response_model=list[TraceLinkRead])
async def list_trace_links(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    requirement_id: UUID | None = None,
    artifact_id: UUID | None = None,
    trace_status: Annotated[TraceLinkStatus | None, Query(alias="status")] = None,
) -> list[TraceLink]:
    await get_owned_project(db, project_id, current_user.id)
    statement = select(TraceLink).where(TraceLink.project_id == project_id)
    if requirement_id is not None:
        statement = statement.where(TraceLink.requirement_id == requirement_id)
    if artifact_id is not None:
        statement = statement.where(TraceLink.artifact_id == artifact_id)
    if trace_status is not None:
        statement = statement.where(TraceLink.status == trace_status)
    result = await db.execute(statement.order_by(TraceLink.created_at.desc()))
    return list(result.scalars().all())


@trace_router.patch("/{trace_link_id}", response_model=TraceLinkRead)
async def update_trace_link(
    project_id: UUID,
    trace_link_id: UUID,
    payload: TraceLinkUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> TraceLink:
    trace_link = await get_owned_trace_link(
        db,
        project_id,
        trace_link_id,
        current_user.id,
    )
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(trace_link, field, value)
    await db.commit()
    await db.refresh(trace_link)
    return trace_link


@trace_router.delete("/{trace_link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trace_link(
    project_id: UUID,
    trace_link_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    trace_link = await get_owned_trace_link(
        db,
        project_id,
        trace_link_id,
        current_user.id,
    )
    await db.delete(trace_link)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@traceability_router.get("/summary", response_model=TraceabilitySummaryRead)
async def traceability_summary(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> TraceabilitySummaryRead:
    await get_owned_project(db, project_id, current_user.id)
    requirements_result = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id).order_by(Requirement.code)
    )
    artifacts_result = await db.execute(
        select(Artifact).where(Artifact.project_id == project_id).order_by(Artifact.code)
    )
    links_result = await db.execute(
        select(TraceLink).where(TraceLink.project_id == project_id)
    )
    coverage = calculate_coverage(
        list(requirements_result.scalars().all()),
        list(artifacts_result.scalars().all()),
        list(links_result.scalars().all()),
    )
    return TraceabilitySummaryRead(**coverage)


@traceability_router.get("/matrix", response_model=TraceabilityMatrixRead)
async def traceability_matrix(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> TraceabilityMatrixRead:
    await get_owned_project(db, project_id, current_user.id)
    requirements_result = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id).order_by(Requirement.code)
    )
    artifacts_result = await db.execute(
        select(Artifact).where(Artifact.project_id == project_id).order_by(Artifact.code)
    )
    links_result = await db.execute(
        select(TraceLink).where(TraceLink.project_id == project_id)
    )
    requirements = list(requirements_result.scalars().all())
    artifacts = list(artifacts_result.scalars().all())
    links = list(links_result.scalars().all())

    return TraceabilityMatrixRead(
        requirements=[
            TraceabilityMatrixRequirement(
                id=requirement.id,
                code=requirement.code,
                title=requirement.title,
            )
            for requirement in requirements
        ],
        artifacts=[
            TraceabilityMatrixArtifact(
                id=artifact.id,
                code=artifact.code,
                name=artifact.name,
                artifact_type=artifact.artifact_type,
            )
            for artifact in artifacts
        ],
        cells=[
            TraceabilityMatrixCell(
                requirement_id=link.requirement_id,
                artifact_id=link.artifact_id,
                trace_link_id=link.id,
                link_type=link.link_type,
                status=link.status,
                confidence_score=link.confidence_score,
            )
            for link in links
        ],
    )
