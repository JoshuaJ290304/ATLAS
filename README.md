# ATLAS

**AI-Assisted Requirement Traceability and Change Impact Analysis Platform**

ATLAS is a full-stack MCA major project that converts software project documents into structured requirements, links those requirements to technical artifacts, explains the impact of changes, and answers project questions from indexed evidence.

## Current release

**v0.6.0 — AI Project Assistant**

Development branch used for this milestone:

```text
feature/milestone-6-ai-project-assistant
```

## Project status

| Milestone | Module | Status |
|---|---|---|
| 1 | Authentication and project management | Completed |
| 2 | Document upload and text extraction | Completed |
| 3 | Requirement intelligence | Completed |
| 4 | Traceability engine | Completed |
| 5 | Change-impact analysis and UI corrections | Completed |
| 6 | AI project assistant | Completed |
| 7 | Analytics and reporting | Next |

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
- Confidence scores and ambiguity warnings
- Manual creation, editing, status management, and versioning

### Traceability

- API, database-table, test-case, and UML-component artifacts
- Manual links and explainable suggestions
- Accept/reject review workflow
- Traceability matrix and coverage metrics

### Change-impact analysis

- Immutable requirement snapshots
- Version-to-version comparison
- Direct and transitive affected artifacts
- Explainable 0–100 risk score and severity
- Persistent impact reports and history

### AI project assistant

- Project-isolated knowledge indexing
- Deterministic text chunking with overlap
- Sentence Transformer embeddings
- Persistent ChromaDB vector storage
- Semantic search across documents, requirements, artifacts, and impact reports
- Retrieval-Augmented Generation through a local Ollama model
- Numbered source citations
- Persistent project conversations and messages
- Retrieval-only fallback when Ollama is unavailable
- Index status, rebuild, and clear operations

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, React Router, Axios |
| Backend | FastAPI, Pydantic, SQLAlchemy asyncio |
| Database | PostgreSQL |
| Migrations | Alembic |
| Documents | PyMuPDF, python-docx |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector database | ChromaDB persistent client |
| Local LLM | Ollama with configurable Qwen/Llama/Gemma model |
| Security | JWT, Argon2 |
| Deployment | Docker Compose, Nginx |
| Quality | Pytest, Ruff |

## Prerequisites

- Docker Desktop with Linux containers and WSL 2
- Git
- Visual Studio Code
- Ollama for full generated answers

Verify Docker:

```powershell
docker --version
docker compose version
docker info
```

## Environment setup

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Replace `JWT_SECRET_KEY` with a long private value.

Important assistant settings:

```env
CHROMA_PERSIST_ROOT=storage/vector
MODEL_CACHE_ROOT=storage/models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:4b-instruct
ASSISTANT_ALLOW_RETRIEVAL_FALLBACK=true
```

Never commit `.env`, vector data, downloaded models, or uploaded project documents.

## Ollama setup

### Recommended: Ollama installed on Windows

Install and start Ollama, then pull the configured model:

```powershell
ollama pull qwen3:4b-instruct
ollama list
```

The backend container reaches Windows Ollama through:

```text
http://host.docker.internal:11434
```

### Optional: Ollama Docker profile

Change `.env`:

```env
OLLAMA_BASE_URL=http://ollama:11434
```

Start the optional service and pull the model:

```powershell
docker compose --profile ai up -d ollama
docker exec atlas-ollama ollama pull qwen3:4b-instruct
docker compose restart backend
```

Do not run both host Ollama and the Docker Ollama service on port `11434` at the same time.

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

Stop the project:

