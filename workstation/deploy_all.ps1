# deploy_all.ps1 - Vollstaendiges Deployment: lokal + GKE + GCE + Mesh
param(
    [switch]$SkipGit,
    [switch]$SkipGke,
    [switch]$SkipGce,
    [switch]$NoGui
)
$ErrorActionPreference = "Continue"
$RepoRoot = if ($env:FUSION_REPO_ROOT) { $env:FUSION_REPO_ROOT } else { "C:\Users\Admin\fusion-hero-os" }
$Project = "project-bbf0e6db-52e1-462b-8e3"
$Region = "europe-west3"
$Cluster = "senfkorn-gke-cluster"
$Bucket = "fusion-ai-data-project-bbf0e6db-52e1-462b-8e3"
$Zone = "europe-west3-a"
$Vm = "fusion-mesh-exit"
$Python = if (Test-Path "C:\Users\Admin\venv\Scripts\python.exe") { "C:\Users\Admin\venv\Scripts\python.exe" } else { "python" }
$Kubectl = if (Test-Path "$env:TEMP\gke-kubectl\kubectl.exe") { "$env:TEMP\gke-kubectl\kubectl.exe" } else { "kubectl" }

$env:FUSION_REPO_ROOT = $RepoRoot
$env:PYTHONPATH = "$RepoRoot\03_Code;$RepoRoot"
$env:USE_GKE_GCLOUD_AUTH_PLUGIN = "True"
$env:FUSION_BUSINESSPLAN_PATH = Join-Path $RepoRoot "docs\business\senfkorn_businessplan.yaml"
$env:FUSION_MAINFRAME_DAEMONS = "1"

function Write-Step($n, $msg) { Write-Host ""; Write-Host "[$n] $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "  OK: $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  WARN: $msg" -ForegroundColor Yellow }

Write-Host "=== Fusion Hero OS Deploy All ===" -ForegroundColor Magenta
Write-Host "Repo: $RepoRoot"

Write-Step "1/7" "Git sync"
if (-not $SkipGit) {
    Push-Location $RepoRoot
    $status = git status --porcelain 2>$null
    if ($status) {
        git add -A 2>$null
        git commit -m "deploy: energy pricing and mainframe ops wiring" 2>$null
    }
    git push origin main 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Ok "origin/main pushed" } else { Write-Warn "git push skipped or failed" }
    Pop-Location
} else { Write-Warn "skipped (-SkipGit)" }

Write-Step "2/7" "GCS training artifacts"
$uploadDir = Join-Path $env:TEMP "fusion-training-upload"
New-Item -ItemType Directory -Force -Path $uploadDir | Out-Null
Copy-Item (Join-Path $RepoRoot "03_Code\training\fusion_stability_train.py") $uploadDir -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $RepoRoot "qb_qubo.py") $uploadDir -Force -ErrorAction SilentlyContinue
gcloud storage cp "$uploadDir\*" "gs://$Bucket/training/" --project=$Project 2>$null
if ($LASTEXITCODE -eq 0) { Write-Ok "gs://$Bucket/training/" } else { Write-Warn "GCS upload failed" }

Write-Step "3/7" "GKE fusion-training"
if (-not $SkipGke) {
    gcloud container clusters get-credentials $Cluster --region=$Region --project=$Project 2>$null
    $k8s = Join-Path $RepoRoot "infra\k8s\fusion-training"
    & $Kubectl apply -f (Join-Path $k8s "namespace.yaml") 2>$null
    & $Kubectl apply -f (Join-Path $k8s "serviceaccount.yaml") 2>$null
    & $Kubectl apply -f (Join-Path $k8s "fusion-training-cpu-fallback-job.yaml") 2>$null
    & $Kubectl apply -f (Join-Path $k8s "fusion-training-tier1-single-l4-job.yaml") 2>$null
    & $Kubectl get job,pods -n fusion-training 2>$null
    Write-Ok "kubectl apply done"
} else { Write-Warn "skipped (-SkipGke)" }

Write-Step "4/7" "Local Dashboard :8000"
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'uvicorn app:app' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Process -FilePath (Join-Path $RepoRoot "run_backend.bat") -WorkingDirectory $RepoRoot -WindowStyle Minimized
$deadline = (Get-Date).AddSeconds(90)
$dashOk = $false
while ((Get-Date) -lt $deadline) {
    try {
        $h = Invoke-RestMethod "http://127.0.0.1:8000/api/health?light=true" -TimeoutSec 3
        if ($h) { $dashOk = $true; break }
    } catch {}
    Start-Sleep -Seconds 2
}
if ($dashOk) { Write-Ok "Dashboard health" } else { Write-Warn "Dashboard timeout" }

