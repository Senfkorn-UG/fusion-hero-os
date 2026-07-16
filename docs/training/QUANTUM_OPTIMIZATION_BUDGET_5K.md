# Quantum / QUBO Optimization — Budget €5.000 (präzise)

**Stand:** 2026-07-16 · Fusion Hero OS v10.0.0  
**Budget:** **€5.000** one-shot / campaign (zusätzlich zum ~€200 Ops-Monat)  
**Ziel:** Wichtungen, Cross-Pollination, QUBO/QAOA-class Optimierung auf dem **besten verfügbaren** Rechner — plus echter Quantum-Pfad, wo möglich.

---

## 1. Ehrlichkeit (Code-Honesty)

| Layer | Was es ist | Was es nicht ist |
|-------|------------|------------------|
| **Klassisch (jetzt im Repo)** | Simulated Annealing / parallel SA (Numba), QUBO-Bridge | Kein physischer Quantencomputer |
| **GPU L3** | Beschleunigte klassische Optimierung (L4/H100) | Kein „Quantum Advantage“-Claim |
| **Quantum Cloud (Pfad)** | Annealer/QPU-API (IonQ, D-Wave, Google) | Erfordert Account + Quota + Adapter |

Quantencomputing ist **strategisch wichtig** → Budget und Architektur halten **beide** Spuren:  
**(A) Best classical on best GPU** + **(B) echte QPU sobald Quota/API da**.

---

## 2. GCP Quota-Realität (europe-west3, gemessen)

| Metric | Limit | Nutzung |
|--------|------:|--------:|
| **NVIDIA_L4_GPUS** | **1** | 0 |
| NVIDIA_T4_GPUS | 1 | 0 |
| NVIDIA_A100_GPUS | **0** | 0 |
| NVIDIA_A100_80GB_GPUS | **0** | 0 |
| H100 (region list) | **nicht freigeschaltet / Scale-up fail** | — |
| CPUS | 200 | 4 |

**H100-Job scheiterte:** `GCE quota exceeded`.  
**Sofort lauffähig „best under quota“:** **1× NVIDIA L4**.  
**Best-in-class nach Quota-Antrag:** **1× NVIDIA H100 80GB** (in Region gelistet).

---

## 3. Budget-Allokation €5.000 (Vorschlag)

| Posten | EUR | Anteil | Zweck |
|--------|----:|-------:|-------|
| **GPU campaign (L4 jetzt + H100 später)** | **2.500** | 50 % | Crosspoll / QUBO restarts, large N |
| **Quantum Cloud (IonQ / D-Wave / Google)** | **1.500** | 30 % | echte QPU/Annealer-Jobs, Credits |
| **Storage + egress + retries** | **400** | 8 % | GCS checkpoints, logs |
| **Mesh always-on (Ops, 3 Monate × ~90)** | **300** | 6 % | L2 exit bleibt stehen |
| **Reserve / failed starts** | **300** | 6 % | Quota-Wartezeit, Fehlstarts |
| **Summe** | **5.000** | 100 % | |

### GPU-Stunden (Richtwerte cost function v2 + Aufschlag)

| Hardware | ~EUR/h (Modell) | Mit €2.500 GPU-Topf |
|----------|----------------:|---------------------|
| **L4** (quota=1) | ~0,70–1,20 | **~2.000–3.500 h** (viel) |
| **H100 80GB** (nach Quota) | ~10–15+ | **~160–250 h** |
| **A100 80GB** (Quota 0, Region dünn) | ~3,90+ | erst nach Quota |

**Empfehlung Campaign:**

1. **Sofort:** L4 Crosspoll (volle Parameter, viele Restarts) — läuft **jetzt**.  
2. **Parallel:** Quota-Request **H100 ≥ 1** + optional **A100 ≥ 1**.  
3. **Mit H100:** „Best classical“ Deep-Runs (n=512–1024, 12k–50k steps, 16–64 restarts).  
4. **Mit €1.500 Cloud-Quantum:** Account + Adapter + kleine QUBO-Instanzen auf QPU zum Vergleich.

---

## 4. Server-Wahl (präzise)

### JETZT (Quota vorhanden) — **NVIDIA L4 × 1**

| | |
|--|--|
| Accelerator | `nvidia-l4` |
| vCPU / RAM | 4 / 16 Gi (Autopilot-fit) |
| Job | `infra/k8s/fusion-training/crosspollination-qubo-l4-job.yaml` |
| n / steps / restarts | 256 / 8000 / 8 (skalierbar nach oben im Script) |
| Kosten | **~1 EUR/h** Ordnung → unter €5k trivial viele Runs |

### NACH QUOTA — **NVIDIA H100 80GB × 1** (best in europe-west3)

