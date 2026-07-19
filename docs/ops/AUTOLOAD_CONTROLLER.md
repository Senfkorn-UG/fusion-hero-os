# Autoload Controller — post-reboot load

**Platform:** Fusion Hero OS v12.0.0  
**Controller:** `autoload_controller_v1`

## Purpose

Before a **desktop restart**, prepare updates + registration.  
After **login**, automatically load everything important.

## Scripts

| Script | When |
|--------|------|
| `scripts/prepare_reboot_autoload.ps1` | **Before** reboot |
| `scripts/autoload_controller.ps1` | **After** login (auto) |
| `fusion_hero_os.core.autoload_controller` | Status API (Python) |

## Before reboot

```powershell
cd C:\Users\Admin\fusion-hero-os
powershell -File scripts\prepare_reboot_autoload.ps1
# then restart Windows
```

Does:

1. `git pull origin main`
2. Dauer-Eupression continuous + Poly-FA ensure
3. Meister status
4. Registers **Startup** launcher + **Scheduled Task** `FusionHeroOS-AutoloadController` (AtLogOn)
5. Writes `~/.fusion/autoload_controller.json` → `ready_for_reboot: true`

## After reboot (automatic, ~25s delay)

1. Env pins (v12, `FUSION_AUTO_LOAD=1`, HT, …)
2. `git pull`
3. Dauer-Eupression pulse
4. Poly-FA handover policy
5. `start_all.ps1` (Dashboard :8000 + API autoload)
6. `scripts/activate_v12.py`
7. Hero Autoupdate service
8. Audio L1 (hear/speak person membrane)

**Log:** `~/.fusion/logs/autoload_controller.log`  
**Dashboard:** http://127.0.0.1:8000

## Manual fallback

```powershell
powershell -File C:\Users\Admin\fusion-hero-os\scripts\autoload_controller.ps1
powershell -File C:\Users\Admin\fusion-hero-os\scripts\autoload_controller.ps1 -SkipGui
python -m fusion_hero_os.core.autoload_controller --status
```

## Notes

- Structure write still **Poly-FA only** (desktop + request).
- Private vault never git-pulled as secrets.
- Dual-org: prepare fetches senfkorn best-effort; pull is origin/main.
