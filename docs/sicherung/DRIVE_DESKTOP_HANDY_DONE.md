# Drive for Desktop + Handy — ausgeführt

## Desktop (erledigt)
- Google Drive for Desktop **läuft** (Account angemeldet)
- Spiegel-Modus: **Desktop + Documents + Downloads** (kein G:-Laufwerk)
- Sicherungsordner: `Documents\Fusion_Hero_OS_Sicherung`
- Snapshot kopiert + in Upload-Warteschlange (`queued_uploads` aktiv)
- Desktop-Hinweis: `Desktop\Fusion_Hero_OS_Sicherung\HANDY_JETZT.txt`

## Handy (analog — auf dem Gerät)
1. Google Drive + Google One Apps
2. Gleicher Account (5 TB)
3. Geräte-Backup AN
4. In Drive: **Computer → dieses Gerät → Documents → Fusion_Hero_OS_Sicherung**
5. Uploads nach `phone_uploads`

## CLI
```powershell
python -m fusion_hero_os.core.google_one_sicherung --snapshot --desktop --phone
powershell -File scripts\setup_drive_desktop_phone.ps1
```
