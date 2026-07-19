# Milestone 6 Implementation Notes

## Goal

Add a project-isolated AI assistant that retrieves evidence from ATLAS records and generates source-grounded answers through a local Ollama model.

## Completed work

- Added migration `0006`.
- Added `knowledge_chunks`, `assistant_indexes`, `assistant_conversations`, and `assistant_messages`.
- Indexed extracted documents, requirements, artifacts, and impact reports.
- Added configurable chunk size and overlap.
- Added Sentence Transformer document/query embeddings.
- Added persistent ChromaDB vector storage filtered by project ID.
- Added Ollama status checking and grounded chat generation.
- Added retrieval-only fallback for unavailable Ollama.
- Added persistent conversations and citation metadata.
- Added index build, clear, semantic search, chat, history, and delete endpoints.
- Added the React AI Assistant page.
- Added optional Ollama Docker profile and persistent model/vector mounts.
- Updated version, README, changelog, environment example, and Git exclusions.

## Design decisions

1. ChromaDB runs as an embedded persistent client to avoid an additional mandatory service.
2. Ollama is optional at runtime; semantic retrieval remains usable through fallback mode.
3. Embeddings are generated locally with `sentence-transformers/all-MiniLM-L6-v2`.
4. Retrieval is always filtered by project ID.
5. The assistant prompt forbids unsupported claims and requests numbered citations.
6. PostgreSQL stores chunk metadata and conversation history; ChromaDB stores vectors.
7. The optional Docker Ollama service is behind the `ai` profile so normal startup remains lightweight.

## Verification

- Ruff: passed
- Pytest: 29 tests passed
- Frontend: production build passed, 89 modules transformed
- Alembic: `0005 → 0006` offline SQL generated successfully
- Assistant router: 8 operations registered
- SQLAlchemy mapper configuration: passed

## Manual acceptance checks

- Build index from a project with extracted content.
- Confirm source and chunk counts.
- Run semantic search and inspect relevance-ranked sources.
- Ask a question with Ollama running and verify numbered citations.
- Stop Ollama and verify retrieval fallback.
- Continue an existing conversation.
- Restart Docker and verify index and conversation persistence.
- Clear the index and verify search/chat are blocked until rebuilt.
- Delete a conversation and verify it disappears.

## Known limitations

- PDF chunks do not yet preserve exact page coordinates.
- First-run model download can be slow.
- Indexing is synchronous.
- Source changes require a manual index rebuild.
- OCR and source-code indexing are not included.
