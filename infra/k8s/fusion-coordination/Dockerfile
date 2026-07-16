# Fusion Hero OS — mesh/service coordination image (GKE L3 CronJob)
# Platform: v10.0.0 · slim, no dashboard/GPU
# Build (Cloud Build from repo root):
#   gcloud builds submit --config=infra/k8s/fusion-coordination/cloudbuild.yaml .

FROM python:3.11-slim

LABEL org.opencontainers.image.title="Fusion Hero OS Coordination"
LABEL org.opencontainers.image.version="10.0.0"
LABEL org.opencontainers.image.vendor="Senfkorn UG (haftungsbeschraenkt)"
LABEL org.opencontainers.image.description="mesh_cluster_coordinator + catalog for GKE Autopilot"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    FUSION_PLATFORM_VERSION=10.0.0 \
    FUSION_OPERATIVE_KANON=v10.0.0 \
    FUSION_HOME=/var/fusion \
    HOME=/var/fusion

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/fusion/.fusion/mesh/coordination \
    && useradd --system --uid 10001 --home-dir /var/fusion --shell /usr/sbin/nologin fusion \
    && chown -R fusion:fusion /var/fusion

COPY infra/k8s/fusion-coordination/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Coordinator + catalog + minimal core for plan/race_guard (no full monorepo)
COPY scripts/mesh_cluster_coordinator.py /app/scripts/mesh_cluster_coordinator.py
COPY mesh_service_coordination.yaml /app/mesh_service_coordination.yaml
COPY mesh_connectors.yaml /app/mesh_connectors.yaml
COPY fusion_hero_os/__init__.py /app/fusion_hero_os/__init__.py
COPY fusion_hero_os/core/__init__.py /app/fusion_hero_os/core/__init__.py
COPY fusion_hero_os/core/race_guard.py /app/fusion_hero_os/core/race_guard.py
COPY fusion_hero_os/core/poly_mesh_router.py /app/fusion_hero_os/core/poly_mesh_router.py

# Script expects ROOT = parents[1] of scripts/ → /app
RUN chown -R fusion:fusion /app

USER fusion

# Default: full cycle + GCS upload (prefix via env)
ENTRYPOINT ["python", "/app/scripts/mesh_cluster_coordinator.py"]
CMD ["--mode", "all", "--upload-gcs", "--catalog", "/app/mesh_service_coordination.yaml"]
