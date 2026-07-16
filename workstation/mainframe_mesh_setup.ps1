# mainframe_mesh_setup.ps1 — Fractal mainframe save + virtual exit node setup (Windows)
param(
    [string]$ExitProfile = "direct",
    [switch]$ApplyExit,
    [switch]$DryRun,
    [switch]$Replicate
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$Py = Join-Path $RepoRoot "fractal_mainframe_mesh.py"

if (-not (Test-Path $Py)) {
    Write-Error "fractal_mainframe_mesh.py not found at $Py"
}

Write-Host "=== Fusion Hero OS — Mainframe Mesh Setup ===" -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot"
Write-Host "Exit profile: $ExitProfile"

$args = @("setup", "--exit", $ExitProfile)
if ($ApplyExit) { $args += "--apply-exit" }
if ($DryRun) { $args += "--dry-run" }

python $Py @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($Replicate) {
    Write-Host "`n-> Replicating fractal manifest to mesh peers..." -ForegroundColor Yellow
    python $Py save --replicate
}

Write-Host "`n-> Fractal status:" -ForegroundColor Green
python $Py status

Write-Host "`nDone. Manifest: $env:USERPROFILE\.fusion\mesh\fractal\manifest.json" -ForegroundColor Green