# offload-full-sweep.ps1 — Alle C:\Users\Admin Ordner durchgehen, Unnoetiges nach GDrive
param(
    [switch]$PlanOnly,
    [int]$MinMb = 20
)
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Python = "C:\Users\Admin\venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
$FusionRoot = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { "C:\Users\Admin\fusion-hero-os" }
$WslTool = "\\wsl.localhost\Ubuntu\home\admin_fuhos\fusion-hero-core\tools\disk_dedup_offload.py"
$Tool = Join-Path $FusionRoot "tools\disk_dedup_offload.py"
if (-not (Test-Path $Tool)) { $Tool = $WslTool }

function Get-FreeGb {
    $d = Get-PSDrive C
    [math]::Round($d.Free / 1GB, 1)
}

Write-Host "=== C: Vollstaendiger GDrive-Sweep ===" -ForegroundColor Cyan
$freeBefore = Get-FreeGb
Write-Host "C: frei vorher: $freeBefore GB"

if ($PlanOnly) {
    & $Python $Tool --report 2>&1
    & $Python $Tool --offload-plan --offload-min-mb $MinMb 2>&1 | Select-Object -Last 30
    exit 0
}

# 1) Cache loeschen (nicht auslagern)
Write-Host "`n[1/4] Cache-Bereinigung..." -ForegroundColor Yellow
$cacheFreed = 0
foreach ($cachePath in @(
    (Join-Path $env:LOCALAPPDATA "npm-cache"),
    (Join-Path $env:LOCALAPPDATA "pnpm-cache"),
    (Join-Path $env:USERPROFILE ".cache\puppeteer")
)) {
    if (Test-Path $cachePath) {
        $s = (Get-ChildItem $cachePath -Recurse -File -EA SilentlyContinue | Measure-Object Length -Sum).Sum
        Remove-Item $cachePath -Recurse -Force -EA SilentlyContinue
        $cacheFreed += $s
        Write-Host ("  geloescht: " + $cachePath) -ForegroundColor Green
    }
}
$tempCutoff = (Get-Date).AddDays(-7)
Get-ChildItem $env:TEMP -File -EA SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $tempCutoff } |
    ForEach-Object { try { $cacheFreed += $_.Length; Remove-Item $_.FullName -Force } catch {} }
Write-Host ("  Cache/Temp: " + [math]::Round($cacheFreed/1MB,0) + " MB") -ForegroundColor Green

# 2) Dedup + Ordner-Offload + Datei-Offload
Write-Host "`n[2/4] Dedup + Ordner + Dateien..." -ForegroundColor Yellow
$stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
& $Python $Tool --dedup --quarantine --run-label $stamp 2>&1 | Select-Object -Last 3
& $Python $Tool --offload-folders 2>&1
& $Python $Tool --offload-execute --offload-min-mb $MinMb 2>&1

# 3) Downloads-Reste (kleine Archive/Installer als Ordner)
Write-Host "`n[3/4] Downloads-Archive verschieben..." -ForegroundColor Yellow
$gdBase = Join-Path $env:USERPROFILE "Google Drive-Streaming\Meine Ablage"
if (-not (Test-Path $gdBase)) { $gdBase = Join-Path $env:USERPROFILE "Google Drive\Meine Ablage" }
$dlDest = Join-Path $gdBase "FusionHero_Offload\Downloads_Archive"
$dlSrc = Join-Path $env:USERPROFILE "Downloads"
if ((Test-Path $dlSrc) -and (Test-Path $gdBase)) {
    New-Item -ItemType Directory -Force -Path $dlDest | Out-Null
    & robocopy $dlSrc $dlDest /E /MOV /XO /R:1 /W:1 /XF "*.crdownload" "*.partial" /NFL /NDL /NJH /NJS /nc /ns /np /MT:8 | Out-Null
    if ($LASTEXITCODE -lt 8) { Write-Host "  Downloads -> $dlDest" -ForegroundColor Green }
}

# 4) Desktop lose Dateien
Write-Host "`n[4/4] Desktop -> GDrive..." -ForegroundColor Yellow
$deskDest = Join-Path $gdBase "FusionHero_Offload\Desktop_Archive"
$deskSrc = Join-Path $env:USERPROFILE "Desktop"
if ((Test-Path $deskSrc) -and (Test-Path $gdBase)) {
    New-Item -ItemType Directory -Force -Path $deskDest | Out-Null
    Get-ChildItem $deskSrc -File -EA SilentlyContinue | ForEach-Object {
        $dst = Join-Path $deskDest $_.Name
        Copy-Item $_.FullName $dst -Force
        if ((Test-Path $dst) -and ((Get-Item $dst).Length -eq $_.Length)) {
            Remove-Item $_.FullName -Force
        }
    }
    Get-ChildItem $deskSrc -Directory -EA SilentlyContinue |
        Where-Object { $_.Name -notlike ".*" } |
        ForEach-Object {
            & robocopy $_.FullName (Join-Path $deskDest $_.Name) /E /MOV /R:1 /W:1 /NFL /NDL /NJH /NJS | Out-Null
        }
    Write-Host "  Desktop archiviert" -ForegroundColor Green
}

$freeAfter = Get-FreeGb
Write-Host "`n=== Ergebnis ===" -ForegroundColor Cyan
Write-Host "C: frei: $freeBefore -> $freeAfter GB (+$([math]::Round($freeAfter - $freeBefore, 1)) GB)" -ForegroundColor Green
Write-Host "GDrive: Speicherplatz freigeben bei FusionHero_Offload nach Upload" -ForegroundColor DarkGray
