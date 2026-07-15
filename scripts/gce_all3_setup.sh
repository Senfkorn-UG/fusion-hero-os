#!/bin/bash
# GCE fusion-mesh-exit: (1) git pull (2) exit-node advertise (3) coordinator cron
set -euo pipefail
echo "=== gce_all3_setup $(date -Iseconds) ==="
CORE=/home/Admin/fusion-hero-core
PUB_BACKUP=/home/Admin/.fusion/publish/v10-backup-$(date +%Y%m%d%H%M%S)

# ---------------------------------------------------------------------------
# 1) git pull — preserve publish + local WIP
# ---------------------------------------------------------------------------
cd "$CORE"
echo "=== 1) GIT PULL ==="
git status -sb || true
# backup publish tree (tracked or not)
if [[ -d docs/publish/v10 ]]; then
  mkdir -p "$PUB_BACKUP"
  cp -a docs/publish/v10/. "$PUB_BACKUP/" || true
  echo "backed up publish to $PUB_BACKUP"
fi
# stash tracked modifications
git stash push -u -m "gce-wip-before-pull-$(date +%Y%m%d%H%M%S)" || true
git fetch origin main
git checkout main
# prefer reset to origin if diverged after stash (clean main)
git pull --ff-only origin main || {
  echo "ff-only failed — trying merge"
  git pull origin main || true
}
echo "HEAD=$(git rev-parse --short HEAD) $(git log -1 --oneline)"
# restore publish assets
mkdir -p docs/publish/v10
if [[ -d "$PUB_BACKUP" ]]; then
  cp -a "$PUB_BACKUP"/. docs/publish/v10/ || true
fi
# re-fetch releases if missing
cd docs/publish/v10
base=https://github.com/95guknow/fusion-hero-os/releases/download
for path in \
  dissertation-v1.0/Dissertation_Stephan_Hagen_Urban_Autopoiesis_Autopolitik_Fusion_Hero_OS_v1.0.pdf \
  geisteskrankheiten-4d-v10.0.0/Geisteskrankheiten_4D_Matrix_v10.0.0_Kompendium.pdf \
  heroische-mathematik-v10.0.0/Heroische_Mathematik_Formale_Herleitung_v10.0.0.pdf
do
  f=$(basename "$path")
  [[ -f "$f" ]] || curl -fsSL -o "$f" "$base/$path" || echo "fail $f"
done
# index if missing
if [[ ! -f index.html ]]; then
  cat > index.html <<'HTML'
<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><title>Fusion v10 Publish</title></head>
<body><h1>Fusion Hero OS · GCE publish v10</h1>
<ul>
<li><a href="Dissertation_Stephan_Hagen_Urban_Autopoiesis_Autopolitik_Fusion_Hero_OS_v1.0.pdf">Dissertation</a></li>
<li><a href="Geisteskrankheiten_4D_Matrix_v10.0.0_Kompendium.pdf">Geisteskrankheiten 4D</a></li>
<li><a href="Heroische_Mathematik_Formale_Herleitung_v10.0.0.pdf">Heroische Mathematik</a></li>
</ul></body></html>
HTML
fi
ls -lah
cd "$CORE"
# ensure hero-docs-server still running
if ! ss -ltn | grep -q ':8088'; then
  nohup python3 hero-docs-server.py > /home/Admin/.fusion/hero-docs.log 2>&1 &
  echo "restarted hero-docs-server pid=$!"
  sleep 1
fi
ss -ltn | grep 8088 || true

# ---------------------------------------------------------------------------
# 2) Exit node advertise
# ---------------------------------------------------------------------------
echo "=== 2) EXIT NODE ==="
if command -v tailscale >/dev/null 2>&1; then
  # advertise exit node without resetting auth if possible
  sudo tailscale set --advertise-exit-node=true 2>/dev/null \
    || sudo tailscale up --advertise-exit-node --accept-routes --hostname=fusion-mesh-exit 2>/dev/null \
    || true
  echo "tailscale status (self):"
  tailscale status --self=true 2>/dev/null || tailscale status | head -5
  # show prefs if available
  tailscale debug prefs 2>/dev/null | head -40 || true
  echo "NOTE: Admin must approve exit node in Tailscale admin console if not already."
else
  echo "tailscale not installed"
fi

# ---------------------------------------------------------------------------
# 3) Coordinator cron (every 30 min)
# ---------------------------------------------------------------------------
echo "=== 3) COORDINATOR CRON ==="
# deps
python3 -m pip install --user pyyaml -q 2>/dev/null || pip3 install --user pyyaml -q || true
mkdir -p /home/Admin/.fusion/mesh/coordination /home/Admin/.fusion/logs
COORD="$CORE/scripts/mesh_cluster_coordinator.py"
if [[ ! -f "$COORD" ]]; then
  # fallback download raw from github
  mkdir -p "$CORE/scripts"
  curl -fsSL -o "$COORD" \
    https://raw.githubusercontent.com/95guknow/fusion-hero-os/main/scripts/mesh_cluster_coordinator.py || true
  curl -fsSL -o "$CORE/mesh_service_coordination.yaml" \
    https://raw.githubusercontent.com/95guknow/fusion-hero-os/main/mesh_service_coordination.yaml || true
fi

# wrapper
cat > /home/Admin/bin/fusion-coord.sh <<'WRAP'
#!/bin/bash
set -euo pipefail
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:$PATH"
CORE=/home/Admin/fusion-hero-core
LOG=$HOME/.fusion/logs/coordinator.log
mkdir -p "$(dirname "$LOG")"
cd "$CORE"
{
  echo "==== $(date -Iseconds) ===="
  python3 scripts/mesh_cluster_coordinator.py --mode all 2>&1 || echo "coord_exit=$?"
} >> "$LOG" 2>&1
# keep log small
if [[ -f "$LOG" ]] && [[ $(stat -c%s "$LOG" 2>/dev/null || echo 0) -gt 2000000 ]]; then
  tail -c 500000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi
WRAP
mkdir -p /home/Admin/bin
chmod +x /home/Admin/bin/fusion-coord.sh

# install crontab entry (user Admin)
CRON_LINE="*/30 * * * * /home/Admin/bin/fusion-coord.sh"
(crontab -l 2>/dev/null | grep -v fusion-coord.sh || true; echo "$CRON_LINE") | crontab -
echo "crontab:"
crontab -l

# run once now
bash /home/Admin/bin/fusion-coord.sh || true
echo "latest coordination:"
ls -la /home/Admin/.fusion/mesh/coordination/ 2>/dev/null || true
if [[ -f /home/Admin/.fusion/mesh/coordination/latest.json ]]; then
  python3 -c "import json; d=json.load(open('/home/Admin/.fusion/mesh/coordination/latest.json')); print({k:d.get(k) for k in ('mode','generated_at')}); print('inventory_ok', (d.get('inventory') or {}).get('ok')); print('tiers', (d.get('plan') or {}).get('online_tiers')); print('drift', (d.get('atlas') or {}).get('drift_score'))" 2>/dev/null || head -c 400 /home/Admin/.fusion/mesh/coordination/latest.json
fi

echo "=== ALL3 DONE ==="
