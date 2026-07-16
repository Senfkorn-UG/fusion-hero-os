# Meta-OS Defizit-Board (Prioritäten)

**Stand:** 2026-07-15 · ehrliche Operator-Karte  
**Policy:** pseudo_inhouse_only · freemium=false · Gott-Layer gesperrt  

| Prio | Item | Status | Nächster Schritt (Operator) |
|------|------|--------|------------------------------|
| **P0** | Cloud-LLM-Keys + Control live | **BLOCKED** — alle Keys EMPTY; nur ollama+internal | Keys in `.env` füllen → `scripts/fill_llm_keys_checklist.md` |
| **P0** | Tailscale DNS health | **PARTIAL** — accept-dns=true; System-DNS noch Fritzbox; netsh braucht Admin | Elevated: `scripts/set_dns_quad9_elevated.ps1` + [Admin DNS](https://login.tailscale.com/admin/dns) Global 9.9.9.9 / 1.1.1.1 |
| **P1** | WSL online | **BLOCKED** — WSL VMs Stopped; HCS `0x800705aa` (Ressourcen) | WSL neu starten / RAM freigeben / `wsl --shutdown` dann `wsl -d Ubuntu` |
| **P1** | mesh-exit GCE | **PARTIAL** — `fusion-mesh-exit` **ping OK**; `cs-724978827604-default` offline 5d | GCE-Instanz starten oder Node aus Registry streichen |
| **P1** | Google OAuth Drive-API | **OFFEN** — kein `~/.fusion/google-oauth/` | OAuth Client anlegen → credentials.json → Connector-Flow |
| **P2** | K17 / K20 | **DONE** — BEWIESEN + pytest 2026-07-15 | Registry sync erledigt |
| **P2** | GOSSIP-LOGN / BFT | **OFFEN/MODELL** — notes verschärft, nicht mythologisiert | Nur mit Property-Tests schließen |
| **P3** | QUBO-Scheduler / LoRA | **OFFEN** | reale Workloads / Datenpipeline |
| **P3** | PMS Validator | **MODELL** — FAIL_CLOSED ohne Binary/`PMS.yaml` | Claim bleibt fail-closed / Konzeptkatalog |

## Live-Signale (Snapshot)

- Control: `configured_count≈4/34`, `p0_blocker` = empty keys  
- DNS Tor stack: proxy `:5454`, Tor DNS `:8853`, SOCKS `:9050`  
- Tailscale: `desktop-kpki9e4` + `fusion-mesh-exit` + phone online  
- Math: K17/K20 sandbox + pytest grün  

## CLI

```powershell
python -m fusion_hero_os.core.control_instances --status
python -m fusion_hero_os.core.dns_tor_stack --status
tailscale status
tailscale dns status
```

**Vermerk:** Defizite priorisieren ≠ Gott-Layer öffnen. Business Suite Mainframe = finale Instanz nur nach Verifikation.
