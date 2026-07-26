# ATLAS Installation Guide

## Development installation

### Requirements

- Docker Desktop with Linux containers
- Docker Compose v2 or later
- Git
- At least 8 GB RAM; 16 GB is recommended when embeddings and Ollama are enabled

### Start ATLAS

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace `JWT_SECRET_KEY` with a unique random value. For example:

```powershell
$bytes = New-Object byte[] 64
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
[Convert]::ToBase64String($bytes)
```

Then start the platform:

```powershell
docker compose up --build -d
docker compose ps
```

Open:

- ATLAS: `http://localhost:5173`
- API documentation in development: `http://localhost:8000/docs`
- Backend liveness: `http://localhost:8000/api/v1/health/live`
- Backend readiness: `http://localhost:8000/api/v1/health/ready`
- Mailpit: `http://localhost:8025`

### AI setup

ATLAS can use Ollama installed on Windows:

```powershell
ollama pull qwen3:4b-instruct
```

Keep this setting in `.env`:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

ATLAS continues with retrieval-only answers when Ollama is unavailable and fallback is enabled.

## Production configuration

Copy `.env.production.example` to a protected deployment-specific `.env` and replace every `REPLACE_WITH_...` value.

Production mode enforces these rules at application startup:

- `DEBUG=false`
- `ENABLE_API_DOCS=false`
- a unique JWT secret of at least 48 characters
- no default database password
- explicit CORS origins
- explicit trusted hosts

Terminate TLS at a trusted reverse proxy and expose only the public frontend/API endpoints. Do not expose PostgreSQL, Mailpit, Ollama, or storage directories to the internet.

## Upgrade an existing installation

1. Create a database and source backup.
2. Pull or apply the new source.
3. Rebuild images.
4. Run migrations.
5. Verify readiness and tests.

```powershell
docker compose build backend frontend
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend pytest -q
```

The expected RC2 migration head is `0013`.
