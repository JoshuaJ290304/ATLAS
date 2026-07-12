@'
# Changelog

All notable changes to ATLAS will be documented in this file.

## [Unreleased]

### Planned

- PDF and DOCX upload
- Document metadata management
- Text extraction
- Requirement extraction preparation

## [0.2.0] - 2026-07-12

### Added

- Project-scoped PDF and DOCX uploads
- File-extension, size, and signature validation
- PostgreSQL document metadata
- Alembic documents-table migration
- PDF text extraction using PyMuPDF
- DOCX text extraction using python-docx
- SHA-256 file checksums
- Document listing and extracted-text endpoints
- Document download and deletion
- Project-isolated upload directories
- React document-management workspace
- Automatic stored-file cleanup

### Verified

- PDF upload and extraction
- Document metadata persistence
- Document download
- Document deletion
- Persistence after container restart
- Project ownership protection


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