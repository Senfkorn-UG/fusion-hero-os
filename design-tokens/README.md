# Design Tokens — Style Dictionary (Fusion Hero OS)

**Source of truth:** `tokens.json` (Git)  
**Build:** `npm run style-dictionary`  
**Config:** `config.js` (custom formatters for Terminal · VS Code · SharePoint)

## Policy

| | |
|--|--|
| Secret vault for colors | **No** — public design values |
| Runtime self-mutation | **No** — edit source, then rebuild |
| Sync guarantee | Re-run build on every `tokens.json` change (local or CI) |

## Fixed palette + three layer accents

| Token | Role | Value |
|-------|------|-------|
| `color.layer.l0` | MasterSeed / foundation | `#f5c542` |
| `color.layer.l1` | Operative stack (dashboard) | `#00ffd5` |
| `color.layer.l2` | Ascension / aspirational | `#a855f7` |

Plus fixed `color.bg.*`, `color.fg.*`, `color.accent.*`, `color.semantic.*`, `color.ansi.*`.

## Commands

```powershell
cd C:\Users\Admin\fusion-hero-os
npm run style-dictionary
# equivalent:
npx style-dictionary build -c design-tokens/config.js
```

Legacy alias: `npm run tokens:build` → same command.

## Outputs (`dist/`)

| File | Format |
|------|--------|
| `terminal/windows-terminal.colorScheme.json` | Windows Terminal `schemes[]` entry |
| `vscode/colorCustomizations.json` | Merge into `.vscode/settings.json` |
| `sharepoint/theme.json` | SPO theme JSON (`Add-SPOTheme` / admin UI) |
| `css/tokens.css` | `:root` CSS variables |
| `manifest.json` | Source SHA-256 + layer accents |

### VS Code

Merge the generated object into `.vscode/settings.json` (or copy the `workbench.colorCustomizations` block).

### Windows Terminal

Paste the scheme object into `settings.json` → `schemes`, then set `"colorScheme": "Fusion Hero OS v12.0.0"` on a profile.

### SharePoint

Import `sharepoint/theme.json` with SPO theming tools. `layerAccents` is extra metadata for your stack; SPO uses `palette`.

## CI sketch

```yaml
- run: npm run style-dictionary
- run: git diff --exit-code design-tokens/dist
```

## Meister Hasch bridge

Role → layer accents (labor frame, public colors only):

| Role | Layer | Hex |
|------|-------|-----|
| Meister | L0 | `#f5c542` |
| Held | L1 | `#00ffd5` |
| St3phaN | L2 | `#a855f7` |

Machine bridge: `docs/dissertation/meister_hasch_layers.json`  
Control: `docs/dissertation/MEISTER_HASCH_KONTROLLE.md`  
Asset seal (PNG hash) is independent of token edits.

## Explicit non-goals

- Azure Key Vault / HashiCorp Vault as token store  
- Autopoietic rewrite of tokens at runtime  
- Treating brand hex values as credentials  
