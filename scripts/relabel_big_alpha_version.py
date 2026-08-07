#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relabel BIG ALPHA corner version badges via PIL (exact strings, no diffusion).

Default: right badge → FUSION HERO OS v{VERSION from root}
Left badge stays v9.10 ASPIRATIONAL unless --left is set.

Honesty: only paints discrete text; composition/DNA/title art untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]

# Sync targets inside repo (byte-identical after update)
REPO_TARGETS = [
    ROOT / "03_Code" / "Dashboard" / "static" / "big_ALPHA.png",
    ROOT / "ascension_os" / "assets" / "big_ALPHA.png",
    ROOT / "docs" / "dissertation" / "assets" / "ascensionOS_big_ALPHA.png",
    ROOT / "docs" / "dissertation" / "assets" / "big_ALPHA_v15.png",
    ROOT / "memes" / "ascensionOS_big_ALPHA.png",
]

CANON_CANDIDATES = [
    Path(r"C:\Dissertation_95guknow\assets\big_ALPHA.png"),
    ROOT / "03_Code" / "Dashboard" / "static" / "big_ALPHA.png",
    ROOT / "docs" / "dissertation" / "assets" / "ascensionOS_big_ALPHA.png",
]


def read_platform_version() -> str:
    vf = ROOT / "VERSION"
    if vf.is_file():
        return vf.read_text(encoding="utf-8").strip() or "15.2.0"
    return "15.2.0"


def pick_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Erste vorhandene Bold-Sans in Kandidatenreihenfolge.

    Windows zuerst (der Kanon-Look wurde dort gesetzt), dann Linux — sonst
    fiel der Lauf auf CI/Containern auf ImageFont.load_default() zurueck, und
    das ist eine winzige Bitmap-Schrift: das Badge waere unlesbar neben dem
    28px-Original. Liberation Sans Bold steht vor DejaVu, weil es metrisch
    Arial-kompatibel ist und damit der Windows-Zweitwahl entspricht.
    """
    for path in (
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\seguiemj.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ):
        p = Path(path)
        if p.is_file():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def _median_bg(im: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    crop = im.crop(box)
    # sample corners of region (avoid text center)
    w, h = crop.size
    samples = [
        crop.getpixel((2, 2)),
        crop.getpixel((w - 3, 2)),
        crop.getpixel((2, h - 3)),
        crop.getpixel((w - 3, h - 3)),
        crop.getpixel((w // 2, 2)),
        crop.getpixel((w // 2, h - 3)),
    ]
    rs = sorted(s[0] for s in samples)
    gs = sorted(s[1] for s in samples)
    bs = sorted(s[2] for s in samples)
    mid = len(samples) // 2
    return rs[mid], gs[mid], bs[mid]


def paint_badge(
    im: Image.Image,
    *,
    text: str,
    side: str,
    fill: tuple[int, int, int] = (0, 229, 255),
    font_size: int = 28,
) -> None:
    """Paint left or right bottom badge; cover previous string first."""
    w, h = im.size
    draw = ImageDraw.Draw(im)
    font = pick_font(font_size)
    # Measure
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin_x = 36
    baseline_y = h - 42
    if side == "left":
        x = margin_x
    else:
        x = w - margin_x - tw
    y = baseline_y - th

    # Cover rect slightly larger than text
    pad = 10
    cover = (max(0, x - pad), max(0, y - pad), min(w, x + tw + pad), min(h, y + th + pad + 6))
    bg = _median_bg(im, cover)
    draw.rectangle(cover, fill=bg)

    # Soft cyan glow (offset darker layers)
    glow = (0, 120, 160)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)):
        draw.text((x + dx, y + dy), text, font=font, fill=glow)
    draw.text((x, y), text, font=font, fill=fill)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Relabel BIG ALPHA version badges")
    ap.add_argument("--version", default=None, help="Platform version (default: root VERSION)")
    ap.add_argument(
        "--left",
        default="v9.10 ASPIRATIONAL",
        help="Left badge text (default keep aspirational track)",
    )
    ap.add_argument("--no-left", action="store_true", help="Do not repaint left badge")
    ap.add_argument("--source", default=None, help="Source PNG path")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    version = args.version or read_platform_version()
    right = f"FUSION HERO OS v{version}"

    src = Path(args.source) if args.source else None
    if src is None:
        for c in CANON_CANDIDATES:
            if c.is_file():
                src = c
                break
    if src is None or not src.is_file():
        print("ERROR: no source big_ALPHA.png", file=sys.stderr)
        return 1

    im = Image.open(src).convert("RGB")
    if not args.no_left and args.left:
        paint_badge(im, text=args.left, side="left")
    paint_badge(im, text=right, side="right")

    tmp = ROOT / "docs" / "ops" / f"_big_ALPHA_v{version.replace('.', '_')}_work.png"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    im.save(tmp, format="PNG", optimize=True)

    digest = sha256_file(tmp)
    print(f"source:  {src}")
    print(f"left:    {args.left if not args.no_left else '(unchanged)'}")
    print(f"right:   {right}")
    print(f"size:    {im.size}  bytes={tmp.stat().st_size}")
    print(f"sha256:  {digest}")

    if args.dry_run:
        print("dry-run: not writing targets")
        return 0

    written: list[str] = []
    for dest in REPO_TARGETS:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tmp, dest)
        written.append(str(dest))

    # External canon + versioned copies (best-effort) — NUR auf Windows.
    #
    # Der frueher hier stehende Guard `extra.parent.is_dir()` war fuer
    # Windows-Semantik geschrieben und ging auf POSIX still daneben: dort ist
    # "C:\Dissertation_95guknow\assets\big_ALPHA.png" kein Pfad, sondern EIN
    # Dateiname (Backslash ist kein Separator). `.parent` ist damit '.', der
    # Guard greift, und die Kopie landet als Datei mit Backslashes im Namen im
    # Repo-Root. Ein Lauf auf Linux/CI hat so drei Muelldateien erzeugt.
    if os.name == "nt":
        for extra in (
            Path(r"C:\Dissertation_95guknow\assets\big_ALPHA.png"),
            Path(rf"C:\Dissertation_95guknow\assets\big_ALPHA_v{version}.png"),
            Path(r"C:\Dissertation_95guknow\assets\big_ALPHA_v15.png"),
        ):
            try:
                if extra.parent.is_dir():
                    shutil.copy2(tmp, extra)
                    written.append(str(extra))
            except OSError as e:
                print(f"note: skip {extra}: {e}")
    else:
        print("note: externe Kanon-Kopien uebersprungen (kein Windows)")

    # Keep historical v13 filename as copy of new art only if explicitly requested?
    # Honesty: big_ALPHA_v13.png should remain v13-era OR be left alone.
    # We write big_ALPHA_v15.png and primary names only.

    print("written:")
    for w in written:
        print(f"  {w}")

    # Ops doc
    doc = ROOT / "docs" / "ops" / "BIG_ALPHA_ASSET_V15.md"
    doc.write_text(
        f"""# BIG ALPHA Asset — v{version} label sync

