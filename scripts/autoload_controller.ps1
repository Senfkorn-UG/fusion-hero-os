#Requires -Version 5.1
<#
.SYNOPSIS
  Fusion Hero OS — Autoload Controller (post-login / post-reboot)

.DESCRIPTION
  Loads critical stack after desktop restart:
    1) Env pins (v12, AUTO_LOAD, HT)
    2) Git pull (origin main) when online
    3) Dauer-Eupression pulse
    4) Poly-FA policy ensure
    5) start_all.ps1 (Dashboard + autoload)
    6) activate_v12.py
    7) Hero Autoupdate service start (background poll)
    8) Optional: local audio membrane (L1)

  State: ~/.fusion/autoload_controller.json
  Log:   ~/.fusion/logs/autoload_controller.log

.PARAMETER PrepOnly
  Only write readiness + env; do not start heavy services.

.PARAMETER SkipGui
  Do not run start_all.ps1 (core modules only).

.PARAMETER NoGit
  Skip git pull.
#>
param(
    [switch]$PrepOnly,
    [switch]$SkipGui,
    [switch]$NoGit,
    [switch]$Force
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path (Join-Path $Root "VERSION"))) {
    $Root = "C:\Users\Admin\fusion-hero-os"
}
$Python = if (Test-Path "C:\Users\Admin\venv\Scripts\python.exe") {
    "C:\Users\Admin\venv\Scripts\python.exe"
} else {
    "python"
}
$FusionDir = Join-Path $env:USERPROFILE ".fusion"
$LogDir = Join-Path $FusionDir "logs"
$StatePath = Join-Path $FusionDir "autoload_controller.json"
$LogPath = Join-Path $LogDir "autoload_controller.log"
$LockPath = Join-Path $FusionDir "autoload_controller.lock"

New-Item -ItemType Directory -Force -Path $FusionDir, $LogDir | Out-Null

function Write-Log([string]$Msg, [string]$Level = "INFO") {
    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ss"), $Level, $Msg
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN"  { "Yellow" }
        "OK"    { "Green" }
        default { "Cyan" }
    }
    Write-Host $line -ForegroundColor $color
}

function Set-FusionEnv {
    $env:FUSION_REPO_ROOT = $Root
    $env:FUSION_PLATFORM_VERSION = "12.0.0"
    $env:FUSION_VERSION = "12.0.0"
    $env:FUSION_AUTO_LOAD = "1"
    $env:FUSION_ALL_MODULES = "1"
    $env:FUSION_HYPERTHREADING = "1"
    $env:FUSION_PROCESS_EXCLUSIVITY = "1"
    $env:FUSION_MAINFRAME_SITE = "1"
    $env:FUSION_GROK_INTERCONNECT = "1"
    $env:FUSION_ROUTE_TABLE = "1"
    $env:FUSION_RACE_GUARD = "1"
    $env:FUSION_DISSERTATION_AS_OS = "1"
    $env:FUSION_V33_DESIGN = "1"
    $env:PYTHONPATH = (@(
        $Root,
        (Join-Path $Root "03_Code"),
        (Join-Path $Root "03_Code\Dashboard"),
        $env:PYTHONPATH
    ) -join [IO.Path]::PathSeparator).Trim([IO.Path]::PathSeparator)
}

function Save-State([hashtable]$Extra) {
    $body = @{
        ok                = $true
        controller        = "autoload_controller_v1"
        platform_version  = "12.0.0"
        repo_root         = $Root
        hostname          = $env:COMPUTERNAME
        updated_at        = (Get-Date).ToUniversalTime().ToString("o")
        log_path          = $LogPath
    }
    foreach ($k in $Extra.Keys) { $body[$k] = $Extra[$k] }
    $body | ConvertTo-Json -Depth 8 | Set-Content -Path $StatePath -Encoding UTF8
}

# --- single instance lock ---
if (Test-Path $LockPath) {
    try {
        $old = Get-Content $LockPath -Raw | ConvertFrom-Json
        $age = [datetime]::UtcNow - [datetime]::Parse($old.at)
        if ($age.TotalMinutes -lt 20 -and $old.pid -and (Get-Process -Id $old.pid -ErrorAction SilentlyContinue)) {
            Write-Log "Another autoload controller running (pid=$($old.pid)) — exit" "WARN"
            exit 0
        }
    } catch {}
}
@{ pid = $PID; at = (Get-Date).ToUniversalTime().ToString("o") } | ConvertTo-Json |
    Set-Content $LockPath -Encoding UTF8

Write-Log "=== Autoload Controller START root=$Root ==="
Set-FusionEnv
Set-Location $Root

$steps = [ordered]@{}

# 0) VERSION
try {
    $ver = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
    $steps["version"] = $ver
    Write-Log "VERSION=$ver" "OK"
} catch {
    $steps["version"] = "unknown"
    Write-Log "VERSION read failed" "WARN"
}

if ($PrepOnly) {
    Save-State @{
        phase   = "prep_only"
        ready   = $true
        steps   = $steps
        message = "Env pinned. Reboot then full controller will run."
    }
    Write-Log "PrepOnly complete — ready for reboot" "OK"
    Remove-Item $LockPath -Force -ErrorAction SilentlyContinue
    exit 0
}

# 1) Git pull
if (-not $NoGit) {
    Write-Log "[1] git fetch/pull origin main..."
    try {
        git -C $Root fetch origin main 2>&1 | Out-Null
        $before = (git -C $Root rev-parse --short HEAD)
        git -C $Root pull --ff-only origin main 2>&1 | Tee-Object -Variable pullOut | Out-Null
        $after = (git -C $Root rev-parse --short HEAD)
        $steps["git"] = @{ before = $before; after = $after; ok = $true }
        Write-Log "git $before -> $after" "OK"
    } catch {
        $steps["git"] = @{ ok = $false; error = "$_" }
        Write-Log "git pull failed: $_" "WARN"
    }
} else {
    $steps["git"] = @{ skipped = $true }
}

