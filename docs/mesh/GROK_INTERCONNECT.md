# Grok Interconnect — Abgreifen & Weiterentwickeln

**Modul:** `fusion_hero_os/core/grok_interconnect.py`  
**UI:** http://127.0.0.1:8000/mainframe/grok  
**API:** `GET /api/grok/interconnect` · `POST /api/grok/interconnect/capture`  
**State:** `~/.fusion/grok_interconnect.json` (race-guard atomic)

## Zweck

1. **Abgreifen** — Live-Graph aller Grok-Knoten und Kanten  
2. **Weiterentwickeln** — Intent-Map, Growth-Flags, Architektur-Empfehlungen  

**Dissertation-as-OS:** Interconnect ist Ausdrucksorgan der Dissertation (das OS *ist* die Arbeit; Text nur eine Form) — siehe `docs/dissertation/ONTOLOGIE_DISSERTATION_IST_DAS_OS.md`.  

## Knoten (Auszug)

| ID | Kind | Rolle |
|----|------|--------|
| grok-cli | cli | Grok Build CLI |
| grok-skill | skill | `~/.grok/skills/fusion-hero-os` |
| grok-bridge | bridge | Dashboard Intent-Bridge |
| grok-llm | llm | xAI API Framework |
| grok-pc-bridge | bridge | optional :8765 |
| dashboard | surface | :8000 |
| mainframe-* | surface | Hub / VR / IDE / Worktree |
| tailscale-mesh | mesh | Operator host |
| gce-publish | mesh | L2 PDF mirror |
| mcp-host | host | MCP session host |
| mesh-coordinator | host | coord latest.json |
| sync-grok-intern | sync | Skill/Workspace mirror |

## Bridge-Intents (erweitert)

`interconnect`, `mainframe`, `dauer_vr`, `ide`, `worktree`, `mesh`, `publish`, `race_guard`, `ops` (+ bestehende load_all, qubo, …)

## CLI

```powershell
cd C:\Users\Admin\fusion-hero-os
python -m fusion_hero_os.core.grok_interconnect
# or
python -c "from fusion_hero_os.core.grok_interconnect import capture, evolve; print(evolve(capture()).health_score)"
```

## Umroutung (canonical)

Alle Intents laufen über `fusion_hero_os.core.grok_route_table`  
(Dissertation-as-OS: die Route-Table ist **Autopolitik** der Arbeit, nicht nur API-Doku):

| Intent | Surface |
|--------|---------|
| interconnect | `/mainframe/grok` |
| mainframe | `/mainframe` |
| dauer_vr | `/mainframe/vr` |
| ide | `/mainframe/ide` |
| worktree | `/mainframe/worktree` |
| ops | `/mainframe/ops` |
| chat | `/api/grok/chat` (+ redirect_hint) |

Legacy redirects: `/grok` → `/mainframe/grok`, `/ide` → `/mainframe/ide`, `/worktree` → `/mainframe/worktree`, `/portal` → `/mainframe`, `/vr/persistent` → `/mainframe/vr`, `/api/interconnect` → `/api/grok/interconnect`.

Route APIs:
- `GET /api/grok/route?intent=ide`
- `GET /api/grok/route?message=öffne%20dauer%20vr`
- `GET /api/grok/routes` — volle Tabelle
