# run-local-infrastructure-kernel.ps1 - Lokale Kernlogik: Probing / Schwellen / Eskalation
param(
    [switch]$ProbeOnly,
    [switch]$StatusOnly,
    [switch]$ApplyActions,
    [double]$Timeout = 4.0
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Root = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$CoreDir = Join-Path $Root "src\normal_os\core"
$Module = Join-Path $CoreDir "local_infrastructure_kernel.py"
$StatusFile = Join-Path $env:USERPROFILE ".fusion\local-infrastructure-kernel\status.json"
$Contract = Join-Path $PSScriptRoot "contracts\local_infrastructure_kernel.v1.json"

if (-not (Test-Path $Module)) {
    $fail = @{
        available = $false
        reason    = "nicht verfuegbar"
        module    = "local_infrastructure_kernel"
        error     = "module file missing: $Module"
    } | ConvertTo-Json -Depth 6
    Write-Output $fail
    exit 1
}

$env:PYTHONPATH = $CoreDir
$py = if ($env:FUSION_PYTHON) { $env:FUSION_PYTHON } else { "python" }

$argsList = @()
if ($StatusOnly) {
    $argsList += "--status"
} elseif ($ProbeOnly) {
    $argsList += "--probe"
} else {
    $argsList += "--run-cycle"
}
if ($ApplyActions) { $argsList += "--apply-actions" }
$argsList += @("--timeout", $Timeout)

& $py $Module @argsList
$code = $LASTEXITCODE
if ($code -ne 0) { exit $code }

if (-not $StatusOnly -and -not $ProbeOnly) {
    Write-Host "Status: $StatusFile" -ForegroundColor DarkGray
    Write-Host "Contract: $Contract" -ForegroundColor DarkGray
}
