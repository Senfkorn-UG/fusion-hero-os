#Requires -Version 5.1
<#
.SYNOPSIS
  Start Google Drive for Desktop + prepare phone-analog Sicherung paths.
#>
$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

function Find-GoogleDriveFS {
    $bases = @(
        "${env:ProgramFiles}\Google\Drive File Stream",
        "${env:ProgramFiles(x86)}\Google\Drive File Stream"
    )
    foreach ($b in $bases) {
        if (-not (Test-Path $b)) { continue }
        $candidates = Get-ChildItem $b -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^\d+\.\d+' } |
            Sort-Object Name -Descending
        foreach ($c in $candidates) {
            $exe = Join-Path $c.FullName "GoogleDriveFS.exe"
            if (Test-Path $exe) { return $exe }
        }
    }
    return $null
}

function Find-MyDrivePaths {
    $found = New-Object System.Collections.Generic.List[string]
    $try = @(
        "$env:USERPROFILE\Google Drive",
        "$env:USERPROFILE\Meine Ablage",
        "$env:USERPROFILE\My Drive",
        "G:\Meine Ablage",
        "G:\My Drive",
        "G:\",
        "H:\Meine Ablage",
        "H:\My Drive"
    )
    foreach ($p in $try) {
        if (Test-Path $p) { [void]$found.Add($p) }
    }
    Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue | ForEach-Object {
        $root = $_.Root
        foreach ($name in @("Meine Ablage", "My Drive", "Google Drive")) {
            $c = Join-Path $root $name
            if (Test-Path $c) { [void]$found.Add($c) }
        }
    }
    return ($found | Select-Object -Unique)
}

Write-Host "=== Drive for Desktop + Handy analog ===" -ForegroundColor Cyan

$exe = Find-GoogleDriveFS
if ($exe) {
    Write-Host "DriveFS: $exe" -ForegroundColor Green
    $running = Get-Process -Name "GoogleDriveFS" -ErrorAction SilentlyContinue
    if (-not $running) {
        Start-Process $exe
        Write-Host "Started Google Drive for Desktop..." -ForegroundColor Yellow
        Start-Sleep -Seconds 8
    } else {
        Write-Host "Google Drive for Desktop already running" -ForegroundColor Green
    }
} else {
    Write-Host "Google Drive for Desktop not found. Install: winget install Google.GoogleDrive" -ForegroundColor Red
    Start-Process "https://www.google.com/drive/download/"
}

$myDrives = @(Find-MyDrivePaths)
Write-Host ("My Drive candidates: " + ($myDrives -join " | ")) -ForegroundColor Gray

$localRoot = Join-Path $env:USERPROFILE ".fusion\sicherung"
$mirrorLocal = Join-Path $localRoot "drive_mirror"
$phoneRoot = Join-Path $localRoot "phone"
New-Item -ItemType Directory -Force -Path $mirrorLocal, $phoneRoot | Out-Null

$targetDriveFolder = $null
foreach ($md in $myDrives) {
    $cand = Join-Path $md "Fusion_Hero_OS_Sicherung"
    try {
        New-Item -ItemType Directory -Force -Path $cand -ErrorAction Stop | Out-Null
        $targetDriveFolder = $cand
        break
    } catch {
        continue
    }
}

$snapRoot = Join-Path $localRoot "snapshots"
$latest = Get-ChildItem $snapRoot -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latest) {
    $mirrorSnap = Join-Path $mirrorLocal "latest_snapshot"
    if (Test-Path $mirrorSnap) {
        Remove-Item $mirrorSnap -Recurse -Force -ErrorAction SilentlyContinue
    }
    Copy-Item $latest.FullName $mirrorSnap -Recurse -Force
    Write-Host "Local mirror latest snapshot: $mirrorSnap" -ForegroundColor Green
    if ($targetDriveFolder) {
        $cloudSnap = Join-Path $targetDriveFolder "snapshots"
        New-Item -ItemType Directory -Force -Path $cloudSnap | Out-Null
        $cloudLatest = Join-Path $cloudSnap $latest.Name
        if (-not (Test-Path $cloudLatest)) {
            Copy-Item $latest.FullName $cloudLatest -Recurse -Force -ErrorAction SilentlyContinue
        }
        Write-Host "Cloud mirror path: $cloudLatest" -ForegroundColor Green
    }
}

# Python hooks (writes docs + state)
python -m fusion_hero_os.core.google_one_sicherung --desktop --phone --no-browser

$state = [ordered]@{
    updated_at          = (Get-Date).ToUniversalTime().ToString("o")
    drivefs_exe         = $exe
    drivefs_running     = [bool](Get-Process -Name "GoogleDriveFS" -ErrorAction SilentlyContinue)
    my_drive_paths      = @($myDrives)
    cloud_fusion_folder = $targetDriveFolder
    local_mirror        = $mirrorLocal
    phone_checklist     = (Join-Path $phoneRoot "HANDY_CHECKLISTE.md")
    plan_tb             = 5
}
$statePath = Join-Path $localRoot "google_one\DESKTOP_PHONE_STATE.json"
$state | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 $statePath

Write-Host ""
Write-Host "Desktop/phone state: $statePath" -ForegroundColor Cyan
Write-Host "Docs: docs\sicherung\DRIVE_FOR_DESKTOP.md + HANDY_CHECKLISTE.md" -ForegroundColor Cyan
if (-not $targetDriveFolder) {
    Write-Host "HINWEIS: My Drive Mount noch nicht erreichbar." -ForegroundColor Yellow
    Write-Host "Taskleiste -> Google Drive -> anmelden (5 TB Konto), dann Skript erneut." -ForegroundColor Yellow
}
Write-Host "Done." -ForegroundColor Green
