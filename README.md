# fusion-hero-os

**ALTE_Frau_95g Heroic Core v8 – Fusion Hero OS + Full Native Hyperthreading**

Ein selbst-modifizierendes, heroic Framework für Rekonstruktivistischen Eudaimonismus und maximale intellektuelle Präzision.

## Aktueller Stand
- Version: v8 (Fusion Hero OS + Full Native Hyperthreading + OptimizerInsights Consolidation)
- MasterSeed: M_0''''
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
Der unified ALTE_Frau_95g Heroic Core wird automatisch top-down geladen.

**Identity Preservation Score: 100**