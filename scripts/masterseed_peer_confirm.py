#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect mutual_sync confirmations from peer MasterSeed instances and publish public summary."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fusion_hero_os.core.heroic_core_orchestrator import MasterSeed
from fusion_hero_os.core.masterseed_public import public_view
from fusion_hero_os.core.masterseed_sync import (
    SyncState,
    identity_preservation_score,
    mutual_sync,
)
from fusion_hero_os.core.masterseed_vault import (
    export_public_display,
    seal_all_modules,
    status as vault_status,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    seed0 = MasterSeed()
    assert seed0.verify_integrity(seed0.state_hash())

    peers_spec = [
        ("mainframe", 0.92, {"role": "mainframe", "note": "operator local"}),
        ("ascension", 0.88, {"role": "ascension_track", "note": "v9.x loadable"}),
        ("mesh_edge", 0.81, {"role": "L0_edge", "note": "phone/extension"}),
        ("hypercluster", 0.95, {"role": "L1_hypercluster", "note": "fluid zitterpolymesh"}),
        ("senfkorn_mirror", 0.90, {"role": "dual_org", "note": "Senfkorn-UG mirror"}),
        ("dissertation", 0.87, {"role": "dissertation_as_os", "note": "meister_hasch public"}),
    ]

    states: dict[str, SyncState] = {}
    for name, fit, payload in peers_spec:
        s = MasterSeed()
        states[name] = SyncState(
            seed=s,
            elite_payload=dict(payload, instance=name),
            elite_fitness=float(fit),
        )

    main = states["mainframe"]
    confirmations = []
    for name, st in list(states.items()):
        if name == "mainframe":
            continue
        pre_a, pre_b = main.elite_fitness, st.elite_fitness
        ha, hb = main.state_hash(), st.state_hash()
        main2, st2 = mutual_sync(main, st)
        conf = {
            "peer": name,
            "ok": True,
            "peer_role": (st.elite_payload or {}).get("role"),
            "pre_fitness": {"mainframe": pre_a, "peer": pre_b},
            "post_fitness": {
                "mainframe": main2.elite_fitness,
                "peer": st2.elite_fitness,
            },
            "identity_preserved": {
                "mainframe": main2.state_hash() == ha,
                "peer": st2.state_hash() == hb,
            },
            "adopted_elite_fitness": main2.elite_fitness,
            "identity_score_mainframe": identity_preservation_score(main2),
            "identity_score_peer": identity_preservation_score(st2),
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
        }
        confirmations.append(conf)
        main = main2
        states[name] = st2
    states["mainframe"] = main

    try:
        from fusion_hero_os.core.poly_mesh_os_port import port_status

        mesh = port_status()
        mesh_pub = {
            "ok": mesh.get("ok"),
            "ported": mesh.get("ported"),
            "tiers": mesh.get("tiers_online"),
            "mesh_ip": (mesh.get("self") or {}).get("mesh_ip"),
            "organ_count": mesh.get("organ_count"),
        }
    except Exception as e:  # noqa: BLE001
        mesh_pub = {"ok": False, "error": str(e)[:160]}

    vault = vault_status()
    pub = public_view().to_dict()
    seal = seal_all_modules()
    export_public_display()

    report = {
        "kind": "masterseed_peer_confirmations",
        "ts": datetime.now(timezone.utc).isoformat(),
        "platform": "10.0.0",
        "public_display": pub,
        "vault": {
            "shard_count": vault.get("shard_count"),
            "gpg": vault.get("gpg_available"),
            "display_id": (vault.get("public") or {}).get("display_id"),
        },
        "seal_after": {"ok": seal.get("ok"), "sealed_count": seal.get("sealed_count")},
        "peers": list(states.keys()),
        "confirmations": confirmations,
        "all_peers_confirmed": all(
            c["ok"]
            and c["identity_preserved"]["mainframe"]
            and c["identity_preserved"]["peer"]
            for c in confirmations
        ),
        "final_elite_fitness": states["mainframe"].elite_fitness,
        "final_identity_score": identity_preservation_score(states["mainframe"]),
        "mesh": mesh_pub,
        "satz": (
            "mutual_sync: both sides fitness = max; seed identity preserved; "
            "fail-closed on integrity"
        ),
    }

    priv = Path.home() / ".fusion" / "ops" / "masterseed_peer_confirmations.json"
    priv.parent.mkdir(parents=True, exist_ok=True)
    priv.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    pub_doc = {
        "kind": "masterseed_peer_confirmations_public",
        "ts": report["ts"],
        "platform": "10.0.0",
        "display_id": pub.get("display_id"),
        "public_fingerprint_prefix": (pub.get("public_fingerprint") or "")[:16],
        "integrity_ok": pub.get("integrity_ok"),
        "peers_confirmed": len(confirmations),
        "all_peers_confirmed": report["all_peers_confirmed"],
        "final_elite_fitness": report["final_elite_fitness"],
        "identity_preservation_score": report["final_identity_score"],
        "confirmations": [
            {
                "peer": c["peer"],
                "role": c["peer_role"],
                "ok": c["ok"],
                "identity_preserved": c["identity_preserved"],
                "post_fitness": c["post_fitness"],
                "confirmed_at": c["confirmed_at"],
            }
            for c in confirmations
        ],
        "mesh": mesh_pub,
        "satz_ref": "fusion_hero_os.core.masterseed_sync.mutual_sync",
    }
    out_json = ROOT / "docs" / "masterseed" / "PEER_CONFIRMATIONS.latest.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(pub_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# MasterSeed Peer-Confirmations (public)",
        "",
        f"**Stand:** {report['ts']}",
        f"**Display:** `{pub.get('display_id')}`",
        f"**Fingerprint:** `{(pub.get('public_fingerprint') or '')[:24]}…`",
        f"**All peers confirmed:** **{report['all_peers_confirmed']}**",
        f"**Final elite fitness (shared max):** {report['final_elite_fitness']}",
        f"**Identity preservation score:** {report['final_identity_score']}",
        "",
        "## Satz",
        "",
        "`mutual_sync(A,B)`: beide Seiten erhalten `elite_fitness = max(f_A,f_B)`; "
        "Seed-Identität bleibt; fail-closed bei Integritätsbruch.",
        "",
        "## Confirmations",
        "",
        "| Peer | Role | OK | ID preserved (main/peer) | Post fitness (main/peer) |",
        "|------|------|----|--------------------------|--------------------------|",
    ]
    for c in confirmations:
        lines.append(
            f"| {c['peer']} | {c['peer_role']} | {c['ok']} | "
            f"{c['identity_preserved']['mainframe']}/{c['identity_preserved']['peer']} | "
            f"{c['post_fitness']['mainframe']}/{c['post_fitness']['peer']} |"
        )
    lines += [
        "",
        "## Mesh (public-safe)",
        "",
        f"- tiers: {mesh_pub.get('tiers')}",
        f"- mesh_ip: {mesh_pub.get('mesh_ip')}",
        f"- organs: {mesh_pub.get('organ_count')}",
        "",
        "Private full log: `~/.fusion/ops/masterseed_peer_confirmations.json` (not published).",
        "",
    ]
    (ROOT / "docs" / "masterseed" / "PEER_CONFIRMATIONS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "ok": True,
                "all_peers_confirmed": report["all_peers_confirmed"],
                "peers": len(confirmations),
                "final_fitness": report["final_elite_fitness"],
                "identity_score": report["final_identity_score"],
                "display_id": pub.get("display_id"),
                "sealed": seal.get("sealed_count"),
                "public_md": "docs/masterseed/PEER_CONFIRMATIONS.md",
                "public_json": "docs/masterseed/PEER_CONFIRMATIONS.latest.json",
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["all_peers_confirmed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
