# ATLAS User Guide

## End-to-end workflow

1. Register or sign in.
2. Create a project.
3. Upload a PDF or DOCX requirements document.
4. Extract and refine requirements.
5. Review requirements and create an approved baseline.
6. Create technical artifacts and traceability links.
7. analyze requirement changes and affected artifacts.
8. Create or generate test cases and approve them.
9. Build the AI knowledge index and ask evidence-grounded questions.
10. Review analytics and create a release candidate.
11. Evaluate quality gates and publish a ready release.

## Authentication

Use **Forgot password?** on the login page when access is lost. Reset links are single-use, expire, and invalidate existing sessions after a successful password change.

Login accepts valid existing passwords even when they were created before the current strong-password policy. New registrations and password resets require at least eight characters, one lowercase letter, one uppercase letter, and one number.

## Projects

The project dashboard provides direct access to:

- Documents
- Requirements
- Traceability
- Reviews & Baselines
- Impact Analysis
- Test Cases
- AI Assistant
- Analytics
- Release Readiness

Projects are owner-isolated. A normal user cannot access another user's project by changing the URL.

## Documents

Accepted formats are PDF and DOCX. ATLAS validates extension, binary signature, file size, DOCX archive integrity, compression ratio, and extracted-text limits.

## Reviews and baselines

Only approved requirements can be included in a baseline. Baselines preserve snapshots, making later comparisons independent of live requirement edits.

## Test cases

Test cases can be manual or AI-assisted. Link each test case to a requirement, add ordered steps and expected results, then use the review status to control approved coverage.

## Release readiness

A release candidate combines a baseline, requirements, and test cases. Quality gates explain readiness, blockers, warnings, and recommended corrections. A published release is locked to preserve its evidence snapshot.
