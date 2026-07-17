# -*- coding: utf-8 -*-
"""Beweise fuer das Multimodal-Archiv-Protokoll (Claim MULTIMODAL-PROTOCOL).

Das Protokoll behauptet: Archive werden vollstaendig durchgegangen, jede
Datei klassifiziert, extrahiert (wo lokal moeglich) und auf Provider-
Faehigkeiten geroutet — ohne je Key-Werte zu lesen. Jede dieser Aussagen
wird hier gegen das echte Repo geprueft.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fusion_hero_os.core.multimodal_protocol import (
    ARCHIVE_ROOTS,
    CAPABILITY_BY_MODALITY,
    REPO_ROOT,
    _extract_audio,
    _extract_video,
    build_inventory_cached,
    classify,
    provider_access_status,
    routing_matrix,
    summary,
    to_dict,
)


# ---------------------------------------------------------------------------
# Klassifikation
# ---------------------------------------------------------------------------

def test_classify_covers_core_modalities():
    assert classify(Path("a.md")) == "text"
    assert classify(Path("a.py")) == "code"
    assert classify(Path("a.pdf")) == "pdf"
    assert classify(Path("a.JPG")) == "image"  # case-insensitiv
    assert classify(Path("a.mp3")) == "audio"
    assert classify(Path("a.unbekannt")) == "other"


def test_every_modality_has_a_routing_target():
    modalities = set(classify(Path(f"x{ext}")) for ext in
                     (".md", ".py", ".pdf", ".jpg", ".mp3", ".mp4", ".zip", ".xyz", ".json"))
    assert modalities <= set(CAPABILITY_BY_MODALITY), "Modalitaet ohne Routing-Ziel"


# ---------------------------------------------------------------------------
# Inventar auf dem echten Repo
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def inventory():
    return build_inventory_cached()


def test_inventory_covers_archives(inventory):
    assert len(inventory) > 100, "Archiv-Sweep hat die Archive nicht erfasst"
    modalities = {e.modality for e in inventory}
    assert {"text", "pdf", "image", "code"} <= modalities


def test_inventory_pdfs_are_actually_extracted(inventory):
    pytest.importorskip("pypdf")
    pdfs = [e for e in inventory if e.modality == "pdf"]
    assert len(pdfs) >= 15, "Master-Archiv-PDFs fehlen im Inventar"
    ok = [e for e in pdfs if e.extraction.get("status") == "ok"]
    assert len(ok) == len(pdfs), (
        f"PDF-Extraktion unvollstaendig: "
        f"{[(e.path, e.extraction) for e in pdfs if e.extraction.get('status') != 'ok'][:3]}"
    )
    assert any(e.extraction.get("chars", 0) > 100 for e in ok), \
        "keine einzige PDF lieferte Text — Extraktor liefert nur Huellen"


def test_inventory_images_have_dimensions(inventory):
    pytest.importorskip("PIL")
    images = [e for e in inventory if e.modality == "image"
              and e.extraction.get("status") == "ok"]
    assert images, "kein Bild extrahiert"
    assert all(e.extraction.get("width", 0) > 0 for e in images)


def test_inventory_entries_have_hashes(inventory):
    assert all(len(e.sha256) == 64 for e in inventory)


def test_inventory_is_cached_via_quantum_dictionary(inventory):
    from fusion_hero_os.core.quantum_dictionaries import get_quantum_dictionary
    second = build_inventory_cached()
    assert second is inventory, "unveraendertes Archiv muss aus dem Wörterbuch kommen"
    assert get_quantum_dictionary("multimodal-inventory").stats()["hits"] >= 1


# ---------------------------------------------------------------------------
# Routing + Zugaenge (ohne Key-Werte)
# ---------------------------------------------------------------------------

def test_provider_status_never_contains_key_values(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-GEHEIM-nicht-ausgeben")
    status = provider_access_status()
    serialized = json.dumps(status)
    assert "GEHEIM" not in serialized, "Key-Wert ist in die Ausgabe gelangt!"
    assert status["claude"]["access"] == "live"


def test_routing_reacts_to_key_presence(monkeypatch):
    for var in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    matrix = routing_matrix()
    assert "gpt" in matrix["image"]["configured_no_key"]
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    matrix = routing_matrix()
    assert "gpt" in matrix["image"]["live_providers"]


def test_summary_and_full_dict_serialize(inventory):
    info = summary(inventory)
    assert info["total_files"] == len(inventory)
    assert set(info["routing"]) == set(CAPABILITY_BY_MODALITY)
    json.dumps(to_dict(inventory))


def test_archive_roots_exist():
    existing = [r for r in ARCHIVE_ROOTS if (REPO_ROOT / r).is_dir()]
    assert len(existing) >= 6, f"Archiv-Wurzeln fehlen: {set(ARCHIVE_ROOTS) - set(existing)}"


# ---------------------------------------------------------------------------
# Audio/Video extraction (mutagen-based, honest about unsupported containers)
# ---------------------------------------------------------------------------

def _tiny_wav(path: Path, *, seconds: float = 1.0, channels: int = 1,
              sample_rate: int = 8000) -> None:
    import struct
    import wave

    with wave.open(str(path), "wb") as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(struct.pack("<h", 0) * int(sample_rate * seconds) * channels)


def test_extract_audio_reads_real_wav_metadata(tmp_path):
    pytest.importorskip("mutagen")
    wav = tmp_path / "silence.wav"
    _tiny_wav(wav, seconds=1.0, channels=1, sample_rate=8000)
    result = _extract_audio(wav)
    assert result["status"] == "ok"
    assert result["duration_seconds"] == pytest.approx(1.0, abs=0.05)
    assert result["channels"] == 1
    assert result["sample_rate"] == 8000


def test_extract_video_reports_unsupported_container_honestly(tmp_path):
    pytest.importorskip("mutagen")
    fake_webm = tmp_path / "clip.webm"
    fake_webm.write_bytes(b"not a real webm container")
    result = _extract_video(fake_webm)
    assert result["status"] == "unsupported_container"
    assert result["container"] == "webm"


def test_extract_audio_missing_file_reports_error(tmp_path):
    pytest.importorskip("mutagen")
    result = _extract_audio(tmp_path / "does_not_exist.mp3")
    assert result["status"] == "error"
