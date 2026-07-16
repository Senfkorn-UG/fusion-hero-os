#!/usr/bin/env bash
# Senfkorn UG — automated Docker deploy on GCE (europe-west3)
# Usage (Cloud Shell or VM):
#   bash workstation/gce_docker_deploy_senfkorn.sh
# Optional env:
#   PROJECT_ID, ZONE (default europe-west3-a), VM_NAME, ALLOW_CIDR (default 0.0.0.0/0)

set -euo pipefail

REGION="${REGION:-europe-west3}"
ZONE="${ZONE:-europe-west3-a}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
VM_NAME="${VM_NAME:-fusion-mesh-exit}"
FW_RULE="${FW_RULE:-allow-fusion-dashboard-8000}"
ALLOW_CIDR="${ALLOW_CIDR:-0.0.0.0/0}"
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"

echo "=== Senfkorn / Fusion Hero OS Docker deploy ==="
echo "project=${PROJECT_ID:-unset} region=${REGION} zone=${ZONE} vm=${VM_NAME}"
echo "repo=${REPO_DIR}"

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "ERROR: set PROJECT_ID or gcloud config set project <id>"
  exit 1
fi

gcloud config set project "${PROJECT_ID}" >/dev/null

# Firewall: TCP 8000 for dashboard (idempotent)
if gcloud compute firewall-rules describe "${FW_RULE}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "[fw] rule ${FW_RULE} already exists"
else
  echo "[fw] creating ${FW_RULE} (tcp:8000 from ${ALLOW_CIDR}) region context ${REGION}"
  gcloud compute firewall-rules create "${FW_RULE}" \
    --project="${PROJECT_ID}" \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:8000 \
    --source-ranges="${ALLOW_CIDR}" \
    --description="Fusion Hero OS dashboard (Senfkorn UG) europe-west3"
fi

# Docker + compose on target (local if already on VM; else remote via SSH)
install_docker() {
  if command -v docker >/dev/null 2>&1; then
    echo "[docker] present: $(docker --version)"
  else
    echo "[docker] installing..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "${USER}" || true
  fi
  if docker compose version >/dev/null 2>&1; then
    echo "[compose] present"
  else
    echo "[compose] plugin missing — install docker compose plugin for your distro"
    exit 1
  fi
}

deploy_stack() {
  cd "${REPO_DIR}"
  install_docker
  echo "[compose] building and starting..."
  docker compose up --build -d
  echo "[compose] status:"
  docker compose ps
  echo "[health] light probe:"
  sleep 5
  curl -fsS "http://127.0.0.1:8000/api/health?light=true" || true
  echo
  echo "Done. Dashboard: http://<VM_EXTERNAL_IP>:8000"
  echo "Energy audit: volume fusion_state_data → /root/.fusion-hero-os/mainframe_energy_pricing/history.jsonl"
}

# If REPO_DIR is this machine, deploy locally (run on the GCE VM itself)
deploy_stack
