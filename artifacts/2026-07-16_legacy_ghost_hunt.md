# Legacy Ghost Hunt — tiefe Analyse

**UTC/local:** 2026-07-16  
**Scope:** `fusion-hero-os` main (`6e27cd0` track) + `legacy_sources/**` + archive/stale branches  
**Methode:** Tree-Inventory, Dual-Registry, Import-Graph, Backlog, Branch-Compare, Geistersuche (unwired)

**Ergebnis in einem Satz:** Die „vergessenen“ Verbesserungen liegen fast alle **schon im Monorepo**, sind aber **nicht verdrahtet** — nicht auf ungemergten Archive-Branches.

---

## 1. Befund: Chaos-Topologie

| Oberfläche | Entry | Was lädt |
|------------|--------|----------|
| FastAPI Dashboard | `03_Code/Dashboard/app.py` | `03_Code/core/module_registry` + selektiv `fusion_hero_os.core.*` |
| Launcher | `start_fusion_hero.py` | IPC + optional Dashboard |
| NiceGUI root | `app.py` | nur `engine.mainframe` + agents |
| Package registry | `fusion_hero_os/registry.py` | ~18 Specs, **3 Stubs** |
| Dispatcher | `fusion_hero_os/modules/*` | BaseModules — **nicht** Dashboard-Default |

**Dual-Trees (Geister-Risiko):**

- `03_Code/**` vs `src/normal_os/**` (suite/core/connectors doppelt)
- `fusion_hero_os.core.poly_mesh_*` vs Root `fractal_mainframe_mesh.py` / `fusion_integration_hub.py`
- `qb_qubo.py` an mehreren Orten

---

## 2. Branch-Geister (Git)

Verglichene Tips (`private-hacking-suite`, `v8/main`, `main-knoten-proofs`, `claude/go-usjug2`, …):

| Branch | ahead of main | Bedeutung |
|--------|---------------|-----------|
| genannte Stale/Archive | **0** | strikte Ancestors — **kein** ungemergter Commit-Delta |
| `release/v9.0.0` | 1 (Version 9) | **nicht** mergen |
| `release/v10.0.0-stage-a` | 3 alt | bereits via #66 weitgehend in main |

**Fazit:** Archive-Branches erneut mergen bringt **keinen** Feature-Gewinn. Wert = **unwired mainline** + `legacy_sources/`.

Conflict-Marker live: **keine** (nur historische Erwähnung in Docs).

---

## 3. Ghost-Module (Auswahl)

### P0 — Ops (Code da, Keys/OAuth fehlen)

| Modul | Pfad | Lücke |
|-------|------|--------|
| Connectors live | `src/normal_os/connectors/*`, `connectors_routes.py` | OAuth/Keys oft leer |
| Google One / Drive | `google_one_sicherung`, Drive connector | Credentials |

### P1 — Verdrahten / de-stubben

| Ghost | Status | Empfehlung |
|-------|--------|------------|
| `mainframe_laden` | **registry stub=True** | Implement aus `autoloader` / suite `load_all` |
| `builder_profile` | stub | aus `heroic-core-foundation` + foundation gate |
| `skill_creator` | stub | SelfModify + kilo skills |
| `entwicklungsquant_{bus,live}.py` | real, **nicht** in module_registry | Dashboard registrieren |
| `fusion_hero_os/meta/**` | komplett, nicht auto-mount | Dashboard mount **oder** explizit lab-only |
| `mcp/fhero_mcp_server.py` | CLI only | opt-in in `start_fusion_hero.py` |
| `inference_scheduler_qubo` | MCP only | UI + MCP boot |
| `controller_aggregate` (v1.1) | **nur** legacy | Port Owner-Auth/Layer-Load |
| Mesh Hub-Splitter | root scripts + poly_mesh_* | **eine** Ops-Fläche im Dashboard |
| HeroicLLM-EA | `stub_llm` | echte Provider |
| Image orchestrator | dry-run | live provider + mister-builder-gui |

### P2 — Produktpfad öffnen

| Feature | Wo | Note |
|---------|-----|------|
| verification_orchestrator | `src/normal_os/core/verification_*` | nicht Dashboard-default |
| Horkrux gossip | Backlog E3 — **Datei fehlt** | nur Sync-Kernel da |
| TTS MessageBus | `tts/tts_router.py` | Piper partial, Swarm offen |
| Timespace + QUBO schedule UI | modules + core | kein Schedule-Panel |
| Comaedchen audio | core + YAML | manuell, nicht boot |
| private-hacking ghosthunt | `legacy_sources/.../ghosthunting` | research; Geisterjagd-Hook |
| SelfModifyCoreModule (legacy class) | FuHOS_pub | moderne Variante: `modules/self_modify.py` |

