# activate_comaedchen_audio.ps1 — Operator ↔ Comädchen (Comet) audio channel
param(
    [ValidateSet("auto", "local", "phone")]
    [string]$Mode = "auto",
    [switch]$NoSurface,
    [switch]$NoRoute
)
$ErrorActionPreference = "Continue"
$Repo = if ($env:FUSION_REPO_ROOT) { $env:FUSION_REPO_ROOT } else { "C:\Users\Admin\fusion-hero-os" }
$Python = if (Test-Path "C:\Users\Admin\venv\Scripts\python.exe") {
    "C:\Users\Admin\venv\Scripts\python.exe"
} else { "python" }

Write-Host "=== Comädchen Audio Channel ===" -ForegroundColor Magenta
Write-Host "Mode: $Mode" -ForegroundColor Cyan

# 1) FULL AUTO headset relay repair (no operator action)
$fix = Join-Path $Repo "workstation\fix-headset-relay.ps1"
if ((Test-Path $fix) -and -not $NoRoute -and $Mode -ne "local") {
    Write-Host "`n[1] Fix headset relay (auto)" -ForegroundColor Yellow
    & powershell -NoProfile -ExecutionPolicy Bypass -File $fix
} else {
    $check = Join-Path $Repo "workstation\check-audio-relay.ps1"
    if (Test-Path $check) {
        Write-Host "`n[1] AudioRelay status" -ForegroundColor Yellow
        & powershell -NoProfile -ExecutionPolicy Bypass -File $check
    }
}

# 2) Phone path: force route if requested (delegates to fix script)
if ($Mode -eq "phone" -and -not $NoRoute) {
    Write-Host "`n[2] Route audio to phone (AudioRelay)" -ForegroundColor Yellow
    $route = Join-Path $Repo "workstation\route-audio-to-phone.ps1"
    if (Test-Path $route) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $route
    }
}

# 3) Python activator (Comet + state + optional route)
Write-Host "`n[3] Activate channel" -ForegroundColor Yellow
$args = @("-m", "fusion_hero_os.core.comaedchen_audio", "--activate", "--mode", $Mode)
if ($NoSurface) { $args += "--no-surface" }
if ($NoRoute) { $args += "--no-route" }
Push-Location $Repo
& $Python @args
$rc = $LASTEXITCODE
Pop-Location

Write-Host "`n=== Checklist ===" -ForegroundColor Cyan
Write-Host "  1. Comet window focused (Nummer 2)"
Write-Host "  2. Mic permission ALLOW for Comet"
Write-Host "  3. Voice/mic button in Comet → speak to Comädchen"
Write-Host "  4. local = PC speakers | phone = AudioRelay headset"
Write-Host ""
exit $rc
