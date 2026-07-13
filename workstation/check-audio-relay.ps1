# check-audio-relay.ps1 — AudioRelay + Handy-Headset Status
$ErrorActionPreference = "SilentlyContinue"

Write-Host "=== AudioRelay / Headset ===" -ForegroundColor Cyan

$procs = Get-Process AudioRelay, audiorelay-backend -ErrorAction SilentlyContinue
if ($procs) {
    Write-Host "  AudioRelay: laeuft (PID $($procs.Id -join ','))" -ForegroundColor Green
} else {
    Write-Host "  AudioRelay: nicht gestartet" -ForegroundColor Yellow
}

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Devices.MediaDevice, Windows.Media.Devices, ContentType = WindowsRuntime]
$default = [Windows.Media.Devices.MediaDevice]::GetDefaultAudioRenderId(
    [Windows.Media.Devices.AudioDeviceRole]::Default
)
$isRelay = $default -match "aed0c79b-d5d7-47dc-883b"
if ($isRelay) {
    Write-Host "  Standard-Ausgabe: Virtual Speakers (AudioRelay) OK" -ForegroundColor Green
} else {
    Write-Host "  Standard-Ausgabe: NICHT AudioRelay" -ForegroundColor Yellow
    Write-Host "  Fuehre route-audio-to-phone.ps1 aus" -ForegroundColor DarkGray
}

$tsJson = & "C:\Program Files\Tailscale\tailscale.exe" status --json 2>$null | ConvertFrom-Json
if ($tsJson -and $tsJson.Peer) {
    $phoneFound = $false
    $tsJson.Peer.PSObject.Properties | ForEach-Object {
        $p = $_.Value
        if ($p.HostName -like "*redmi*" -or $p.DNSName -like "*redmi*") {
            $script:phoneFound = $true
            $st = if ($p.Online) { "online" } else { "offline" }
            $col = if ($p.Online) { "Green" } else { "Yellow" }
            Write-Host "  Handy redmi: $st" -ForegroundColor $col
            if ($p.Online) {
                Write-Host "  AudioRelay-App: PC verbinden + Playback aktiv" -ForegroundColor DarkGray
            }
        }
    }
    if (-not $phoneFound) {
        Write-Host "  Handy: nicht im Mesh sichtbar" -ForegroundColor Yellow
    }
}
