# Speicher-Tresor & Auslagerung

> **Stand:** v8.3.0 · 2026-07-13

## Globale Speicherpolitik

**Google Drive ist der Standard-Speicherort** fuer Dokumente, Archive, Medien und
alle Daten, die nicht operativ noetig sind. Lokal bleiben Code, laufende Dienste,
Build-Artefakte und aktive Projekte.

| Artefakt | Pfad |
|----------|------|
| Policy (maschinenlesbar) | `workstation/storage_policy.json` |
| Resolver | `tools/storage_policy.py` |
| Anwenden | `workstation/apply-storage-policy.ps1` |
| Mesh-Verankerung | `src/normal_os/integration/mesh_roles.yaml` → `storage` |
| Pfade | `workstation/paths.json` → `storage` |
| Status | `~/.fusion/storage-policy.status.json` |
| GDrive-Ziel | `Meine Ablage/FusionHero_Offload` |

```powershell
# Standard-Auslagerung (Dedup + grosse Dateien > 50 MB)
.\workstation\apply-storage-policy.ps1

# Nur Plan
.\workstation\apply-storage-policy.ps1 -PlanOnly

# Vollsweep (Downloads/Desktop/Ordner)
.\workstation\apply-storage-policy.ps1 -FullSweep
```

`load-env.ps1` setzt `FUSION_GDRIVE_OFFLOAD` automatisch aus der Policy.

---

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

## Lauf 2026-07-13 Vollsweep (alle C:\Users\Admin Ordner)

| Aktion | Ergebnis |
|--------|----------|
| Cache gelöscht | npm, pnpm, puppeteer, Temp (~1,6 GB) |
| Dedup | 5 Gruppen, 0,81 GB (Duplikate in Quarantäne) |
| SD-Modelle | `stable-diffusion-webui/models` → `FusionHero_Offload/SD_models` (~4 GB) |
| LLM-Modelle | `internal_llm/models` → `LLM_models` |
| private-hacking-suite | → `Archives/private-hacking-suite` |
| Grok Sessions/Downloads | → `Archives/grok_*` (~1,5 GB) |
| Downloads + Desktop | → `Downloads_Archive`, `Desktop_Archive` |

**Skript:** `workstation/offload-full-sweep.ps1`

## Lauf 2026-07-13 (C: ~22 GB frei)

| Aktion | Ergebnis |
|--------|----------|
| Dedup | 1 Gruppe, 0,02 GB (Drive-Upload-Temp Dubletten) |
| DCIM Fotos | `Pictures/DCIM` → `Meine Ablage/ALTE_Frau_95g_Photo_Ingestion/DCIM_PC` (~3,9 GB) |
| Gothic Downloads | 6 Dateien / 4,75 GB → `FusionHero_Offload/` |
| **Gesamt ausgelagert** | **~8,7 GB** (lokal gelöscht, in Drive-Streaming-Cache) |

**Skript:** `workstation/offload-to-gdrive.ps1`  
**CLI:** `python tools/disk_dedup_offload.py --offload-execute --offload-min-mb 50`

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
