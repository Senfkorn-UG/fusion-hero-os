# setup-google-oauth.ps1 - Google OAuth fuer Gmail/Drive/Calendar (include_granted_scopes)
param(
    [ValidateSet("gmail", "google_drive", "google_calendar", "all")]
    [string]$Connector = "gmail",
    [switch]$StatusOnly
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Root = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$ConnectorsDir = Join-Path $Root "src\normal_os\connectors"
$OAuthDir = Join-Path $env:USERPROFILE ".fusion\google-oauth"
$OAuthModule = Join-Path $ConnectorsDir "google_oauth.py"

if (-not (Test-Path $OAuthModule)) {
    Write-Host "FEHLER: google_oauth.py nicht gefunden" -ForegroundColor Red
    exit 1
}

$env:PYTHONPATH = (Split-Path $ConnectorsDir -Parent)
$py = if ($env:FUSION_PYTHON) { $env:FUSION_PYTHON } else { "python" }

if ($StatusOnly) {
    & $py $OAuthModule --status
    exit $LASTEXITCODE
}

Write-Host "Google OAuth Setup (include_granted_scopes=true)" -ForegroundColor Cyan
Write-Host "Credentials: $OAuthDir\credentials.json" -ForegroundColor DarkGray
Write-Host "Token:       $OAuthDir\token.json" -ForegroundColor DarkGray

if (-not (Test-Path $OAuthDir)) {
    New-Item -ItemType Directory -Force -Path $OAuthDir | Out-Null
}

$targets = if ($Connector -eq "all") { @("gmail", "google_drive", "google_calendar") } else { @($Connector) }
foreach ($t in $targets) {
    Write-Host "`n=== Auth: $t ===" -ForegroundColor Yellow
    & $py $OAuthModule --auth $t
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "`n=== Status ===" -ForegroundColor Cyan
& $py $OAuthModule --status
