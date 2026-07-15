# -*- coding: utf-8 -*-
"""Probe Google DriveFS mount / mirror paths (no secrets printed)."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

ACC = Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\DriveFS\116784105447428485978"))
ROOT_PREF = Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\DriveFS\root_preference_sqlite.db"))


def dump_text(path: Path, limit: int = 800) -> None:
    if not path.exists():
        print(f"missing {path}")
        return
    data = path.read_bytes()
    print(f"== {path.name} len={len(data)}")
    print(data.decode("utf-8", errors="replace")[:limit])


def dump_db(path: Path, only_interesting: bool = True) -> None:
    if not path.exists():
        print(f"missing db {path}")
        return
    print(f"== DB {path}")
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except Exception as e:
        print("open fail", e)
        return
    cur = con.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("tables", tables[:50])
    for t in tables:
        low = t.lower()
        if only_interesting and not any(
            k in low for k in ("pref", "mount", "account", "mirror", "sync", "path", "folder", "root", "config", "drive")
        ):
            continue
        try:
            cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t})").fetchall()]
            rows = cur.execute(f"SELECT * FROM {t} LIMIT 20").fetchall()
            print(f"T {t} {cols}")
            for r in rows:
                s = repr(r)
                if len(s) > 400:
                    s = s[:400] + "..."
                # redact long tokens
                print(" ", s)
        except Exception as e:
            print("err", t, e)
    con.close()


def main() -> None:
    print("ACC", ACC, "exists", ACC.is_dir())
    for name in ("identifier", "user_settings", "core_feature_config"):
        dump_text(ACC / name)
    dump_db(ROOT_PREF, only_interesting=False)
    dump_db(ACC / "mirror_sqlite.db")
    lf = ACC / "local_folders"
    if lf.exists():
        for p in sorted(lf.rglob("*"))[:40]:
            print("LF", p)
    # letter scan
    for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        root = Path(f"{letter}:/")
        if root.exists():
            try:
                names = [x.name for x in root.iterdir()][:12]
            except Exception as e:
                names = [f"err:{e}"]
            print(f"DRIVE {letter}: {names}")


if __name__ == "__main__":
    main()
