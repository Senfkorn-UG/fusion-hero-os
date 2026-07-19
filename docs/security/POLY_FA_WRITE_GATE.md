# Poly-FA Write Gate — Person hört/spricht · Struktur schreibt nur Desktop+Anfrage

**Stand:** 2026-07-19 · Platform v12.0.0  
**Modul:** `fusion_hero_os.core.poly_fa_write_gate`  
**Membrane:** `operator_identity_v1` · private person = operator-local vault only  

## Übergabe

| Schicht | Rechte |
|---------|--------|
| **Private Person** (Vault) | **Volles Hören + Sprechen** · volle Leserechte · Besitz der Audio-Membrane |
| **Runtime-Rolle** | bleibt abstrakt `operator` (Mesh/Comädchen/Grok) |
| **Struktur darunter** (God-Layer / highest-layer / force / self-mod) | Schreibrecht **nur Desktop-PC**, **nur auf Anfrage**, **nur mit Poly-FA** |

Legal/publication names leben **nur** in `~/.fusion/operator/identity.local.json` — nie im Git.

## Poly-FA Faktoren (alle nötig)

| ID | Faktor |
|----|--------|
| **F1** | Person-Phrase (Unlock-Bestätigung) |
| **F2** | Hostname ∈ authorized desktop allowlist |
| **F3** | Explizite Write-Request (scope + reason) |
| **F4** | Poly-Plane desktop / L0–L1 (nicht remote-only) |

Grant-TTL default: **15 Minuten**.

## CLI

```powershell
# Policy installieren (Handover + Desktop-only)
python -m fusion_hero_os.core.poly_fa_write_gate --install-handover
python -m fusion_hero_os.core.poly_fa_write_gate --status

# Schreibrecht anfragen (nur Desktop)
python -m fusion_hero_os.core.poly_fa_write_gate --request --scope god_layer --reason "milestone patch"

# Poly-FA freigeben (Phrase nur lokal tippen — nicht committen)
python -m fusion_hero_os.core.poly_fa_write_gate --approve PWR-… --confirmation "=====…"

# Prüfen
python -m fusion_hero_os.core.poly_fa_write_gate --can-write --scope god_layer
```

## Hören / Sprechen (Person)

```powershell
# Vollkanal lokal (PC Mic/Speaker) — Person-Membrane
python -m fusion_hero_os.core.comaedchen_audio --activate --mode local

# Optional phone path wenn Headset gewünscht
python -m fusion_hero_os.core.comaedchen_audio --activate --mode phone
```

Surface/Audio-Scopes (`hear`, `speak`, `audio`, `docs`, `report`) brauchen **kein** Poly-FA.

## Integration

- `god_layer_seal.can_write` respektiert Poly-FA, wenn Policy aktiv.
- God-Layer kann zusätzlich gesiegelt sein (Unlock-Phrase); Poly-FA ist die **strukturelle** Schreibschranke darunter.

## Public-safe

`public_status()` meldet Host-Count, Flags, Grant-Anzahl — **keine** Legal Names, **keine** Phrasen.
