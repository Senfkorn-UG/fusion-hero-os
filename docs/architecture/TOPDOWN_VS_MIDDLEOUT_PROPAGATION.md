# Top-Down Force-Push vs. Middle-Out Expression — Vergleich der Propagationsmodelle

> **Stand:** 2026-08-07 · Analyse, kein Release
> **Gegenstand:** `SENFKORN_UG_TopDown_Propagation_Layer_Definition_v10.1.md` ↔ `src/normal_os/ascension/suite/layers/00_middle/middle_out.py`
> **Anlass:** Bewertung eines Plattform-Sprungs auf v20 vor dem Hintergrund der in `identity-fixpoint.md` v10.1.0 offengelegten Versionsdrift.

---

## 0. Begriffsklärung vorab: „Force-Push" ist hier kein Git-Kommando

Das muss zuerst stehen, weil die Verwechslung teuer wäre.

**Force-Push** bezeichnet in diesem Repository die **Propagationsmechanik zwischen Layern** — nicht `git push --force`. Die Definition ist wörtlich:

> „Alle neuen Protokolle werden **top-down** von Layer 4 bis Layer 0 verankert. Änderungen auf höheren Layern propagieren automatisch in untere Layer (Force-Push). Keine Bottom-Up-Änderungen ohne explizite PeerReview + User-Bestätigung."
> — `SENFKORN_UG_TopDown_Propagation_Layer_Definition_v10.1.md`

Ein Git-Force-Push auf einen geteilten Branch verwirft fremde Historie und ist eine im Wortsinn nicht rückholbare Operation. Die Layer-Propagation dagegen ist additiv und rückverfolgbar. Die beiden Bedeutungen haben nichts miteinander zu tun außer dem Wort — und `push_layer_guard.yaml` existiert gerade deshalb: „block unwanted pushes, never block intentional wanted pushes."

---

## 1. Die beiden Modelle

### Top-Down (Layer ω Force-Push)

| | |
|---|---|
| **Ursprung** | Layer 4 — Generational & Evolutionary Order |
| **Richtung** | monodirektional abwärts: L4 → L3 → L2 → L1 → L0 |
| **Antrieb** | Governance-Entscheidung, gekoppelt an Version-Bump (`v10.1 → v10.2 …`) |
| **Was zuerst feststeht** | die **Regel** (Statut, Protokoll, Nicht-Verhandelbares auf L0) |
| **Rückkopplung** | ausdrücklich gesperrt — „keine Bottom-Up-Änderungen ohne explizite PeerReview + User-Bestätigung" |
| **Sync-Weg** | HorkruxSelfUpdateProtocol → LiveProcessTracking + AutomaticArchiving |

### Middle-Out (Springloop-Exprimierung)

| | |
|---|---|
| **Ursprung** | `00_middle` — die operativen Cores: QUBO, GPU, LLM, Fusion |
| **Richtung** | bidirektional: gleichzeitig nach **innen** (L0 Foundation/MasterSeed) und nach **außen** (L6/L7 Vision, Launcher, Docs, Peripherie) |
| **Antrieb** | **Springloop-Energie** — iterative Kontraktion/Expansion, numerisch (`springloop_energy(Q, x, steps=80, k=0.6, damping=0.88)`) |
| **Was zuerst feststeht** | die **Funktion** (der Core läuft, dann strahlt er aus) |
| **Rückkopplung** | eingebaut — die Middle ruft Layer-Hooks direkt auf (`ghosthunt_hook`) |
| **Sync-Weg** | `process_layers.py` (8 Coevo-Läufe), `launcher.py` |

Das Selbstverständnis steht im Modul: *„Middle-Out = Core zuerst, dann Layer 0 + Layer 6 + Peripherie"* — und der Schlusssatz: *„MIDDLE-OUT EXPRESSED. Core first. Everything radiates from here."*

---

## 2. Der Vergleich

