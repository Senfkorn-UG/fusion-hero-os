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

Optional: `FUSION_ARCHIV_GPG_PASSPHRASE` setzen (sonst deterministischer Default-Salt).

## Wiederherstellen

```bash
cd archiv/obfuscated/latest
./RECOVER.sh --target restored
```

## Passphrase (Default)

`sha256("fusion-hero-os|archiv|desktop-kpki9e4|example.ts.net")` — Fingerprint steht in `manifest.json` unter `passphrase_sha256`.
