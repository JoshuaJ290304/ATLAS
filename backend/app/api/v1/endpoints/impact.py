from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DbSession
from app.api.v1.endpoints.projects import get_owned_project
from app.api.v1.endpoints.requirements import get_owned_requirement
from app.models.artifact import Artifact
from app.models.impact import ImpactAnalysis, ImpactSeverity, RequirementVersion
from app.models.requirement import Requirement
from app.models.trace_link import TraceLink, TraceLinkStatus
from app.schemas.impact import (
    ImpactAnalysisCreate,
    ImpactAnalysisRead,
    ImpactSummaryRead,
    RequirementVersionComparisonRead,
    RequirementVersionRead,
)
from app.services.impact import (
    assess_risk,
    build_change_summary,
    build_impact_graph,
    compare_versions,
    ensure_requirement_snapshot,
)

version_router = APIRouter(
    prefix="/projects/{project_id}/requirements",
    tags=["impact analysis"],
)
impact_router = APIRouter(
    prefix="/projects/{project_id}/impact-analyses",
    tags=["impact analysis"],
)


async def get_requirement_versions(
    db: DbSession,
    requirement: Requirement,
) -> list[RequirementVersion]:
    await ensure_requirement_snapshot(db, requirement)
    await db.flush()
    result = await db.execute(
        select(RequirementVersion)
        .where(RequirementVersion.requirement_id == requirement.id)
        .order_by(RequirementVersion.version.asc())
    )
    return list(result.scalars().all())


async def get_owned_impact_analysis(
    db: DbSession,
    project_id: UUID,
    analysis_id: UUID,
    owner_id: UUID,
) -> ImpactAnalysis:
    await get_owned_project(db, project_id, owner_id)
    result = await db.execute(
        select(ImpactAnalysis).where(
            ImpactAnalysis.id == analysis_id,
            ImpactAnalysis.project_id == project_id,
        )
    )
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Impact analysis not found")
    return analysis


