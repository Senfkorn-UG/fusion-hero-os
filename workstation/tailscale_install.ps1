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

$authKey = if ($env:TS_AUTHKEY) { $env:TS_AUTHKEY } else {
    "tskey-auth-kfffkrbmhF11CNTRL-srWw54orSqToi6yGMjfSqTFyk1PE6hsmT"
}

Write-Host "Running tailscale up --reset ..." -ForegroundColor Green

$upArgs = @(
    "up",
    "--reset",
    "--auth-key=$authKey",
    "--hostname=desktop-kpki9e4",
    "--accept-routes",
    "--unattended"
)

& $tsPath @upArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "tailscale up failed (exit $LASTEXITCODE)." -ForegroundColor Red
    Write-Host "Create a new reusable key: https://login.tailscale.com/admin/settings/keys" -ForegroundColor Yellow
    Write-Host 'Then: $env:TS_AUTHKEY="tskey-auth-..."; .\tailscale_install.ps1' -ForegroundColor Yellow
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Tailscale configured." -ForegroundColor Green
& $tsPath status
Write-Host ""
Write-Host "Optional (after tagOwners in ACL): tailscale up --advertise-tags=tag:fusion-node-desktop --advertise-exit-node" -ForegroundColor DarkGray
Write-Host "Next: .\tailscale-account-check.ps1" -ForegroundColor DarkGray
