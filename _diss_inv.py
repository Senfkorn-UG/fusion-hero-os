import os, json, time
from pathlib import Path
root = Path(r"C:\Users\Admin\fusion-hero-os")
# inventory key trees
trees = ["docs", "06_Master_Archive", "04_Buch_und_Archiv", "ascension_os", "archive", "docs/Heroismus", "docs/v8", "docs/01_vision", "docs/02_architecture"]
inv = {}
for t in trees:
    p = root / t
    if not p.exists():
        inv[t] = {"exists": False}
        continue
    files = [x for x in p.rglob("*") if x.is_file()]
    by_ext = {}
    for f in files:
        by_ext[f.suffix.lower() or "(none)"] = by_ext.get(f.suffix.lower() or "(none)", 0) + 1
    inv[t] = {"exists": True, "files": len(files), "by_ext": dict(sorted(by_ext.items(), key=lambda kv: -kv[1])[:12])}
# root key docs
keys = ["BEST_VERSION.md","README.md","FUSION_HERO_OS_v7.5_MASTER_UNIFIED.md","Fusion_MasterSeed_v7.11.md","fusion_unified.yaml","mesh_connectors.yaml","mesh_service_coordination.yaml","proof_registry.yaml","PMS.yaml"]
key_meta = {}
for k in keys:
    fp = root / k
    if fp.exists():
        key_meta[k] = {"bytes": fp.stat().st_size, "lines": sum(1 for _ in fp.open("r", encoding="utf-8", errors="replace"))}
out = {"ts": time.time(), "inventory": inv, "keys": key_meta}
outp = Path.home()/".fusion"/"mesh"/"coordination"/"dissertation_corpus_inventory.json"
outp.parent.mkdir(parents=True, exist_ok=True)
outp.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2)[:8000])
