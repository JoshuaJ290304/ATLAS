from __future__ import annotations

import re
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import delete, select

from app.api.dependencies import CurrentUser, DbSession
from app.api.v1.endpoints.documents import get_owned_document
from app.api.v1.endpoints.projects import get_owned_project
from app.models.document import DocumentStatus
from app.models.requirement import (
    Requirement,
    RequirementSource,
    RequirementStatus,
    RequirementType,
)
from app.schemas.requirement import (
    RequirementCreate,
    RequirementExtractionRead,
    RequirementExtractionRequest,
    RequirementRead,
    RequirementSummaryRead,
    RequirementUpdate,
)
from app.services.impact import ensure_requirement_snapshot, requirement_version_from_model
from app.services.requirements import (
    analyze_ambiguity,
    extract_requirement_candidates,
    normalize_for_comparison,
)

router = APIRouter(prefix="/projects/{project_id}/requirements", tags=["requirements"])
CODE_PATTERN = re.compile(r"^REQ-(\d+)$")


async def get_owned_requirement(
    db: DbSession,
    project_id: UUID,
    requirement_id: UUID,
    owner_id: UUID,
) -> Requirement:
    await get_owned_project(db, project_id, owner_id)
    result = await db.execute(
        select(Requirement).where(
            Requirement.id == requirement_id,
            Requirement.project_id == project_id,
        )
    )
    requirement = result.scalar_one_or_none()
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


async def next_requirement_number(db: DbSession, project_id: UUID) -> int:
    result = await db.execute(select(Requirement.code).where(Requirement.project_id == project_id))
    numbers = [
        int(match.group(1))
        for code in result.scalars().all()
        if (match := CODE_PATTERN.match(code)) is not None
    ]
    return max(numbers, default=0) + 1


