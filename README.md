# ATLAS — Milestone 1

ATLAS is an AI-assisted requirement traceability and change-impact analysis platform. This milestone establishes the working full-stack foundation for document intelligence, traceability, impact analysis, and RAG modules.

## Version

Current release: **v0.1.0**

## Included in this milestone

* FastAPI application with versioned API routes
* PostgreSQL with asynchronous SQLAlchemy
* Alembic database migrations
* User registration
* Argon2 password hashing
* JWT authentication
* Authenticated `/auth/me` endpoint
* Protected project CRUD endpoints
* React, Vite, and Tailwind CSS frontend
* Login, registration, and project-dashboard screens
* Docker Compose environment
* Backend tests and linting configuration

## Prerequisites

### Recommended: Docker Desktop

1. Create the local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Replace `JWT_SECRET_KEY` in `.env` with a long random value.

3. Start the application:

   ```powershell
   docker compose up --build
   ```

4. Open:

   * Frontend: `http://localhost:5173`
   * API documentation: `http://localhost:8000/docs`
   * API health endpoint: `http://localhost:8000/api/v1/health`

5. Stop the application:

   ```powershell
   docker compose down
   ```

To remove the PostgreSQL development volume:

```powershell
docker compose down -v
```

## Local backend setup without Docker

Use Python 3.12 or newer and a running PostgreSQL server.

```powershell
cd backend

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

Copy-Item ..\.env.example ..\.env

alembic upgrade head
uvicorn app.main:app --reload
```

For a locally installed PostgreSQL server, change the `DATABASE_URL` host from `postgres` to `localhost`.

Run the backend tests:

```powershell
pytest
```

Run lint checks:

```powershell
ruff check .
```

## Local frontend setup without Docker

Use Node.js 20.19 or newer, or Node.js 22.12 or newer.

```powershell
cd frontend

npm install
npm run dev
```

The frontend reads the `VITE_API_URL` environment variable. Its fallback value is:

```text
http://localhost:8000/api/v1
```

## First verification flow

1. Open the registration page and create an account.
2. Log in using the registered email and password.
3. Create a project from the dashboard.
4. Refresh the page and confirm that the project remains available.
5. Restart the Docker containers and verify database persistence.
6. Open Swagger and test the authenticated endpoints.

## Current API endpoints

| Method | Endpoint                        | Purpose                          |
| ------ | ------------------------------- | -------------------------------- |
| GET    | `/api/v1/health`                | Check API health                 |
| POST   | `/api/v1/auth/register`         | Create a user account            |
| POST   | `/api/v1/auth/login`            | Obtain a JWT access token        |
| GET    | `/api/v1/auth/me`               | Read the authenticated user      |
| POST   | `/api/v1/projects`              | Create a project                 |
| GET    | `/api/v1/projects`              | List the current user’s projects |
| GET    | `/api/v1/projects/{project_id}` | Read one project                 |
| PATCH  | `/api/v1/projects/{project_id}` | Update one project               |
| DELETE | `/api/v1/projects/{project_id}` | Delete one project               |

## Versioning

ATLAS follows Semantic Versioning:

* `v0.1.0` — Milestone 1 foundation
* `v0.1.x` — Milestone 1 fixes
* `v0.2.0` — Milestone 2 document processing
* `v1.0.0` — First stable release

## Next milestone

Milestone 2 will add:

* PDF and DOCX upload
* File-type and file-size validation
* Project-isolated document storage
* Document metadata in PostgreSQL
* PDF text extraction with PyMuPDF
* DOCX text extraction with `python-docx`
* Uploaded-document management
* Requirement extraction preparation
