#Requires -Version 5.1
# Fusion Hero OS Autoload Controller (post-login / post-reboot)
param(
    [switch]$PrepOnly,
    [switch]$SkipGui,
    [switch]$NoGit,
    [switch]$Force
)

$ErrorActionPreference = "Continue"
$Root = "C:\Users\Admin\fusion-hero-os"
if (-not (Test-Path (Join-Path $Root "VERSION"))) {
    $Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}
$Python = "python"
if (Test-Path "C:\Users\Admin\venv\Scripts\python.exe") {
    $Python = "C:\Users\Admin\venv\Scripts\python.exe"
}
$FusionDir = Join-Path $env:USERPROFILE ".fusion"
$LogDir = Join-Path $FusionDir "logs"
$StatePath = Join-Path $FusionDir "autoload_controller.json"
$LogPath = Join-Path $LogDir "autoload_controller.log"
$LockPath = Join-Path $FusionDir "autoload_controller.lock"

New-Item -ItemType Directory -Force -Path $FusionDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log {
    param([string]$Msg, [string]$Level = "INFO")
    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ss"), $Level, $Msg
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
    Write-Host $line
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
    $pp = @(
        $Root,
        (Join-Path $Root "03_Code"),
        (Join-Path $Root "03_Code\Dashboard")
    )
    if ($env:PYTHONPATH) { $pp += $env:PYTHONPATH }
    $env:PYTHONPATH = ($pp -join ";")
}

function Save-State {
    param([hashtable]$Extra)
    $body = @{
        ok = $true
        controller = "autoload_controller_v1"
        platform_version = "12.0.0"
        repo_root = $Root
        hostname = $env:COMPUTERNAME
        updated_at = (Get-Date).ToUniversalTime().ToString("o")
        log_path = $LogPath
    }
    foreach ($k in $Extra.Keys) {
        $body[$k] = $Extra[$k]
    }
    $json = $body | ConvertTo-Json -Depth 8
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($StatePath, $json, $utf8NoBom)
}

# single-instance lock
if (Test-Path $LockPath) {
    try {
        $old = Get-Content $LockPath -Raw | ConvertFrom-Json
        $age = [datetime]::UtcNow - [datetime]::Parse($old.at)
        if ($age.TotalMinutes -lt 20) {
            if ($old.pid) {
                $p = Get-Process -Id $old.pid -ErrorAction SilentlyContinue
                if ($p) {
                    Write-Log "Another autoload controller running - exit" "WARN"
                    exit 0
                }
            }
        }
    } catch {
        # ignore stale lock
    }
}
$lockObj = @{ pid = $PID; at = (Get-Date).ToUniversalTime().ToString("o") }
($lockObj | ConvertTo-Json) | Set-Content -Path $LockPath -Encoding UTF8

Write-Log ("=== Autoload Controller START root={0} ===" -f $Root)
Set-FusionEnv
Set-Location $Root

$steps = @{}

try {
    $ver = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
    $steps["version"] = $ver
    Write-Log ("VERSION={0}" -f $ver) "OK"
} catch {
    $steps["version"] = "unknown"
    Write-Log "VERSION read failed" "WARN"
}

if ($PrepOnly) {
    Save-State @{
        phase = "prep_only"
        ready = $true
        ready_for_reboot = $true
        steps = $steps
        message = "Env pinned. Reboot then full controller will run."
    }
    Write-Log "PrepOnly complete - ready for reboot" "OK"
    Remove-Item $LockPath -Force -ErrorAction SilentlyContinue
    exit 0
}

if (-not $NoGit) {
    Write-Log "[1] git fetch/pull origin main..."
    try {
        git -C $Root fetch origin main 2>&1 | Out-Null
        $before = git -C $Root rev-parse --short HEAD
        git -C $Root pull --ff-only origin main 2>&1 | Out-Null
        $after = git -C $Root rev-parse --short HEAD
        $steps["git"] = @{ before = $before; after = $after; ok = $true }
        Write-Log ("git {0} -> {1}" -f $before, $after) "OK"
    } catch {
        $steps["git"] = @{ ok = $false; error = "$_" }
        Write-Log "git pull failed" "WARN"
    }
} else {
    $steps["git"] = @{ skipped = $true }
}

Write-Log "[2] Dauer-Eupression..."
try {
    & $Python -m fusion_hero_os.core.dauer_eupression --install 2>&1 | Out-Null
    $steps["dauer_eupression"] = @{ ok = $true }
    Write-Log "Dauer-Eupression OK" "OK"
} catch {
    $steps["dauer_eupression"] = @{ ok = $false }
    Write-Log "Dauer-Eupression fail" "WARN"
}

