# provision_google_mesh_server.ps1 — Create GCE VM for mesh exit + fractal replica
param(
    [string]$ProjectId = "project-bbf0e6db-52e1-462b-8e3",
    [string]$Zone = "europe-west3-a",
    [string]$InstanceName = "fusion-mesh-exit",
    [string]$MachineType = "e2-micro",
    [string]$TailscaleHostname = "fusion-mesh-exit",
    [string]$TsAuthKey = $env:TS_AUTHKEY
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$Startup = Join-Path $PSScriptRoot "gce_mesh_server_startup.sh"

Write-Host "=== Provision Google Mesh Server (GCE) ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectId"
Write-Host "Zone:    $Zone"
Write-Host "VM:      $InstanceName"

gcloud config set project $ProjectId | Out-Null
gcloud services enable compute.googleapis.com --quiet | Out-Null

$meta = "fusion-hostname=$TailscaleHostname"
if ($TsAuthKey) {
    $meta += ",ts-authkey=$TsAuthKey"
    Write-Host "TS_AUTHKEY: set (headless Tailscale join)" -ForegroundColor Green
} else {
    $meta += ",ts-authkey=unset"
    Write-Host "TS_AUTHKEY: not set — join Tailscale manually via SSH after create" -ForegroundColor Yellow
}

$exists = gcloud compute instances describe $InstanceName --zone=$Zone 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Instance $InstanceName already exists — starting..." -ForegroundColor Yellow
    gcloud compute instances start $InstanceName --zone=$Zone
} else {
    gcloud compute instances create $InstanceName `
        --zone=$Zone `
        --machine-type=$MachineType `
        --image-family=ubuntu-2204-lts `
        --image-project=ubuntu-os-cloud `
        --boot-disk-size=20GB `
        --tags="tailscale,http-server" `
        --metadata=$meta `
        --metadata-from-file=startup-script=$Startup
}

$ip = gcloud compute instances describe $InstanceName --zone=$Zone --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
Write-Host ""
Write-Host "VM ready." -ForegroundColor Green
Write-Host "  Name:       $InstanceName"
Write-Host "  External:   $ip"
Write-Host "  SSH:        gcloud compute ssh $InstanceName --zone=$Zone"
Write-Host "  Tailscale:  will appear as $TailscaleHostname after startup (2-3 min)"
Write-Host ""
Write-Host "After online, flush pending fractal sync:" -ForegroundColor Cyan
Write-Host "  python $RepoRoot\mesh_cloud_backends.py flush-pending"