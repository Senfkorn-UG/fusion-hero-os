# -*- coding: utf-8 -*-
"""
x402 audit — on-chain publicity attestation (self-message).

Sends a 0-value transaction with UTF-8 data payload containing the heroic
security message + GitHub 95guknow link. Optional tiny native tip amount.

Requires:
  FUSION_PUBLICITY_PRIVATE_KEY  (hex, no 0x required) — operator wallet
  FUSION_PUBLICITY_RPC          (default: Base mainnet public RPC)

Never attacks facilitators. Never drains third parties.
Gas is paid by the operator (will exceed 0.01 ct — the 0.01 ct is the
declared public *damage envelope* of the lab story, not gas).

Usage:
  python scripts/x402_onchain_publicity.py --dry-run
  python scripts/x402_onchain_publicity.py --broadcast
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MSG_PATH = ROOT / "docs" / "security" / "X402_ONCHAIN_PUBLICITY_MESSAGE.txt"
OUT_DIR = Path.home() / ".fusion" / "alerts"

# Base mainnet — cheap data txs; override via env
DEFAULT_RPC = os.environ.get(
    "FUSION_PUBLICITY_RPC",
    "https://mainnet.base.org",
)
DEFAULT_CHAIN_ID = int(os.environ.get("FUSION_PUBLICITY_CHAIN_ID", "8453"))  # Base


def _load_dotenv() -> None:
    for rel in (".env", ".env.local"):
        p = ROOT / rel
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and not (os.environ.get(k) or "").strip():
                os.environ[k] = v


def build_payload() -> bytes:
    text = MSG_PATH.read_text(encoding="utf-8") if MSG_PATH.is_file() else ""
    # attach fresh sim hash if present
    sim = Path.home() / ".fusion" / "alerts" / "x402_sandbox_attack_sim.json"
    if sim.is_file():
        try:
            sha = json.loads(sim.read_text(encoding="utf-8")).get("sha16", "")
            text += f"\nFresh attack-sim SHA16: {sha}\n"
        except Exception:
            pass
    text += f"\nAttestedAtUTC: {datetime.now(timezone.utc).isoformat()}\n"
    text += "GitHub: https://github.com/95guknow/fusion-hero-os\n"
    return text.encode("utf-8")


def dry_run() -> dict:
    data = build_payload()
    return {
        "mode": "dry_run",
        "chain_id": DEFAULT_CHAIN_ID,
        "rpc": DEFAULT_RPC,
        "data_bytes": len(data),
        "data_sha256": hashlib.sha256(data).hexdigest(),
        "data_preview": data.decode("utf-8")[:500],
        "data_hex_prefix": "0x" + data.hex()[:80] + "...",
        "note": "Set FUSION_PUBLICITY_PRIVATE_KEY and run --broadcast to publish on-chain",
    }


def broadcast() -> dict:
    _load_dotenv()
    raw = (
        os.environ.get("FUSION_PUBLICITY_PRIVATE_KEY")
        or os.environ.get("ETH_PRIVATE_KEY")
        or os.environ.get("BASE_PRIVATE_KEY")
        or ""
    ).strip()
    if not raw:
        return {
            "ok": False,
            "error": "missing FUSION_PUBLICITY_PRIVATE_KEY (or ETH_PRIVATE_KEY)",
            "dry_run": dry_run(),
        }
    if raw.startswith("0x"):
        raw = raw[2:]

    try:
        from eth_account import Account
        import urllib.request
    except ImportError as e:
        return {"ok": False, "error": f"import:{e}"}

    # Minimal JSON-RPC eth_sendRawTransaction without full web3 if needed
    try:
        from web3 import Web3
    except ImportError:
        # install hint
        return {
            "ok": False,
            "error": "web3 not installed — run: pip install web3",
            "dry_run": dry_run(),
        }

    w3 = Web3(Web3.HTTPProvider(DEFAULT_RPC, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        return {"ok": False, "error": f"rpc_unreachable:{DEFAULT_RPC}"}

    acct = Account.from_key(bytes.fromhex(raw))
    data = build_payload()
    nonce = w3.eth.get_transaction_count(acct.address)
    # 0-value self-tx with data (publicity attestation)
    tx = {
        "chainId": DEFAULT_CHAIN_ID,
        "nonce": nonce,
        "to": acct.address,
        "value": 0,
        "data": data,
        "gas": 100000 + (len(data) // 32) * 1000,
        "maxFeePerGas": w3.to_wei("0.05", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("0.01", "gwei"),
        "type": 2,
    }
    # estimate gas if possible
    try:
        est = w3.eth.estimate_gas(
            {"from": acct.address, "to": acct.address, "value": 0, "data": data}
        )
        tx["gas"] = int(est * 1.2)
    except Exception as e:  # noqa: BLE001
        tx["gas_estimate_error"] = str(e)[:120]

    try:
        base = w3.eth.gas_price
        tx["maxFeePerGas"] = int(base * 2)
        tx["maxPriorityFeePerGas"] = min(int(base), w3.to_wei("0.1", "gwei"))
    except Exception:
        pass

    signed = acct.sign_transaction(tx)
    raw_tx = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction", None)
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    h = tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)
    if not h.startswith("0x"):
        h = "0x" + h

    explorer = f"https://basescan.org/tx/{h}"
    result = {
        "ok": True,
        "mode": "broadcast",
        "chain": "base",
        "chain_id": DEFAULT_CHAIN_ID,
        "from": acct.address,
        "to": acct.address,
        "value_wei": 0,
        "tx_hash": h,
        "explorer": explorer,
        "data_bytes": len(data),
        "data_sha256": hashlib.sha256(data).hexdigest(),
        "github": "https://github.com/95guknow/fusion-hero-os",
        "public_damage_envelope": "0.01 ct notional (lab) — gas paid separately by operator",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "x402_onchain_publicity.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    (ROOT / "docs" / "security" / "x402_onchain_publicity.summary.json").write_text(
        json.dumps(
            {
                "tx_hash": h,
                "explorer": explorer,
                "chain": "base",
                "github": result["github"],
                "data_sha256": result["data_sha256"],
                "generated_at": result["generated_at"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    md = OUT_DIR / "X402_ONCHAIN_PUBLICITY.md"
    md.write_text(
        "\n".join(
            [
                "# x402 On-Chain Publicity Attestation",
                "",
                f"**TX:** [{h}]({explorer})",
                f"**Chain:** Base ({DEFAULT_CHAIN_ID})",
                f"**From/To:** `{acct.address}` (self)",
                f"**GitHub:** https://github.com/95guknow/fusion-hero-os",
                f"**Data SHA256:** `{result['data_sha256']}`",
                "",
                "Heroic message embedded in tx input data (UTF-8).",
                "Public damage envelope of lab story: **0,01 ct** (notional, dormant lab wallet).",
                "No third-party funds moved. Security audit attestation only.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    result["evidence_paths"] = [
        str(OUT_DIR / "x402_onchain_publicity.json"),
        str(md),
        str(ROOT / "docs" / "security" / "x402_onchain_publicity.summary.json"),
    ]
    return result


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="x402 on-chain publicity attestation")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--broadcast", action="store_true")
    args = ap.parse_args()
    if args.broadcast:
        r = broadcast()
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0 if r.get("ok") else 1
    print(json.dumps(dry_run(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
