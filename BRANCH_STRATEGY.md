# Branching Strategy — Fusion Hero OS → AscensionOS (Final v8.8+)

## Aktuelles Modell (Hyperthreading + Archive)

### `main` (Stable Release Line)
- Geschützt. Direkte Pushes sind blockiert (CI + idealerweise Branch Protection).
- Nur Merges via Pull Request von `develop` oder `ascension`.
- Tags (`v8.8`, `v8.9` ...) markieren stabile Releases.

### `develop` – Option A Track (Evolutionary)
- Aktive Weiterentwicklung des bestehenden Heroic Core.
- AscensionOS wird hier als Vision/Fundament behandelt.
- Wird regelmäßig nach `main` gemergt.

### `ascension` – Option B Track (Strong Ascension Path)
- Radikalere, visionäre Entwicklungslinie für AscensionOS als eigenständiges Zielprogramm.
- Neue Strukturen (`ascension_os/`, `AscensionCore`).

### `archive` (Langzeit-Archiv)
- Sinnvoll organisiertes Archiv für alles Alte.
- Struktur:
  - `v7/`
  - `experimental/`
  - `docs/`
  - `theory/`
  - `legacy/`
- Read-only. Wird nicht mehr aktiv entwickelt.

## Hyperthreading Prinzip
Zwei parallele Tracks laufen gleichzeitig, damit beide Optionen (konservativ vs. stark) verfolgt werden können, bis eine finale Entscheidung oder Fusion getroffen wird.

**Ziel:** Alles seit April 2026 entwickelte (Grounding, Dynamic Assignment, SisyphosCycle, Fail-Closed, Psycholysis, HeroicCore, etc.) soll in **AscensionOS** münden.

## Status (09.07.2026)
- Pipeline gehärtet: Direkte Pushes auf `main` sind blockiert.
- `archive/` Verzeichnis auf `main` angelegt und strukturiert.
- Zwei-Track-Modell aktiv.
