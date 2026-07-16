# Deploy Fusion coordination CronJob with real image + Workload Identity
# Usage (repo root):
#   powershell -File scripts/deploy_coordination_gke.ps1
#   powershell -File scripts/deploy_coordination_gke.ps1 -SkipBuild
#   powershell -File scripts/deploy_coordination_gke.ps1 -ManualOnly

param(
    [switch]$SkipBuild,
    [switch]$ManualOnly,
    [string]$Project = "project-bbf0e6db-52e1-462b-8e3",
    [string]$Region = "europe-west3",
    [string]$Cluster = "senfkorn-gke-cluster",
    [string]$Tag = "v10.0.0"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$env:Path = "$env:USERPROFILE\.local\bin;C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin;" + $env:Path

$Image = "$Region-docker.pkg.dev/$Project/fusion-hero/coordination:$Tag"
$Gsa = "fusion-training-sa@$Project.iam.gserviceaccount.com"
$KsaMember = "serviceAccount:$Project.svc.id.goog[fusion-coordination/fusion-coordination-ksa]"

Write-Host "=== Fusion coordination deploy ($Tag) ===" -ForegroundColor Cyan
Write-Host "  project: $Project"
Write-Host "  image:   $Image"

# 1) AR repo (idempotent)
gcloud artifacts repositories describe fusion-hero --location=$Region --project=$Project 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud artifacts repositories create fusion-hero `
        --repository-format=docker `
        --location=$Region `
        --project=$Project `
        --description="Fusion Hero OS images"
}

# 2) WI binding (idempotent)
Write-Host "[WI] bind $KsaMember -> $Gsa" -ForegroundColor DarkCyan
gcloud iam service-accounts add-iam-policy-binding $Gsa `
    --project=$Project `
    --role="roles/iam.workloadIdentityUser" `
    --member=$KsaMember 2>&1 | Out-Null

# 3) Build + push
if (-not $SkipBuild) {
    Write-Host "[build] Cloud Build submit..." -ForegroundColor DarkCyan
    gcloud builds submit `
        --config=infra/k8s/fusion-coordination/cloudbuild.yaml `
        --project=$Project `
        --substitutions=_TAG=$Tag `
        .
    if ($LASTEXITCODE -ne 0) { throw "Cloud Build failed" }
} else {
    Write-Host "[build] skipped" -ForegroundColor Yellow
}

# 4) Credentials + apply
gcloud container clusters get-credentials $Cluster --region $Region --project $Project | Out-Null
kubectl apply -f infra/k8s/fusion-coordination/namespace.yaml
kubectl apply -f infra/k8s/fusion-coordination/coordination-cronjob.yaml

# 5) Manual one-shot (always, unless ManualOnly false and we only want cron — we always verify)
if (-not $ManualOnly) {
    $job = "fusion-coord-manual-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Write-Host "[job] create $job from CronJob" -ForegroundColor DarkCyan
    kubectl create job --from=cronjob/fusion-service-coordination $job -n fusion-coordination
    Write-Host "Waiting for job complete (up to 10 min)..."
    kubectl wait --for=condition=complete "job/$job" -n fusion-coordination --timeout=600s
    if ($LASTEXITCODE -ne 0) {
        kubectl describe "job/$job" -n fusion-coordination
        kubectl get pods -n fusion-coordination -l job-name=$job -o wide
        kubectl logs -n fusion-coordination -l "job-name=$job" --tail=80
        throw "Manual coordination job did not complete"
    }
    Write-Host "[job] logs:" -ForegroundColor Green
    kubectl logs -n fusion-coordination -l "job-name=$job" --tail=100
}

Write-Host "=== OK: CronJob fusion-service-coordination live ===" -ForegroundColor Green
kubectl get cronjob,sa -n fusion-coordination -o wide
Write-Host "GCS: gs://fusion-ai-data-$Project/coordination/"
