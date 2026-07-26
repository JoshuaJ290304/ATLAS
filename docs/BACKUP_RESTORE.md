# ATLAS Backup and Restore

## Back up PostgreSQL

```powershell
$backupDir = ".\backups\$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Force $backupDir | Out-Null
$postgres = (docker compose ps -q postgres).Trim()

docker exec $postgres sh -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/atlas.dump'
docker cp "${postgres}:/tmp/atlas.dump" "$backupDir\atlas.dump"
docker exec $postgres rm -f /tmp/atlas.dump
```

## Back up file data

```powershell
Compress-Archive -Path .\storage\uploads -DestinationPath "$backupDir\uploads.zip"
Compress-Archive -Path .\storage\vector -DestinationPath "$backupDir\vector.zip"
Copy-Item .\.env "$backupDir\.env" -Force
```

Protect the backup directory because `.env` contains secrets.

## Restore PostgreSQL

Restoration replaces current database contents. Stop application traffic and take a fresh backup first.

```powershell
docker compose stop backend
$postgres = (docker compose ps -q postgres).Trim()
docker cp ".\backups\YOUR_BACKUP\atlas.dump" "${postgres}:/tmp/atlas.dump"
docker exec $postgres sh -lc 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /tmp/atlas.dump'
docker exec $postgres rm -f /tmp/atlas.dump
docker compose up -d backend frontend
```

Verify:

```powershell
docker compose exec backend alembic current
Invoke-WebRequest http://localhost:8000/api/v1/health/ready -UseBasicParsing
```
