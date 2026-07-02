# BRANCH_STRATEGY_v8.md

**ALTE_Frau_95g Heroic Core v8 – Fusion Hero OS Branch Model**

## Ziel
Klare, sichere und zukunftssichere Branch-Struktur für ein selbst-modifizierendes, heroic Core-Repository.

## Branch-Modell (gültig ab v8)

### main (protected, stable)
- Einziger stabiler Release-Branch
- Enthält nur vollständig peer-reviewed und archivierte v8-Code + Docs
- Force-Push streng verboten
- Alle Änderungen nur über Merge aus develop nach erfolgreicher 5/6-Dimensions-PeerReview + AutomaticArchiving
- Tags: v8.0, v8.1, v8.2... (klare semver- oder heroic-Versionierung)

### develop (active integration)
- Täglicher Arbeits-Branch für alle laufenden Self-Modifications
- Feature-Branches werden hier integriert
- Regelmäßige Merges nach main (nach vollständigem Review)
- Kann bei Bedarf mit Archivierung zurückgesetzt werden

### feature/<kurzname>
- Kurzlebige Branches für konkrete Aufgaben
- Beispiele:
  - feature/v8-folder-restructure
  - feature/hyperthreading-metrics
  - feature/horkrux-full-propagation
  - feature/optimizer-insights-consolidation
  - feature/branch-strategy-implementation
- Werden nach Fertigstellung in develop gemerged und gelöscht
- Jeder Feature-Branch triggert eigenen kurzen Review-Zyklus

### archive/ oder Tags (Historie)
- Alte Major-Versionen als Tags oder im archive/-Ordner
- archive/v7.4, archive/v7.8 etc. nur bei Bedarf als Branch
- Empfehlung: Tags + Inhalt im archive/-Ordner (sauberer)

### hotfix/<name> (selten)
- Nur für kritische Fixes direkt auf main
- Sofortiger Rückfluss in develop

## Regeln (im Core verankert)
- Branch-Namen heroic-konform (keine kryptischen oder persönlichen Namen)
- Vor jedem Merge in main oder develop: 5-stufiger Erkenntnisprozess + PeerReview + LiveProcessTracking-Eintrag
- AutomaticArchiving bei jedem Merge in main
- main ist geschützt (Branch Protection Rules empfohlen)

## Umsetzung
Diese Strategie wird mit diesem Commit in docs/v8/BRANCH_STRATEGY_v8.md dokumentiert und ist ab sofort verbindlich für alle weiteren Evolutionen.

**Status:** v8 | Identity Preservation 100 | Ready for develop creation