@version_router.get(
    "/{requirement_id}/versions",
    response_model=list[RequirementVersionRead],
)
async def list_requirement_versions(
    project_id: UUID,
    requirement_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[RequirementVersion]:
    requirement = await get_owned_requirement(db, project_id, requirement_id, current_user.id)
    versions = await get_requirement_versions(db, requirement)
    await db.commit()
    return versions


@version_router.get(
    "/{requirement_id}/compare",
    response_model=RequirementVersionComparisonRead,
)
async def compare_requirement_version_endpoint(
    project_id: UUID,
    requirement_id: UUID,
    baseline_version: Annotated[int, Query(ge=1)],
    target_version: Annotated[int, Query(ge=1)],
    db: DbSession,
    current_user: CurrentUser,
) -> RequirementVersionComparisonRead:
    if baseline_version >= target_version:
        raise HTTPException(status_code=422, detail="Baseline version must be lower than target")
    requirement = await get_owned_requirement(db, project_id, requirement_id, current_user.id)
    versions = await get_requirement_versions(db, requirement)
    by_number = {item.version: item for item in versions}
    baseline = by_number.get(baseline_version)
    target = by_number.get(target_version)
    if baseline is None or target is None:
        raise HTTPException(
            status_code=404,
            detail="One or both requirement versions were not found",
        )
    comparison = compare_versions(baseline, target)
    await db.commit()
    return RequirementVersionComparisonRead(
        requirement_id=requirement.id,
        requirement_code=requirement.code,
        baseline=RequirementVersionRead.model_validate(baseline),
        target=RequirementVersionRead.model_validate(target),
        change_type=comparison.change_type,
        changed_fields=comparison.changed_fields,
        text_similarity=comparison.text_similarity,
        change_ratio=comparison.change_ratio,
        added_terms=comparison.added_terms,
        removed_terms=comparison.removed_terms,
        unified_diff=comparison.unified_diff,
        field_changes=comparison.field_changes,
    )


@impact_router.post(
    "",
    response_model=ImpactAnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_impact_analysis(
    project_id: UUID,
    payload: ImpactAnalysisCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ImpactAnalysis:
    await get_owned_project(db, project_id, current_user.id)
    requirement = await get_owned_requirement(
        db,
        project_id,
        payload.requirement_id,
        current_user.id,
    )
    versions = await get_requirement_versions(db, requirement)
    by_number = {item.version: item for item in versions}

    target = (
        by_number.get(payload.target_version)
        if payload.target_version is not None
        else versions[-1]
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Target requirement version was not found")

    if payload.baseline_version is not None:
        baseline = by_number.get(payload.baseline_version)
    else:
        prior_versions = [item for item in versions if item.version < target.version]
        baseline = prior_versions[-1] if prior_versions else None

    if baseline is None:
        raise HTTPException(
            status_code=409,
            detail="Edit the requirement once to create a previous version before analysis",
        )
    if baseline.version >= target.version:
        raise HTTPException(status_code=422, detail="Baseline version must be lower than target")

    comparison = compare_versions(baseline, target)

    requirements_result = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id)
    )
    artifacts_result = await db.execute(select(Artifact).where(Artifact.project_id == project_id))
    links_result = await db.execute(
        select(TraceLink).where(
            TraceLink.project_id == project_id,
            TraceLink.status == TraceLinkStatus.ACCEPTED,
        )
    )
    graph = build_impact_graph(
        requirement.id,
        list(requirements_result.scalars().all()),
        list(artifacts_result.scalars().all()),
        list(links_result.scalars().all()),
    )
    risk = assess_risk(
        comparison,
        target,
        graph.direct_artifacts,
        graph.transitive_artifacts,
    )
    summary = build_change_summary(
        requirement.code,
        baseline.version,
        target.version,
        comparison,
        len(graph.direct_artifacts),
        len(graph.transitive_artifacts),
        risk,
    )
    differences = {
        "changed_fields": comparison.changed_fields,
        "text_similarity": comparison.text_similarity,
        "change_ratio": comparison.change_ratio,
        "added_terms": comparison.added_terms,
        "removed_terms": comparison.removed_terms,
        "unified_diff": comparison.unified_diff,
        "field_changes": comparison.field_changes,
    }
    analysis = ImpactAnalysis(
        project_id=project_id,
        requirement_id=requirement.id,
        requirement_code=requirement.code,
        requirement_title=requirement.title,
        baseline_version=baseline.version,
        target_version=target.version,
        change_type=comparison.change_type,
        risk_score=risk.risk_score,
        severity=risk.severity,
        change_summary=summary,
        differences=differences,
        direct_artifacts=graph.direct_artifacts,
        transitive_artifacts=graph.transitive_artifacts,
        risk_factors=risk.factors,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis


@impact_router.get("", response_model=list[ImpactAnalysisRead])
async def list_impact_analyses(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    requirement_id: UUID | None = None,
    severity: ImpactSeverity | None = None,
) -> list[ImpactAnalysis]:
    await get_owned_project(db, project_id, current_user.id)
    statement = select(ImpactAnalysis).where(ImpactAnalysis.project_id == project_id)
    if requirement_id is not None:
        statement = statement.where(ImpactAnalysis.requirement_id == requirement_id)
    if severity is not None:
        statement = statement.where(ImpactAnalysis.severity == severity)
    result = await db.execute(statement.order_by(ImpactAnalysis.created_at.desc()))
    return list(result.scalars().all())


@impact_router.get("/summary", response_model=ImpactSummaryRead)
async def impact_summary(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ImpactSummaryRead:
    await get_owned_project(db, project_id, current_user.id)
    result = await db.execute(
        select(ImpactAnalysis)
        .where(ImpactAnalysis.project_id == project_id)
        .order_by(ImpactAnalysis.created_at.desc())
    )
    analyses = list(result.scalars().all())
    latest = analyses[0] if analyses else None
    return ImpactSummaryRead(
        total=len(analyses),
        low=sum(item.severity == ImpactSeverity.LOW for item in analyses),
        medium=sum(item.severity == ImpactSeverity.MEDIUM for item in analyses),
        high=sum(item.severity == ImpactSeverity.HIGH for item in analyses),
        critical=sum(item.severity == ImpactSeverity.CRITICAL for item in analyses),
        latest_risk_score=latest.risk_score if latest else None,
        latest_severity=latest.severity if latest else None,
    )


@impact_router.get("/{analysis_id}", response_model=ImpactAnalysisRead)
async def read_impact_analysis(
    project_id: UUID,
    analysis_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ImpactAnalysis:
    return await get_owned_impact_analysis(db, project_id, analysis_id, current_user.id)


@impact_router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_impact_analysis(
    project_id: UUID,
    analysis_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    analysis = await get_owned_impact_analysis(db, project_id, analysis_id, current_user.id)
    await db.delete(analysis)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
