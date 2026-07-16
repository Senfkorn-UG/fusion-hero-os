# Crosspollination QUBO — Best of the Best (präzise Anweisungen + Kosten)

**Stand:** 2026-07-16 · Fusion Hero OS **v10.0.0**  
**Workload:** Wichtungen / Assoziationsgewichte (Cross-Pollination) → QUBO  
**Placement:** **L3_cluster only** (`force_cluster`, `poly_mesh_router`)  
**Hinweis:** **Klassisches** Simulated Annealing (Numba/HT) — **kein** Quantencomputer-Hardware-Claim.

---

## 1. Workload-Spezifikation (vollständig)

| Parameter | Wert (Best) | Light-Alternative |
|-----------|-------------|-------------------|
| Problemgröße \(n\) | **512** | 256 |
| SA-Steps | **12 000** | 4 000 |
| Restarts | **16** (parallel) | 4 |
| Cardinality \(k\) | **64** (soft) | optional |
| Sources | **pure-core first:** formal_math, diverse_algorithms, pure_core, mesh, cluster, llm, saas, ascension, operator | subset / `FUSION_CROSS_SOURCES` |
| vCPU | **22** | 4–8 |
| RAM | **85 Gi** | 16 Gi |
| GPU | **2× NVIDIA A100 80GB** | 1× L4 |
| Image | `nvcr.io/nvidia/pytorch:24.06-py3` | same |
| Region | **europe-west3** | — |
| Namespace | `fusion-training` | — |
| Active deadline | 24 h | 6 h |

**Algorithmus (kurz):**  
Knotenwerte aus Multi-Source-Scores + Cosine-Assoziation \(A=VV^\top\) → QUBO \(Q\) →  
\(\min_x x^\top Q x\), \(x\in\{0,1\}^n\), optional \((1^\top x - k)^2\).

---

## 2. Bester Server (empfohlen)

### Tier BEST (Wichtungen / Crosspollination)

| | |
|--|--|
| **Klasse** | **2× NVIDIA A100 80GB** |
| **GKE** | Autopilot + `cloud.google.com/gke-accelerator: nvidia-tesla-a100` |
| **GPU request** | `nvidia.com/gpu: "2"` |
| **CPU / RAM** | 22 vCPU / 85 Gi |
| **Job** | `infra/k8s/fusion-training/crosspollination-qubo-best-job.yaml` |
| **Script** | `scripts/crosspollination_qubo_optimize.py` |

### Tier GUT (Budget-Monat ~€200)

| | |
|--|--|
| **Klasse** | **1× NVIDIA L4** |
| **GPU** | 1× L4, 4–8 vCPU, 16 Gi |
| **Kosten** | ~0,70 EUR/h GPU → **zeitlich begrenzt** |
| **Wann** | \(n\le 256\), steps ≤ 4k, wenige Restarts |

### Tier NICHT für Dauerbetrieb unter €200/Monat

- 2× A100 **24/7** (~190–240 EUR/Tag GPU-Anteil allein)  
- Nur **one-shot** mit Training-Budget (Businessplan: **700 EUR** one-shot)

---

## 3. Bekannte Kosten (cost function v2.0)

| Komponente | Rate (EUR) | 2× A100 Job |
|------------|------------|-------------|
| A100 GPU hour | **3,90** | **7,80 / h** (2 GPUs) |
| Autopilot CPU/RAM (grober Aufschlag) | — | **~+1–2 EUR/h** |
| **Gesamt realistisch** | | **~9–11 EUR/h** |

| Laufzeit | Geschätzte Kosten |
|----------|------------------:|
| **2 h** (smoke / short) | **~18–22 EUR** |
| **6 h** (standard best) | **~54–66 EUR** |
| **12 h** | **~110–130 EUR** |
| **24 h** | **~220–260 EUR** |

**Mesh always-on** (2× e2-micro + desk) bleibt extra **~90 EUR/Monat**.  
→ Best-of-Best A100-Jobs = **one-shot / budgetiert**, nicht Dauerlast neben dem €200-Ops-Budget.

**API-Tier:** `qubo_enterprise` (P_1k aus Live-\(C_h\); unter Last steigt der Preis).

---

## 4. Präzise Anweisungen (Copy-Paste)

### A) Code nach GCS

```powershell
$BUCKET = "fusion-ai-data-project-bbf0e6db-52e1-462b-8e3"
cd C:\Users\Admin\fusion-hero-os
gsutil cp scripts/crosspollination_qubo_optimize.py "gs://$BUCKET/training/"
gsutil cp qb_qubo.py "gs://$BUCKET/training/"
# optional stability train
gsutil cp 03_Code/training/fusion_stability_train.py "gs://$BUCKET/training/"
```

### B) Job starten (Best)

```powershell
$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
gcloud container clusters get-credentials senfkorn-gke-cluster `
  --region europe-west3 --project project-bbf0e6db-52e1-462b-8e3

kubectl apply -f infra/k8s/fusion-training/namespace.yaml
kubectl apply -f infra/k8s/fusion-training/serviceaccount.yaml
# SA annotation must use real project id (already in live cluster)

kubectl create -f infra/k8s/fusion-training/crosspollination-qubo-best-job.yaml
kubectl get jobs,pods -n fusion-training -l app=crosspoll-qubo
kubectl logs -n fusion-training -l app=crosspoll-qubo -f
```

### C) Ergebnis holen

```powershell
gsutil ls gs://fusion-ai-data-project-bbf0e6db-52e1-462b-8e3/crosspollination/
gsutil cp gs://fusion-ai-data-project-bbf0e6db-52e1-462b-8e3/crosspollination/latest.json .
```

### D) Orchestrierungs-Gate (lokal)

```powershell
python -m fusion_hero_os.core.poly_mesh_router --assert-local qubo-anneal
# expected: allowed=false, run_on=L3_cluster
```

---

## 5. Parameter-Tuning (Best)

| Ziel | Env |
|------|-----|
| Max Qualität | `FUSION_QUBO_N=512`, `FUSION_ANNEAL_STEPS=12000`, `FUSION_N_RESTARTS=16` |
| Mehr Selektivität | `FUSION_CARDINALITY_K=32` … `64` |
| Reproduzierbar | `FUSION_WEIGHT_SEED=42` |
| Quellen-Mix | `FUSION_CROSS_SOURCES=mesh,dissertation,qubo,operator,ascension,heroic` |

---

## 6. Anti-Patterns

- Crosspollination-QUBO **lokal** starten während L3 live (Dual-Start)  
- 2× A100 **dauerhaft** im €200-Ops-Monat  
- Ergebnis nur in Pod-Logs (ohne GCS)  
- „Quantum“ als Hardware behaupten (hier: **klassische** Optimierung)

---

## 7. Verwandt

- `scripts/crosspollination_qubo_optimize.py`  
- `infra/k8s/fusion-training/crosspollination-qubo-best-job.yaml`  
- `fusion_hero_os/meta/qubo_bridge.py` (Graph→QUBO)  
- `docs/business/COST_FUNCTION_v2.md`  