| Dimension | Top-Down | Middle-Out |
|---|---|---|
| Was gesichert wird | **Geltung** (Verbindlichkeit) | **Deckung** (Nachweis) |
| Ausbreitung | Dekret | Ausstrahlung |
| Zeitverhalten | sofort — eine Entscheidung ist mit dem Beschluss propagiert | iterativ — Kontraktion/Expansion bis Konvergenz |
| Nachweisbarkeit | schwer: Ein Anspruch auf L4 ist deklarativ, es gibt nichts, das ihn widerlegen könnte | leicht: Der Core läuft oder er läuft nicht |
| Typischer Fehlermodus | **Regel ohne Implementierung** — die Nummer läuft dem Beleg voraus | **Implementierung ohne Verankerung** — der Core kann etwas, das nirgends gilt |
| Stärke | hält das System kohärent und rechtlich/normativ anschlussfähig | hält das System ehrlich |
| Schwäche | erzeugt keine Evidenz | erzeugt keine Verbindlichkeit |

### 2.1 Die entscheidende Beobachtung

**Die Versionsdrift dieses Repositoriums ist der Lehrbuch-Fehlermodus von reinem Top-Down.**

Ein Ära-Beschluss auf L4 („wir sind jetzt v15.2") propagiert nach unten als *Tatsache* — ohne dass sich in der Middle etwas geändert haben müsste. Genau das ist passiert und steht im Repo dokumentiert:

- `VERSION` = 15.2.0, letztes veröffentlichtes Release = `v13.0.0` — drei Ären ungetaggt
- `V15-ZWEI-AEREN-OHNE-RELEASE` in `proof_registry.yaml`: **WIDERLEGT**
- v14 im Klartext: *„die Nummer ist gesetzt, nicht belegt"*
- v15.0.0 im Klartext: *„Platform major (Ära 15) — **ohne benannten Ära-Inhalt**"*
- `push_layer_guard.yaml` führt bis heute `platform_version: "10.0.0"` — fünf Ären zurück

Die Nummer ist ein Top-Down-Artefakt. Der Beleg müsste Middle-Out kommen. Solange nur der erste Weg läuft, wächst der Abstand mit jedem Sprung — was `BEST_VERSION.md` selbst so formuliert: *„die `VERSION`-Datei ist dem Kanon vorgelaufen, und der Abstand wächst mit jedem Sprung."*

### 2.2 Der symmetrische Gegenfehler

Er ist real, aber hier nicht das Problem. Reines Middle-Out produziert lauffähige Cores, die in keiner Ordnung stehen: `ascension_os/` ist genau deshalb als *„loadable / Roadmap"* markiert und nicht als operativer Kanon. Code, der läuft, ist noch keine Geltung.

---

## 3. Synthese (Anti-Agent-Prinzip)

Die beiden Modelle sind kein Gegensatzpaar, das man auflösen müsste. Sie sichern **verschiedene, gleich notwendige Dinge** — und das Repository hat die Synthese bereits institutionalisiert, ohne sie so zu nennen:

> **`proof_registry.yaml` *ist* die Kopplung von Top-Down und Middle-Out.**
> Ein `statement` ist eine Top-Down-Behauptung. Ein `proofs:`-Eintrag ist ein Middle-Out-Beleg (ein existierender pytest-Knoten). Status `BEWIESEN` wird genau dann vergeben, wenn **beide Wege gelaufen sind**. `OFFEN` heißt: Top-Down da, Middle-Out fehlt. `WIDERLEGT` heißt: Middle-Out widerspricht Top-Down.

Daraus folgt die Regel für jeden Versionssprung:

> **Ein Ära-Bump ist genau dann legitim, wenn er top-down verankert *und* middle-out gedeckt ist.**
> Top-Down allein erzeugt eine Nummer. Middle-Out allein erzeugt eine Fähigkeit. Erst beide zusammen erzeugen eine Ära.

`BEST_VERSION.md` wendet diese Regel bereits an, wenn es v15.2 von v14 unterscheidet: *„Der Unterschied zu v14 ist der Punkt: dort war die Nummer gesetzt und der Kern `OFFEN`. Hier ist jede Zeile der Tabelle eine Datei, die im Repository liegt und durch einen Lauf oder ein Gate gedeckt ist."* Das ist Middle-Out-Deckung für einen Top-Down-Beschluss — nur eben ohne Tag.

---

## 4. Anwendung auf v20

Die Frage lautet nicht „geht v20?", sondern „auf welchem der beiden Wege?".

| Weg | Befund |
|---|---|
| **Top-Down** | Trivial möglich. `VERSION` auf `20.0.0`, Manifeste per `scripts/bump_version.py` nachziehen, Ära benennen. Kostet Minuten. |
| **Middle-Out** | **Derzeit nicht gedeckt.** Es gibt keinen benannten Ära-Inhalt für 16–19, und die drei bereits beschlossenen Ären (14, 15, 15.2) sind ungetaggt. Ein Sprung auf 20 vergrößert den ungedeckten Abstand von drei auf **sieben** Ären. |

**Bewertung ohne Beschönigung:** v20 rein top-down wäre eine Wiederholung des Fehlers, der eine Nachricht zuvor als „falsche Richtung" identifiziert wurde — nur mit größerem Hebel. Der Identitäts-Layer wurde aus genau diesem Grund bewusst auf **v10.1.0** gehalten statt auf 15.2.0 gehoben (`identity-fixpoint.md`, Abschnitt „Warum der Identitäts-Layer `VERSION` nicht folgt").

