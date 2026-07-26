from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.api.v1.endpoints.projects import get_owned_project
from app.api.v1.endpoints.requirements import get_owned_requirement
from app.models.governance import (
    AuditLog,
    BaselineRequirement,
    ProjectBaseline,
    RequirementComment,
    RequirementReview,
    ReviewStatus,
)
from app.models.requirement import Requirement, RequirementStatus
from app.models.user import User
from app.schemas.governance import (
    AuditLogRead,
    BaselineComparisonCreate,
    BaselineComparisonRead,
    BaselineCreate,
    BaselineRead,
    BaselineRequirementRead,
    BaselineSummaryRead,
    CommentCreate,
    GovernanceSummaryRead,
    RequirementCommentRead,
    RequirementReviewRead,
    ReviewDecisionCreate,
    ReviewRequestCreate,
    UserReference,
)
from app.services.governance import compare_baseline_snapshots, requirement_snapshot
from app.services.impact import ensure_requirement_snapshot, requirement_version_from_model

router = APIRouter(prefix="/projects/{project_id}/governance", tags=["governance"])


def _user_reference(user: User) -> UserReference:
    return UserReference.model_validate(user)


def _review_read(review: RequirementReview) -> RequirementReviewRead:
    return RequirementReviewRead(
        id=review.id,
        project_id=review.project_id,
        requirement_id=review.requirement_id,
        requirement_code=review.requirement.code,
        requirement_title=review.requirement.title,
        reviewer=_user_reference(review.reviewer),
        requested_by=_user_reference(review.requested_by),
        status=review.status,
        priority=review.priority,
        due_date=review.due_date,
        request_note=review.request_note,
        decision_note=review.decision_note,
        decided_at=review.decided_at,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


def _comment_read(comment: RequirementComment) -> RequirementCommentRead:
    return RequirementCommentRead(
        id=comment.id,
        requirement_id=comment.requirement_id,
        requirement_code=comment.requirement.code,
        author=_user_reference(comment.author),
        body=comment.body,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


def _baseline_summary(baseline: ProjectBaseline) -> BaselineSummaryRead:
    return BaselineSummaryRead(
        id=baseline.id,
        project_id=baseline.project_id,
        name=baseline.name,
        version_label=baseline.version_label,
        description=baseline.description,
        status=baseline.status,
        requirement_count=baseline.requirement_count,
        created_by=_user_reference(baseline.created_by),
        created_at=baseline.created_at,
        updated_at=baseline.updated_at,
    )


def _baseline_read(baseline: ProjectBaseline) -> BaselineRead:
    summary = _baseline_summary(baseline)
    return BaselineRead(
        **summary.model_dump(),
        items=[
            BaselineRequirementRead(
                id=item.id,
                requirement_id=item.requirement_id,
                code=item.code,
                requirement_version=item.requirement_version,
                snapshot_data=item.snapshot_data,
                created_at=item.created_at,
            )
            for item in baseline.items
        ],
    )


def _audit_read(log: AuditLog) -> AuditLogRead:
    return AuditLogRead(
        id=log.id,
        actor=_user_reference(log.actor),
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        details=log.details,
        created_at=log.created_at,
    )


def _add_audit(
    db: DbSession,
    *,
    project_id: UUID,
    actor_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    details: dict[str, object] | None = None,
) -> None:
    db.add(
        AuditLog(
            project_id=project_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
        )
    )


async def _load_review(
    db: DbSession,
    project_id: UUID,
    review_id: UUID,
) -> RequirementReview:
    result = await db.execute(
        select(RequirementReview)
        .options(
            selectinload(RequirementReview.requirement),
            selectinload(RequirementReview.reviewer),
            selectinload(RequirementReview.requested_by),
        )
        .where(
            RequirementReview.id == review_id,
            RequirementReview.project_id == project_id,
        )
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=404, detail="Review request not found")
    return review


async def _load_baseline(
    db: DbSession,
    project_id: UUID,
    baseline_id: UUID,
) -> ProjectBaseline:
    result = await db.execute(
        select(ProjectBaseline)
        .options(
            selectinload(ProjectBaseline.created_by),
            selectinload(ProjectBaseline.items),
        )
        .where(
            ProjectBaseline.id == baseline_id,
            ProjectBaseline.project_id == project_id,
        )
    )
    baseline = result.scalar_one_or_none()
    if baseline is None:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return baseline


@router.get("/summary", response_model=GovernanceSummaryRead)
async def governance_summary(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> GovernanceSummaryRead:
    await get_owned_project(db, project_id, current_user.id)

    requirement_result = await db.execute(
        select(Requirement.status, func.count(Requirement.id))
        .where(Requirement.project_id == project_id)
        .group_by(Requirement.status)
    )
    requirement_counts = {status_value: count for status_value, count in requirement_result.all()}

    pending_reviews = await db.scalar(
        select(func.count(RequirementReview.id)).where(
            RequirementReview.project_id == project_id,
            RequirementReview.status == ReviewStatus.PENDING,
        )
    )
    comments = await db.scalar(
        select(func.count(RequirementComment.id)).where(RequirementComment.project_id == project_id)
    )
    baselines = await db.scalar(
        select(func.count(ProjectBaseline.id)).where(ProjectBaseline.project_id == project_id)
    )

    return GovernanceSummaryRead(
        pending_reviews=int(pending_reviews or 0),
        approved_requirements=int(requirement_counts.get(RequirementStatus.APPROVED, 0)),
        rejected_requirements=int(requirement_counts.get(RequirementStatus.REJECTED, 0)),
        in_review_requirements=int(requirement_counts.get(RequirementStatus.REVIEWED, 0)),
        comments=int(comments or 0),
        baselines=int(baselines or 0),
        approved_baseline_candidates=int(requirement_counts.get(RequirementStatus.APPROVED, 0)),
    )


@router.get("/reviewers", response_model=list[UserReference])
async def list_reviewers(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[UserReference]:
    await get_owned_project(db, project_id, current_user.id)
    result = await db.execute(
        select(User).where(User.is_active.is_(True)).order_by(User.name.asc(), User.email.asc())
    )
    return [_user_reference(user) for user in result.scalars().all()]


@router.get("/reviews", response_model=list[RequirementReviewRead])
async def list_reviews(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    review_status: Annotated[
        ReviewStatus | None,
        Query(alias="status"),
    ] = None,
) -> list[RequirementReviewRead]:
    await get_owned_project(db, project_id, current_user.id)
    statement = (
        select(RequirementReview)
        .options(
            selectinload(RequirementReview.requirement),
            selectinload(RequirementReview.reviewer),
            selectinload(RequirementReview.requested_by),
        )
        .where(RequirementReview.project_id == project_id)
    )
    if review_status is not None:
        statement = statement.where(RequirementReview.status == review_status)

    result = await db.execute(
        statement.order_by(
            RequirementReview.status.asc(),
            RequirementReview.created_at.desc(),
        )
    )
    return [_review_read(review) for review in result.scalars().all()]


@router.post(
    "/requirements/{requirement_id}/reviews",
    response_model=RequirementReviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def request_requirement_review(
    project_id: UUID,
    requirement_id: UUID,
    payload: ReviewRequestCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> RequirementReviewRead:
    requirement = await get_owned_requirement(
        db,
        project_id,
        requirement_id,
        current_user.id,
    )
    reviewer = await db.get(User, payload.reviewer_id)
    if reviewer is None or not reviewer.is_active:
        raise HTTPException(status_code=422, detail="Selected reviewer is not available")

    existing = await db.scalar(
        select(RequirementReview.id).where(
            RequirementReview.project_id == project_id,
            RequirementReview.requirement_id == requirement_id,
            RequirementReview.reviewer_id == reviewer.id,
            RequirementReview.status == ReviewStatus.PENDING,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="This reviewer already has a pending request for the requirement",
        )

    review = RequirementReview(
        project_id=project_id,
        requirement_id=requirement_id,
        reviewer_id=reviewer.id,
        requested_by_id=current_user.id,
        status=ReviewStatus.PENDING,
        priority=payload.priority,
        due_date=payload.due_date,
        request_note=payload.request_note,
    )
    db.add(review)
    if requirement.status != RequirementStatus.REVIEWED:
        await ensure_requirement_snapshot(db, requirement)
        requirement.status = RequirementStatus.REVIEWED
        requirement.version += 1
        await db.flush()
        db.add(requirement_version_from_model(requirement))
    else:
        await db.flush()
    _add_audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action="review_requested",
        entity_type="requirement",
        entity_id=requirement.id,
        details={
            "requirement_code": requirement.code,
            "reviewer_id": str(reviewer.id),
            "reviewer_name": reviewer.name,
            "priority": review.priority.value,
            "due_date": review.due_date.isoformat() if review.due_date else None,
            "request_note": review.request_note,
        },
    )
    await db.commit()

    loaded = await _load_review(db, project_id, review.id)
    return _review_read(loaded)


@router.post("/reviews/{review_id}/decision", response_model=RequirementReviewRead)
async def decide_requirement_review(
    project_id: UUID,
    review_id: UUID,
    payload: ReviewDecisionCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> RequirementReviewRead:
    await get_owned_project(db, project_id, current_user.id)
    review = await _load_review(db, project_id, review_id)
    if review.status != ReviewStatus.PENDING:
        raise HTTPException(status_code=409, detail="This review has already been decided")

    review.status = ReviewStatus(payload.status)
    review.decision_note = payload.decision_note
    review.decided_at = datetime.now(UTC)
    resolved_requirement_status = (
        RequirementStatus.APPROVED
        if review.status == ReviewStatus.APPROVED
        else RequirementStatus.REJECTED
    )
    if review.requirement.status != resolved_requirement_status:
        await ensure_requirement_snapshot(db, review.requirement)
        review.requirement.status = resolved_requirement_status
        review.requirement.version += 1
        await db.flush()
        db.add(requirement_version_from_model(review.requirement))
    _add_audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action=f"review_{review.status.value}",
        entity_type="requirement",
        entity_id=review.requirement_id,
        details={
            "review_id": str(review.id),
            "requirement_code": review.requirement.code,
            "decision_note": review.decision_note,
        },
    )
    await db.commit()

    loaded = await _load_review(db, project_id, review.id)
    return _review_read(loaded)


@router.get(
    "/requirements/{requirement_id}/comments",
    response_model=list[RequirementCommentRead],
)
async def list_requirement_comments(
    project_id: UUID,
    requirement_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[RequirementCommentRead]:
    await get_owned_requirement(db, project_id, requirement_id, current_user.id)
    result = await db.execute(
        select(RequirementComment)
        .options(
            selectinload(RequirementComment.requirement),
            selectinload(RequirementComment.author),
        )
        .where(
            RequirementComment.project_id == project_id,
            RequirementComment.requirement_id == requirement_id,
        )
        .order_by(RequirementComment.created_at.asc())
    )
    return [_comment_read(comment) for comment in result.scalars().all()]


@router.post(
    "/requirements/{requirement_id}/comments",
    response_model=RequirementCommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_requirement_comment(
    project_id: UUID,
    requirement_id: UUID,
    payload: CommentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> RequirementCommentRead:
    requirement = await get_owned_requirement(db, project_id, requirement_id, current_user.id)
    comment = RequirementComment(
        project_id=project_id,
        requirement_id=requirement_id,
        author_id=current_user.id,
        body=payload.body,
    )
    db.add(comment)
    await db.flush()
    _add_audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action="comment_added",
        entity_type="requirement",
        entity_id=requirement_id,
        details={
            "requirement_code": requirement.code,
            "comment": comment.body,
        },
    )
    await db.commit()

    result = await db.execute(
        select(RequirementComment)
        .options(
            selectinload(RequirementComment.requirement),
            selectinload(RequirementComment.author),
        )
        .where(RequirementComment.id == comment.id)
    )
    return _comment_read(result.scalar_one())


@router.get("/baselines", response_model=list[BaselineSummaryRead])
async def list_baselines(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[BaselineSummaryRead]:
    await get_owned_project(db, project_id, current_user.id)
    result = await db.execute(
        select(ProjectBaseline)
        .options(selectinload(ProjectBaseline.created_by))
        .where(ProjectBaseline.project_id == project_id)
        .order_by(ProjectBaseline.created_at.desc())
    )
    return [_baseline_summary(baseline) for baseline in result.scalars().all()]


@router.post(
    "/baselines",
    response_model=BaselineRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_baseline(
    project_id: UUID,
    payload: BaselineCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> BaselineRead:
    await get_owned_project(db, project_id, current_user.id)
    duplicate = await db.scalar(
        select(ProjectBaseline.id).where(
            ProjectBaseline.project_id == project_id,
            func.lower(ProjectBaseline.version_label) == payload.version_label.lower(),
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=409,
            detail="A baseline with this version label already exists",
        )

    requirement_statement = select(Requirement).where(
        Requirement.project_id == project_id,
        Requirement.status == RequirementStatus.APPROVED,
    )
    selected_ids = list(dict.fromkeys(payload.requirement_ids or []))
    if selected_ids:
        requirement_statement = requirement_statement.where(Requirement.id.in_(selected_ids))

    requirement_result = await db.execute(requirement_statement.order_by(Requirement.code.asc()))
    requirements = list(requirement_result.scalars().all())

    if not requirements:
        raise HTTPException(
            status_code=409,
            detail="Select at least one approved requirement before creating a baseline",
        )

    if selected_ids and len(requirements) != len(selected_ids):
        raise HTTPException(
            status_code=422,
            detail="Every selected requirement must belong to this project and be approved",
        )

    baseline = ProjectBaseline(
        project_id=project_id,
        created_by_id=current_user.id,
        name=payload.name,
        version_label=payload.version_label,
        description=payload.description,
        status=payload.status,
        requirement_count=len(requirements),
    )
    db.add(baseline)
    await db.flush()

    for requirement in requirements:
        db.add(
            BaselineRequirement(
                baseline_id=baseline.id,
                requirement_id=requirement.id,
                code=requirement.code,
                requirement_version=requirement.version,
                snapshot_data=requirement_snapshot(requirement),
            )
        )

    _add_audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action="baseline_created",
        entity_type="baseline",
        entity_id=baseline.id,
        details={
            "name": baseline.name,
            "version_label": baseline.version_label,
            "status": baseline.status.value,
            "requirement_count": baseline.requirement_count,
            "requirement_codes": [requirement.code for requirement in requirements],
        },
    )
    await db.commit()

    loaded = await _load_baseline(db, project_id, baseline.id)
    return _baseline_read(loaded)


@router.get("/baselines/{baseline_id}", response_model=BaselineRead)
async def read_baseline(
    project_id: UUID,
    baseline_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> BaselineRead:
    await get_owned_project(db, project_id, current_user.id)
    baseline = await _load_baseline(db, project_id, baseline_id)
    return _baseline_read(baseline)


@router.get(
    "/baselines/{baseline_id}/compare",
    response_model=BaselineComparisonRead,
)
async def compare_baseline(
    project_id: UUID,
    baseline_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> BaselineComparisonRead:
    await get_owned_project(db, project_id, current_user.id)
    baseline = await _load_baseline(db, project_id, baseline_id)
    current_result = await db.execute(
        select(Requirement)
        .where(Requirement.project_id == project_id)
        .order_by(Requirement.code.asc())
    )
    current_snapshots = [
        requirement_snapshot(requirement) for requirement in current_result.scalars().all()
    ]
    comparison = compare_baseline_snapshots(
        [item.snapshot_data for item in baseline.items],
        current_snapshots,
    )

    return BaselineComparisonRead(
        baseline_id=baseline.id,
        baseline_name=baseline.name,
        version_label=baseline.version_label,
        target_is_current=True,
        added=comparison["added"],
        modified=comparison["modified"],
        removed=comparison["removed"],
        unchanged=comparison["unchanged"],
        added_count=len(comparison["added"]),
        modified_count=len(comparison["modified"]),
        removed_count=len(comparison["removed"]),
        unchanged_count=len(comparison["unchanged"]),
    )


@router.post(
    "/baseline-comparisons",
    response_model=BaselineComparisonRead,
)
async def compare_two_baselines(
    project_id: UUID,
    payload: BaselineComparisonCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> BaselineComparisonRead:
    await get_owned_project(db, project_id, current_user.id)
    source = await _load_baseline(db, project_id, payload.source_baseline_id)
    target = await _load_baseline(db, project_id, payload.target_baseline_id)

    comparison = compare_baseline_snapshots(
        [item.snapshot_data for item in source.items],
        [item.snapshot_data for item in target.items],
    )

    _add_audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action="baseline_comparison_performed",
        entity_type="baseline",
        entity_id=source.id,
        details={
            "source_baseline_id": str(source.id),
            "source_name": source.name,
            "source_version_label": source.version_label,
            "target_baseline_id": str(target.id),
            "target_name": target.name,
            "target_version_label": target.version_label,
        },
    )
    await db.commit()

    return BaselineComparisonRead(
        baseline_id=source.id,
        baseline_name=source.name,
        version_label=source.version_label,
        target_baseline_id=target.id,
        target_baseline_name=target.name,
        target_version_label=target.version_label,
        target_is_current=False,
        added=comparison["added"],
        modified=comparison["modified"],
        removed=comparison["removed"],
        unchanged=comparison["unchanged"],
        added_count=len(comparison["added"]),
        modified_count=len(comparison["modified"]),
        removed_count=len(comparison["removed"]),
        unchanged_count=len(comparison["unchanged"]),
    )


@router.delete("/baselines/{baseline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_baseline(
    project_id: UUID,
    baseline_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    await get_owned_project(db, project_id, current_user.id)
    baseline = await _load_baseline(db, project_id, baseline_id)
    baseline_name = baseline.name
    baseline_version = baseline.version_label
    await db.delete(baseline)
    _add_audit(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        action="baseline_deleted",
        entity_type="baseline",
        entity_id=baseline_id,
        details={"name": baseline_name, "version_label": baseline_version},
    )
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/audit", response_model=list[AuditLogRead])
async def list_audit_logs(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=250),
) -> list[AuditLogRead]:
    await get_owned_project(db, project_id, current_user.id)
    result = await db.execute(
        select(AuditLog)
        .options(selectinload(AuditLog.actor))
        .where(AuditLog.project_id == project_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return [_audit_read(log) for log in result.scalars().all()]
