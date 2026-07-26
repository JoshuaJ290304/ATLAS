# ATLAS

**AI-Assisted Requirement Traceability and Change Impact Analysis Platform**

ATLAS is a full-stack requirements engineering platform that converts software project documents into structured requirements, links requirements to technical artifacts, governs review and approval, explains the impact of changes, answers project questions from indexed evidence, and presents project health through an analytics and reporting dashboard.

## Current release

**v0.10.0 — Release Readiness and Quality Gates**

Development branch:

```text
feature/milestone-10-release-readiness
```

## Project status

| Milestone | Module | Status |
|---|---|---|
| 1 | Authentication and project management | Completed |
| 2 | Document upload and text extraction | Completed |
| 3 | Requirement intelligence | Completed |
| 4 | Traceability engine | Completed |
| 5 | Change-impact analysis | Completed |
| 6 | AI project assistant | Completed |
| 7 | Analytics, reporting, UI/UX, and validation | Completed |
| 8 | Requirement governance, review, and baselines | Completed |
| 9 | Test Case Intelligence | Completed |
| 10 | Release readiness and quality gates | In development |

## Main capabilities

### Authentication and project management

- Registration with strong-password validation
- Argon2 password hashing and JWT authentication
- Owner-isolated project CRUD
- Duplicate project-name protection
- Responsive project dashboard with direct access to every module

### Document intelligence

- PDF and DOCX upload
- File extension, size, and binary-signature validation
- SHA-256 checksum and project-isolated storage
- Text extraction using PyMuPDF and `python-docx`
- Document metadata, download, and deletion

### Requirement intelligence

- Deterministic requirement extraction
- Functional and non-functional classification
- Non-functional categories
- Confidence and ambiguity scores
- Manual creation, review status, editing, and immutable version snapshots

### Traceability

- API, database-table, test-case, and UML-component artifacts
- Manual and explainable suggested links
- Accept/reject workflow
- Requirement and artifact coverage
- Traceability matrix

### Change-impact analysis

- Requirement version comparison
- Direct and transitive affected artifacts
- Explainable 0–100 risk score
- Low, medium, high, and critical severity
- Persistent impact reports and history

### AI project assistant

- Project-isolated semantic index
- Sentence Transformer embeddings
- Persistent ChromaDB storage
- Ollama-based grounded answers
- Numbered citations
- Semantic search and persistent conversations
- Retrieval-only fallback when Ollama is unavailable


### Requirement governance

- Requirement review requests and reviewer assignment
- Approval and rejection decisions with mandatory rationale
- Timestamped requirement comments
- Immutable approved-requirement baselines
- Added, modified, removed, and unchanged baseline comparison
- Governance audit history


### Test Case Intelligence

- Manual and AI-assisted test-case authoring
- Numbered steps and expected results
- Requirement-to-test traceability
- Draft, review, approval, rejection, and needs-review states
- Test-case version history and approved coverage analytics

### Release readiness and quality gates

- Release-candidate planning with selected baselines, requirements, and test cases
- Configurable traceability, test-coverage, impact-risk, and overdue-review thresholds
- Ten explainable quality gates with Passed, Failed, Warning, and Not Evaluated outcomes
- Weighted readiness score with Ready, At Risk, and Blocked classifications
- Release review, approval/rejection, publication lock, and audit events
- Candidate comparison plus JSON and CSV readiness reports

### Analytics and reporting

- Project-health score from 0 to 100
- Explainable health factors and improvement priorities
- Document extraction statistics
- Requirement type, status, category, review, and ambiguity analytics
- Artifact inventory analytics
- Traceability coverage and link-status analytics
- Impact-risk and severity analytics
- Assistant index and usage statistics
- Recent project activity
- Standalone HTML report download
- CSV and JSON exports

## UI/UX improvements in v0.7.0

- Unified visual design system across all modules
- Responsive project navigation and project action grid
- Consistent cards, typography, spacing, buttons, inputs, alerts, and tables
- Polished authentication experience
- Mobile-friendly layouts and horizontal navigation
- Loading, empty, success, warning, and error states
- Keyboard-visible focus states and readable contrast
- Reduced-motion support

## Validation model

ATLAS validates data in both React and FastAPI.

### Frontend validation

- Required fields and blank-space prevention
- Minimum and maximum lengths
- Email format
- Strong password rules and password confirmation
- PDF/DOCX type and 10 MB size checks
- Non-functional category requirement
- Artifact and requirement form validation
- Requirement-version ordering for impact analysis
- Assistant search and question length checks
- Inline field-specific errors
- Disabled submit buttons during requests

### Backend validation