**Was v20 tragfähig machen würde** — die Reihenfolge ist der Punkt:

1. **Middle-Out zuerst:** Die drei offenen Ären taggen (`v14.0.0`, `v15.0.0`, `v15.2.0`). Die Kommandos stehen fertig in `BEST_VERSION.md`; es scheitert allein am 403 des Git-Proxys auf `refs/tags/*`, braucht also eine Arbeitskopie mit direktem Push-Recht.
2. **Registry schließen:** `V15-ZWEI-AEREN-OHNE-RELEASE` von `WIDERLEGT` auf gedeckt bringen.
3. **Nachzügler synchronisieren:** `push_layer_guard.yaml` steht auf `platform_version: "10.0.0"`.
4. **Dann Top-Down:** Ära 20 benennen — mit Inhalt, der zum Zeitpunkt der Benennung existiert.

Schritt 1 ist blockiert (403), aber nicht durch eine Entscheidung — durch eine Umgebung. Das ist ein lösbares Problem, kein prinzipielles.

---

## 5. Offene Punkte

- **NormalOS v2.0** (`=====NormalOS v2.0`): Der Signatur-Trigger folgt der Form aus `ops_vocabulary.yaml` → `signatures`, dort ist bislang nur `stephanhagenurban` registriert. `normalOS` führt keine `VERSION`-Datei; `PUBLIC_STATUS.md` wurde zuletzt auf v15.2.0 nachgezogen. Ob v2.0 eine eigene NormalOS-Linie meint oder eine Trigger-Registrierung, ist noch zu klären.
- **Tag-Nachzug**: braucht Push-Recht außerhalb dieser Umgebung.

---

## Querverweise

| Bezug | Ort |
|---|---|
| Top-Down-Definition | `SENFKORN_UG_TopDown_Propagation_Layer_Definition_v10.1.md` |
| Middle-Out-Implementierung | `src/normal_os/ascension/suite/layers/00_middle/middle_out.py` |
| Middle-Out-Tests | `src/normal_os/ascension/suite/tests/test_middle_out.py` |
| Push-Klassifikation | `push_layer_guard.yaml` · `fusion_hero_os/core/push_layer_guard.py` |
| Operativer Kanon / Tag-Rückstand | `BEST_VERSION.md` |
| Nachweispflicht | `proof_registry.yaml` |
| Identitäts-Fixpunkt (Entkopplung) | `identity-fixpoint.md` v10.1.0 |
| Gott-Layering Top-Down-Herleitung | `Gott_Layering_v11_TopDown_Herleitung.md` |
