# Google One Sicherung — aktiv

**Status:** ACTIVATED  
**Provider:** Google One + Drive  
**Plan:** **aktiv · 5 TB** (Operator-bestätigt)  
**Landing:** https://one.google.com/?g1_landing_page=1  
**Storage:** https://one.google.com/storage  
**Drive-Ordner:** [Fusion_Hero_OS_Sicherung](https://drive.google.com/drive/folders/1a_jWLVX7p5Zw4UCOCbpZjGoAOaj3qUpO)  
**Lokal:** `C:\Users\Admin\.fusion\sicherung`

## Stand

| Punkt | Status |
|-------|--------|
| Google One Plan | **aktiv · 5 TB** |
| Lokale Sicherung | aktiv (`ACTIVATED.json`) |
| Public-safe Snapshots | `~/.fusion/sicherung/snapshots/` |
| Drive-Zielordner | `Fusion_Hero_OS_Sicherung` |
| Secrets in Backup | **ausgeschlossen** |

## Operator

1. ~~Plan prüfen~~ → erledigt (5 TB)
2. Storage-Auslastung gelegentlich prüfen: https://one.google.com/storage
3. Optional: Google Drive for Desktop — Snapshot-Ordner in den Drive-Ordner spiegeln
4. CLI-Snapshot bei Bedarf:

```powershell
python -m fusion_hero_os.core.google_one_sicherung --snapshot
python -m fusion_hero_os.core.google_one_sicherung --status
```

**Policy:** secrets NEVER · freemium=false · pseudo_inhouse_only
