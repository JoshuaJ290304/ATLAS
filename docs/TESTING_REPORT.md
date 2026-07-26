# ATLAS 1.0.0 Testing Report

## Automated commands

```powershell
docker compose exec backend alembic current
docker compose exec backend pytest -q
docker compose exec backend ruff check .
docker compose build frontend
docker compose exec frontend nginx -t
```

Expected migration head for RC2: `0013`.

## Service verification

```powershell
Invoke-WebRequest http://localhost:5173/healthz -UseBasicParsing
Invoke-WebRequest http://localhost:8000/api/v1/health/live -UseBasicParsing
Invoke-WebRequest http://localhost:8000/api/v1/health/ready -UseBasicParsing
```

## Regression coverage

- registration, login, logout, recovery, expiry, and rate limiting
- admin authorization, existing-user management, suspension, and session invalidation
- project ownership isolation
- PDF/DOCX upload validation, extraction, download, and deletion
- requirements, governance, baselines, traceability, impact analysis
- test cases, version history, and coverage
- AI indexing, retrieval, citations, and fallback
- analytics and exports
- release quality gates, comparison, sign-off, and publication lock

## Responsive acceptance

Verify at 1440, 1024, 768, and 390 pixels. The page itself must not overflow horizontally; wide tables may scroll inside labelled table regions.

## Release decision

Do not tag `v1.0.0` until all automated commands and the end-to-end demonstration workflow pass on the target machine.