# 2) Dauer-Eupression continuous
Write-Log "[2] Dauer-Eupression install/pulse..."
try {
    & $Python -m fusion_hero_os.core.dauer_eupression --install 2>&1 | Out-String | ForEach-Object { Write-Log $_.Trim() }
    $steps["dauer_eupression"] = @{ ok = $true }
    Write-Log "Dauer-Eupression OK" "OK"
} catch {
    $steps["dauer_eupression"] = @{ ok = $false; error = "$_" }
    Write-Log "Dauer-Eupression fail: $_" "WARN"
}

# 3) Poly-FA handover policy
Write-Log "[3] Poly-FA write gate ensure..."
try {
    & $Python -m fusion_hero_os.core.poly_fa_write_gate --install-handover 2>&1 | Out-Null
    $steps["poly_fa"] = @{ ok = $true }
    Write-Log "Poly-FA OK" "OK"
} catch {
    $steps["poly_fa"] = @{ ok = $false }
    Write-Log "Poly-FA fail: $_" "WARN"
}

# 4) Meister Hasch integrity (status only)
Write-Log "[4] Meister Hasch status..."
try {
    $mh = & $Python -c "from fusion_hero_os.core.meister_hasch_optimize import status; import json; print(json.dumps(status()))" 2>&1
    $steps["meister_hasch"] = $mh | Out-String
    Write-Log "Meister status captured" "OK"
} catch {
    $steps["meister_hasch"] = @{ ok = $false }
}

# 5) Dashboard + full autoload
if (-not $SkipGui) {
    Write-Log "[5] start_all.ps1 ..."
    $startAll = Join-Path $Root "start_all.ps1"
    if (Test-Path $startAll) {
        try {
            $env:FUSION_AUTO_LOAD = "1"
            if ($Force) {
                & powershell -NoProfile -ExecutionPolicy Bypass -File $startAll -Force
            } else {
                & powershell -NoProfile -ExecutionPolicy Bypass -File $startAll
            }
            $steps["start_all"] = @{ ok = $true }
            Write-Log "start_all finished" "OK"
        } catch {
            $steps["start_all"] = @{ ok = $false; error = "$_" }
            Write-Log "start_all fail: $_" "ERROR"
        }
    } else {
        $steps["start_all"] = @{ ok = $false; error = "missing" }
    }

    # 6) activate v12 HTTP surface
    Write-Log "[6] activate_v12.py ..."
    $act = Join-Path $Root "scripts\activate_v12.py"
    if (Test-Path $act) {
        try {
            & $Python $act 2>&1 | Out-String | ForEach-Object { if ($_) { Write-Log $_.Trim() } }
            $steps["activate_v12"] = @{ ok = $true }
        } catch {
            $steps["activate_v12"] = @{ ok = $false; error = "$_" }
            Write-Log "activate_v12 soft-fail: $_" "WARN"
        }
    }
} else {
    $steps["start_all"] = @{ skipped = $true }
    # offline activate
    $act = Join-Path $Root "scripts\activate_v12.py"
    if (Test-Path $act) {
        & $Python $act --no-http 2>&1 | Out-Null
        $steps["activate_v12"] = @{ ok = $true; mode = "no-http" }
    }
}

# 7) Hero Autoupdate background
Write-Log "[7] Hero Autoupdate service..."
try {
    $auCmd = @"
import os, sys
sys.path.insert(0, r'$Root')
os.environ['FUSION_REPO_ROOT'] = r'$Root'
from fusion_hero_os.core.hero_autoupdate import get_service, HeroAutoupdateConfig
svc = get_service()
if hasattr(svc, 'start'):
    svc.start()
    print('started')
elif hasattr(svc, 'ensure_running'):
    print(svc.ensure_running())
else:
    # tick once + leave process if service has run loop
    if hasattr(svc, 'tick'):
        print(svc.tick())
    print('service_bound', type(svc).__name__)
"@
    $auOut = & $Python -c $auCmd 2>&1 | Out-String
    $steps["hero_autoupdate"] = @{ ok = $true; detail = $auOut.Trim() }
    Write-Log "Hero Autoupdate: $($auOut.Trim())" "OK"
} catch {
    $steps["hero_autoupdate"] = @{ ok = $false; error = "$_" }
    Write-Log "Hero Autoupdate fail: $_" "WARN"
}

# 8) Audio membrane L1 (person hear/speak) — non-fatal
Write-Log "[8] Comaedchen audio L1 (optional)..."
try {
    & $Python -m fusion_hero_os.core.comaedchen_audio --activate --mode local --no-surface 2>&1 | Out-Null
    $steps["audio_l1"] = @{ ok = $true }
    Write-Log "Audio L1 OK" "OK"
} catch {
    $steps["audio_l1"] = @{ ok = $false }
    Write-Log "Audio L1 soft-fail" "WARN"
}

# Health probe
$health = $null
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health?light=true" -TimeoutSec 5
    $steps["dashboard_health"] = @{ ok = $true; light = $true }
    Write-Log "Dashboard health OK" "OK"
} catch {
    $steps["dashboard_health"] = @{ ok = $false }
    Write-Log "Dashboard not up yet (may still be booting)" "WARN"
}

Save-State @{
    phase     = "full"
    ready     = $true
    steps     = $steps
    health_ok = [bool]$health
    message   = "Autoload controller completed post-boot sequence"
}

Write-Log "=== Autoload Controller DONE ===" "OK"
Remove-Item $LockPath -Force -ErrorAction SilentlyContinue
exit 0
