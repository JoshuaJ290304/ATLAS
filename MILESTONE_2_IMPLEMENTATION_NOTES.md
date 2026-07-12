# ATLAS Milestone 2 — Document Processing

## Implemented

- Added `documents` table through Alembic migration `0002`.
- Added owner-protected, project-scoped document APIs.
- Added PDF and DOCX uploads with a configurable 10 MB default limit.
- Added filename sanitization and PDF/DOCX signature validation.
- Added SHA-256 checksums and document metadata.
- Added PDF extraction using PyMuPDF.
- Added DOCX paragraph and table extraction using python-docx.
- Added project-isolated persistent storage at `storage/uploads/<project_id>/`.
- Added document listing, metadata read, extracted-text read, download, and deletion.
- Added physical storage cleanup when a document or project is deleted.
- Added a React project document workspace with upload, status, download, and delete actions.

## New API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/projects/{project_id}/documents` | Upload and extract a PDF/DOCX |
| GET | `/api/v1/projects/{project_id}/documents` | List project documents |
| GET | `/api/v1/projects/{project_id}/documents/{document_id}` | Read document metadata |
| GET | `/api/v1/projects/{project_id}/documents/{document_id}/text` | Read extracted text |
| GET | `/api/v1/projects/{project_id}/documents/{document_id}/download` | Download original file |
| DELETE | `/api/v1/projects/{project_id}/documents/{document_id}` | Delete metadata and file |

## Verification completed before packaging

- Ruff: passed.
- Pytest: 7 tests passed.
- Frontend production build: passed; 85 modules transformed.
- Alembic PostgreSQL SQL generation through revision `0002`: passed.
- FastAPI route registration: passed.

## Local acceptance test

1. Apply the patch from the repository root.
2. Rebuild and start:

   ```powershell
   docker compose down
   docker compose up --build -d
   docker compose ps
   ```

3. Check migration and startup logs:

   ```powershell
   docker compose logs --tail=120 postgres backend frontend
   ```

4. Open `http://localhost:5173`.
5. Log in and click **Documents** on a project.
6. Upload a valid PDF or DOCX under 10 MB.
7. Confirm status is `extracted` and character/page counts appear.
8. Download the original file.
9. Delete it and confirm it disappears from `storage/uploads/<project_id>/`.
10. Confirm an invalid `.pdf` containing plain text is rejected.

## Versioning

Keep these changes on `feature/milestone-2-document-processing` until local acceptance passes.

Suggested commit:

```powershell
git add .
git commit -m "feat: add project document upload and text extraction"
git push -u origin feature/milestone-2-document-processing
```

After local acceptance and merge to `main`, update `VERSION` to `0.2.0`, move the Milestone 2 changelog items from **Unreleased** to **0.2.0**, then create and push tag `v0.2.0`.
