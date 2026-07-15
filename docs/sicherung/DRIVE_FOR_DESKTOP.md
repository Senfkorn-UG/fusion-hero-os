# Google Drive for Desktop

**DriveFS running:** True
**Exe:** `C:\Program Files\Google\Drive File Stream\128.0.0.0\GoogleDriveFS.exe`
**My Drive paths:** (noch nicht gemountet — anmelden)
**Cloud folder:** `pending sign-in`
**Local mirror:** `C:\Users\Admin\.fusion\sicherung\drive_mirror\latest_snapshot`
**Drive web:** https://drive.google.com/drive/folders/1a_jWLVX7p5Zw4UCOCbpZjGoAOaj3qUpO

## Setup

```powershell
powershell -File scripts/setup_drive_desktop_phone.ps1
python -m fusion_hero_os.core.google_one_sicherung --desktop --status
```

1. Taskleiste → Google Drive → **anmelden** (5-TB-Konto).
2. Einstellungen → Streamen oder Spiegeln.
3. Ordner `Fusion_Hero_OS_Sicherung` erscheint in My Drive.
4. Skript erneut ausführen → Snapshot in Cloud kopieren.

Install falls fehlend: `winget install Google.GoogleDrive`
