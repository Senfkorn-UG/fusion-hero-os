# start_core.ps1 - Alle Backend-Funktionen laden OHNE GUI (Browser/templates)
# Virtual Hyperthreading, AutoLoad, Module, GPU/CPU-Coupler, Integration-Hub
param(
    [switch]$Force,
    [switch]$WithDocs,
    [switch]$WithBridge
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Root = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$Dash = Join-Path $Root "03_Code\Dashboard"
$Python = if ($env:FUSION_PYTHON) { $env:FUSION_PYTHON } else { "C:\Users\Admin\venv\Scripts\python.exe" }
if (-not (Test-Path $Python)) { $Python = "python" }
$ApiUrl = "http://127.0.0.1:8000"

$env:FUSION_SKIP_GUI = "1"
$env:FUSION_HYPERTHREADING = "1"
$env:FUSION_VIRTUAL_HT_GPU = "1"
$env:FUSION_VIRTUAL_THREADS = if ($env:FUSION_VIRTUAL_THREADS) { $env:FUSION_VIRTUAL_THREADS } else { "256" }
$env:FUSION_ALL_MODULES = "1"

function Stop-FusionProcesses {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'uvicorn app:app|workspace\.py|rest_api_server' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

function Wait-ApiReady([int]$MaxSec = 120) {
    $deadline = (Get-Date).AddSeconds($MaxSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-RestMethod -Uri "$ApiUrl/api/health?light=true" -TimeoutSec 3
            if ($r) { return $true }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Invoke-CoreStep([string]$Label, [scriptblock]$Action) {
    Write-Host "[$Label]..." -NoNewline
    try {
        $result = & $Action
        Write-Host " OK" -ForegroundColor Green
        return @{ ok = $true; result = $result }
    } catch {
        Write-Host " FALLBACK ($($_.Exception.Message))" -ForegroundColor Yellow
        return @{ ok = $false; error = $_.Exception.Message }
    }
}

function Start-BackgroundPython([string]$Name, [string]$WorkDir, [string]$Args) {
    $existing = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match [regex]::Escape($Name) }
    if ($existing) {
        Write-Host "  $Name laeuft bereits" -ForegroundColor DarkGray
        return
    }
    Start-Process -FilePath $Python -ArgumentList $Args -WorkingDirectory $WorkDir -WindowStyle Minimized
    Write-Host "  $Name gestartet" -ForegroundColor DarkGray
}

Write-Host "=== Fusion Hero OS - Core Load (ohne GUI) ===" -ForegroundColor Cyan
Write-Host "API: $ApiUrl  |  Virtual HT: $($env:FUSION_VIRTUAL_HT_GPU)" -ForegroundColor DarkGray

if ($Force) {
    $env:FUSION_FORCE_SYNC = "1"
    Write-Host "Modus: FORCE (Full AutoLoad)" -ForegroundColor Magenta
}

$syncScript = Join-Path $Root "sync_grok_intern.ps1"
if (Test-Path $syncScript) { & $syncScript }

Stop-FusionProcesses
Start-Sleep -Seconds 1

$backendBat = Join-Path $Root "run_backend.bat"
if (-not (Test-Path $backendBat)) { $backendBat = Join-Path $PSScriptRoot "run_backend.bat" }
Start-Process -FilePath $backendBat -WorkingDirectory $Root -WindowStyle Minimized

Write-Host "[Backend] API starten..." -NoNewline
if (-not (Wait-ApiReady)) {
    Write-Host " FEHLER" -ForegroundColor Red
    exit 1
}
Write-Host " OK" -ForegroundColor Green

if ($WithDocs) {
    $docs = Join-Path $Root "src\normal_os\integration\hero-docs-server.py"
    if (Test-Path $docs) {
        Start-BackgroundPython "hero-docs-server" (Split-Path $docs -Parent) $docs
    }
}
if ($WithBridge -and $env:NORMALOS_ROOT) {
    Start-BackgroundPython "grok_pc_bridge" $env:NORMALOS_ROOT "-m src.normal_os.bridge.grok_pc_bridge"
}

$alBody = if ($Force) {
    '{"phase":"full","force":true,"sync":true,"attach_meta":true}'
} else {
    '{"phase":"staged","attach_meta":true}'
}
$alTimeout = if ($Force) { 300 } else { 120 }

Invoke-CoreStep "AutoLoad" {
    Invoke-RestMethod -Uri "$ApiUrl/api/autoload/run" -Method POST `
        -Body $alBody -ContentType "application/json" -TimeoutSec $alTimeout | Out-Null
}

Invoke-CoreStep "Mainframe" {
    $deadline = (Get-Date).AddSeconds(120)
    while ((Get-Date) -lt $deadline) {
        $s = Invoke-RestMethod -Uri "$ApiUrl/api/health" -TimeoutSec 5
        if ($s.mainframe.loaded) { return $s.mainframe }
        Start-Sleep -Seconds 1
    }
    throw "timeout"
}

Invoke-CoreStep "Hyperthreading" {
    $ht = Invoke-RestMethod -Uri "$ApiUrl/api/hyperthreading" -Method POST `
        -Body '{"enabled":true}' -ContentType "application/json" -TimeoutSec 15
    if (-not $ht.enabled) { throw "HT not enabled" }
    $ht
}

Invoke-CoreStep "Virtual-HT-GPU" {
    $ht = Invoke-RestMethod -Uri "$ApiUrl/api/hyperthreading" -TimeoutSec 10
    if (-not $ht.virtual_ht_gpu) {
        throw "virtual_ht_gpu=false (FUSION_VIRTUAL_HT_GPU pruefen)"
    }
    Write-Host " workers=$($ht.workers) vthreads=$($ht.virtual_threads) " -NoNewline
    $ht
}

Invoke-CoreStep "CPU-Tuner" {
    Invoke-RestMethod -Uri "$ApiUrl/api/cpu/tuner/run" -Method POST -TimeoutSec 15 | Out-Null
}

Invoke-CoreStep "GPU-Compute-Boost" {
    Invoke-RestMethod -Uri "$ApiUrl/api/gpu/compute/boost" -Method POST -TimeoutSec 30 | Out-Null
}

Invoke-CoreStep "Load-All-Modules" {
    $la = Invoke-RestMethod -Uri "$ApiUrl/api/load-all?force=true" -Method POST -TimeoutSec 120
    Write-Host " $($la.count)/$($la.total) " -NoNewline
    $la
}

Invoke-CoreStep "Resource-Coupler" {
    Invoke-RestMethod -Uri "$ApiUrl/api/resource/coupler/run" -Method POST -TimeoutSec 20 | Out-Null
}

Invoke-CoreStep "Meta-Layer" {
    Invoke-RestMethod -Uri "$ApiUrl/api/meta-layer/attach" -Method POST -TimeoutSec 15 | Out-Null
}

Invoke-CoreStep "Windows-Substrat" {
    Invoke-RestMethod -Uri "$ApiUrl/api/windows/substrate/tune" -Method POST -TimeoutSec 25 | Out-Null
}

Invoke-CoreStep "Cyber-Layer" {
    Invoke-RestMethod -Uri "$ApiUrl/api/windows/cyber-layer/activate" -Method POST -TimeoutSec 15 | Out-Null
}

$kernelScript = Join-Path $PSScriptRoot "run-local-infrastructure-kernel.ps1"
if (Test-Path $kernelScript) {
    Invoke-CoreStep "Local-Kernel-Probe" {
        & $kernelScript -ProbeOnly -Timeout 3 2>&1 | Out-Null
    }
}

try {
    $health = Invoke-RestMethod -Uri "$ApiUrl/api/health" -TimeoutSec 10
    $ht = $health.hyperthreading
    Write-Host ""
    Write-Host "=== Core bereit (ohne GUI) ===" -ForegroundColor Cyan
    Write-Host "  API:              $ApiUrl/api/health"
    Write-Host "  Mainframe:        $($health.mainframe.loaded) ($($health.mainframe.version))"
    Write-Host "  Hyperthreading:   $($ht.enabled) | workers=$($ht.workers)"
    Write-Host "  Virtual HT GPU:   $($ht.virtual_ht_gpu) | vthreads=$($ht.virtual_threads)"
    Write-Host "  AutoLoad:         $ApiUrl/api/autoload/status"
    Write-Host "  Module:           $ApiUrl/api/registry/status"
    Write-Host ""
    Write-Host "GUI bei Bedarf:     start_all.ps1  oder  Start-Process $ApiUrl" -ForegroundColor DarkGray
} catch {
    Write-Host "Health-Check fehlgeschlagen: $_" -ForegroundColor Yellow
}
