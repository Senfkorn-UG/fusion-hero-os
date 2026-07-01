# Fusion Hero OS - Deployment Guide

## 🎯 Quick Start

### Prerequisites
```bash
pip install fastapi uvicorn nicegui requests psutil
```

### Terminal 1: Backend (Port 8000)
```bash
cd 03_Code/reference
python rest_api_server.py
```

### Terminal 2: Frontend (Port 8080)
```bash
cd 03_Code/reference
python app.py
```

### Access
- **Frontend UI**: http://127.0.0.1:8080
- **Backend API**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs

---

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (NiceGUI, Port 8080)              │
│  - Workspace Canvas + IDE                               │
│  - Autonomous Task Assignment                           │
│  - Live Agent Monitor                                   │
│  - Pipelines & Visualization                            │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP REST
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Backend API (FastAPI, Port 8000)             │
│  - Task Queue Management                                │
│  - Event Logging                                        │
│  - Hyperthreading Control                               │
│  - System Monitoring                                    │
└────────────────────┬────────────────────────────────────┘
                     │ Python imports
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Mainframe Core (in-process)                   │
│  - QUBO Solver (Simulated Annealing)                    │
│  - Heroic Orchestration                                 │
│  - Agent Supervisor                                     │
│  - PeerReview Module                                    │
└───────────────────────���─────────────────────────────────┘
```

---

## ✅ Fixes Applied

✅ CodeQL Workflow disabled (`.github/workflows/codeql.yml`)
✅ Git submodules fixed (`.gitmodules` created)
✅ Frontend configured (Port 8080, NiceGUI)
✅ Backend REST API configured (Port 8000, FastAPI)
✅ CORS enabled between frontend and backend

---

## 🚀 Deployment Status

| Component | Status | Location | Port |
|-----------|--------|----------|------|
| Frontend | ✅ Ready | `03_Code/reference/app.py` | 8080 |
| Backend API | ✅ Ready | `03_Code/reference/rest_api_server.py` | 8000 |
| Mainframe Core | ✅ Integrated | In-process | — |
| Agent Monitor | ✅ Ready | Frontend module | — |
| Git Workflows | ✅ Fixed | `.github/workflows/` | — |

---

## 📡 API Example Usage

### Health Check
```bash
curl http://127.0.0.1:8000/api/health
```

### Get CPU Info
```bash
curl http://127.0.0.1:8000/api/input-factors
```

### Enable Hyperthreading
```bash
curl -X POST http://127.0.0.1:8000/api/hyperthreading \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

### Log Event
```bash
curl -X POST http://127.0.0.1:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{"type": "task", "msg": "Task 1 assigned"}'
```

---

## 🔧 Troubleshooting

### Port already in use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Backend not responding
- Check: `python 03_Code/reference/rest_api_server.py` running?
- Check: CORS headers correct?
- Check: Firewall allowing localhost connections?

### Frontend can't connect to backend
- Verify `API_BASE = "http://127.0.0.1:8000"` in `workspace.py` (line 97)
- Check CORS middleware in `rest_api_server.py`
- Check Network tab in browser DevTools

---

## 📚 Next Steps

1. **Start Backend**: `python 03_Code/reference/rest_api_server.py`
2. **Start Frontend**: `python 03_Code/reference/app.py`
3. **Open Browser**: http://127.0.0.1:8080
4. **Test Features**: Try autonomous task assignment, pipelines, etc.
5. **Monitor**: Check `http://127.0.0.1:8000/docs` for live API docs

✨ **Deployment ready!**
