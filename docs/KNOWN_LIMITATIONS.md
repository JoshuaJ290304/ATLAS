# Known Limitations

- Scanned PDFs are not processed because OCR is not implemented.
- PDF citations do not include exact page coordinates.
- AI generation depends on local model availability and must be verified against cited evidence.
- Indexing, extraction, and analytics are synchronous and aimed at student/small-team project sizes.
- HTML is the native printable report format; server-generated PDF is not implemented.
- Bearer tokens are stored in browser `localStorage`; secure cookie authentication is recommended for a public internet deployment.
- Rate limiting is persistent and shared through PostgreSQL, but it is not a replacement for reverse-proxy or network-level abuse protection.
- Mailpit is for local development only.
- The default Docker Compose file exposes development ports and should sit behind a TLS reverse proxy for deployment.
