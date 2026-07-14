# Tailscale Installation + Mesh Setup for Fusion Hero OS (Windows)
# For the desktop node (grok-workstation)
# Run as Administrator in PowerShell

$ErrorActionPreference = "Stop"

Write-Host "[Fusion Hero OS] Tailscale Windows Mesh Setup" -ForegroundColor Cyan

$tsPath = "C:\Program Files\Tailscale\tailscale.exe"
if (-not (Test-Path $tsPath)) {
    Write-Host "Tailscale not found. Install via: winget install tailscale.tailscale" -ForegroundColor Yellow
    Write-Host "Or download: https://tailscale.com/download" -ForegroundColor Yellow
    exit 1
}

Write-Host "Tailscale found at $tsPath" -ForegroundColor Green

$authKey = if ($env:TS_AUTHKEY) { $env:TS_AUTHKEY } else {
    "tskey-auth-kfffkrbmhF11CNTRL-srWw54orSqToi6yGMjfSqTFyk1PE6hsmT"
}

Write-Host ""
Write-Host "Running tailscale up (hostname=desktop-kpki9e4, tag=fusion-node-desktop)..." -ForegroundColor Green

$upArgs = @(
    "up",
    "--auth-key=$authKey",
    "--hostname=desktop-kpki9e4",
    "--advertise-tags=tag:fusion-node-desktop",
    "--advertise-exit-node",
    "--accept-routes",
    "--unattended"
)

& $tsPath @upArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "tailscale up failed (exit $LASTEXITCODE). Auth key may be expired - regenerate at login.tailscale.com/admin/settings/keys" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Tailscale configured." -ForegroundColor Green
Write-Host ""
Write-Host "Current Tailscale status:" -ForegroundColor Cyan
& $tsPath status

Write-Host ""
Write-Host "Install / config complete for Fusion Hero OS desktop node." -ForegroundColor Green
Write-Host "Next: .\tailscale-account-check.ps1" -ForegroundColor DarkGray
