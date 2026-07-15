# Tailscale Mesh - Fusion Hero OS v10

> **Stand:** v10.0.0 - public docs use placeholders only  
> **Roles:** `src/normal_os/integration/mesh_roles.yaml`  
> **Registry:** `mesh_connectors.yaml` - Exit profiles: `mesh_virtual_exit_nodes.yaml`  
> **Coordination:** `mesh_service_coordination.yaml` + `docs/mesh/SERVICE_COORDINATION.md` (inhouse vs external + GKE placement)

**Purpose:** Mesh VPN + phone bridge + optional funnel for mainframe and peers.  
**Coordination purpose:** Cluster-backed inventory/placement so external SaaS and in-house modules share one routing truth.

**Dissertation-as-OS:** Mesh + coordinator are *organs of the dissertation* (the OS *is* the work; text is one expression). See `docs/dissertation/ONTOLOGIE_DISSERTATION_IST_DAS_OS.md`. Canonical re-routes: `docs/mesh/GROK_INTERCONNECT.md`, control plane `/mainframe/grok`.

**Power Mesh Fusion (bottom-up Langzeit):** long-term evolution of mesh+power+fusion strata as dissertation organs — `power_mesh_fusion_evolution.yaml`, `python -m fusion_hero_os.core.power_mesh_fusion_evolution`, dissertation annex **A12**.

## Principle

Each connector is its own mesh segment (ID, host role, health path, Tailscale tag).

## Node roles (placeholders)

| Role | Example hostname key | Platform | Notes |
|------|----------------------|----------|--------|
| mainframe | `mainframe` | windows | Canonical orchestrator |
| desktop | alias of mainframe | windows | Workstation / enduser peer of phone |
| phone | `phone` | android | Mobile enduser |
| mesh-exit | `mesh-exit` | linux | Optional cloud anchor |
| wsl | `mainframe-wsl` | linux | Optional dev leaf |

Live hostnames, MagicDNS names, Tailscale IPs, and node IDs are **operator-local**.  
Do not commit `mesh_live_inventory.json` or real CGNAT addresses.

## Setup (operator machine)

```powershell
tailscale up --hostname=<your-mainframe-hostname> --unattended
tailscale status
powershell -File start_all.ps1
```

## Local URLs (examples)

| Surface | Example |
|---------|---------|
| Dashboard local | http://127.0.0.1:8000 |
| Health light | http://127.0.0.1:8000/api/health?light=true |
| Mesh MagicDNS | `https://<your-host>.<your-tailnet.ts.net>` (private) |

See root `mesh_connectors.yaml` and `mesh_roles.yaml` for public placeholder registries.
