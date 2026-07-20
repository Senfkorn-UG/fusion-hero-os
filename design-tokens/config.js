/**
 * Style Dictionary config — Fusion Hero OS design tokens
 *
 * Source of truth: tokens.json (Git only — not a secret vault).
 * Refine by editing tokens.json, then: npm run style-dictionary
 * (or: npx style-dictionary build -c design-tokens/config.js)
 *
 * Custom formatters:
 *   fusion/windowsTerminal  → Windows Terminal color scheme
 *   fusion/vscodeSettings   → VS Code workbench.colorCustomizations fragment
 *   fusion/sharePointTheme  → SharePoint Online theme JSON
 *   fusion/cssVariables     → :root CSS custom properties (+ layer accents)
 */

import StyleDictionary from "style-dictionary";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

/** Flat map: "color.bg.base" → resolved value */
function tokenIndex(dictionary) {
  const map = Object.create(null);
  for (const t of dictionary.allTokens) {
    map[t.path.join(".")] = t.value;
  }
  return map;
}

function t(map, path, fallback) {
  if (path in map) return map[path];
  if (fallback !== undefined) return fallback;
  throw new Error(`[design-tokens] missing token: ${path}`);
}

function sourceSha256() {
  const raw = readFileSync(join(__dirname, "tokens.json"));
  return createHash("sha256").update(raw).digest("hex");
}

// ── Custom formats ──────────────────────────────────────────────────────────

StyleDictionary.registerFormat({
  name: "fusion/windowsTerminal",
  format: ({ dictionary }) => {
    const m = tokenIndex(dictionary);
    const name = `${t(m, "meta.name")} v${t(m, "meta.version")}`;
    const scheme = {
      name,
      background: t(m, "color.bg.base"),
      foreground: t(m, "color.fg.primary"),
      cursorColor: t(m, "color.layer.l1"),
      selectionBackground: t(m, "color.border.accent"),
      black: t(m, "color.ansi.black"),
      red: t(m, "color.ansi.red"),
      green: t(m, "color.ansi.green"),
      yellow: t(m, "color.ansi.yellow"),
      blue: t(m, "color.ansi.blue"),
      purple: t(m, "color.ansi.magenta"),
      cyan: t(m, "color.ansi.cyan"),
      white: t(m, "color.ansi.white"),
      brightBlack: t(m, "color.ansi.brightBlack"),
      brightRed: t(m, "color.ansi.brightRed"),
      brightGreen: t(m, "color.ansi.brightGreen"),
      brightYellow: t(m, "color.ansi.brightYellow"),
      brightBlue: t(m, "color.ansi.brightBlue"),
      brightPurple: t(m, "color.ansi.brightMagenta"),
      brightCyan: t(m, "color.ansi.brightCyan"),
      brightWhite: t(m, "color.ansi.brightWhite"),
      // Layer accents (extra keys for tooling; WT ignores unknown scheme fields safely)
      _layerL0: t(m, "color.layer.l0"),
      _layerL1: t(m, "color.layer.l1"),
      _layerL2: t(m, "color.layer.l2"),
    };
    return JSON.stringify(scheme, null, 2) + "\n";
  },
});

