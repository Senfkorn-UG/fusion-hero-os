# Multimodal-Archiv-Protokoll (MAP) v1.0

> **Stand:** v8.3.0 · 2026-07-11 · Code: `fusion_hero_os/core/multimodal_protocol.py`

## Anspruch — und ehrliche Abgrenzung

Ziel ist allgemeine Multimodalität nach dem Muster der großen Provider
(OpenAI, Anthropic, DeepSeek): **ein** Eingang, alle Modalitäten. Die
ehrliche Abgrenzung (Geltungskategorien): dieses Repo **trainiert kein
Modell**. Multimodalität entsteht hier durch drei geprüfte Stufen über den
konfigurierten Fremd-Providern:

| Stufe | Was passiert | Beweis |
|-------|-------------|--------|
| 1 · Durchgehen | Archiv-Sweep über 8 Wurzeln (`04_Buch_und_Archiv`, `06_Master_Archive`, `docs`, `archive`, `memes`, `03_VR_Assets`, `visual_seeds`, `tts`); jede Datei klassifiziert (text/code/data/pdf/image/audio/video/bundle), gehasht, inventarisiert | `test_inventory_covers_archives` |
| 2 · Extrahieren | Lokale Extraktoren je Modalität: Text/Code direkt, PDF via pypdf (Seiten + Zeichenausbeute), Bild via PIL (Format + Dimensionen). Fehlender Extraktor ⇒ ehrlich `extractor_missing`, nie stiller Erfolg | `test_inventory_pdfs_are_actually_extracted` |
| 3 · Routen | Modalität → benötigte Fähigkeit → Provider aus `llm_frameworks.yaml`. Zugang je Framework: `live` (Key-Env gesetzt) oder `configured_no_key`. **Key-Werte werden nie gelesen oder ausgegeben** | `test_provider_status_never_contains_key_values` |

## Fähigkeits-Matrix (deklariert, konservativ)

| Modalität | Fähigkeit | Kandidaten |
|-----------|-----------|-----------|
| text/code/data/pdf | text-generation | grok, claude, gpt, gemini, openrouter, ollama |
| image | vision | grok, claude, gpt, gemini, openrouter |
| audio | audio-transcription | gpt, gemini |
| video | video-understanding | gemini |

Welche Kandidaten **jetzt** bedienbar sind, ist Laufzeitbefund
(`--routing`), kein Dokumentationsversprechen — es hängt allein daran,
welche Key-Umgebungsvariablen gesetzt sind (`.env`, nie committen).

## Wiederholte Läufe

Das Inventar läuft über das Quanten-Wörterbuch
(`multimodal-inventory`, mtime-Signatur): Rescan nur bei Archiv-Änderung.

## Nutzung

```bash
python -m fusion_hero_os.core.multimodal_protocol --routing   # Zugangs-Matrix
python -m fusion_hero_os.core.multimodal_protocol --scan      # Inventar -> docs/v8/multimodal_inventory.json
python -m fusion_hero_os.core.multimodal_protocol --check     # CI-Gate
```

Dashboard: `GET /api/multimodal/inventory` (JSON, inkl. Routing).

## Bewusst offen (nicht behauptet)

- Audio-/Video-Extraktion lokal: kein Extraktor installiert — Einträge
  tragen `extractor_missing`, Routing zeigt den Provider-Pfad.
- `bundle` (zip/tar): wird inventarisiert, nicht entpackt.
- Tatsächliche Provider-Aufrufe (Vision/ASR über die Archive) sind
  Orchestrator-Arbeit (`universal_llm_router`) — das Protokoll liefert
  dafür die maschinenlesbare Arbeitsliste, führt sie aber nicht aus.
