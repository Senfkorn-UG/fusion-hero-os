# Senfkorn UG — Fusion Hero OS production image (europe-west3)
# FastAPI dashboard + Numba/NumPy + Qdrant client + energy/cost daemons
FROM python:3.11-slim

LABEL org.opencontainers.image.title="Fusion Hero OS"
LABEL org.opencontainers.image.version="10.0.0"
LABEL org.opencontainers.image.vendor="Senfkorn UG (haftungsbeschraenkt)"
LABEL org.opencontainers.image.description="Mainframe dashboard + energy pricing (europe-west3)"

# GCC toolchain for numba/numpy wheels that need compile fallbacks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Persistent daemon state (audit trail under FUSION_STATE_DIR)
RUN mkdir -p /root/.fusion-hero-os/mainframe_energy_pricing \
    && mkdir -p /root/.fusion-hero-os/mainframe_cost_analysis

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Full repo context (Dashboard imports core via PYTHONPATH=/app/03_Code)
COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/03_Code:/app \
    FUSION_STATE_DIR=/root/.fusion-hero-os \
    FUSION_BUSINESSPLAN_PATH=/app/docs/business/senfkorn_businessplan.yaml \
    FUSION_ENERGY_PRICING_INTERVAL_SEC=60 \
    FUSION_AUTO_LOAD=0 \
    FUSION_PROFILE=docker

EXPOSE 8000

# Module path: 03_Code/Dashboard/app.py with PYTHONPATH including 03_Code
WORKDIR /app/03_Code/Dashboard
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
