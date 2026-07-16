# Control Instances — multi-model, max accuracy

**Config:** `control_instances.yaml` (v1.2)  
**Code:** `fusion_hero_os/core/control_instances.py`  
**Policy:** each control instance forces **highest accuracy** (`temperature=0`, verifier JSON, structured scores)

## Principle

Independent **control instances** run on **different models**. No single model is sole truth.  
Each instance is forced to max accuracy; consensus/disagreement is recorded.

| Force | Value |
|-------|--------|
| temperature | **0.0** |
| top_p | **1.0** |
| role | verifier |
| output | JSON score schema |
| internal | always-on honesty stub |

## Multi-slot pattern (analog)

Same `provider` + different `model_override` (or `model_env`) = independent control slots.  
Gemini pioneered the multi-slot layout; Grok / Claude / GPT / Groq / OpenRouter-free / Ollama follow the same pattern.

## Instances

| Group | Slot IDs |
|-------|----------|
| **Gemini** | `control_gemini`, `control_gemini_flash`, `control_gemini_flash_lite`, `control_gemini_15_pro`, `control_gemini_15_flash`, `control_gemini_25_flash`, `control_gemini_25_pro` |
| **Grok** | `control_grok`, `control_grok_2`, `control_grok_3` |
| **Claude** | `control_claude`, `control_claude_sonnet`, `control_claude_haiku`, `control_claude_opus` |
| **GPT** | `control_gpt`, `control_gpt_4o`, `control_gpt_4o_mini`, `control_gpt_4_1` |
| **Groq** | `control_groq`, `control_groq_llama70`, `control_groq_mixtral` |
| **OpenRouter** | `control_openrouter`, `control_openrouter_free`, `control_or_free_gemma`, `control_or_free_llama`, `control_or_free_qwen` |
| **Further** | `control_huggingface`, `control_nvidia`, `control_github_models`, `control_cloudflare_ai` |
| **Local** | `control_ollama`, `control_ollama_llama32`, `control_ollama_mistral` |
| **Always** | `control_internal` |

All share **accuracy: max** (`temperature=0`, verifier JSON).  
Only configured/live providers execute (internal always).  
Filter by `provider` **or** instance `id` (e.g. `control_gemini_flash`).

## Secrets

Operator keys via dotenv (no values logged):

- `.env`, `.env.local`, `~/.fusion/secrets/push.env`
- Gemini: `GOOGLE_API_KEY` or `GEMINI_API_KEY`
- Others: `XAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, …

## CLI

```powershell
python -m fusion_hero_os.core.control_instances --status
python -m fusion_hero_os.core.control_instances --prompt "Verify deploy=private push=public merge=both"
python -m fusion_hero_os.core.control_instances --providers gemini,control_gemini_25_pro,grok,internal
```

## API

- `GET /api/control/instances/status` — includes `multi_slots`, `gemini_control_slots`
- `POST /api/control/instances/run` `{"prompt":"...", "providers":["gemini","internal"]}`

## Output

- Full: `~/.fusion/control/last_control_report.json`
- Summary: `docs/control/last_control_report.summary.json`
