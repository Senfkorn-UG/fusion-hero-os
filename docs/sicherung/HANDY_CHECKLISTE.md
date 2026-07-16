# Handy-Sicherung (analog Drive for Desktop)

**Gleicher Account wie PC · Google One 5 TB**  
**Cloud-Ordner:** [Fusion_Hero_OS_Sicherung](https://drive.google.com/drive/folders/1a_jWLVX7p5Zw4UCOCbpZjGoAOaj3qUpO)

## Apps

| App | Android | iOS |
|-----|---------|-----|
| Google Drive | [Play](https://play.google.com/store/apps/details?id=com.google.android.apps.docs) | [App Store](https://apps.apple.com/app/google-drive/id507874739) |
| Google One | [Play](https://play.google.com/store/apps/details?id=com.google.android.apps.subscriptions.red) | [App Store](https://apps.apple.com/app/google-one/id1454120035) |

## Schritte (analog Desktop)

| Desktop | Handy (analog) |
|---------|----------------|
| Drive for Desktop starten | Google Drive App öffnen |
| Mit 5-TB-Konto anmelden | **Derselbe** Google-Account |
| Ordner Fusion_Hero_OS_Sicherung | In Drive-App denselben Ordner öffnen |
| Snapshot spiegeln | Optional: Dateien nach `phone_uploads` hochladen |
| (PC-Dateien) | Google One → **Geräte-Backup** (Fotos, Kontakte, SMS/Android) |

## Checkliste

1. [ ] Google Drive App installiert + Login
2. [ ] Google One App installiert + Login (5 TB sichtbar)
3. [ ] Geräte-Backup aktiv: https://one.google.com/about/device-backup
4. [ ] Ordner `Fusion_Hero_OS_Sicherung` in Drive sichtbar
5. [ ] Optional: wichtige Handy-Dateien nach `Fusion_Hero_OS_Sicherung/phone_uploads`
6. [ ] Optional Mesh lokal: `powershell -File workstation/mesh_phone_mirror.ps1`

## Policy

Keine Secrets (.env, API-Keys, private GPG) aufs Handy-Backup laden.