**Source (canonical disk):** `C:\\Dissertation_95guknow\\assets\\big_ALPHA.png`  
**Versioned copy:** `C:\\Dissertation_95guknow\\assets\\big_ALPHA_v{version}.png`  
**Also in repo:** `docs/dissertation/assets/big_ALPHA_v15.png`

## Visual

| Field | Value |
|-------|--------|
| Title | ASCENSIONOS / BIG ALPHA |
| Left label | `{args.left if not args.no_left else "(unchanged)"}` |
| Right label | `{right}` |
| Size | {im.size[0]}×{im.size[1]} · ~{tmp.stat().st_size // 1024} KB |
| SHA256 | `{digest}` |

## Synced repo paths (byte-identical)

- `03_Code/Dashboard/static/big_ALPHA.png`
- `ascension_os/assets/big_ALPHA.png`
- `docs/dissertation/assets/ascensionOS_big_ALPHA.png`
- `docs/dissertation/assets/big_ALPHA_v15.png`
- `memes/ascensionOS_big_ALPHA.png`

## Method (honesty)

Exact version strings painted via PIL (not diffusion) for discrete accuracy.
Composition / DNA / title art preserved; only corner badges repainted.
Script: `scripts/relabel_big_alpha_version.py` (platform from root `VERSION`={version}).

Historical `big_ALPHA_v13.png` / `BIG_ALPHA_ASSET_V13.md` remain as v13-era record.
""",
        encoding="utf-8",
    )
    print(f"doc: {doc}")

    # Cleanup work file from ops root noise optional — keep for audit
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
