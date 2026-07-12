# Speicher-Tresor & Auslagerung

> **Stand:** v8.3.0 · 2026-07-11

Verankerung des privaten Auslagerungs-Tresors im Haupt-Repo. Große Binärdaten
gehören weder hierher noch nach GitHub (100-MB-Dateilimit); sie liegen in
Google Drive. Der Tresor hält nur die **maschinenlesbare Provenance**.

## Tresor-Repo

**[95guknow/fusion-hero-vault](https://github.com/95guknow/fusion-hero-vault)** (privat)

- `offload/` — je Lauf: ausgelagerte Datei, SHA-256, Größe, GDrive-Zielpfad
- `dedup/` — je Lauf: entfernte Dubletten + behaltenes Original (mit Hash)

## Werkzeug

`tools/disk_dedup_offload.py` — zerstörungsfreier Dedup- + Offload-Planer:

```bash
python tools/disk_dedup_offload.py --report          # Kategorien-Vermessung
python tools/disk_dedup_offload.py --dedup            # Duplikate finden (dry-run)
python tools/disk_dedup_offload.py --dedup --quarantine   # reversibel in Quarantäne
python tools/disk_dedup_offload.py --offload-plan     # GDrive-Kandidaten
python tools/disk_dedup_offload.py --undo <manifest>  # Quarantäne zurücknehmen
```

## Lauf 2026-07-11 (C: war 91 % voll)

| Aktion | Ergebnis |
|--------|----------|
| Dedup (Hash + Verwendungszweck) | 21 Dubletten entfernt, 0,89 GB (Originale verifiziert erhalten) |
| Offload nach Google Drive | 20 Dateien / 9,99 GB (Installer, Archive, Medien) → `Meine Ablage/FusionHero_Offload/` |
| Cache-Bereinigung | npm-Cache + 0,31 GB alte Temp-Dateien |

**Hinweis:** Nach dem Offload liegen die Dateien zunächst im lokalen
Drive-Streaming-Cache und laden im Hintergrund hoch. Endgültiger lokaler
Platzgewinn erst, wenn im Google-Drive-Client für `FusionHero_Offload/`
„Speicherplatz freigeben" / „Online-only" gewählt wird (nach Upload).

## Ziel-Ordnung (Reihenfolge der Auslagerungs-Priorität)

1. **Dedup** — byte-identische Dubletten (Hash + gleicher Zweck) zuerst
2. **Offline entbehrlich** — Installer/Archive/Medien > 100 MB → GDrive
3. **Wegwerfbar** — Caches/Temp → gelöscht (nie ausgelagert)
4. **Offline nötig** — bleibt lokal (Code, aktive Projekte, Modelle)
