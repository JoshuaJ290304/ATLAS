# ATLAS Milestone 6 Patch Manifest

Apply this ZIP at the repository root while on:

```text
feature/milestone-6-ai-project-assistant
```

The patch contains Milestone 6 source, migration, tests, Docker/environment additions, and completed `v0.6.0` documentation.

It does not replace:

- `.env`
- `frontend/Dockerfile`
- `frontend/package-lock.json`
- uploaded project files
- PostgreSQL data
- existing vector/model cache contents

After extraction, rebuild the backend so the new Python dependencies are installed and Alembic applies migration `0006`.

For full generated answers, install/start Ollama and pull the configured model. Semantic retrieval fallback remains available when Ollama is offline.
