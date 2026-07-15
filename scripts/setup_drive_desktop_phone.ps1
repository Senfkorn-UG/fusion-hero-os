#Requires -Version 5.1
<#
.SYNOPSIS
  Start Google Drive for Desktop + prepare phone-analog Sicherung paths.
.DESCRIPTION
  - Launches GoogleDriveFS if installed
  - Detects mount / My Drive path
  - Creates Fusion_Hero_OS_Sicherung mirror staging under local + optional Drive path
  - Writes phone checklist + deep links
  - Calls python activate (no secrets)
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
    $found = @()
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
        if (Test-Path $p) { $found += $p }
    }
    # scan drive letters for "My Drive" / "Meine Ablage"
    Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue | ForEach-Object {
        $root = $_.Root
        foreach ($name in @("Meine Ablage", "My Drive", "Google Drive")) {
            $c = Join-Path $root $name
            if (Test-Path $c) { $found += $c }
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
        Write-Host "Google Drive for Desktop already running (PID $($running.Id -join ','))" -ForegroundColor Green
    }
} else {
    Write-Host "Google Drive for Desktop not found. Install: winget install Google.GoogleDrive" -ForegroundColor Red
    Start-Process "https://www.google.com/drive/download/"
}

$myDrives = Find-MyDrivePaths
Write-Host "My Drive candidates: $($myDrives -join ' | ')" -ForegroundColor Gray

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

# Always keep a stable local mirror of latest snapshot
$snapRoot = Join-Path $localRoot "snapshots"
$latest = Get-ChildItem $snapRoot -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latest) {
    $mirrorSnap = Join-Path $mirrorLocal "latest_snapshot"
    if (Test-Path $mirrorSnap) { Remove-Item $mirrorSnap -Recurse -Force -ErrorAction SilentlyContinue }
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

# Phone checklist (analog)
$phoneMd = @"
# Handy-Sicherung (analog zu Drive for Desktop)

**Plan:** Google One 5 TB (gleicher Account wie Desktop)
**Cloud-Ordner:** Fusion_Hero_OS_Sicherung
**Web:** https://drive.google.com/drive/folders/1a_jWLVX7p5Zw4UCOCbpZjGoAOaj3qUpO

## Apps (Android / iOS)

1. **Google Drive** — App Store / Play Store  
   - https://play.google.com/store/apps/details?id=com.google.android.apps.docs  
   - https://apps.apple.com/app/google-drive/id507874739
2. **Google One** — Geräte-Backup + Speicher  
   - https://play.google.com/store/apps/details?id=com.google.android.apps.subscriptions.red  
   - https://apps.apple.com/app/google-one/id1454120035

## Schritte Handy (5 Min)

1. Mit **demselben Google-Konto** anmelden wie am PC (5 TB Plan).
2. **Google One** öffnen → Geräte-Backup / Backup jetzt → Fotos, Kontakte, SMS (Android) aktivieren.
3. **Google Drive** öffnen → Ordner **Fusion_Hero_OS_Sicherung** (steht unter „Bei mir“ / freigegeben).
4. Optional: wichtige lokale Dateien **hochladen** in `Fusion_Hero_OS_Sicherung/phone_uploads`.
5. Optional Mesh (lokal im Heimnetz/Tailscale):  
   `powershell -File workstation\mesh_phone_mirror.ps1`

## Policy

- Keine Secrets (.env, API-Keys, GPG private) in Drive laden.
- Dissertation-public-safe Snapshots kommen vom Desktop-Mirror.
"@
$phoneMd | Set-Content -Encoding utf8 (Join-Path $phoneRoot "HANDY_CHECKLISTE.md")
$phoneMd | Set-Content -Encoding utf8 (Join-Path $Root "docs\sicherung\HANDY_CHECKLISTE.md")

# Desktop guide
$deskMd = @"
# Google Drive for Desktop — Fusion Hero OS

## Status-Skript
``````powershell
powershell -File scripts\setup_drive_desktop_phone.ps1
python -m fusion_hero_os.core.google_one_sicherung --desktop --phone --status
``````

## Nach dem Start

1. Taskleisten-Icon **Google Drive** → anmelden (5 TB Konto).
2. Einstellungen → Google Drive → **Streamen** oder **Spiegeln**.
3. Ordner **Fusion_Hero_OS_Sicherung** im Drive (My Drive) sichtbar machen.
4. Lokal: ``~/.fusion/sicherung/drive_mirror/latest_snapshot``
5. Cloud-Link: https://drive.google.com/drive/folders/1a_jWLVX7p5Zw4UCOCbpZjGoAOaj3qUpO

## Install (falls fehlend)
``````powershell
winget install Google.GoogleDrive
``````
"@
$deskMd | Set-Content -Encoding utf8 (Join-Path $Root "docs\sicherung\DRIVE_FOR_DESKTOP.md")

# State JSON
$state = @{
    updated_at = (Get-Date).ToUniversalTime().ToString("o")
    drivefs_exe = $exe
    drivefs_running = [bool](Get-Process -Name "GoogleDriveFS" -ErrorAction SilentlyContinue)
    my_drive_paths = @($myDrives)
    cloud_fusion_folder = $targetDriveFolder
    local_mirror = $mirrorLocal
    phone_checklist = (Join-Path $phoneRoot "HANDY_CHECKLISTE.md")
    plan_tb = 5
}
$state | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $localRoot "google_one\DESKTOP_PHONE_STATE.json")

# Python activate hooks
python -m fusion_hero_os.core.google_one_sicherung --desktop --phone --no-browser 2>&1 | Write-Host

Write-Host ""
Write-Host "Desktop state: $(Join-Path $localRoot 'google_one\DESKTOP_PHONE_STATE.json')" -ForegroundColor Cyan
Write-Host "Phone checklist: docs\sicherung\HANDY_CHECKLISTE.md" -ForegroundColor Cyan
if (-not $targetDriveFolder) {
    Write-Host "HINWEIS: My Drive Mount noch nicht erreichbar — in Drive-App anmelden, dann Skript erneut ausführen." -ForegroundColor Yellow
}
Write-Host "Done." -ForegroundColor Green
