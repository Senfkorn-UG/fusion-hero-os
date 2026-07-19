# Graph API for all connectors

**Platform:** Fusion Hero OS v12.0.0  
**Policy:** dry-run default · live only with tokens + `FUSION_GRAPH_LIVE=1`

## Hub

| Component | Path |
|-----------|------|
| Config | `graph_api_connectors.yaml` |
| Python | `fusion_hero_os/connectors/graph_api.py` |
| CLI | `python scripts/graph_api_connectors.py` |
| HTTP | `GET /api/graph/connectors` |
| IG publish | `POST /api/graph/instagram/publish` |

## Connectors (graph-style)

instagram · facebook · github_graphql · github_rest · x_api · gmail · drive · vercel · notion · canva

## Live Instagram

```env
INSTAGRAM_ACCESS_TOKEN=...
IG_USER_ID=...
FUSION_GRAPH_LIVE=1
```

```powershell
python scripts/graph_api_connectors.py --instagram-publish `
  --image-url https://raw.githubusercontent.com/95guknow/fusion-hero-os/main/docs/security/media/IG_meister_hasch.png `
  --caption-file docs/security/media/meister_hasch_v12/IG_CAPTION.txt
```

Without tokens: returns structured **DRY-RUN** plan (`would_execute=false`).

## Security

- No network on import
- No write to X without `allow_write`
- Meta Graph publish requires explicit live flag
- Never log token values
