# Google One Sicherung — aktiv

**Status:** ACTIVATED (`2026-07-15T15:11:10.440910+00:00`)
**Provider:** Google One + Drive
**Landing:** https://one.google.com/?g1_landing_page=1
**Storage:** https://one.google.com/storage
**Drive-Ordner:** [Fusion_Hero_OS_Sicherung](https://drive.google.com/drive/folders/1a_jWLVX7p5Zw4UCOCbpZjGoAOaj3qUpO)
**Lokal:** `C:\Users\Admin\.fusion\sicherung`

## Operator (Browser)

1. https://one.google.com/?g1_landing_page=1 — Plan / Geräte-Backup prüfen
2. https://one.google.com/storage — Speicherplatz prüfen
3. Drive-Ordner `Fusion_Hero_OS_Sicherung` für public-safe Snapshots
4. Google Drive for Desktop: optional Ordner spiegeln

## CLI

```powershell
python -m fusion_hero_os.core.google_one_sicherung --activate
python -m fusion_hero_os.core.google_one_sicherung --snapshot
python -m fusion_hero_os.core.google_one_sicherung --status
```

**Policy:** secrets NEVER · freemium=false · pseudo_inhouse_only
