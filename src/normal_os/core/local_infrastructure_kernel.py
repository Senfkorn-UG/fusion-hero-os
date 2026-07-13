# -*- coding: utf-8 -*-
"""
local_infrastructure_kernel.py — Lokale Kernlogik (Probing / Schwellen / Eskalation).

Windows-Mainframe-Seite des Vertrags ``workstation/contracts/local_infrastructure_kernel.v1.json``.
Die API/GUI-Schicht importiert dieses Modul oder liest ``~/.fusion/local-infrastructure-kernel/status.json``.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONTRACT_VERSION = "1.0"
MODULE_ID = "local_infrastructure_kernel"

_LEVEL_RANK = {"ok": 0, "warn": 1, "alert": 2, "critical": 3}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _state_dir() -> Path:
    custom = os.getenv("FUSION_LOCAL_KERNEL_STATE")
    if custom:
        return Path(custom)
    return Path.home() / ".fusion" / "local-infrastructure-kernel"


def _status_file() -> Path:
    return _state_dir() / "status.json"


def _thresholds_file() -> Path:
    custom = os.getenv("FUSION_LOCAL_KERNEL_THRESHOLDS")
    if custom:
        return Path(custom)
    return _repo_root() / "workstation" / "local_infrastructure_thresholds.json"


def _paths_config() -> Dict[str, Any]:
    paths_file = _repo_root() / "workstation" / "paths.json"
    if not paths_file.exists():
        return {}
    try:
        return json.loads(paths_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _service_endpoints() -> Dict[str, str]:
    endpoints = (_paths_config().get("endpoints") or {})
    return {
        "service_dashboard": endpoints.get("fusionDashboard", "http://127.0.0.1:8000"),
        "service_hero_docs": endpoints.get("heroDocs", "http://127.0.0.1:8088"),
        "service_bridge": endpoints.get("normalOSBridge", "http://127.0.0.1:8765"),
    }


def is_available() -> bool:
    """Lokales Modul ist verfügbar (Import erfolgreich)."""
    return True


def is_enabled() -> bool:
    return os.getenv("FUSION_LOCAL_KERNEL", "1").lower() in ("1", "true", "yes", "on")


def load_thresholds() -> Dict[str, Any]:
    path = _thresholds_file()
    if not path.exists():
        return {"metrics": {}, "escalation_actions": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"metrics": {}, "escalation_actions": {}, "error": str(exc)}


def status() -> Dict[str, Any]:
    """Statischer Modulstatus ohne aktive Probes."""
    cached = read_cached_state()
    return {
        "available": True,
        "module": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "enabled": is_enabled(),
        "platform": platform.system(),
        "state_file": str(_status_file()),
        "thresholds_file": str(_thresholds_file()),
        "last_cycle_at": (cached or {}).get("cycle_at"),
        "last_escalation": (cached or {}).get("escalation", {}).get("level"),
        "probe_targets": list(_service_endpoints().keys()) + ["ram_util_pct", "disk_c_util_pct", "tailscale_online"],
    }


def _probe_http(base_url: str, path: str, timeout: float) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    started = time.perf_counter()
    result: Dict[str, Any] = {
        "url": url,
        "online": False,
        "http_status": None,
        "latency_ms": None,
        "error": None,
    }
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            result["http_status"] = resp.status
            result["online"] = resp.status == 200
    except urllib.error.HTTPError as exc:
        result["http_status"] = exc.code
        result["online"] = exc.code < 500
        result["error"] = str(exc)
    except Exception as exc:
        result["error"] = str(exc)
    result["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
    return result


def _probe_ram() -> Dict[str, Any]:
    try:
        import psutil

        mem = psutil.virtual_memory()
        return {
            "ram_util_pct": mem.percent,
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
        }
    except Exception as exc:
        return {"ram_util_pct": None, "error": str(exc)}


def _probe_disk_c() -> Dict[str, Any]:
    try:
        import psutil

        root = "C:\\" if platform.system() == "Windows" else "/"
        usage = psutil.disk_usage(root)
        util = round(usage.used / usage.total * 100, 1) if usage.total else None
        return {
            "disk_c_util_pct": util,
            "free_gb": round(usage.free / (1024 ** 3), 2),
            "total_gb": round(usage.total / (1024 ** 3), 2),
        }
    except Exception as exc:
        return {"disk_c_util_pct": None, "error": str(exc)}


def _probe_tailscale(timeout: float = 8.0) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            return {"tailscale_online": False, "error": proc.stderr.strip() or "tailscale unavailable"}
        data = json.loads(proc.stdout)
        self_data = data.get("Self", {})
        return {
            "tailscale_online": bool(self_data.get("Online", False)),
            "hostname": self_data.get("HostName"),
            "tailnet": data.get("MagicDNSSuffix"),
        }
    except FileNotFoundError:
        return {"tailscale_online": False, "error": "tailscale binary not found"}
    except Exception as exc:
        return {"tailscale_online": False, "error": str(exc)}


def probe(timeout: float = 4.0) -> Dict[str, Any]:
    """Aktive Health-Probes gegen lokale Dienste und Substrat."""
    if not is_enabled():
        return {
            "available": True,
            "module": MODULE_ID,
            "contract_version": CONTRACT_VERSION,
            "probed_at": time.time(),
            "skipped": True,
            "reason": "disabled",
        }

    services: Dict[str, Any] = {}
    for name, base in _service_endpoints().items():
        path = "/api/metrics" if name == "service_dashboard" else "/"
        services[name] = _probe_http(base, path, timeout)

    payload: Dict[str, Any] = {
        "available": True,
        "module": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "probed_at": time.time(),
        "substrate": {
            **_probe_ram(),
            **_probe_disk_c(),
            **_probe_tailscale(min(timeout, 8.0)),
        },
        "services": services,
    }
    return payload


def _metric_level(metric: str, value: Any, rules: Dict[str, Any]) -> str:
    if value is None:
        return "warn"

    if metric.startswith("service_"):
        offline_level = str(rules.get("offline_is", "warn"))
        return "ok" if value else offline_level

    if metric == "tailscale_online":
        false_level = str(rules.get("false_is", "warn"))
        return "ok" if value else false_level

    try:
        num = float(value)
    except (TypeError, ValueError):
        return "warn"

    if num >= float(rules.get("critical", 101)):
        return "critical"
    if num >= float(rules.get("alert", 101)):
        return "alert"
    if num >= float(rules.get("warn", 101)):
        return "warn"
    return "ok"


def evaluate(probe_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Wendet Schwellenwerte an und bestimmt Eskalationsstufe + Aktionen."""
    data = probe_result if probe_result is not None else probe()
    thresholds = load_thresholds()
    rules = thresholds.get("metrics") or {}
    actions_map = thresholds.get("escalation_actions") or {}

    findings: List[Dict[str, Any]] = []
    overall = "ok"

    substrate = data.get("substrate") or {}
    for key in ("ram_util_pct", "disk_c_util_pct", "tailscale_online"):
        metric_rules = rules.get(key) or {}
        if key == "tailscale_online":
            value = substrate.get("tailscale_online")
        else:
            value = substrate.get(key)
        level = _metric_level(key, value, metric_rules)
        findings.append({"metric": key, "value": value, "level": level})
        if _LEVEL_RANK[level] > _LEVEL_RANK[overall]:
            overall = level

    for name, svc in (data.get("services") or {}).items():
        metric_rules = rules.get(name) or {}
        online = bool((svc or {}).get("online"))
        level = _metric_level(name, online, metric_rules)
        findings.append({
            "metric": name,
            "value": online,
            "level": level,
            "latency_ms": (svc or {}).get("latency_ms"),
        })
        if _LEVEL_RANK[level] > _LEVEL_RANK[overall]:
            overall = level

    actions = list(actions_map.get(overall, []))
    return {
        "available": True,
        "module": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "evaluated_at": time.time(),
        "escalation": {
            "level": overall,
            "actions": actions,
            "findings": findings,
        },
    }