StyleDictionary.registerFormat({
  name: "fusion/vscodeSettings",
  format: ({ dictionary }) => {
    const m = tokenIndex(dictionary);
    // Fragment ready to merge into .vscode/settings.json
    const settings = {
      "workbench.colorCustomizations": {
        "editor.background": t(m, "color.bg.base"),
        "editor.foreground": t(m, "color.fg.primary"),
        "editorCursor.foreground": t(m, "color.layer.l1"),
        "editor.selectionBackground": t(m, "color.border.accent"),
        "editor.lineHighlightBackground": t(m, "color.bg.elevated"),
        "editorLineNumber.foreground": t(m, "color.fg.muted"),
        "editorLineNumber.activeForeground": t(m, "color.layer.l0"),
        "sideBar.background": t(m, "color.bg.surface"),
        "sideBar.foreground": t(m, "color.fg.primary"),
        "sideBarTitle.foreground": t(m, "color.layer.l1"),
        "activityBar.background": t(m, "color.bg.void"),
        "activityBar.foreground": t(m, "color.layer.l1"),
        "activityBarBadge.background": t(m, "color.layer.l2"),
        "activityBarBadge.foreground": "#ffffff",
        "statusBar.background": t(m, "color.bg.void"),
        "statusBar.foreground": t(m, "color.fg.primary"),
        "statusBarItem.remoteBackground": t(m, "color.layer.l0"),
        "titleBar.activeBackground": t(m, "color.bg.void"),
        "titleBar.activeForeground": t(m, "color.fg.primary"),
        "tab.activeBackground": t(m, "color.bg.elevated"),
        "tab.inactiveBackground": t(m, "color.bg.surface"),
        "tab.activeBorderTop": t(m, "color.layer.l1"),
        "panel.background": t(m, "color.bg.surface"),
        "panel.border": t(m, "color.border.subtle"),
        "terminal.background": t(m, "color.bg.base"),
        "terminal.foreground": t(m, "color.fg.primary"),
        "terminal.ansiBlack": t(m, "color.ansi.black"),
        "terminal.ansiRed": t(m, "color.ansi.red"),
        "terminal.ansiGreen": t(m, "color.ansi.green"),
        "terminal.ansiYellow": t(m, "color.ansi.yellow"),
        "terminal.ansiBlue": t(m, "color.ansi.blue"),
        "terminal.ansiMagenta": t(m, "color.ansi.magenta"),
        "terminal.ansiCyan": t(m, "color.ansi.cyan"),
        "terminal.ansiWhite": t(m, "color.ansi.white"),
        "terminal.ansiBrightBlack": t(m, "color.ansi.brightBlack"),
        "terminal.ansiBrightRed": t(m, "color.ansi.brightRed"),
        "terminal.ansiBrightGreen": t(m, "color.ansi.brightGreen"),
        "terminal.ansiBrightYellow": t(m, "color.ansi.brightYellow"),
        "terminal.ansiBrightBlue": t(m, "color.ansi.brightBlue"),
        "terminal.ansiBrightMagenta": t(m, "color.ansi.brightMagenta"),
        "terminal.ansiBrightCyan": t(m, "color.ansi.brightCyan"),
        "terminal.ansiBrightWhite": t(m, "color.ansi.brightWhite"),
        "button.background": t(m, "color.layer.l1"),
        "button.foreground": t(m, "color.fg.inverse"),
        "focusBorder": t(m, "color.layer.l1"),
        "list.activeSelectionBackground": t(m, "color.border.accent"),
        "list.hoverBackground": t(m, "color.bg.elevated"),
        "input.background": t(m, "color.bg.elevated"),
        "input.foreground": t(m, "color.fg.primary"),
        "input.border": t(m, "color.border.subtle"),
        "badge.background": t(m, "color.layer.l2"),
        "badge.foreground": "#ffffff",
        // Layer-specific chrome (status bar segments / peacocks-style)
        "statusBarItem.prominentBackground": t(m, "color.layer.l0"),
        "statusBarItem.prominentForeground": t(m, "color.bg.void"),
        "chart.line": t(m, "color.layer.l1"),
        "charts.green": t(m, "color.layer.l1"),
        "charts.purple": t(m, "color.layer.l2"),
        "charts.yellow": t(m, "color.layer.l0"),
      },
      // Optional: expose layer accents for extensions / custom CSS
      "fusionHero.layerAccents": {
        l0: t(m, "color.layer.l0"),
        l1: t(m, "color.layer.l1"),
        l2: t(m, "color.layer.l2"),
      },
    };
    return JSON.stringify(settings, null, 2) + "\n";
  },
});

StyleDictionary.registerFormat({
  name: "fusion/sharePointTheme",
  format: ({ dictionary }) => {
    const m = tokenIndex(dictionary);
    const theme = {
      name: `${t(m, "meta.name")} Dark`,
      isInverted: true,
      backgroundImageUri: null,
      palette: {
        themePrimary: t(m, "color.layer.l1"),
        themeLighterAlt: t(m, "color.bg.elevated"),
        themeLighter: t(m, "color.border.accent"),
        themeLight: t(m, "color.accent.teal"),
        themeTertiary: t(m, "color.accent.mint"),
        themeSecondary: t(m, "color.accent.cyan"),
        themeDarkAlt: t(m, "color.accent.mint"),
        themeDark: "#008f8f",
        themeDarker: "#006666",
        neutralLighterAlt: t(m, "color.bg.elevated"),
        neutralLighter: t(m, "color.bg.surface"),
        neutralLight: t(m, "color.border.subtle"),
        neutralQuaternaryAlt: "#2a2a38",
        neutralQuaternary: "#333344",
        neutralTertiaryAlt: t(m, "color.fg.muted"),
        neutralTertiary: t(m, "color.fg.muted"),
        neutralSecondary: "#cbd5e1",
        neutralPrimaryAlt: t(m, "color.fg.primary"),
        neutralPrimary: t(m, "color.fg.primary"),
        neutralDark: "#f1f5f9",
        black: "#ffffff",
        white: t(m, "color.bg.base"),
        primaryBackground: t(m, "color.bg.base"),
        primaryText: t(m, "color.fg.primary"),
        bodyBackground: t(m, "color.bg.base"),
        bodyText: t(m, "color.fg.primary"),
        disabledBackground: t(m, "color.bg.surface"),
        disabledText: t(m, "color.fg.muted"),
        error: t(m, "color.semantic.danger"),
        accent: t(m, "color.layer.l2"),
      },
      layerAccents: {
        l0: t(m, "color.layer.l0"),
        l1: t(m, "color.layer.l1"),
        l2: t(m, "color.layer.l2"),
      },
      _meta: {
        generatedFrom: "design-tokens/tokens.json",
        version: t(m, "meta.version"),
        sourceSha256: sourceSha256(),
        note: "Public design values only — not secrets. Import via SPO theme tooling.",
      },
    };
    return JSON.stringify(theme, null, 2) + "\n";
  },
});

