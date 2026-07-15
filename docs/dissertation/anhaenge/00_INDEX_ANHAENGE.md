# Anhänge — Module und Funktionen, aus dem Nichts hergeleitet

**Dissertation:** *Autopoiesis und Autopolitik des Fusion Hero OS*  
**Designvorlage:** Kompendium der Heroik **V3.3** (zwingend)  
**Ontologie:** Dissertation ≡ Fusion Hero OS; Text = eine Ausdrucksform  

---

## Synthese

Diese Anhänge leisten, was der Haupttext verdichtet und der Code *ist*: sie **leiten** die Module und Funktionen **aus dem Nichts her** — ohne heroische Spezialannahmen vor der allgemeinen Logik, mit Geltungsmarken, und mit Verweis auf den konkreten Code.

| Anhang | Inhalt | Register |
|--------|--------|----------|
| [A00](A00_V10_ACTIVATION.md) | **v10.0.0 Auto-Activation** Record | Spezifikation |
| [A01](A01_Fundament_aus_dem_Nichts.md) | Logik, Geltung, Modulbegriff, BaseModule | Herleitung |
| [A02](A02_Core_Module_Herleitung.md) | `fusion_hero_os.core.*` | Herleitung + Spezifikation |
| [A03](A03_Engine_QUBO_Mainframe.md) | QUBO, Annealing, Mainframe-Engine | Herleitung + Satz/Bedingt |
| [A04](A04_Methodik_Geltung_V33.md) | PeerReview, FormalMath, V3.3Structure | Herleitung |
| [A05](A05_Meta_Consent_Governance.md) | Consent, Vault, Pipeline, Meta-API | Spezifikation + Modell |
| [A06](A06_Dashboard_Surfaces_Routes.md) | FastAPI, Surfaces, Bridge, Gateway | Spezifikation |
| [A07](A07_Mesh_Interconnect_Routing.md) | Mesh, Route-Table, Race-Guard, Interconnect | Herleitung + Spezifikation |
| [A08](A08_Modules_Providers_Orchestration.md) | modules/, providers/, orchestration | Spezifikation |
| [A09](A09_Entwicklungsgeschichte_Null_bis_v10.md) | Genealogie der Entwicklung | Fragment/Historie + Spezifikation |
| [A10](A10_Funktionskatalog_AST.md) | Vollkatalog Klassen/Funktionen (AST) — `fusion_hero_os` + `03_Code/Dashboard` | Spezifikation |

**v10 aktivieren:** `python scripts/activate_v10.py`  

**Regenerate Katalog:** `python scripts/generate_anhang_katalog.py`  

**Pipeline (v10 + Katalog + DOCX/PDF):** `python scripts/pipeline_dissertation_v10.py`  

**In DOCX/PDF einbetten:** `python scripts/embed_dissertation_anhaenge.py --regen-catalog --pdf` (aktiviert v10 standardmäßig)

### Geltungsschnellreferenz

| Marke | Bedeutung in diesen Anhängen |
|-------|------------------------------|
| **Definition** | Begriffsfestlegung |
| **Satz** | Nachrechenbar / pytest / Proof Registry BEWIESEN |
| **Bedingt** | Gilt unter genannten Annahmen |
| **Modell** | Heuristik / Architekturlesart — kein Beweis |
| **Fragment** | Unvollständig / historisch |
| **Spezifikation** | Code-Wahrheit (was der Repo *tut*) |

### Qualitätsregel (V3.3)

Keine Metapher als Beweis. Kein Betrieb ohne Geltungsmarke an zentralen Claims. Spezifikation, Exkurs und Herleitung trennen.

**Vermerk:** [MAINFRAME · V3.3 · Dissertation-as-OS · Anhänge aus dem Nichts]
