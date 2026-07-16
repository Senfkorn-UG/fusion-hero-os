# A08 — Modules, Providers, Orchestration: Herleitung

**Pakete:** `fusion_hero_os/modules/`, `providers/`, `orchestration/`, `mcp/`, `integrations/`  

---

## Synthese

Oberhalb des Core liegen **anwendungsnahe** Organe: sie erben den Modulvertrag, spezialisieren `process`, und koppeln an Provider (LLM), Agenten und MCP-Werkzeuge. Hier: Frage → Modul → Funktionen → Geltung.

---

## Bogen 1 — Native Methodik-Module (modules/)

| Modul | Frage | Kern-API (typisch) | Geltung |
|-------|-------|--------------------|---------|
| `formal_mathematics` | Wie markieren? | classify-artig | Spezifikation |
| `code_review` | Wie prüfen Code-Text? | review | Modell/Heuristik |
| `self_modify` | Wie vorschlagen ohne Auto-Patch? | propose | Spezifikation (deklarativ) |
| `automatic_archiving` | Wie planen, ohne still zu zippen? | plan | Spezifikation |
| `conversation_context` | Was bleibt im Dialog? | context API | Spezifikation |
| `live_process_tracking` | Was läuft gerade? | status | Spezifikation |
| `generational_evolution` | Wie evolvieren Populationen? | evolve | Modell/Bedingt |
| `qubo_integration` | Wie QUBO anbinden? | run/secure | Spezifikation |
| `mer` | Klinische MER-Heuristik? | MER helpers | **Modell** (kein DSM) |
| `weltraudaimonia` | Eudaimonia-Guard? | guard | Modell |
| `phone_link` | Phone-Bridge Status? | snapshot | Spezifikation + Privacy-Mask |

---

## Bogen 2 — Heroic LLM EA

**Pfad:** `modules/heroic_llm_ea/`

| Datei | Rolle |
|-------|--------|
| `orchestrator` | Steuerung |
| `evolution` | Populationsschritte |
| `fitness` | Bewertung |
| `memory` | Erinnerung |
| `providers` | LLM-Anbindung |
| `config/campfire_templates.yaml` | Templates |

**[Geltung]** Evolutionäre Suche über Prompt/Policy-Raum — **Modell/Bedingt**, kein Beweis optimaler Intelligenz.

---

## Bogen 3 — Image Orchestrator

**Pfad:** `modules/image_orchestrator/`

| Datei | Rolle |
|-------|--------|
| `orchestrator` | Jobs steuern |
| `pipeline` | Schritte |
| `job_queue` | Warteschlange |
| `prompt_builder` | Prompt-Bau |
| `providers` | Bild-APIs |
| `rate_limiter` | Drossel |
| `config/visual_identity.yaml` | Visual Identity |

**[Spezifikation]** Rate-Limits und Queues sind Membranen gegen API-Chaos.

---

## Bogen 4 — Timespace Token

**Pfad:** `modules/timespace_token/`

| Datei | Rolle | Geltung |
|-------|--------|---------|
| `geometry` | Raum/Zeit-Geometrie der Tokens | Modell |
| `bottleneck` | Engpass | Modell |
| `manager` / `module` | Verwaltung | Spezifikation |

---

## Bogen 5 — Providers und Agents

**Providers** (`providers/`):

| Modul | Rolle |
|-------|--------|
| `base` | Provider-Vertrag |
| `grok_provider` | xAI/Grok |
| `claude_provider` | Claude |
| `everyapi_provider` | Aggregator |
| `internal_provider` | lokal/intern |

**Orchestration** (`orchestration/agents.py`): Multi-Agent-Register und Zuweisung.

**MCP** (`mcp/fhero_mcp_server.py`): Tools z. B. Layer0-Verify, Schedule-QUBO — Membran nach außen.

**Integrations** (`integrations/phone_link/reader.py`): Snapshot mit Maskierung.

---

## Bogen 6 — Builder / Skill / Mainframe-Laden

| Pfad | Rolle |
|------|--------|
| `modules/builder_profile` | Builder-Profil (README) |
| `modules/skill_creator` | Skill-Scaffold |
| `modules/mainframe_laden` | Mainframe-Laden-Vermerk-Organ |

**[Modell]** Skills sind textuelle/operative Verkörperungen der Methodik (Dissertation-as-OS).

---

## Anhang A08

Vollständige Methoden: A10.  
Provider-Secrets: nie im Public Repo.  
