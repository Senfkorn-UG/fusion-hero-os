# A01 — Fundament aus dem Nichts

**Geltung der Kernthesen:** Definition / Satz / Modell (markiert)  
**Designvorlage:** V3.3 · Herleitung aus dem Nichts  
**Code-Anker:** `fusion_hero_os/core/base_module.py`, `dispatcher.py`, `config.py`, `registry.py`

---

## Synthese

Bevor es „Module“, „Dispatcher“ oder „Heroic Core“ geben darf, muss klar sein, *was* man überhaupt bauen darf, ohne die Autorität des Mathematischen zu missbrauchen. Dieses Kapitel baut die unterste Schicht: **Unterscheidung**, **Geltung**, **Modulvertrag**, **Registrierung**, **Aufruf**.

**Kernthesen**

1. **[Definition]** Ein *Modul* ist eine benannte Einheit mit einer Kernoperation `process`.  
2. **[Definition]** *Geltung* trennt Satz, Bedingt, Modell, Fragment.  
3. **[Spezifikation]** `BaseModule` ist der gemeinsame Vertrag im Code.  
4. **[Spezifikation]** `Dispatcher` mappt Namen → Modulinstanzen und ruft `process` auf.  
5. **[Modell]** Die Kette „Nichts → Unterscheidung → Modul → System“ ist die operative Lesart von \(q\circ b\) (schneiden/benennen, fließen/verarbeiten).

---

## Bogen 1 — Der Ruf: Warum „aus dem Nichts“?

„Nichts“ meint hier **keine** mystische Leere, sondern: *keine heroischen Spezialannahmen vor der allgemeinen Logik*.

**[Definition]** *Herleitung aus dem Nichts* = jeder tragende Begriff wird eingeführt, bevor er Last trägt; Metaphern werden nie als Beweise gelesen (V3.3).

Ohne diese Disziplin entstünde ein System, das sich selbst mit Pathos beweist — genau der Fehler, den FormalMathematics und CriticalMetaAnalysis verbieten.

---

## Bogen 2 — Die Schwelle: Unterscheidung und Name

**[Definition]** Eine *Unterscheidung* trennt Innen/Außen eines Begriffs (Spencer-Brown-Nähe, philosophisch; hier **Modell**, nicht Satz der Gesetze der Form).

**[Definition]** Ein *Name* ist eine endliche Zeichenkette, die eine Einheit im System adressiert.

**[Spezifikation]** Im Code: `BaseModule.name` (Default: Klassenname).

```text
Nichts
  → Unterscheidung (was ist „dieses“ Modul?)
    → Name
      → Vertrag (was darf es tun?)
        → Instanz
          → Aufruf
```

---

## Bogen 3 — Geltung (FormalMathematics)

**[Definition]** Vier (plus Definition) Geltungskategorien:

| Marke | Darf behaupten |
|-------|----------------|
| Definition | Zweckmäßige Festlegung |
| Satz | Ableitbar / nachrechenbar / CI-BEWIESEN |
| Bedingt | Ableitbar unter Annahmen \(A_1,\ldots,A_n\) |
| Modell | Kohärente Heuristik ohne universellen Beweis |
| Fragment | Unvollständig, offen markiert |

**[Spezifikation]** Code: `fusion_hero_os/methodology/core_modules.py` → `FormalMathematicsCoreModule.classify`; Proof Registry parallel.

**[Verbot]** „Heroischer Exkurs“ oder OS-Ontologie als *Satz* ausgeben.

---

## Bogen 4 — Der Modulvertrag (BaseModule)

**[Herleitung]**

1. Es gibt Arbeitseinheiten.  
2. Arbeitseinheiten brauchen eine Kernoperation.  
3. Evolution und Review sind *optional* und dürfen nichts stillschweigend ausführen.

**[Definition]** `BaseModule`:

| Methode | Pflicht | Bedeutung |
|---------|---------|-----------|
| `process(payload)` | ja | Kernarbeit |
| `propose_evolution(context)` | nein | deklarativer Vorschlag, kein Auto-Patch |
| `peer_review(target)` | nein | Kriterien-Report; leeres Review = *nicht* bestanden |

**[Spezifikation]** `EvolutionProposal` enthält absichtlich **kein** ausführbares Objekt — nur Text/Diff zur menschlichen/CI-Prüfung.

**[Satz-ähnlich / Bedingt]** Wenn `peer_review` keine Kriterien liefert, ist `passed == False` — spezifiziert im Docstring von `BaseModule.peer_review`.

---

## Bogen 5 — Dispatcher und Config

**[Herleitung]** Viele Module → Bedarf einer *Abbildung* Name → Instanz.

**[Definition]** *Dispatcher* = Registry + Aufrufkonvention.

**[Spezifikation]** `fusion_hero_os/core/dispatcher.py`:

| API | Rolle |
|-----|--------|
| `register` / `unregister` | Modulverwaltung |
| `list_modules` | Inventar |
| `dispatch(name, payload)` | Einzelaufruf |
| `dispatch_many` | Mehrfach |
| `propose_evolution` / coll. peer review | optional Meta |
| `build_default_dispatcher` / `get_default_dispatcher` | Factory |

**[Spezifikation]** `config.get_config()` / `DispatcherConfig` — env-gesteuerte Worker-Grenzen (`FUSION_*`).

**[Bedingt]** Parallelität der Dispatch-Aufrufe hängt von Konfiguration und GIL/IO ab — keine generelle Parallelitätsgarantie als Satz.

---

## Bogen 6 — Rückkehr: Vom Vertrag zum Organismus

Erst mit BaseModule + Dispatcher + Geltung darf man höhere Organe bauen (Math Engine, QUBO, Mesh), ohne den Boden zu verlieren.

**[Modell — Dissertation-as-OS]** Diese Fundamentalschicht *ist* bereits Teil der Dissertation: der Vertrag, unter dem die Arbeit sich selbst aufruft.

### Spezifikation — minimale Nutzskizze

```python
from fusion_hero_os.core.base_module import BaseModule
from fusion_hero_os.core.dispatcher import Dispatcher

class Echo(BaseModule):
    def process(self, payload=None):
        return payload

d = Dispatcher()
d.register(Echo())
assert d.dispatch("Echo", {"x": 1}) == {"x": 1}
```

---

## Anhang A01

### Quellen

- V3.3 Designvorlage · FormalMathematics  
- `fusion_hero_os/core/base_module.py`  
- `fusion_hero_os/core/dispatcher.py`  
- `fusion_hero_os/config.py`  

### Begriffe

Modul, Name, Geltung, Dispatcher, EvolutionProposal (deklarativ)

### Was bewusst *nicht* hier bewiesen wird

- Korrektheit aller abgeleiteten Module  
- Empirie der heroischen Eudaimonia  
- Physische Identität von Gehirn und Universum  
