# Fusion Hero OS - Deployment Guide

> **Stand:** v10.0.0 · 2026-07-15 · Operativer Kanon + Dashboard + VR + Dependency Atlas  
> **Plattform-Version:** Root-`VERSION` / Tag `v10.0.0` (siehe `BEST_VERSION.md`)  
> **Dissertation-as-OS:** Deployed runtime *is* the dissertation in operation; text under `docs/dissertation/` is one expression. See `docs/dissertation/ONTOLOGIE_DISSERTATION_IST_DAS_OS.md`.

## Quick Start

### Prerequisites
```bash
pip install fastapi uvicorn psutil
```

### Single Process: Dashboard GUI + API (Port 8000)

**Empfohlen: Fast-Boot.** Der volle Auto-Load (GPU-Tuning, Provider-Probing,
Modul-Registry) läuft synchron im Startup-Event und kann den Serverstart
minutenlang blockieren ("Waiting for application startup", Befund 2026-07-11).
Mit `FUSION_AUTO_LOAD=0` ist die Bridge-UI sofort verfügbar; Module lassen
sich danach über die API nachladen.

```bash
cd 03_Code/Dashboard
FUSION_AUTO_LOAD=0 python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

PowerShell:
```powershell
$env:FUSION_AUTO_LOAD = "0"; python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Or on Windows (voller Auto-Load):
```bat
run_backend.bat
```

### Auto-Load (voller Boot, kann lange dauern)
```powershell
powershell -File start_all.ps1
```

### Access
- **Standard GUI**: http://127.0.0.1:8000
- **API Health**: http://127.0.0.1:8000/api/health
- **API Docs**: http://127.0.0.1:8000/docs
- **WebSocket**: ws://127.0.0.1:8000/ws
- **VR 360° Viewer**: http://127.0.0.1:8000/vr/viewer (Szenen dynamisch aus `03_VR_Assets/`; `/api/vr/assets`, `/api/vr/roadmap`, `/api/vr/status`)
- **Highest Layer**: http://127.0.0.1:8000/highest-layer · `/highest-layer-vr`
- **Dependency Atlas**: http://127.0.0.1:8000/architecture (Mermaid-Plot) · `/api/architecture/atlas` (JSON)

### Optional: NiceGUI Legacy (Port 8080)
Only if needed — not the default GUI:
```powershell
powershell -File start_all.ps1 -NiceGUI
```
Or manually: `run_workspace.bat` → http://127.0.0.1:8080

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│     Standard GUI (FastAPI + HTML, Port 8000)            │
│  - templates/index.html (Dashboard)                     │
│  - WebSocket /ws (Live Events)                          │
│  - REST API /api/*                                      │
└────────────────────┬────────────────────────────────────┘
                     │ Python imports
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Mainframe Core (in-process)                   │
│  - Heroic Orchestration                                 │
│  - Hyperthreading Control                               │
│  - Agent Supervisor                                     │
│  - QUBO / AutoLoad                                      │
└─────────────────────────────────────────────────────────┘
```

---

## Deployment Status

| Component | Status | Location | Port |
|-----------|--------|----------|------|
| Standard GUI | Ready | `03_Code/Dashboard/app.py` | 8000 |
| NiceGUI Legacy | Optional | `03_Code/Dashboard/workspace.py` | 8080 |
| Reference REST | Dev/Ref | `03_Code/reference/rest_api_server.py` | — |

---

## API Example Usage

### Health Check
```bash
curl http://127.0.0.1:8000/api/health
```

### GUI Status
```bash
curl http://127.0.0.1:8000/api/gui/status
```

### Enable Hyperthreading
```bash
curl -X POST http://127.0.0.1:8000/api/hyperthreading \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

---

## Troubleshooting

### Port 8000 already in use
```bat
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### NiceGUI conflicts with other apps on 8080
Do not start NiceGUI unless needed. Default is port 8000 only.