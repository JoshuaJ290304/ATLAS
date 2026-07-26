## [0.11.0-dev] — Administration and Platform Operations

### Added
- Administrator-only FastAPI authorization dependency and protected React routes.
- Live management of all existing user records, including real project, document, requirement, test-case, and release-candidate totals.
- User role changes, suspension/reactivation, session invalidation, and administrator-triggered password recovery.
- Safeguards preventing demotion or suspension of the final active administrator.
- Platform-wide project oversight with archive, restore, and audited ownership transfer.
- Platform audit records for registration, login success/failure, password recovery, roles, sessions, projects, and settings.
- CSV and JSON audit exports.
- System health for database, Alembic, backend, Ollama, SMTP, AI indexes, storage, and failed documents.
- Persisted operational settings for registration, maintenance mode, AI operations, session duration, password-reset expiry, and document upload policy.
- Alembic revision `0012` preserving every existing user ID, password hash, role, project, and ownership relationship.
- Responsive administration dashboard, user directory, user detail, project oversight, audit, system, and settings pages.

### Security
- Session-version claims invalidate all issued tokens after suspension, role-sensitive changes, password reset, or an explicit administrator action.
- Normal users receive HTTP 403 on all administrator endpoints.
- Password hashes, reset-token hashes, JWT secrets, SMTP credentials, and database credentials are never returned by admin APIs.

### Development status
- Version remains `0.11.0-dev` until migration, backend tests, frontend build, and complete admin smoke testing pass.

## [0.10.0] — Release Readiness and Quality Gates

### Added
- Release-candidate management with baseline, requirement, and test-case selection.
- Configurable release thresholds for traceability, approved test coverage, high-risk impacts, and overdue reviews.
- Ten explainable quality gates with weighted readiness scoring.
- Ready, At Risk, Blocked, and Not Evaluated classifications.
- Release submission, sign-off, rejection, publication lock, and immutable release snapshots.
- Release comparison plus JSON and CSV readiness reports.
- Alembic revision `0010` and focused backend readiness tests.
- Responsive Release Readiness workspace aligned with the ATLAS project design system.

### Development status
- Version remains `0.10.0` until migration, backend tests, frontend build, and browser smoke tests pass.

## [0.9.0] — Test Case Intelligence

### Added
- Test case, test step, and test case version models.
- Requirement-to-test traceability and coverage summary.
- Manual authoring and AI-assisted scenario generation.
- Review status, priority, reviewer notes, and rejection validation.
- Responsive Test Case Intelligence workspace with search and filters.
- Alembic revision 0009 and backend schema tests.

# Changelog

## 0.8.1 — Governance Input Completeness

### Added

- Added review priority (`Low`, `Medium`, `High`, and `Critical`).
- Added optional review due dates with client-side past-date validation.
- Added explicit approved-requirement selection when creating a baseline.
- Added baseline status (`Active` or `Archived`).
- Added baseline-to-baseline comparison in addition to baseline-to-current comparison.
- Added audit entries for baseline comparisons.
- Expanded audit details to show review context, priority, due date, comments, decision reasons, baseline status, and requirement counts.
- Added Alembic migration `0008_expand_governance_fields.py`.

### Changed

- Baseline creation now validates that every selected requirement belongs to the project and is approved.
- Review cards now display priority and due date.
- Baseline cards now display their governance status.
- Updated application and frontend versions to `0.8.1`.

### Verified

- Frontend production build completed successfully.
- Governance backend tests passed, including the new review and baseline input schemas.
- Python syntax compilation passed for the updated backend and migration files.

## 0.8.0 — Requirement Governance and Baselines

- Added a dedicated Reviews & Baselines workspace.
- Added requirement review requests, reviewer assignment, approval and rejection decisions.
- Added requirement discussion comments with user and timestamp attribution.
- Added immutable baselines containing approved requirement snapshots.
- Added baseline-to-current comparison for added, modified, removed, and unchanged requirements.
- Added project governance audit history.
- Added backend migration `0007_create_governance_workflow.py`.
- Moved dashboard summary cards into the right side of the project command centre header.
- Added the governance module to project navigation and project action cards.
- Updated the professional footer attribution to retain “Developed by Joshua J”.
- Added automated cleanup for the legacy milestone-seven QA demo label.
- Updated the application release to 0.8.0.

