# ATLAS Milestone 3 — Requirement Intelligence

## Implemented

- Deterministic requirement candidate detection from extracted PDF/DOCX text
- Functional and non-functional classification
- Non-functional categories such as security, performance, usability and availability
- Confidence scoring for automatically extracted requirements
- Ambiguity detection with human-readable flags and a 0–100 score
- PostgreSQL `requirements` table and Alembic migration `0003`
- Automatic extraction with duplicate prevention and optional replacement
- Manual requirement creation
- Requirement list, summary, read, update and delete endpoints
- Editable requirement type, category, status, title and description
- Version counter incremented after each edit
- Project ownership checks across all requirement endpoints
- React requirement intelligence workspace

## Deliberate design decision

Milestone 3 uses deterministic rules rather than an LLM. This provides reproducible results,
keeps the local Docker stack lightweight, and allows reviewers to see exactly why a statement
was classified or marked ambiguous. A later milestone can compare these baseline results with
Ollama-based extraction.

## Acceptance checks

1. Upload an SRS with requirement statements containing words such as `shall` or `must`.
2. Open the project's Requirements workspace.
3. Select the extracted source document and run extraction.
4. Confirm functional/non-functional classifications and ambiguity flags.
5. Edit one requirement and confirm its version increases.
6. Create a manual requirement.
7. Refresh and restart containers to verify persistence.
8. Delete a requirement and confirm it disappears.
