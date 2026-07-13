# ATLAS Milestone 4 — Traceability Engine

## Implemented

- Software artifact register for APIs, database tables, test cases, and UML components.
- Project-scoped artifact CRUD with stable `ART-0001` style codes.
- Manual requirement-to-artifact trace links.
- Explainable system suggestions using token overlap, artifact-name evidence, and artifact-type cues.
- Link types: implements, stores, verifies, represents, and relates-to.
- Suggested, accepted, and rejected review states.
- Requirement and artifact coverage metrics based on accepted links only.
- Traceability matrix response for the React workspace.
- PostgreSQL migration `0004` with cascade-safe ownership relationships.
- Pure unit tests for scoring, link inference, and coverage calculations.

## Design decisions

- Suggestions are deterministic in this milestone so every confidence score can be explained in the viva.
- Suggested links do not count as coverage until a user accepts them.
- Rejected links are retained as review history and are not recreated by default.
- One requirement/artifact pair can have one current trace link, preventing duplicate matrix cells.
- A later semantic-embedding implementation can replace the scorer without changing the trace-link schema.

## Local acceptance flow

1. Create at least one API, database table, test case, and UML component.
2. Generate suggestions with a minimum confidence of 0.30.
3. Accept a correct suggestion and reject an incorrect one.
4. Create one manual link.
5. Confirm requirement and artifact coverage update only for accepted/manual links.
6. Confirm the matrix shows suggested, accepted, and rejected states.
7. Refresh and restart Docker to verify persistence.
8. Delete an artifact and confirm its trace links disappear through database cascade rules.
