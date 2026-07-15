#Requires -RunAsAdministrator
<#
.SYNOPSIS
  P0 Tailscale DNS health: set WLAN DNS to Quad9 + Cloudflare (keep MagicDNS via TS).
#>
$ErrorActionPreference = "Stop"
Write-Host "Setting WLAN DNS: 9.9.9.9, 1.1.1.1, 149.112.112.112" -ForegroundColor Cyan
netsh interface ip set dns name="WLAN" static 9.9.9.9 primary
netsh interface ip add dns name="WLAN" 1.1.1.1 index=2
netsh interface ip add dns name="WLAN" 149.112.112.112 index=3
Write-Host "Also try Ethernet if present..." -ForegroundColor Gray
try {
  netsh interface ip set dns name="Ethernet" static 9.9.9.9 primary 2>$null
  netsh interface ip add dns name="Ethernet" 1.1.1.1 index=2 2>$null
} catch {}
& "$env:ProgramFiles\Tailscale\tailscale.exe" set --accept-dns=true
Start-Sleep 2
& "$env:ProgramFiles\Tailscale\tailscale.exe" dns status
Write-Host ""
Write-Host "Admin console (global resolvers for whole tailnet):" -ForegroundColor Yellow
Write-Host "  https://login.tailscale.com/admin/dns"
Write-Host "  Add Global nameservers: 9.9.9.9 and 1.1.1.1 (Override local DNS optional)"
Write-Host "Done." -ForegroundColor Green
