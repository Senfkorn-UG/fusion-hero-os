# -*- coding: utf-8 -*-
"""Headset multi-layer membrane — several layers armed, ONE active (loud & clear).

Layers (placement-aligned, additive):
  L1_local       PC speakers/mic (no AudioRelay default)
  L2_phone       Phone headset via AudioRelay (system audio)
  L3_comaedchen  Operator <-> Comädchen voice on phone path
  L4_hyperraum   Hyperraum control-plane membrane (phone path + plane tag)

Multi-layer usage: any subset may be **enabled** (armed).
Exactly one layer is **active** (default playback route + channel semantics).

State: ``~/.fusion/headset_layers.json``
Banner: always printed / returned so the operator never guesses the level.

Geltung: Spezifikation · hardware state = empirical.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

__all__ = [
    "LAYERS",
    "LAYER_ORDER",
    "STATE_PATH",
    "banner",
    "status",
    "enable",
    "disable",
    "set_active",
    "apply_active_route",
    "activate_stack",
]

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = Path.home() / ".fusion" / "headset_layers.json"
SVV = ROOT / "workstation" / "tools" / "SoundVolumeView.exe"

LAYER_ORDER = ("L1_local", "L2_phone", "L3_comaedchen", "L4_hyperraum")

LAYERS: Dict[str, Dict[str, Any]] = {
    "L1_local": {
        "id": "L1_local",
        "rank": 1,
        "label": "LOCAL PC",
        "short": "L1",
        "route": "local",
        "device_hint": "Lautsprecher / host Realtek",
        "plane": "hyperraum",
        "description": "PC speakers + mic. No phone relay as default output.",
        "color": "cyan",
    },
    "L2_phone": {
        "id": "L2_phone",
        "rank": 2,
        "label": "PHONE RELAY",
        "short": "L2",
        "route": "phone",
        "device_hint": "Virtual Speakers for AudioRelay",
        "plane": "hyperraum",
        "description": "System audio -> phone headset (AudioRelay).",
        "color": "green",
    },
    "L3_comaedchen": {
        "id": "L3_comaedchen",
        "rank": 3,
        "label": "COMAEDCHEN",
        "short": "L3",
        "route": "phone",
        "device_hint": "Virtual Speakers for AudioRelay + Comet",
        "plane": "hyperraum",
        "description": "Operator <-> Nummer-2 voice channel on phone path.",
        "opens_comet": True,
        "color": "magenta",
    },
    "L4_hyperraum": {
        "id": "L4_hyperraum",
        "rank": 4,
        "label": "HYPERRAUM",
        "short": "L4",
        "route": "phone",
        "device_hint": "Virtual Speakers + hyperraum control membrane",
        "plane": "hyperraum",
        "description": "Half-private hyperraum audio membrane (control plane).",
        "color": "yellow",
        "opens_comet": False,
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_state() -> Dict[str, Any]:
    return {
        "version": "1.0",
        "platform_version": "10.0.0",
        "membrane": "headset_layers_v1",
        "enabled": ["L1_local", "L2_phone", "L3_comaedchen", "L4_hyperraum"],
        "active": "L1_local",
        "updated_at": None,
        "last_apply": None,
        "history": [],
    }


def load_state() -> Dict[str, Any]:
    st = _default_state()
    if STATE_PATH.is_file():
        try:
            raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                st.update({k: v for k, v in raw.items() if k in st or k in (
                    "enabled", "active", "updated_at", "last_apply", "history", "note"
                )})
        except (OSError, json.JSONDecodeError):
            st["load_error"] = "corrupt_state_reset"
    # sanitize
    enabled = [x for x in (st.get("enabled") or []) if x in LAYERS]
    if not enabled:
        enabled = list(LAYER_ORDER)
    st["enabled"] = enabled
    active = st.get("active") or "L1_local"
    if active not in LAYERS:
        active = "L1_local"
    # active must be enabled — if not, promote first enabled
    if active not in enabled:
        active = enabled[0]
    st["active"] = active
    return st


def save_state(st: Dict[str, Any]) -> Path:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    st = dict(st)
    st["updated_at"] = _now()
    # keep short history
    hist = list(st.get("history") or [])
    hist.append({
        "ts": st["updated_at"],
        "active": st.get("active"),
        "enabled": list(st.get("enabled") or []),
    })
    st["history"] = hist[-20:]
    STATE_PATH.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return STATE_PATH


def banner(active: Optional[str] = None, enabled: Optional[List[str]] = None) -> str:
    """Very loud, unambiguous active-level banner (ASCII)."""
    st = load_state()
    act = active or st["active"]
    en = enabled if enabled is not None else list(st["enabled"])
    meta = LAYERS.get(act, {})
    label = meta.get("label", act)
    short = meta.get("short", "?")
    route = meta.get("route", "?")
    plane = meta.get("plane", "?")
    desc = meta.get("description", "")
    device = meta.get("device_hint", "")

    # enabled markers
    marks = []
    for lid in LAYER_ORDER:
        m = LAYERS[lid]
        if lid == act:
            marks.append(f"[{m['short']}:ACTIVE]")
        elif lid in en:
            marks.append(f"[{m['short']}:armed]")
        else:
            marks.append(f"[{m['short']}:off]")

    lines = [
        "",
        "################################################################",
        f"#  HEADSET ACTIVE LEVEL >>>  {short} = {label}  <<<",
        f"#  route={route}   plane={plane}",
        f"#  device: {device}",
        f"#  {desc}",
        f"#  stack: {'  '.join(marks)}",
        "################################################################",
        "",
    ]
    return "\n".join(lines)


def status(*, apply_probe: bool = False) -> Dict[str, Any]:
    st = load_state()
    act = st["active"]
    meta = dict(LAYERS[act])
    layers_view = []
    for lid in LAYER_ORDER:
        m = dict(LAYERS[lid])
        m["enabled"] = lid in st["enabled"]
        m["active"] = lid == act
        m["marker"] = "ACTIVE" if lid == act else ("armed" if lid in st["enabled"] else "off")
        layers_view.append(m)

    out: Dict[str, Any] = {
        "ok": True,
        "membrane": "headset_layers_v1",
        "platform_version": "10.0.0",
        "active": act,
        "active_label": meta.get("label"),
        "active_short": meta.get("short"),
        "active_route": meta.get("route"),
        "active_plane": meta.get("plane"),
        "active_device_hint": meta.get("device_hint"),
        "enabled": list(st["enabled"]),
        "layers": layers_view,
        "banner": banner(act, st["enabled"]),
        "banner_one_line": (
            f"HEADSET ACTIVE LEVEL >>> {meta.get('short')}={meta.get('label')} "
            f"(route={meta.get('route')}) <<<"
        ),
        "state_path": str(STATE_PATH),
        "updated_at": st.get("updated_at"),
        "clarity_rule": (
            "Multi-layer allowed: many layers may be armed; "
            "exactly ONE is ACTIVE. Always read banner / active_short."
        ),
    }

    # live hardware hints
    try:
        from fusion_hero_os.core.comaedchen_audio import (
            _process_running,
            _phone_online,
        )

        out["live"] = {
            "audiorelay": _process_running(["AudioRelay", "audiorelay-backend"]),
            "phone": _phone_online(),
        }
    except Exception as exc:  # noqa: BLE001
        out["live"] = {"error": str(exc)[:160]}

    if apply_probe:
        out["default_device_probe"] = _probe_default_device()
    return out


def _probe_default_device() -> Dict[str, Any]:
    if not SVV.is_file():
        return {"ok": False, "error": "SoundVolumeView missing"}
    csv = Path.home() / ".fusion" / "headset_default_probe.csv"
    try:
        subprocess.run(
            [str(SVV), "/scomma", str(csv)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if not csv.is_file():
            return {"ok": False, "error": "no csv"}
        import csv as csvmod

        with csv.open("r", encoding="utf-8", errors="replace") as f:
            rows = list(csvmod.DictReader(f))
        for row in rows:
            if row.get("Type") == "Device" and row.get("Direction") == "Render":
                d = row.get("Default") or ""
                dm = row.get("Default Multimedia") or ""
                if d == "Render" or dm == "Render":
                    name = row.get("Name") or ""
                    dev = row.get("Device Name") or ""
                    is_ar = "AudioRelay" in dev or "Virtual Speakers" in name
                    return {
                        "ok": True,
                        "name": name,
                        "device_name": dev,
                        "is_audiorelay": is_ar,
                        "inferred_route": "phone" if is_ar else "local",
                    }
        return {"ok": False, "error": "no default render row"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def enable(layer_id: str) -> Dict[str, Any]:
    lid = _norm(layer_id)
    st = load_state()
    en = list(st["enabled"])
    if lid not in en:
        en.append(lid)
        # keep order
        en = [x for x in LAYER_ORDER if x in en]
    st["enabled"] = en
    save_state(st)
    return status()


def disable(layer_id: str) -> Dict[str, Any]:
    lid = _norm(layer_id)
    st = load_state()
    en = [x for x in st["enabled"] if x != lid]
    if not en:
        return {
            "ok": False,
            "error": "cannot disable last layer — at least one must stay armed",
            "banner": banner(),
        }
    st["enabled"] = en
    if st["active"] == lid:
        st["active"] = en[0]
    save_state(st)
    # re-apply if active changed
    return set_active(st["active"], apply_route=True)


def _norm(layer_id: str) -> str:
    raw = (layer_id or "").strip()
    aliases = {
        "1": "L1_local",
        "l1": "L1_local",
        "local": "L1_local",
        "pc": "L1_local",
        "2": "L2_phone",
        "l2": "L2_phone",
        "phone": "L2_phone",
        "relay": "L2_phone",
        "3": "L3_comaedchen",
        "l3": "L3_comaedchen",
        "comaedchen": "L3_comaedchen",
        "comet": "L3_comaedchen",
        "4": "L4_hyperraum",
        "l4": "L4_hyperraum",
        "hyperraum": "L4_hyperraum",
        "hyper": "L4_hyperraum",
    }
    key = raw.lower().replace("-", "_")
    if raw in LAYERS:
        return raw
    if key in aliases:
        return aliases[key]
    # L2_phone style
    for lid in LAYER_ORDER:
        if key == lid.lower() or key == LAYERS[lid]["short"].lower():
            return lid
    raise ValueError(f"unknown headset layer: {layer_id!r} — use {list(LAYER_ORDER)}")


def set_active(layer_id: str, *, apply_route: bool = True) -> Dict[str, Any]:
    """Set the single ACTIVE layer (must be enabled or will be auto-enabled)."""
    lid = _norm(layer_id)
    st = load_state()
    en = list(st["enabled"])
    if lid not in en:
        en.append(lid)
        en = [x for x in LAYER_ORDER if x in en]
    st["enabled"] = en
    st["active"] = lid
    save_state(st)

    apply_result = None
    if apply_route:
        apply_result = apply_active_route()
        st = load_state()
        st["last_apply"] = apply_result
        save_state(st)

    out = status(apply_probe=True)
    out["apply"] = apply_result
    out["ok"] = True if apply_result is None else bool(
        (apply_result or {}).get("ok", True)
    )
    return out


def apply_active_route() -> Dict[str, Any]:
    """Apply Windows default device + optional Comet for current active layer."""
    st = load_state()
    lid = st["active"]
    meta = LAYERS[lid]
    route = meta["route"]
    report: Dict[str, Any] = {
        "ok": False,
        "active": lid,
        "label": meta["label"],
        "route": route,
        "ts": _now(),
        "steps": {},
        "banner_one_line": (
            f"HEADSET ACTIVE LEVEL >>> {meta['short']}={meta['label']} "
            f"(route={route}) <<<"
        ),
    }

    if route == "phone":
        fix = ROOT / "workstation" / "fix-headset-relay.ps1"
        if fix.is_file():
            try:
                r = subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(fix),
                        "-NoRestartAudioRelay",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=90,
                    cwd=str(ROOT),
                )
                report["steps"]["fix_headset_relay"] = {
                    "ok": r.returncode == 0,
                    "rc": r.returncode,
                    "stdout_tail": (r.stdout or "")[-400:],
                }
            except Exception as exc:  # noqa: BLE001
                report["steps"]["fix_headset_relay"] = {"ok": False, "error": str(exc)[:200]}
        # ensure default Virtual Speakers
        report["steps"]["set_default"] = _svv_set_default("Virtual Speakers for AudioRelay")
    else:
        # local — try common host speaker names
        for name in (
            "Lautsprecher",
            "Speakers",
            "2- Realtek(R) Audio",
        ):
            res = _svv_set_default(name)
            report["steps"][f"set_default_{name}"] = res
            if res.get("ok"):
                break
        report["steps"]["local_note"] = {
            "ok": True,
            "note": "L1 local: prefer host speakers; phone relay not forced as default",
        }

    if meta.get("opens_comet"):
        try:
            from fusion_hero_os.core.comaedchen_audio import activate as comaedchen_activate

            report["steps"]["comaedchen"] = comaedchen_activate(
                mode="phone" if route == "phone" else "local",
                open_surface=True,
                route_audio=False,  # already routed above
            )
        except Exception as exc:  # noqa: BLE001
            report["steps"]["comaedchen"] = {"ok": False, "error": str(exc)[:200]}

    # probe
    probe = _probe_default_device()
    report["probe"] = probe
    if route == "phone":
        report["ok"] = bool(probe.get("is_audiorelay") or report["steps"].get("fix_headset_relay", {}).get("ok"))
    else:
        report["ok"] = bool(not probe.get("is_audiorelay", False) or probe.get("ok") is False)
        # if probe failed, still ok if we attempted local
        if not probe.get("ok"):
            report["ok"] = True
            report["note"] = "local apply attempted; probe inconclusive"

    report["banner"] = banner()
    return report


def _svv_set_default(device_name: str) -> Dict[str, Any]:
    if not SVV.is_file():
        return {"ok": False, "error": "SoundVolumeView missing", "device": device_name}
    try:
        r = subprocess.run(
            [str(SVV), "/SetDefault", device_name, "all"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        time.sleep(0.4)
        return {"ok": r.returncode == 0, "rc": r.returncode, "device": device_name}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200], "device": device_name}


def activate_stack(
    *,
    active: str = "L2_phone",
    enable_all: bool = True,
) -> Dict[str, Any]:
    """Arm multi-layer stack and set active level (default phone relay)."""
    st = load_state()
    if enable_all:
        st["enabled"] = list(LAYER_ORDER)
    save_state(st)
    return set_active(active, apply_route=True)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Headset multi-layer — clear ACTIVE level"
    )
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--banner", action="store_true")
    ap.add_argument("--active", default="", help="set active layer (L1..L4 or alias)")
    ap.add_argument("--enable", default="", help="arm a layer without switching active")
    ap.add_argument("--disable", default="", help="disarm a layer")
    ap.add_argument("--apply", action="store_true", help="re-apply route for current active")
    ap.add_argument("--stack", action="store_true", help="enable all layers")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.enable:
        out = enable(args.enable)
    elif args.disable:
        out = disable(args.disable)
    elif args.active:
        out = set_active(args.active, apply_route=True)
    elif args.apply:
        apply_active_route()
        out = status(apply_probe=True)
    elif args.stack:
        out = activate_stack(active="L2_phone", enable_all=True)
    else:
        out = status(apply_probe=True)

    # Always print banner to stdout (clarity requirement)
    print(out.get("banner") or banner(), file=sys.stderr if args.json else sys.stdout)
    if args.json or args.status or args.active or args.stack or args.apply or args.enable or args.disable:
        # strip huge banner from json body duplicate
        body = dict(out)
        if args.json:
            print(json.dumps(body, indent=2, ensure_ascii=False))
        else:
            print(body.get("banner_one_line", ""))
            print(f"active={body.get('active')}  enabled={body.get('enabled')}")
            if body.get("apply"):
                print(f"apply_ok={body['apply'].get('ok')}  route={body['apply'].get('route')}")
            probe = body.get("default_device_probe") or (body.get("apply") or {}).get("probe")
            if probe:
                print(
                    f"device_probe: {probe.get('name')} / {probe.get('device_name')} "
                    f"is_audiorelay={probe.get('is_audiorelay')}"
                )
    return 0 if out.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
