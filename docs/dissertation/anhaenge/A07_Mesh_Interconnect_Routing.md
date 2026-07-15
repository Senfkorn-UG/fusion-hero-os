# A07 — Mesh, Interconnect, Routing: Herleitung

**YAML:** `mesh_connectors.yaml`, `fusion_unified.yaml`, `mesh_service_coordination.yaml`  
**Code:** `grok_route_table`, `grok_interconnect`, `race_guard`, Coordinator-Skripte  

---

## Synthese

Ein Organismus mit verteilten Organen braucht **Membranen** (MCP/SaaS), **Nerven** (Tailscale), **Koordination** (Placement L0–L4) und **eine Wahrheitstabelle der Wege** (Route-Table). Hier aus dem Nichts.

---

## Bogen 1 — Verbindung

**[Definition]** *Mesh-Node* = Host mit Rolle, Health-Pfad, Tag (Platzhalter public).

**[Spezifikation]** `mesh_connectors.yaml` — principle: jeder Konnektor eigenes Segment.  
**[Spezifikation]** `ontology: dissertation_as_os` im YAML-Kommentarfeld/Key.

**[Nicht im Public Repo]** Live-IPs, MagicDNS real — operator-local.

---

## Bogen 2 — Placement als Autopolitik

**[Herleitung]**

1. Arbeit hat Kosten und Sensibilität.  
2. Nicht jede Arbeit gehört in die Cloud.  
3. Also Tiers:

| Tier | Ort | Beispiel |
|------|-----|----------|
| L0 | Edge/Phone | Journal |
| L1 | Mainframe | Dashboard, MCP, Consent |
| L2 | Mesh-Exit | Publish-Mirror, durable |
| L3 | Cluster | Training, heavy QUBO |
| L4 | SaaS | nie Source-of-Truth |

**[Spezifikation]** `docs/mesh/SERVICE_COORDINATION.md`, `mesh_cluster_coordinator.py`.

---

## Bogen 3 — Race-Guard (Gleichzeitigkeit)

**[Herleitung]** Desktop + GCE-Cron + optional Cluster schreiben JSON → ohne Lock: Korruption.

**[Spezifikation]** `race_guard.py`:

| API | Mechanik |
|-----|----------|
| `FileLock` | advisory exclusive |
| `atomic_write_text/json` | temp + fsync + replace |
| `locked_atomic_write_json` | Lock + atomic |
| `compare_and_swap_json` | generation CAS |
| `RaceConditionGuard` | Fassade |
| `race_stress_test` | CI-Harness |

**[Bedingt]** Korrektheit unter OS-Lock-Semantik; Timeout → `TimeoutError`.

---

## Bogen 4 — Route-Table (Autopolitik der Wege)

**[Definition]** `RouteTarget(intent, surface, api, kind, node_id, aliases, description)`.

**[Spezifikation]**

| Funktion | Input → Output |
|----------|----------------|
| `resolve` | Intent/Alias → `RouteTarget` |
| `route_message` | Message + Intents → plan + redirect_hint |
| `all_routes` | table + legacy + entrypoints |
| `LEGACY_REDIRECTS` | alte Pfade → kanonisch |

**[Modell]** Route-Table = Autopolitik der Dissertation (wo darf Intent landen?).

---

## Bogen 5 — Interconnect Graph

**[Herleitung]** Knoten (CLI, Skill, Bridge, Dashboard, Mesh, GCE, MCP, …) + Kanten (Relation live/offline).

**[Spezifikation]**

| API | Rolle |
|-----|--------|
| `capture` | Live-Abgreifen |
| `evolve` | Recommendations / evolved architecture |
| `get_graph` | Cache/Refresh |
| `probe_http` / `_tcp_open` | Health-Proben |
| `_persist` | race-safe JSON |

**[Modell]** `health_score` ist Aggregat-Heuristik, kein medizinischer Score.

---

## Bogen 6 — Bifurkale Sync und Publish

**[Spezifikation]** Bifurkale Mesh-Direktive: Pull State / Push Morph.  
**[Spezifikation]** GCE hero-docs :8088 — L2 Publish-Spiegel als empirische Ausdrucksform.

**[Modell]** Bifokalität Universum↔Gehirn bleibt **OFFEN** (siehe Bifokal-Verweis); Mesh-Bifurkation ist **operative** Dualität Pull/Push.

---

## Anhang A07

Entry points:

```text
control_plane: /mainframe/grok
route_api:     /api/grok/route
routes_table:  /api/grok/routes
interconnect:  /api/grok/interconnect
```
