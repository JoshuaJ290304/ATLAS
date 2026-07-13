from fastapi import APIRouter

from app.api.v1.endpoints import auth, documents, health, projects, requirements, traceability

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(documents.router)
api_router.include_router(requirements.router)

api_router.include_router(traceability.artifact_router)
api_router.include_router(traceability.trace_router)
api_router.include_router(traceability.traceability_router)
