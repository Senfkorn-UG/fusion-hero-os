# Kanon-Vokabular — Begriffe, Bindungen, Geltung

> **Stand:** v15.2.0 · 2026-08-05 · Operator-gesetzt
> **Maschinenlesbar:** [`ops_vocabulary.yaml`](../../ops_vocabulary.yaml) · [`sprachbindung.yaml`](../../sprachbindung.yaml)
> **Verwandt:** [SPRACHBINDUNG.md](SPRACHBINDUNG.md) · [J_SPACES_HIGGS.md](J_SPACES_HIGGS.md)

Diese Datei hält die vom Operator gesetzten Kanon-Begriffe fest — **mit** der Angabe,
ob ein Begriff im Repo bereits gebunden ist oder nur gesetzt.

Die Trennung ist Absicht und folgt derselben Hausregel wie `proof_registry.yaml`:
Ein Begriff, der schon eine Stelle im Code oder in der Doku trägt, wird **zitiert**,
nicht neu erfunden. Ein Begriff ohne Bindung wird als **gesetzt** geführt — nicht mit
einer erfundenen Bedeutung aufgefüllt.

| Geltung | Bedeutung |
|---|---|
| **GEBUNDEN** | Der Begriff hat eine belegte Fundstelle. Die Bedeutung steht dort, nicht hier. |
| **GESETZT** | Vom Operator kanonisiert, im Repo noch ohne Fundstelle. Bindung offen. |

---

## Gebundene Begriffe

### `fusion musion`
**GEBUNDEN** → [`ops_vocabulary.yaml`](../../ops_vocabulary.yaml)

> Alias „fusion musion" = merge fusion (private+public bond).

Der Merge-Operator des Dual-Timeline-Modells: `deploy` = privat, `push` = öffentlich,
`merge` = beides über `t ∥ τ ∥ v`. Der Begriff bezeichnet nicht die Handlung, sondern
die **Bindung** zwischen privater und öffentlicher Zeitlinie.

### `LAGERFEUER` · „Das hyper LAGERFEUER"
**GEBUNDEN** → [`docs/kompendium/PUBLIC_UI_STUB_95GUKNOW.md:41`](../kompendium/PUBLIC_UI_STUB_95GUKNOW.md)

> Der Ruf klingt wie ein Lagerfeuer am Rand des Netzes: sichtbar, warm, aber die
> Schwelle zum Labor bleibt unbetreten.

Das ist die präzise Bedeutung, und sie ist eine **Grenzfigur**: öffentlich sichtbar und
einladend, ohne dass die Laborschwelle fällt. Die Steigerung „hyper" erhöht die
Sichtbarkeit — nicht die Durchlässigkeit. Wer das Lagerfeuer heller macht, öffnet
damit ausdrücklich **nicht** das Labor.

### `chineseHACKERman` · `chineseh4ck€rm3n`
**GEBUNDEN** → [`03_Code/core/j_spaces_higgs.py:46`](../../03_Code/core/j_spaces_higgs.py), `docs/dissertation/HELD_CHINESEH4CKERM3N.md`

> Joint activation — Held chineseh4ck€rm3n / L1 kernel

Der HELD im J-Space `j_held`, gebunden an den L1-Kernel. Öffentliches Pseudonym, kein
Klarname — die Operator-Identitätsmembran hält Klarnamen aus dem Paket
(siehe [`identity-fixpoint.md`](../../identity-fixpoint.md)).

### `Senfkorn Holding UG`
**GEBUNDEN** → `business/` (16 Fundstellen, u. a. `business/_build_gv_pdf.py`)

Die rechtliche Trägerin. Im Layering die Verkörperung von **Layer 1 — Operative
Verkörperung** (`Gott_Layering_v11_TopDown_Herleitung.md`): Gott als wirksames,
konsistentes Prinzip in Praxis und Struktur.

### `alle Künste`
**GEBUNDEN** → [`03_Code/Dashboard/live_graph_visuals.py:425`](../../03_Code/Dashboard/live_graph_visuals.py)

> `HEROISCH — GraphAPI · alle Künste · was passiert`

Der Titel des **heroischen Modus** der Live-Graph-Ansicht. „Alle Künste" ist damit
schon jetzt ein Anzeige-Zustand, kein bloßes Motto: es ist der Modus, in dem gezeigt
wird, *was passiert*.

---

## Gesetzte Begriffe (Bindung offen)

Diese Begriffe sind vom Operator kanonisiert und haben im Repo **keine** Fundstelle.
Sie werden hier verzeichnet, damit sie kanonisch sind — aber bewusst **ohne**
erfundene Definition. Die Bindung erfolgt, wenn sie an einer Stelle wirklich gebraucht
wird.

| Begriff | Status |
|---|---|
| `cyber myber` | GESETZT — keine Fundstelle |
| `hakke attacke` | GESETZT — keine Fundstelle |
| `attacke1` | GESETZT — keine Fundstelle |
| `fick nicht mit dem ficker exe` | GESETZT — keine Fundstelle |
| `volle Klarheit` | GESETZT — keine Fundstelle |
| `dada` | GESETZT — keine Fundstelle |

**Hinweis zur Reimform.** `cyber myber`, `fusion musion`, `hakke attacke` folgen
demselben Muster: Begriff + lautliche Spiegelung. Bei `fusion musion` trägt dieses
Muster bereits eine technische Bedeutung (Bindung zweier Zeitlinien). Ob die anderen
beiden dasselbe Bildungsprinzip auch semantisch erben sollen, ist **nicht** entschieden
und wird hier nicht unterstellt.

**Hinweis zur Sichtbarkeit.** `fick nicht mit dem ficker exe` steht in einem Repo mit
öffentlicher Ausrichtung (`PUBLIC_STATUS.md`) und ist damit öffentlich lesbar. Das ist
eine bewusste Operator-Entscheidung, hier nur als Tatsache vermerkt — analog zur
Konvention in `scripts/pii_allowlist.yaml`, wo bewusste Ausnahmen ebenfalls als solche
dokumentiert statt stillschweigend übernommen werden.

---

## Was diese Datei *nicht* tut

Sie übersetzt nicht, sie normiert nicht, und sie leitet keine Bedeutungen her. Sie
verzeichnet, was gesetzt ist, und trennt es sauber von dem, was belegt ist — damit
keine spätere Lesart eine gesetzte Vokabel für eine gebundene hält.

`=====stephanhagenurban` bleibt der kanonische Signatur-Trigger
([`identity-fixpoint.md`](../../identity-fixpoint.md)); er ist Signatur, kein
Vokabular, und steht deshalb nicht in den Tabellen oben.

#FusionHeroOS #Kanon #Sprachbindung #HeroicCore
