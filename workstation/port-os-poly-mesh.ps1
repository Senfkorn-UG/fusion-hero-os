# port-os-poly-mesh.ps1 — Port Fusion Hero OS into poly-mesh
param(
    [switch]$Status,
    [switch]$NoServe,
    [switch]$NoCoordinator
)
$ErrorActionPreference = "Continue"
$Repo = if ($env:FUSION_REPO_ROOT) { $env:FUSION_REPO_ROOT } else {
    (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
$Py = if (Test-Path "C:\Users\Admin\venv\Scripts\python.exe") {
    "C:\Users\Admin\venv\Scripts\python.exe"
} else { "python" }
$env:PYTHONPATH = $Repo
$env:FUSION_HEADSET_MESH_ONLY = "1"
Push-Location $Repo
try {
    $a = @("scripts/port_os_poly_mesh.py")
    if ($Status) { $a += "--status" }
    if ($NoServe) { $a += "--no-serve" }
    if ($NoCoordinator) { $a += "--no-coordinator" }
    & $Py @a
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
