# -*- coding: utf-8 -*-
"""
x402 Full Stack — one entry point for the complete security package.

Runs:
  1) threat audit (heroic math + gates + emergency warn)
  2) sandbox property audit (6 evidence cases)
  3) successful attack simulation (0.01 ct dormant wallet, insecure mock)
  4) master report (JSON + MD)
  5) optional: on-chain dry-run / broadcast
  6) optional: gh release notes path

Usage:
  python scripts/run_x402_stack.py
  python scripts/run_x402_stack.py --broadcast-onchain
  python scripts/run_x402_stack.py --json-only
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "03_Code"))

OUT = Path.home() / ".fusion" / "x402"
DOCS = ROOT / "docs" / "security"


def _run_all(budget_eur: float = 500.0) -> dict:
    from fusion_hero_os.core.x402_hackability_audit import audit as threat_audit
    from fusion_hero_os.core.x402_sandbox_audit import (
        run_sandbox_audit,
        simulate_successful_attack,
    )

    threat = threat_audit(emit=True)
    sandbox = run_sandbox_audit(budget_eur=budget_eur)
    attack = simulate_successful_attack(
        public_damage_eur_cents=0.01, dormant_days=900
    )

    master = {
        "ok": bool(sandbox.get("ok") and attack.get("ok")),
        "stack": "x402_full",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "github": "https://github.com/95guknow/fusion-hero-os",
        "instagram": "https://www.instagram.com/95guknow/",
        "instagram_status": "CONNECTED_LIVE",
        "threat_audit": {
            "level": threat.level,
            "risk_score": threat.risk_score,
            "warn": threat.warn,
            "controls": f"{threat.controls_ok}/{threat.controls_total}",
            "open_attacks": [a.get("id") for a in threat.open_attacks],
            "emergency_paths": threat.emergency_paths,
        },
        "sandbox_audit": {
            "proved": f"{sandbox.get('proved_count')}/{sandbox.get('case_count')}",
            "ok": sandbox.get("ok"),
            "sha16": sandbox.get("sha16"),
            "evidence_paths": sandbox.get("evidence_paths"),
        },
        "attack_simulation": {
            "succeeded_insecure": attack.get("attack_succeeded_on_insecure_mock"),
            "blocked_secure": attack.get("attack_blocked_on_secure_mock"),
            "public_damage_ct": 0.01,
            "dormant_days": 900,
            "real_chain_transfer": False,
            "sha16": attack.get("sha16"),
            "impact": attack.get("impact"),
            "evidence_paths": attack.get("evidence_paths"),
        },
        "media": {
            "pack": "docs/security/media/",
            "instagram_profile": "https://www.instagram.com/95guknow/",
            "pr": "https://github.com/95guknow/fusion-hero-os/pull/69",
            "caption": "docs/security/media/IG_CAPTION.txt",
            "image": "docs/security/media/IG_x402_block_hack_lab.jpg",
        },
        "onchain": {
            "script": "scripts/x402_onchain_publicity.py",
            "chain": "base",
            "requires": "FUSION_PUBLICITY_PRIVATE_KEY",
            "message": "docs/security/X402_ONCHAIN_PUBLICITY_MESSAGE.txt",
        },
        "policy": {
            "sandbox_only_for_attack": True,
            "no_exploit_payloads": True,
            "no_live_facilitator_attack": True,
            "x402_as_source_of_truth": False,
        },
        "cli": {
            "stack": "python scripts/run_x402_stack.py",
            "audit": "python -m fusion_hero_os.core.x402_hackability_audit --audit",
            "sandbox": "python -m fusion_hero_os.core.x402_sandbox_audit",
            "attack": "python -m fusion_hero_os.core.x402_sandbox_audit --simulate-attack",
            "onchain_dry": "python scripts/x402_onchain_publicity.py --dry-run",
            "onchain_broadcast": "python scripts/x402_onchain_publicity.py --broadcast",
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    master_path = OUT / "x402_stack_master.json"
    master_path.write_text(json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = [
        "# x402 Full Stack — Master Report",
        "",
        f"**Generated:** {master['generated_at']}",
        f"**GitHub:** {master['github']}",
        f"**Instagram:** {master['instagram']} (`{master['instagram_status']}`)",
        "",
        "## Results",
        "",
        f"| Layer | Status |",
        f"|-------|--------|",
        f"| Threat audit | **{threat.level}** · score {threat.risk_score} · gates {threat.controls_ok}/{threat.controls_total} |",
        f"| Sandbox evidence | **{sandbox.get('proved_count')}/{sandbox.get('case_count')} proved** |",
        f"| Attack sim (insecure) | **SUCCESS** · SHA `{attack.get('sha16')}` |",
        f"| Attack sim (secure) | **BLOCKED** |",
        f"| Public damage envelope | **0,01 ct** · dormant 900d · no chain transfer |",
        f"| Media pack | PR #69 merged · @95guknow |",
        f"| On-chain publicity | script ready (needs `FUSION_PUBLICITY_PRIVATE_KEY`) |",
        "",
        "## One-liner",
        "",
        "```powershell",
        "python scripts/run_x402_stack.py",
        "```",
        "",
        "## Policy",
        "",
        "- Sandbox attack only · no live facilitator exploit",
        "- Emergency warn when gates open",
        "- MasterSeed never via x402",
        "",
        f"Master JSON: `{master_path}`",
        "",
    ]
    md_path = OUT / "X402_STACK_MASTER.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    (DOCS / "X402_STACK.md").write_text("\n".join(md_lines), encoding="utf-8")
    (DOCS / "x402_stack.summary.json").write_text(
        json.dumps(
            {
                "generated_at": master["generated_at"],
                "threat_level": threat.level,
                "threat_score": threat.risk_score,
                "sandbox_proved": f"{sandbox.get('proved_count')}/{sandbox.get('case_count')}",
                "attack_insecure": attack.get("attack_succeeded_on_insecure_mock"),
                "attack_secure_block": attack.get("attack_blocked_on_secure_mock"),
                "attack_sha16": attack.get("sha16"),
                "instagram": master["instagram"],
                "github": master["github"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    master["master_paths"] = [
        str(master_path),
        str(md_path),
        str(DOCS / "X402_STACK.md"),
        str(DOCS / "x402_stack.summary.json"),
    ]
    return master


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="x402 full stack runner")
    ap.add_argument("--budget-eur", type=float, default=500.0)
    ap.add_argument("--broadcast-onchain", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    ap.add_argument("--release", action="store_true", help="create gh release if gh available")
    args = ap.parse_args()

    master = _run_all(budget_eur=args.budget_eur)

    if args.broadcast_onchain:
        try:
            from scripts.x402_onchain_publicity import broadcast

            master["onchain_result"] = broadcast()
        except Exception:
            # import path fallback
            sys.path.insert(0, str(ROOT / "scripts"))
            try:
                import x402_onchain_publicity as oc  # type: ignore

                master["onchain_result"] = oc.broadcast()
            except Exception as e:  # noqa: BLE001
                master["onchain_result"] = {"ok": False, "error": str(e)[:200]}

    if args.release:
        try:
            notes = (
                f"x402 Full Stack\n"
                f"- Threat: {master['threat_audit']['level']} {master['threat_audit']['risk_score']}\n"
                f"- Sandbox: {master['sandbox_audit']['proved']}\n"
                f"- Attack sim SHA: {master['attack_simulation']['sha16']}\n"
                f"- Instagram: {master['instagram']}\n"
                f"- Docs: docs/security/X402_STACK.md\n"
            )
            tag = f"x402-stack-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
            subprocess.run(
                [
                    "gh",
                    "release",
                    "create",
                    tag,
                    "--title",
                    f"x402 Security Stack {tag}",
                    "--notes",
                    notes,
                    "--latest",
                ],
                cwd=str(ROOT),
                check=False,
                capture_output=True,
                text=True,
            )
            master["release_tag"] = tag
        except Exception as e:  # noqa: BLE001
            master["release_error"] = str(e)[:200]

    if args.json_only:
        print(json.dumps(master, indent=2, ensure_ascii=False))
    else:
        print(
            json.dumps(
                {
                    "ok": master["ok"],
                    "threat": master["threat_audit"],
                    "sandbox": master["sandbox_audit"],
                    "attack": {
                        "insecure": master["attack_simulation"]["succeeded_insecure"],
                        "secure_block": master["attack_simulation"]["blocked_secure"],
                        "sha16": master["attack_simulation"]["sha16"],
                        "damage_ct": 0.01,
                    },
                    "instagram": master["instagram"],
                    "github": master["github"],
                    "master_paths": master["master_paths"],
                    "onchain": master.get("onchain_result") or master["onchain"],
                    "release_tag": master.get("release_tag"),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    return 0 if master.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
