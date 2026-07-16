# OS → Poly-Mesh Port

**Stand:** 2026-07-16 · Fusion Hero OS **v10.0.0**  
**Manifest:** `mesh_os_port.yaml`  
**Runtime:** `fusion_hero_os.core.poly_mesh_os_port`  
**CLI:** `python scripts/port_os_poly_mesh.py`

## Ziel

Das **gesamte OS** als Organ-Set ins **Poly-Mesh** portieren:

| Tier | Rolle | OS-Organe |
|------|--------|-----------|
| L0 | Phone edge | AudioRelay client, capture |
| L1 | Mainframe | Dashboard, Hyperraum/Business API, Grok, Operator, Headset |
| L2 | Mesh exit | Publish mirror, fractal, always-on |
| L3 | GKE | Coordination Cron, Training |
| L4 | SaaS | MCP-Membranen (nie Source-of-Truth) |

## Was „porten“ heißt

1. **Inventar** Tailscale + GKE  
2. **Registry** Organe → Mesh-URLs (`http://100.x:8000/...`)  
3. **Optional Serve** `tailscale serve` (Mesh-sichtbar, kein Funnel = nicht öffentlich)  
4. **Coordinator** Placement-Plan  
5. **Headset mesh_only** erzwingen  

**Nicht:** Secrets/MCP vom Mainframe nehmen · OS als Tailscale-„Apps“ SaaS-Eintrag (falsche UI).

## CLI

```powershell
# Full port
python scripts/port_os_poly_mesh.py
# or
powershell -File workstation\port-os-poly-mesh.ps1

# Status only
python -m fusion_hero_os.core.poly_mesh_os_port --status

# Dashboard must be up for mesh URLs to answer:
powershell -File start_all.ps1
# then re-serve if needed:
tailscale serve --bg 8000
```

## Registry (operator-local)

`~/.fusion/mesh/os_port/latest.json`

## Mesh URLs (Beispiel)

Nach Port auf L1 `desktop-kpki9e4` / `100.64.104.58`:

- `http://100.64.104.58:8000/` — Dashboard  
- `http://100.64.104.58:8000/api/hyperraum` — Hyperraum  
- `http://100.64.104.58:8000/api/v1/business` — Business  

Phone/Peers im Tailnet erreichen das **ohne LAN**.

## Anti-Patterns

- Tailscale **Apps** (SaaS domain routing) mit Fusion Hero OS verwechseln  
- AudioRelay über 192.168.x bei mesh_only  
- GKE-Pod als Source-of-Truth für Secrets  
- Funnel ohne explizite Operator-Freigabe  

## Algorithmus-Orchestrierung (perfekt)

Sole authority: `poly_mesh_router`  
Orchestrator: `fusion_hero_os.core.poly_mesh_orchestrator`

```powershell
# Plan + coherence score (0-100)
python scripts/orchestrate_poly_mesh.py

# Execute: coordinator + dual-start asserts + OS port + headset mesh_only
python scripts/orchestrate_poly_mesh.py --execute
```

Waves: L1 control → L2 replica → L3 force_cluster → L0 edge → general.  
Perfect = score 100, no dual-start, force_cluster on L3 or blocked, control plane L1.

State: `~/.fusion/mesh/orchestration/last_report.json`  
Summary: `docs/mesh/poly_mesh_orchestration.summary.json`

## Verwandt

- `docs/mesh/SERVICE_COORDINATION.md`  
- `docs/mesh/POLY_MESH_OFFLOAD_STATUS.md`  
- `docs/architecture/API_PLANE_SEPARATION.md`  
- `workstation/force-headset-mesh-only.ps1`  

