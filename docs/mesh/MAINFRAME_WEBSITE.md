# Mainframe Website · Dauer-VR · IDE · Worktree

**Status:** operational (Dashboard Port **8000**)  
**Platform:** Fusion Hero OS v10.0.0

## Surfaces

| URL | Funktion |
|-----|----------|
| http://127.0.0.1:8000/mainframe | Hub / Portal |
| http://127.0.0.1:8000/mainframe/vr | **Dauer-VR** (A-Frame always-on + HUD) |
| http://127.0.0.1:8000/mainframe/ide | Browser-IDE (Tree + Preview + Live-APIs) |
| http://127.0.0.1:8000/mainframe/worktree | Komplettes Repo hyperlinked |
| http://127.0.0.1:8000/mainframe/ops | Ops Console |
| http://127.0.0.1:8000/vr/persistent | Alias → Dauer-VR |

## API

- `GET /api/mainframe/site/status`
- `GET /api/mainframe/worktree/list?path=`
- `GET /api/mainframe/worktree/git`
- `GET /api/mainframe/worktree/content?path=`
- `GET /api/mainframe/worktree/raw?path=`
- `GET /api/mainframe/ide/status`

## Start

```powershell
$env:FUSION_AUTO_LOAD = "0"
$env:FUSION_REPO_ROOT = "C:\Users\Admin\fusion-hero-os"
cd C:\Users\Admin\fusion-hero-os\03_Code\Dashboard
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

## Security

Worktree-View nur unter `FUSION_REPO_ROOT` (Default: monorepo). Path-Traversal (`..`) wird abgewiesen.

## Code

- `03_Code/Dashboard/mainframe_site_routes.py`
- Templates: `mainframe_site.html`, `mainframe_vr_persistent.html`, `mainframe_ide.html`, `mainframe_worktree.html`
- Static: `mainframe_site.js`, `mainframe_site.css`
