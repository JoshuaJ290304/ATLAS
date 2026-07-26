from __future__ import annotations

import csv
import io
from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.api.v1.endpoints.projects import get_owned_project
from app.models.assistant import AssistantIndex, AssistantIndexStatus
from app.models.document import Document, DocumentStatus
from app.models.governance import (
    AuditLog,
    BaselineStatus,
    ProjectBaseline,
    RequirementReview,
    ReviewStatus,
)
from app.models.impact import ImpactAnalysis, ImpactSeverity
from app.models.release_readiness import (
    ReleaseCandidate,
    ReleaseCandidateStatus,
    ReleaseGateEvaluation,
    ReleaseReadinessLabel,
)
from app.models.requirement import Requirement, RequirementStatus
from app.models.test_case import TestCase, TestCaseStatus
from app.models.trace_link import TraceLink, TraceLinkStatus
from app.schemas.release_readiness import (
    ReleaseCandidateCreate,
    ReleaseCandidateRead,
    ReleaseCandidateUpdate,
    ReleaseComparisonCreate,
    ReleaseComparisonRead,
    ReleaseDecisionCreate,
    ReleaseEvaluationRead,
    ReleaseWorkspaceSummary,
)
from app.services.release_readiness import compare_release_snapshots, evaluate_release_evidence

router = APIRouter(prefix="/projects/{project_id}/releases", tags=["release readiness"])


def _uuid_list(values: list[str]) -> list[UUID]:
    return [UUID(value) for value in values]


