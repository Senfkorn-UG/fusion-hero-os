# Archiv — Obfuscated SHA256+GPG Anker

Nicht committete lokale Dateien werden hier als **obfuskierte SHA256+GPG-Blobs** verankert.

## Struktur

```
archiv/obfuscated/
  latest -> 2026-07-12_HHMMSS/
  recover_obfuscated.py
  <stamp>/
    manifest.json      # SHA256-Register aller Einträge
    RECOVER.sh           # Wiederherstellung
    blobs/*.obf          # Obfuscated GPG payloads
```

## Algorithmus

1. **SHA256** über Rohbytes jeder Datei
2. **GPG symmetric** (AES256, armored)
3. **Obfuscation**: Base64 des Armored-Texts, in 48-Zeichen-Chunks, jedes Chunk reversed + SHA256-Fragment-Prefix
4. **manifest_sha256** über das Eintrags-Register

## Anker erzeugen

```bash
python3 scripts/archiv_anchor_uncommitted.py --include-ignored
```

Optional: `FUSION_ARCHIV_GPG_PASSPHRASE` setzen (sonst neutraler Default-Salt für neue Anker).

## Wiederherstellen

```bash
cd archiv/obfuscated/latest
./RECOVER.sh --target restored
```

## Passphrase-Ableitung

Reihenfolge (der Salt-/Passphrase-Wert wird nie geloggt oder gespeichert — nur
sein sha256-Fingerprint steht in `manifest.json` unter `passphrase_sha256`):

1. `FUSION_ARCHIV_GPG_PASSPHRASE` (verbatim), sonst
2. bei Legacy-Verifikation (pre-v10): `sha256($FUSION_ARCHIVE_LEGACY_SALT)` —
   der historische Salt ist **absichtlich nicht** im Baum hinterlegt und muss
   privat über diese Umgebungsvariable bereitgestellt werden (fail-closed, wenn
   sie fehlt), sonst
3. `sha256("fusion-hero-os|archiv|v10")` — neutraler Default für neue Anker.

### Migration (v10)

Vor v10 erzeugte Anker wurden mit einem historischen Salt verankert, der
Geräte-/Netzwerk-Identifier enthielt. Dieser Wert wurde aus dem öffentlichen
Baum entfernt. Zur Wiederherstellung solcher Altbestände den privaten Salt
setzen und `--legacy-salt` verwenden:

```bash
FUSION_ARCHIVE_LEGACY_SALT='<privater-alt-salt>' \
  ./archiv/obfuscated/<stamp>/RECOVER.sh --target restored
```
