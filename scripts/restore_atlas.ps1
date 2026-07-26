[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$DatabaseDump,

    [Parameter(Mandatory = $true)]
    [ValidateSet("RESTORE")]
    [string]$Confirm
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$dumpPath = (Resolve-Path $DatabaseDump).Path
$postgresContainer = (docker compose ps -q postgres).Trim()
if (-not $postgresContainer) {
    throw "The PostgreSQL container is not running."
}

Write-Warning "This operation replaces the current ATLAS database."
Write-Host "Stopping application services..." -ForegroundColor Yellow
docker compose stop backend frontend
if ($LASTEXITCODE -ne 0) { throw "Could not stop application services." }

docker cp $dumpPath "${postgresContainer}:/tmp/atlas-restore.dump"
if ($LASTEXITCODE -ne 0) { throw "Could not copy the restore file." }

docker exec $postgresContainer sh -lc 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner /tmp/atlas-restore.dump'
if ($LASTEXITCODE -ne 0) { throw "PostgreSQL restore failed." }

docker exec $postgresContainer rm -f /tmp/atlas-restore.dump | Out-Null

docker compose up -d backend frontend
if ($LASTEXITCODE -ne 0) { throw "Could not restart ATLAS." }

Write-Host "Database restore completed. Verify migration and application health." -ForegroundColor Green
