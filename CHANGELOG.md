# Changelog

All notable changes to ATLAS are documented here. The project follows Semantic Versioning.

## [Unreleased]

### Planned

- Project analytics and health dashboard
- Exportable final reports
- Deployment and final-release preparation

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
- Ollama/model availability reporting
- Retrieval-only fallback when Ollama is unavailable
- React AI Assistant workspace with chat and semantic-search modes
- Optional Ollama Docker Compose profile
- Persistent model and vector-storage mounts
- Alembic migration `0006`

### Changed

- Project cards now include an AI Assistant action.
- Dashboard milestone status updated to Milestone 6.
- API application version updated to `0.6.0`.
- README and environment documentation now include Ollama, ChromaDB, and embedding setup.

### Verified

- Chunking and normalization behavior
- Index source generation for all four project source types
- Grounded prompt construction and numbered citations
- Retrieval-only fallback behavior
- 29 backend tests
- Ruff checks
- Frontend production build with 89 transformed modules
- Alembic `0005 → 0006` SQL generation
- Eight assistant API operations registered

### Limitations

- Exact PDF page-level citations are not yet available.
- The first embedding run downloads the configured Sentence Transformer model.
- Indexing is synchronous and designed for student-scale projects.
- The project index must be rebuilt after source records change.

## [0.5.0] - 2026-07-13

### Added

- Persisted requirement-version snapshots
- Requirement version list and comparison endpoints
- Deterministic requirement change detection
- Directly and transitively affected artifact discovery
- Reproducible risk scoring and impact severity
- Explainable risk-factor breakdown
- Stored change summaries and impact-analysis history
- React impact-analysis workspace
- Alembic migration `0005`

### Changed

- Project-card actions use a responsive layout.
- Traceability summary displays rejected-link count.

## [0.4.0] - 2026-07-13

### Added

- Software artifact management
- Manual and suggested requirement-to-artifact links
- Confidence scoring and accept/reject workflow
- Traceability matrix and coverage metrics
- Alembic migration `0004`
- React traceability workspace

## [0.3.0] - 2026-07-13

### Added

- Requirement extraction and functional/non-functional classification
- Confidence scores and ambiguity detection
- Manual requirement creation, editing, status, and version increments
- Alembic migration `0003`
- React requirement workspace

## [0.2.0] - 2026-07-12

### Added

- Project-scoped PDF and DOCX uploads
- File validation, checksums, metadata, and text extraction
- Document list, text, download, and deletion endpoints
- Alembic migration `0002`
- React document workspace

## [0.1.0] - 2026-07-12

### Added

- FastAPI and React foundations
- PostgreSQL with asynchronous SQLAlchemy
- Alembic migration `0001`
- Registration, Argon2 password hashing, and JWT authentication
- Protected project CRUD
- Docker Compose environment
