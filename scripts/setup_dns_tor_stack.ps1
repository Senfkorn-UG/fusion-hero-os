#Requires -Version 5.1
<#
.SYNOPSIS
  Fusion DNS stack: Clearnet + Tailscale MagicDNS + Tor (.onion DNSPort)
#>
$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "=== Fusion DNS + Tor stack ===" -ForegroundColor Cyan

# 1) Tor Browser if no tor.exe
python -c "from fusion_hero_os.core.dns_tor_stack import find_tor_exe; print(find_tor_exe() or '')" | Tee-Object -Variable torExe | Out-Null
$torExe = (python -c "from fusion_hero_os.core.dns_tor_stack import find_tor_exe; print(find_tor_exe() or '')").Trim()
if (-not $torExe) {
    Write-Host "Installing Tor Browser (tor.exe) via winget..." -ForegroundColor Yellow
    winget install --id TorProject.TorBrowser -e --accept-package-agreements --accept-source-agreements
}

# 2) Ensure torrc
$torDir = Join-Path $env:USERPROFILE ".fusion\tor"
New-Item -ItemType Directory -Force -Path $torDir,(Join-Path $torDir "data") | Out-Null
$torrc = Join-Path $torDir "torrc"
if (-not (Test-Path $torrc)) {
    Copy-Item (Join-Path $Root "dns_tor_stack.yaml") -ErrorAction SilentlyContinue
    @"
SocksPort 127.0.0.1:9050
DNSPort 127.0.0.1:5354
ControlPort 127.0.0.1:9051
CookieAuthentication 1
AutomapHostsOnResolve 1
AutomapHostsSuffixes .onion,.exit
ClientOnly 1
AvoidDiskWrites 1
"@ | Set-Content -Encoding utf8 $torrc
}

# 3) Start Tor + report
python -m fusion_hero_os.core.dns_tor_stack --start-tor
python -m fusion_hero_os.core.dns_tor_stack --configure-tailscale

# 4) Start DNS proxy in background
$proxy = Start-Process -FilePath "python" -ArgumentList "-m","fusion_hero_os.core.dns_tor_stack","--serve" -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 2
python -m fusion_hero_os.core.dns_tor_stack --status
python -m fusion_hero_os.core.dns_tor_stack --resolve "quad9.net"
python -m fusion_hero_os.core.dns_tor_stack --resolve "example.onion"

Write-Host ""
Write-Host "Local DNS proxy: 127.0.0.1:5353" -ForegroundColor Green
Write-Host "  *.onion  -> Tor DNSPort 127.0.0.1:5354" -ForegroundColor Gray
Write-Host "  clearnet -> Quad9 / Cloudflare" -ForegroundColor Gray
Write-Host "  *.ts.net -> Tailscale MagicDNS (accept-dns)" -ForegroundColor Gray
Write-Host "SOCKS5 Tor: 127.0.0.1:9050 (apps that speak Tor/SOCKS)" -ForegroundColor Green
Write-Host "Proxy PID: $($proxy.Id)" -ForegroundColor Cyan
Write-Host "Docs: docs/mesh/DNS_TOR_STACK.md" -ForegroundColor Cyan
