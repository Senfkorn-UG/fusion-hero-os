# A05 — Meta, Consent, Governance: Herleitung

**Paket:** `fusion_hero_os/meta/`  
**Autopolitik:** Placement, Membran, Fail-Closed  

---

## Synthese

Wenn das OS die Dissertation *ist*, braucht es Organe, die sagen: **was darf wofür** (Consent), **was wird erinnert** (Vault/Memory), **wie koppelt sich Lernen** (Hebbian/Coupling), **wie fließt Aktivierung** (Pipeline), **wie wird optimiert** (QUBO-Bridge). Das ist Autopolitik in Code.

---

## Bogen 1 — Consent aus dem Nichts

**[Herleitung]**

1. Daten können personenbezogen sein.  
2. Verarbeitung ohne Zweck ist Gewalt an der Grenze der Person.  
3. Also: **Zweck + Grant + Fail-Closed**.

**[Spezifikation]** `consent.py` — `Purpose`, Grant-APIs; `api.grant_consent`.

**[Modell]** Consent-Gate als Membran (Dissertation Autopolitik L0–L4).

**[Satz-Norm]** Stage-A: fail-closed für personenbezogene Ops (siehe BEST_VERSION / Tests).

---

## Bogen 2 — Vault und Working Memory

| Modul | Rolle | Geltung |
|-------|-------|---------|
| `vault` | geschützter Speicherpfad | Spezifikation |
| `working_memory` | kurzfristiger Arbeitskontext | Spezifikation |
| `schemas` | Datenverträge | Definition |

**[Bedingt]** Sicherheit hängt von Deployment, Keys, OS-Rechten ab — Code allein ist keine vollständige Security-Zusage.

---

## Bogen 3 — Graph, Coupling, Hebbian

**[Herleitung]** Assoziation: was gemeinsam aktiv ist, verbindet sich stärker (Hebb — **Modell** im System, nicht Neurobeweis).

| Modul | API-Idee | Geltung |
|-------|----------|---------|
| `graph` | Knoten/Kanten Meta-Graph | Spezifikation |
| `coupling` | Kopplungsstärken | Modell |
| `hebbian` | Lernupdate | Modell |
| `qubo_bridge` | Optimierungsbrücke | Spezifikation/Bedingt |

---

## Bogen 4 — Pipeline und API

**[Spezifikation]** `pipeline.py` — Ablauf Ingest → Activate → Associate → Optimize.

**[Spezifikation]** `api.py`:

| Funktion | Rolle |
|----------|--------|
| `get_service` | Service-Zugriff |
| `grant_consent` | Consent |
| `ingest` / `activate` / `associate` / `optimize` | Pipeline-Schritte |
| `audit_trail` | Nachvollziehbarkeit |
| `create_app` | FastAPI-App Factory |

**[Spezifikation]** `cli.py` — `run_demo`, `main`.

---

## Bogen 5 — Audit als Organ der Dissertation

**[Modell]** `audit_trail` ist epistemisches Organ: die Arbeit muss sich selbst zitieren können (Code Honesty).

---

## Bogen 6 — Was nicht behauptet wird

- Kein vollständiges DSGVO-Rechtsgutachten im Code.  
- Kein Beweis, dass Hebbian-Updates „das Gehirn“ sind.  
- Kein Ersatz für menschliche Verantwortung am Consent.

---

## Anhang A05

Siehe A10 für Methodenlisten; Stage-A/B-Tests im Repo für Fail-Closed-Norm.  
