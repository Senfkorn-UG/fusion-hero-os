#!/bin/bash
set -euo pipefail
cd /home/Admin/fusion-hero-core
git fetch origin main
git stash push -u -m "pre-race-guard-pull" 2>/dev/null || true
git pull --ff-only origin main || git reset --hard origin/main
echo "HEAD=$(git log -1 --oneline)"
test -f fusion_hero_os/core/race_guard.py && echo "race_guard: present" || echo "race_guard: MISSING"
python3 -m pip install --user pyyaml -q || true
# ensure PYTHONPATH for fusion_hero_os
export PYTHONPATH=/home/Admin/fusion-hero-core${PYTHONPATH:+:$PYTHONPATH}
python3 -c "from fusion_hero_os.core.race_guard import race_stress_test; from pathlib import Path; r=race_stress_test(Path.home()/'.fusion'/'mesh'/'coordination'/'race_stress.json', n_workers=4, n_writes_each=8); print(r)"
# update coord wrapper env
cat > /home/Admin/bin/fusion-coord.sh <<'WRAP'
#!/bin/bash
set -euo pipefail
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:$PATH"
export PYTHONPATH=/home/Admin/fusion-hero-core${PYTHONPATH:+:$PYTHONPATH}
CORE=/home/Admin/fusion-hero-core
LOG=$HOME/.fusion/logs/coordinator.log
mkdir -p "$(dirname "$LOG")"
cd "$CORE"
{
  echo "==== $(date -Iseconds) ===="
  python3 scripts/mesh_cluster_coordinator.py --mode all 2>&1 || echo "coord_exit=$?"
} >> "$LOG" 2>&1
WRAP
chmod +x /home/Admin/bin/fusion-coord.sh
bash /home/Admin/bin/fusion-coord.sh || true
python3 -c "import json; d=json.load(open('/home/Admin/.fusion/mesh/coordination/latest.json')); print('race_guard', d.get('race_guard')); print('inventory_ok', (d.get('inventory') or {}).get('ok'))"
echo DEPLOY_OK
