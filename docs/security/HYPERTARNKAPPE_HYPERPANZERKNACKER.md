# Hypertarnkappe + Hyperpanzerknacker

**Stand:** 2026-07-19 · **Platform:** Fusion Hero OS v12.0.0  
**Scope:** Meister Hasch Sandkasten + public publish surfaces  
**Policy:** lab / Sandkasten · no Realraum vault commit · no third-party attacks

## Kurzdefinition

| Begriff | Rolle | Was es **ist** | Was es **nicht** ist |
|---------|--------|----------------|----------------------|
| **Hypertarnkappe** | Privacy cloak | Öffentliche Oberflächen so halten, dass private Vault-Shards, Keys und Live-Tokens **nie** mitwandern; Hash-only Integrität | Kein vollständiger Tor/Tails-Runtime-Ersatz (dafür: `Tarnkappe_Cloak_Practical_Guide_v8.2.md`, `Tails_as_Ultimate_Tarnkappe_v8.2.md`) |
| **Hyperpanzerknacker** | Lab-only integrity probe | Defensive Property-Checks am **eigenen** Sandkasten-Frame (Hashes, Pfade, Policy-Gates) | Kein Exploit-Toolkit, kein PoC gegen Dritte, kein Realraum-Angriff |

## Hypertarnkappe (cloak)

### Öffentliche Meister-Oberfläche (erlaubt)

- `docs/dissertation/assets/meister_hasch.png` + `.sha256`
- Public frame docs (`MEISTER_HASCH_*.md`)
- Memes / mesh public / android / journal **Kopien desselben** Public-Assets
- Instagram pack captions **ohne** Secrets

### Niemals public (cloak-Pflicht)

- Private MasterSeed shards (`masterseed_vault`, `~/.fusion/vault`)
- `.env*`, API tokens, GPG private keys
- Live Graph tokens (`FUSION_GRAPH_LIVE=1` nur lokal)
- Operator legal-name / PII jenseits der Identity-Membrane

### Operative Checks

Modul: `fusion_hero_os.core.meister_hasch_optimize` → Lens `hypertarnkappe`

- Scan public Meister-Docs auf Private-Key / Token-Muster  
- SHA256-Sidecar = Public-Integrität (kein Vault-Inhalt)  
- Policy-Restatement: private vault never git-public  

## Hyperpanzerknacker (lab probe)

### Erlaubt (Sandkasten)

- Hash/Size-Vergleich Source ↔ Repo-Kopien  
- Prüfung, dass Control-Report PASS + kanonischen Hash trägt  
- Rollen-Frame (Held / Operator / Meister) intakt  
- `sandbox_only=True` hard gate — Modul **wirft**, wenn False  

### Verboten

- Exploit-Payloads, Weaponized PoCs  
- Externe Targets / Facilitator-Mainnet-Angriffe  
- „Knacken“ realer Systeme außerhalb des autorisierten Labs  

Gleiche Geisteshaltung wie `x402_sandbox_audit.py`:

> local, defensive, authorized lab only · no_external_targets

### Operative Checks

Modul-Lens `hyperpanzerknacker` — siehe Summary:

- `docs/dissertation/meister_hasch_optimize.summary.json`
- `docs/security/meister_hasch_optimize.summary.json`

## Zusammenspiel mit Fable5 / Mythos5

| Lens | Organ | Ehrlichkeit |
|------|--------|-------------|
| **Fable5** | Engineering integrity | Checkliste auf beobachtetem Repo-Zustand |
| **Mythos5** | Narrative / Geltung | Sinn-Organ derselben Assessment-Basis — **kein** unabhängiger Zweit-Reviewer |
| **Hypertarnkappe** | Privacy | Public surface cloak |
| **Hyperpanzerknacker** | Integrity probe | Lab property tests only |

Siehe: `docs/dissertation/MEISTER_HASCH_FABLE5_MYTHOS5.md`  
Honesty-Vorbild: `docs/meta_neural/IMPROVEMENT_BACKLOG_v10.md` (same underlying model).

## CLI

```bash
python scripts/meister_hasch_fable_mythos_optimize.py
python scripts/meister_hasch_fable_mythos_optimize.py --json
python scripts/meister_hasch_fable_mythos_optimize.py --status-only
```

## Frame (unverändert)

Labor / Sandkasten: Held + Operator ↔ Meister · reiner Erkenntnisgewinn · **kein** Realraum-Commit privater Vault-Shards.
