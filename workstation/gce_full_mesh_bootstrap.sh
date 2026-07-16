#!/bin/bash
# Full mesh leaf bootstrap for fusion-mesh-exit (GCE)
# Run on VM: bash gce_full_mesh_bootstrap.sh
# Or: gcloud compute ssh fusion-mesh-exit --zone=europe-west3-a --command="curl -fsSL ... | bash"
set -euo pipefail

REPO_URL="${FUSION_REPO_URL:-https://github.com/95guknow/fusion-hero-os.git}"
INSTALL_DIR="${FUSION_INSTALL_DIR:-/home/$USER/fusion-hero-core}"
HOSTNAME="${FUSION_TS_HOSTNAME:-fusion-mesh-exit}"
LOG=/var/log/fusion-mesh-bootstrap.log

exec > >(tee -a "$LOG") 2>&1
echo "=== Fusion full mesh bootstrap $(date -Iseconds) ==="

export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -y
sudo apt-get install -y curl git python3 python3-pip ca-certificates

# Tailscale
if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi
sudo systemctl enable --now tailscaled

TS_KEY="${TS_AUTHKEY:-}"
if [[ -z "$TS_KEY" ]]; then
  TS_KEY="$(curl -fsS -H "Metadata-Flavor: Google" \
    http://metadata.google.internal/computeMetadata/v1/instance/attributes/ts-authkey 2>/dev/null || true)"
fi

if [[ -n "$TS_KEY" && "$TS_KEY" != "unset" ]]; then
  sudo tailscale up --reset \
    --auth-key="$TS_KEY" \
    --hostname="$HOSTNAME" \
    --accept-routes \
    --advertise-exit-node \
    --ssh
  echo "Tailscale joined with auth key as $HOSTNAME"
else
  echo "No TS_AUTHKEY — run: sudo tailscale up --hostname=$HOSTNAME --advertise-exit-node --ssh"
  sudo tailscale up --hostname="$HOSTNAME" --accept-routes --advertise-exit-node --ssh 2>&1 || true
fi

sudo tailscale status || true

# Clone fusion-hero-os
if [[ ! -d "$INSTALL_DIR/.git" ]]; then
  git clone "$REPO_URL" "$INSTALL_DIR" || git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"
git pull --ff-only origin main 2>/dev/null || true

python3 -m pip install --user pyyaml 2>/dev/null || sudo pip3 install pyyaml

mkdir -p "$HOME/.fusion/mesh/fractal/replicas"

# hero-docs systemd service
sudo tee /etc/systemd/system/fusion-hero-docs.service >/dev/null <<EOF
[Unit]
Description=Fusion Hero Docs Server (mesh fractal replica)
After=network.target tailscaled.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/hero-docs-server.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable fusion-hero-docs
sudo systemctl restart fusion-hero-docs || sudo systemctl start fusion-hero-docs

sleep 2
curl -fsS http://127.0.0.1:8088/mesh/fractal/status 2>/dev/null | head -c 200 || echo "hero-docs starting..."

echo "Bootstrap complete. Install dir: $INSTALL_DIR"
echo "Tailscale: $(sudo tailscale ip -4 2>/dev/null || echo pending)"