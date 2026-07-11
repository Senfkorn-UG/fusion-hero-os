# BEST VERSION — Fusion Hero OS

**Stand:** v8.3-Konsolidierung (2026-07-10)

Dieses Dokument benennt den besten, kohärentesten Stand des Systems — und
trennt dabei explizit den **operativen Kanon** vom **Roadmap-Track**
(Auflösung des früheren Widerspruchs zu
`docs/v8/BESTVERSION_CONSOLIDATION_MANIFEST.md`, siehe
`docs/v8/erkenntnisse_index.yaml` → `bestversion-vs-ascension`).

## Operativer Kanon: v8/main

**v8/main dieses Repos ist die kanonische, lauffähige Bestversion.**

- QUBO-Engine (`fusion_hero_os/engine/mainframe.py`, Numba + optionales Rust-Backend)
- Multi-Agenten-Orchestrierung (`fusion_hero_os/orchestration/agents.py`)
- Layer 0/4/5 Orchestrator (`fusion_hero_os/core/heroic_core_orchestrator.py`)
- Tailscale-Mesh + MCP-Konnektoren (`tailscale_mesh_registry.py`, `mesh_connectors.yaml`)
- LLM-Frameworks + Integration Hub (`fusion_integration_hub.py`, `llm_frameworks.yaml`)
- Layer-Registry über alle 13 Layer (`fusion_hero_os/core/layer_registry.py`, v8.3)
- CI-gesichert: pytest-Suite + Proof-Registry-Gate + Erkenntnis-Index-Gate

## Roadmap-/Forschungs-Track: AscensionOS v9.x

`ascension_os/` enthält den visionären v9.x-Track (**nicht** der operative Kanon):

### 1. CoEvolutionaryClosure (CEC) v9.3
- MasterSeed Strict Contraction Enforcement (Runtime-Modell)
- Hyperthreading Track Management
- Coevolutionäre Event-Propagation

### 2. AscensionCore v9.4
- Hält Sisyphos, Psycholysis, LLM Core, MasterSeed
- Integriert GenerationalEvolutionEngine
- Nutzt PersistentSisyphosCycle

### 3. PersistentSisyphosCycle v9.4
- Volle Historie + JSON-Persistence
- Automatische CEC-Benachrichtigung

### 4. GenerationalEvolutionEngine
- Inside-Out Evolution, coevolutionär mit AscensionCore verbunden

Der Ascension-Track ist seit v8.3 als optionaler Layer (`ascension`) in
`fusion_unified.yaml` registriert und über die `QuadCoreBridge`
(`mode="ascension"`) aus dem Kanon heraus nutzbar.

## Architektur-Prinzipien

- **Inside-Out**: Alles beginnt im Kern (MasterSeed, Sisyphos) und strahlt nach außen.
- **Coevolutionär**: Komponenten beeinflussen sich kontrolliert gegenseitig.
- **Persistent + Stateful**: Wichtige Zustände (Sisyphos) werden persistiert.
- **Ehrlich**: Was gilt, steht in `proof_registry.yaml` und
  `docs/01_vision/V8_STATUS_REPORT.md` — Roadmap-Anspruch wird nicht als
  Ist-Zustand ausgegeben.

## Nächste logische Erweiterungen (Roadmap)

- HorkruxSelfUpdateProtocol
- Governance-fähige Self-Modification
- Volle Cross-Track-Synergie zwischen Heroic und Ascension
- Systemweiter EudaimoniaGuard
