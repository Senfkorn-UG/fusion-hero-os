# Fusion-HERO-OS

Kilo-Konfigurations-Repo: eine virtuelle Identität (H.E.R.O.) plus ein Satz
spezialisierter Engineering-Agents, betrieben über [Kilo](https://app.kilo.ai)
(`kilo.jsonc` + `agents/*.md`).

Dieses Dokument ist die **korrelierte Systemanalyse**: Top-down (Architektur,
Schichten, Config-Schema) gegen Bottom-up (Datei-für-Datei-Befunde) gestellt.

---

## Top-down: Architektur

```
┌──────────────────────────────────────────────────────────┐
│  KERNEL          kilo.jsonc                              │
│  Permissions · Compaction · Experimental · Commit-Prompt │
├──────────────────────────────────────────────────────────┤
│  IDENTITÄT       hero-core.md        (Stimme & Format)   │
│                  hero-philosophy.md  (Denkschule)        │
├──────────────────────────────────────────────────────────┤
│  ENGINEERING     architect ─────► plant                  │
│                  code-simplifier ► implementiert/refact. │
│                  code-reviewer ──► prüft Qualität        │
│                  code-skeptic ───► erzwingt Beweise      │
│                  test-engineer ──► testet                │
│                  frontend-specialist · docs-specialist   │
│                  data (Notebook-first)                   │
├──────────────────────────────────────────────────────────┤
│  PROMPT-BIBLIOTHEK   mainframe-laden.prompt.md           │
└──────────────────────────────────────────────────────────┘
```

Die Schichten korrelieren so: Die **Identitätsschicht** definiert *wie*
gesprochen und gedacht wird (H.E.R.O.-Stimme, Affirmative Aporia). Die
**Engineering-Schicht** definiert *was* getan wird — als Pipeline
Planen → Bauen → Prüfen → Bezweifeln → Testen. Der **Kernel** setzt die
Leitplanken (Rechte, Kontext-Haushalt) für beide.

## Agent-Matrix (Bottom-up-Inventar)

| Agent | Rolle | edit | bash | mcp¹ | Besonderheit |
|---|---|---|---|---|---|
| `hero-core` | Identität, Short-Content | nur Text/Config-Dateien | allow | deny | 1–2 Meme-Regel, duale Mem-Schicht |
| `hero-philosophy` | Denkschule | nur Text/Config-Dateien | allow | deny | 4 Gesetze, 4 Werkzeuge |
| `architect` | Planung | nur Plan-Dateien | deny | deny | schreibt nach `.kilo/plans/` |
| `code-simplifier` | Refactoring | allow | allow | allow | einziger Voll-Schreibzugriff |
| `code-reviewer` | Review | deny | allow | deny | read-only per Design |
| `code-skeptic` | Qualitäts-Gatekeeper | nur Markdown | allow | allow | „Show me the logs" |
| `test-engineer` | Tests | nur `*.test.*`/`*.spec.*` | allow | deny | |
| `frontend-specialist` | UI | nur TS/JS/CSS | allow | deny | |
| `docs-specialist` | Doku | nur Doku-Formate | allow | deny | |
| `data` | Datenanalyse | (Default) | (Default) | (Default) | Notebook-first, kein Permission-Block |

¹ `mcp` und `plan_exit` stehen nicht im aktuell publizierten Config-Schema —
die Keys wurden bewusst belassen, da sie ggf. von der App ausgewertet werden.

`mainframe-laden.prompt.md` ist kein Agent, sondern ein wiederverwendbarer
Workspace-Prompt (kein Frontmatter, keine Permissions).

## Korrelation: Wo Top-down und Bottom-up kollidierten (behobene Befunde)

1. **Kontext-Limits (Kernel):** `compaction.threshold_percent` existiert im
   Kilo-Schema nicht — der einzige Limit-Schutz des Systems war wirkungslos.
   Ersetzt durch die gültigen Keys `auto` (frühzeitig kompaktieren),
   `prune` (alte Tool-Ausgaben verwerfen) und `reserved` (Puffer, damit die
   Kompaktierung nicht selbst am Limit scheitert).
2. **Ungültiger Permission-Key:** `todoread` existiert im Schema nicht (nur
   `todowrite`) — entfernt.
3. **Permission-Reihenfolge:** Die HERO-Dateien listeten `"*": deny` als
   *letzten* Eintrag der edit-Map, alle anderen Agents als *ersten*. Auf das
   Mehrheitsmuster normalisiert (deny zuerst, Allows danach), damit das
   Verhalten nicht von der Auswertungsreihenfolge abhängt.
4. **Fremde Projektregeln:** `code-skeptic` enthielt hartkodierte Regeln aus
   einem anderen Projekt („actor system", TypeScript-spezifisch). Auf
   generische, repo-eigene Regelquellen umgestellt.
5. **Textdefekte (Identitätsschicht):** Mojibake `Kein坊` → „Kein Spam";
   „Derritt der Antagonismen" → „Der Riss der Antagonismen"; „Gesetz der
   eternen Wiederkehr" → „ewigen Wiederkehr" (konsistent mit dem Rest der
   Datei); mehrere Grammatik-/Groß-/Kleinschreibungsfehler.
6. **Typos (Engineering-Schicht):** `code-simplifier` („Never assume-verify",
   fehlender Gedankenstrich im Schlusssatz) korrigiert.

## Offene Punkte (bewusst nicht geändert)

- **`keploy.keployio-2.1.7-win32-x64.vsix` (10,7 MB):** Ein VS-Code-
  Extension-Binary gehört nicht in ein Config-Repo und bläht jeden Clone auf.
  Empfehlung: löschen und die Extension über den Marketplace beziehen.
  Nicht entfernt, da möglicherweise absichtlich hinterlegt.
- **`indexing`-Block und `experimental.speech_to_text_model`:** Stehen nicht
  im aktuell publizierten Schema, könnten aber von der App noch gelesen
  werden. Mit Kommentar markiert statt entfernt.
- **`data`-Agent ohne Permission-Block:** Erbt die (großzügigen) globalen
  Rechte aus `kilo.jsonc`. Falls unerwünscht, analog zu den anderen Agents
  einschränken.

## Limit-Probleme vermeiden (Betriebsleitfaden)

- `compaction.auto` + `prune` sind jetzt aktiv — alte Tool-Ausgaben werden
  automatisch aus dem Kontext entfernt, bevor das Fenster überläuft.
- `terminal_command_display: "collapsed"` beibehalten; `code_edit_display:
  "expanded"` kostet nur UI, keine Tokens.
- Große Binärdateien (siehe `.vsix`) nie in den Kontext ziehen lassen.
- Lange Sessions thematisch schneiden; für Recherche-Aufgaben Subagents
  (`task`-Permission ist global `allow`) statt der Hauptsession nutzen.
- Bei hartnäckigen Limits: `compaction.tail_turns` (Default 2) klein halten
  und `preserve_recent_tokens` setzen, statt den Verlauf manuell zu kürzen.
