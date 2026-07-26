[CmdletBinding()]
param(
    [string]$ExpectedRevision = "0013"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-LastExitCode([string]$Message) {
    if ($LASTEXITCODE -ne 0) {
        throw $Message
    }
}

Write-Host "ATLAS release verification" -ForegroundColor Cyan

docker compose ps
Assert-LastExitCode "Docker Compose service check failed."

$currentRevision = (docker compose exec -T backend alembic current 2>&1 | Out-String).Trim()
Assert-LastExitCode "Alembic revision check failed."
if ($currentRevision -notmatch [regex]::Escape($ExpectedRevision)) {
    throw "Expected Alembic revision $ExpectedRevision, received: $currentRevision"
}
Write-Host "Alembic: $currentRevision" -ForegroundColor Green

docker compose exec -T backend pytest -q
Assert-LastExitCode "Backend tests failed."

docker compose exec -T backend ruff check .
Assert-LastExitCode "Backend Ruff checks failed."

docker compose build frontend
Assert-LastExitCode "Frontend production build failed."

docker compose up -d frontend
Assert-LastExitCode "Frontend restart failed."

docker compose exec -T frontend nginx -t
Assert-LastExitCode "Frontend Nginx validation failed."

$checks = @(
    "http://localhost:5173/healthz",
    "http://localhost:8000/api/v1/health/live",
    "http://localhost:8000/api/v1/health/ready"
)

foreach ($url in $checks) {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    if ($response.StatusCode -ne 200) {
        throw "$url returned HTTP $($response.StatusCode)."
    }
    Write-Host "$url -> HTTP 200" -ForegroundColor Green
}

Write-Host "ATLAS release verification passed." -ForegroundColor Green
