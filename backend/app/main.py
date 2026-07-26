import re
from secrets import token_hex

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-assisted requirement traceability and change-impact analysis platform.",
    debug=settings.DEBUG,
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_API_DOCS else None,
)

if settings.trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
    expose_headers=["Content-Disposition", "X-Request-ID"],
    max_age=600,
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def apply_security_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", request_id):
        request_id = token_hex(16)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    if settings.SECURITY_HEADERS_ENABLED:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )
        if request.url.path.startswith(settings.API_V1_PREFIX):
            response.headers["Cache-Control"] = "no-store"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    result = {"message": "ATLAS API", "version": settings.APP_VERSION}
    if settings.ENABLE_API_DOCS:
        result["docs"] = "/docs"
    return result
