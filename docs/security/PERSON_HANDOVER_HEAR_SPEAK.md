# Person-Übergabe — volles Hören & Sprechen · Schreib-Struktur

**Stand:** 2026-07-19 · **Status:** ACTIVE (operator-local)  
**Directive:** volle Audio-Membrane an die echte private Person; Struktur-Schreibrecht nur Desktop + Anfrage + Poly-FA

## Was gilt

1. **Hören + Sprechen = voll** für die private Person (lokaler Vault-Bind).  
2. Runtime bleibt `role=operator` — Mesh sieht keine Legal Name.  
3. **Struktur darunter** (God/highest/force/self-mod):  
   - nur **dieser Desktop-PC**  
   - nur **auf Anfrage**  
   - nur mit **Poly-FA** (F1–F4)  
4. Surface/Docs/Report und Audio-Scopes bleiben für die Person offen.

## Operator-local (nie Git)

| Datei | Inhalt |
|-------|--------|
| `~/.fusion/operator/identity.local.json` | Person bind + routing |
| `~/.fusion/operator/poly_fa_write_policy.json` | Desktop allowlist + policy |
| `~/.fusion/operator/poly_fa_requests.json` | offene Requests |
| `~/.fusion/operator/poly_fa_grants.json` | zeitlich begrenzte Grants |
| `~/.fusion/comaedchen_audio.json` | letzte Audio-Aktivierung |

## Public module docs

- `docs/security/POLY_FA_WRITE_GATE.md`  
- `docs/security/OPERATOR_IDENTITY_MEMBRANE.md`  

## Verifikation

```powershell
python -m fusion_hero_os.core.poly_fa_write_gate --status
python -m fusion_hero_os.core.god_layer_seal --status
python -m fusion_hero_os.core.comaedchen_audio --status
python -m fusion_hero_os.core.operator_identity --public
```

## Frame

Hypertarnkappe: Person-Name und Unlock-Phrasen **nicht** in Public-Repos.  
Hyperpanzerknacker: Lab-only — dieses Gate ist defensive Autorisierung, kein Exploit.
