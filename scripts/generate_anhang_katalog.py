# -*- coding: utf-8 -*-
"""Generate dissertation appendix A10 function catalog from AST."""
from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path


def main() -> int:
    root = Path("fusion_hero_os")
    by_pkg: dict[str, list] = defaultdict(list)
    for p in sorted(root.rglob("*.py")):
        if "__pycache__" in str(p):
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        rel = p.as_posix()
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

    out = Path("docs/dissertation/anhaenge")
    out.mkdir(parents=True, exist_ok=True)
    total_c = total_f = 0
    for items in by_pkg.values():
        for kind, *_ in items:
            if kind == "class":
                total_c += 1
            else:
                total_f += 1

    lines: list[str] = [
        "# A10 — Funktionskatalog (maschinell aus AST)",
        "",
        "**Geltung:** Spezifikation (Inventar des Codes, Stand Generator-Lauf).",
        "**Nicht:** Beweis der Korrektheit einzelner Funktionen.",
        "**Designvorlage:** V3.3 — Katalog = Spezifikation; Herleitungen in A01–A09.",
        "",
        f"**Dateien:** {len(by_pkg)} · **Klassen:** {total_c} · **Top-Level-Funktionen:** {total_f}",
        "",
        "Regenerieren: `python scripts/generate_anhang_katalog.py`",
        "",
    ]
    for rel, items in sorted(by_pkg.items()):
        lines.append(f"## `{rel}`")
        lines.append("")
        for kind, name, methods, priv in items:
            if kind == "class":
                lines.append(f"### class `{name}`")
                if methods:
                    lines.append("- public: " + ", ".join(f"`{m}`" for m in methods))
                if priv:
                    shown = priv[:20]
                    extra = " …" if len(priv) > 20 else ""
                    lines.append(
                        "- intern: " + ", ".join(f"`{m}`" for m in shown) + extra
                    )
                if not methods and not priv:
                    lines.append("- (Datenklasse / ohne Methoden)")
            else:
                lines.append(f"- def `{name}`")
        lines.append("")

    path = out / "A10_Funktionskatalog_AST.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path} classes={total_c} funcs={total_f} files={len(by_pkg)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
