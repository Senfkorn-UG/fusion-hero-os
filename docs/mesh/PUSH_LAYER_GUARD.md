# Push Layer Guard — unwanted vs wanted pushes

**Config:** `push_layer_guard.yaml`  
**Code:** `fusion_hero_os/core/push_layer_guard.py`  
**Hook:** `scripts/install_push_guard_hooks.py` → `.git/hooks/pre-push`  
**Policy:** pseudo_inhouse_only · freemium=false

## Goal

| | Unwanted | Wanted |
|---|----------|--------|
| Auto-save spam to GitHub | **blocked** | — |
| Secrets / live inventory | **always blocked** | — |
| Conventional `feat:`/`fix:`/`docs:` | — | **allowed** |
| Explicit intent | — | **allowed** |
| Known remote only | others **blocked** | `95guknow/fusion-hero-os` |

## Known identifications

- Remote: `https://github.com/95guknow/fusion-hero-os.git`
- Branch: `main` (force/delete blocked)
- Platform: `VERSION` = `10.0.0`
- Path → layers: L0…L6 (foundation … protected local)
- Auto-save message prefix: `auto-save`
- Intent: env `FUSION_PUSH_INTENT=1` or commit marker `[push-ok]`

## Install hook

```powershell
python scripts/install_push_guard_hooks.py
```

## Wanted push examples

```powershell
# A) via operator secrets (.env loaded automatically — values never logged)
#    any of: FUSION_PUSH_SECRET, GITHUB_TOKEN, GROQ_API_KEY, OPENROUTER_API_KEY, …
python scripts/wanted_push_via_secrets.py
python scripts/wanted_push_via_secrets.py --dry   # evaluate only

# B) intent env
$env:FUSION_PUSH_INTENT = "1"
git push origin main

# C) conventional commit (not pure auto-save)
git commit -m "feat: add dual timeline training"
git push origin main

# D) marker
git commit -m "docs: update mesh [push-ok]"
git push origin main
```

Secrets unlock **wanted** identity only. They do **not** allow pushing `.env` / keys (hard denylist).

## Unwanted (blocked)

```powershell
# pure auto-save commits without intent
git push origin main
# → BLOCK: Unwanted auto-save push without intent
```

## CLI

```powershell
python -m fusion_hero_os.core.push_layer_guard
python -m fusion_hero_os.core.push_layer_guard --status
```

## Layer weave

Changes are classified into L0–L6. L6 protected local paths never push without intent. Hard denylist (`.env`, keys, `mesh_live_inventory.json`) never pushes even with intent.

`auto_save.ps1 -Push` runs the guard before `git push`.
