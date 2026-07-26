from datetime import UTC, datetime

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.api.dependencies import DbSession
from app.core.config import settings

router = APIRouter(tags=["health"])


def _base_health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ATLAS API",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health")
@router.get("/health/live")
async def health_check() -> dict[str, str]:
    return _base_health()


@router.get("/health/ready")
async def readiness_check(db: DbSession, response: Response) -> dict[str, str]:
    payload = _base_health()
    try:
        await db.execute(text("SELECT 1"))
        payload["database"] = "ready"
        return payload
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        payload["status"] = "unavailable"
        payload["database"] = "unavailable"
        return payload
