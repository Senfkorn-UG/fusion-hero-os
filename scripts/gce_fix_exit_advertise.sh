#!/bin/bash
# Force fusion-mesh-exit to advertise as exit node properly
set -euo pipefail
echo "=== fix exit advertise $(date -Iseconds) ==="

# IP forwarding (required for exit node)
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.ipv6.conf.all.forwarding=1
# persist
if ! grep -q 'net.ipv4.ip_forward=1' /etc/sysctl.d/99-tailscale.conf 2>/dev/null; then
  echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-tailscale.conf
  echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
  sudo sysctl --system >/dev/null 2>&1 || true
fi

# Prefer set (keeps login); fall back to up without --reset
echo "--- advertise via set ---"
sudo tailscale set --advertise-exit-node=true 2>&1 || true
sudo tailscale set --advertise-routes=10.156.0.0/20 2>&1 || true

# Some versions need explicit re-up without reset
echo "--- advertise via up (no reset) ---"
sudo tailscale up \
  --advertise-exit-node \
  --advertise-routes=10.156.0.0/20 \
  --accept-routes \
  --hostname=fusion-mesh-exit \
  --ssh 2>&1 || true

sleep 2
echo "--- prefs ---"
tailscale debug prefs > /tmp/ts-prefs.json
python3 -c 'import json; p=json.load(open("/tmp/ts-prefs.json")); print("AdvertiseRoutes:", p.get("AdvertiseRoutes")); print("Hostname:", p.get("Hostname")); print("WantRunning:", p.get("WantRunning")); print("RouteAll:", p.get("RouteAll"))'

echo "--- status ---"
tailscale status

# Show if we're offering exit in local status line
if tailscale status --json 2>/dev/null | python3 -c '
import sys,json
d=json.load(sys.stdin)
s=d.get("Self") or {}
print("Self.ExitNodeOption", s.get("ExitNodeOption"))
print("Self.AllowedIPs", s.get("AllowedIPs"))
print("Self.PrimaryRoutes", s.get("PrimaryRoutes"))
print("Self.HostName", s.get("HostName") or s.get("DNSName"))
' 2>/dev/null; then
  true
fi

echo "DONE — if client still says not advertising: re-approve Exit Node + Subnets in admin UI"
