# P0 — Cloud-LLM-Keys (Control-Panel live)

Ohne Keys bleiben 34 Control-Slots größtenteils Attrappe (nur Ollama + Internal).

## Datei

`C:\Users\Admin\fusion-hero-os\.env` (nicht committen)

## Mindestens setzen (Werte eintragen, keine Leerzeichen)

```
GOOGLE_API_KEY=...          # oder GEMINI_API_KEY=
XAI_API_KEY=...             # oder GROK_API_KEY=
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
OPENROUTER_API_KEY=...      # deckt openrouter + openrouter_free
GROQ_API_KEY=...
```

Optional: `HUGGINGFACE_API_KEY`, `NVIDIA_API_KEY`, `GITHUB_TOKEN`, Cloudflare.

## Verify

```powershell
cd C:\Users\Admin\fusion-hero-os
python -m fusion_hero_os.core.control_instances --status
# Erwartung: keys_set_count > 0, cloud_live true, p0_blocker null
python -m fusion_hero_os.core.control_instances --providers gemini,internal --prompt "2+2?"
```

**Policy:** Keys nie in Git, nie in Public Snapshots.