- Pydantic field limits and enum validation
- Trimmed and normalized text
- Strong registration password rules
- Duplicate project and artifact name checks
- Non-functional category enforcement
- Trace-confidence ranges
- Impact baseline/target ordering
- File binary-signature and size validation
- Project ownership enforcement on every module

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, React Router, Axios |
| Backend | FastAPI, Pydantic, SQLAlchemy asyncio |
| Database | PostgreSQL |
| Migrations | Alembic |
| Documents | PyMuPDF, python-docx |
| Embeddings | Sentence Transformers |
| Vector database | ChromaDB |
| Local LLM | Ollama |
| Security | JWT, Argon2 |
| Deployment | Docker Compose, Nginx |
| Quality | Pytest, Ruff |

## Prerequisites

- Docker Desktop using Linux containers and WSL 2
- Git
- Visual Studio Code
- Ollama for generated AI answers

## Environment setup

```powershell
Copy-Item .env.example .env
```

Replace `JWT_SECRET_KEY` with a long private value. Keep the existing database and assistant settings from `.env.example`.

Never commit `.env`, uploaded files, vector data, or downloaded models.

## Run with Docker

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
docker compose logs --tail=200 postgres backend frontend
```

## Database migrations

| Revision | Purpose |
|---|---|
| `0001` | Users and projects |
| `0002` | Documents |
| `0003` | Requirements |
| `0004` | Artifacts and trace links |
| `0005` | Requirement snapshots and impact reports |
| `0006` | AI assistant knowledge and conversation records |

Milestone 7 does not require a migration because all analytics are calculated from existing live records.

## Analytics workflow

1. Open a project.
2. Select **Analytics** from the project card or project navigation.
3. Review the health score and factor explanations.
4. Inspect requirement, artifact, traceability, impact, and assistant charts.
5. Review recent project activity.
6. Download an HTML, CSV, or JSON report.

### Analytics API

Base path:

```text
/api/v1/projects/{project_id}/analytics
```

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/analytics` | Read complete live project analytics |
| GET | `/analytics/export?format=html` | Download standalone HTML report |
| GET | `/analytics/export?format=csv` | Download metric rows as CSV |
| GET | `/analytics/export?format=json` | Download complete analytics as JSON |

## Project-health scoring

The score is deterministic and explainable:

| Factor | Maximum |
|---|---:|
| Document readiness | 15 |
| Requirement quality | 20 |
| Traceability coverage | 30 |
| Impact-analysis discipline | 15 |
| Artifact inventory | 10 |
| AI knowledge-index readiness | 10 |
| **Total** | **100** |

The dashboard presents each factor, its score, and the specific action that improves it.

## Ollama setup

For Ollama installed on Windows:

```powershell
ollama pull qwen3:4b-instruct
ollama list
```

Use:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

The assistant still provides retrieval-only evidence if Ollama is unavailable and fallback is enabled.

## Testing

```powershell
docker compose exec backend pytest -q
docker compose exec backend ruff check .
docker compose build frontend
```

Milestone 7 verified results:

```text
36 backend tests passed
Ruff checks passed
Frontend production build passed with 94 transformed modules
No Milestone 7 migration required
```

## Versioning

| Version | Description |
|---|---|
| `v0.1.0` | Authentication and projects |
| `v0.2.0` | Document upload and extraction |
| `v0.3.0` | Requirement intelligence |
| `v0.4.0` | Traceability engine |
| `v0.5.0` | Change-impact analysis |
| `v0.6.0` | AI project assistant |
| `v0.7.0` | Analytics, reporting, UI/UX, and validation |
| `v0.8.0` | Requirement governance, reviews, and baselines |
| `v0.8.1` | Review priority/due dates, selected baseline scope, status, and baseline comparison |
| `v1.0.0` | Stable final release |

## Current limitations

- The generated project report is HTML rather than PDF.
- Scanned PDFs require OCR, which is not implemented.
- Exact PDF page-coordinate citations are not available.
- Indexing and analytics are synchronous and intended for student-scale projects.
- Generated AI answers should be verified against their cited project evidence.

## Next release

### v1.0.0 — Final stable project

Planned finalization work:

- Full end-to-end acceptance test
- Production deployment guidance
- Optional cloud configuration
- Final MCA report and demonstration script
- Security and performance review
- Formal release notes and repository cleanup


## Requirement governance and baselines

ATLAS 0.8.1 completes the controlled governance workflow:

- Request a review for any requirement, assign an active user, set priority, and optionally set a due date.
- Record approval or rejection with a mandatory decision rationale.
- Discuss requirement details with timestamped comments.
- Create immutable baselines from explicitly selected approved requirements and record their active or archived status.
- Compare two baselines, or compare a baseline with the current specification, to identify added, modified, removed, and unchanged requirements.
- Review an audit history of governance actions.

The module is available from **Reviews & Baselines** in every project workspace.



## Milestone 9 — Test Case Intelligence

ATLAS 0.9.0 adds a traceable test engineering workspace with manual and AI-assisted test case authoring, numbered steps, review status, priorities, requirement coverage, and immutable version snapshots.

Project route: `/projects/{project_id}/test-cases`


