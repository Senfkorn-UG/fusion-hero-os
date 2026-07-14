# Tailscale Installation + Mesh Setup for Fusion Hero OS (Windows)
# For the desktop node (grok-workstation)
# Run as Administrator in PowerShell

$ErrorActionPreference = "Stop"

Write-Host "🚀 [Fusion Hero OS] Tailscale Windows Mesh Setup" -ForegroundColor Cyan

# 1. Check if Tailscale is installed
$tsPath = "C:\Program Files\Tailscale\tailscale.exe"
if (-not (Test-Path $tsPath)) {
    Write-Host "→ Tailscale not found. Please download and install from https://tailscale.com/download" -ForegroundColor Yellow
    Write-Host "   Or use: winget install tailscale.tailscale" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Tailscale found at $tsPath"

# 2. Configure with pre-auth key + Fusion settings
# Matches mesh_connectors.yaml for 'desktop' node
Write-Host ""
Write-Host "🔐 Running tailscale up with auth key and mesh parameters..." -ForegroundColor Green
Write-Host "   hostname: desktop-kpki9e4"
Write-Host "   tag:      tag:fusion-node-desktop"
Write-Host "   advertise-exit-node, accept-routes"

& $tsPath up `
    --auth-key=tskey-auth-kfffkrbmhF11CNTRL-srWw54orSqToi6yGMjfSqTFyk1PE6hsmT `
    --hostname=desktop-kpki9e4 `
    --advertise-tags=tag:fusion-node-desktop `
    --advertise-exit-node `
    --accept-routes `
    --unattended

Write-Host ""
Write-Host "✅ Tailscale configured."

# 3. Status
Write-Host ""
Write-Host "📡 Current Tailscale status:" -ForegroundColor Cyan
& $tsPath status

Write-Host ""
Write-Host "✅ Install / config complete for Fusion Hero OS desktop node."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  .\tailscale-account-check.ps1"
Write-Host "  Run mesh registry or start services"
Write-Host ""
Write-Host "To use this node as exit node from other devices:"
Write-Host "  tailscale up --exit-node=100.64.104.58 --exit-node-allow-lan-access"
Write-Host ""
Write-Host "⚠️  The auth key is one-time / time-limited. Regenerate in Tailscale admin if needed." -ForegroundColor Yellow