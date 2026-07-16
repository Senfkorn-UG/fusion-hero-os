# Pure-Core Langzeit-Coevolution

**Stand:** 2026-07-16 · Fusion Hero OS **v10.0.0**  
**Membrane:** `pure_core_coevolution_v1`  
**Identität:** Operator = **reiner Core** (Source of Truth)

---

## 1. Policy (unverhandelbar)

| Achse | Regel |
|-------|--------|
| **Identität** | Reiner Core — keine SaaS-/LLM-Persona als Wahrheitsträger |
| **Eigene Stärken (Core)** | **Formale mathematische Neuerungen** + **diverse Algorithmen** |
| **Fremde Stärken** | Alles andere (Mesh, LLM, GKE, SaaS, UI, Ascension-Roadmap, …) |
| **Mutual** | Cross-Pollination in **beide** Richtungen |
| **Authority** | Core = source of truth; Foreign = **peripheral** only |
| **Inside-Out** | Core **radiates** → Foreign; Foreign → Core nur **gated** |

### Was Foreign **nicht** darf

- MasterSeed überschreiben  
- Theoreme / formale Sätze ersetzen  
- `source_of_truth` / `replace_core` beanspruchen  
- Operator-Identität (reiner Core) ersetzen  

### Was Foreign **darf** (gated)

- `weight_*`, `score_*`, `metric_*`, `placement_*`, `cost_*`, `coverage_*`, `latency_*`, `energy_*`, `hint_*`, `feedback_*`  
- empirische Hinweise für QUBO-Wichtungen und Placement  

---

## 2. Artefakte

| Pfad | Rolle |
|------|--------|
| `fusion_hero_os/core/pure_core_coevolution.py` | Membrane + Step/Cycle/Status |
| `fusion_hero_os/core/catalogs/pure_core_strengths.yaml` | Core- vs. Foreign-Katalog |
| `scripts/pure_core_coevolution_status.py` | CLI |
| `scripts/crosspollination_qubo_optimize.py` | nutzt Core-first `crosspoll_sources` |
| Registry | `core.pure_core_coevolution` |

State (operator-local):

- `~/.fusion/coevolution/last_pure_core_report.json`  
- `~/.fusion/coevolution/pure_core_history.jsonl`  

---

## 3. Core-Stärken (Katalog)

1. **formal_math_innovations** — u. a. Transpositions-Reziprozität, Orthogonalprojektor, Banach-Fixpunkt, QUBO-Landschaften, MasterSeed-Contraction  
2. **diverse_algorithms** — SA/parallel anneal, poly-mesh Routing/Orchestrierung, Kostenfunktion \(C_h\), Crosspoll-Assoziation, Generational Evolution  
3. **pure_core_identity** — Operator-Rolle abstrakt, Dissertation-as-OS, Inside-Out  

Evidence-Pfade werden beim Scan gegen das Repo geprüft (Coverage).

---

## 4. Fremde Stärken (Auszug)

| ID | Authority |
|----|-----------|
| `llm_inference` | peripheral |
| `mesh_infra` | peripheral |
| `gke_cluster` | peripheral |
| `saas_connectors` | peripheral |
| `ui_dashboard` | peripheral |
| `ascension_aspirational` | peripheral_roadmap |

Diese **co-evolven** mit Core-Algorithmen/Math — ersetzen sie nicht.

---

## 5. Transfer-Semantik

```
  [ Pure Core ]  ──radiate──►  [ Foreign Strengths ]
       ▲                              │
       └──────── gated ◄──────────────┘
              (weights / metrics only)
```

Formelisch (an CEC angelehnt):

\[
M_{n+1} = R_{\mathrm{pure}}(M_n,\, E_n^{\mathrm{gated}})
\]

wobei \(E_n^{\mathrm{gated}}\) nur periphere Signale enthält und Claims auf Core-Ersetzung verwirft.

---

## 6. Crosspollination / QUBO

Default-Sources (Core first):

```text
formal_math, diverse_algorithms, pure_core,
mesh, cluster, llm, saas, ascension, operator
```

Override: `FUSION_CROSS_SOURCES=...`  
Catalog override: `FUSION_PURE_CORE_CATALOG=/path/to.yaml`

Cluster-Jobs (`crosspollination-qubo-*-job.yaml`) erben diese Defaults über das Optimize-Script.

---

## 7. CLI

```powershell
cd C:\Users\Admin\fusion-hero-os
python scripts/pure_core_coevolution_status.py
python scripts/pure_core_coevolution_status.py --cycle 5
python scripts/pure_core_coevolution_status.py --reject-test
```

Python:

```python
from fusion_hero_os.core.pure_core_coevolution import (
    status, mutual_cycle, assert_core_not_replaced, global_pure_core,
)

status()
mutual_cycle(3)
assert_core_not_replaced("llm")  # → False
global_pure_core.step({"weight_hint": 0.7})
```

---

## 8. Beziehung zu CEC / Ascension

| Layer | Rolle |
|-------|--------|
| `fusion_hero_os/core/cec.py` | generischer CEC-Schritt |
| `ascension_os/.../coevolutionary_closure.py` | aspirational HT-Tracks |
| **`pure_core_coevolution`** | **operative Policy:** reiner Core vs. fremde Stärken |

v10-operativ: Pure-Core-Membrane ist Kanon-Policy für Langzeit-Mutual.  
Ascension bleibt loadable Roadmap, nicht Ersatz des reinen Cores.

---

## 9. Geltung

- Membrane / Gates = **Spezifikation**  
- Evidence-Coverage = **empirisch** (Pfad-Existenz)  
- „Fortschritt der Dissertation“ als Fitness = **Bedingt** (nur Repo-Evidenz)  
- Kein Claim: Foreign-LLM „ist“ der Core  
