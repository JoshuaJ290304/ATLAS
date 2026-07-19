$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$stagePattern = ("MILE" + "STONE_*.md")

$legacyFiles = @(
    Get-ChildItem -LiteralPath $projectRoot -File -Filter $stagePattern
    Get-ChildItem -LiteralPath $projectRoot -File -Filter "PATCH_MANIFEST.md"
)

if (-not $legacyFiles) {
    Write-Host "No legacy development-stage note files were found." -ForegroundColor Green
    exit 0
}

$legacyFiles | Sort-Object FullName -Unique | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Force
    Write-Host "Removed $($_.Name)" -ForegroundColor Yellow
}

Write-Host "Legacy notes removed. Release documentation is available in README.md, CHANGELOG.md, and docs/." -ForegroundColor Green
