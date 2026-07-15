#!/bin/bash
set -euo pipefail
mkdir -p /home/Admin/bin /home/Admin/.fusion/logs /home/Admin/.fusion/mesh/coordination
python3 -m pip install --user pyyaml -q || true

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
WRAP
chmod +x /home/Admin/bin/fusion-coord.sh

(crontab -l 2>/dev/null | grep -v fusion-coord.sh || true; echo '*/30 * * * * /home/Admin/bin/fusion-coord.sh') | crontab -
echo "CRONTAB:"
crontab -l

bash /home/Admin/bin/fusion-coord.sh || true
echo "COORD DIR:"
ls -la /home/Admin/.fusion/mesh/coordination/ || true
if [[ -f /home/Admin/.fusion/mesh/coordination/latest.json ]]; then
  python3 - <<'PY'
import json
d=json.load(open("/home/Admin/.fusion/mesh/coordination/latest.json"))
print("inventory_ok", (d.get("inventory") or {}).get("ok"))
print("tiers", (d.get("plan") or {}).get("online_tiers"))
print("drift", (d.get("atlas") or {}).get("drift_score"))
print("matched", len((d.get("inventory") or {}).get("matched_roles") or []))
PY
fi

echo "GIT:"
git -C /home/Admin/fusion-hero-core log -1 --oneline
echo "EXIT ADVERTISE:"
tailscale debug prefs 2>/dev/null | python3 -c 'import sys,json; p=json.load(sys.stdin); print(p.get("AdvertiseRoutes")); print(p.get("Hostname"))' || true
echo "PUBLISH:"
curl -fsS -o /dev/null -w "http=%{http_code}\n" http://127.0.0.1:8088/docs/publish/v10/ || true
echo DONE
