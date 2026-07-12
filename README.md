# ATLAS

**AI-Assisted Requirement Traceability and Change Impact Analysis Platform**

ATLAS is a full-stack software engineering platform designed to extract, classify, organize, and trace software requirements from project documents.

The system helps developers and project managers understand project requirements, detect ambiguous statements, establish relationships between software artifacts, and analyze the possible impact of requirement changes.

## Current Version

Development version: **v0.3.0**

Current branch:

```text
feature/milestone-3-requirement-intelligence
```

## Project Status

| Milestone   | Module                                | Status         |
| ----------- | ------------------------------------- | -------------- |
| Milestone 1 | Authentication and project management | Completed      |
| Milestone 2 | Document upload and text extraction   | Completed      |
| Milestone 3 | Requirement intelligence              | In development |
| Milestone 4 | Traceability engine                   | Planned        |
| Milestone 5 | Change-impact analysis                | Planned        |
| Milestone 6 | AI project assistant                  | Planned        |
| Milestone 7 | Analytics and reporting               | Planned        |

## Core Features

### Authentication

* User registration
* Argon2 password hashing
* JWT login
* Authenticated user profile
* Protected API endpoints
* Project ownership protection

### Project Management

* Create projects
* List projects
* View project details
* Update projects
* Delete projects
* Isolated data for each user

### Document Management

* Upload PDF and DOCX files
* Maximum file-size validation
* File-extension validation
* Actual PDF and DOCX signature validation
* SHA-256 file checksum generation
* Project-specific upload directories
* Document metadata stored in PostgreSQL
* PDF text extraction using PyMuPDF
* DOCX text extraction using `python-docx`
* Download uploaded documents
* Delete uploaded documents
* Automatic file cleanup

### Requirement Intelligence

* Extract requirement statements from document text
* Classify functional requirements
* Classify non-functional requirements
* Detect security requirements
* Detect performance requirements
* Detect availability requirements
* Detect usability requirements
* Calculate classification confidence
* Detect ambiguous requirement language
* Display ambiguity reasons
* Create requirements manually
* Edit requirement details
* Track requirement versions
* Update requirement review status
* Prevent duplicate extraction
* Delete requirements

## Technology Stack

### Frontend

* React
* Vite
* Tailwind CSS
* React Router
* Axios

### Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* Alembic
* JWT authentication
* Argon2 password hashing

### Database

* PostgreSQL

### Document Processing

* PyMuPDF
* `python-docx`

### Development and Deployment

* Docker
* Docker Compose
* Nginx
* Pytest
* Ruff
* Git and GitHub

## Project Structure

```text
ATLAS_Milestone_1/
│
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │       ├── 0001_create_users_and_projects.py
│   │       ├── 0002_create_documents.py
│   │       └── 0003_create_requirements.py
│   │
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │           ├── auth.py
│   │   │           ├── documents.py
│   │   │           ├── health.py
│   │   │           ├── projects.py
│   │   │           └── requirements.py
│   │   │
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   │   ├── document.py
│   │   │   ├── project.py
│   │   │   ├── requirement.py
│   │   │   └── user.py
│   │   │
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── DocumentsPage.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   └── RequirementsPage.jsx
│   │   └── App.jsx
│   │
│   ├── Dockerfile
│   ├── package.json
│   └── package-lock.json
│
├── storage/
│   └── uploads/
│
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── docker-compose.yml
├── VERSION
└── README.md
```

## Prerequisites

Install the following software:

* Docker Desktop
* Git
* Visual Studio Code

Docker Desktop must use Linux containers with the WSL 2 engine.

Check Docker:

```powershell
docker --version
docker compose version
docker info
```

## Environment Configuration

Create the local environment file:

```powershell
Copy-Item ".env.example" ".env"
```

Open `.env` and replace the example JWT secret:

```env
JWT_SECRET_KEY=replace_with_a_long_random_secret
```

Use a long private value.

Do not commit `.env` to Git.

Verify that Git ignores it:

```powershell
git check-ignore .env
git ls-files .env
```

The second command should return no output.

## Run the Project with Docker

From the project root, run:

```powershell
docker compose up --build -d
```

Check the containers:

```powershell
docker compose ps
```

View logs:

```powershell
docker compose logs --tail=150 postgres backend frontend
```

Open the application:

* Frontend: `http://localhost:5173`
* Swagger API: `http://localhost:8000/docs`
* Health endpoint: `http://localhost:8000/api/v1/health`

Stop the project:

