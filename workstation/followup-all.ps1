# followup-all.ps1 - Alle Session-Follow-ups in einem Durchlauf (Windows)
$ErrorActionPreference = "SilentlyContinue"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Root = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }

Write-Host "=== Fusion Hero OS - Follow-up All-in-One ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/9] Mesh Mainframe-Rolle" -ForegroundColor Yellow
$roles = Join-Path $Root "src\normal_os\integration\mesh_roles.py"
if (Test-Path $roles) {
    python "$roles" 2>$null | ConvertFrom-Json | Select-Object -ExpandProperty mainframe |
        Format-List hostname, role, platform
}

Write-Host "[2/9] Verification API" -ForegroundColor Yellow
try {
    $v = Invoke-RestMethod "http://127.0.0.1:8000/api/verification/full/status" -TimeoutSec 3
    Write-Host "  Orchestrator: $($v.enabled) | LLM-Recovery: $($v.llm_recovery_enabled)"
} catch {
    Write-Host "  Dashboard nicht auf :8000" -ForegroundColor DarkGray
}

Write-Host "[3/9] Tailscale + Mesh" -ForegroundColor Yellow
& "$PSScriptRoot\status.ps1" | Select-Object -First 20

Write-Host "[4/9] AudioRelay" -ForegroundColor Yellow
& "$PSScriptRoot\check-audio-relay.ps1"
& "$PSScriptRoot\route-audio-to-phone.ps1"

Write-Host "[5/9] Gmail Triage" -ForegroundColor Yellow
python (Join-Path $Root "scripts\gmail_triage_bridge.py") 2

Write-Host "[6/9] Archiv-Anker" -ForegroundColor Yellow
python (Join-Path $Root "scripts\archiv_anchor_uncommitted.py") --include-ignored

Write-Host "[7/9] Planova Inneneinrichter" -ForegroundColor Yellow
$planScript = Join-Path $PSScriptRoot "install-planova.ps1"
$planExe = Join-Path $env:USERPROFILE "Programs\planova\planova.exe"
if (Test-Path $planExe) {
    Write-Host "  Bereits installiert: $planExe" -ForegroundColor Green
    & $planScript -SkipBuild
} else {
    & $planScript -Auto
}

Write-Host "[8/9] GDrive Storage Policy" -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "apply-storage-policy.ps1")

Write-Host "[9/9] Bottom-Up Merge" -ForegroundColor Yellow
$winHead = (git -C $Root rev-parse HEAD 2>$null)
$originHead = (git -C $Root rev-parse origin/main 2>$null)
if ($winHead -and $originHead -and ($winHead -eq $originHead)) {
    Write-Host "  Bereits sync (HEAD $($winHead.Substring(0,7)))" -ForegroundColor Green
} else {
    & (Join-Path $PSScriptRoot "merge-bottom-up.ps1")
}

Write-Host ""
Write-Host "=== Follow-up abgeschlossen ===" -ForegroundColor Green
