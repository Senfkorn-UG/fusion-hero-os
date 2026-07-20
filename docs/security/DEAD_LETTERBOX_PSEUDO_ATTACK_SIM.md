# Dead-Letterbox Pseudo-Attack Simulation

**Stand:** 2026-07-20 · **Platform:** v12.0.0  
**Frame:** Meister Hasch Labor · Hyper-Modus **OFF**  
**Modul:** `fusion_hero_os.core.dead_letterbox_pseudo_attack_sim`

## Zweck

Die **Simulation operationalisieren**, ohne Realraum-Offensive:

| Begriff | Bedeutung hier |
|---------|----------------|
| **Toter Briefkasten** | Lokale Queue (`DeadLetterbox`) — `delivered=False` immer; **kein** SMTP/IMAP |
| **Pseudoangriff** | Synthetische Probes von retired box IDs gegen **eigene** Lab-Surfaces |
| **Operationalisieren** | Dual-Path Property-Test: insecure mock akzeptiert · secure mock quarantine |

## Policy (hard)

```
sandbox_only = True
real_smtp = False
external_targets = FORBIDDEN
palantir.* / live hosts = denylist reject
hyper_mode = OFF
```

## CLI

```powershell
cd C:\Users\Admin\fusion-hero-os
python -m fusion_hero_os.core.dead_letterbox_pseudo_attack_sim
python -m fusion_hero_os.core.dead_letterbox_pseudo_attack_sim --json
python -m fusion_hero_os.core.dead_letterbox_pseudo_attack_sim --status
```

## Outcomes (erwartet)

| Pfad | Lab-Probe | Externes Target (z. B. Marketing-URL) |
|------|-----------|----------------------------------------|
| **Insecure mock** | `accepted_insecure` | `rejected_forbidden` |
| **Secure mock** | `dead_lettered` | `rejected_forbidden` |

Properties (alle müssen PASS):

1. Denylist blockt Externe auf **beiden** Pfaden  
2. Secure quarantine’t Lab-Probes  
3. Insecure akzeptiert Lab-Probes (Kontrast)  
4. Keine Message mit `delivered=True`  
5. `sandbox_only` · kein reales SMTP  

## Evidence

| Path | Inhalt |
|------|--------|
| `~/.fusion/alerts/dead_letterbox_pseudo_attack_sim.json` | Full report |
| `docs/security/dead_letterbox_pseudo_attack.summary.json` | Public-safe summary |

## Heroischer Bezug

Weg aus `HEROIC_MODE_PATHS.md`:

- **Integritäts-Held** — Property-Tests am eigenen Defender  
- **Hypertarnkappe** — Pseudo-Noise landet in toten Kästen, nicht live  
- **Sisyphos** — wiederholbarer Lab-Lauf (`--seed`)  

## Was bewusst fehlt

- Keine echten Mailaccounts  
- Keine Botnet-/Burner-Infra gegen Dritte  
- Kein Exploit-Payload  
- Kein „Hyper-Angriff“  

**Geltung:** Sandbox-Outcomes = **Satz** (lokal gemessen). Mapping auf reale Ops = **Modell**.
