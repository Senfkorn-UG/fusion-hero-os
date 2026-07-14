# operationalize.ps1 - Repo operationalisieren (lokale Config, CI-Gates, Follow-ups)
param(
    [switch]$SkipFollowup,
    [switch]$DeployDocs
)
$ErrorActionPreference = "SilentlyContinue"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Root = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$LocalPaths = Join-Path $PSScriptRoot "paths.local.json"
$ExamplePaths = Join-Path $PSScriptRoot "paths.local.example.json"
$DocsUrl = "https://95guknow.github.io/fusion-hero-os/"

Write-Host "=== Fusion Hero OS - Operationalize ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/5] Lokale Pfade (paths.local.json)" -ForegroundColor Yellow
if (-not (Test-Path $LocalPaths)) {
    if (Test-Path $ExamplePaths) {
        Copy-Item $ExamplePaths $LocalPaths
        Write-Host "  Erstellt: $LocalPaths (bitte echte Mesh-Werte eintragen)" -ForegroundColor Yellow
    } else {
        Write-Host "  Fehlt: paths.local.example.json" -ForegroundColor Red
    }
} else {
    Write-Host "  OK: paths.local.json vorhanden" -ForegroundColor Green
}

Write-Host "[2/5] Pfade aufloesen" -ForegroundColor Yellow
$Python = "C:\Users\Admin\venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
& $Python (Join-Path $PSScriptRoot "resolve_paths.py") *> $null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  resolve_paths.py OK" -ForegroundColor Green
} else {
    Write-Host "  resolve_paths.py fehlgeschlagen" -ForegroundColor Red
}

Write-Host "[3/5] GitHub Pages + Docs-Deploy" -ForegroundColor Yellow
if ($DeployDocs) {
    gh workflow run deploy-docs.yml --repo 95guknow/fusion-hero-os 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  deploy-docs.yml Workflow gestartet" -ForegroundColor Green
    } else {
        Write-Host "  deploy-docs manuell: gh workflow run deploy-docs.yml" -ForegroundColor DarkGray
    }
} else {
    Write-Host "  Uebersprungen (-DeployDocs fuer MkDocs-Push)" -ForegroundColor DarkGray
}

Write-Host "[4/5] Bottom-Up Sync-Check" -ForegroundColor Yellow
$winHead = (git -C $Root rev-parse HEAD 2>$null)
$originHead = (git -C $Root rev-parse origin/main 2>$null)
if ($winHead -and $originHead) {
    if ($winHead -eq $originHead) {
        Write-Host "  Sync OK: $($winHead.Substring(0,7))" -ForegroundColor Green
    } else {
        Write-Host "  Drift: local=$($winHead.Substring(0,7)) origin=$($originHead.Substring(0,7))" -ForegroundColor Yellow
        & (Join-Path $PSScriptRoot "merge-bottom-up.ps1")
    }
}

Write-Host "[5/5] Follow-up All-in-One" -ForegroundColor Yellow
if (-not $SkipFollowup) {
    & (Join-Path $PSScriptRoot "followup-all.ps1")
} else {
    Write-Host "  Uebersprungen (-SkipFollowup)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=== Operationalize abgeschlossen ===" -ForegroundColor Green
Write-Host "Docs: $DocsUrl" -ForegroundColor DarkGray