def _apply_escalation_actions(level: str, actions: List[str]) -> Dict[str, Any]:
    """Führt erlaubte lokale Aktionen aus (best-effort, idempotent)."""
    applied: Dict[str, Any] = {"level": level, "actions": actions, "results": {}}

    if "memory_guard_relieve" in actions or "stop_llama_server" in actions:
        try:
            from memory_guard import get_memory_guard

            applied["results"]["memory_guard"] = get_memory_guard().relieve_once()
        except Exception as exc:
            applied["results"]["memory_guard"] = {"error": str(exc)}

    if "trigger_storage_policy" in actions and level == "critical":
        script = _repo_root() / "workstation" / "apply-storage-policy.ps1"
        applied["results"]["storage_policy"] = {
            "script": str(script),
            "exists": script.exists(),
            "note": "run via workstation/apply-storage-policy.ps1",
        }

    if "suggest_storage_offload" in actions:
        applied["results"]["storage_offload"] = {
            "script": str(_repo_root() / "workstation" / "offload-to-gdrive.ps1"),
            "suggested": True,
        }

    return applied


def write_state(payload: Dict[str, Any]) -> Path:
    path = _status_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def read_cached_state() -> Optional[Dict[str, Any]]:
    path = _status_file()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def run_cycle(
    timeout: float = 4.0,
    apply_actions: bool = False,
) -> Dict[str, Any]:
    """Probe + Evaluate (+ optional Aktionen) und Status persistieren."""
    probed = probe(timeout=timeout)
    evaluated = evaluate(probed)
    escalation = evaluated.get("escalation") or {}
    level = str(escalation.get("level", "ok"))
    actions = list(escalation.get("actions") or [])

    payload: Dict[str, Any] = {
        "available": True,
        "module": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "cycle_at": time.time(),
        "probe": probed,
        "escalation": escalation,
    }

    if apply_actions and level in ("alert", "critical"):
        payload["applied"] = _apply_escalation_actions(level, actions)

    write_state(payload)
    return payload


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Local infrastructure kernel cycle")
    parser.add_argument("--run-cycle", action="store_true", help="Probe + evaluate + write status.json")
    parser.add_argument("--probe", action="store_true", help="Nur probe (JSON stdout)")
    parser.add_argument("--status", action="store_true", help="Nur status (JSON stdout)")
    parser.add_argument("--apply-actions", action="store_true", help="Eskalationsaktionen ausführen")
    parser.add_argument("--timeout", type=float, default=4.0)
    args = parser.parse_args()

    if args.run_cycle:
        out = run_cycle(timeout=args.timeout, apply_actions=args.apply_actions)
    elif args.probe:
        out = probe(timeout=args.timeout)
    elif args.status:
        out = status()
    else:
        out = run_cycle(timeout=args.timeout, apply_actions=False)

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
