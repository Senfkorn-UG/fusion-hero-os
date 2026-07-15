# Tailscale Installation + Mesh Setup for Fusion Hero OS (Windows)
# Run as Administrator in PowerShell

$ErrorActionPreference = "Stop"

Write-Host "[Fusion Hero OS] Tailscale Windows Mesh Setup" -ForegroundColor Cyan

$tsPath = "C:\Program Files\Tailscale\tailscale.exe"
if (-not (Test-Path $tsPath)) {
    Write-Host "Tailscale not found. Install: winget install tailscale.tailscale" -ForegroundColor Yellow
    exit 1
}

Write-Host "Tailscale found at $tsPath" -ForegroundColor Green

if (-not $env:TS_AUTHKEY) {
    Write-Host "Set TS_AUTHKEY first (reusable key from login.tailscale.com/admin/settings/keys):" -ForegroundColor Yellow
    Write-Host '  $env:TS_AUTHKEY="tskey-auth-..."' -ForegroundColor Yellow
    exit 1
}

Write-Host "Running tailscale up --reset ..." -ForegroundColor Green

$upArgs = @(
    "up",
    "--reset",
    "--auth-key=$env:TS_AUTHKEY",
    "--hostname=mainframe",
    "--accept-routes",
    "--unattended"
)

& $tsPath @upArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "tailscale up failed (exit $LASTEXITCODE)." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Tailscale configured." -ForegroundColor Green
& $tsPath status
Write-Host ""
Write-Host "Optional (after tagOwners in ACL): tailscale up --advertise-tags=tag:fusion-node-desktop --advertise-exit-node" -ForegroundColor DarkGray
Write-Host "Next: .\tailscale-account-check.ps1" -ForegroundColor DarkGray
