# mesh_join_remote.ps1 — Geraet per SSH ins Tailscale-Mesh aufnehmen
param(
    [Parameter(Mandatory = $true)]
    [string]$SshTarget,
    [string]$Hostname = "",
    [ValidateSet("leaf", "exit", "subnet")]
    [string]$Role = "leaf",
    [string]$TsAuthKey = $env:TS_AUTHKEY,
    [string]$AdvertiseRoutes = "10.0.0.0/8",
    [switch]$NoHeroDocs,
    [switch]$ReplicateFractal,
    [switch]$DryRun
)
$ErrorActionPreference = "Stop"
$RepoRoot = if ($env:FUSION_REPO_ROOT) { $env:FUSION_REPO_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$Bootstrap = Join-Path $PSScriptRoot "mesh_join_remote_bootstrap.sh"

if (-not (Test-Path $Bootstrap)) { throw "Missing $Bootstrap" }
if (-not $TsAuthKey) {
    Write-Host "TS_AUTHKEY fehlt. Erstelle einen Reusable Key:" -ForegroundColor Yellow
    Write-Host "  https://login.tailscale.com/admin/settings/keys" -ForegroundColor Cyan
    Write-Host '  $env:TS_AUTHKEY = "tskey-auth-..."' -ForegroundColor Yellow
    exit 1
}
if (-not $Hostname) {
    $Hostname = ($SshTarget -split '@')[-1] -replace '[^a-zA-Z0-9-]', '-'
    if ($Hostname.Length -gt 40) { $Hostname = $Hostname.Substring(0, 40) }
}

Write-Host "=== Fusion Mesh — Remote Join per SSH ===" -ForegroundColor Cyan
Write-Host "Target:   $SshTarget"
Write-Host "Hostname: $Hostname"
Write-Host "Role:     $Role"
Write-Host "Tailnet:  example.ts.net"

$remoteEnv = @(
    "export TS_AUTHKEY='$TsAuthKey'",
    "export FUSION_TS_HOSTNAME='$Hostname'",
    "export FUSION_MESH_ROLE='$Role'",
    "export FUSION_ADVERTISE_ROUTES='$AdvertiseRoutes'",
    "export FUSION_MESH_HERO_DOCS=$(if ($NoHeroDocs) { '0' } else { '1' })"
) -join '; '

if ($DryRun) {
    Write-Host "[DryRun] scp $Bootstrap -> ${SshTarget}:/tmp/fusion_mesh_join.sh" -ForegroundColor DarkGray
    Write-Host "[DryRun] ssh $SshTarget `"$remoteEnv; bash /tmp/fusion_mesh_join.sh`"" -ForegroundColor DarkGray
    exit 0
}

Write-Host "`n[1/3] Bootstrap-Skript hochladen..." -ForegroundColor Yellow
scp -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new $Bootstrap "${SshTarget}:/tmp/fusion_mesh_join.sh"
if ($LASTEXITCODE -ne 0) { throw "scp failed" }
Write-Ok "uploaded"

Write-Host "[2/3] Remote Join ausfuehren..." -ForegroundColor Yellow
ssh -o ConnectTimeout=15 $SshTarget "${remoteEnv}; chmod +x /tmp/fusion_mesh_join.sh; bash /tmp/fusion_mesh_join.sh"
if ($LASTEXITCODE -ne 0) { throw "remote bootstrap failed" }
Write-Ok "remote bootstrap"

Write-Host "[3/3] Verify..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
$magic = "$Hostname.example.ts.net"
try {
    $ts = tailscale status 2>&1 | Out-String
    if ($ts -match [regex]::Escape($Hostname)) { Write-Ok "peer in tailscale status" }
    else { Write-Warn "peer noch nicht in lokalem status — ggf. 30s warten" }
} catch { Write-Warn "tailscale status lokal nicht verfuegbar" }

if ($Role -eq "exit") {
    Write-Host ""
    Write-Host "Exit-Node: In Tailscale Admin genehmigen:" -ForegroundColor Yellow
    Write-Host "  https://login.tailscale.com/admin/machines" -ForegroundColor Cyan
    Write-Host "  Machine '$Hostname' -> Edit route settings -> Use as exit node" -ForegroundColor DarkGray
}
if ($Role -eq "subnet") {
    Write-Host ""
    Write-Host "Subnet-Routen in Admin genehmigen (Subnet router):" -ForegroundColor Yellow
    Write-Host "  https://login.tailscale.com/admin/machines" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Verify URLs:" -ForegroundColor Green
Write-Host "  tailscale ping $magic"
Write-Host "  ssh $SshTarget   # oder: ssh ${Hostname}.example.ts.net (Tailscale SSH)"
Write-Host "  http://${magic}:8088/status"
Write-Host "  http://${magic}:8088/mesh/fractal/status"

if ($ReplicateFractal) {
    Write-Host "`nFractal replicate..." -ForegroundColor Yellow
    Push-Location $RepoRoot
    python fractal_mainframe_mesh.py save --replicate
    Pop-Location
}

function Write-Ok($m) { Write-Host "  OK: $m" -ForegroundColor Green }
function Write-Warn($m) { Write-Host "  WARN: $m" -ForegroundColor Yellow }