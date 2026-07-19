# Quality Assurance Checklist

## Automated checks

```powershell
docker compose exec backend pytest -q
docker compose exec backend ruff check .
docker compose build frontend
```

## Functional regression

- Register, log in, log out, and verify expired-session handling.
- Create, list, search, and reopen projects.
- Upload, extract, download, and delete PDF/DOCX documents.
- Extract, create, edit, classify, version, and delete requirements.
- Create artifacts and review traceability links.
- Generate and reopen impact reports.
- Build and clear the assistant index; verify grounded answers and citations.
- Review analytics and export HTML, CSV, and JSON reports.
- Restart Docker and verify persistence.

## Interface review

Test at approximately 1440 px, 1024 px, 768 px, and 390 px.

- Header, footer, and project navigation remain accessible.
- Buttons remain inside cards.
- Forms use available width without overlap.
- Tables scroll horizontally when required.
- Text wraps without leaving its container.
- Error and success messages remain near the relevant workflow.
- Keyboard focus is visible.
- Reduced-motion preference is respected.