```powershell
docker compose down
```

Stop the project and remove the PostgreSQL volume:

```powershell
docker compose down -v
```

> Removing the volume permanently deletes local database records.

## Database Migrations

Migrations are applied automatically when the backend container starts.

Current migrations:

```text
0001 - users and projects
0002 - documents
0003 - requirements and requirement versions
```

Run migrations manually:

```powershell
docker compose exec backend alembic upgrade head
```

Check the current migration:

```powershell
docker compose exec backend alembic current
```

View migration history:

```powershell
docker compose exec backend alembic history
```

## Local Backend Setup without Docker

Use Python 3.12 or newer and a running PostgreSQL instance.

```powershell
cd backend

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

alembic upgrade head

uvicorn app.main:app --reload
```

For a locally installed PostgreSQL server, change the host in `DATABASE_URL` from `postgres` to `localhost`.

Run backend tests:

```powershell
pytest -q
```

Run lint checks:

```powershell
ruff check .
```

## Local Frontend Setup without Docker

Use Node.js 20.19 or newer.

```powershell
cd frontend

npm install
npm run dev
```

Create a production build:

```powershell
npm run build
```

The frontend reads:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Application Workflow

### 1. Register

Open:

```text
http://localhost:5173/register
```

Create a user account with a valid name, email address, and password.

### 2. Log In

Open:

```text
http://localhost:5173/login
```

Use the registered credentials.

### 3. Create a Project

From the dashboard:

1. Click **Create Project**.
2. Enter the project name.
3. Enter an optional description.
4. Save the project.

### 4. Upload a Document

Open the project’s Documents page.

Upload a valid:

* PDF file
* DOCX file

The file must be within the configured maximum upload size.

ATLAS will:

1. Validate the file extension.
2. Validate the file signature.
3. Generate a SHA-256 checksum.
4. Save the file inside the project directory.
5. Extract the document text.
6. Store document metadata in PostgreSQL.

Uploaded files are stored under:

```text
storage/uploads/<project-id>/
```

### 5. Extract Requirements

Open the project’s Requirements page.

1. Select an uploaded document.
2. Click **Extract Requirements**.
3. Review the extracted statements.
4. Check their classifications.
5. Review ambiguity warnings.
6. Edit incorrect or incomplete requirements.
7. Mark requirements as reviewed or approved.

## Requirement Classification

ATLAS currently uses deterministic analysis rules.

### Functional Requirement

A functional requirement describes what the system must do.

Example:

```text
The system shall allow registered users to log in using email and password.
```

### Non-Functional Requirement

A non-functional requirement describes a quality attribute or operational constraint.

Example:

```text
The application shall respond within two seconds for 500 concurrent users.
```

Supported non-functional categories include:

* Performance
* Security
* Availability
* Usability
* Reliability
* Maintainability
* Scalability
* Other

## Ambiguity Detection

ATLAS identifies requirement statements that contain vague, subjective, or incomplete wording.

Examples of ambiguous terms:

* fast
* user-friendly
* efficient
* simple
* flexible
* appropriate
* sufficient
* usually
* generally
* should
* may
* and so on

Ambiguous example:

```text
The application should provide a fast and user-friendly interface.
```

This statement is ambiguous because:

* “should” is weaker than “shall” or “must”
* “fast” is not measurable
* “user-friendly” is subjective

A better version is:

```text
The application shall display the dashboard within two seconds for at least 95% of requests.
```

## Requirement Versioning

Each requirement starts with:

```text
Version 1
```

When an existing requirement is edited:

1. Its previous state is preserved.
2. The version number increases.
3. The updated content becomes the current version.

Example:

```text
Version 1 → Version 2
```

This provides an audit history for future traceability and impact analysis.

## API Endpoints

### Health

| Method | Endpoint         | Purpose          |
| ------ | ---------------- | ---------------- |
| GET    | `/api/v1/health` | Check API health |

### Authentication

| Method | Endpoint                | Purpose                     |
| ------ | ----------------------- | --------------------------- |
| POST   | `/api/v1/auth/register` | Create an account           |
| POST   | `/api/v1/auth/login`    | Obtain a JWT token          |
| GET    | `/api/v1/auth/me`       | Read the authenticated user |

### Projects

| Method | Endpoint                        | Purpose          |
| ------ | ------------------------------- | ---------------- |
| POST   | `/api/v1/projects`              | Create a project |
| GET    | `/api/v1/projects`              | List projects    |
| GET    | `/api/v1/projects/{project_id}` | Read a project   |
| PATCH  | `/api/v1/projects/{project_id}` | Update a project |
| DELETE | `/api/v1/projects/{project_id}` | Delete a project |