All notable changes to ATLAS are documented here. The project follows Semantic Versioning.

## [Unreleased]

### Planned

- Final deployment hardening
- Optional OCR for scanned PDFs
- Background indexing for larger projects

## [0.7.0] - 2026-07-13

### Added

- Live project analytics aggregation endpoint
- Explainable 100-point project-health score
- Health factors for document readiness, requirement quality, traceability, artifact inventory, impact discipline, and AI-index readiness
- Requirement type, status, and non-functional-category distributions
- Artifact-type distribution
- Accepted, suggested, and rejected trace-link analytics
- Requirement and artifact coverage analytics
- Impact-risk and severity distribution
- Assistant index, conversation, and message statistics
- Recent project activity feed
- Downloadable HTML project-health report
- CSV analytics export
- JSON analytics export
- React analytics and reporting workspace
- Reusable project navigation, icons, alerts, loading states, statistics, progress bars, and empty states
- Shared frontend form-validation utilities
- Shared backend string normalization and password-strength validation
- Duplicate project-name and artifact-name protection
- New analytics and validation tests

### Changed

- Complete visual refresh for authentication, dashboard, project navigation, cards, forms, tables, buttons, alerts, and responsive layouts
- Project cards now expose all six modules in a stable responsive grid
- All project workspaces share a consistent navigation bar
- Registration now requires uppercase, lowercase, and numeric password characters
- Project, requirement, artifact, assistant, impact, and upload forms provide clearer client-side errors
- Pydantic schemas trim whitespace and reject blank-only text
- Non-functional requirements require a category
- API and user-interface version updated to `0.7.0`
- README expanded with analytics, reporting, design, validation, and release guidance

### Verified

- 36 backend tests passing
- Ruff checks passing
- Frontend production build successful with 94 transformed modules
- Analytics JSON, CSV, and HTML export generation
- Project health scoring at complete, partial, and empty states
- Existing Milestone 1–6 routes remain registered
- No database migration required because analytics are calculated from live project data

### Limitations

- The HTML report is a standalone downloadable report rather than a PDF.
- Analytics are calculated on request and are designed for student-scale projects.
- Exact PDF page-level citations and OCR remain future enhancements.

## [0.6.0] - 2026-07-13

### Added

- Project-isolated knowledge indexing
- Deterministic chunking with configurable overlap
- Sentence Transformer document and query embeddings
- Persistent ChromaDB vector storage
- Semantic search across documents, requirements, artifacts, and impact reports
- Ollama-based Retrieval-Augmented Generation
- Numbered source citations in assistant answers
- Persistent assistant conversations and messages
- Index status, rebuild, and clear operations
- Retrieval-only fallback when Ollama is unavailable
- Alembic migration `0006`

## [0.5.0] - 2026-07-13

### Added

- Persisted requirement-version snapshots
- Requirement version comparison
- Direct and transitive affected-artifact discovery
- Reproducible risk scoring and impact severity
- Persistent impact reports
- Alembic migration `0005`

## [0.4.0] - 2026-07-13

### Added

- Software artifact management
- Manual and suggested requirement-to-artifact links
- Confidence scoring and accept/reject workflow
- Traceability matrix and coverage metrics
- Alembic migration `0004`

## [0.3.0] - 2026-07-13

### Added

- Requirement extraction and functional/non-functional classification
- Confidence scores and ambiguity detection
- Manual requirement creation, editing, status, and version increments
- Alembic migration `0003`

## [0.2.0] - 2026-07-12

### Added

- Project-scoped PDF and DOCX uploads
- File validation, checksums, metadata, and text extraction
- Alembic migration `0002`

## [0.1.0] - 2026-07-12

### Added

- FastAPI and React foundations
- PostgreSQL with asynchronous SQLAlchemy
- Registration, Argon2 password hashing, and JWT authentication
- Protected project CRUD
- Docker Compose environment
- Alembic migration `0001`



