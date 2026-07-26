# Quality Assurance Checklist

## Automated checks

```powershell
docker compose ps
docker compose exec backend alembic current
docker compose exec backend pytest -q
docker compose exec backend ruff check .
docker compose build frontend
docker compose exec frontend nginx -t
```

Expected database migration: `0013 (head)`.

## Service checks

```powershell
(Invoke-WebRequest http://localhost:5173/healthz -UseBasicParsing).StatusCode
(Invoke-WebRequest http://localhost:8000/api/v1/health/live -UseBasicParsing).StatusCode
(Invoke-WebRequest http://localhost:8000/api/v1/health/ready -UseBasicParsing).StatusCode
```

All must return `200` while PostgreSQL and the application are healthy.

## Security regression

- Repeated failed logins return HTTP 429 after the configured limit.
- A successful login clears the email-specific failed-login window.
- Repeated registration and password-recovery requests are rate limited.
- Reset links are single-use and expire.
- Password reset and admin session invalidation reject previously issued tokens.
- Suspended users cannot authenticate.
- Normal users receive HTTP 403 from admin endpoints.
- Production configuration rejects default secrets, debug mode, and enabled API docs.
- Invalid PDF/DOCX signatures, oversized files, encrypted DOCX files, unsafe paths, and compression bombs are rejected.

## Functional regression

- Register, log in, log out, and verify expired-session handling.
- Create, list, search, and reopen projects.
- Upload, extract, download, and delete PDF/DOCX documents.
- Extract, create, edit, classify, version, and delete requirements.
- Create artifacts and review traceability links.
- Generate and reopen impact reports.
- Build and clear the assistant index; verify grounded answers and citations.
- Review analytics and export HTML, CSV, and JSON reports.
- Create, review, and approve test cases.
- Evaluate, approve, compare, and publish release candidates.
- Manage existing users and projects through administrator pages.
- Restart Docker and verify persistence.

## Interface review

Test at approximately 1440 px, 1024 px, 768 px, and 390 px.

- Header, footer, and project navigation remain accessible.
- Buttons remain inside cards and do not wrap vertically.
- Forms use available width without overlap.
- Tables scroll horizontally inside their own labelled containers.
- Text wraps without leaving its container.
- Error and success messages remain near the relevant workflow.
- Keyboard focus is visible.
- Reduced-motion preference is respected.
