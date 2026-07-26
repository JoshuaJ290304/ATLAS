from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    analytics,
    assistant,
    auth,
    documents,
    governance,
    health,
    impact,
    projects,
    requirements,
    release_readiness,
    traceability,
    test_cases,
)

api_router = APIRouter()
api_router.include_router(admin.router)
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(documents.router)
api_router.include_router(requirements.router)
api_router.include_router(governance.router)
api_router.include_router(test_cases.router)
api_router.include_router(release_readiness.router)

api_router.include_router(traceability.artifact_router)
api_router.include_router(traceability.trace_router)
api_router.include_router(traceability.traceability_router)

api_router.include_router(impact.version_router)
api_router.include_router(impact.impact_router)

api_router.include_router(assistant.router)
api_router.include_router(analytics.router)
