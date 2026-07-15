#!/bin/bash
set -euo pipefail
echo "=== exit node check $(date -Iseconds) ==="
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.ipv6.conf.all.forwarding=1
# re-assert advertise
sudo tailscale set --advertise-exit-node=true || sudo tailscale set --advertise-exit-node || true
sleep 2
echo "--- prefs AdvertiseRoutes ---"
tailscale debug prefs | python3 -c 'import sys,json; p=json.load(sys.stdin); print(p.get("AdvertiseRoutes")); print("hostname", p.get("Hostname"))'
echo "--- status ---"
tailscale status
echo "--- ip ---"
tailscale ip -4
echo DONE
