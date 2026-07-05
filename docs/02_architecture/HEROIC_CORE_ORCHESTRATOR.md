# HEROIC CORE ORCHESTRATOR (v8)

**Layer 0 – 5 Integration Layer**

Dieses Modul bildet den **zentralen Orchestrator** des Fusion-Hero-OS. Es definiert die Grundstruktur für eine unveränderliche MasterSeed-Schicht (Layer 0), einen geplanten PMS Evidence Spine (Layer 4) und eine Fail-Closed AI Bridge (Layer 5).

> **Ehrlicher Status (Code-Honesty-Korrektur):** Dieses Modul ist ein
> Architektur-Gerüst, kein fertiges System. Fail-Closed-Verhalten funktioniert
> tatsächlich; die Integritäts- und Rust-Kernel-Anbindung sind Platzhalter.
> Details siehe Tabelle "Status" unten.

## Architektur-Einordnung

| Layer | Komponente          | Verantwortung                                    | Status |
|-------|---------------------|---------------------------------------------------|--------|
| 0     | `MasterSeed`         | Unveränderlicher Banach-Fixpunkt         | `verify_integrity()` ECHT seit 2026-07-04: SHA-256-Zustands-Hash, Manipulation -> `False`; + `verify_strict_contraction` (K20) |
| 4     | `PMSEvidenceSpine`   | Kapselt den EIGENEN deterministischen Minimal-Kernel | `pms_rust_kernel_crate/` (seit 2026-07-04): PMS.yaml-Validierung, JSONL-Audit, FAIL_CLOSED; ohne gebautes Binary weiterhin sauberes `FAIL_CLOSED` |
| 5     | `QuadCoreBridge`     | Fail-Closed-Routing + Phoenix-Mode                 | Fail-Closed ist real; Phoenix-Mode ist aktuell nur Logging (kein echter State-Reset) |

## Kernprinzipien

- **Fail-Closed**: Real und verifiziert. Fehlt der Rust-Kernel oder ist die Domäne ungültig, wird sofort ein sicherer `FAIL_CLOSED`/`ValueError`-Zustand zurückgegeben statt eine unsichere Ausführung zu versuchen.
- **Phoenix-Mode**: `invoke_phoenix_mode()` setzt aktuell nur ein `mode`-Flag und gibt Log-Zeilen aus. `_flush_volatile_memory()` löscht **keinen** tatsächlichen Zustand (kein Attribut wird zurückgesetzt) — als Namensgeber für ein zukünftiges Feature zu verstehen, nicht als bereits wirksamer Resilienz-Mechanismus.
- **Quad-Domain-Modell**: Strenge Trennung in MYTHOS, GRUND, BEWEIS, GESTALT ist im Code durchgesetzt (`ValueError` bei ungültiger Domäne). Nur BEWEIS und GESTALT lösen den (aktuell nicht funktionsfähigen) Spine-Aufruf aus.

## Boot-Sequenz

```python
from core.heroic_core_orchestrator import bootstrap_v8_system

heroic_core = bootstrap_v8_system()
response = heroic_core.process_query(
    domain="GESTALT",
    operator_id="OP_Q_B_CIRC",
    payload={"action": "verify_reciprocity"}
)
# ohne gebautes Binary: {"status": "FAIL_CLOSED", ...}; mit Binary: {"status": "SUCCESS", "result": {...}}
# solange kein ./pms_rust_kernel-Binary vorhanden ist (aktuell immer der Fall).
```

## Integration mit Heroic Math Engine

Das Orchestrator-Modul ist konzeptionell komplementär zur `heroic_math_engine.py` gedacht:

- `heroic_math_engine.py` → Knoten 16/17/19/20 als BEWIESENE Sätze
  (Beweise in Docstrings, 0-Verletzungs-Sweeps, Regressionstests —
  Stand 2026-07-04, siehe `docs/01_vision/V8_STATUS_REPORT.md` 2.3)
- `heroic_core_orchestrator.py` → Architektur-Gerüst für systemweite
  Koordination; deterministische Ausführung seit 2026-07-04 real (eigener Minimal-Kernel).

Beide zusammen bilden das v8-Architektur-**Gerüst** — nicht eine vollständige, lauffähige Core-Schicht.

## Status

- **Deterministisch**: Ja — eigener Minimal-Kernel `pms_rust_kernel` (byte-identische Ergebnisse, Kernel-Integrationstests in `tests/test_heroic_core_orchestrator.py`); das externe tz-dev/PMS-RUST bleibt nicht eingebunden.
- **Fail-Closed**: Ja — verifiziert, funktioniert wie beschrieben.
- **Phoenix-Resilient**: Ja — echter Reset des flüchtigen Zustands (Query-Historie + Response-Cache) mit anschließender Seed-Re-Verifikation (seit 2026-07-04).

**Teil der 02_architecture Schicht.**
