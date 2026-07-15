# Control Instances — multi-model, max accuracy

**Config:** `control_instances.yaml`  
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

## Instances

Grok · Claude · GPT · Gemini · Groq · OpenRouter · Ollama · Internal  

Only configured/live providers execute (internal always).

## CLI

```powershell
python -m fusion_hero_os.core.control_instances --status
python -m fusion_hero_os.core.control_instances --prompt "Verify deploy=private push=public merge=both"
python -m fusion_hero_os.core.control_instances --providers grok,claude,internal
```

## API

- `GET /api/control/instances/status`
- `POST /api/control/instances/run` `{"prompt":"...", "providers":["grok","claude"]}`

## Output

- Full: `~/.fusion/control/last_control_report.json`
- Summary: `docs/control/last_control_report.summary.json`
