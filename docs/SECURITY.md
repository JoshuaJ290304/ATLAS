# ATLAS Security Guide

## Implemented controls

- Argon2 password hashing
- strong-password validation for registration and reset
- JWT issuer, audience, expiry, unique token ID, password version, and session version
- backend project ownership and administrator authorization
- single-use hashed password-reset tokens
- persistent login, registration, and reset rate limits
- generic password-recovery response
- PDF/DOCX signature validation and DOCX decompression safeguards
- trusted-host and explicit CORS configuration
- security response headers
- production startup validation for secrets and debug/docs settings
- non-root backend container
- database-aware readiness checks

## Production requirements

- Generate unique JWT and database secrets.
- Use TLS through a reverse proxy.
- Set `ENVIRONMENT=production` and `ENABLE_API_DOCS=false`.
- Restrict `CORS_ORIGINS` and `TRUSTED_HOSTS` to deployed domains.
- Use a real SMTP service and do not expose Mailpit.
- Do not expose PostgreSQL, Ollama, or storage volumes publicly.
- Rotate any credential shared in screenshots, logs, source control, or chat.
- Back up PostgreSQL and file storage regularly.

## Token storage limitation

The browser currently stores the bearer access token in `localStorage`. This is appropriate for the current local/student deployment model but increases exposure if an XSS vulnerability is introduced. A future internet-facing deployment should move authentication to secure, HttpOnly, SameSite cookies with explicit CSRF protection.

## Reporting vulnerabilities

Do not include passwords, reset links, JWTs, `.env` contents, database dumps, or uploaded confidential documents in issue reports.