### P3 — Research / ignore for product

| Item | Why |
|------|-----|
| suite QUBO miner/PoW/wallet | Experiment, nicht Produkt-Mining |
| bare-metal `kernel/` außer bridge | QEMU research |
| Tkinter `heroic_core_gui*` | Launcher-Fallback |
| `fractal_ghost_hunt` artifacts | Streamlit viz |
| Nested `.git` under Dashboard | Accidental |
| `legacy_sources/**` full trees | Snapshots nach Cherry-Pick |

---

## 4. Legacy-Quellen-Karte

| Package | ~py | Ghost-Wert |
|---------|-----|------------|
| `private-hacking-suite` | 87 | ghosthunt, virology bench, highest_layer VR, LoRA train — **suite cherry-picked** |
| `FuHOS_pub` | 55 | SelfModifyCore, foundation gate, QUBO math — **teilweise portiert** |
| `normalOS` | 29 | connectors/Docker/VR — **parallel `src/normal_os`** |
| `AscensionOS` | 4 | psycholyse/eudaimonia — **ascension_os/** |
| `Fusion_Hero_OS_v1.1` | 10 | **controller_aggregate** = Port-Kandidat |
| foundation/manifest/kilo/gui | 0–2 | skills/prose |

Cherry-Pick-Log: `docs/v8/CHERRY_PICK_LOG.md` (suite 112 files).

---

## 5. Dual-Registry-Lücke

**`fusion_hero_os/registry.py`:** schmal (mainframe, agents, math, cec, 3 stubs, mining_qubo…).

**`03_Code/core/module_registry.py`:** breit (HT/GPU, suite_*, selfmod, highest_layer…).

Dashboard → 03_Code-Registry.  
NiceGUI root → fast nichts.  
→ Module wirken „tot“ je nach gestartetem Prozess.

---

## 6. Top-15 Recovery (priorisiert)

| # | Aktion | P |
|---|--------|---|
| 1 | Ops-Keys + OAuth Connectors live | P0 |
| 2 | Canonical tree wählen: `03_Code` **oder** `src/normal_os` dokumentieren | P0 |
| 3 | Entwicklungsquant-Bus → module_registry + Dashboard | P1 |
| 4 | Meta-neural: mount **oder** lab-only label | P1 |
| 5 | MCP opt-in in start_fusion_hero | P1 |
| 6 | Registry-Stubs implementieren (laden/builder/skill) | P1 |
| 7 | controller_aggregate port | P1 |
| 8 | Mesh-Entrypoints unifizieren | P1 |
| 9 | HeroicLLM-EA echte Provider | P1 |
| 10 | Image orchestrator live + builder GUI | P1 |
| 11 | verification_orchestrator → 03_Code path | P2 |
| 12 | Horkrux gossip implementieren (fehlt Datei) | P2 |
| 13 | TTS MessageBus | P2 |
| 14 | Timespace/QUBO Schedule UI | P2 |
| 15 | Miner/kernel/Tkinter nur archive | P3 |

**Doktrin:** **Wiring + De-Dup** vor Re-Import von `legacy_sources`.

---

## 7. Cleanup (sicher)

- `legacy_sources/**` nach Review behalten als Snapshot  
- Nested `.git` in Dashboard entfernen  
- `03_Code/reference/**`, doppelte `qb_qubo` → eine Kanon-Quelle  
- Stale remote branches taggen/archivieren  
- `baumeister-bob` remote tot → local ref aufräumen  

---

## 8. Geistersuche-Metaphor (ghosthunting)

Legacy enthält wörtlich `ghosthunting/run_ghosthunt.py` + `ghosthunt_hook` — Coevo-Layer-Diagnose.  
Produkt-Äquivalent auf main: **poly_mesh_router**, **race_guard**, **dependency_atlas**, **deficit board** — aber **kein** einheitlicher „GhostHunt“-Button im Dashboard.

---

*Erstellt: Legacy Ghost Hunt 2026-07-16 · Fusion Hero OS v10 · keine Branch-Re-Merges nötig.*
