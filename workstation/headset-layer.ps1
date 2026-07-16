# headset-layer.ps1 - Multi-layer headset with LOUD active-level banner
# Usage:
#   powershell -File workstation\headset-layer.ps1
#   powershell -File workstation\headset-layer.ps1 -Active L2
#   powershell -File workstation\headset-layer.ps1 -Active L3
#   powershell -File workstation\headset-layer.ps1 -Active local
#   powershell -File workstation\headset-layer.ps1 -Stack
#   powershell -File workstation\headset-layer.ps1 -Status

param(
    [string]$Active = "",
    [switch]$Stack,
    [switch]$Status,
    [switch]$Apply
)

$ErrorActionPreference = "Continue"
$Repo = if ($env:FUSION_REPO_ROOT) { $env:FUSION_REPO_ROOT } else { "C:\Users\Admin\fusion-hero-os" }
$Py = if (Test-Path "C:\Users\Admin\venv\Scripts\python.exe") {
    "C:\Users\Admin\venv\Scripts\python.exe"
} else { "python" }

$env:PYTHONPATH = $Repo
Push-Location $Repo
try {
    $args = @("-m", "fusion_hero_os.core.headset_layers")
    if ($Stack) {
        $args += "--stack"
    } elseif ($Active) {
        $args += @("--active", $Active)
    } elseif ($Apply) {
        $args += "--apply"
    } else {
        $args += "--status"
    }
    & $Py @args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
