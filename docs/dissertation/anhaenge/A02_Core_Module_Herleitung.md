# A02 — Core-Module: Herleitung und Funktionen

**Paket:** `fusion_hero_os/core/`  
**Geltung:** gemischt (markiert pro Familie)  
**Katalog:** siehe A10 für AST-Vollständigkeit  

---

## Synthese

Aus dem Fundament (A01) entstehen *spezialisierte* Organe. Jedes Core-Modul beantwortet eine Frage, die ohne es offen bliebe. Hier: **Herleitung der Frage → Definition → zentrale Funktionen → Geltung → Datei**.

---

## Bogen 1 — Math Engine (Beweis-Organ)

**Frage:** Was lässt sich an heroischen Operatoren *nachrechnen*?

**[Herleitung]** Vektorräume und Matrizen (allgemein) → Endomorphismen → Kommutator → Projektoren → Fixpunkte.

| Klasse | Kernfunktionen | Geltung |
|--------|----------------|---------|
| `HeroicMatrixEngine` | `compute_commutator`, Reciprocity-Checks | Satz/Bedingt (lineare Algebra) |
| `OrthogonalProjector` | `project`, `is_idempotent`, `is_symmetric`, `spectrum_in_01` | Satz unter Matrix-Annahmen |
| `StableCoreLattice` | Ordnung, Join, transitive Closure | Modell/Satz gemischt |
| `RepairedStructureIP` | `compute_stability`, `fusion_operator` | Modell + Bedingt |
| `BanachContractionSeed` | `apply`, `fixpoint`, `iterate`, `verify_contraction_bound` | Satz (Banach) **bedingt** kontrahierend |
| `run_sandbox_verification` | Sandbox-Checks | Spezifikation/Test |

**Datei:** `heroic_math_engine.py`  
**[Nicht behauptet]** Klinische oder kosmische Wahrheit der Metaphern.

---

## Bogen 2 — Quantum Cognition (Formalismus, nicht Physik im Kopf)

**Frage:** Wie modelliert man Nicht-Kommutativität von Urteilen?

**[Herleitung]** Hilbertraum-Zustand → Projektor → Born-Regel → Ordnungseffekte.

| Symbol / API | Rolle | Geltung |
|--------------|-------|---------|
| `_as_state`, `_check_projector` | Normalisierung / Validierung | Satz (Math) |
| `BeliefState.prob/collapse` | Born + Messung | Satz (Math) |
| `order_effect`, `interference_term` | Nicht-Kommutativität | Satz (Math) |
| `TwoLevelOscillator` | Unitäre Evolution | Satz (Math) |
| Empirischer Fit Sisyphos | — | **OFFEN / Modell** |

**Datei:** `quantum_cognition.py`  
**[Ehrlich]** Kein physischer Quantenprozess im Gehirn behauptet.

---

## Bogen 3 — MasterSeed, CEC, Sync, HeroicCore

**Frage:** Was bleibt invariant unter Evolution?

| Modul | API | Herleitung in einem Satz | Geltung |
|-------|-----|--------------------------|---------|
| `MasterSeed` | `state_hash`, `verify_integrity` | Ankerzustand + Hash | **Bedingt/Fragment**: Integrity-Stub ehrlich in Docs |
| `CoEvolutionaryClosure` | `step`, `_calculate_coherence` | Feedback Umwelt↔Seed | Modell operativ |
| `SyncState` / `mutual_sync` | bidirektionale Sync | Zwei Zustände gleichen sich an | Spezifikation + Modell |
| `identity_preservation_score` | Skalar | Wie viel Identität bleibt? | Modell |
| `HeroicCore` | `register_module`, `get_llm`, `enforce_fail_closed`, `trigger` | Fassade | Spezifikation |
| `QuadCoreBridge` | `process_query`, `ask_llm`, Phoenix-Hooks | Bridge heroic/ascension | Spezifikation |
| `bootstrap_v8_system` | Factory | Startpfad | Spezifikation |
| `PMSEvidenceSpine` | Operator-Ketten | Evidence-Pfad | Fragment/Roadmap-Anteil ehrlich |

**Dateien:** `heroic_core_orchestrator.py`, `cec.py`, `masterseed_sync.py`, `heroic_core.py`

---

## Bogen 4 — Schichten, Atlas, Multimodal

**Frage:** Wo liegt was, und was hängt wovon ab?

| Modul | API | Geltung |
|-------|-----|---------|
| `layer_registry` | `get_layer_status`, `get_all_layer_status`, Layer-Checks | Spezifikation (Pfad/Health-Heuristik) |
| `dependency_atlas` | `scan_python/rust/js`, `build_atlas`, `find_cycles`, `render_mermaid` | Spezifikation |
| `multimodal_protocol` | `classify`, `build_inventory`, `routing_matrix`, Provider-Status | Spezifikation |
| `erkenntnisse_summary` | Aggregat | Spezifikation |

---

## Bogen 5 — Sicherheit der Gleichzeitigkeit und Routing

| Modul | API | Herleitung | Geltung |
|-------|-----|------------|---------|
| `race_guard` | `FileLock`, `atomic_write_*`, `compare_and_swap_json`, `RaceConditionGuard` | Mehrere Schreiber → Lock + atomic replace + CAS | Spezifikation; Stress-Test |
| `grok_route_table` | `resolve`, `route_message`, `all_routes`, `ROUTE_TABLE` | Intent → Surface/API | Spezifikation |
| `grok_interconnect` | `capture`, `evolve`, `get_graph`, `probe_http` | Graph der Knoten/Kanten | Spezifikation + Health-**Modell** |
| `universal_llm_router` | `SisyphosCycle`, `FailClosed`, `UnifiedHeroicLLMCore.ask` | Routing + Sustainability | Spezifikation + Modell |
| `inference_scheduler_qubo` | `build_qubo`, `solve_schedule` | Scheduling als QUBO | Bedingt (Heuristik SA) |
| `quantum_dictionaries` | `get_or_compute`, TTL-Cache | Memoization | Spezifikation |
| `psycholysis_trigger` | `should_trigger`, `trigger`, Session | Trigger-Logik | Modell |
| `rhe` | `RustHybridEmbodiment` | Embodiment-State | Modell/Fragment |

---

## Bogen 6 — Dispatcher-Ökosystem und Dashboard-Core

| Modul | API | Geltung |
|-------|-----|---------|
| `dashboard.orchestration.DashboardOrchestrator` | Agent-Register/Assign | Spezifikation |
| `dashboard.workspace.Workspace` | key-value Workspace | Spezifikation |
| `models.Task` / `TaskResult` | Datenträger | Definition |
| `dispatcher` | siehe A01 | Spezifikation |

---

## Anhang A02 — Entwicklungsnotiz (Null → Core)

```text
Nichts
 → Unterscheidung/Name (A01)
  → BaseModule
   → Math (Beweisbarkeit)
    → Cognition-Formalismus (ohne Physik-Claim)
     → Seed/CEC (Invarianz-Frage)
      → Layer/Atlas (Lage)
       → Race/Route/Interconnect (Koordination)
        → LLM-Router (Handlung unter Fail-Closed)
```

**Vollständige Symboltabelle:** A10.  
**Engine/QUBO-Tiefe:** A03.  
