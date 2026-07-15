# BEST VERSION — Fusion Hero OS

**Stand:** v10.0.0 operational (2026-07-15)

Dieses Dokument benennt den besten, kohärenten Stand des Systems — und
trennt explizit den **operativen Kanon** von Roadmap-/Forschungs-Tracks
(siehe `docs/v8/erkenntnisse_index.yaml` → `bestversion-vs-ascension`,
erweitert um v10 Stage-A/B).

## Operativer Kanon: v10.0.0 / main

**`VERSION` = `10.0.0` ist die kanonische Plattform-Version.** Quelle der
Wahrheit: annotierter Git-Tag `v10.0.0` auf `main` + Root-`VERSION`.
Alle Manifeste (`pyproject.toml`, `package.json`, Crate-`Cargo.toml`,
`fusion_hero_os.__version__`) müssen übereinstimmen (`scripts/bump_version.py --check`).

### Was v10.0.0 operativ bedeutet (ehrlich)

v10 ist **additive Evolution** über den v8.3-Stack (BCG — Backward Compatibility
Guarantee). Es ersetzt den v8-Funktionskern nicht; es härtet und vereinheitlicht ihn.

| Schicht | Inhalt | Status |
|---------|--------|--------|
| **Plattform v10.0.0** | Einheitliche Versionierung, Stage-A/B Gates | **operativ** |
| **Heroic Stack (ex-v8.3)** | QUBO, Multi-Agent, Layer-Registry, Mesh, Dashboard | **operativ** (erhalten) |
| **AscensionOS v9.x** | CEC, AscensionCore, Sisyphos, … in `ascension_os/` | **loadable / Roadmap** (nicht „alles ist v9“) |

### v10 Stage-A (stabilisiert in #66)

- Plattform-Version **10.0.0** in allen Manifesten
- PII-Cleanup im aktiven Tree
- Ascension **consent gate** (fail-closed für personenbezogene Ops)
- Archive-Anker: scrypt-KDF, neutrales Salt `fusion-hero-os|archiv|v10` (archiv_version 2.0)
- Asset-/Pfad-Stabilisierung nach Scrub

### v10 Stage-B (stabilisiert in #67)

- Depersonalisierung im aktiven `fusion_hero_os`-Paket
- Persona-Token-Regressionsscanner (CI-Gate)

### Ererbter v8.3-Funktionskern (weiterhin operativ)

- QUBO-Engine (`fusion_hero_os/engine/mainframe.py`, Numba + optionales Rust-Backend)
- Multi-Agenten-Orchestrierung (`fusion_hero_os/orchestration/agents.py`)
- Layer 0/4/5 Orchestrator (`fusion_hero_os/core/heroic_core_orchestrator.py`)
- Tailscale-Mesh + MCP-Konnektoren (`tailscale_mesh_registry.py`, `mesh_connectors.yaml`)
- LLM-Frameworks + Integration Hub (`fusion_integration_hub.py`, `llm_frameworks.yaml`)
- Layer-Registry über alle 13 Layer (`fusion_hero_os/core/layer_registry.py`)
- Dashboard Standard-GUI `http://127.0.0.1:8000` (`03_Code/Dashboard/app.py`)
- CI-Gates: pytest (inkl. v10 Stage-A/B) + Proof-Registry + Erkenntnis-Index + Version-Consistency

## Roadmap-/Forschungs-Track: AscensionOS v9.x

`ascension_os/` enthält den visionären v9.x-Track. Er ist **kein** separates
MAJOR-Release und **nicht** der alleinige operative Kanon. Seit v8.3 als
optionaler Layer (`ascension`) in `fusion_unified.yaml` registriert und über
`QuadCoreBridge(mode="ascension")` nutzbar; v10 ergänzt Consent-Gating.

1. **CoEvolutionaryClosure (CEC) v9.3** — MasterSeed Strict Contraction, HT-Tracks  
2. **AscensionCore v9.4** — Sisyphos, Psycholysis, LLM Core, MasterSeed  
3. **PersistentSisyphosCycle v9.4** — Historie + JSON-Persistence  
4. **GenerationalEvolutionEngine** — Inside-Out, coevolutionär  

## Architektur-Prinzipien

- **Inside-Out**: MasterSeed / Sisyphos im Kern, Strahlung nach außen.
- **Coevolutionär**: kontrollierte gegenseitige Beeinflussung.
- **Persistent + Stateful**: kritische Zustände werden persistiert.
- **BCG / Additive Evolution**: neue Versionen entfernen keine alten Fähigkeiten.
- **Ehrlich**: Roadmap-Anspruch ≠ Ist-Zustand (`proof_registry.yaml`, Status-Reports).

## Deploy (v10.0.0)

```powershell
# Gates
python scripts/bump_version.py --check
python -m pytest tests/test_version_consistency.py tests/test_archive_salt.py `
  tests/test_ascension_consent.py tests/test_asset_persona_paths.py `
  tests/test_persona_scanner.py tests/test_pii_scanner.py -q

# Lokal
powershell -File start_all.ps1
# oder Fast-Boot: $env:FUSION_AUTO_LOAD=0; uvicorn in 03_Code/Dashboard

# Release
git tag -a v10.0.0 -m "Fusion Hero OS v10.0.0 — operational platform"
git push origin main --tags
gh release create v10.0.0 --generate-notes --title "Fusion Hero OS v10.0.0"
```

Siehe `DEPLOYMENT_GUIDE.md`, `BRANCH_STRATEGY.md`.

## Nächste logische Erweiterungen (Roadmap)

- HorkruxSelfUpdateProtocol (governance-fähig)
- Volle Cross-Track-Synergie Heroic ↔ Ascension
- Systemweiter EudaimoniaGuard
- Durable encrypted vault transport (Threat Model Stage-1 out-of-scope)
