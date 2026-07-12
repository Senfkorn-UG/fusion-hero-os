#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Doc-Versions-Gate: jedes aktive Dokument traegt eine sichtbare Versionierung.

Regel (CI-fatal bei Verstoss):
  Ein Dokument gilt als versioniert, wenn EINE der Bedingungen erfuellt ist:
    a) Der Dateiname enthaelt einen Versionsmarker (v<major>[.<minor>...]).
    b) Die ersten 12 Zeilen enthalten '**Stand:**' ODER 'version:' (Frontmatter)
       ODER ein 'v<major>.<minor>'-Muster.

Scope (kuratiert, bewusst NICHT alles):
  * alle Top-Level-*.md
  * die aktiven SKILL.md-Standorte (01_Framework, docs, 03_Code/reference,
    01_Framework/skills/**, .grok/skills/**)
  * docs/OVERVIEW.md
Ausgenommen: legacy_sources/ (Snapshots fremder Repos, siehe IMPORT_MANIFEST),
generierte Artefakte (DEPENDENCY_ATLAS.md traegt seinen Generator-Hinweis),
Archive (docs/99_archive, 04_Buch_und_Archiv, 06_Master_Archive).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

NAME_MARKER = re.compile(r"v\d+([._]\d+)*", re.IGNORECASE)
HEAD_MARKER = re.compile(r"\*\*Stand:\*\*|^version:|v\d+\.\d+", re.IGNORECASE | re.MULTILINE)
HEAD_LINES = 12


def _scope() -> list[Path]:
    docs: list[Path] = sorted(REPO_ROOT.glob("*.md"))
    docs += [
        REPO_ROOT / "docs" / "SKILL.md",
        REPO_ROOT / "docs" / "OVERVIEW.md",
        REPO_ROOT / "01_Framework" / "SKILL.md",
        REPO_ROOT / "03_Code" / "reference" / "SKILL.md",
    ]
    docs += sorted((REPO_ROOT / "01_Framework" / "skills").rglob("SKILL.md"))
    docs += sorted((REPO_ROOT / ".grok" / "skills").rglob("SKILL.md"))
    return [d for d in docs if d.is_file()]


def is_versioned(path: Path) -> bool:
    if NAME_MARKER.search(path.name):
        return True
    head = "\n".join(path.read_text(encoding="utf-8", errors="replace")
                     .splitlines()[:HEAD_LINES])
    return bool(HEAD_MARKER.search(head))


def main() -> int:
    missing = [p for p in _scope() if not is_versioned(p)]
    checked = len(_scope())
    if missing:
        for p in missing:
            rel = p.relative_to(REPO_ROOT)
            print(f"[DocVersions][FATAL] unversioniert: {rel} — "
                  f"'> **Stand:** vX.Y.Z · YYYY-MM-DD' im Kopf ergaenzen "
                  f"oder Versionsmarker in den Dateinamen.")
        print(f"[DocVersions] {len(missing)}/{checked} Dokumente ohne Versionierung.")
        return 1
    print(f"[OK] Doc-Versions-Gate: alle {checked} Dokumente im Scope sind versioniert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
