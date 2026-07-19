# Operator Identity Membrane — Person herausgelöst aus der Rolle

**Stand:** 2026-07-16 · Fusion Hero OS **v10.0.0**  
**Membrane:** `operator_identity_v1`  
**Modul:** `fusion_hero_os.core.operator_identity`  
**Extraktion:** `python scripts/extract_operator_urban.py`

## These

Der **Operator** ist eine **Rolle** (Autopolitik der Steuerung).  
**Urban** (legal/academic person) ist **nicht** die Rolle — die Person wird aus dem operativen Kernel **herausgelöst**.

| Schicht | Identität | Ort |
|---------|-----------|-----|
| Runtime, Mesh, Comädchen, Grok, GKE | `role=operator` | Code + Config ohne Legal Name |
| Operator-local Vault | optional person bind | `~/.fusion/operator/identity.local.json` |
| Dissertation / Academia / Kompendium | Autor (Publication) | `docs/dissertation/*` (bewusst) |

## Regeln (verbindlich)

1. Operativer Code adressiert **nur** `operator` / `OP_*` — nie Legal Name.
2. Legal/publication name nur in Vault **oder** Publication-Surfaces.
3. Vault ist **nie** git-committed (liegt unter `~/.fusion/`).
4. `FUSION_AUTHOR_BIND=1` (oder vault `bind_to_publication`) nötig, damit Tools den Autor-Namen aus dem Vault lesen.
5. Stage-B Persona-Scanner bleibt aktiv; Legal-Name-Hits in `fusion_hero_os/` sind Extraktions-Regressionen.

## CLI

```powershell
# Status (public-safe)
python -m fusion_hero_os.core.operator_identity --status
python -m fusion_hero_os.core.operator_identity --public

# Vault anlegen (leer, keine Person)
python -m fusion_hero_os.core.operator_identity --init-vault

# Scan + Report
python scripts/extract_operator_urban.py

# Optional: Person nur lokal binden (ENV, nicht committen)
$env:FUSION_AUTHOR_LEGAL_NAME = "…"
$env:FUSION_AUTHOR_PUBLICATION_NAME = "…"
$env:FUSION_AUTHOR_BIND = "1"
python scripts/extract_operator_urban.py --bind-from-env
```

## Comädchen / Mesh

- Comädchen reports **only to** `operator` (role).
- Mesh peers see `operator`, not a legal person string.
- Headset / AudioRelay path is operator membrane, not person-named.

## Person-Übergabe + Poly-FA (2026-07-19)

- **Hören/Sprechen:** voll an private Person (Vault) — `docs/security/PERSON_HANDOVER_HEAR_SPEAK.md`
- **Struktur-Schreibrecht:** nur autorisierter **Desktop**, nur **auf Anfrage**, nur **Poly-FA** — `docs/security/POLY_FA_WRITE_GATE.md`
- Modul: `fusion_hero_os.core.poly_fa_write_gate`

## Dissertation

Monographie und Academia behalten den kanonischen **Autorennamen** (Namenskanon).  
Das ist **Publication**, nicht Runtime. Extraktion ≠ Löschung des Autors im Text.

## Geltung

- Membrane / Rolle: **Spezifikation**
- Vault-Bindung: **Bedingt** (operator-local)
- Dissertation-Autor: **Spezifikation** (Namenskanon) auf Publication-Surface
