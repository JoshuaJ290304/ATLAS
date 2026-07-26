[CmdletBinding()]
param(
    [string]$DestinationRoot = ".\backups"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupRoot = Join-Path (Resolve-Path ".").Path (Join-Path $DestinationRoot $timestamp)
New-Item -ItemType Directory -Force $backupRoot | Out-Null

$postgresContainer = (docker compose ps -q postgres).Trim()
if (-not $postgresContainer) {
    throw "The PostgreSQL container is not running."
}

Write-Host "Creating PostgreSQL backup..." -ForegroundColor Yellow
docker exec $postgresContainer sh -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/atlas-backup.dump'
if ($LASTEXITCODE -ne 0) { throw "PostgreSQL backup failed." }

docker cp "${postgresContainer}:/tmp/atlas-backup.dump" (Join-Path $backupRoot "atlas.dump")
if ($LASTEXITCODE -ne 0) { throw "Copying the PostgreSQL backup failed." }
docker exec $postgresContainer rm -f /tmp/atlas-backup.dump | Out-Null

foreach ($directory in @("storage/uploads", "storage/vector")) {
    if (Test-Path $directory) {
        $name = (Split-Path $directory -Leaf) + ".zip"
        Compress-Archive -Path $directory -DestinationPath (Join-Path $backupRoot $name) -Force
    }
}

if (Test-Path ".env") {
    Copy-Item ".env" (Join-Path $backupRoot ".env") -Force
}

Get-FileHash (Join-Path $backupRoot "atlas.dump") -Algorithm SHA256 |
    Format-List Algorithm, Hash, Path

Write-Host "Backup created at $backupRoot" -ForegroundColor Green
Write-Warning "The backup may contain confidential data and secrets. Store it securely."
