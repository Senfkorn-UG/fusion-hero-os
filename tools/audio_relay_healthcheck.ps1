<#
.SYNOPSIS
    Diagnose fuer den Bluetooth-Audio-Relay-Link mainframe <-> phone-node
    (siehe ascension_os/config/access_policy.json, service "bluetooth-audio-relay").

.DESCRIPTION
    Rein lesend / diagnostisch. Aendert KEINE System- oder Firewall-Einstellungen.
    Meldet nur, was zu tun ist, falls etwas nicht passt (z. B. "Set-NetConnectionProfile ..."
    wird nur ausgegeben, nicht ausgefuehrt).

.NOTES
    Aufruf: powershell -File tools\audio_relay_healthcheck.ps1
#>

$ErrorActionPreference = "Continue"
$PhoneTailscaleIp = "100.64.0.11"
$PhoneHostname = "phone-node"
$AudioRelayPort = 59100

Write-Host "=== AudioRelay Mesh-Healthcheck ===" -ForegroundColor Cyan

# 1) Tailscale-Interface: Netzwerkprofil muss "Private" sein, sonst blockt Windows Firewall den Port.
Write-Host "`n[1/4] Tailscale-Netzwerkprofil..." -ForegroundColor Yellow
$tsProfile = Get-NetConnectionProfile -InterfaceAlias "Tailscale" -ErrorAction SilentlyContinue
if (-not $tsProfile) {
    Write-Host "  WARNUNG: Kein Netzwerk-Interface 'Tailscale' gefunden. Laeuft der Tailscale-Client?" -ForegroundColor Red
} elseif ($tsProfile.NetworkCategory -ne "Private") {
    Write-Host "  WARNUNG: Tailscale-Interface ist '$($tsProfile.NetworkCategory)', sollte 'Private' sein." -ForegroundColor Red
    Write-Host "  Fix (als Administrator ausfuehren): Set-NetConnectionProfile -InterfaceAlias 'Tailscale' -NetworkCategory Private" -ForegroundColor Red
} else {
    Write-Host "  OK: Tailscale-Interface ist 'Private'." -ForegroundColor Green
}

# 2) Ist das Handy im Tailnet ueberhaupt online?
Write-Host "`n[2/4] Tailscale-Status von $PhoneHostname..." -ForegroundColor Yellow
$tsStatus = & tailscale status 2>&1
$phoneLine = $tsStatus | Select-String -Pattern $PhoneTailscaleIp
if ($phoneLine -match "offline") {
    Write-Host "  WARNUNG: $PhoneHostname ist offline im Tailnet." -ForegroundColor Red
    Write-Host "  -> Tailscale-App auf dem Handy oeffnen/pruefen. Haeufigste Ursache: Android-Akku-Optimierung" -ForegroundColor Red
    Write-Host "     killt die App im Hintergrund. Fix auf dem Handy: Einstellungen > Apps > Tailscale >" -ForegroundColor Red
    Write-Host "     Akku > 'Uneingeschraenkt' / keine Optimierung, plus in der Tailscale-App selbst" -ForegroundColor Red
    Write-Host "     'Run in background' / 'Always-on VPN' aktivieren." -ForegroundColor Red
} elseif ($phoneLine -match "active") {
    Write-Host "  OK: $PhoneHostname ist online (active)." -ForegroundColor Green
} else {
    Write-Host "  Unklar, Rohzeile: $phoneLine" -ForegroundColor Yellow
}

# 3) Erreichbarkeit (ICMP kann per Tailscale-ACL geblockt sein, ist nur ein Zusatzindiz).
Write-Host "`n[3/4] Ping $PhoneTailscaleIp..." -ForegroundColor Yellow
$ping = Test-Connection -ComputerName $PhoneTailscaleIp -Count 2 -Quiet -ErrorAction SilentlyContinue
if ($ping) {
    Write-Host "  OK: Handy antwortet auf Ping." -ForegroundColor Green
} else {
    Write-Host "  Kein Ping-Antwort (bei 'offline' oben erwartet; falls Handy sonst online ist, kein Alarmsignal - ICMP kann separat blockiert sein)." -ForegroundColor Yellow
}

# 4) Port 59100 frei / durch AudioRelay belegt?
Write-Host "`n[4/4] Port $AudioRelayPort..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort $AudioRelayPort -ErrorAction SilentlyContinue
if ($portInUse) {
    $proc = Get-Process -Id ($portInUse[0].OwningProcess) -ErrorAction SilentlyContinue
    Write-Host "  Port $AudioRelayPort ist belegt von: $($proc.ProcessName) (PID $($portInUse[0].OwningProcess))" -ForegroundColor Green
    Write-Host "  (Das ist erwuenscht, wenn das AudioRelay.exe ist und laeuft.)" -ForegroundColor Green
} else {
    Write-Host "  Port $AudioRelayPort ist frei (AudioRelay laeuft aktuell nicht / horcht nicht)." -ForegroundColor Yellow
}

Write-Host "`n=== Ende Healthcheck ===" -ForegroundColor Cyan
