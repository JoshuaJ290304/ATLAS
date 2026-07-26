from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.api.v1.endpoints.projects import get_owned_project
from app.models.requirement import Requirement, RequirementStatus
from app.models.test_case import (
    TestCase,
    TestCasePriority,
    TestCaseSource,
    TestCaseStatus,
    TestCaseType,
    TestCaseVersion,
    TestStep,
)
from app.schemas.test_case import (
    TestCaseCreate,
    TestCaseGenerateRequest,
    TestCaseRead,
    TestCaseSummary,
    TestCaseUpdate,
)

router = APIRouter(prefix="/projects/{project_id}/test-cases", tags=["test cases"])
CODE_PATTERN = re.compile(r"^TC-(\d+)$")


async def owned_case(db, project_id, test_case_id, owner_id):
    await get_owned_project(db, project_id, owner_id)
    r = await db.execute(
        select(TestCase)
        .options(selectinload(TestCase.steps))
        .where(TestCase.id == test_case_id, TestCase.project_id == project_id)
    )
    item = r.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Test case not found")
    return item


async def next_code(db, project_id):
    r = await db.execute(select(TestCase.code).where(TestCase.project_id == project_id))
    nums = [int(m.group(1)) for c in r.scalars().all() if (m := CODE_PATTERN.match(c))]
    return f"TC-{max(nums, default=0) + 1:04d}"


def snapshot(item):
    return {
        "code": item.code,
        "title": item.title,
        "objective": item.objective,
        "preconditions": item.preconditions,
        "test_data": item.test_data,
        "overall_expected_result": item.overall_expected_result,
        "test_type": item.test_type.value,
        "priority": item.priority.value,
        "status": item.status.value,
        "source": item.source.value,
        "requirement_id": str(item.requirement_id) if item.requirement_id else None,
        "steps": [
            {"position": s.position, "action": s.action, "expected_result": s.expected_result}
            for s in item.steps
        ],
    }


async def validate_requirement(db, project_id, requirement_id):
    if not requirement_id:
        return None
    r = await db.execute(
        select(Requirement).where(
            Requirement.id == requirement_id, Requirement.project_id == project_id
        )
    )
    req = r.scalar_one_or_none()
    if not req:
        raise HTTPException(422, "Selected requirement does not belong to this project")
    return req


@router.get("", response_model=list[TestCaseRead])
async def list_test_cases(project_id: UUID, db: DbSession, current_user: CurrentUser):
    await get_owned_project(db, project_id, current_user.id)
    r = await db.execute(
        select(TestCase)
        .options(selectinload(TestCase.steps))
        .where(TestCase.project_id == project_id)
        .order_by(TestCase.code)
    )
    return list(r.scalars().unique().all())


@router.get("/summary", response_model=TestCaseSummary)
async def summary(project_id: UUID, db: DbSession, current_user: CurrentUser):
    await get_owned_project(db, project_id, current_user.id)
    rows = (
        await db.execute(
            select(TestCase.status, TestCase.source, func.count())
            .where(TestCase.project_id == project_id)
            .group_by(TestCase.status, TestCase.source)
        )
    ).all()
    total = sum(x[2] for x in rows)
    approved = sum(x[2] for x in rows if x[0] == TestCaseStatus.APPROVED)
    in_review = sum(x[2] for x in rows if x[0] == TestCaseStatus.IN_REVIEW)
    needs = sum(x[2] for x in rows if x[0] == TestCaseStatus.NEEDS_REVIEW)
    ai = sum(x[2] for x in rows if x[1] == TestCaseSource.AI_GENERATED)
    req_count = (
        await db.execute(
            select(func.count())
            .select_from(Requirement)
            .where(Requirement.project_id == project_id)
        )
    ).scalar_one()
    covered = (
        await db.execute(
            select(func.count(func.distinct(TestCase.requirement_id))).where(
                TestCase.project_id == project_id,
                TestCase.status == TestCaseStatus.APPROVED,
                TestCase.requirement_id.is_not(None),
            )
        )
    ).scalar_one()
    return TestCaseSummary(
        total=total,
        approved=approved,
        in_review=in_review,
        needs_review=needs,
        ai_generated=ai,
        requirement_count=req_count,
        covered_requirements=covered,
        coverage_percent=round(covered * 100 / req_count, 1) if req_count else 0,
    )


