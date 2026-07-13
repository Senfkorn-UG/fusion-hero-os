# Baumeister Bob Monorepo Architektur

**Fusion Hero OS v8** nutzt eine monolithische Repository-Struktur (Monorepo), um die radikale Transparenz und Effizienz des Systemkerns zu gewährleisten. 

Das Ziel dieser Architektur ist absolute Kohärenz: Philosophischer Kern, technische Infrastruktur, Experimente und visuelle Identität existieren in einem einzigen, versionierten Raum. Dies ermöglicht das reibungslose Greifen des `HorkruxSelfUpdateProtocols` über alle Disziplinen hinweg.

## Die MasterSeed Hierarchie

```text
fusion-hero-os/
├── .github/                # CI/CD Workflows (Matrix-Builds, CodeQL, Docs-Deploy)
├── core/                   # Philosophischer & theoretischer Kern
│   ├── theory/             # Axiome, Modelle, Eudaimonismus-Theorie
│   ├── psycholyse/         # Psycholyse-Protokolle & Methodik
│   └── self-modification/  # Evolutionäre Konzepte (HorkruxSelfUpdateProtocol)
├── infrastructure/         # Technische Infrastruktur & Skripte
├── docs/                   # Wissensportal (MkDocs Material)
├── experiments/            # Praktische Feldarbeit (Tinder, Social, Psycholyse)
├── visuals/                # Visuelle Identität, Memes, Design-System
├── legal/                  # Verträge, Settlements & juristische Basis
└── tools/                  # Interne Werkzeuge zur Systemwartung
```

### Effizienz-Vorteile (EfficiencyDistillation)

1. **Holistische Versionierung**: Eine Änderung in der Eudaimonismus-Theorie (`core/`) kann im selben Commit mit dem passenden Experiment (`experiments/`) verknüpft werden.

2. **CI/CD Präzision**: GitHub Actions triggern spezifisch. Ein Push in `docs/` baut das MkDocs-Portal, lässt aber die Python-Tests für `core/` ruhen, wenn dort keine Änderungen stattfanden.

3. **Zentrale Wahrheit**: Neue Schnittstellen oder Partner (PeerReview) finden das gesamte Universum an einem einzigen Ort.