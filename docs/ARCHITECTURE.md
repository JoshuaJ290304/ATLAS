# ATLAS Architecture

## Logical architecture

```text
React + Vite + Nginx
        |
        | HTTPS / JSON API
        v
FastAPI + Pydantic
        |
        +-- SQLAlchemy async + PostgreSQL
        +-- PyMuPDF / python-docx
        +-- ChromaDB + Sentence Transformers
        +-- Ollama
        +-- SMTP
```

## Backend organization

- `app/api/v1/endpoints`: HTTP routes and authorization boundaries
- `app/schemas`: request and response validation
- `app/models`: SQLAlchemy persistence models
- `app/services`: domain logic and external-service integration
- `app/core`: configuration and cryptographic helpers
- `alembic/versions`: ordered database migrations

## Security boundaries

- Access tokens include issuer, audience, expiry, unique token ID, password version, and session version.
- Every project route validates ownership before accessing project records.
- Admin routes require the backend `CurrentAdmin` dependency.
- Authentication rate-limit events are persisted as HMAC-derived identifiers rather than plaintext emails or IP addresses.
- Password reset tokens are random, stored only as hashes, and single-use.

## Data lifecycle

Documents are stored under project-isolated UUID directories. Requirements, traceability links, impact analyses, baselines, test cases, release candidates, and audit records are stored in PostgreSQL. The assistant vector index is project-isolated in persistent Chroma storage.

## Migration history

| Revision | Capability |
|---|---|
| 0001 | Users and projects |
| 0002 | Documents |
| 0003 | Requirements |
| 0004 | Traceability |
| 0005 | Impact analysis |
| 0006 | AI assistant |
| 0007 | Governance and baselines |
| 0008 | Governance completeness |
| 0009 | Test Case Intelligence |
| 0010 | Release readiness |
| 0011 | Password recovery |
| 0012 | Administration |
| 0013 | Persistent authentication rate limiting |
