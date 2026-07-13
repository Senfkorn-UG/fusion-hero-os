# offload-to-gdrive.ps1 — C:-Speicher entlasten via Google Drive (FusionHero_Offload)
param(
    [switch]$PlanOnly,
    [switch]$IncludeImages,
    [switch]$SkipDedup,
    [switch]$SkipCache,
    [switch]$CompactWsl,
    [int]$MinMb = 50
)
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Python = "C:\Users\Admin\venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
$FusionRoot = $env:FUSION_HERO_ROOT
if (-not $FusionRoot) { $FusionRoot = Split-Path $PSScriptRoot -Parent }
$Tool = Join-Path $FusionRoot "tools\disk_dedup_offload.py"

function Get-FreeGb {
    $d = Get-PSDrive C
    [math]::Round($d.Free / 1GB, 1)
}

Write-Host "=== Fusion Hero - GDrive Offload ===" -ForegroundColor Cyan
$freeBefore = Get-FreeGb
Write-Host "C: frei vorher: $freeBefore GB" -ForegroundColor DarkGray

if (-not (Test-Path $Tool)) {
    Write-Host "FEHLER: $Tool nicht gefunden" -ForegroundColor Red
    exit 1
}

# 1) Dedup (reversibel)
if (-not $SkipDedup) {
    Write-Host "`n[1/4] Dedup (Duplikate -> Quarantaene)..." -ForegroundColor Yellow
    $stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
    & $Python $Tool --dedup 2>&1 | Select-Object -Last 5
    & $Python $Tool --dedup --quarantine --run-label $stamp 2>&1 | Select-Object -Last 3
}

# 2) Offload-Plan
Write-Host "`n[2/4] Offload-Kandidaten..." -ForegroundColor Yellow
$imgFlag = if ($IncludeImages) { "--include-images" } else { "" }
& $Python $Tool --offload-plan --offload-min-mb $MinMb $imgFlag 2>&1 | Select-Object -Last 25

if ($PlanOnly) {
    Write-Host "`nPlanOnly - keine Ausfuehrung." -ForegroundColor Yellow
    exit 0
}

# 3) Auslagern nach Google Drive
Write-Host "`n[3/5] Auslagern nach FusionHero_Offload..." -ForegroundColor Yellow
& $Python $Tool --offload-execute --offload-min-mb $MinMb $imgFlag 2>&1

# 3b) DCIM-Fotos als Ordner (viele kleine Dateien)
if ($IncludeImages) {
    Write-Host "`n[3b/5] Pictures/DCIM -> GDrive Photo-Ingestion..." -ForegroundColor Yellow
    $dcim = Join-Path $env:USERPROFILE "Pictures\DCIM"
    $gdBase = $env:FUSION_GDRIVE_LIBRARY
    if (-not $gdBase) {
        $gdBase = Join-Path $env:USERPROFILE "Google Drive-Streaming\Meine Ablage"
        if (-not (Test-Path $gdBase)) {
            $gdBase = Join-Path $env:USERPROFILE "Google Drive\Meine Ablage"
        }
    }
    $photoDest = $env:FUSION_GDRIVE_PHOTOS
    if (-not $photoDest) {
        $photoDest = Join-Path $gdBase "ALTE_Frau_95g_Photo_Ingestion\DCIM_PC"
    }
    if ((Test-Path $dcim) -and (Test-Path (Split-Path $photoDest -Parent))) {
        New-Item -ItemType Directory -Force -Path $photoDest | Out-Null
        & robocopy $dcim $photoDest /E /MOV /XO /R:1 /W:1 /NFL /NDL /NJH /NJS /nc /ns /np /MT:8 | Out-Null
        $rc = $LASTEXITCODE
        if ($rc -lt 8) {
            Write-Host "  DCIM verschoben nach $photoDest (robocopy $rc)" -ForegroundColor Green
        } else {
            Write-Host "  DCIM robocopy Fehler: $rc" -ForegroundColor Red
        }
    } else {
        Write-Host "  DCIM oder GDrive nicht gefunden - uebersprungen" -ForegroundColor DarkGray
    }
}

# 4) Cache + optional WSL
if (-not $SkipCache) {
    Write-Host "`n[4/5] Cache-Bereinigung..." -ForegroundColor Yellow
    $npm = Join-Path $env:LOCALAPPDATA "npm-cache"
    if (Test-Path $npm) {
        npm cache clean --force 2>$null
        Write-Host "  npm-cache bereinigt" -ForegroundColor Green
    }
    $tempCutoff = (Get-Date).AddDays(-7)
    $tempFreed = 0
    Get-ChildItem $env:TEMP -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $tempCutoff } |
        ForEach-Object {
            try { $tempFreed += $_.Length; Remove-Item $_.FullName -Force -ErrorAction Stop } catch {}
        }
  if ($tempFreed -gt 0) {
        Write-Host ("  Temp (>7d): " + [math]::Round($tempFreed/1MB,0) + " MB") -ForegroundColor Green
    }
}

if ($CompactWsl) {
    Write-Host "`n[WSL] Disk komprimieren..." -ForegroundColor Yellow
    wsl --shutdown 2>$null
    Start-Sleep -Seconds 3
    $vhdx = Get-ChildItem "$env:LOCALAPPDATA\Packages" -Recurse -Filter "ext4.vhdx" -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($vhdx) {
        $before = [math]::Round($vhdx.Length/1GB, 2)
        Optimize-VHD -Path $vhdx.FullName -Mode Full 2>$null
        $vhdx.Refresh()
        $after = [math]::Round($vhdx.Length/1GB, 2)
        Write-Host "  WSL VHDX: $before GB -> $after GB" -ForegroundColor Green
    } else {
        Write-Host "  Keine ext4.vhdx gefunden" -ForegroundColor DarkGray
    }
}

$freeAfter = Get-FreeGb
Write-Host "`n=== Ergebnis ===" -ForegroundColor Cyan
Write-Host "C: frei nachher: $freeAfter GB (Delta: +$([math]::Round($freeAfter - $freeBefore, 1)) GB)" -ForegroundColor Green
Write-Host ""
Write-Host "Hinweis Google Drive Streaming:" -ForegroundColor DarkGray
Write-Host "  Nach Upload: Rechtsklick FusionHero_Offload -> Speicherplatz freigeben" -ForegroundColor DarkGray
Write-Host "  Ziel: $env:USERPROFILE\Google Drive-Streaming\Meine Ablage\FusionHero_Offload" -ForegroundColor DarkGray
