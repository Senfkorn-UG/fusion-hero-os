# Archiv — Obfuscated scrypt-KDF + GPG Anker

Nicht committete lokale Dateien werden hier als **obfuskierte GPG-Blobs**
verankert. Der GPG-Passphrase wird ab `archiv_version` 2.0 über eine
versionierte, speicherharte **scrypt**-Schlüsselableitung erzeugt — nicht mehr
über ein schnelles SHA256.

## Struktur

```
archiv/obfuscated/
  latest -> 2026-07-12_HHMMSS/
  recover_obfuscated.py
  <stamp>/
    manifest.json      # Integritaets-Register + KDF-Block (nicht-geheim)
    RECOVER.sh           # Wiederherstellung
    blobs/*.obf          # Obfuscated GPG payloads
```

## Algorithmus

1. **Content-SHA256** über die Rohbytes jeder Datei — reines Integritaets-Hash
   über nicht-geheime Bytes (Funktion `_content_digest`), getrennt von der
   Passphrase-Ableitung.
2. **scrypt-KDF** leitet den GPG-Passphrase aus geheimem Material + einem
   zufälligen Per-Archiv-Salt ab (`n=16384, r=8, p=1, dklen=32`).
3. **GPG symmetric** (AES256, armored) mit dem abgeleiteten Passphrase.
4. **Obfuscation**: Base64 des Armored-Texts, in 48-Zeichen-Chunks, jedes Chunk
   reversed + SHA256-Fragment-Prefix.
5. **manifest_sha256** über das Eintrags-Register (Integritaet).

## Anker erzeugen

```bash
python3 scripts/archiv_anchor_uncommitted.py --include-ignored
```

Optional: `FUSION_ARCHIV_GPG_PASSPHRASE` setzen (sonst neutraler Default-Salt
für neue Anker — nur geringe Entropie, für echte Geheimhaltung die Variable
setzen).

## Wiederherstellen

```bash
cd archiv/obfuscated/latest
./RECOVER.sh --target restored
```

`RECOVER.sh` liest die (nicht-geheimen) KDF-Parameter und den Salt aus
`manifest.json`, leitet mit scrypt denselben Passphrase erneut ab und ruft
`recover_obfuscated.py` auf. Für explizit verschlüsselte Anker muss dasselbe
`FUSION_ARCHIV_GPG_PASSPHRASE` gesetzt sein.

## Passphrase-Ableitung (KDF v2)

Weder das geheime Material noch der abgeleitete Passphrase werden geloggt oder
gespeichert. Im `manifest.json` steht ausschließlich der **nicht-geheime**
`kdf`-Block (Algorithmus, Kostenparameter, zufälliger Salt, Secret-Quelle):

1. Geheim-Material: `FUSION_ARCHIV_GPG_PASSPHRASE` (empfohlen), sonst der
   neutrale Default-Salt `"fusion-hero-os|archiv|v10"`.
2. `passphrase = base64(scrypt(secret, salt=<random 16B>, n, r, p, dklen))`.

Das Integritaets-SHA256 über die Dateibytes ist bewusst getrennt benannt
(`_content_digest` / Manifest-Feld `sha256`), damit klar ist, dass hier keine
Credential-Ableitung stattfindet.

### Migration (v1 → v2)

Vor v10 (bzw. `archiv_version` 1.0) wurde der Passphrase über ein schnelles
`sha256(salt)` abgeleitet und ein historischer Salt enthielt
Geräte-/Netzwerk-Identifier. Beides ist entfernt:

- Neue Anker verwenden ausschließlich die scrypt-KDF (v2).
- Der frühere `--legacy-salt`-Schreib-/Ableitungspfad und die Variable
  `FUSION_ARCHIVE_LEGACY_SALT` existieren nicht mehr.
- Bereits erstellte v1-Anker bleiben über ihr eigenes, mitgeliefertes
  `RECOVER.sh` wiederherstellbar (read-only Altbestand); es wird kein neuer v1-
  Anker mehr geschrieben.
