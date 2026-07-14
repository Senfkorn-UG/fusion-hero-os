#!/bin/bash
# Run FROM Google Cloud Shell to finish fusion-mesh-exit setup
# Usage: bash gce_cloudshell_bootstrap.sh
set -euo pipefail

PROJECT="project-bbf0e6db-52e1-462b-8e3"
ZONE="europe-west3-a"
VM="fusion-mesh-exit"

gcloud config set project "$PROJECT"

echo "=== 1) Tailscale login URL (open in browser, same account as desktop) ==="
gcloud compute ssh "$VM" --zone="$ZONE" --command \
  "sudo tailscale up --hostname=fusion-mesh-exit --accept-routes --advertise-exit-node --ssh 2>&1 || true; sudo tailscale status 2>&1 | head -6"

echo ""
echo "=== 2) Clone repo + hero-docs ==="
gcloud compute ssh "$VM" --zone="$ZONE" --command 'bash -s' <<'REMOTE'
set -euo pipefail
INSTALL_DIR="$HOME/fusion-hero-core"
REPO="https://github.com/95guknow/fusion-hero-os.git"
if [[ ! -d "$INSTALL_DIR/.git" ]]; then
  git clone --depth 1 "$REPO" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"
sudo pip3 install -q pyyaml 2>/dev/null || pip3 install --user pyyaml
mkdir -p "$HOME/.fusion/mesh/fractal/replicas"
sudo tee /etc/systemd/system/fusion-hero-docs.service >/dev/null <<EOF
[Unit]
Description=Fusion Hero Docs Server
After=network.target tailscaled.service
[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/hero-docs-server.py
Restart=on-failure
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now fusion-hero-docs
sleep 2
curl -fsS http://127.0.0.1:8088/status 2>/dev/null | head -c 80 || echo hero-docs_pending
REMOTE

echo ""
echo "=== 3) Status ==="
gcloud compute ssh "$VM" --zone="$ZONE" --command \
  "sudo tailscale ip -4 2>/dev/null; sudo systemctl is-active fusion-hero-docs; ls -la ~/fusion-hero-core/hero-docs-server.py 2>/dev/null"

echo ""
echo "Done. From desktop run: python mesh_cloud_backends.py flush-pending"