Write-Log "[3] Poly-FA..."
try {
    & $Python -m fusion_hero_os.core.poly_fa_write_gate --install-handover 2>&1 | Out-Null
    $steps["poly_fa"] = @{ ok = $true }
    Write-Log "Poly-FA OK" "OK"
} catch {
    $steps["poly_fa"] = @{ ok = $false }
    Write-Log "Poly-FA fail" "WARN"
}

Write-Log "[4] Meister Hasch status..."
try {
    $mhScript = Join-Path $Root "scripts\meister_status_snippet.py"
    if (-not (Test-Path $mhScript)) {
        $code = @'
from fusion_hero_os.core.meister_hasch_optimize import status
import json
print(json.dumps(status()))
'@
        Set-Content -Path $mhScript -Value $code -Encoding UTF8
    }
    $mh = & $Python -c "from fusion_hero_os.core.meister_hasch_optimize import status; import json; print(json.dumps(status()))"
    $steps["meister_hasch"] = "$mh"
    Write-Log "Meister status captured" "OK"
} catch {
    $steps["meister_hasch"] = @{ ok = $false }
}

if (-not $SkipGui) {
    Write-Log "[5] start_all.ps1..."
    $startAll = Join-Path $Root "start_all.ps1"
    if (Test-Path $startAll) {
        try {
            $env:FUSION_AUTO_LOAD = "1"
            if ($Force) {
                & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $startAll -Force
            } else {
                & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $startAll
            }
            $steps["start_all"] = @{ ok = $true }
            Write-Log "start_all finished" "OK"
        } catch {
            $steps["start_all"] = @{ ok = $false }
            Write-Log "start_all fail" "ERROR"
        }
    } else {
        $steps["start_all"] = @{ ok = $false; error = "missing" }
    }

    Write-Log "[6] activate_v12.py..."
    $act = Join-Path $Root "scripts\activate_v12.py"
    if (Test-Path $act) {
        try {
            & $Python $act 2>&1 | Out-Null
            $steps["activate_v12"] = @{ ok = $true }
        } catch {
            $steps["activate_v12"] = @{ ok = $false }
            Write-Log "activate_v12 soft-fail" "WARN"
        }
    }
} else {
    $steps["start_all"] = @{ skipped = $true }
    $act = Join-Path $Root "scripts\activate_v12.py"
    if (Test-Path $act) {
        & $Python $act --no-http 2>&1 | Out-Null
        $steps["activate_v12"] = @{ ok = $true; mode = "no-http" }
    }
}

Write-Log "[7] Hero Autoupdate..."
try {
    $once = Join-Path $Root "scripts\hero_autoupdate_once.py"
    $poller = Join-Path $Root "scripts\hero_autoupdate_poller.py"
    $auOut = ""
    if (Test-Path $once) {
        $auOut = & $Python $once 2>&1 | Out-String
    }
    if (Test-Path $poller) {
        Start-Process -FilePath $Python -ArgumentList $poller -WorkingDirectory $Root -WindowStyle Hidden
    }
    $steps["hero_autoupdate"] = @{ ok = $true; detail = $auOut.Trim() }
    Write-Log ("Hero Autoupdate: {0}" -f $auOut.Trim()) "OK"
} catch {
    $steps["hero_autoupdate"] = @{ ok = $false }
    Write-Log "Hero Autoupdate fail" "WARN"
}

Write-Log "[8] Audio L1..."
try {
    & $Python -m fusion_hero_os.core.comaedchen_audio --activate --mode local --no-surface 2>&1 | Out-Null
    $steps["audio_l1"] = @{ ok = $true }
    Write-Log "Audio L1 OK" "OK"
} catch {
    $steps["audio_l1"] = @{ ok = $false }
    Write-Log "Audio L1 soft-fail" "WARN"
}

$healthOk = $false
try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health?light=true" -TimeoutSec 5
    $healthOk = $true
    $steps["dashboard_health"] = @{ ok = $true }
    Write-Log "Dashboard health OK" "OK"
} catch {
    $steps["dashboard_health"] = @{ ok = $false }
    Write-Log "Dashboard not up yet" "WARN"
}

Save-State @{
    phase = "full"
    ready = $true
    ready_for_reboot = $false
    steps = $steps
    health_ok = $healthOk
    message = "Autoload controller completed post-boot sequence"
}

Write-Log "=== Autoload Controller DONE ===" "OK"
Remove-Item $LockPath -Force -ErrorAction SilentlyContinue
exit 0
