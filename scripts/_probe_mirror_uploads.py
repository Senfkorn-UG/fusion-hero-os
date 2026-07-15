# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path

p = Path(r"C:\Users\Admin\AppData\Local\Google\DriveFS\116784105447428485978\mirror_sqlite.db")
con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
cur = con.cursor()
for t in ("pending_uploads", "queued_uploads", "pending_deletes"):
    try:
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(t, n)
    except Exception as e:
        print(t, e)
rows = cur.execute(
    "SELECT local_filename, cloud_filename, local_size, is_root "
    "FROM mirror_item WHERE local_filename LIKE '%Fusion%' OR cloud_filename LIKE '%Fusion%' "
    "LIMIT 30"
).fetchall()
print("fusion_rows", len(rows))
for r in rows:
    print(" ", r)
con.close()

from pathlib import Path as P
for path in (
    P.home() / "Documents" / "Fusion_Hero_OS_Sicherung",
    P.home() / "Desktop" / "Fusion_Hero_OS_Sicherung",
):
    files = list(path.rglob("*")) if path.exists() else []
    nfiles = sum(1 for f in files if f.is_file())
    print(path, "exists", path.exists(), "files", nfiles)
