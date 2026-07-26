# ATLAS Administrator Guide

## Access

Only users with the `admin` role can access `/admin` or any `/api/v1/admin/*` endpoint. Backend authorization remains authoritative even when frontend routes are hidden.

## Existing users

The user directory reads the existing `users` table. It shows real identities, roles, account status, registration/last-login dates, owned projects, and artifact totals. Password hashes and reset-token hashes are never returned.

## User operations

Administrators can:

- promote or demote users
- suspend or reactivate accounts
- invalidate all sessions
- trigger password recovery
- inspect user-owned projects and recent security activity

ATLAS prevents suspension or demotion of the final active administrator.

## Project oversight

Administrators can search all projects, archive or restore them, and transfer ownership to another active existing user. Ownership transfers require a reason and are written to the platform audit log.

## Audit log

The platform audit log records authentication and administrative events. Use filters for action, severity, user, and text search. Export is available as JSON or CSV.

## System health

The System Health page reports application version, database connectivity, Alembic revision, AI/SMTP reachability, storage usage, failed documents, and AI-index status. It never displays secrets.

## Platform settings

Administrators can control registration, maintenance mode, AI generation, session duration, reset expiry, upload size, and allowed document extensions. JWT, database, and SMTP credentials remain environment-only settings.

## Suspension and sessions

Suspending a user or explicitly invalidating sessions increments the account's session version. Previously issued access tokens then fail authentication immediately.