### Documents

| Method | Endpoint                                                         | Purpose                |
| ------ | ---------------------------------------------------------------- | ---------------------- |
| POST   | `/api/v1/projects/{project_id}/documents`                        | Upload a document      |
| GET    | `/api/v1/projects/{project_id}/documents`                        | List project documents |
| GET    | `/api/v1/projects/{project_id}/documents/{document_id}`          | Read document metadata |
| GET    | `/api/v1/projects/{project_id}/documents/{document_id}/download` | Download a document    |
| GET    | `/api/v1/projects/{project_id}/documents/{document_id}/text`     | Read extracted text    |
| DELETE | `/api/v1/projects/{project_id}/documents/{document_id}`          | Delete a document      |

### Requirements

| Method | Endpoint                                                               | Purpose                     |
| ------ | ---------------------------------------------------------------------- | --------------------------- |
| POST   | `/api/v1/projects/{project_id}/requirements/extract`                   | Extract requirements        |
| POST   | `/api/v1/projects/{project_id}/requirements`                           | Create a manual requirement |
| GET    | `/api/v1/projects/{project_id}/requirements`                           | List requirements           |
| GET    | `/api/v1/projects/{project_id}/requirements/{requirement_id}`          | Read a requirement          |
| PATCH  | `/api/v1/projects/{project_id}/requirements/{requirement_id}`          | Update a requirement        |
| GET    | `/api/v1/projects/{project_id}/requirements/{requirement_id}/versions` | View version history        |
| DELETE | `/api/v1/projects/{project_id}/requirements/{requirement_id}`          | Delete a requirement        |

## Testing

Run all backend tests:

```powershell
docker compose exec backend pytest -q
```

Run lint checks:

```powershell
docker compose exec backend ruff check .
```

Build the frontend:

```powershell
docker compose build frontend
```

Current Milestone 3 verification target:

```text
12 backend tests passing
Frontend production build successful
Alembic migration 0003 successful
```

## Git Workflow

ATLAS uses feature branches for each milestone.

Current branch:

```text
feature/milestone-3-requirement-intelligence
```

Commit Milestone 3 work:

```powershell
git add .

git commit -m "feat: add requirement extraction and ambiguity analysis"

git push -u origin feature/milestone-3-requirement-intelligence
```

After successful testing, merge it into `main`:

```powershell
git switch main
git pull origin main

git merge --no-ff feature/milestone-3-requirement-intelligence `
  -m "merge: complete milestone 3 requirement intelligence"

git push origin main
```

Create the Milestone 3 release:

```powershell
git tag -a v0.3.0 `
  -m "ATLAS v0.3.0 - Requirement intelligence"

git push origin v0.3.0
```

## Versioning

ATLAS follows Semantic Versioning.

| Version  | Description                                   |
| -------- | --------------------------------------------- |
| `v0.1.0` | Authentication and project management         |
| `v0.2.0` | Document upload and extraction                |
| `v0.3.0` | Requirement extraction and ambiguity analysis |
| `v0.4.0` | Traceability engine                           |
| `v0.5.0` | Change-impact analysis                        |
| `v0.6.0` | AI project assistant                          |
| `v1.0.0` | First stable release                          |

## Security Notes

* Never commit `.env`.
* Never commit JWT secret keys.
* Never commit database passwords.
* Uploaded files are isolated by project.
* API access is protected using JWT authentication.
* Project ownership is checked before document or requirement access.
* Uploaded file extensions and signatures are validated.
* Passwords are stored as Argon2 hashes.

## Current Limitations

* Requirement extraction is rule-based.
* Scanned PDFs without selectable text are not supported yet.
* OCR is not implemented.
* Requirement relationships are not yet generated.
* Source-code analysis is not yet implemented.
* LLM-based classification is planned for a later milestone.
* Real-time team collaboration is not yet implemented.

## Next Milestone

### Milestone 4 — Traceability Engine

The next milestone will add:

* Software artifact records
* API artifact management
* Database-table artifact management
* UML component management
* Test-case artifact management
* Requirement-to-artifact links
* Manual traceability links
* Suggested traceability links
* Link confidence scoring
* Traceability matrix
* Requirement coverage metrics
* Artifact coverage metrics

## License

This project is currently developed as an MCA major project.

A formal open-source license has not yet been selected.