```powershell
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to delete PostgreSQL and Ollama volumes.

## Database migrations

| Revision | Purpose |
|---|---|
| `0001` | Users and projects |
| `0002` | Documents |
| `0003` | Requirements |
| `0004` | Artifacts and trace links |
| `0005` | Requirement snapshots and impact reports |
| `0006` | Knowledge chunks, assistant index, conversations, and messages |

The backend runs `alembic upgrade head` during startup.

```powershell
docker compose exec backend alembic current
docker compose exec backend alembic history
```

## AI assistant workflow

1. Create or open a project.
2. Upload at least one PDF or DOCX with selectable text.
3. Extract or create requirements.
4. Add software artifacts and impact reports when available.
5. Open **AI Assistant** from the project card.
6. Click **Build index**.
7. Wait for the embedding model to download on the first run.
8. Use **Semantic search** to inspect retrieved evidence.
9. Use **Ask project** for a grounded answer with numbered citations.
10. Rebuild the index whenever project documents or structured records change.

Indexed source types:

- Uploaded document text
- Requirements
- Software artifacts
- Impact-analysis reports

Only data belonging to the selected project is retrieved.

## Retrieval and answer behavior

ATLAS embeds project chunks with Sentence Transformers and stores them in a persistent ChromaDB collection. Questions are embedded using the same model and filtered by `project_id` before nearest-neighbor retrieval.

The Ollama prompt contains only the retrieved project evidence and instructs the model to:

- Avoid unsupported claims
- State when evidence is insufficient
- Cite claims using `[1]`, `[2]`, and similar markers

When Ollama cannot be reached and retrieval fallback is enabled, ATLAS returns the strongest evidence excerpts instead of inventing an answer.

## Assistant API endpoints

Base path:

```text
/api/v1/projects/{project_id}/assistant
```

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/status` | Read index, Ollama, and model status |
| POST | `/index` | Build or rebuild project knowledge index |
| DELETE | `/index` | Clear project knowledge index |
| POST | `/search` | Run project-isolated semantic search |
| POST | `/ask` | Ask a grounded project question |
| GET | `/conversations` | List project conversations |
| GET | `/conversations/{conversation_id}` | Read messages and citations |
| DELETE | `/conversations/{conversation_id}` | Delete a conversation |

## Assistant storage

Generated local data is stored under:

```text
storage/vector/   # ChromaDB persistence
storage/models/   # Sentence Transformer/Hugging Face cache
```

These folders are mounted into the backend container and excluded from Git, except for `.gitkeep` files.

## Testing

```powershell
docker compose exec backend pytest -q
docker compose exec backend ruff check .
docker compose build frontend
```

Milestone 6 verification target:

```text
29 backend tests passing
Frontend production build successful (89 modules)
Alembic migration 0006 successful
8 assistant API operations registered
```

## Git release workflow

After local testing:

```powershell
git add .
git commit -m "feat: add source-grounded AI project assistant"
git push -u origin feature/milestone-6-ai-project-assistant
```

Merge and tag only after indexing, search, Ollama answers, fallback answers, citations, persistence, and deletion pass:

```powershell
git switch main
git pull origin main
git merge --no-ff feature/milestone-6-ai-project-assistant -m "merge: complete milestone 6 AI project assistant"
git push origin main
git tag -a v0.6.0 -m "ATLAS v0.6.0 - AI project assistant"
git push origin v0.6.0
```

## Current limitations

- The first index build requires internet access to download the embedding model unless it is already cached.
- Full generated answers require Ollama and the configured model.
- Chunks from PDFs currently cite the document rather than exact page coordinates.
- Scanned PDFs require OCR, which is not implemented yet.
- Indexing runs synchronously and is intended for student-scale projects.
- Rebuild the index after changing documents, requirements, artifacts, or impact reports.
- Answers are grounded by retrieval, but users should still verify critical engineering decisions against cited sources.

## Next milestone

### Milestone 7 — Analytics and Reporting

Planned work:

- Project health dashboard
- Requirement-type and status charts
- Ambiguity trends
- Traceability and coverage analytics
- Impact-risk distribution
- Document and assistant usage statistics
- Exportable project report
- Final deployment, documentation, and release preparation
