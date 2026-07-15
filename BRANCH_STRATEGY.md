# Branching Strategy — Fusion Hero OS → AscensionOS

> **Stand:** v10.0.0 · 2026-07-15

## Versionierung (kanonisch ab v8.3.0, aktueller Kanon v10.0.0)

**Quelle der Wahrheit ist der annotierte Git-Tag `vMAJOR.MINOR.PATCH` auf
`main` dieses Repos** (`95guknow/fusion-hero-os`), gespiegelt in der Datei
`VERSION` im Root. Jeder Tag bekommt ein GitHub-Release. Alles andere ist
abgeleitet — kein Dokument, Branch oder Manifest führt eine eigene Zählung.

- **MAJOR** = Ära.
  - **8** = FuHOS-Konsolidierungsära (letzter Release-Tag der Ära: `v8.3.0`).
  - **9** = nie als alleiniges Platform-Release vergeben; „v9.x“ bleibt
    **Roadmap-Label** für den Ascension-Track in `ascension_os/` (loadable).
  - **10** = aktuelle operative Plattform-Ära (Privacy/PII Stage-A/B,
    Consent-Gate, einheitliche Manifest-Version, Archive scrypt-KDF) —
    **additiv** über den v8.3-Funktionskern (BCG). Aktuell: **`10.0.0`**.
- **MINOR** = Feature-/Konsolidierungsstand (neue Layer, Mesh-Ausbau, …).
- **PATCH** = Fixes.
- Vorab-Stände: `v10.1.0-rc.1` usw.

**Mechanik:**

- `VERSION` (Root) trägt die Plattform-Version ohne `v`-Prefix.
- `scripts/bump_version.py` setzt sie und gleicht alle Manifeste an
  (`package.json` Root + workstation, `pyproject.toml`, beide Crate-
  `Cargo.toml`). CI-Gate: `bump_version.py --check` (fail bei Drift).
- Release: `python scripts/bump_version.py X.Y.Z` → Commit → Merge nach
  `main` → `git tag -a vX.Y.Z` → `gh release create vX.Y.Z --generate-notes`.
- Commits folgen Conventional Commits (`feat:`, `fix:`, `docs:`, …), damit
  MINOR/PATCH ableitbar sind und Release-Notes automatisch entstehen.
- **Keine Versionsnummern mehr in Branch- oder Dateinamen.** Neue Doku trägt
  den Stand nur im Header (`> Stand: vX.Y.Z`). Bestehende `archive/v*`-
  Branches und `_v7.x_`-Dateien bleiben unangetastete Historie.

**Ökosystem:** Vorgänger-Repos (`fusion-hero-os-v1`, `Fusion_Hero_OS_v1.1`,
`fusion-hero-core`, `alte-frau-95g-heroic-core`, `AscensionOS`, `FuHOS_pub`)
sind auf GitHub archiviert. Aktive Satelliten-Repos (`normalOS`,
`fusion-hero-vault`, `mister-builder-gui`, `dashboard`,
`fusion-hero-os-daily-plans`) versionieren unabhängig nach demselben Schema
und deklarieren ihre Plattform-Kompatibilität in `fuhos_compat.yaml`
(z. B. `fuhos_compat: ">=10.0 <11"` bzw. legacy `">=8.3 <11"`).

## Aktuelles Modell (Hyperthreading + Archive)

### `main` (Stable Release Line)
- Geschützt. Direkte Pushes sind blockiert.
- Nur Merges via Pull Request von `develop` oder `ascension`.

### `develop` – Option A Track (Evolutionary)
- Aktive Weiterentwicklung des bestehenden Heroic Core.

### `ascension` – Option B Track (Strong Ascension Path)
- Radikalere Entwicklungslinie für AscensionOS.
- `ascension_os/` und `AscensionCore` sind jetzt auch auf `main` verfügbar.

### `archive`
- Sinnvoll organisiertes Archiv für alles Alte.

## Bifurzierter Bottom-Up-Merge (WSL -> Windows -> GitHub)

Fuer die Zweigstelle **WSL** (`fusion-hero-core`) und den **Mainframe** (`C:\Users\Admin\fusion-hero-os`):

| Layer | Repo | Rolle |
|-------|------|-------|
| 0 (Leaf) | WSL `~/fusion-hero-core` | Entwicklung, kein GitHub-Push |
| 1 (Mainframe) | Windows `fusion-hero-os` | Merge + Push (GitHub-Auth) |
| 2 (Root) | `origin/main` | Kanon auf GitHub |

**Skripte:** `workstation/merge-bottom-up.sh` (WSL) + `workstation/merge-bottom-up.ps1` (Windows)

```bash
# Vollstaendiger Lauf
bash workstation/merge-bottom-up.sh

# Nur Plan
bash workstation/merge-bottom-up.sh --plan-only

# Mit Commit-Message fuer WSL-Aenderungen
bash workstation/merge-bottom-up.sh --message "feat: ..."
```

**Regeln:**
- Merge-Strategie: `git pull --no-rebase` (kein Rebase auf Auto-Save-Historie)
- Keine Duplikate im Repo-Root (`workstation/`, `tools/`, `src/` sind kanonisch)
- Status: `~/.fusion/merge-bottom-up.status.json`

**Hinweis:** `develop`/`ascension` sind derzeit hinter `main` — zuerst `main` in die Tracks mergen, nicht umgekehrt.

**Ziel:** Alles seit April 2026 entwickelte soll in AscensionOS münden.
