# Pseudo-Inhouse AI — Local Facade (no freemium)

**Platform:** Fusion Hero OS v10.0.0  
**Policy:** `pseudo_inhouse_only` · **`freemium: false`**  
**Placement:** L1 Mainframe (facade) · external providers = membranes only  
**Config:** `llm_free_services.yaml`  
**Code:** `fusion_hero_os/core/pseudo_inhouse_ai.py` · `03_Code/Dashboard/pseudo_inhouse_routes.py`  
**Creative sibling:** [PSEUDO_INHOUSE_CREATIVE.md](PSEUDO_INHOUSE_CREATIVE.md)

## Principle

**All clients talk only to the local AI server** (`:8000`). There is **no freemium product surface**.  
Optional backends (Groq, OpenRouter, Gemini, Ollama, HF, Cloudflare, NVIDIA, GitHub Models) are **membranes**, not SKUs and not source-of-truth.

```
Client / MCP / IDE
       │
       ▼
  http://127.0.0.1:8000/v1/chat/completions   ← looks in-house
       │
       ▼
  pseudo_inhouse_ai.complete()  failover chain
       │
       ├── ollama (true local)
       ├── openrouter_free
       ├── groq
       ├── gemini
       ├── huggingface
       ├── cloudflare_ai
       ├── nvidia
       ├── github_models
       └── internal (always)
```

## Endpoints

| Path | Role |
|------|------|
| `GET /api/ai/inhouse/status` | Live provider matrix |
| `GET /api/ai/inhouse/catalog` | YAML catalog |
| `POST /api/ai/inhouse/chat` | `{message, provider?, system?}` |
| `GET /v1/models` | OpenAI model list |
| `POST /v1/chat/completions` | OpenAI-compatible chat |

## Env keys (optional free tiers)

| Service | Env |
|---------|-----|
| Ollama | `OLLAMA_HOST` (default localhost) |
| OpenRouter free | `OPENROUTER_API_KEY`, `FUSION_OPENROUTER_FREE_MODEL` |
| Groq | `GROQ_API_KEY` |
| Gemini | `GOOGLE_API_KEY` / `GEMINI_API_KEY` |
| Hugging Face | `HF_TOKEN` |
| Cloudflare | `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` |
| NVIDIA NIM | `NVIDIA_API_KEY` |
| GitHub Models | `GITHUB_TOKEN` |

## Client example (OpenAI SDK)

```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="fusion-local")
r = client.chat.completions.create(
    model="fusion-inhouse/auto",
    messages=[{"role": "user", "content": "Hallo vom Pseudo-Inhouse Hub"}],
)
print(r.choices[0].message.content)
```

## Honesty

- Free tiers have **rate limits** and change over time.  
- Not unlimited compute.  
- **Never** store MasterSeed or personal clinical data as SaaS source-of-truth.  
- Internal fallback is a **stub**, not a frontier model.

## CLI

```powershell
python -m fusion_hero_os.core.pseudo_inhouse_ai
```
