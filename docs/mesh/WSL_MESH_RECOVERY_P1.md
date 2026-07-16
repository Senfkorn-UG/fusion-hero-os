# P1 — WSL + mesh-exit Recovery

## Live-Probe 2026-07-15

| Node | Status |
|------|--------|
| `desktop-kpki9e4` | online |
| `fusion-mesh-exit` | **online** (ping DERP fra ~26–168 ms) |
| `redmi-note-13-pro-5g` | online |
| `desktop-kpki9e4-wsl` | offline ~14 h |
| `cs-724978827604-default` | offline ~5 d (exit node idle) |

## WSL

Alle Distros **Stopped**. Startversuch:

```
Wsl/Service/CreateInstance/CreateVm/HCS/0x800705aa
→ Nicht genügend Systemressourcen
```

### Recovery

```powershell
wsl --shutdown
# RAM freigeben (Browser-Tabs, Comet, schwere Jobs)
wsl -d Ubuntu
wsl -e bash -lc "sudo tailscale up --hostname=desktop-kpki9e4-wsl; tailscale status"
```

Falls HCS weiter scheitert: Hyper-V/WSL-Feature prüfen, Reboot, `bcdedit`/Virtualisierung im BIOS.

## GCE / cs-node

`fusion-mesh-exit` lebt — primärer Exit.  
`cs-724978827604-default` 5d offline:

```powershell
# auf GCE oder via gcloud (Operator)
gcloud compute instances start <name> --zone=<zone>
# oder Node aus mesh-registry deprecaten
```

## Bifurkal

Leaf (WSL) → Mainframe (Windows) → Public: erst Leaf wiederbeleben, dann merge-bottom-up.
