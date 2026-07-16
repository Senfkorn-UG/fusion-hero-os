# Cluster-Routing — einzige Autorität (kein Dual-Start)

## Bug (vorher)

`mesh_cluster_coordinator.plan()` wählte bei Kandidaten `[L1, L3]` **immer L1 zuerst**.  
L3 galt schon als online, sobald nur `~/.kube/config` existierte — **ohne** Ready-Nodes.

Folge: schwere Jobs wirkten „ready“ lokal, obwohl sie ins Cluster sollten.

## Fix (allein gebaut, konfliktfrei)

| Komponente | Rolle |
|------------|--------|
| `fusion_hero_os/core/poly_mesh_router.py` | **Sole authority** für Placement |
| GKE-Probe | `kubectl get nodes` → Ready ≥ 1 |
| Prefer high tier | L3 > L2 > L1 unter online candidates |
| `force_cluster` | Training/QUBO: **kein** stiller L1-Fallback |
| Coordinator | `plan()` delegiert an Router |

## Live-Beweis (Cluster)

```text
kubectl apply -f infra/k8s/fusion-coordination/poly-mesh-router-proof-job.yaml
# Pod scheduled on gk3-senfkorn-gke-cluster-pool-1-...
# logs: poly_mesh_router_proof=ok  tier=L3_cluster
```

Stuck GPU-Job (`fusion-durability-train-tier1`, L4-Quota/Pending 23h) **gelöscht** — verursachte Autoscaler-Konflikte.

## CLI

```powershell
$env:PATH = "$env:USERPROFILE\.fusion\bin;$env:PATH"
python -m fusion_hero_os.core.poly_mesh_router --probe-gke
python -m fusion_hero_os.core.poly_mesh_router --route-all
python -m fusion_hero_os.core.poly_mesh_router --assert-local fusion-stability-train
# exit 2 = local forbidden → must use cluster Job
python scripts\mesh_cluster_coordinator.py --mode plan
```

## Routing-Beispiel (GKE live)

| Capability | Placement |
|------------|-----------|
| fusion-dashboard | L1_mainframe |
| qubo-anneal | **L3_cluster** (force) |
| fusion-stability-train | **L3_cluster** (force) |
| academia-curriculum-train | **L3_cluster** (force) |

## Policy

- Kein Dual-Start: wer `force_cluster` hat, startet **nicht** parallel lokal.
- GPU-Jobs nur wenn Quota/Node da; sonst CPU-Fallback-Job oder **blocked** — nicht heimlich Mainframe.
- Comädchen / Secrets bleiben L1.

**Vermerk:** Router allein · Cluster real · lokaler Fehlstart verboten.
