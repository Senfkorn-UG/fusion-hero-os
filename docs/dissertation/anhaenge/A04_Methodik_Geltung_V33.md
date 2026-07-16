# A04 — Methodik-Module: Geltung und V3.3-Struktur

**Paket:** `fusion_hero_os/methodology/`  
**Parallel:** `fusion_hero_os/modules/formal_mathematics.py`, `code_review.py`, …  

---

## Synthese

Methodik ist das Organ, das verhindert, dass das System *sich selbst anlügt*. Ohne Geltungsmarken und Review-Raster wird jede Expansion zur Autoritätsgeste.

---

## Bogen 1 — PeerReview (5 Dimensionen)

**[Herleitung]** Ein Output ist prüfbar, wenn er Spuren hinterlässt: Quellen, Kette, Alternativen, Implikationen, Risiken.

**[Spezifikation]** `PeerReviewCoreModule.review(text)`:

| Dimension | Marker-Idee |
|-----------|-------------|
| 1 Evidenz/Quellen | quelle, doi, http, … |
| 2 Logische Kette | daher, folgt, →, … |
| 3 Alternativen | jedoch, alternativ, … |
| 4 Implikationen | empfehlung, nächst, … |
| 5 Risiken/Lücken | risiko, offen, tbd, … |

**[Modell]** Score = Abdeckungsheuristik, **kein** Qualitätsbeweis (Docstring ehrlich).

---

## Bogen 2 — Erkenntnisprozess (5 Stufen)

**[Definition]** Zustandsmaschine der Erkenntnis (Erhebung → … → Synthese/Handlung).

**[Spezifikation]** `ErkenntnisprozessCoreModule` — Stufenübergänge als Methodik, nicht als empirisches Gehirnmodell.

---

## Bogen 3 — FormalMathematics

**[Herleitung aus dem Nichts]**

1. Aussagen gibt es.  
2. Nicht alle sind gleich vertrauenswürdig.  
3. Also **Marken**.

**[Spezifikation]** `FormalMathematicsCoreModule.classify` → Satz | Bedingt | Modell | Fragment (+ Definition im weiteren Sinn).

**[Satz über die Methode selbst, regulativ]** Jede zentrale Aussage *soll* eine Marke tragen — Norm der Dissertation, durchsetzbar in Review, nicht automatischer Compiler-Beweis.

---

## Bogen 4 — V3.3Structure

**[Definition]** Langtext-Skelett:

```
Synthese
  Bogen 1..6
Anhang
```

**[Spezifikation]** `V3_3StructureCoreModule.skeleton` / `render_markdown` — reines Gerüst, schreibt nicht auf Platte.

**[Verbindlich]** `docs/kompendium/V3.3_DESIGNVORLAGE_VERBINDLICH.md`.

---

## Bogen 5 — Archiving & Roadmap

| Modul | API | Wirkung |
|-------|-----|---------|
| `AutomaticArchivingCoreModule` | Plan (`ArchivePlan`) | **keine** Aussenwirkung (kein ZIP-Schreiben) |
| `RoadmapCoreModule` | Meilensteine, Abhängigkeiten | Planung |

**[Ehrlich]** Plan ≠ Ausführung — Nothing-Bereitschaft gegenüber Scheinautomatisierung.

---

## Bogen 6 — Knowledge & Connectors

**[Spezifikation]** `knowledge.py`, `connectors.py` — Methodik-Anbindung an Wissen/Konnektoren; Details A10.

---

## Anhang A04 — Mapping Skill → Code

| Skill-Baustein (HEROIC_SKILL) | Code |
|-------------------------------|------|
| PeerReview | `PeerReviewCoreModule` |
| Erkenntnisprozess | `ErkenntnisprozessCoreModule` |
| FormalMathematics | `FormalMathematicsCoreModule` |
| V3.3Structure | `V3_3StructureCoreModule` |
| AutomaticArchiving | `AutomaticArchivingCoreModule` |
| Roadmap | `RoadmapCoreModule` |