@router.post("", response_model=TestCaseRead, status_code=201)
async def create_test_case(
    project_id: UUID, payload: TestCaseCreate, db: DbSession, current_user: CurrentUser
):
    await get_owned_project(db, project_id, current_user.id)
    await validate_requirement(db, project_id, payload.requirement_id)
    data = payload.model_dump(exclude={"steps"})
    item = TestCase(project_id=project_id, code=await next_code(db, project_id), **data)
    db.add(item)
    await db.flush()
    for i, s in enumerate(payload.steps, 1):
        db.add(TestStep(test_case_id=item.id, position=i, **s.model_dump()))
    await db.flush()
    r = await db.execute(
        select(TestCase).options(selectinload(TestCase.steps)).where(TestCase.id == item.id)
    )
    item = r.scalar_one()
    db.add(
        TestCaseVersion(
            test_case_id=item.id, version=1, snapshot=snapshot(item), change_note="Initial version"
        )
    )
    await db.commit()
    return item


@router.put("/{test_case_id}", response_model=TestCaseRead)
async def update_test_case(
    project_id: UUID,
    test_case_id: UUID,
    payload: TestCaseUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    item = await owned_case(db, project_id, test_case_id, current_user.id)
    await validate_requirement(db, project_id, payload.requirement_id)
    for k, v in payload.model_dump(exclude={"steps", "change_note"}).items():
        setattr(item, k, v)
    item.version += 1
    await db.execute(delete(TestStep).where(TestStep.test_case_id == item.id))
    for i, s in enumerate(payload.steps, 1):
        db.add(TestStep(test_case_id=item.id, position=i, **s.model_dump()))
    await db.flush()
    r = await db.execute(
        select(TestCase).options(selectinload(TestCase.steps)).where(TestCase.id == item.id)
    )
    item = r.scalar_one()
    db.add(
        TestCaseVersion(
            test_case_id=item.id,
            version=item.version,
            snapshot=snapshot(item),
            change_note=payload.change_note,
        )
    )
    await db.commit()
    return item


@router.delete("/{test_case_id}", status_code=204)
async def delete_test_case(
    project_id: UUID, test_case_id: UUID, db: DbSession, current_user: CurrentUser
):
    item = await owned_case(db, project_id, test_case_id, current_user.id)
    await db.delete(item)
    await db.commit()
    return Response(status_code=204)


@router.post("/generate", response_model=list[TestCaseRead], status_code=201)
async def generate(
    project_id: UUID, payload: TestCaseGenerateRequest, db: DbSession, current_user: CurrentUser
):
    await get_owned_project(db, project_id, current_user.id)
    req = await validate_requirement(db, project_id, payload.requirement_id)
    if req.status not in {RequirementStatus.APPROVED, RequirementStatus.REVIEWED}:
        raise HTTPException(409, "Approve or review the requirement before generating test cases")
    created = []
    for t in dict.fromkeys(payload.test_types):
        priority = (
            TestCasePriority.CRITICAL
            if t == TestCaseType.SECURITY
            else TestCasePriority.HIGH
            if t in {TestCaseType.NEGATIVE, TestCaseType.BOUNDARY}
            else TestCasePriority.MEDIUM
        )
        item = TestCase(
            project_id=project_id,
            requirement_id=req.id,
            code=await next_code(db, project_id),
            title=f"{t.value.replace('_', ' ').title()} — {req.title}",
            objective=f"Verify {req.code}: {req.description}",
            preconditions="The application is running and the tester has appropriate access.",
            test_data="Use valid project data plus scenario-specific invalid or boundary values.",
            overall_expected_result=(
                f"The system satisfies {req.code} for the {t.value.replace('_', ' ')} scenario."
            ),
            test_type=t,
            priority=priority,
            status=TestCaseStatus.DRAFT,
            source=TestCaseSource.AI_GENERATED,
            generation_explanation=(
                f"Generated from {req.code} using requirement wording, "
                "scenario type, and traceability context."
            ),
        )
        db.add(item)
        await db.flush()
        steps = [
            ("Open the relevant ATLAS workflow.", "The workflow loads without errors."),
            (
                f"Execute the {t.value.replace('_', ' ')} scenario described by {req.code}.",
                (
                    "The system validates and processes the scenario "
                    "consistently with the requirement."
                ),
            ),
            (
                "Review the displayed result and stored state.",
                f"Observed behaviour matches {req.code} and no unrelated data is changed.",
            ),
        ]
        for i, (a, e) in enumerate(steps, 1):
            db.add(TestStep(test_case_id=item.id, position=i, action=a, expected_result=e))
        await db.flush()
        r = await db.execute(
            select(TestCase).options(selectinload(TestCase.steps)).where(TestCase.id == item.id)
        )
        item = r.scalar_one()
        db.add(
            TestCaseVersion(
                test_case_id=item.id,
                version=1,
                snapshot=snapshot(item),
                change_note="AI-assisted generation",
            )
        )
        created.append(item)
    await db.commit()
    return created
