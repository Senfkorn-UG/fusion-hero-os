# fusion-hero-os

**ALTE_Frau_95g Heroic Core v8 – Fusion Hero OS + echtes Multi-Core-Hyperthreading**

Ein heroic Framework für Rekonstruktivistischen Eudaimonismus und maximale intellektuelle Präzision.

## Aktueller Stand
- Version: v8 (Fusion Hero OS + OptimizerInsights Consolidation)
- **Hyperthreading:** echt und gemessen — `parallel_anneal(backend="auto")` in
  `fusion_hero_os/engine/` nutzt Rust/rayon (~4.4x) bzw. Numba-nogil (~3.4x)
  über alle logischen Kerne; `VirtualGPUHTCache` (03_Code) ist davon getrennt
  eine Simulation
- **Mathematischer Kern:** Knoten 16/17/19/20 als bewiesene Sätze
  (`fusion_hero_os/core/heroic_math_engine.py` — Beweise + 0-Verletzungs-Sweeps
  + Regressionstests); PMS Evidence Spine: eigener deterministischer Minimal-Kernel `pms_rust_kernel` implementiert (2026-07-04): PMS.yaml-Validierung, JSONL-Audit, FAIL_CLOSED; Operatoren = die vier bewiesenen Knoten-Saetze. Das externe tz-dev/PMS-RUST bleibt NICHT eingebunden
  (siehe `docs/01_vision/V8_STATUS_REPORT.md`)
- MasterSeed: M_0'''' — `verify_integrity()` ist seit 2026-07-04 eine ECHTE Pruefung
  (SHA-256-Zustands-Hash + Kontraktions-Check); MasterSeed-Syncs optimieren sich
  BEWEISBAR gegenseitig (`fusion_hero_os/core/masterseed_sync.py`, Satz + Tests)
- Struktur: siehe [docs/v8/PROJECT_STRUCTURE_v8.md](docs/v8/PROJECT_STRUCTURE_v8.md)
- Branches: siehe [docs/v8/BRANCH_STRATEGY_v8.md](docs/v8/BRANCH_STRATEGY_v8.md)
- CI: `ci.yml` + `fusion-hero-os-hyperthread.yml` (grün auf `main`); redundante/kaputte Workflows entfernt

## Entwicklung lokal starten

```bash
# Python-Backend/GUI (fusion_hero_os/ — installierbares Package, siehe pyproject.toml)
pip install -e ".[dev]"
python -m fusion_hero_os.registry           # Status aller Teilsysteme (Registry)
python -m fusion_hero_os.core.heroic_math_engine   # Sandbox-Verifikation
pytest

# Frontend (SvelteKit)
npm install
npm run dev
```

Details zu Endpunkten und alternativen Startwegen: [.REST_API_CONFIG](.REST_API_CONFIG).

## Branch Model (kurz)
- **main** → Stabile v8-Releases (protected)
- **develop** → Aktive Integration (wird angelegt)
- **feature/*** → Kurzlebige Aufgaben-Branches
- Historie → Tags + archive/-Ordner

Weitere Details: docs/v8/BRANCH_STRATEGY_v8.md

## Schnellstart
```bash
git clone https://github.com/95guknow/fusion-hero-os.git
cd fusion-hero-os
# Aktueller Stand auf main (v8 stable)
```

## Core
Der unified ALTE_Frau_95g Heroic Core wird über die Registry
(`python -m fusion_hero_os.registry`) geladen.

*(Die frühere Angabe "Identity Preservation Score: 100" war eine unbelegte
Selbstauskunft ohne Messverfahren und wurde entfernt.)*