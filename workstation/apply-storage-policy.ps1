# apply-storage-policy.ps1 - GDrive als Standard-Speicher fuer nicht-operative Daten anwenden
param(
    [switch]$PlanOnly,
    [switch]$FullSweep,
    [switch]$IncludeImages,
    [int]$MinMb = 0
)
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "load-env.ps1")

$policyFile = Join-Path $PSScriptRoot "storage_policy.json"
if (-not (Test-Path $policyFile)) {
    Write-Host "FEHLER: storage_policy.json fehlt" -ForegroundColor Red
    exit 1
}

$policy = Get-Content $policyFile -Raw | ConvertFrom-Json
if ($MinMb -le 0) { $MinMb = [int]$policy.thresholds.offload_min_mb }

Write-Host "=== Fusion Hero - Storage Policy ===" -ForegroundColor Cyan
Write-Host "Policy: $($policy.policy_id)" -ForegroundColor DarkGray
Write-Host $policy.principle -ForegroundColor DarkGray
Write-Host "GDrive Ziel: $env:FUSION_GDRIVE_OFFLOAD" -ForegroundColor Green

if (-not $env:FUSION_GDRIVE_OFFLOAD) {
    Write-Host "WARNUNG: Google Drive nicht gemountet - Auslagerung uebersprungen" -ForegroundColor Yellow
    exit 2
}

$statusDir = Join-Path $env:USERPROFILE ".fusion"
$statusFile = Join-Path $statusDir "storage-policy.status.json"
New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
@{
    policy_id = $policy.policy_id
    state     = if ($PlanOnly) { "planned" } else { "running" }
    gdrive    = $env:FUSION_GDRIVE_OFFLOAD
    updated   = (Get-Date).ToString("o")
} | ConvertTo-Json | Set-Content $statusFile -Encoding UTF8

$offloadScript = Join-Path $PSScriptRoot "offload-to-gdrive.ps1"
$sweepScript = Join-Path $PSScriptRoot "offload-full-sweep.ps1"

try {
    if ($FullSweep) {
        $sweepMin = [int]$policy.thresholds.sweep_min_mb
        if ($PlanOnly) {
            & $sweepScript -PlanOnly -MinMb $sweepMin
        } else {
            & $sweepScript -MinMb $sweepMin
        }
    } else {
        $args = @{ MinMb = $MinMb }
        if ($PlanOnly) { $args.PlanOnly = $true }
        if ($IncludeImages) { $args.IncludeImages = $true }
        & $offloadScript @args
    }
    @{
        policy_id = $policy.policy_id
        state     = "success"
        gdrive    = $env:FUSION_GDRIVE_OFFLOAD
        updated   = (Get-Date).ToString("o")
    } | ConvertTo-Json | Set-Content $statusFile -Encoding UTF8
} catch {
    @{
        policy_id = $policy.policy_id
        state     = "failed"
        message   = $_.Exception.Message
        updated   = (Get-Date).ToString("o")
    } | ConvertTo-Json | Set-Content $statusFile -Encoding UTF8
    throw
}

Write-Host "`nStorage Policy angewendet. Status: $statusFile" -ForegroundColor Green
