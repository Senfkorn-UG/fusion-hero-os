# Operator Urban — Extraction Report

**UTC:** 2026-07-16  
**Platform:** Fusion Hero OS v10.0.0  
**Membrane:** `operator_identity_v1`  
**Operative clean:** **True** (0 hits in operative prefixes)  
**Publication surface hits (expected):** 65  
**Other tree hits:** 18  
**Vault:** `~/.fusion/operator/identity.local.json` (git-ignored via `~/.fusion/`)

## Separation

| Layer | Identity |
|-------|----------|
| Runtime / mesh / Comaedchen | role=`operator` |
| Operator-local vault | optional legal/publication bind |
| Dissertation / Academia | author (publication surface) |

## Rules

- Runtime role = operator (abstract)
- Legal person only in `~/.fusion/operator/identity.local.json` or publication docs
- Comaedchen / mesh / agents address role only
- `FUSION_AUTHOR_BIND=1` required to surface vault author in tools

## What was done

1. New module `fusion_hero_os/core/operator_identity.py`
2. Removed hard-coded legal author from `conversation_archive_inventory.py`
3. Extractor `scripts/extract_operator_urban.py`
4. Doc `docs/security/OPERATOR_IDENTITY_MEMBRANE.md`
5. Tests `tests/test_operator_identity.py` (6 passed)
6. Catalog / BEST_VERSION notes

## CLI

```powershell
python -m fusion_hero_os.core.operator_identity --status
python scripts/extract_operator_urban.py
# optional local bind (never commit):
$env:FUSION_AUTHOR_LEGAL_NAME="..."
$env:FUSION_AUTHOR_PUBLICATION_NAME="..."
$env:FUSION_AUTHOR_BIND="1"
python scripts/extract_operator_urban.py --bind-from-env
```

## Note

Dissertation and Academia **keep** the canonical author name (Namenskanon).  
Extraction means: **runtime role is not the person**. Publication is a separate surface.
