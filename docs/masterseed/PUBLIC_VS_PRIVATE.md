# MasterSeed: Public unique display · Private GPG+QUBO modular vault

**Policy:** Public presentation is **unambiguous and unique**.  
Private code material is **GPG-encrypted**, **QUBO-obfuscated**, and **split by module/function** locally.

## Public (may publish / show in UI)

| Field | Meaning |
|-------|---------|
| `display_id` | `MS-PUB-v10-{short8}-{check4}` — unique human form |
| `public_fingerprint` | SHA-256 over public-safe fields only |
| `integrity_ok` | boolean |
| `state_hash_prefix` | first 12 hex of `state_hash()` only |
| `criticality_target_display` | labeled model value |

```powershell
python -m fusion_hero_os.core.masterseed_public
python -m fusion_hero_os.core.masterseed_vault --public-only
```

Example ID: `MS-PUB-v10-XXXXXXXX-YYYY`

## Private (never publish)

Root: `~/.fusion/masterseed/private/modules/{module}/functions/{function}.shard.gpg`

Pipeline per function shard:

1. JSON payload (binding metadata — not source dump of whole repo)  
2. **QUBO permute** (byte-block permutation from seed-derived QUBO)  
3. **GPG** symmetric (`FUSION_MASTERSEED_GPG_PASSPHRASE`) or recipient encrypt  

```powershell
python -m fusion_hero_os.core.masterseed_vault --seal
python -m fusion_hero_os.core.masterseed_vault --status
```

## Module / function split

Configured in `masterseed_public_display.yaml` → `modules_split`:

- `core.orchestrator` · `MasterSeed.state_hash` · `verify_integrity` · …
- `core.masterseed_sync` · `mutual_sync` · …
- `engine.mainframe` · annealing · …
- …

## Anti-patterns

- Publishing `.shard.gpg` or vault private paths  
- One monolithic private blob without module split  
- Ambiguous public labels without checksum  

## Related

- `MasterSeed` class: `fusion_hero_os/core/heroic_core_orchestrator.py`  
- Sync: `masterseed_sync.py`  
- Push guard denylist should keep vault secrets local  
