@'
# Changelog

All notable changes to ATLAS will be documented in this file.

## [Unreleased]

### Planned

- PDF and DOCX upload
- Document metadata management
- Text extraction
- Requirement extraction preparation

## [0.1.0] - 2026-07-12

### Added

- FastAPI backend
- React and Tailwind CSS frontend
- PostgreSQL database integration
- Docker Compose environment
- Alembic migrations
- User registration and login
- Argon2 password hashing
- JWT authentication
- Project CRUD operations
- Swagger API documentation
- Backend tests and linting

### Fixed

- Replaced inaccessible registry URLs in package-lock.json
- Changed frontend Docker image to Node 20 Bookworm Slim
- Corrected frontend dependency installation
'@ | Set-Content ".\CHANGELOG.md" -Encoding UTF8