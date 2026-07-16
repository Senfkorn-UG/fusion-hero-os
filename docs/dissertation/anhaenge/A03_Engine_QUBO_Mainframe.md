# A03 — Engine, QUBO, Mainframe: Herleitung

**Paket:** `fusion_hero_os/engine/`  
**Designvorlage:** V3.3 — Mathematik ehrlich, Heuristik markiert  

---

## Synthese

Optimierung ist die Stelle, an der das System *schneidet* (Auswahl) und *fließt* (Suche im Zustandsraum). QUBO formalisiert binäre Entscheidungen; Simulated Annealing sucht gute Zustände. Hier wird beides **aus dem Nichts** aufgebaut und an den Code gebunden.

---

## Bogen 1 — Binäre Entscheidung

**[Definition]** Eine binäre Variable \(x_i \in \{0,1\}\).

**[Definition]** Ein QUBO-Problem minimiert
\[
E(x) = x^\top Q x
\]
(ggf. mit linearen Termen in der Diagonalen von \(Q\)).

**[Spezifikation]** `QUBOProblem`, `QUBOSolverConfig`, `SolverResult` in `mainframe.py`.

---

## Bogen 2 — Suche ohne Gradienten: Annealing

**[Herleitung]**

1. Zustand \(x \in \{0,1\}^n\).  
2. Nachbarschaft: Bit-Flip.  
3. Akzeptanz schlechterer Schritte mit Temperatur \(T\) (Metropolis).  
4. \(T\) sinkt → Exploitation.

**[Spezifikation]**

| Funktion | Rolle |
|----------|--------|
| `_simulated_annealing_kernel` | Numba-Kernel |
| `simulated_annealing` | Single-run |
| `local_search` | Greedy-Verbesserung |
| `parallel_anneal` | Mehrfachläufe / Thread-Pool |
| `_anneal_one`, `_sa_kernel_trace` | Worker / Trace |
| `warmup_kernels` | JIT warm |
| `make_Q` | Hilfskonstruktion |

**[Bedingt]** Qualität der Lösung hängt von Schritten, \(T_0\), Problemstruktur ab — **kein** globaler Optimalitäts-Satz für allgemeine QUBO (NP-schwer).

**[Satz]** Für konkrete kleine Instanzen kann man Optimalität *testen* (Exhaustion) — wo Tests das tun, gilt BEWIESEN nur für diese Instanzen.

---

## Bogen 3 — Backends

| Klasse | Rolle | Geltung |
|--------|-------|---------|
| `SolverBackend` | abstrakt `solve` | Definition |
| `ClassicalBackend` | Pre/Post-Audit-Hooks + SA | Spezifikation |
| `get_rust_backend` / `rust_backend.parallel_anneal_rust` | optional schneller Pfad | Spezifikation + Fallback |
| `_load_rust_backend` | Kandidatenimport, Cache | Spezifikation |

**[Ehrlich]** Rust ist Beschleunigung, keine neue Mathematik.

---

## Bogen 4 — Evolution und Meta *im* Engine-Kontext

| Klasse | Was sie *wirklich* tut | Was sie *nicht* ist |
|--------|------------------------|---------------------|
| `SelfModifyCoreModule` | Audit-Hooks / Vorschlagsliste | kein autonomer Code-Umschreiber |
| `GenerationalEvolutionProtocolCoreModule` | \((\mu+\lambda)\) über SA-Configs, Fitness \(-\)energy | keine allgemeine AGI-Evolution |
| `CriticalMetaAnalysisCoreModule` | Heuristik-Analyse | kein Beweis-Engine |
| `ExecutableAuditAgent` | Gateway | begrenzt |
| `QUBOIntegrationCoreModule` | secure run + Ascension-Interlock | ehrliche Hooks |

**[Spezifikation]** Docstring von `mainframe.py` markiert Platzhalter vs. echte Evolution — diese Ehrlichkeit ist Teil der Dissertation (Code Honesty).

---

## Bogen 5 — Mining-QUBO und Scheduling-Schwester

**Mining (`mining_qubo.py`):**

- `estimate_profit_matrix`, `build_profit_switching_qubo`, `decode_assignment`, `optimize_switching`  
- **Geltung:** Modell/Anwendung; Profit-Schätzungen empirisch bedingt.

**Scheduling (`core/inference_scheduler_qubo.py`):**

- `ScheduleProblem`, `build_qubo`, `greedy_schedule`, `solve_schedule`  
- **Geltung:** Bedingt (Heuristik).

---

## Bogen 6 — Rückkehr zur Autopolitik

QUBO-Läufe kosten Energie und Zeit → Placement L1/L3 (Mainframe vs. Cluster) ist **Autopolitik der Rechnung**.

**[Modell]** Engine = Muskel; MasterSeed/Geltung = Urteil (vgl. Cluster-als-Muskel, Gehirn-nicht-auslagern).

---

## Anhang A03 — Minimalbeispiel (Spezifikation)

```python
import numpy as np
from fusion_hero_os.engine.mainframe import make_Q, simulated_annealing

# Beispiel: n=4, zufällige symmetrische Q (Skizze)
n = 4
A = np.random.randn(n, n)
Q = (A + A.T) / 2
# energy, x = simulated_annealing(Q, steps=1000)  # Signatur siehe Code
```

Exact API: Source + A10.  
