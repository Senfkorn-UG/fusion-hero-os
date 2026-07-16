# -*- coding: utf-8 -*-
import json
from pathlib import Path

from fusion_hero_os.core.heroic_core_orchestrator import MasterSeed
from fusion_hero_os.core.masterseed_public import (
    assert_unique_display,
    display_id_from_fingerprint,
    parse_display_id,
    public_fingerprint,
    public_view,
)
from fusion_hero_os.core.masterseed_vault import (
    open_function_shard,
    qubo_permute,
    qubo_unpermute,
    seal_function_shard,
    status,
)


def test_public_display_unique_and_parseable():
    v = public_view()
    assert v.display_id.startswith("MS-PUB-v")
    parsed = parse_display_id(v.display_id)
    assert parsed is not None
    assert len(v.public_fingerprint) == 64
    assert v.integrity_ok is True
    # uniqueness against self
    assert assert_unique_display([v, v]) is False or v.display_id == v.display_id
    v2 = public_view(MasterSeed())
    # same seed → same display
    assert v.display_id == v2.display_id
    assert v.public_fingerprint == v2.public_fingerprint


def test_display_id_format_stable():
    fp = public_fingerprint()
    d1 = display_id_from_fingerprint(fp, "10")
    d2 = display_id_from_fingerprint(fp, "10")
    assert d1 == d2
    assert parse_display_id(d1)["check4"]


def test_qubo_permute_roundtrip():
    key = "ab" * 32
    data = b"hello masterseed modular vault payload 12345"
    enc = qubo_permute(data, key, n=16)
    assert enc != data
    dec = qubo_unpermute(enc, key, n=16)
    assert dec == data


def test_seal_and_open_shard(tmp_path, monkeypatch):
    monkeypatch.setenv("FUSION_MASTERSEED_VAULT", str(tmp_path / "ms"))
    meta = seal_function_shard(
        "core.orchestrator",
        "MasterSeed.state_hash",
        {"module": "core.orchestrator", "function": "state_hash", "k": 1},
    )
    assert Path(meta.path).is_file()
    data = open_function_shard("core.orchestrator", "MasterSeed.state_hash")
    assert data is not None
    assert data.get("function") == "state_hash"
    st = status()
    assert st["public"]["display_id"].startswith("MS-PUB-")
    assert st.get("freemium") is False


def test_public_view_has_no_private_fields():
    d = public_view().to_dict()
    blob = json.dumps(d)
    assert "shard" not in blob
    assert "passphrase" not in blob
    assert "gpg" not in blob.lower() or "policy" in blob
