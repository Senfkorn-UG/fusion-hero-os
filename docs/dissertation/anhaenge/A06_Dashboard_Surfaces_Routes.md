# A06 — Dashboard, Surfaces, Routes: Herleitung

**Pfad:** `03_Code/Dashboard/` (+ `fusion_hero_os/bridge/`)  
**Port:** `8000` (Spezifikation Default)  

---

## Synthese

Das Dashboard ist die **Haut** der Dissertation: wo der Organismus berührbar wird. Surfaces sind keine Dekoration; sie sind Ausdrucksorgane (Dissertation-as-OS). Hier: vom HTTP-Nichts zur Route-Table.

---

## Bogen 1 — Prozess und Exklusivität

**[Herleitung]** Zwei Server auf einem Port → Chaos. Also Lock.

**[Spezifikation]** `core.process_exclusivity` / Dashboard `_acquire_dashboard_lock` → Key `dashboard:8000`.

**[Spezifikation]** Fast-Boot: `FUSION_AUTO_LOAD=0`.

---

## Bogen 2 — App-Kern und Router-Include

**[Spezifikation]** `app.py` bindet u. a.:

- VR / Architecture / Ops  
- `mainframe_site_routes`  
- `grok_interconnect_routes`  
- Extensions / Bridge-Endpunkte  

---

## Bogen 3 — Surfaces (Mainframe Website)

| Surface | Pfad | Organ |
|---------|------|-------|
| Hub | `/mainframe` | Portal |
| Grok Interconnect | `/mainframe/grok` | Control Plane |
| Dauer-VR | `/mainframe/vr` | Embodied View |
| IDE | `/mainframe/ide` | Editor |
| Worktree | `/mainframe/worktree` | Hyperlink-Repo |
| Ops | `/mainframe/ops` | Kosten/Repo |

**Legacy 307:** `/grok`, `/ide`, `/worktree`, `/portal`, `/vr/persistent`, `/api/interconnect`, …  
**Spezifikation:** `grok_interconnect_routes.py` + `grok_route_table.LEGACY_REDIRECTS`.

---

## Bogen 4 — Bridge und Input-Gateway

| Modul | Funktion | Geltung |
|-------|----------|---------|
| `grok_bridge` | Intent-Erkennung, Chat-Kontext, `route_plan` | Spezifikation |
| `input_gateway` | `validate_input`, `classify_message`, `accept_input` | Spezifikation |
| `api_extensions` | `/api/grok/chat`, status, route_plan | Spezifikation |

**[Herleitung]** Nachricht → Intents → `resolve` → Surface/API-Hints → Worker oder Sync.

---

## Bogen 5 — Bridge-Paket im Core

| Modul | API | Rolle |
|-------|-----|-------|
| `bridge.gateway.IPCGateway` | `dispatch`, `status`, math/orch status | IPC |
| `bridge.router` | `route_dispatch`, `handle_ipc_message`, `route_list_modules` | Routing |

---

## Bogen 6 — Weitere Dashboard-Organe (Übersicht)

| Datei | Rolle (kurz) |
|-------|----------------|
| `autoloader.py` | Modul-Autoload |
| `connectivity.py` | Ports, Access Points |
| `mainframe_ops_routes.py` | Ops APIs |
| `mainframe_site_routes.py` | Worktree/IDE/Site APIs |
| `vr_routes.py` | VR Viewer |
| `watch_*` | Watch-Party Sync |
| `worker_tasks.py` / `process_worker.py` | Async Workers |
| `faden_store.py` | Faden/State |
| `supabase_*` | optionale Sync-Membran |

**Details:** Source; AST-Katalog deckt primär `fusion_hero_os` (A10). Dashboard-Python ist **Spezifikation im Tree**.

---

## Anhang A06 — Control-Plane-Minimalpfad

```text
GET /api/grok/routes          → all_routes()
GET /api/grok/route?intent=ide → resolve("ide")
GET /mainframe/grok           → HTML Interconnect
GET /grok                     → 307 /mainframe/grok
```
