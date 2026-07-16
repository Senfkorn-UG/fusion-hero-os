# Deploy · Push · Merge

**Kanon (v10):**

| Operation | Bedeutung | Deutsch |
|-----------|-----------|---------|
| **deploy** | **private** | privat |
| **push** | **public** | öffentlich |
| **merge** | **both** via dual timeline \(t \parallel \tau\) | beide verbinden |

```
deploy  →  private only   (~/.fusion vault, training, creative)
push    →  public only    (GitHub known remote, public MasterSeed display)
merge   →  both           (public display_id ↔ private module/function ↔ timeline)
```

## CLI

```powershell
python scripts/ops.py vocabulary
python scripts/ops.py deploy          # private
python scripts/ops.py push --dry      # public evaluate
python scripts/ops.py push            # public git push (guard + secrets)
python scripts/ops.py merge           # both via timeline
```

## Rules

- **deploy** never `git push`es private shards.  
- **push** never includes denylist (`.env`, `*.shard.gpg`, vault private).  
- **merge** writes link manifests only — no ciphertext in git.  
  - full: `~/.fusion/ops/merge_latest.json`  
  - summary: `docs/ops/merge_latest.summary.json`

## Related

- Push guard: `docs/mesh/PUSH_LAYER_GUARD.md`  
- MasterSeed public/private: `docs/masterseed/PUBLIC_VS_PRIVATE.md`  
- Dual timeline: `docs/training/DUAL_TIMELINE_AUTO_TRAIN.md`  
- Config: `ops_vocabulary.yaml`
