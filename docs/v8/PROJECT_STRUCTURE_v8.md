# Fusion Hero OS v8 — Projektstruktur (Ist-Zustand)

Diese Datei beschreibt die tatsächliche, aktuelle Ordnerstruktur des Repos
(Stand: CI-/Cleanup-Durchgang 2026-07). Sie ersetzt ältere, teils rein
aspirative Struktur-Dokumente (siehe `docs/PROJECT_STRUCTURE_v7.4.md` im
Archiv), die Ordner/Dateien beschrieben, die nie umgesetzt wurden.

## Aktiver Code

| Pfad | Sprache | Zweck |
|---|---|---|
| `app.py` | Python | NiceGUI-Desktop-GUI, Einstiegspunkt für die lokale IDE |
| `core/` | Python | Kernmodule (u.a. `heroic_math_engine.py`, `heroic_core_orchestrator.py`, `cec.py`, `rhe.py`) |
| `engine/` | Python | QUBO-Solver / Simulated-Annealing-Kernel (`mainframe.py`, `mining_qubo.py`) |
| `orchestration/` | Python | Multi-Agenten-System (`agents.py`: MessageBus, TaskQueue, Supervisor) |
| `methodology/` | Python | Service-Wrapper für externe Connectoren (GitHub, Drive, Vercel, …), standardmäßig Dry-Run |
| `src/` | JS/Svelte | SvelteKit-Frontend (eigenständig, kommuniziert nicht direkt mit dem Python-Kern im Code) |
| `rust_engine_crate/` | Rust | PyO3-Bindings für den Solver-Kernel (experimentell, noch nicht produktiv eingebunden) |
| `kernel/` | C/ASM | Low-Level-Prototyp (Boot-Code, Treiber-Stubs) — experimentell, nicht Teil des laufenden Systems |
| `tests/` | Python | pytest-Suite, wird von CI ausgeführt |

## Konfiguration & Tooling

- `requirements.txt` / `requirements-dev.txt` — Python-Abhängigkeiten
- `package.json` / `vite.config.js` / `jsconfig.json` — Node/SvelteKit-Toolchain
- `pytest.ini` — Testkonfiguration (`pythonpath = .`, `testpaths = tests`)
- `.github/workflows/` — CI (siehe unten)
- `Dockerfile` — Container-Build

## CI-Workflows

Nach dem Cleanup-Durchgang aktiv:

- `ci.yml` — Haupt-CI: Ruff-Lint, Core-Import-Check, Heroic-Math-Engine-Verifikation, pytest (Matrix: Python 3.11/3.12 auf `main`/`develop`, leichter Check auf anderen Branches)
- `fusion-hero-os-hyperthread.yml` — Strukturvalidierung (Core-Verzeichnis vorhanden, Python-Syntax-Check, Migrationskonzept-Vollständigkeit)
- `summary.yml` — automatische Zusammenfassung neuer Issues

Entfernt wurden reine Duplikate, nicht ausführender "Theater"-CI (nur `echo`-Statements ohne echte Prüfung) sowie Drittanbieter-Scanner-Templates, die nie konfiguriert wurden (falsche/fehlende Secrets, veraltete Runner-Images) und dauerhaft hängen blieben.

## Dokumentation & Archiv

- `docs/` — aktive Dokumentation (Architektur, Integration, Roadmap)
- `docs/99_archive/` — historische/versionierte Markdown-Dokumente (v7.4–v7.12), aus dem Root hierher verschoben
- `04_Buch_und_Archiv/`, `06_Master_Archive/`, `archive/`, `v2_beta/`, `03_Code/` — größere historische Materialsammlungen (Buch-Manuskripte, alte Framework-Stände, Wissensdatenbank-Versionen). Diese wurden im Rahmen dieses Durchgangs **nicht** inhaltlich konsolidiert, da sie umfangreich sind und eine inhaltliche Bewertung durch den Repo-Owner erfordern — siehe Statusbericht für Details und Vorschläge.

## Bekannte offene Punkte

- `src/` (SvelteKit) und der Python-Kern laufen aktuell unabhängig; eine dokumentierte Schnittstelle (REST/WebSocket) fehlt.
- `rust_engine_crate/` ist nicht in `engine/rust_backend.py` eingebunden (Stub).
- Mehrere Ordner enthalten Mehrfachversionen desselben Inhalts (z. B. `03_Code/core/knowledge/Geisteskrankheiten_4D_Matrix_v2` bis `v7`, dreifach verschachtelte Kopien in `04_Buch_und_Archiv/`). Konsolidierung erfordert inhaltliche Entscheidungen und wurde bewusst nicht automatisiert durchgeführt.
