# -*- coding: utf-8 -*-
"""Generate dissertation appendix A10 function catalog from AST.

Scans:
  - fusion_hero_os/**/*.py
  - 03_Code/Dashboard/**/*.py  (surfaces, bridge, routes)
"""
from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [
    ROOT / "fusion_hero_os",
    ROOT / "03_Code" / "Dashboard",
]
OUT = ROOT / "docs" / "dissertation" / "anhaenge" / "A10_Funktionskatalog_AST.md"


def _rel(p: Path) -> str:
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def scan_tree(root: Path) -> dict[str, list]:
    by_pkg: dict[str, list] = defaultdict(list)
    if not root.exists():
        return by_pkg
    for p in sorted(root.rglob("*.py")):
        if "__pycache__" in str(p):
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        rel = _rel(p)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods = [
                    n.name
                    for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not n.name.startswith("_")
                ]
                priv = [
                    n.name
                    for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and n.name.startswith("_")
                ]
                by_pkg[rel].append(("class", node.name, methods, priv))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                by_pkg[rel].append(("def", node.name, [], []))
    return by_pkg


def main() -> int:
    by_pkg: dict[str, list] = {}
    for root in SCAN_ROOTS:
        by_pkg.update(scan_tree(root))

    total_c = total_f = 0
    for items in by_pkg.values():
        for kind, *_ in items:
            if kind == "class":
                total_c += 1
            else:
                total_f += 1

    dash_files = sum(1 for k in by_pkg if k.startswith("03_Code/Dashboard"))
    core_files = sum(1 for k in by_pkg if k.startswith("fusion_hero_os"))

    lines: list[str] = [
        "# A10 — Funktionskatalog (maschinell aus AST)",
        "",
        "**Geltung:** Spezifikation (Inventar des Codes, Stand Generator-Lauf).",
        "**Nicht:** Beweis der Korrektheit einzelner Funktionen.",
        "**Designvorlage:** V3.3 — Katalog = Spezifikation; Herleitungen in A01–A09.",
        "",
        f"**Dateien gesamt:** {len(by_pkg)} "
        f"(fusion_hero_os: {core_files} · Dashboard: {dash_files}) · "
        f"**Klassen:** {total_c} · **Top-Level-Funktionen:** {total_f}",
        "",
        "Scan-Wurzeln:",
        "- `fusion_hero_os/`",
        "- `03_Code/Dashboard/`",
        "",
        "Regenerieren: `python scripts/generate_anhang_katalog.py`",
        "",
    ]

    # Group: package first, then dashboard
    for section_title, pred in (
        ("Teil I — `fusion_hero_os`", lambda k: k.startswith("fusion_hero_os")),
        ("Teil II — `03_Code/Dashboard`", lambda k: k.startswith("03_Code/Dashboard")),
        ("Teil III — Sonstiges", lambda k: not k.startswith("fusion_hero_os") and not k.startswith("03_Code/Dashboard")),
    ):
        keys = [k for k in sorted(by_pkg) if pred(k)]
        if not keys:
            continue
        lines.append(f"# {section_title}")
        lines.append("")
        for rel in keys:
            items = by_pkg[rel]
            lines.append(f"## `{rel}`")
            lines.append("")
            for kind, name, methods, priv in items:
                if kind == "class":
                    lines.append(f"### class `{name}`")
                    if methods:
                        lines.append(
                            "- public: " + ", ".join(f"`{m}`" for m in methods)
                        )
                    if priv:
                        shown = priv[:20]
                        extra = " …" if len(priv) > 20 else ""
                        lines.append(
                            "- intern: "
                            + ", ".join(f"`{m}`" for m in shown)
                            + extra
                        )
                    if not methods and not priv:
                        lines.append("- (Datenklasse / ohne Methoden)")
                else:
                    lines.append(f"- def `{name}`")
            lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT} classes={total_c} funcs={total_f} files={len(by_pkg)} "
        f"(core={core_files} dash={dash_files})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
