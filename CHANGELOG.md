@'
# Changelog

All notable changes to ATLAS will be documented in this file.

## [0.4.0] - 2026-07-13

### Added

- Software artifact management
- API, database-table, test-case, and UML-component artifacts
- Manual requirement-to-artifact traceability links
- Automatic trace-link suggestions
- Explainable confidence scoring
- Accept and reject review workflow
- Traceability matrix
- Requirement coverage metrics
- Artifact coverage metrics
- Cascade deletion for artifact trace links
- Alembic traceability migration
- React traceability workspace

### Verified

- Artifact creation, editing, and deletion
- Automatic suggestion generation
- Accept and reject workflow
- Manual traceability links
- Traceability matrix states
- Requirement and artifact coverage
- Restart persistence
- Cascade cleanup after artifact deletion

### Known Issues

- Project-card navigation buttons can overflow or become misaligned on some screen sizes.
- Rejected trace-link count is not displayed in the top traceability summary cards.
- These UI issues are scheduled for correction in Milestone 5.


## [0.3.0] - 2026-07-13

### Added

- Requirement extraction from uploaded document text
- Functional and non-functional requirement classification
- Non-functional categories for security, performance, availability, usability, reliability, maintainability, and scalability
- Requirement classification confidence scores
- Ambiguous-language detection
- Readable ambiguity reasons
- Manual requirement creation
- Requirement editing
- Requirement status management
- Requirement version history
- Duplicate extraction prevention
- Requirement deletion
- Project ownership protection for requirement operations
- Alembic requirements migration
- React requirement-management workspace

### Verified

- Requirement extraction from uploaded documents
- Functional and non-functional classification
- Ambiguity flag generation
- Manual requirement creation
- Requirement editing
- Version increment after editing
- Requirement deletion
- Persistence after Docker restart
- Backend tests
- Frontend production build

### Limitations

- Requirement extraction is currently rule-based.
- Scanned PDFs without selectable text are not supported.
- OCR is not yet implemented.
- AI-based classification is planned for a later milestone.


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