@router.post("/extract", response_model=RequirementExtractionRead)
async def extract_requirements(
    project_id: UUID,
    payload: RequirementExtractionRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> RequirementExtractionRead:
    await get_owned_project(db, project_id, current_user.id)
    document = await get_owned_document(db, project_id, payload.document_id, current_user.id)
    if document.status != DocumentStatus.EXTRACTED or not document.extracted_text:
        raise HTTPException(status_code=409, detail="Document text is not available for extraction")

    if payload.replace_existing:
        await db.execute(
            delete(Requirement).where(
                Requirement.project_id == project_id,
                Requirement.source_document_id == document.id,
                Requirement.source == RequirementSource.EXTRACTED,
            )
        )
        await db.flush()

    candidates = extract_requirement_candidates(document.extracted_text)
    if not candidates:
        raise HTTPException(
            status_code=422,
            detail="No requirement-like statements were detected in this document",
        )

    existing_result = await db.execute(
        select(Requirement.description).where(Requirement.project_id == project_id)
    )
    existing = {
        normalize_for_comparison(description) for description in existing_result.scalars().all()
    }
    sequence = await next_requirement_number(db, project_id)
    created: list[Requirement] = []
    skipped = 0

    for candidate in candidates:
        normalized = normalize_for_comparison(candidate.description)
        if normalized in existing:
            skipped += 1
            continue
        requirement = Requirement(
            project_id=project_id,
            source_document_id=document.id,
            code=f"REQ-{sequence:04d}",
            title=candidate.title,
            description=candidate.description,
            requirement_type=candidate.requirement_type,
            non_functional_category=candidate.non_functional_category,
            status=RequirementStatus.DRAFT,
            source=RequirementSource.EXTRACTED,
            source_excerpt=candidate.source_excerpt,
            source_position=candidate.source_position,
            confidence_score=candidate.confidence_score,
            ambiguity_score=candidate.ambiguity_score,
            ambiguity_flags=candidate.ambiguity_flags,
        )
        db.add(requirement)
        await db.flush()
        db.add(requirement_version_from_model(requirement))
        created.append(requirement)
        existing.add(normalized)
        sequence += 1

    await db.commit()
    for requirement in created:
        await db.refresh(requirement)

    return RequirementExtractionRead(
        document_id=document.id,
        detected_count=len(candidates),
        created_count=len(created),
        skipped_duplicate_count=skipped,
        requirements=[RequirementRead.model_validate(item) for item in created],
    )


@router.post("", response_model=RequirementRead, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    project_id: UUID,
    payload: RequirementCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Requirement:
    await get_owned_project(db, project_id, current_user.id)
    sequence = await next_requirement_number(db, project_id)
    ambiguity_score, ambiguity_flags = analyze_ambiguity(
        payload.description,
        payload.requirement_type,
    )
    requirement = Requirement(
        project_id=project_id,
        code=f"REQ-{sequence:04d}",
        title=payload.title.strip(),
        description=payload.description.strip(),
        requirement_type=payload.requirement_type,
        non_functional_category=(
            payload.non_functional_category.strip()
            if payload.non_functional_category
            and payload.requirement_type == RequirementType.NON_FUNCTIONAL
            else None
        ),
        status=payload.status,
        source=RequirementSource.MANUAL,
        confidence_score=1.0,
        ambiguity_score=ambiguity_score,
        ambiguity_flags=ambiguity_flags,
    )
    db.add(requirement)
    await db.flush()
    db.add(requirement_version_from_model(requirement))
    await db.commit()
    await db.refresh(requirement)
    return requirement


@router.get("", response_model=list[RequirementRead])
async def list_requirements(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    requirement_type: RequirementType | None = None,
    requirement_status: Annotated[RequirementStatus | None, Query(alias="status")] = None,
    document_id: UUID | None = None,
    ambiguous_only: bool = False,
) -> list[Requirement]:
    await get_owned_project(db, project_id, current_user.id)
    statement = select(Requirement).where(Requirement.project_id == project_id)
    if requirement_type is not None:
        statement = statement.where(Requirement.requirement_type == requirement_type)
    if requirement_status is not None:
        statement = statement.where(Requirement.status == requirement_status)
    if document_id is not None:
        statement = statement.where(Requirement.source_document_id == document_id)
    if ambiguous_only:
        statement = statement.where(Requirement.ambiguity_score > 0)
    result = await db.execute(statement.order_by(Requirement.code.asc()))
    return list(result.scalars().all())


@router.get("/summary", response_model=RequirementSummaryRead)
async def requirement_summary(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> RequirementSummaryRead:
    await get_owned_project(db, project_id, current_user.id)
    result = await db.execute(
        select(
            Requirement.requirement_type,
            Requirement.status,
            Requirement.ambiguity_score,
            Requirement.non_functional_category,
        ).where(Requirement.project_id == project_id)
    )
    rows = result.all()
    categories: dict[str, int] = {}
    for requirement_type, _, _, category in rows:
        if requirement_type == RequirementType.NON_FUNCTIONAL and category:
            categories[category] = categories.get(category, 0) + 1

    return RequirementSummaryRead(
        total=len(rows),
        functional=sum(1 for row in rows if row.requirement_type == RequirementType.FUNCTIONAL),
        non_functional=sum(
            1 for row in rows if row.requirement_type == RequirementType.NON_FUNCTIONAL
        ),
        ambiguous=sum(1 for row in rows if row.ambiguity_score > 0),
        draft=sum(1 for row in rows if row.status == RequirementStatus.DRAFT),
        reviewed=sum(1 for row in rows if row.status == RequirementStatus.REVIEWED),
        approved=sum(1 for row in rows if row.status == RequirementStatus.APPROVED),
        rejected=sum(1 for row in rows if row.status == RequirementStatus.REJECTED),
        categories=categories,
    )


@router.get("/{requirement_id}", response_model=RequirementRead)
async def read_requirement(
    project_id: UUID,
    requirement_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Requirement:
    return await get_owned_requirement(db, project_id, requirement_id, current_user.id)


@router.patch("/{requirement_id}", response_model=RequirementRead)
async def update_requirement(
    project_id: UUID,
    requirement_id: UUID,
    payload: RequirementUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Requirement:
    requirement = await get_owned_requirement(db, project_id, requirement_id, current_user.id)
    await ensure_requirement_snapshot(db, requirement)
    updates = payload.model_dump(exclude_unset=True)

    if "title" in updates and updates["title"] is not None:
        updates["title"] = updates["title"].strip()
    if "description" in updates and updates["description"] is not None:
        updates["description"] = updates["description"].strip()

    resolved_type = updates.get("requirement_type", requirement.requirement_type)
    resolved_category = updates.get("non_functional_category", requirement.non_functional_category)
    if resolved_type == RequirementType.FUNCTIONAL:
        updates["non_functional_category"] = None
    elif not resolved_category:
        raise HTTPException(status_code=422, detail="A non-functional category is required")

    for field, value in updates.items():
        setattr(requirement, field, value)

    if "description" in updates or "requirement_type" in updates:
        requirement.ambiguity_score, requirement.ambiguity_flags = analyze_ambiguity(
            requirement.description,
            requirement.requirement_type,
        )
    requirement.version += 1
    await db.flush()
    db.add(requirement_version_from_model(requirement))

    await db.commit()
    await db.refresh(requirement)
    return requirement


@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    project_id: UUID,
    requirement_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    requirement = await get_owned_requirement(db, project_id, requirement_id, current_user.id)
    await db.delete(requirement)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
