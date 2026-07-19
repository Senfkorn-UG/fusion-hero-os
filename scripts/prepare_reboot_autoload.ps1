#Requires -Version 5.1
<#
.SYNOPSIS
  Prepare Fusion Hero OS for desktop reboot — updates + Autoload Controller registration.

.DESCRIPTION
  Run BEFORE restarting the PC:
    - git fetch/pull origin main
    - pin readiness state
    - register Logon scheduled task + Startup launcher
    - optional dual-org fetch (senfkorn)
    - Dauer-Eupression + Poly-FA ensure (no full GUI)

.PARAMETER RegisterTask
  Register Windows Scheduled Task at logon (default: true).

.PARAMETER RegisterStartup
  Place launcher in user Startup folder (default: true).
#>
param(
    [switch]$NoRegisterTask,
    [switch]$NoRegisterStartup,
    [switch]$NoGit
)

$ErrorActionPreference = "Continue"
$Root = "C:\Users\Admin\fusion-hero-os"
if (-not (Test-Path (Join-Path $Root "VERSION"))) {
    $Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}
$Python = if (Test-Path "C:\Users\Admin\venv\Scripts\python.exe") {
    "C:\Users\Admin\venv\Scripts\python.exe"
} else { "python" }

$FusionDir = Join-Path $env:USERPROFILE ".fusion"
$LogDir = Join-Path $FusionDir "logs"
$StatePath = Join-Path $FusionDir "autoload_controller.json"
$LauncherCmd = Join-Path $FusionDir "run_autoload_controller.cmd"
$ControllerPs1 = Join-Path $Root "scripts\autoload_controller.ps1"
$TaskName = "FusionHeroOS-AutoloadController"

New-Item -ItemType Directory -Force -Path $FusionDir, $LogDir | Out-Null

Write-Host "=== PREPARE REBOOT / AUTOLOAD ===" -ForegroundColor Cyan
Write-Host "Root: $Root"

# 1) Git update
$gitInfo = @{}
if (-not $NoGit) {
    Write-Host "[1] git fetch/pull..." -ForegroundColor Yellow
    Push-Location $Root
    try {
        git fetch origin main 2>&1 | Out-Host
        $before = git rev-parse --short HEAD
        git pull --ff-only origin main 2>&1 | Out-Host
        $after = git rev-parse --short HEAD
        $gitInfo = @{ before = $before; after = $after; ok = $true }
        Write-Host "  HEAD $before -> $after" -ForegroundColor Green
        # best-effort senfkorn fetch (no merge force)
        git fetch senfkorn main 2>&1 | Out-Null
    } catch {
        $gitInfo = @{ ok = $false; error = "$_" }
        Write-Host "  git warn: $_" -ForegroundColor Yellow
    }
    Pop-Location
}

# 2) Policies without full GUI
Write-Host "[2] Dauer-Eupression + Poly-FA..." -ForegroundColor Yellow
Push-Location $Root
$env:FUSION_REPO_ROOT = $Root
$env:FUSION_PLATFORM_VERSION = "12.0.0"
$env:FUSION_AUTO_LOAD = "1"
$env:PYTHONPATH = $Root
& $Python -m fusion_hero_os.core.dauer_eupression --install 2>&1 | Out-Host
& $Python -m fusion_hero_os.core.poly_fa_write_gate --install-handover 2>&1 | Out-Host
& $Python -c 'from fusion_hero_os.core.meister_hasch_optimize import status; import json; print(json.dumps(status()))' 2>&1 | Out-Host
Pop-Location

# 3) Launcher cmd (used by Startup + Task)
$cmdBody = @"
@echo off
REM Fusion Hero OS Autoload Controller — generated, safe to re-run
set FUSION_REPO_ROOT=$Root
set FUSION_PLATFORM_VERSION=12.0.0
set FUSION_AUTO_LOAD=1
set FUSION_ALL_MODULES=1
set FUSION_HYPERTHREADING=1
cd /d "$Root"
timeout /t 25 /nobreak >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Minimized -File "$ControllerPs1"
"@
Set-Content -Path $LauncherCmd -Value $cmdBody -Encoding ASCII
Write-Host "[3] Launcher: $LauncherCmd" -ForegroundColor Green

# 4) Startup folder
if (-not $NoRegisterStartup) {
    $startup = [Environment]::GetFolderPath("Startup")
    $startupCmd = Join-Path $startup "FusionHeroOS-AutoloadController.cmd"
    Copy-Item -Force $LauncherCmd $startupCmd
    Write-Host "[4] Startup registered: $startupCmd" -ForegroundColor Green
} else {
    Write-Host "[4] Startup skipped" -ForegroundColor DarkGray
}

# 5) Scheduled Task at logon
if (-not $NoRegisterTask) {
    Write-Host "[5] Scheduled Task: $TaskName" -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$LauncherCmd`"" -WorkingDirectory $Root
        $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
            -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
            -Settings $settings -Principal $principal -Force | Out-Null
        Write-Host "  Task registered (AtLogOn)" -ForegroundColor Green
    } catch {
        Write-Host "  Task register failed (need rights?): $_" -ForegroundColor Yellow
        Write-Host "  Startup folder launcher still active." -ForegroundColor Yellow
    }
}

# 6) Readiness state
$ready = @{
    ok                 = $true
    phase              = "pre_reboot_ready"
    ready_for_reboot   = $true
    controller         = "autoload_controller_v1"
    platform_version   = "12.0.0"
    repo_root          = $Root
    hostname           = $env:COMPUTERNAME
    git                = $gitInfo
    launcher           = $LauncherCmd
    task_name          = $TaskName
    prepared_at        = (Get-Date).ToUniversalTime().ToString("o")
    after_reboot       = @(
        "Wait ~30s for network",
        "Autoload Controller runs (Startup + Task)",
        "git pull · Dauer-Eupression · Poly-FA · start_all · activate_v12 · hero_autoupdate · audio L1",
        "Dashboard http://127.0.0.1:8000",
        "Log: $env:USERPROFILE\.fusion\logs\autoload_controller.log"
    )
    manual_fallback    = "powershell -File $ControllerPs1"
}
$json = $ready | ConvertTo-Json -Depth 6
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($StatePath, $json, $utf8NoBom)

# 7) PrepOnly pin via controller
& powershell -NoProfile -ExecutionPolicy Bypass -File $ControllerPs1 -PrepOnly

Write-Host ""
Write-Host "=== READY FOR REBOOT ===" -ForegroundColor Green
Write-Host "State: $StatePath"
Write-Host "After login the Autoload Controller starts automatically."
Write-Host "Manual: powershell -File `"$ControllerPs1`""
Write-Host ""
Write-Host "You can restart the desktop PC now." -ForegroundColor Cyan
exit 0
