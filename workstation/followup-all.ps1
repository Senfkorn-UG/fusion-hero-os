# followup-all.ps1 — Alle Session-Follow-ups in einem Durchlauf (Windows)
$ErrorActionPreference = "SilentlyContinue"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Root = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }

Write-Host "=== Fusion Hero OS — Follow-up All-in-One ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/7] Mesh Mainframe-Rolle" -ForegroundColor Yellow
$roles = Join-Path $Root "src\normal_os\integration\mesh_roles.py"
if (Test-Path $roles) {
    python "$roles" 2>$null | ConvertFrom-Json | Select-Object -ExpandProperty mainframe |
        Format-List hostname, role, platform
}

Write-Host "[2/6] Verification API" -ForegroundColor Yellow
try {
    $v = Invoke-RestMethod "http://127.0.0.1:8000/api/verification/full/status" -TimeoutSec 3
    Write-Host "  Orchestrator: $($v.enabled) | LLM-Recovery: $($v.llm_recovery_enabled)"
} catch {
    Write-Host "  Dashboard nicht auf :8000" -ForegroundColor DarkGray
}

Write-Host "[3/6] Tailscale + Mesh" -ForegroundColor Yellow
& "$PSScriptRoot\status.ps1" | Select-Object -First 20

Write-Host "[4/6] AudioRelay" -ForegroundColor Yellow
& "$PSScriptRoot\check-audio-relay.ps1"
& "$PSScriptRoot\route-audio-to-phone.ps1"

Write-Host "[5/6] Gmail Triage" -ForegroundColor Yellow
python (Join-Path $Root "scripts\gmail_triage_bridge.py") 2

Write-Host "[6/6] Archiv-Anker" -ForegroundColor Yellow
python (Join-Path $Root "scripts\archiv_anchor_uncommitted.py") --include-ignored

Write-Host ""
Write-Host "=== Follow-up abgeschlossen ===" -ForegroundColor Green
