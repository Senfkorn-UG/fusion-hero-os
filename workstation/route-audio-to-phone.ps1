# Route Windows system audio to phone via AudioRelay virtual device.
$ErrorActionPreference = "Stop"

$targetShortName = "Virtual Speakers for AudioRelay"
$targetName = "Virtual Speakers (Virtual Speakers for AudioRelay)"
$targetId = "{0.0.0.00000000}.{AED0C79B-D5D7-47DC-883B-3AA0926F3865}"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$svv = Join-Path $scriptDir "tools\SoundVolumeView.exe"
if (-not (Test-Path $svv)) {
    $svv = Join-Path $scriptDir "tools\soundvolumeview\SoundVolumeView.exe"
}

function Test-DefaultIsAudioRelay {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
    $null = [Windows.Media.Devices.MediaDevice, Windows.Media.Devices, ContentType = WindowsRuntime]
    $id = [Windows.Media.Devices.MediaDevice]::GetDefaultAudioRenderId(
        [Windows.Media.Devices.AudioDeviceRole]::Default
    )
    return ($id -match "AED0C79B-D5D7-47DC-883B-3AA0926F3865")
}

function Set-DefaultAudioRelay {
    if (Test-Path $svv) {
        & $svv /SetDefault $targetShortName all | Out-Null
        Start-Sleep -Milliseconds 500
        if (Test-DefaultIsAudioRelay) { return $true }
        & $svv /SetDefault $targetId all | Out-Null
        Start-Sleep -Milliseconds 500
        return (Test-DefaultIsAudioRelay)
    }
    return $false
}

$switched = Set-DefaultAudioRelay
if (-not $switched) {
    Write-Warning "Automatisches Umschalten fehlgeschlagen."
    Write-Host "Bitte manuell: Windows-Einstellungen > System > Sound > Ausgabe -> '$targetName'"
}

$audioRelay = Get-Process -Name "AudioRelay" -ErrorAction SilentlyContinue
if (-not $audioRelay) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\AudioRelay\AudioRelay.exe"),
        (Join-Path $env:LOCALAPPDATA "AudioRelay\AudioRelay.exe"),
        "C:\Program Files\AudioRelay\AudioRelay.exe"
    )
    $exe = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($exe) {
        Start-Process $exe
        Write-Host "AudioRelay gestartet: $exe"
    } else {
        Write-Warning "AudioRelay.exe nicht gefunden. Bitte App manuell starten."
    }
} else {
    Write-Host "AudioRelay laeuft bereits (PID $($audioRelay.Id -join ','))"
}

if (Test-DefaultIsAudioRelay) {
    Write-Host "OK: Standard-Ausgabe -> $targetShortName"
} else {
    Write-Warning "Standard-Ausgabe ist noch nicht AudioRelay."
}

Write-Host ""
Write-Host "In der AudioRelay-App pruefen:"
<<<<<<< HEAD
Write-Host "  1. Handy (redmi-note-13-pro-5g) verbunden"
=======
Write-Host "  1. Handy (phone-node) verbunden"
>>>>>>> 404701973eb09fd68448759c001b712e6fb2ef09
Write-Host "  2. Playback / Wiedergabe aktiv"
Write-Host ""
Write-Host "WSL/Cursor-Audio: PULSE_SERVER=unix:/mnt/wslg/PulseServer -> Windows-Standardgeraet"
