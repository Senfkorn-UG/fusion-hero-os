# Branching Strategy — Fusion Hero OS (v8.8+)

## Ziel
Eine klare, nachvollziehbare und sinnvolle Entwicklungshistorie, die sowohl schnelle Iteration als auch Stabilität ermöglicht.

## Aktuelles Modell (empfohlen ab v8.8)

### `main`
- **Stable / Release Line**
- Enthält nur gut getestete, grounded Versionen.
- Wird nur durch Merge von `develop` oder Hotfix-Branches aktualisiert.
- Tags (`v8.8`, `v8.7`, `v8.6` ...) markieren offizielle Releases.

### `develop`
- **Active Development Line** (neu angelegt)
- Alle neuen Features, Refactorings, epistemische Code-Belegungen und Modul-Erweiterungen landen zuerst hier.
- Wird regelmäßig in `main` gemergt, wenn ein neuer stabiler Stand erreicht ist (z. B. v8.9, v9.0).

### Feature / Themen-Branches
- `feature/heroic-xxx` oder `heroic/grounding-xxx`
- Kurze, fokussierte Branches für größere Arbeiten (z. B. grounding eines bestimmten Moduls wie `agents.py` oder `qubo_integration`).
- Werden nach Merge in `develop` gelöscht.

### Tags
- `vX.Y` für jede größere stabile Version (z. B. `v8.8`, `v8.7`).
- Annotierte Tags mit kurzer Release-Note.

## Bisherige Historie (v8.x Serie)
Die Versionen v8.3 bis v8.8 wurden linear auf `main` entwickelt. Das war für die intensive Grounding-Phase sinnvoll.
Ab v8.8 gilt das neue zweigleisige Modell (`main` + `develop`), um die Historie langfristig sauber zu halten.

## Wie neue Arbeit starten
```bash
git checkout develop
git pull origin develop
# neue Feature-Branch
```

## Release-Prozess (vereinfacht)
1. Arbeit auf `develop` oder Feature-Branch
2. Bei stabilen Stand: Merge nach `main`
3. Tag auf `main` setzen (`git tag -a v8.9 -m "..."`)
4. `main` pushen + Tags pushen

## Warum dieses Modell?
- Klare Trennung von "was gerade entwickelt wird" und "was stabil ist".
- Nachvollziehbare Historie für zukünftige Leser/Buch/Archiv.
- Ermöglicht parallele Arbeit ohne Chaos auf `main`.

**Stand:** v8.8 — `develop` Branch neu angelegt, Strategy dokumentiert.
