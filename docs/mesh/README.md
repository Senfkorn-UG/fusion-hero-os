# Tailscale Mesh — Fusion Hero OS v10

> **Stand:** v10.0.0 · 2026-07-15 · Live inventory aligned  
> **Quelle der Wahrheit (Rollen):** `src/normal_os/integration/mesh_roles.yaml`  
> **Live-Snapshot:** `mesh_live_inventory.json`  
> **Registry:** `mesh_connectors.yaml` · Exit-Profile: `mesh_virtual_exit_nodes.yaml`

**Zweck:** Zero-Config Mesh-VPN + Phone-Bridge + Funnel für Mainframe und Peers.

## Prinzip: Jeder Konnektor = eigenes Teil

Kein Monolith. Jedes Mesh-Segment hat:

- **Eigene ID** (`mesh-connector-github`, `mesh-connector-gmail`, …)
- **Eigener Host-Knoten** (`mainframe` / `desktop` — physisch identisch)
- **Eigene Health-Probe** (`/mesh/{connector}/status`)
- **Eigener Tailscale-Tag** (`tag:fusion-connector-github`, …)

## Physische Knoten (Live 2026-07-15)

| Knoten | Rolle | MagicDNS | IP | Status |
|--------|-------|----------|-----|--------|
| `desktop-kpki9e4` | **Mainframe** (Windows Orchestrator) | `desktop-kpki9e4.tail391adb.ts.net` | `100.64.104.58` | online |
| `desktop` | Alias → mainframe | same | same | online |
| `redmi-note-13-pro-5g` | Phone (Android) | `redmi-note-13-pro-5g.tail391adb.ts.net` | `100.108.67.116` | online |
| `fusion-mesh-exit` | Cloud mesh anchor | `fusion-mesh-exit.tail391adb.ts.net` | `100.103.188.54` | online |
| `desktop-kpki9e4-wsl` | WSL dev-leaf | `desktop-kpki9e4-wsl.tail391adb.ts.net` | `100.125.58.100` | offline |
| `cs-724978827604-default` | Legacy GCP exit | `cs-724978827604-default.tail391adb.ts.net` | `100.127.145.106` | offline |

Tailnet: `tail391adb.ts.net`

## MCP-Konnektor-Segmente

| Konnektor | Mesh-ID | Host |
|-----------|---------|------|
| GitHub | `mesh-connector-github` | desktop |
| Gmail | `mesh-connector-gmail` | desktop |
| Google Drive | `mesh-connector-google-drive` | desktop |
| Google Calendar | `mesh-connector-google-calendar` | desktop |
| Canva | `mesh-connector-canva` | desktop |
| Gamma | `mesh-connector-gamma` | desktop |
| Notion | `mesh-connector-notion` | desktop |
| Vercel | `mesh-connector-vercel` | desktop |
| HyperFrames | `mesh-connector-hyperframes` | desktop |
| Tasks | `mesh-connector-tasks` | desktop |

## Setup (Windows Mainframe)

```powershell
# Tailscale up (hostname + unattended flags required when non-defaults exist)
tailscale up --hostname=desktop-kpki9e4 --unattended
tailscale status

# Full stack
powershell -File start_all.ps1

# Fast-Boot Dashboard only
$env:FUSION_AUTO_LOAD = "0"
# then: uvicorn in 03_Code/Dashboard on :8000
```

Scripts: `workstation/tailscale_install.ps1`, `workstation/mainframe_mesh_setup.ps1`, `tailscale_control.sh`.

## URLs

| Surface | URL |
|---------|-----|
| Dashboard (local) | http://127.0.0.1:8000 |
| Dashboard (mesh) | http://desktop-kpki9e4.tail391adb.ts.net:8000 |
| Hero Docs / mesh status | https://desktop-kpki9e4.tail391adb.ts.net (Funnel, if enabled) |
| Health light | http://127.0.0.1:8000/api/health?light=true |

## Dateien

| Datei | Zweck |
|-------|-------|
| `mesh_live_inventory.json` | Live Tailscale snapshot (commit when topology changes) |
| `mesh_connectors.yaml` | Registry aller Segmente + physische Nodes |
| `mesh_virtual_exit_nodes.yaml` | Virtual exit profiles |
| `src/normal_os/integration/mesh_roles.yaml` | Kanonische Rollen (Single Source of Truth) |
| `tailscale_mesh_registry.py` | Health-Probes |
| `fractal_mainframe_mesh.py` | Fractal mesh orchestration |
| `mesh_file_share.py` | Phone file share / mirror |

---

**Layer 0 verankert** — Mesh ist natives Modul des ALTE_Frau_95g Heroic Core (Mainframe = Windows-Desktop).
