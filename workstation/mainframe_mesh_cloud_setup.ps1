# mainframe_mesh_cloud_setup.ps1 — Fractal mesh + Supabase + Google server/Drive
param(
    [string]$ExitProfile = "google-server",
    [switch]$ApplyExit,
    [switch]$DryRun,
    [switch]$SkipSupabaseCheck
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$DashboardEnv = Join-Path $RepoRoot "03_Code\Dashboard\.env"
$DashboardExample = Join-Path $RepoRoot "03_Code\Dashboard\.env.example"

Write-Host "=== Mainframe Mesh Cloud Setup (Supabase + Google) ===" -ForegroundColor Cyan

if (-not $SkipSupabaseCheck -and -not (Test-Path $DashboardEnv)) {
    Write-Host "[Supabase] Keine Dashboard .env — Vorlage anlegen..." -ForegroundColor Yellow
    Copy-Item $DashboardExample $DashboardEnv
    Write-Host "  Bitte SUPABASE_PUBLISHABLE_KEY in $DashboardEnv eintragen" -ForegroundColor Yellow
    Write-Host "  Projekt: https://supabase.com/dashboard/project/swmmoxhdzarmoupyssqe" -ForegroundColor DarkGray
    Write-Host "  Schema v5: 03_Code/Dashboard/supabase/schema_migration_v5_fractal_mesh.sql" -ForegroundColor DarkGray
}

$env:FUSION_SUPABASE_SYNC = "1"
$env:FUSION_SUPABASE_CLOUD_SYNC = "1"
$env:PUBLIC_SUPABASE_PROJECT_REF = "swmmoxhdzarmoupyssqe"
if (Test-Path $DashboardEnv) {
    Get-Content $DashboardEnv | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            if ($value) { Set-Item -Path "env:$name" -Value $value }
        }
    }
}

$setupArgs = @("setup", "--exit", $ExitProfile)
if ($ApplyExit) { $setupArgs += "--apply-exit" }
if ($DryRun) { $setupArgs += "--dry-run" }

Push-Location $RepoRoot
try {
    python fractal_mainframe_mesh.py @setupArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "`n-> Cloud backend status:" -ForegroundColor Green
    python mesh_cloud_backends.py status
} finally {
    Pop-Location
}