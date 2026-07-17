# Start Fusion Hero OS stack on canonical port 42069 (worktree port/42069)
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File workstation\start_42069.ps1
#   powershell -File workstation\start_42069.ps1 -NoFunnel

param(
    [switch]$NoFunnel,
    [switch]$NoDashboard,
    [switch]$BridgeOnly
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path (Join-Path $Root "start_fusion_hero.py"))) {
    $Root = "C:\Users\Admin\fusion-hero-os-wt-42069"
}
$Port = 42069
$env:FUSION_PORT_BASE = "$Port"
$env:FUSION_BACKEND_PORT = "$Port"
$env:FUSION_FUNNEL_PORT = "$Port"
$env:PYTHONPATH = "$Root;$Root\03_Code;$env:PYTHONPATH"

Write-Host "=== Fusion Hero OS @ $Port (worktree) ===" -ForegroundColor Cyan
Write-Host "Root: $Root"

# Free port if our old python servers hold it
Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Stopping PID $($_.OwningProcess) on :$Port"
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}

if ($BridgeOnly) {
    Start-Process -FilePath "python" -ArgumentList "start_fusion_hero.py","--bridge-only","--mainframe-laden" -WorkingDirectory $Root -WindowStyle Minimized
    Write-Host "Bridge-only started"
    exit 0
}

if (-not $NoDashboard) {
    $dash = Join-Path $Root "03_Code\Dashboard"
    Start-Process -FilePath "python" -ArgumentList @(
        "-m","uvicorn","app:app","--host","127.0.0.1","--port","$Port"
    ) -WorkingDirectory $dash -WindowStyle Minimized
    Start-Sleep -Seconds 2
    try {
        $code = (Invoke-WebRequest "http://127.0.0.1:$Port/api/health" -UseBasicParsing -TimeoutSec 8).StatusCode
        Write-Host "Dashboard HTTP $code -> http://127.0.0.1:$Port"
    } catch {
        # health path may vary
        try {
            $code = (Invoke-WebRequest "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 8).StatusCode
            Write-Host "Dashboard root HTTP $code -> http://127.0.0.1:$Port"
        } catch {
            Write-Host "Dashboard probe pending: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

if (-not $NoFunnel) {
    $ts = "C:\Program Files\Tailscale\tailscale.exe"
    if (Test-Path $ts) {
        & $ts funnel reset 2>$null
        & $ts serve reset 2>$null
        & $ts serve --bg --yes $Port 2>&1 | Out-Host
        & $ts funnel --bg --yes $Port 2>&1 | Out-Host
        & $ts funnel status 2>&1 | Out-Host
    }
}

Write-Host ""
Write-Host "Local:  http://127.0.0.1:$Port/"
Write-Host "MeshOps: http://127.0.0.1:$Port/api/mesh/ops"
Write-Host "Funnel: https://desktop-kpki9e4.tail391adb.ts.net/"
Write-Host "Done."
