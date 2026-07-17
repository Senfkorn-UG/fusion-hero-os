# Dual-Org Push + Merge: 95guknow + Senfkorn-UG

**UTC/local:** 2026-07-17  
**Confirmation:** `=====bestätigung` (push und merge mit github 95guknow und senfkorn ug)  
**Platform:** v10.0.0

## Surfaces

| Host | Repo | Role |
|------|------|------|
| `95guknow` | fusion-hero-os | Personal/seed kanon (origin) |
| `Senfkorn-UG` | fusion-hero-os | Org/company mirror (remote `senfkorn`) |

## Guard change

`push_layer_guard.yaml` identities extended with Senfkorn-UG URLs + remote name `senfkorn` + branches develop/ascension (BCG additive).

## Strategy

- **origin (95guknow):** already at v10.0.0 `a4a3a25`; re-push + guard update commit
- **senfkorn (Senfkorn-UG):** diverged history (9 README-only commits not in kanon); backup tip then align main/develop/ascension to 95guknow heads
- **merge:** ops merge (private+public timeline) + track heads aligned

*No private shards pushed. Force only where history divergence requires mirror overwrite after backup.*
