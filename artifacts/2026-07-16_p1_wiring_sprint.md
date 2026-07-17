# P1 Wiring Sprint — complete

**UTC/local:** 2026-07-16  
**Platform:** Fusion Hero OS v10.0.0

## Done

### 1. Registry stubs → real modules
| Module | Status | API |
|--------|--------|-----|
| `modules.mainframe_laden` | **loaded** (was stub) | `load_all()`, boot via `--mainframe-laden` |
| `modules.builder_profile` | **loaded** | foundation gate from `01_Framework/heroic-core-foundation` |
| `modules.skill_creator` | **loaded** | `propose_skill()` declarative SKILL.md |

Also registered: `core.poly_mesh_router`, `core.poly_mesh_orchestrator`, `core.inference_scheduler_qubo`.

### 2. MCP opt-in
```text
python start_fusion_hero.py --with-mcp
python start_fusion_hero.py --with-dashboard --with-mcp --mainframe-laden
```
Starts `python -m fusion_hero_os.mcp.fhero_mcp_server` (stdio JSON-RPC).

### 3. Entwicklungsquant
- `03_Code/core/module_registry.py` → `entwicklungsquant_bus` + `poly_mesh_ops`
- Bus import smoke: available=True

### 4. Mesh Ops API (Dashboard)
| Method | Path |
|--------|------|
| GET | `/api/mesh/ops` |
| GET | `/api/mesh/ops/tailscale` |
| GET | `/api/mesh/ops/funnel` |
| GET | `/api/mesh/ops/poly` |
| GET | `/api/mesh/ops/entwicklungsquant` |
| GET | `/api/mesh/ops/p1` |
| POST | `/api/mesh/ops/mainframe-laden` |

Wired in `app.py` via `mesh_ops_routes`.

## Verify
```powershell
$env:PYTHONPATH="C:\Users\Admin\fusion-hero-os;C:\Users\Admin\fusion-hero-os\03_Code"
python -c "from fusion_hero_os.registry import Registry; r=Registry(); print(r.load('modules.mainframe_laden').status)"
# with dashboard up:
# curl http://127.0.0.1:8000/api/mesh/ops
```

## Not in this sprint (by design)
- P0 OAuth/keys
- P2 Horkrux gossip / TTS swarm
- P3 miner/kernel