| | |
|--|--|
| Accelerator | `nvidia-h100-80gb` |
| vCPU / RAM | 8 / 64 Gi (Autopilot-safe) |
| Job | `infra/k8s/fusion-training/crosspollination-qubo-best-job.yaml` |
| n / steps / restarts | **512 / 12000 / 16** |
| Kosten | **~10–15 EUR/h** → ~**€100–150 pro 10h-Deep-Run** |

### Echter Quantum (nicht GKE-GPU)

| Anbieter | Rolle | Budget-Topf |
|----------|--------|-------------|
| **IonQ** (via Azure/AWS/Google) | Gate-model QPU | €1.500 Cloud |
| **D-Wave** | Quantum Annealing (natürlich QUBO-nah) | €1.500 Cloud |
| **Google Quantum AI / Cirq** | Research + Simulator + ggf. Hardware | Teil von €1.500 |

Adapter-Status im Repo: **klassischer** `qubo_bridge` / `qb_qubo` — QPU-Adapter ist **Roadmap-Modul** (nächster Bau).

---

## 5. Präzise Anweisungen

### A) L4 Crosspoll **jetzt** (empfohlen sofort)

```powershell
$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
gcloud container clusters get-credentials senfkorn-gke-cluster `
  --region europe-west3 --project project-bbf0e6db-52e1-462b-8e3

# Code (bereits auf GCS, bei Bedarf erneut)
gsutil cp C:\Users\Admin\fusion-hero-os\scripts\crosspollination_qubo_optimize.py `
  gs://fusion-ai-data-project-bbf0e6db-52e1-462b-8e3/training/
gsutil cp C:\Users\Admin\fusion-hero-os\qb_qubo.py `
  gs://fusion-ai-data-project-bbf0e6db-52e1-462b-8e3/training/

kubectl delete job -n fusion-training -l app=crosspoll-qubo --ignore-not-found
kubectl create -f C:\Users\Admin\fusion-hero-os\infra\k8s\fusion-training\crosspollination-qubo-l4-job.yaml
kubectl get pods -n fusion-training -l app=crosspoll-qubo -w
kubectl logs -n fusion-training -l app=crosspoll-qubo -f
```

### B) H100 Quota anfordern (Best classical)

1. Console → [IAM & Admin → Quotas](https://console.cloud.google.com/iam-admin/quotas?project=project-bbf0e6db-52e1-462b-8e3)  
2. Filter region **europe-west3**, Metrics:  
   - `NVIDIA_H100_GPUS` / GPUs related to H100  
   - ggf. `A2_CPUS` / GPU family CPUs  
3. Request **limit ≥ 1** (Begründung: QUBO/crosspollination research, budget €5k)  
4. Nach Approve:

```powershell
kubectl create -f infra/k8s/fusion-training/crosspollination-qubo-best-job.yaml
```

### C) Orchestrierungs-Policy (unverändert)

```powershell
python -m fusion_hero_os.core.poly_mesh_router --assert-local qubo-anneal
# allowed=false → L3 only
python scripts/orchestrate_poly_mesh.py --execute
```

---

## 6. Campaign-Plan (mit €5k)

| Phase | Dauer | Hardware | Ausgaben (ca.) | Deliverable |
|-------|-------|----------|----------------|-------------|
| **P0** | Tag 1 | L4 | €20–100 | Crosspoll baseline n=256–512 |
| **P1** | Woche 1–2 | L4 heavy + Quota wait | €200–500 | Parameter-Sweep, Gewichts-Stabilität |
| **P2** | nach Quota | H100 deep | €500–1.500 | n=512–1024, 16–64 restarts |
| **P3** | parallel | Quantum Cloud | €500–1.500 | kleine Instanzen QPU vs classical |
| **P4** | Rest | Reserve + Mesh | €300–500 | Repro, Docs, dual-start free |

---

## 7. Anti-Patterns

- H100-Job spammen ohne Quota (verbrennt Autoscaler-Backoff)  
- Quantum **behaupten**, obwohl nur SA auf GPU läuft  
- €5k in 24/7 GPU verbrennen ohne Checkpoint-GCS  
- Dual-Start lokal + Cluster  

---

## 8. Dateien

| Datei | Rolle |
|-------|--------|
| `scripts/crosspollination_qubo_optimize.py` | Wichtungs-QUBO |
| `infra/k8s/fusion-training/crosspollination-qubo-l4-job.yaml` | L4 now |
| `infra/k8s/fusion-training/crosspollination-qubo-best-job.yaml` | H100 after quota |
| `docs/business/COST_FUNCTION_v2.md` | Kostenformel |
| `docs/training/CROSSPOLLINATION_QUBO_BEST.md` | Ops detail |