try {
    $e = Invoke-RestMethod "http://127.0.0.1:8000/api/mainframe/energy/status" -TimeoutSec 8
    $m = $e.subcontractor_pricing.margin_pct_applied_mode
    Write-Ok "Energy API ($m)"
} catch { Write-Warn "Energy API: $_" }

Write-Step "5/7" "Mainframe daemons"
& (Join-Path $RepoRoot "workstation\start_mainframe_daemons.ps1") 2>$null
Start-Sleep -Seconds 3
try {
    Invoke-RestMethod "http://127.0.0.1:8000/api/mainframe/energy/tick" -Method POST -TimeoutSec 15 | Out-Null
    Write-Ok "energy tick"
} catch { Write-Warn "energy tick: $_" }

Write-Step "6/7" "hero-docs :8088"
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'hero-docs-server' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1
$heroDocs = Join-Path $RepoRoot "hero-docs-server.py"
Start-Process $Python -ArgumentList $heroDocs -WorkingDirectory $RepoRoot -WindowStyle Hidden
Start-Sleep -Seconds 2
try {
    $hd = Invoke-RestMethod "http://127.0.0.1:8088/mainframe/ops/status" -TimeoutSec 8
    $hasEnergy = $null -ne $hd.energy
    Write-Ok "hero-docs mainframe ops energy=$hasEnergy"
} catch { Write-Warn "hero-docs: $_" }

Write-Step "7/7" "GCE sync + restart"
if (-not $SkipGce) {
    $remoteInstall = "/home/Admin/fusion-hero-core"
    $files = @(
        "hero-docs-server.py",
        "fractal_mainframe_mesh.py",
        "docs/business/senfkorn_businessplan.yaml",
        "03_Code/core/mainframe_energy_pricing_daemon.py",
        "03_Code/core/mainframe_cost_analysis_daemon.py",
        "03_Code/core/repo_mirror_correction_daemon.py",
        "03_Code/core/repo_structure_registry.py",
        "03_Code/Dashboard/business_plan_routes.py",
        "03_Code/Dashboard/mainframe_background.py",
        "03_Code/Dashboard/mainframe_ops_routes.py",
        "03_Code/Dashboard/static/mainframe_ops.js",
        "03_Code/Dashboard/templates/mainframe_ops.html"
    )
    foreach ($rel in $files) {
        $local = Join-Path $RepoRoot $rel
        if (-not (Test-Path $local)) { continue }
        $remote = "$remoteInstall/$($rel -replace '\\','/')"
        $remoteDir = ($remote -replace '/[^/]+$','')
        $mkCmd = "mkdir -p $remoteDir"
        gcloud compute ssh $Vm --zone=$Zone --project=$Project --command=$mkCmd 2>$null | Out-Null
        gcloud compute scp $local "${Vm}:${remote}" --zone=$Zone --project=$Project 2>$null
    }
    $bootstrap = "pip3 install -q numpy pyyaml; sudo mkdir -p /etc/systemd/system/fusion-hero-docs.service.d; printf '[Service]`nEnvironment=PYTHONPATH=/home/Admin/fusion-hero-core/03_Code:/home/Admin/fusion-hero-core`nEnvironment=FUSION_BUSINESSPLAN_PATH=/home/Admin/fusion-hero-core/docs/business/senfkorn_businessplan.yaml`n' | sudo tee /etc/systemd/system/fusion-hero-docs.service.d/override.conf >/dev/null; sudo systemctl daemon-reload; sudo fuser -k 8088/tcp 2>/dev/null; sudo systemctl reset-failed fusion-hero-docs; sudo systemctl restart fusion-hero-docs"
    gcloud compute ssh $Vm --zone=$Zone --project=$Project --command=$bootstrap 2>&1 | ForEach-Object { Write-Host "  $_" }
    Write-Ok "GCE sync + hero-docs restart"
} else { Write-Warn "skipped (-SkipGce)" }

Write-Step "8/8" "Fractal manifest replicate"
Push-Location $RepoRoot
& $Python fractal_mainframe_mesh.py save --replicate 2>&1 | Select-Object -Last 5 | ForEach-Object { Write-Host "  $_" }
Pop-Location

Write-Host ""
Write-Host "=== Deploy All abgeschlossen ===" -ForegroundColor Green
Write-Host "  Dashboard:  http://127.0.0.1:8000/mainframe/ops"
Write-Host "  Energy API: http://127.0.0.1:8000/api/mainframe/energy/pricing/subcontractor"
Write-Host "  hero-docs:  http://127.0.0.1:8088/mainframe/energy/status"
if (-not $NoGui) { Start-Process 'http://127.0.0.1:8000/mainframe/ops' }