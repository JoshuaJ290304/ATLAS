$ErrorActionPreference = "Stop"

$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $PatchRoot
$PageTarget = Join-Path $ProjectRoot "frontend\src\pages\TestCasesPage.jsx"
$CssTarget = Join-Path $ProjectRoot "frontend\src\index.css"
$PageSource = Join-Path $PatchRoot "frontend\src\pages\TestCasesPage.jsx"
$CssSource = Join-Path $PatchRoot "test-cases-header-fix.css"
$BackupRoot = Join-Path $ProjectRoot ("backups\test-cases-header-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
$Marker = "/* ATLAS 0.9.0 — Test Cases header alignment fix */"

Write-Host "[1/5] Validating ATLAS project..." -ForegroundColor Cyan
if (-not (Test-Path $PageTarget) -or -not (Test-Path $CssTarget)) {
    throw "TestCasesPage.jsx or frontend/src/index.css was not found. Extract this folder directly inside the ATLAS project root."
}

Write-Host "[2/5] Backing up current Test Cases UI..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force $BackupRoot | Out-Null
Copy-Item $PageTarget (Join-Path $BackupRoot "TestCasesPage.jsx") -Force
Copy-Item $CssTarget (Join-Path $BackupRoot "index.css") -Force

Write-Host "[3/5] Moving Test Case metrics into the project header..." -ForegroundColor Cyan
Copy-Item $PageSource $PageTarget -Force

$css = Get-Content $CssTarget -Raw
if ($css.Contains($Marker)) {
    $css = $css.Substring(0, $css.IndexOf($Marker)).TrimEnd() + "`r`n"
}
$fixCss = Get-Content $CssSource -Raw
Set-Content -Path $CssTarget -Value ($css + "`r`n`r`n" + $fixCss) -Encoding UTF8

Write-Host "[4/5] Rebuilding frontend..." -ForegroundColor Cyan
docker compose build frontend
if ($LASTEXITCODE -ne 0) {
    throw "Frontend build failed. Original files are available in $BackupRoot"
}

docker compose up -d frontend
if ($LASTEXITCODE -ne 0) {
    throw "Frontend restart failed."
}

Write-Host "[5/5] Test Cases header aligned successfully." -ForegroundColor Green
Write-Host "Backup: $BackupRoot"
Write-Host "Open http://localhost:5173 and press Ctrl+F5."
