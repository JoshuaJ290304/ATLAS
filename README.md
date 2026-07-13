# ATLAS

**AI-Assisted Requirement Traceability and Change Impact Analysis Platform**

ATLAS is a full-stack MCA major project that converts project documents into structured requirements, links those requirements to software artifacts, and explains the impact of requirement changes.

## Current release

**v0.5.0 — Change-impact analysis**

Development branch used for this milestone:

```text
feature/milestone-5-impact-analysis
```

## Project status

| Milestone | Module | Status |
|---|---|---|
| 1 | Authentication and project management | Completed |
| 2 | Document upload and text extraction | Completed |
| 3 | Requirement intelligence | Completed |
| 4 | Traceability engine | Completed |
| 5 | Change-impact analysis and UI corrections | Completed |
| 6 | AI project assistant | Next |
| 7 | Analytics and reporting | Planned |

## Main features

### Authentication and projects

- Registration and Argon2 password hashing
- JWT login and protected endpoints
- Owner-isolated project CRUD

### Documents

- PDF and DOCX upload
- Size, extension, and binary-signature checks
- SHA-256 checksum
- Project-isolated storage
- PyMuPDF and `python-docx` text extraction
- Document list, text, download, and delete operations

### Requirement intelligence

- Deterministic requirement extraction
- Functional/non-functional classification
- Non-functional categories
- Confidence score and ambiguity warnings
- Manual creation, editing, status management, and versioning

### Traceability

- API, database-table, test-case, and UML-component artifacts
- Manual links and explainable suggestions
- Accept/reject review workflow
- Traceability matrix and coverage metrics

### Change-impact analysis

- Immutable requirement snapshots
- Version-to-version comparison
- Changed fields, added/removed terms, and unified text diff
- Directly affected artifacts from accepted links
- Transitive impact paths through the trace graph
- Explainable 0–100 risk score
- Low, medium, high, and critical severity
- Persistent impact reports and history

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, React Router, Axios |
| Backend | FastAPI, Pydantic, SQLAlchemy asyncio |
| Database | PostgreSQL |
| Migrations | Alembic |
| Documents | PyMuPDF, python-docx |
| Security | JWT, Argon2 |
| Deployment | Docker Compose, Nginx |
| Quality | Pytest, Ruff |

## Run with Docker

```powershell
Copy-Item .env.example .env
```

Replace `JWT_SECRET_KEY` in `.env`, then run:

```powershell
docker compose up --build -d
docker compose ps
```

Open:

- Frontend: `http://localhost:5173`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

View logs:

```powershell
docker compose logs --tail=150 postgres backend frontend
```

Stop the project:

```powershell
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to delete the local PostgreSQL data volume.

## Database migrations

| Revision | Purpose |
|---|---|
| `0001` | Users and projects |
| `0002` | Documents |
| `0003` | Requirements |
| `0004` | Artifacts and trace links |
| `0005` | Requirement snapshots and impact reports |

The backend container runs `alembic upgrade head` during startup.

Manual commands:

```powershell
docker compose exec backend alembic current
docker compose exec backend alembic history
docker compose exec backend alembic upgrade head
```

## Milestone 5 workflow

1. Open a project and create or extract requirements.
2. Open **Traceability**, create artifacts, and accept correct links.
3. Open **Requirements**, edit and save a requirement to create another version.
4. Open **Impact**.
5. Select the requirement, baseline version, and target version.
6. Generate a report.
7. Review changed fields, direct artifacts, transitive paths, risk factors, and severity.
8. Reopen the report from history after a restart.

Only accepted trace links influence impact analysis. Suggested and rejected links are excluded.

## Impact risk model

| Factor | Maximum points |
|---|---:|
| Textual change magnitude | 30 |
| Directly affected artifacts | 30 |
| Transitive artifacts | 15 |
| Requirement lifecycle status | 10 |
| Ambiguity and high-risk NFR category | 10 |
| Traceability uncertainty | 5 |

Severity:

- Low: 0–24
- Medium: 25–49
- High: 50–74
- Critical: 75–100

The score is an explainable engineering heuristic, not a statistical probability.

## API groups

- `/api/v1/auth`
- `/api/v1/projects`
- `/api/v1/projects/{project_id}/documents`
- `/api/v1/projects/{project_id}/requirements`
- `/api/v1/projects/{project_id}/artifacts`
- `/api/v1/projects/{project_id}/trace-links`
- `/api/v1/projects/{project_id}/traceability`
- `/api/v1/projects/{project_id}/impact-analyses`

Requirement version endpoints:

```text
GET /api/v1/projects/{project_id}/requirements/{requirement_id}/versions
GET /api/v1/projects/{project_id}/requirements/{requirement_id}/compare
```

## Testing

```powershell
docker compose exec backend pytest -q
docker compose exec backend ruff check .
docker compose build frontend
```

## Git release workflow

After local testing:

```powershell
git add .
git commit -m "feat: add change impact analysis and responsive project actions"
git push -u origin feature/milestone-5-impact-analysis
```

Merge and tag only after the full local workflow passes:

```powershell
git switch main
git pull origin main
git merge --no-ff feature/milestone-5-impact-analysis -m "merge: complete milestone 5 impact analysis"
git push origin main
git tag -a v0.5.0 -m "ATLAS v0.5.0 - Change impact analysis"
git push origin v0.5.0
```

## Current limitations

- Historical requirement states from before migration `0005` cannot be reconstructed.
- Scanned PDFs require OCR, which is not implemented yet.
- Transitive impact uses accepted trace paths, not source-code call graphs.
- The risk model is deterministic and intentionally reviewable.
- AI-assisted semantic classification and question answering are planned for Milestone 6.

## Next milestone

### Milestone 6 — AI Project Assistant

Planned work:

- Project-isolated semantic search
- Text chunking and embeddings
- ChromaDB vector storage
- Ollama local LLM integration
- Retrieval-Augmented Generation
- Source-cited project answers
- Requirement and artifact explanations
