# Legacy Sources — Import-Manifest

**Zweck:** Kuratierte Quell-Snapshots aller zugehörigen `95guknow`-GitHub-Repositories,
gebündelt im Monorepo `fusion-hero-os`. Jeder Ordner unter `legacy_sources/` ist ein
Snapshot **ohne** eigene Git-Historie (kein Submodule) — nur Quellcode und Dokumente,
ohne Build-Artefakte (`node_modules/`, `target/`, `dist/`, `build/`, `.venv/`,
`__pycache__/`, `.svelte-kit/`) und ohne Binaries (`*.vsix`, `*.zip`, `*.exe`, `*.dll`).

**Provenance-Regel:** Jeder Snapshot trägt unten seinen Herkunfts-Commit (SHA). Zum
Aktualisieren: Repo frisch klonen, `.git` + Artefakte entfernen, Ordner ersetzen, SHA
hier fortschreiben. So bleibt jederzeit nachvollziehbar, welchem Upstream-Stand ein
Snapshot entspricht.

**Stand:** 2026-07-11 (Sync via `gh` + Depth-1-Klon).

| Ordner | GitHub-Repo | Branch | Herkunfts-Commit | Sichtbarkeit |
|--------|-------------|--------|------------------|--------------|
| `AscensionOS/` | [95guknow/AscensionOS](https://github.com/95guknow/AscensionOS) | main | `e80131a` | privat |
| `FuHOS_pub/` | [95guknow/FuHOS_pub](https://github.com/95guknow/FuHOS_pub) | main | `e2c3322` | öffentlich |
| `Fusion_Hero_OS_v1.1/` | [95guknow/Fusion_Hero_OS_v1.1](https://github.com/95guknow/Fusion_Hero_OS_v1.1) | main | `43351d0` | privat |
| `alte-frau-95g-heroic-core/` | [95guknow/alte-frau-95g-heroic-core](https://github.com/95guknow/alte-frau-95g-heroic-core) | main | `2bb62b6` | privat |
| `dashboard/` | [95guknow/dashboard](https://github.com/95guknow/dashboard) | main | `10bd167` | öffentlich |
| `fusion-hero-core/` | [95guknow/fusion-hero-core](https://github.com/95guknow/fusion-hero-core) | main | `f40ac76` | privat |
| `fusion-hero-os-daily-plans/` | [95guknow/fusion-hero-os-daily-plans](https://github.com/95guknow/fusion-hero-os-daily-plans) | main | `3178e83` | privat |
| `fusion-hero-os-v1/` | [95guknow/fusion-hero-os-v1](https://github.com/95guknow/fusion-hero-os-v1) | main | `610334f` | privat |
| `heroic-fusion-os-manifest/` | [95guknow/heroic-fusion-os-manifest](https://github.com/95guknow/heroic-fusion-os-manifest) | fourteen | `cd4191f` | öffentlich |
| `kilo/` | [95guknow/kilo](https://github.com/95guknow/kilo) | main | `5d82ed8` | öffentlich |
| `mister-builder-gui/` | [95guknow/mister-builder-gui](https://github.com/95guknow/mister-builder-gui) | main | `b57f7fd` | privat |
| `normalOS/` | [95guknow/normalOS](https://github.com/95guknow/normalOS) | main | `76c3582` | öffentlich |

## Nicht aus einem Standalone-Repo importiert

Diese Ordner unter `legacy_sources/` haben **kein** eigenes `95guknow`-Repository und
sind repo-interne Quellen — sie werden von diesem Sync nicht berührt:

- `heroic-core-foundation/`
- `private-hacking-suite/`

## Nicht gespiegelt

- `fusion-hero-os` selbst — ist dieses Repository (kein Selbst-Nesting).

## Hinweis

`heroic-fusion-os-manifest` steht auf dem Default-Branch `fourteen` (nicht `main`);
der Snapshot entspricht diesem Branch.
