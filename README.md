# ATLAS - Milestone 1

ATLAS is an AI-assisted requirement traceability and change-impact analysis platform. This milestone establishes a working full-stack foundation for later document intelligence, traceability, impact analysis, and RAG modules.

## Included in this milestone

- FastAPI application with versioned routes
- PostgreSQL and asynchronous SQLAlchemy
- Alembic database migration
- User registration, Argon2 password hashing, JWT login, and `/me`
- Protected project create/list/read/update/delete endpoints
- React 19 + Vite 8 + Tailwind CSS 4 frontend
- Login, registration, and project dashboard screens
- Docker Compose for PostgreSQL, backend, and frontend
- Basic backend tests and formatting configuration

## Prerequisites

### Recommended: Docker Desktop

1. Copy the environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Replace `JWT_SECRET_KEY` in `.env` with a long random value.

3. Start the stack:

   ```powershell
   docker compose up --build
   ```

4. Open:

   - Frontend: http://localhost:5173
   - API documentation: http://localhost:8000/docs
   - API health: http://localhost:8000/api/v1/health

5. Stop the stack:

   ```powershell
   docker compose down
   ```

To delete the development database volume too:

```powershell
docker compose down -v
```

## Local backend setup without Docker

Use Python 3.12 or newer and a running PostgreSQL instance.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example ..\.env
alembic upgrade head
uvicorn app.main:app --reload
```

For a locally installed PostgreSQL server, change `DATABASE_URL` host from `postgres` to `localhost`.

Run tests:

```powershell
pytest
```

Check formatting and common errors:

```powershell
ruff check .
```

## Local frontend setup without Docker

Use Node.js 22.12 or newer.

```powershell
cd frontend
npm install
npm run dev
```

The frontend reads `VITE_API_URL`. Its fallback is `http://localhost:8000/api/v1`.

## First verification flow

1. Visit the registration page and create an account.
2. Log in using the same email and password.
3. Create a project from the dashboard.
4. Refresh the page and confirm that the project remains available.
5. Open Swagger at `/docs`, authorize using the login endpoint's token, and test `/auth/me`.

## Current API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Service health check |
| POST | `/api/v1/auth/register` | Create user account |
| POST | `/api/v1/auth/login` | Obtain JWT access token |
| GET | `/api/v1/auth/me` | Read current authenticated user |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects` | List current user's projects |
| GET | `/api/v1/projects/{project_id}` | Read one project |
| PATCH | `/api/v1/projects/{project_id}` | Update one project |
| DELETE | `/api/v1/projects/{project_id}` | Delete one project |

## Next milestone

The next implementation stage adds document upload, PDF/DOCX validation, text extraction, document metadata, storage isolation per project, and requirement extraction records.
