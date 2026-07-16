# -*- coding: utf-8 -*-
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_run_x402_stack_script():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_x402_stack.py"), "--json-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, r.stderr[:500]
    data = json.loads(r.stdout)
    assert data.get("ok") is True
    assert data["sandbox_audit"]["ok"] is True
    assert data["attack_simulation"]["succeeded_insecure"] is True
    assert data["attack_simulation"]["blocked_secure"] is True
    assert "95guknow" in data.get("github", "")
    assert Path(data["master_paths"][0]).is_file()
