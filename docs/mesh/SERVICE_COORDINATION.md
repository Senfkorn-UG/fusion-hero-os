# Service & Structure Coordination (Cluster-backed)

**Stand:** 2026-07-15 · Fusion Hero OS v10.0.0  
**Catalog:** `mesh_service_coordination.yaml`  
**Engine:** `scripts/mesh_cluster_coordinator.py`  
**Cluster:** `infra/k8s/fusion-coordination/` · GKE `senfkorn-gke-cluster` (europe-west3)

**Dissertation-as-OS:** Placement (L0–L4), Inhouse-Wahrheit und SaaS-Membranen sind **Autopolitik der Dissertation** — das OS *ist* die Arbeit; Koordination ist ihr Organsystem. Siehe `docs/dissertation/ONTOLOGIE_DISSERTATION_IST_DAS_OS.md`.

## Problem

Externe Dienste (Tailscale, GKE, GCS, Supabase, MCP-SaaS) und Inhouse-Lösungen (Dashboard, Fractal Mesh, QUBO, Orchestrator) liefen parallel, ohne gemeinsame Placement-Wahrheit. Cluster-Rechenzeit wurde fast nur für Training genutzt, nicht für Koordination.

## Lösung (kurz)

1. **Ein Katalog** trennt `inhouse` / `external` und mappt jedes Capability auf eine **Placement-Tier** (L0 Edge → L3 Cluster → L4 SaaS).
2. **Routing-Regeln** entscheiden, wo Arbeit läuft (MCP bleibt auf dem Mainframe; schwere Scans/Training auf GKE).
3. **Coordinator** erzeugt Inventar + Placement-Plan (+ Atlas-Drift) und speichert unter `~/.fusion/mesh/coordination/`.
4. **GKE CronJob** (optional) verbrennt günstige Autopilot-CPU alle 30 min für Plan-Refresh und GCS-Snapshot.

## Live-Topology (Rollen)

| Live-Host | Rolle | Tier |
|-----------|--------|------|
| `desktop-kpki9e4` | mainframe / orchestrator | L1 |
| `desktop-kpki9e4-wsl` | optional dev leaf | L1 |
| `fusion-mesh-exit` | mesh anchor / exit | L2 |
| `redmi-note-13-pro-5g` | phone enduser | L0 |
| `cs-*` | ephemeral cloud shell | **nicht** durable |
| `senfkorn-gke-cluster` | Autopilot compute | L3 |

## Was läuft wo

| Capability | Placement | Begründung |
|------------|-----------|------------|
| Dashboard, MCP, Consent, Grok-CLI | L1 Mainframe | OAuth/Session + niedrige Latenz |
| Fractal replica / exit health | L2 mesh-exit | Desktop darf schlafen |
| Training, large QUBO, inventory atlas | L3 GKE | teure CPU/GPU auslagern |
| GitHub/Gmail/Drive/Canva/… | L4 SaaS via L1 MCP | SaaS nie Source-of-Truth |
| MasterSeed / Integrity hashes | nur Inhouse | Anti-Pattern `saas-as-source-of-truth` |

## Lokal ausführen

```powershell
cd C:\Users\Admin\fusion-hero-os
pip install pyyaml
python scripts\mesh_cluster_coordinator.py --mode all
# optional:
python scripts\mesh_cluster_coordinator.py --mode plan --upload-gcs
```

Ausgabe: `~/.fusion/mesh/coordination/latest.json`

## Cluster aktivieren (wenn kubectl + WI stehen)

```bash
# kubectl im PATH (Cloud SDK bin) + gcloud container clusters get-credentials ...
kubectl apply -f infra/k8s/fusion-coordination/namespace.yaml
# Image/WI/PROJECT_ID in CronJob ersetzen, dann:
kubectl apply -f infra/k8s/fusion-coordination/coordination-cronjob.yaml
```

Bis das Image gebaut ist: **lokaler Coordinator** ist die operative Quelle; CronJob-Manifest ist vorbereitet.

## Anti-Patterns

- Durable Jobs auf Cloud-Shell-Nodes
- MCP-Connectors im Cluster (keine Desktop-OAuth-Sessions)
- Supabase/Drive als einzige Wahrheit für Fractal-Anchors
- Routing blockieren, weil WSL offline ist

## Verwandte Dateien

- `mesh_connectors.yaml` — Mesh-Segment-Registry
- `fusion_unified.yaml` — Layer-Graph
- `mesh_cloud_backends.py` — Supabase / Drive / GCE
- `infra/k8s/fusion-training/` — schwere Trainingsjobs
- `infra/terraform/senfkorn-fusion-stack/` — GCS + Workload Identity
