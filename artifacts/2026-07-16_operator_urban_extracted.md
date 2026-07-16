# Operator Urban — Extraction Report

**UTC:** 2026-07-16T00:15:56.664522+00:00
**Platform:** Fusion Hero OS v10.0.0
**Membrane:** `operator_identity_v1`
**Operative clean:** **True** (0 hits in operative prefixes)
**Publication surface hits (expected):** 65
**Other tree hits:** 18
**Vault:** `C:\Users\Admin\.fusion\operator\identity.local.json` (git-ignored via ~/.fusion/)

## Separation

| Layer | Identity |
|-------|----------|
| Runtime / mesh / Comädchen | role=`operator` |
| Operator-local vault | optional legal/publication bind |
| Dissertation / Academia | author (publication surface) |

## Rules

- Runtime role = operator (abstract)
- Legal person only in ~/.fusion/operator/identity.local.json or publication docs
- Comädchen / mesh / agents address role only
- FUSION_AUTHOR_BIND=1 required to surface vault author in tools

## CLI

```powershell
python -m fusion_hero_os.core.operator_identity --status
python scripts/extract_operator_urban.py
# optional local bind (never commit):
$env:FUSION_AUTHOR_LEGAL_NAME="…"
$env:FUSION_AUTHOR_PUBLICATION_NAME="…"
$env:FUSION_AUTHOR_BIND="1"
python scripts/extract_operator_urban.py --bind-from-env
```

## Operative hits (must be empty)

_none — person extracted from operative package._
