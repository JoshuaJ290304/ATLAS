# Changelog

All notable changes to ATLAS are documented here. The project follows Semantic Versioning.

## [Unreleased]

### Planned

- Local AI project assistant with semantic search and source citations
- ChromaDB vector indexing and Ollama integration
- Analytics and reporting improvements

## [0.5.0] - 2026-07-13

### Added

- Persisted requirement-version snapshots
- Requirement version list and comparison endpoints
- Deterministic requirement change detection
- Directly affected artifact discovery through accepted trace links
- Transitive impact paths through the requirement-artifact graph
- Reproducible risk scoring from change magnitude, trace scope, lifecycle status, and quality signals
- Low, medium, high, and critical impact severity
- Explainable risk-factor breakdown
- Stored change summaries and impact-analysis history
- Impact-report detail and deletion endpoints
- React impact-analysis workspace
- Alembic migration `0005`

### Changed

- Project-card actions now use a responsive two-column grid and remain inside each card.
- Added an Impact action to every project card.
- Traceability summary now displays rejected-link count.
- API application version updated to `0.5.0`.

### Verified

- Requirement snapshots are created for new, extracted, and edited requirements.
- Version comparisons identify changed fields and added/removed terms.
- Suggested/rejected links are excluded from impact paths.
- Direct and transitive artifacts are resolved from accepted trace links.
- Risk scoring is deterministic.
- Impact reports persist and can be reopened or deleted.
- Dashboard and traceability UI corrections build successfully.

### Limitations

- Requirement versions created before migration `0005` cannot be reconstructed; the current stored state becomes the first available snapshot.
- Transitive impact follows accepted requirement-artifact paths and does not yet include source-code call graphs.
- Risk scores are explainable heuristics, not probability estimates.

## [0.4.0] - 2026-07-13

### Added

- Software artifact management
- API, database-table, test-case, and UML-component artifacts
- Manual requirement-to-artifact links
- Explainable automatic trace-link suggestions
- Confidence scoring and accept/reject review workflow
- Traceability matrix
- Requirement and artifact coverage metrics
- Cascade deletion for artifact trace links
- Alembic migration `0004`
- React traceability workspace

### Known Issues

- Project-card navigation actions could overflow on some screen sizes.
- Rejected trace-link count was not displayed in the top summary.

Both issues are corrected in `v0.5.0`.

## [0.3.0] - 2026-07-13

### Added

- Requirement extraction from uploaded document text
- Functional and non-functional classification
- Classification confidence scores
- Ambiguous-language detection with readable reasons
- Manual requirement creation and editing
- Requirement status management and version increments
- Duplicate extraction prevention
- Alembic migration `0003`
- React requirement-management workspace

## [0.2.0] - 2026-07-12

### Added

- Project-scoped PDF and DOCX uploads
- File extension, size, and signature validation
- SHA-256 checksums and PostgreSQL document metadata
- PDF extraction with PyMuPDF and DOCX extraction with `python-docx`
- Document listing, extracted-text, download, and deletion endpoints
- Project-isolated upload directories
- Alembic migration `0002`
- React document workspace

## [0.1.0] - 2026-07-12

### Added

- FastAPI backend and React frontend foundations
- PostgreSQL with asynchronous SQLAlchemy
- Alembic migration `0001`
- User registration, Argon2 password hashing, and JWT authentication
- Protected project CRUD
- Docker Compose development environment
- Swagger documentation, backend tests, and linting
