# OS-level Mainframe Daemons (Kostenanalyse + Energie/Preise + Repo-Spiegelung/Korrektur)
# Läuft ohne Mauseingabe — nur Spiegelung + automatische Korrektur auf Dateisystem-Ebene.
param(
    [int]$CostIntervalSec = 60,
    [int]$EnergyIntervalSec = 60,
    [int]$MirrorIntervalSec = 45,
    [switch]$NoAutoCorrect
)

$ErrorActionPreference = "Stop"
$RepoRoot = if ($env:FUSION_REPO_ROOT) { $env:FUSION_REPO_ROOT } else { "C:\Users\Admin\fusion-hero-os" }
$Dashboard = Join-Path $RepoRoot "03_Code\Dashboard"

$env:FUSION_REPO_ROOT = $RepoRoot
$env:FUSION_COST_ANALYSIS_INTERVAL_SEC = "$CostIntervalSec"
$env:FUSION_ENERGY_PRICING_INTERVAL_SEC = "$EnergyIntervalSec"
$env:FUSION_BUSINESSPLAN_PATH = Join-Path $RepoRoot "docs\business\senfkorn_businessplan.yaml"
$env:FUSION_REPO_MIRROR_INTERVAL_SEC = "$MirrorIntervalSec"
$env:FUSION_REPO_MIRROR_AUTO_CORRECT = if ($NoAutoCorrect) { "0" } else { "1" }
$env:PYTHONPATH = "$RepoRoot\03_Code;$RepoRoot"

$daemonScript = @"
import os, sys, time
sys.path.insert(0, os.path.join(r'$RepoRoot', '03_Code'))
from core.mainframe_cost_analysis_daemon import get_cost_daemon
from core.mainframe_energy_pricing_daemon import get_energy_daemon
from core.repo_mirror_correction_daemon import get_mirror_daemon

cost = get_cost_daemon()
energy = get_energy_daemon()
mirror = get_mirror_daemon()
cost.start_background()
energy.start_background()
mirror.start_background()
ci = int(os.getenv('FUSION_COST_ANALYSIS_INTERVAL_SEC', '60'))
ei = int(os.getenv('FUSION_ENERGY_PRICING_INTERVAL_SEC', '60'))
mi = int(os.getenv('FUSION_REPO_MIRROR_INTERVAL_SEC', '45'))
print('[mainframe-daemon] cost + energy + repo mirror started', flush=True)
while cost._running and energy._running and mirror._running:
    try:
        cost.tick()
    except Exception as e:
        print('[cost]', e, flush=True)
    try:
        energy.tick()
    except Exception as e:
        print('[energy]', e, flush=True)
    try:
        mirror.tick()
    except Exception as e:
        print('[mirror]', e, flush=True)
    time.sleep(min(ci, ei, mi))
"@

$scriptPath = Join-Path $env:TEMP "fusion_mainframe_daemon.py"
Set-Content -Path $scriptPath -Value $daemonScript -Encoding UTF8

$existing = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*fusion_mainframe_daemon.py*" }
if ($existing) {
    Write-Host "Mainframe daemon already running (PID $($existing.ProcessId))"
    exit 0
}

Start-Process python -ArgumentList $scriptPath -WindowStyle Hidden -WorkingDirectory $Dashboard
Write-Host "Mainframe OS daemons gestartet (Kosten ${CostIntervalSec}s, Energie ${EnergyIntervalSec}s, Mirror ${MirrorIntervalSec}s)"
Write-Host "Dashboard: http://127.0.0.1:8000/mainframe/ops"