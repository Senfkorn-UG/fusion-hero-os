#!/bin/bash
# Deploy Fusion AI Tier-2 training (2x A100) on senfkorn-gke-cluster
# Run from Google Cloud Shell or any machine with gcloud + kubectl.
set -euo pipefail

PROJECT="project-bbf0e6db-52e1-462b-8e3"
REGION="europe-west3"
CLUSTER="senfkorn-gke-cluster"
BUCKET="fusion-ai-data-project-bbf0e6db-52e1-462b-8e3"
REPO_ROOT="${REPO_ROOT:-$HOME/fusion-hero-os}"

gcloud config set project "$PROJECT"

echo "=== 1) GCS bucket + training code ==="
if ! gcloud storage buckets describe "gs://${BUCKET}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${BUCKET}" \
    --location="$REGION" \
    --uniform-bucket-level-access
fi

mkdir -p /tmp/fusion-training-upload
cp "${REPO_ROOT}/03_Code/training/fusion_stability_train.py" /tmp/fusion-training-upload/
cp "${REPO_ROOT}/qb_qubo.py" /tmp/fusion-training-upload/
gcloud storage cp /tmp/fusion-training-upload/* "gs://${BUCKET}/training/"

echo "=== 2) Workload Identity service account ==="
SA="fusion-training-sa"
if ! gcloud iam service-accounts describe "${SA}@${PROJECT}.iam.gserviceaccount.com" >/dev/null 2>&1; then
  gcloud iam service-accounts create fusion-training-sa \
    --display-name="Fusion AI training workload (GKE)"
fi
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${SA}@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin" \
  --quiet >/dev/null
gcloud iam service-accounts add-iam-policy-binding "${SA}@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${PROJECT}.svc.id.goog[fusion-training/fusion-training-ksa]" \
  --quiet >/dev/null

echo "=== 3) GKE credentials ==="
gcloud container clusters get-credentials "$CLUSTER" --region="$REGION" --project="$PROJECT"

echo "=== 4) Apply Kubernetes manifests ==="
kubectl apply -f "${REPO_ROOT}/infra/k8s/fusion-training/namespace.yaml"
kubectl apply -f "${REPO_ROOT}/infra/k8s/fusion-training/serviceaccount.yaml"
kubectl delete job fusion-durability-train-tier2 -n fusion-training --ignore-not-found
kubectl apply -f "${REPO_ROOT}/infra/k8s/fusion-training/fusion-training-tier2-job.yaml"

echo "=== 5) Status ==="
kubectl get job,pods -n fusion-training -w &
WATCH_PID=$!
sleep 15
kill $WATCH_PID 2>/dev/null || true
kubectl describe job fusion-durability-train-tier2 -n fusion-training | tail -20

echo ""
echo "Done. Monitor: kubectl logs -n fusion-training -l app=fusion-training -f"
echo "Bucket: gs://${BUCKET}"
echo "Estimated Tier-2 cost: ~688 EUR for 72h full run (Autopilot bills per second while pods run)."