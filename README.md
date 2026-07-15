<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20,24,25&height=180&section=header&text=Fusion%20Hero%20OS%20v10&fontSize=50&fontColor=fff&fontAlignY=35&desc=Hybrid%20Architecture%20%7C%20Governance%20%26%20Operational%20Continuity&descAlignY=58&descSize=18" />

<div align="center">

[![Release](https://img.shields.io/badge/Release-v10.0.0-00C853?style=for-the-badge&logo=github)](https://github.com/95guknow/fusion-hero-os/releases/tag/v10.0.0)
[![Architecture](https://img.shields.io/badge/Architecture-Hybrid-blueviolet?style=for-the-badge)](#-architecture)
[![Compliance](https://img.shields.io/badge/Compliance-Stage_A%2FB_Active-1E88E5?style=for-the-badge)](#-stage-ab-governance)
[![Runtime](https://img.shields.io/badge/Runtime-Operational-00ACC1?style=for-the-badge)](#-quick-start)
[![Mesh](https://img.shields.io/badge/Mesh-Tailscale_Live-7C4DFF?style=for-the-badge)](#-tailscale-mesh)

<a href="https://github.com/95guknow/fusion-hero-os">
  <img src="https://readme-typing-svg.demolab.com/?font=Fira+Code&size=18&pause=1000&color=9333EA&center=true&vCenter=true&width=720&lines=Fusion+Hero+OS+v10.0.0+Operational;Mainframe+%7C+Heroic+Core+%7C+Tailscale+Mesh;Stage-A%2FB+Governance+%2B+v8.3+Stack+(BCG);Dashboard+http%3A%2F%2F127.0.0.1%3A8000" alt="Typing SVG" />
</a>

**KI-OS / Hybrid Mainframe** · Platform `10.0.0` · Tag [`v10.0.0`](https://github.com/95guknow/fusion-hero-os/releases/tag/v10.0.0)  
Maintainer: [95guknow](https://github.com/95guknow) · Core: **ALTE_Frau_95g Heroic Core**

</div>

---

<div align="center">

### Navigation

[Overview](#-release-overview) ·
[Architecture](#-architecture) ·
[Quick Start](#-quick-start) ·
[Mesh](#-tailscale-mesh) ·
[Governance](#-stage-ab-governance) ·
[Docs](#-documentation) ·
[Tech](#-tech-stack)

</div>

---

## Release Overview

```typescript
const fusionHeroOS = {
  version: "10.0.0",
  tag: "v10.0.0",
  concept: "Hybrid README · Hybrid Architecture · Mainframe-aligned",
  system_state: "Operational + Governed",
  compatibility: "Backward-compatible with v8.3 functional baseline (BCG)",
  active_core: "ALTE_Frau_95g Heroic Core",
  mainframe: {
    host: "desktop-kpki9e4",
    role: "Windows orchestrator",
    dashboard: "http://127.0.0.1:8000",
    mesh_ip: "100.64.104.58",
  },
  layers: [
    "Stage-A: privacy, consent gate, archive scrypt KDF, version unity",
    "Stage-B: depersonalization + persona/PII regression scanners",
    "Operative stack: QUBO, multi-agent, 13-layer registry, mesh, dashboard",
    "AscensionOS v9.x: loadable roadmap track (not sole kanon claim)",
  ],
};
```

| Claim | Verified (2026-07-15) |
|-------|------------------------|
| `VERSION` / manifests | `10.0.0` (`bump_version.py --check`) |
| GitHub release | [v10.0.0](https://github.com/95guknow/fusion-hero-os/releases/tag/v10.0.0) |
| Package | `fusion_hero_os.__version__ == "10.0.0"` |
| Dashboard light-health | `{"status":"ok","backend":"online"}` |
| Tailscale | Running · self `desktop-kpki9e4` |
| Capsule-render / SVG header | HTTP 200 (`image/svg+xml`) |

> **Honesty rule:** Roadmap language (Ascension v9.x “full autonomy”) is not claimed as shipped. See [`BEST_VERSION.md`](BEST_VERSION.md).

---

## Architecture

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=24,25,6&height=70&section=header&text=System%20Architecture&fontSize=28&fontColor=fff&fontAlignY=65&animation=fadeIn" width="100%" />
</div>

```text
┌─────────────────────────────────────────────────────────────┐
│  Standard GUI + REST + WS          http://127.0.0.1:8000    │
│  03_Code/Dashboard/app.py  ·  Fast-Boot: FUSION_AUTO_LOAD=0 │
└────────────────────────────┬────────────────────────────────┘
                             │ in-process
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Mainframe Core (ALTE_Frau_95g / fusion_hero_os)            │
│  QUBO · Multi-Agent · Layer Registry (13) · Hyperthreading  │
│  AutoLoad · Integration Hub · Mesh registry                 │
└────────────────────────────┬────────────────────────────────┘
                             │ Tailscale mesh
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Peers: phone · fusion-mesh-exit · WSL (optional)           │
│  MCP segments: GitHub, Gmail, Drive, Calendar, …            │
│  Inventory: mesh_live_inventory.json                        │
└─────────────────────────────────────────────────────────────┘
```

| Layer | Content | Status |
|-------|---------|--------|
| **Platform v10.0.0** | Unified versioning, Stage-A/B gates | **operative** |
| **Heroic stack (ex-v8.3)** | QUBO, agents, layers, mesh, dashboard | **operative** (kept) |
| **AscensionOS v9.x** | CEC, AscensionCore, Sisyphos in `ascension_os/` | **loadable / roadmap** |

---

## Quick Start

```powershell
# Full boot (can take minutes under AutoLoad)
powershell -File start_all.ps1

# Fast-Boot (recommended for interactive work)
cd 03_Code\Dashboard
$env:FUSION_AUTO_LOAD = "0"
$env:FUSION_HYPERTHREADING = "1"
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

| Endpoint | Purpose |
|----------|---------|
| http://127.0.0.1:8000 | Standard GUI |
| `/api/health?light=true` | Fast probe |
| `/api/health` | Full status (may block under heavy AutoLoad) |
| `/api/docs` | OpenAPI |
| `/ws` | Live events |
| `/architecture` | Dependency Atlas |

Details: [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)

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

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=11,20,24&height=70&section=header&text=Tailscale%20Mesh&fontSize=28&fontColor=fff&fontAlignY=65&animation=fadeIn" width="100%" />
</div>

**Principle:** every connector is its own mesh segment (ID, host, health, tag).  
**Mainframe = Windows desktop** (`desktop-kpki9e4`), not a separate Linux box.

| Node | Role | IP | Status |
|------|------|-----|--------|
| `desktop-kpki9e4` | Mainframe / orchestrator | `100.64.104.58` | online |
| `redmi-note-13-pro-5g` | Phone | `100.108.67.116` | online |
| `fusion-mesh-exit` | Cloud anchor | `100.103.188.54` | online |
| `desktop-kpki9e4-wsl` | WSL leaf | `100.125.58.100` | offline |
| `cs-724978827604-default` | Legacy exit | `100.127.145.106` | offline |

```powershell
tailscale up --hostname=desktop-kpki9e4 --unattended
tailscale status
```

Full mesh ops: [`docs/mesh/README.md`](docs/mesh/README.md) · registries: `mesh_connectors.yaml`, `mesh_roles.yaml`, `mesh_live_inventory.json`

---

## Stage-A/B Governance

| Stage | What shipped |
|-------|----------------|
| **A** | PII cleanup, Ascension consent gate (fail-closed), archive scrypt KDF (`archiv` v2 / salt `fusion-hero-os\|archiv\|v10`), version consistency |
| **B** | Active-package depersonalization, persona-token regression scanners |

```typescript
const governance = {
  stage_a: ["privacy", "consent_gate", "scrypt_archive_kdf", "version_unity"],
  stage_b: ["depersonalization", "persona_scanners"],
  bcg: "strict additive evolution — no drop of v8.3 capabilities",
};
```

Threat model notes: [`docs/meta_neural/THREAT_MODEL.md`](docs/meta_neural/THREAT_MODEL.md)

---

## Tech Stack

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=70&section=header&text=Tech%20Stack&fontSize=28&fontColor=fff&fontAlignY=65&animation=fadeIn" width="100%" />
</div>

<div align="center">

<a href="https://skillicons.dev">
  <img src="https://skillicons.dev/icons?i=python,linux,windows,githubactions,git,bash,md,fastapi,rust&theme=dark&perline=9" alt="Skill icons" />
</a>

</div>

| Domain | Stack |
|--------|--------|
| Runtime | Python 3.11+ · FastAPI · Uvicorn · Numba |
| Kernel / speed | Rust crates (`pms_rust_kernel_crate`, `rust_engine_crate`) |
| Mesh | Tailscale · MagicDNS · per-connector registry |
| AI | Local Llama / Ollama hooks · Integration Hub (dry-run default for external connectors) |
| Data | SQLite/SQLModel paths · optional Supabase sync |
| CI | pytest Stage-A/B · proof-registry · version gate |

---

## Documentation

| Doc | Role |
|-----|------|
| [`BEST_VERSION.md`](BEST_VERSION.md) | Operative kanon vs roadmap (source of truth narrative) |
| [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) | Boot, ports, troubleshooting |
| [`BRANCH_STRATEGY.md`](BRANCH_STRATEGY.md) | SemVer · tags · MAJOR 10 era |
| [`docs/mesh/README.md`](docs/mesh/README.md) | Mesh ops (rescued + v10-aligned) |
| [`docs/v8/`](docs/v8/) | v8 consolidation / erkenntnisse |
| [`ascension_os/`](ascension_os/) | Ascension track (loadable) |

---

## System Map (operative modules)

* **Fusion Hero OS core** — `fusion_hero_os/` (QUBO, orchestration, modules registry)  
  Status: `Active` · version `10.0.0`
* **Dashboard Mainframe** — `03_Code/Dashboard/`  
  Status: `Active` · light-health verified
* **Tailscale Mesh** — registries + `fractal_mainframe_mesh.py`  
  Status: `Live`
* **Local AI orchestration** — Integration Hub / llama-local hooks  
  Status: `Configured` (provider auto; heavy models optional)
* **Immune system (CI)** — pytest Stage-A/B + version gate  
  Status: `Enforced`

---

## Telemetry (GitHub)

<div align="center">

<img src="https://github-readme-stats.vercel.app/api?username=95guknow&show_icons=true&theme=tokyonight&hide_border=true" width="48%" alt="GitHub stats" />
<img src="https://streak-stats.demolab.com/?user=95guknow&theme=tokyonight&hide_border=true" width="48%" alt="Streak" />

<br/>

<img src="https://github-readme-stats.vercel.app/api/top-langs/?username=95guknow&layout=compact&theme=tokyonight&hide_border=true" width="48%" alt="Top languages" />

</div>

---

## License & Core notice

Platform code: see repository license files where present.  
**Heroic Core / Mainframe policy:** solutions under ALTE_Frau_95g operate with BCG (backward-compatible additive evolution) and code-honesty (no capability claimed without implementation).

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20,24,25&height=120&section=footer&text=Layer%200%20anchored%20%7C%20v10.0.0%20operational&fontSize=18&fontColor=fff&fontAlignY=55" width="100%" />

**Fusion Hero OS** · Mainframe online · Mesh inventory committed · Release [`v10.0.0`](https://github.com/95guknow/fusion-hero-os/releases/tag/v10.0.0)

</div>
