# Branching Strategy — Fusion Hero OS → AscensionOS (Hyperthreading Model)

## Hyperthreading Development Model (ab v8.8)

Wir führen **zwei parallele Tracks** (Hyperthreading), weil Option A und Option B unterschiedliche Ziele verfolgen:

### Track 1: `develop` – Option A (Evolutionary / Foundation)
- **Ziel**: Stabile, saubere Weiterentwicklung des bestehenden Heroic Core.
- AscensionOS wird als **Vision / Zielprogramm** positioniert, dem der aktuelle HeroicCore als Fundament dient.
- Keine großen Breaking Changes an Namen.
- Fokus auf Integration, Tests, saubere Grounding aller Module.
- Wird regelmäßig nach `main` gemergt (stabile Releases).

### Track 2: `ascension` – Option B (Strong Ascension Path)
- **Ziel**: Radikalere, zukunftsorientierte Struktur für AscensionOS als eigenständiges Zielprogramm.
- Neue Top-Level-Namen und Paketstruktur (`ascension_os/`).
- `AscensionCore` als neuer zentraler Aggregator (kann HeroicCore langfristig ablösen oder stark erweitern).
- Mehr Fokus auf Ascension-spezifische Konzepte, höhere Abstraktionsebene und langfristige Vision.
- Kann später in `main` gemergt werden, wenn der Track reif ist, oder als langlebiger alternativer Strang geführt werden.

## Branch-Übersicht

| Branch      | Zweck                              | Hyperthread-Track | Merge-Ziel     |
|-------------|------------------------------------|-------------------|----------------|
| `main`      | Stabile Releases                   | -                 | -              |
| `develop`   | Option A (konservativ)             | Track 1           | `main`         |
| `ascension` | Option B (stark / visionär)       | Track 2           | `main` (später) oder eigenständig |
| `feature/*` | Kurze fokussierte Arbeiten         | je nach Track     | develop / ascension |

## Hyperthreading-Prinzip
- Beide Tracks laufen parallel (wie Hyperthreading).
- Wichtige Erkenntnisse können zwischen den Tracks ausgetauscht werden.
- Am Ende soll **alles in AscensionOS münden** – entweder über den evolutionären oder den starken Pfad (oder eine Synthese beider).

## Aktueller Stand (09.07.2026)
- `develop` und `ascension` existieren parallel.
- Beide Tracks starten vom gleichen v8.8 HeroicCore-Stand.
- Hyperthreading-Modus ist aktiviert.

**Ziel**: Alles seit April entwickelte (Grounding, Dynamic Assignment, Sisyphos, Fail-Closed, Psycholysis, HeroicCore Aggregator etc.) soll in AscensionOS münden – über einen der beiden Tracks oder eine spätere Fusion.
