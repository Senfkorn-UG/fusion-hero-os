# x402 Full Stack — Fusion Hero OS

**One command builds the whole thing.**

```powershell
cd C:\Users\Admin\fusion-hero-os
python scripts\run_x402_stack.py
python scripts\run_x402_stack.py --release          # optional gh release
python scripts\run_x402_stack.py --broadcast-onchain  # needs FUSION_PUBLICITY_PRIVATE_KEY
```

## Package contents

| Piece | Path / command |
|-------|----------------|
| Threat audit (heroic math + gates + emergency) | `python -m fusion_hero_os.core.x402_hackability_audit --audit` |
| Sandbox evidence (6 cases) | `python -m fusion_hero_os.core.x402_sandbox_audit` |
| Attack sim SUCCESS (0,01 ct, dormant wallet) | `python -m fusion_hero_os.core.x402_sandbox_audit --simulate-attack` |
| On-chain publicity (Base self-tx) | `scripts/x402_onchain_publicity.py` |
| Instagram pack @95guknow | `docs/security/media/` · LIVE |
| Config | `x402_hackability.yaml` |
| API | `GET /api/x402/status` · `POST /api/x402/run` |
| Master report | `~/.fusion/x402/X402_STACK_MASTER.md` |

## Public surfaces

- **GitHub:** https://github.com/95guknow/fusion-hero-os  
- **Instagram:** https://www.instagram.com/95guknow/ (CONNECTED · LIVE)  
- **PR media:** https://github.com/95guknow/fusion-hero-os/pull/69  

## Policy

- Attack path: **sandbox only**
- Public damage envelope: **0,01 ct** notional · long-dormant lab wallet · **no real chain drain**
- x402 is **not** source-of-truth for MasterSeed
- Emergency warn when production gates open (default)

## Grok / GitHub notes

Grok-on-GitHub suggestions (CI honesty, export modules, connectors) live elsewhere in the repo.  
This stack is the **complete x402 security + media product** wired into v10.
