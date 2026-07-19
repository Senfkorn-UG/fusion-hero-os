# Dauer-Eupression — continuous pressure by defined dependencies

**Stand:** 2026-07-19 · Platform v12.0.0  
**Modul:** `fusion_hero_os.core.dauer_eupression`  
**Catalog:** `fusion_hero_os/core/catalogs/dauer_eupression_deps.yaml`  
**State (local):** `~/.fusion/dauer_eupression.json`

## Principle

> Eupression without Eudaimon is stress; Eudaimon without Eupression is soft.

**Dauer-Eupression** = continuous *good pressure* applied **bottom-up** along an explicit dependency DAG — not ambient chaos, not one-shot pep talk.

## Dependency chain (bottom → top)

```
base_module
  └─ operator_identity
       └─ god_layer_seal
            └─ poly_fa_write_gate
  └─ dependency_atlas
       └─ layer_registry
poly_fa + atlas
  └─ meister_hasch_optimize
       └─ weltraudaimonia   (Eudaimon metric)
            └─ comaedchen_audio  (hear/speak person membrane)
```

| Node | Pressure role |
|------|----------------|
| base_module | structural contract |
| operator_identity | membrane (role ≠ person in git) |
| god_layer_seal | seal / unlock membrane |
| poly_fa_write_gate | structure write: desktop + request + Poly-FA |
| dependency_atlas | graph integrity (import/cycle honesty) |
| layer_registry | 13-layer graph |
| meister_hasch_optimize | sandkasten integrity |
| weltraudaimonia | Eudaimon score floor |
| comaedchen_audio | full hear/speak for private person |

## Continuous policy

- `continuous.enabled: true`
- min interval **60 s** between pulses (force with `--force`)
- **fail_closed** if a dependency is not satisfied (downstream blocked)
- Structure write still **poly_fa_only**
- Hear/speak remain **person surface open**

## CLI

```powershell
python -m fusion_hero_os.core.dauer_eupression --install
python -m fusion_hero_os.core.dauer_eupression --pulse --force
python -m fusion_hero_os.core.dauer_eupression --status
python -m fusion_hero_os.core.dauer_eupression --pulse --json-full
```

## Organs

| Organ | Continuous |
|-------|------------|
| **Eupression** | chain probes in topo order |
| **Eudaimon** | Weltraudaimonia score ≥ 0.5 floor |

## Honesty

- Catalog is **Spezifikation** (explicit YAML).  
- Scores are **Modell** (heuristic, not moral world-authority).  
- No legal names / unlock phrases in public status.
