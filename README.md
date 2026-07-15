# Fusion Hero OS

[![Release](https://img.shields.io/badge/Release-v10.0.0-00C853?style=for-the-badge&logo=github)](https://github.com/95guknow/fusion-hero-os/releases/tag/v10.0.0)
[![Platform](https://img.shields.io/badge/Platform-10.0.0-blue?style=for-the-badge)](VERSION)
[![Governance](https://img.shields.io/badge/Governance-Stage_A%2FB-1E88E5?style=for-the-badge)](#stage-ab-governance)

´´
**Hybrid AI / mainframe platform** | operative kanon **v10.0.0**  
Core: **ALTE_Frau_95g Heroic Core** | additive over the v8.3 stack (BCG)

## ´´
> This public repository must not contain personal profile data, private
> locations, or live Tailscale inventory (IPs, node IDs, private MagicDNS).
> Runtime topology lives only on the operator machine / private config.``

---

## Architecture

```
[ Dashboard :8000  GUI + REST + WS ]
              |
              v
[ Mainframe core: fusion_hero_os / ALTE_Frau_95g ]
  QUBO | multi-agent | layer registry | AutoLoad | mesh registry
              |
              v
[ Tailscale mesh + MCP connector segments ]
  (roles/config in repo = placeholders; live values stay local)
```

| Layer | Content | Status |
|-------|---------|--------|
| Platform v10.0.0 | Unified versioning, Stage-A/B gates | operative |
| Heroic stack (ex-v8.3) | QUBO, agents, layers, mesh, dashboard | operative |
| AscensionOS v9.x | `ascension_os/` CEC, AscensionCore, Sisyphos | loadable / roadmap |

```typescript
const fusionHeroOS = {
  version: "10.0.0",
  tag: "v10.0.0",
  system_state: "Operational + Governed",
  compatibility: "Backward-compatible with v8.3 baseline (BCG)",
  active_core: "ALTE_Frau_95g Heroic Core",
  layers: [
    "Stage-A: privacy, consent gate, archive scrypt KDF, version unity",
    "Stage-B: depersonalization + persona/PII regression scanners",
    "Operative stack: QUBO, multi-agent, 13-layer registry, mesh, dashboard",
    "AscensionOS v9.x: loadable roadmap (not sole kanon claim)",
  ],
};
```

See [BEST_VERSION.md](BEST_VERSION.md) for honest operative vs roadmap status.

---

## Quick Start

```powershell
# Full boot (AutoLoad can take minutes)
powershell -File start_all.ps1

# Fast-Boot (recommended)
cd 03_Code\Dashboard
$env:FUSION_AUTO_LOAD = "0"
$env:FUSION_HYPERTHREADING = "1"
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

| Endpoint | Purpose |
|----------|---------|
| http://127.0.0.1:8000 | Standard GUI |
| `/api/health?light=true` | Fast health probe |
| `/api/health` | Full status |
| `/docs` | OpenAPI |
| `/ws` | Live events |
| `/architecture` | Dependency atlas |

Full guide: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Version gates

```powershell
python scripts/bump_version.py --check
python -m pytest tests/test_version_consistency.py `
  tests/test_archive_salt.py tests/test_ascension_consent.py `
  tests/test_asset_persona_paths.py tests/test_persona_scanner.py `
  tests/test_pii_scanner.py -q
```

---

## Tailscale Mesh

**Principle:** each connector is its own mesh segment (ID, host, health, tag).  
**Mainframe role:** Windows orchestrator (canonical in `mesh_roles.yaml`).

Public configs use **placeholders only**. Do not commit live inventory.

| File | Role |
|------|------|
| `mesh_connectors.yaml` | Segment registry (placeholder hostnames) |
| `src/normal_os/integration/mesh_roles.yaml` | Role assignments |
| `mesh_virtual_exit_nodes.yaml` | Exit profiles (placeholders) |
| [docs/mesh/README.md](docs/mesh/README.md) | Ops notes |

```powershell
# Operator machine only - never commit the resulting inventory JSON
tailscale up --hostname=<your-mainframe-hostname> --unattended
tailscale status
```

---

## Stage-A/B Governance

| Stage | Shipped |
|-------|---------|
| **A** | PII cleanup, consent gate, archive scrypt KDF, version consistency |
| **B** | Package depersonalization, persona/PII regression scanners |

Public surface policy: no personal identity, no private location, no live mesh inventory in this repo.

---

## Tech Stack

| Domain | Stack |
|--------|--------|
| Runtime | Python 3.11+ / FastAPI / Uvicorn / Numba |
| Performance | Rust crates (`pms_rust_kernel_crate`, `rust_engine_crate`) |
| Mesh | Tailscale / per-connector registry |
| AI | Local model hooks / Integration Hub (external connectors dry-run by default) |
| CI | pytest Stage-A/B / proof-registry / version gate |

---

## Documentation

| Doc | Role |
|-----|------|
| [BEST_VERSION.md](BEST_VERSION.md) | Operative kanon vs roadmap |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Boot / ports / troubleshooting |
| [BRANCH_STRATEGY.md](BRANCH_STRATEGY.md) | SemVer / tags |
| [docs/mesh/README.md](docs/mesh/README.md) | Mesh ops (placeholders) |
| [docs/v8/](docs/v8/) | v8 consolidation notes |
| [ascension_os/](ascension_os/) | Ascension track (loadable) |

---

## Modules

- **fusion_hero_os/** - core package `10.0.0` (Active)
- **03_Code/Dashboard/** - mainframe GUI + API (Active)
- **Mesh tooling** - registries + scripts (config placeholders public; live data local)
- **CI gates** - Stage-A/B pytest (Enforced)

---
``

**Release:** [v10.0.0](https://github.com/95guknow/fusion-hero-os/releases/tag/v10.0.0)
