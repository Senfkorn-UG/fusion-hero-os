# Route Windows system audio to phone via AudioRelay virtual device.
# Prefer workstation\fix-headset-relay.ps1 for full auto (firewall + start + route).
$ErrorActionPreference = "Continue"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$fix = Join-Path $scriptDir "fix-headset-relay.ps1"
if (Test-Path $fix) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $fix
    exit $LASTEXITCODE
}

# Fallback (legacy): SoundVolumeView only
$targetShortName = "Virtual Speakers for AudioRelay"
$svv = Join-Path $scriptDir "tools\SoundVolumeView.exe"
if (-not (Test-Path $svv)) {
    $svv = Join-Path $scriptDir "tools\soundvolumeview\SoundVolumeView.exe"
}
if (Test-Path $svv) {
    & $svv /SetDefault $targetShortName all | Out-Null
    Write-Host "OK: SetDefault $targetShortName"
} else {
    Write-Warning "SoundVolumeView.exe missing"
}
