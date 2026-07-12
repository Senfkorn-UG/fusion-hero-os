# -*- coding: utf-8 -*-
"""Gemeinsame Test-Helfer.

Mehrere Testdateien schieben unterschiedliche Verzeichnisse an sys.path[0]
(Repo-Root, 03_Code/core, 03_Code/Dashboard). pytest fuehrt beim Einsammeln
alle Modul-Level-Inserts VOR dem ersten Testlauf aus - je nach Reihenfolge
trifft ein spaeteres "import app" deshalb das falsche app.py (Repo-Root-
NiceGUI statt Dashboard-FastAPI). import_dashboard_app() loest das
deterministisch auf: Dashboard-Pfad nach vorn + falsch gecachtes Modul raus.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = REPO_ROOT / "03_Code" / "Dashboard"
_DASHBOARD_APP_FILE = str(DASHBOARD_DIR / "app.py")


def import_dashboard_app():
    """Importiert 03_Code/Dashboard/app.py garantiert als Modul 'app'."""
    if str(DASHBOARD_DIR) in sys.path:
        sys.path.remove(str(DASHBOARD_DIR))
    sys.path.insert(0, str(DASHBOARD_DIR))
    cached = sys.modules.get("app")
    if cached is not None and getattr(cached, "__file__", None) != _DASHBOARD_APP_FILE:
        del sys.modules["app"]
    return importlib.import_module("app")
