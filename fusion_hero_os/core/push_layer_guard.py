# -*- coding: utf-8 -*-
"""
Push Layer Guard — weave update structure into layers.

Uses known identifications (remote, branch, VERSION, path→layer, auto-save
markers, intent tokens) to:
  - fail closed on unwanted pushes
  - never block intentional wanted pushes (except hard secret denylist)

Geltung: Spezifikation (guard) · path layering aligned with dual_timeline/layers.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "push_layer_guard.yaml"

__all__ = [
    "PushDecision",
    "evaluate_push",
    "load_config",
    "install_hint",
    "status",
]


@dataclass
class PushDecision:
    allow: bool
    reason: str
    wanted: bool
    unwanted: bool
    intent: bool
    auto_save: bool
    remote_ok: bool
    branch: str
    remote: str
    layers_touched: List[str] = field(default_factory=list)
    deny_hits: List[str] = field(default_factory=list)
    soft_deny_hits: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    commit_subjects: List[str] = field(default_factory=list)
    platform_ok: bool = True
    advice: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _git(args: Sequence[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=str(cwd or ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def _match_any(path: str, patterns: List[str]) -> Optional[str]:
    path_n = path.replace("\\", "/")
    while path_n.startswith("./"):
        path_n = path_n[2:]
    base = path_n.split("/")[-1]
    for pat in patterns or []:
        pat_n = pat.replace("\\", "/")
        # basename / exact
        if path_n == pat_n.lstrip("*/") or base == pat_n.lstrip("*/"):
            return pat
        if pat_n.startswith("**/"):
            tail = pat_n[3:]
            if fnmatch.fnmatch(path_n, pat_n) or fnmatch.fnmatch(base, tail) or path_n.endswith("/" + tail) or path_n == tail:
                return pat
        if fnmatch.fnmatch(path_n, pat_n) or fnmatch.fnmatch(base, pat_n):
            return pat
        # prefix style
        if pat_n.endswith("/") and (path_n.startswith(pat_n) or path_n.startswith(pat_n.lstrip("*/"))):
            return pat
        if path_n == pat_n.rstrip("/"):
            return pat
        # *secret* style on full path
        if "*" in pat_n and fnmatch.fnmatch(path_n, pat_n):
            return pat
    return None


def _layers_for_paths(paths: List[str], cfg: Dict[str, Any]) -> List[str]:
    layers_cfg = cfg.get("layers") or {}
    touched: List[str] = []
    for path in paths:
        p = path.replace("\\", "/")
        for lid, meta in layers_cfg.items():
            for pref in meta.get("paths") or []:
                pref_n = pref.replace("\\", "/").rstrip("*")
                if pref_n.endswith("/"):
                    if p.startswith(pref_n) or ("/" + pref_n) in ("/" + p):
                        if lid not in touched:
                            touched.append(lid)
                elif fnmatch.fnmatch(p, pref.replace("\\", "/")) or p == pref_n or p.startswith(pref_n.rstrip("/") + "/"):
                    if lid not in touched:
                        touched.append(lid)
    return touched


def _intent_present(cfg: Dict[str, Any], subjects: List[str]) -> bool:
    intent = cfg.get("intent") or {}
    true_vals = {v.lower() for v in (intent.get("env_true_values") or ["1", "true"])}
    for key in intent.get("env_keys") or []:
        val = (os.environ.get(key) or "").strip().lower()
        if val in true_vals:
            return True
    markers = intent.get("commit_markers") or []
    prefixes = intent.get("conventional_prefixes") or []
    for sub in subjects:
        s = sub.strip()
        sl = s.lower()
        for m in markers:
            if m.lower() in sl:
                return True
        for pref in prefixes:
            if s.startswith(pref) or sl.startswith(pref.lower()):
                # pure auto-save with conventional? rare — still count as wanted style
                if not any(sl.startswith(ap) for ap in (cfg.get("auto_save") or {}).get("message_prefixes") or []):
                    return True
    return False


def _is_auto_save(subjects: List[str], cfg: Dict[str, Any]) -> bool:
    prefixes = (cfg.get("auto_save") or {}).get("message_prefixes") or ["auto-save"]
    if not subjects:
        return False
    # all subjects look like auto-save → auto_save batch
    hits = 0
    for sub in subjects:
        sl = sub.lower().strip()
        if any(sl.startswith(p.lower()) for p in prefixes):
            hits += 1
    return hits == len(subjects) and hits > 0


def _remote_ok(remote_url: str, cfg: Dict[str, Any]) -> bool:
    ids = cfg.get("identities") or {}
    allowed = ids.get("remote_urls") or []
    url = (remote_url or "").strip().rstrip("/")
    if not url:
        return False
    for a in allowed:
        a = a.strip().rstrip("/")
        if url == a or url.endswith(a.replace("https://", "").replace("git@", "")):
            return True
        if "95guknow/fusion-hero-os" in url and "95guknow/fusion-hero-os" in a:
            return True
    return False


def _platform_ok(cfg: Dict[str, Any]) -> bool:
    ids = cfg.get("identities") or {}
    expected = str(ids.get("platform_version") or "10.0.0")
    vf = ROOT / (ids.get("platform_version_file") or "VERSION")
    if not vf.exists():
        return False
    return vf.read_text(encoding="utf-8").strip() == expected


def _collect_push_files(remote: str, branch: str) -> Tuple[List[str], List[str]]:
    """Return (files, commit subjects) for commits not on remote/branch."""
    # commits to be pushed
    code, out = _git(["log", f"{remote}/{branch}..HEAD", "--pretty=%s"])
    if code != 0:
        # no upstream yet — use unpushed vs origin/main or all recent
        code2, out2 = _git(["log", "origin/main..HEAD", "--pretty=%s"])
        subjects = [ln.strip() for ln in (out2 if code2 == 0 else out).splitlines() if ln.strip()]
        code3, out3 = _git(["diff", "--name-only", "origin/main...HEAD"])
        if code3 != 0:
            code3, out3 = _git(["diff", "--name-only", "HEAD~10..HEAD"])
        files = [ln.strip().replace("\\", "/") for ln in out3.splitlines() if ln.strip()]
        return files, subjects

    subjects = [ln.strip() for ln in out.splitlines() if ln.strip()]
    code, out = _git(["diff", "--name-only", f"{remote}/{branch}...HEAD"])
    files = [ln.strip().replace("\\", "/") for ln in out.splitlines() if ln.strip()]
    return files, subjects


def evaluate_push(
    *,
    remote: str = "origin",
    branch: Optional[str] = None,
    remote_url: Optional[str] = None,
    force: bool = False,
    files: Optional[List[str]] = None,
    subjects: Optional[List[str]] = None,
) -> PushDecision:
    cfg = load_config()
    code, cur_branch = _git(["branch", "--show-current"])
    branch = (branch or cur_branch.strip() or "main").strip()

    if not remote_url:
        code, url = _git(["remote", "get-url", remote])
        remote_url = url.strip() if code == 0 else ""

    if files is None or subjects is None:
        f2, s2 = _collect_push_files(remote, branch)
        files = files if files is not None else f2
        subjects = subjects if subjects is not None else s2

    files = [f.replace("\\", "/") for f in (files or [])]
    subjects = list(subjects or [])

    intent = _intent_present(cfg, subjects)
    auto_save = _is_auto_save(subjects, cfg)
    remote_ok = _remote_ok(remote_url or "", cfg)
    platform_ok = _platform_ok(cfg)
    layers = _layers_for_paths(files, cfg)

    deny_hits: List[str] = []
    soft_hits: List[str] = []
    for f in files:
        d = _match_any(f, cfg.get("deny_globs") or [])
        if d:
            deny_hits.append(f"{f} ({d})")
        s = _match_any(f, cfg.get("soft_deny_globs") or [])
        if s:
            soft_hits.append(f"{f} ({s})")

    # L6 protected
    if "L6_protected_local" in layers and not intent:
        return PushDecision(
            allow=False,
            reason="L6_protected_local paths require explicit push intent",
            wanted=False,
            unwanted=True,
            intent=intent,
            auto_save=auto_save,
            remote_ok=remote_ok,
            branch=branch,
            remote=remote,
            layers_touched=layers,
            deny_hits=deny_hits,
            soft_deny_hits=soft_hits,
            files=files,
            commit_subjects=subjects,
            platform_ok=platform_ok,
            advice="Set FUSION_PUSH_INTENT=1 for wanted push; never commit live inventory/secrets.",
        )

    if deny_hits:
        return PushDecision(
            allow=False,
            reason="Hard denylist hit (secrets/local inventory) — blocked even with intent",
            wanted=False,
            unwanted=True,
            intent=intent,
            auto_save=auto_save,
            remote_ok=remote_ok,
            branch=branch,
            remote=remote,
            layers_touched=layers,
            deny_hits=deny_hits,
            soft_deny_hits=soft_hits,
            files=files,
            commit_subjects=subjects,
            platform_ok=platform_ok,
            advice="Remove deny_globs matches from the push set.",
        )

    if soft_hits and not intent:
        return PushDecision(
            allow=False,
            reason="Soft denylist (large binaries/venv) without push intent",
            wanted=False,
            unwanted=True,
            intent=intent,
            auto_save=auto_save,
            remote_ok=remote_ok,
            branch=branch,
            remote=remote,
            layers_touched=layers,
            deny_hits=deny_hits,
            soft_deny_hits=soft_hits,
            files=files,
            commit_subjects=subjects,
            platform_ok=platform_ok,
            advice="Set FUSION_PUSH_INTENT=1 if this binary push is wanted.",
        )

    branch_rules = (cfg.get("branches") or {}).get(branch) or (cfg.get("branches") or {}).get("*") or {}
    if force and branch_rules.get("block_force", True):
        if not intent:
            return PushDecision(
                allow=False,
                reason="Force-push blocked without intent",
                wanted=False,
                unwanted=True,
                intent=intent,
                auto_save=auto_save,
                remote_ok=remote_ok,
                branch=branch,
                remote=remote,
                layers_touched=layers,
                files=files,
                commit_subjects=subjects,
                platform_ok=platform_ok,
                advice="Refusing force-push. Set FUSION_PUSH_INTENT=1 only if truly wanted.",
            )

    if branch_rules.get("require_identity_remote", True) and not remote_ok:
        return PushDecision(
            allow=False,
            reason=f"Remote URL not in known identities: {remote_url!r}",
            wanted=False,
            unwanted=True,
            intent=intent,
            auto_save=auto_save,
            remote_ok=False,
            branch=branch,
            remote=remote,
            layers_touched=layers,
            files=files,
            commit_subjects=subjects,
            platform_ok=platform_ok,
            advice="Push only to known remote github.com/95guknow/fusion-hero-os",
        )

    if not platform_ok:
        # warn but allow with intent (version bump mid-flight)
        if not intent:
            return PushDecision(
                allow=False,
                reason="VERSION platform pin mismatch without intent",
                wanted=False,
                unwanted=True,
                intent=intent,
                auto_save=auto_save,
                remote_ok=remote_ok,
                branch=branch,
                remote=remote,
                layers_touched=layers,
                files=files,
                commit_subjects=subjects,
                platform_ok=False,
                advice="Align VERSION to 10.0.0 or set FUSION_PUSH_INTENT=1 for intentional version drift push.",
            )

    # auto-save only commits → unwanted on main unless intent
    auto_need = bool((cfg.get("auto_save") or {}).get("require_intent_for_push", True))
    if auto_save and auto_need and not intent:
        return PushDecision(
            allow=False,
            reason="Unwanted auto-save push without intent (layer guard)",
            wanted=False,
            unwanted=True,
            intent=False,
            auto_save=True,
            remote_ok=remote_ok,
            branch=branch,
            remote=remote,
            layers_touched=layers,
            files=files,
            commit_subjects=subjects,
            platform_ok=platform_ok,
            advice=(
                "Wanted: $env:FUSION_PUSH_INTENT='1'; git push "
                "OR commit with conventional prefix (feat:/fix:/docs:) "
                "OR message marker [push-ok]."
            ),
        )

    # empty push
    if not files and not subjects:
        return PushDecision(
            allow=True,
            reason="Nothing to push",
            wanted=True,
            unwanted=False,
            intent=intent,
            auto_save=auto_save,
            remote_ok=remote_ok,
            branch=branch,
            remote=remote,
            platform_ok=platform_ok,
            advice="",
        )

    # wanted path
    return PushDecision(
        allow=True,
        reason=(
            "Wanted push allowed (intent or conventional commit; known remote; "
            "layers classified; no hard deny)"
            if intent or not auto_save
            else "Allowed"
        ),
        wanted=True,
        unwanted=False,
        intent=intent,
        auto_save=auto_save,
        remote_ok=remote_ok,
        branch=branch,
        remote=remote,
        layers_touched=layers,
        deny_hits=deny_hits,
        soft_deny_hits=soft_hits,
        files=files,
        commit_subjects=subjects,
        platform_ok=platform_ok,
        advice="",
    )


def status() -> Dict[str, Any]:
    cfg = load_config()
    code, branch = _git(["branch", "--show-current"])
    code, url = _git(["remote", "get-url", "origin"])
    d = evaluate_push(remote="origin", branch=branch.strip() or "main", remote_url=url.strip())
    return {
        "ok": True,
        "platform": "10.0.0",
        "policy": "pseudo_inhouse_only",
        "freemium": False,
        "config": str(CONFIG_PATH),
        "decision_preview": d.to_dict(),
        "identities": cfg.get("identities"),
        "layers": list((cfg.get("layers") or {}).keys()),
    }


def install_hint() -> str:
    return (
        "python scripts/install_push_guard_hooks.py\n"
        "Wanted push: $env:FUSION_PUSH_INTENT='1'; git push origin main\n"
        "Or commit subject with [push-ok] / feat: / fix: / docs:"
    )


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Push layer guard")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    d = evaluate_push(
        remote=args.remote,
        branch=args.branch or None,
        force=args.force,
    )
    if args.json:
        print(json.dumps(d.to_dict(), indent=2, ensure_ascii=False))
    else:
        mark = "ALLOW" if d.allow else "BLOCK"
        print(f"[{mark}] {d.reason}")
        if d.layers_touched:
            print("layers:", ", ".join(d.layers_touched))
        if d.advice:
            print("advice:", d.advice)
        if d.deny_hits:
            print("deny:", d.deny_hits)
        if d.commit_subjects[:5]:
            print("commits:", d.commit_subjects[:5])
    # write last decision
    out = Path.home() / ".fusion" / "mesh" / "coordination" / "push_guard_last.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = d.to_dict()
    payload["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if d.allow else 2


if __name__ == "__main__":
    raise SystemExit(main())
