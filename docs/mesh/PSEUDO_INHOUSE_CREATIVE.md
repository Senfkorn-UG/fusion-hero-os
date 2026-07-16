# Pseudo-Inhouse Creative — Image · Video · PDF · Graphics

**Platform:** Fusion Hero OS v10.0.0  
**Policy:** `pseudo_inhouse_only` · **`freemium: false`**  
**Config:** `creative_inhouse_services.yaml`  
**Code:** `fusion_hero_os/core/pseudo_inhouse_creative.py`

## Principle

Creative work is **only** exposed through the Mainframe facade.  
There is **no freemium product tier**. Local engines are primary; any external API is a membrane, never a SKU.

```
Client
  → POST /api/creative/inhouse/create
  → local engines (Pillow canvas, PDF, SVG, GIF/ffmpeg)
  → ~/.fusion/creative/inhouse/*
```

## Modalities

| Modality | Engine | Output |
|----------|--------|--------|
| **image** | pillow_canvas | PNG poster/generative field |
| **graphics** | canvas + SVG | PNG + SVG |
| **pdf** | pillow_pdf | multi-page PDF |
| **video** | gif_animator (+ ffmpeg if present) | GIF / MP4 |

## Endpoints

| Path | Role |
|------|------|
| `GET /api/creative/inhouse/status` | engines live matrix |
| `GET /api/creative/inhouse/catalog` | YAML catalog |
| `POST /api/creative/inhouse/create` | `{modality, prompt, …}` |
| `POST /api/creative/inhouse/image` | image only |
| `POST /api/creative/inhouse/pdf` | PDF only |
| `POST /api/creative/inhouse/video` | video/GIF |
| `POST /api/creative/inhouse/graphics` | graphics+SVG |
| `GET /api/creative/inhouse/artifacts` | recent files |
| `POST /v1/images/generations` | OpenAI-compatible images |

## Example

```powershell
# after dashboard up
curl -s -X POST http://127.0.0.1:8000/api/creative/inhouse/create `
  -H "Content-Type: application/json" `
  -d "{\"modality\":\"pdf\",\"prompt\":\"Autopoiesis abstract\",\"pages\":3}"
```

```python
from fusion_hero_os.core.pseudo_inhouse_creative import create
r = create("image", "Heroic cyberpunk campfire")
print(r.path)
```

## Related

- LLM pseudo-inhouse: `docs/mesh/PSEUDO_INHOUSE_AI.md`  
- Policy: no freemium — same for text and creative.