StyleDictionary.registerFormat({
  name: "fusion/cssVariables",
  format: ({ dictionary }) => {
    const m = tokenIndex(dictionary);
    const lines = [
      `/* Generated by style-dictionary — do not edit by hand */`,
      `/* Source: design-tokens/tokens.json · ${t(m, "meta.name")} v${t(m, "meta.version")} */`,
      `:root {`,
      `  --fusion-bg-void: ${t(m, "color.bg.void")};`,
      `  --fusion-bg-base: ${t(m, "color.bg.base")};`,
      `  --fusion-bg-surface: ${t(m, "color.bg.surface")};`,
      `  --fusion-bg-elevated: ${t(m, "color.bg.elevated")};`,
      `  --fusion-fg-primary: ${t(m, "color.fg.primary")};`,
      `  --fusion-fg-muted: ${t(m, "color.fg.muted")};`,
      `  --fusion-accent-cyan: ${t(m, "color.accent.cyan")};`,
      `  --fusion-accent-teal: ${t(m, "color.accent.teal")};`,
      `  --fusion-layer-l0: ${t(m, "color.layer.l0")};`,
      `  --fusion-layer-l1: ${t(m, "color.layer.l1")};`,
      `  --fusion-layer-l2: ${t(m, "color.layer.l2")};`,
      `  --fusion-success: ${t(m, "color.semantic.success")};`,
      `  --fusion-warning: ${t(m, "color.semantic.warning")};`,
      `  --fusion-danger: ${t(m, "color.semantic.danger")};`,
      `  --fusion-border-subtle: ${t(m, "color.border.subtle")};`,
      `  --fusion-font-sans: ${t(m, "font.family.sans")};`,
      `  --fusion-font-mono: ${t(m, "font.family.mono")};`,
      `  --fusion-radius-md: ${t(m, "radius.md")};`,
      `}`,
      "",
    ];
    return lines.join("\n");
  },
});

StyleDictionary.registerFormat({
  name: "fusion/manifest",
  format: ({ dictionary }) => {
    const m = tokenIndex(dictionary);
    return (
      JSON.stringify(
        {
          name: t(m, "meta.name"),
          version: t(m, "meta.version"),
          source: "design-tokens/tokens.json",
          sourceSha256: sourceSha256(),
          generatedAt: new Date().toISOString(),
          layerAccents: {
            l0: t(m, "color.layer.l0"),
            l1: t(m, "color.layer.l1"),
            l2: t(m, "color.layer.l2"),
          },
          targets: [
            "terminal/windows-terminal.colorScheme.json",
            "vscode/colorCustomizations.json",
            "sharepoint/theme.json",
            "css/tokens.css",
          ],
          policy: {
            sourceOfTruth: "git",
            secretVault: false,
            runtimeSelfMutation: false,
            refineBy: "edit tokens.json + style-dictionary build",
          },
        },
        null,
        2
      ) + "\n"
    );
  },
});

// ── Platforms ───────────────────────────────────────────────────────────────

/** @type {import('style-dictionary').Config} */
export default {
  source: [join(__dirname, "tokens.json")],
  platforms: {
    terminal: {
      transforms: ["attribute/cti", "name/kebab", "color/hex"],
      buildPath: join(__dirname, "dist") + "/",
      files: [
        {
          destination: "terminal/windows-terminal.colorScheme.json",
          format: "fusion/windowsTerminal",
        },
      ],
    },
    vscode: {
      transforms: ["attribute/cti", "name/kebab", "color/hex"],
      buildPath: join(__dirname, "dist") + "/",
      files: [
        {
          destination: "vscode/colorCustomizations.json",
          format: "fusion/vscodeSettings",
        },
      ],
    },
    sharepoint: {
      transforms: ["attribute/cti", "name/kebab", "color/hex"],
      buildPath: join(__dirname, "dist") + "/",
      files: [
        {
          destination: "sharepoint/theme.json",
          format: "fusion/sharePointTheme",
        },
      ],
    },
    css: {
      transforms: ["attribute/cti", "name/kebab", "color/hex"],
      buildPath: join(__dirname, "dist") + "/",
      files: [
        {
          destination: "css/tokens.css",
          format: "fusion/cssVariables",
        },
        {
          destination: "manifest.json",
          format: "fusion/manifest",
        },
      ],
    },
  },
};