async def _candidate(
    db: DbSession,
    project_id: UUID,
    release_id: UUID,
    owner_id: UUID,
) -> ReleaseCandidate:
    await get_owned_project(db, project_id, owner_id)
    result = await db.execute(
        select(ReleaseCandidate)
        .options(selectinload(ReleaseCandidate.evaluations))
        .where(
            ReleaseCandidate.id == release_id,
            ReleaseCandidate.project_id == project_id,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Release candidate not found")
    return item


async def _audit(
    db: DbSession,
    *,
    project_id: UUID,
    actor_id: UUID,
    action: str,
    entity_id: UUID,
    details: dict[str, object],
) -> None:
    db.add(
        AuditLog(
            project_id=project_id,
            actor_id=actor_id,
            action=action,
            entity_type="release_candidate",
            entity_id=entity_id,
            details=details,
        )
    )


async def _validate_selection(
    db: DbSession,
    project_id: UUID,
    baseline_id: UUID | None,
    requirement_ids: list[UUID],
    test_case_ids: list[UUID],
) -> tuple[ProjectBaseline | None, list[Requirement], list[TestCase]]:
    baseline = None
    if baseline_id:
        baseline = (
            await db.execute(
                select(ProjectBaseline).where(
                    ProjectBaseline.id == baseline_id,
                    ProjectBaseline.project_id == project_id,
                )
            )
        ).scalar_one_or_none()
        if baseline is None:
            raise HTTPException(
                status_code=422, detail="Selected baseline does not belong to this project"
            )

    requirements = list(
        (
            await db.execute(
                select(Requirement).where(
                    Requirement.project_id == project_id,
                    Requirement.id.in_(requirement_ids),
                )
            )
        )
        .scalars()
        .all()
    )
    if len(requirements) != len(requirement_ids):
        raise HTTPException(
            status_code=422,
            detail="One or more selected requirements do not belong to this project",
        )

    tests: list[TestCase] = []
    if test_case_ids:
        tests = list(
            (
                await db.execute(
                    select(TestCase).where(
                        TestCase.project_id == project_id,
                        TestCase.id.in_(test_case_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        if len(tests) != len(test_case_ids):
            raise HTTPException(
                status_code=422,
                detail="One or more selected test cases do not belong to this project",
            )
    return baseline, requirements, tests


async def _collect_evidence(db: DbSession, item: ReleaseCandidate) -> dict[str, object]:
    requirement_ids = _uuid_list(item.selected_requirement_ids)
    test_case_ids = _uuid_list(item.selected_test_case_ids)
    baseline, requirements, tests = await _validate_selection(
        db, item.project_id, item.baseline_id, requirement_ids, test_case_ids
    )
    requirement_by_id = {requirement.id: requirement for requirement in requirements}

    approved_requirements = [
        requirement
        for requirement in requirements
        if requirement.status == RequirementStatus.APPROVED
    ]
    unapproved = [
        requirement.code
        for requirement in requirements
        if requirement.status != RequirementStatus.APPROVED
    ]
    critical_ambiguities = [
        requirement.code for requirement in requirements if requirement.ambiguity_score >= 70
    ]

    accepted_requirement_ids = set(
        (
            await db.execute(
                select(TraceLink.requirement_id).where(
                    TraceLink.project_id == item.project_id,
                    TraceLink.requirement_id.in_(requirement_ids),
                    TraceLink.status == TraceLinkStatus.ACCEPTED,
                )
            )
        )
        .scalars()
        .all()
    )
    traced_count = len(accepted_requirement_ids)
    untraced_codes = [
        requirement.code
        for requirement in requirements
        if requirement.id not in accepted_requirement_ids
    ]

    approved_test_requirement_ids = {
        test.requirement_id
        for test in tests
        if test.status == TestCaseStatus.APPROVED and test.requirement_id in requirement_by_id
    }
    untested_codes = [
        requirement.code
        for requirement in requirements
        if requirement.id not in approved_test_requirement_ids
    ]

    impact_rows = list(
        (
            await db.execute(
                select(ImpactAnalysis)
                .where(
                    ImpactAnalysis.project_id == item.project_id,
                    ImpactAnalysis.requirement_id.in_(requirement_ids),
                )
                .order_by(ImpactAnalysis.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    latest_impact_by_requirement: dict[UUID, ImpactAnalysis] = {}
    for impact in impact_rows:
        if impact.requirement_id and impact.requirement_id not in latest_impact_by_requirement:
            latest_impact_by_requirement[impact.requirement_id] = impact
    high_risk_impacts = [
        impact
        for impact in latest_impact_by_requirement.values()
        if impact.severity in {ImpactSeverity.HIGH, ImpactSeverity.CRITICAL}
    ]

    overdue_rows = list(
        (
            await db.execute(
                select(RequirementReview.requirement_id).where(
                    RequirementReview.project_id == item.project_id,
                    RequirementReview.requirement_id.in_(requirement_ids),
                    RequirementReview.status == ReviewStatus.PENDING,
                    RequirementReview.due_date.is_not(None),
                    RequirementReview.due_date < date.today(),
                )
            )
        )
        .scalars()
        .all()
    )
    overdue_codes = sorted(
        {
            requirement_by_id[requirement_id].code
            for requirement_id in overdue_rows
            if requirement_id in requirement_by_id
        }
    )

    rejected_codes = [
        requirement.code
        for requirement in requirements
        if requirement.status == RequirementStatus.REJECTED
    ] + [test.code for test in tests if test.status == TestCaseStatus.REJECTED]

    documents = list(
        (await db.execute(select(Document).where(Document.project_id == item.project_id)))
        .scalars()
        .all()
    )
    processed_documents = [
        document for document in documents if document.status == DocumentStatus.EXTRACTED
    ]
    failed_documents = [
        document for document in documents if document.status == DocumentStatus.FAILED
    ]

    assistant_index = (
        await db.execute(select(AssistantIndex).where(AssistantIndex.project_id == item.project_id))
    ).scalar_one_or_none()
    latest_evidence_time = max(
        [entity.updated_at for entity in [*requirements, *tests, *documents] if entity.updated_at]
        or [item.updated_at]
    )
    index_ready = bool(assistant_index and assistant_index.status == AssistantIndexStatus.READY)
    index_fresh = bool(
        index_ready
        and assistant_index.last_indexed_at
        and assistant_index.last_indexed_at >= latest_evidence_time
    )

    count = len(requirements)
    return {
        "baseline_selected": baseline is not None,
        "baseline_active": bool(baseline and baseline.status == BaselineStatus.ACTIVE),
        "baseline_id": str(baseline.id) if baseline else None,
        "baseline_version": baseline.version_label if baseline else None,
        "selected_requirement_count": count,
        "approved_requirement_count": len(approved_requirements),
        "unapproved_requirement_codes": unapproved,
        "critical_ambiguity_count": len(critical_ambiguities),
        "critical_ambiguity_codes": critical_ambiguities,
        "traceability_percent": round((traced_count / count) * 100, 1) if count else 0.0,
        "untraced_requirement_codes": untraced_codes,
        "approved_test_coverage_percent": round(
            (len(approved_test_requirement_ids) / count) * 100, 1
        )
        if count
        else 0.0,
        "untested_requirement_codes": untested_codes,
        "included_test_case_count": len(tests),
        "approved_test_case_count": sum(
            1 for test in tests if test.status == TestCaseStatus.APPROVED
        ),
        "high_risk_impact_count": len(high_risk_impacts),
        "high_risk_requirement_codes": [impact.requirement_code for impact in high_risk_impacts],
        "overdue_review_count": len(overdue_codes),
        "overdue_review_codes": overdue_codes,
        "rejected_artifact_count": len(rejected_codes),
        "rejected_artifact_codes": rejected_codes,
        "document_count": len(documents),
        "processed_document_count": len(processed_documents),
        "failed_document_count": len(failed_documents),
        "ai_index_ready": index_ready,
        "ai_index_fresh": index_fresh,
        "ai_last_indexed_at": assistant_index.last_indexed_at.isoformat()
        if assistant_index and assistant_index.last_indexed_at
        else None,
    }


def _snapshot(item: ReleaseCandidate) -> dict[str, object]:
    return {
        "id": str(item.id),
        "name": item.name,
        "version_label": item.version_label,
        "status": item.status.value,
        "selected_requirement_ids": list(item.selected_requirement_ids),
        "selected_test_case_ids": list(item.selected_test_case_ids),
        "readiness_score": item.readiness_score,
        "readiness_label": item.readiness_label.value,
        "gate_results": item.gate_summary.get("results", []),
        "gate_summary": item.gate_summary.get("counts", {}),
        "blockers": list(item.blockers),
        "recommendations": list(item.recommendations),
        "evaluated_at": item.evaluated_at.isoformat() if item.evaluated_at else None,
        "signed_off_at": item.signed_off_at.isoformat() if item.signed_off_at else None,
    }


@router.get("", response_model=list[ReleaseCandidateRead])
async def list_releases(project_id: UUID, db: DbSession, current_user: CurrentUser):
    await get_owned_project(db, project_id, current_user.id)
    result = await db.execute(
        select(ReleaseCandidate)
        .where(ReleaseCandidate.project_id == project_id)
        .order_by(ReleaseCandidate.updated_at.desc())
    )
    return list(result.scalars().all())


@router.get("/summary", response_model=ReleaseWorkspaceSummary)
async def workspace_summary(project_id: UUID, db: DbSession, current_user: CurrentUser):
    await get_owned_project(db, project_id, current_user.id)
    rows = (
        await db.execute(
            select(ReleaseCandidate.status, func.count())
            .where(ReleaseCandidate.project_id == project_id)
            .group_by(ReleaseCandidate.status)
        )
    ).all()
    counts = {status_value: count for status_value, count in rows}
    average = (
        await db.execute(
            select(func.avg(ReleaseCandidate.readiness_score)).where(
                ReleaseCandidate.project_id == project_id,
                ReleaseCandidate.readiness_label != ReleaseReadinessLabel.NOT_EVALUATED,
            )
        )
    ).scalar_one_or_none()
    return ReleaseWorkspaceSummary(
        total=sum(counts.values()),
        draft=counts.get(ReleaseCandidateStatus.DRAFT, 0),
        in_review=counts.get(ReleaseCandidateStatus.IN_REVIEW, 0),
        ready=counts.get(ReleaseCandidateStatus.READY, 0),
        blocked=counts.get(ReleaseCandidateStatus.BLOCKED, 0),
        released=counts.get(ReleaseCandidateStatus.RELEASED, 0),
        average_readiness_score=round(float(average or 0), 1),
    )


@router.post("", response_model=ReleaseCandidateRead, status_code=status.HTTP_201_CREATED)
async def create_release(
    project_id: UUID,
    payload: ReleaseCandidateCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    await get_owned_project(db, project_id, current_user.id)
    duplicate = await db.execute(
        select(ReleaseCandidate.id).where(
            ReleaseCandidate.project_id == project_id,
            func.lower(ReleaseCandidate.version_label) == payload.version_label.lower(),
        )
    )
    if duplicate.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409, detail="A release candidate with this version already exists"
        )
    await _validate_selection(
        db,
        project_id,
        payload.baseline_id,
        payload.selected_requirement_ids,
        payload.selected_test_case_ids,
    )
    values = payload.model_dump()
    values["selected_requirement_ids"] = [str(value) for value in payload.selected_requirement_ids]
    values["selected_test_case_ids"] = [str(value) for value in payload.selected_test_case_ids]
    item = ReleaseCandidate(project_id=project_id, created_by_id=current_user.id, **values)
    db.add(item)
    await db.flush()
    await _audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action="release.created",
        entity_id=item.id,
        details={"name": item.name, "version": item.version_label},
    )
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/{release_id}", response_model=ReleaseCandidateRead)
async def read_release(
    project_id: UUID, release_id: UUID, db: DbSession, current_user: CurrentUser
):
    return await _candidate(db, project_id, release_id, current_user.id)


@router.put("/{release_id}", response_model=ReleaseCandidateRead)
async def update_release(
    project_id: UUID,
    release_id: UUID,
    payload: ReleaseCandidateUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    item = await _candidate(db, project_id, release_id, current_user.id)
    if item.locked_at or item.status == ReleaseCandidateStatus.RELEASED:
        raise HTTPException(status_code=409, detail="Released candidates are locked")
    await _validate_selection(
        db,
        project_id,
        payload.baseline_id,
        payload.selected_requirement_ids,
        payload.selected_test_case_ids,
    )
    duplicate = await db.execute(
        select(ReleaseCandidate.id).where(
            ReleaseCandidate.project_id == project_id,
            ReleaseCandidate.id != item.id,
            func.lower(ReleaseCandidate.version_label) == payload.version_label.lower(),
        )
    )
    if duplicate.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409, detail="A release candidate with this version already exists"
        )
    values = payload.model_dump(exclude={"status"})
    values["selected_requirement_ids"] = [str(value) for value in payload.selected_requirement_ids]
    values["selected_test_case_ids"] = [str(value) for value in payload.selected_test_case_ids]
    for field, value in values.items():
        setattr(item, field, value)
    item.readiness_label = ReleaseReadinessLabel.NOT_EVALUATED
    item.readiness_score = 0
    item.gate_summary = {}
    item.blockers = []
    item.recommendations = []
    item.evaluated_at = None
    if item.status not in {ReleaseCandidateStatus.DRAFT, ReleaseCandidateStatus.ARCHIVED}:
        item.status = ReleaseCandidateStatus.DRAFT
    await _audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action="release.updated",
        entity_id=item.id,
        details={"version": item.version_label, "evaluation_reset": True},
    )
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_release(
    project_id: UUID, release_id: UUID, db: DbSession, current_user: CurrentUser
):
    item = await _candidate(db, project_id, release_id, current_user.id)
    if item.status == ReleaseCandidateStatus.RELEASED or item.locked_at:
        raise HTTPException(status_code=409, detail="Released candidates cannot be deleted")
    await db.delete(item)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{release_id}/evaluate", response_model=ReleaseEvaluationRead)
async def evaluate_release(
    project_id: UUID, release_id: UUID, db: DbSession, current_user: CurrentUser
):
    item = await _candidate(db, project_id, release_id, current_user.id)
    if item.locked_at:
        raise HTTPException(status_code=409, detail="Released candidates are locked")
    evidence = await _collect_evidence(db, item)
    result = evaluate_release_evidence(
        evidence,
        minimum_traceability_percent=item.minimum_traceability_percent,
        minimum_test_coverage_percent=item.minimum_test_coverage_percent,
        maximum_high_risk_impacts=item.maximum_high_risk_impacts,
        maximum_overdue_reviews=item.maximum_overdue_reviews,
        require_active_baseline=item.require_active_baseline,
        require_approved_requirements=item.require_approved_requirements,
    )
    now = datetime.now(UTC)
    item.readiness_score = float(result["readiness_score"])
    item.readiness_label = ReleaseReadinessLabel(str(result["readiness_label"]))
    item.gate_summary = {
        "counts": result["gate_summary"],
        "results": result["gate_results"],
    }
    item.blockers = list(result["blockers"])
    item.recommendations = list(result["recommendations"])
    item.evaluated_at = now
    if item.status not in {ReleaseCandidateStatus.IN_REVIEW, ReleaseCandidateStatus.ARCHIVED}:
        item.status = (
            ReleaseCandidateStatus.READY
            if item.readiness_label == ReleaseReadinessLabel.READY
            else ReleaseCandidateStatus.BLOCKED
            if item.readiness_label == ReleaseReadinessLabel.BLOCKED
            else ReleaseCandidateStatus.DRAFT
        )
    evaluation = ReleaseGateEvaluation(
        release_candidate_id=item.id,
        evaluated_by_id=current_user.id,
        readiness_score=item.readiness_score,
        readiness_label=item.readiness_label,
        gate_results=list(result["gate_results"]),
        evidence=evidence,
        blockers=item.blockers,
        recommendations=item.recommendations,
        created_at=now,
    )
    db.add(evaluation)
    await db.flush()
    await _audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action="release.evaluated",
        entity_id=item.id,
        details={
            "readiness_score": item.readiness_score,
            "readiness_label": item.readiness_label.value,
            "gate_summary": result["gate_summary"],
        },
    )
    await db.commit()
    return ReleaseEvaluationRead(
        id=evaluation.id,
        readiness_score=evaluation.readiness_score,
        readiness_label=evaluation.readiness_label,
        gate_results=evaluation.gate_results,
        evidence=evaluation.evidence,
        blockers=evaluation.blockers,
        recommendations=evaluation.recommendations,
        created_at=evaluation.created_at,
    )


@router.post("/{release_id}/submit", response_model=ReleaseCandidateRead)
async def submit_release(
    project_id: UUID, release_id: UUID, db: DbSession, current_user: CurrentUser
):
    item = await _candidate(db, project_id, release_id, current_user.id)
    if item.locked_at:
        raise HTTPException(status_code=409, detail="Released candidates are locked")
    if item.readiness_label == ReleaseReadinessLabel.NOT_EVALUATED:
        raise HTTPException(
            status_code=409, detail="Evaluate quality gates before submitting for review"
        )
    item.status = ReleaseCandidateStatus.IN_REVIEW
    await _audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action="release.submitted",
        entity_id=item.id,
        details={"readiness_score": item.readiness_score},
    )
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/{release_id}/decision", response_model=ReleaseCandidateRead)
async def decide_release(
    project_id: UUID,
    release_id: UUID,
    payload: ReleaseDecisionCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    item = await _candidate(db, project_id, release_id, current_user.id)
    if item.status != ReleaseCandidateStatus.IN_REVIEW:
        raise HTTPException(
            status_code=409, detail="Submit the release for review before recording a decision"
        )
    if payload.approved and item.readiness_label != ReleaseReadinessLabel.READY:
        raise HTTPException(
            status_code=409, detail="Only a release with Ready quality-gate status can be approved"
        )
    now = datetime.now(UTC)
    item.reviewer_name = payload.reviewer_name
    item.review_comments = payload.review_comments
    item.decision_reason = payload.decision_reason
    item.signed_off_at = now
    item.status = (
        ReleaseCandidateStatus.READY if payload.approved else ReleaseCandidateStatus.BLOCKED
    )
    await _audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action="release.approved" if payload.approved else "release.rejected",
        entity_id=item.id,
        details={
            "reviewer": payload.reviewer_name,
            "reason": payload.decision_reason,
            "readiness_score": item.readiness_score,
        },
    )
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/{release_id}/publish", response_model=ReleaseCandidateRead)
async def publish_release(
    project_id: UUID, release_id: UUID, db: DbSession, current_user: CurrentUser
):
    item = await _candidate(db, project_id, release_id, current_user.id)
    if item.status != ReleaseCandidateStatus.READY or item.signed_off_at is None:
        raise HTTPException(
            status_code=409, detail="A signed-off Ready release is required before publishing"
        )
    now = datetime.now(UTC)
    item.status = ReleaseCandidateStatus.RELEASED
    item.locked_at = now
    item.release_snapshot = _snapshot(item)
    await _audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action="release.published",
        entity_id=item.id,
        details={"version": item.version_label, "locked_at": now.isoformat()},
    )
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/compare", response_model=ReleaseComparisonRead)
async def compare_releases(
    project_id: UUID,
    payload: ReleaseComparisonCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    source = await _candidate(db, project_id, payload.source_release_id, current_user.id)
    target = await _candidate(db, project_id, payload.target_release_id, current_user.id)
    comparison = compare_release_snapshots(
        source.release_snapshot or _snapshot(source),
        target.release_snapshot or _snapshot(target),
    )
    return ReleaseComparisonRead(
        source_release_id=source.id,
        target_release_id=target.id,
        **comparison,
    )


@router.get("/{release_id}/report")
async def release_report(
    project_id: UUID, release_id: UUID, db: DbSession, current_user: CurrentUser
):
    item = await _candidate(db, project_id, release_id, current_user.id)
    evidence = await _collect_evidence(db, item)
    return {
        "release": _snapshot(item),
        "configuration": {
            "minimum_traceability_percent": item.minimum_traceability_percent,
            "minimum_test_coverage_percent": item.minimum_test_coverage_percent,
            "maximum_high_risk_impacts": item.maximum_high_risk_impacts,
            "maximum_overdue_reviews": item.maximum_overdue_reviews,
            "require_active_baseline": item.require_active_baseline,
            "require_approved_requirements": item.require_approved_requirements,
        },
        "evidence": evidence,
        "generated_at": datetime.now(UTC).isoformat(),
    }


@router.get("/{release_id}/report.csv")
async def release_report_csv(
    project_id: UUID, release_id: UUID, db: DbSession, current_user: CurrentUser
):
    item = await _candidate(db, project_id, release_id, current_user.id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Gate", "Status", "Measured value", "Threshold", "Message"])
    for gate in item.gate_summary.get("results", []):
        writer.writerow(
            [
                gate.get("name"),
                gate.get("status"),
                gate.get("measured_value"),
                gate.get("threshold"),
                gate.get("message"),
            ]
        )
    filename = f"atlas-release-{item.version_label}-readiness.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
