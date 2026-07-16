#!/bin/bash
set -euo pipefail
echo "=== diagnose exit $(date -Iseconds) ==="
tailscale status --json > /tmp/ts-status.json
python3 <<'PY'
import json
d=json.load(open("/tmp/ts-status.json"))
s=d.get("Self") or {}
print("HostName:", s.get("HostName"))
print("Online:", s.get("Online"))
print("ExitNode:", s.get("ExitNode"))
print("ExitNodeOption:", s.get("ExitNodeOption"))
print("AllowedIPs:", s.get("AllowedIPs"))
print("PrimaryRoutes:", s.get("PrimaryRoutes"))
print("Tags:", s.get("Tags"))
print("CapMap keys:", list((s.get("CapMap") or {}).keys())[:20])
# Peer view of ourselves doesn't exist; list who offers exit
print("--- peers with ExitNodeOption ---")
for p in (d.get("Peer") or {}).values():
    if p.get("ExitNodeOption") or p.get("ExitNode") or "exit" in str(p.get("AllowedIPs") or "").lower():
        print(p.get("HostName"), "ExitNodeOption=", p.get("ExitNodeOption"), "AllowedIPs=", p.get("AllowedIPs"))
print("--- any peer AllowedIPs with 0.0.0.0 ---")
for p in (d.get("Peer") or {}).values():
    aips=p.get("AllowedIPs") or []
    if any(x.startswith("0.0.0.0") or x=="::/0" for x in aips):
        print(p.get("HostName"), aips)
PY

echo "--- try force re-advertise with advertise-routes empty first? ---"
# Some TS versions: exit node = advertise 0.0.0.0/0 and ::/0 specifically
sudo tailscale set --advertise-exit-node=true
# Explicit default routes (exit node is these routes)
sudo tailscale set --advertise-routes=0.0.0.0/0,::/0,10.156.0.0/20 2>&1 || \
  sudo tailscale up --advertise-exit-node --advertise-routes=0.0.0.0/0,::/0,10.156.0.0/20 --hostname=fusion-mesh-exit --accept-routes --ssh 2>&1 || true

sleep 3
tailscale debug prefs > /tmp/ts-prefs2.json
python3 -c 'import json; p=json.load(open("/tmp/ts-prefs2.json")); print("AdvertiseRoutes", p.get("AdvertiseRoutes"))'
tailscale status --json > /tmp/ts-status2.json
python3 -c 'import json; s=json.load(open("/tmp/ts-status2.json")).get("Self") or {}; print("AllowedIPs", s.get("AllowedIPs")); print("ExitNodeOption", s.get("ExitNodeOption")); print("PrimaryRoutes", s.get("PrimaryRoutes"))'

echo "--- backend state ---"
# If AllowedIPs still only /32, control plane has NOT approved routes
python3 <<'PY'
import json
s=json.load(open("/tmp/ts-status2.json")).get("Self") or {}
aips=s.get("AllowedIPs") or []
if not any(x in ("0.0.0.0/0","::/0") or x.startswith("0.0.0.0/") for x in aips):
    print("DIAGNOSIS: Control plane has NOT approved exit routes yet.")
    print("ACTION: Admin UI -> fusion-mesh-exit -> ... menu or machine details")
    print("  -> Edit route settings")
    print("  -> Approve 0.0.0.0/0 and ::/0 (and Subnets if pending)")
    print("  Badge 'Exit Node' alone is not enough if routes still pending.")
else:
    print("DIAGNOSIS: Exit routes approved in netmap. Client should see ExitNodeOption soon.")
PY
echo DONE
