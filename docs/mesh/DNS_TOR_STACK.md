# DNS-Stack: Clearnet + MagicDNS + Tor

**Config:** `dns_tor_stack.yaml`  
**Code:** `fusion_hero_os/core/dns_tor_stack.py`  
**Torrc:** `~/.fusion/tor/torrc`  

## Ziel

Ein DNS, das **auch Tor-Protokoll** beherrscht:

| Name / Zone | Weg |
|-------------|-----|
| `*.ts.net` / MagicDNS | Tailscale (`accept-dns`) |
| Clearnet (normal) | Quad9 `9.9.9.9` / Cloudflare `1.1.1.1` |
| `*.onion` | **Tor DNSPort** `127.0.0.1:8853` |
| Apps mit SOCKS | Tor SOCKS5 `127.0.0.1:9050` |

Ports **5353/5354** sind auf Windows oft **mDNS/Bonjour** — daher Fusion: **5454** (Proxy) + **8853** (Tor DNS).

## Architektur

```text
App / OS
   │
   ├─ MagicDNS (Tailscale) ──► 100.x mesh names
   │
   └─ Fusion DNS Proxy :5454
         ├─ *.onion ──► Tor DNSPort :8853 ──► Tor network
         └─ * ────────► 9.9.9.9 / 1.1.1.1
```

Tor **SOCKS** (9050) = volles Tor-Protokoll für Browser/Apps.  
Tor **DNSPort** (8853) = Namensauflösung inkl. `.onion` (AutomapHostsOnResolve).

## Start

```powershell
cd C:\Users\Admin\fusion-hero-os
powershell -File scripts\setup_dns_tor_stack.ps1
# oder:
python -m fusion_hero_os.core.dns_tor_stack --start-tor
python -m fusion_hero_os.core.dns_tor_stack --serve
python -m fusion_hero_os.core.dns_tor_stack --status
python -m fusion_hero_os.core.dns_tor_stack --resolve duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion
```

## Optional: Windows-NIC auf Proxy

Nur mit Admin (ändert System-DNS):

```powershell
# Nur mit Admin — und nur wenn du Port 53 im Proxy willst (listen_port: 53)
# netsh interface ip set dns name="WLAN" static 127.0.0.1
```

Empfehlung: **nicht** global erzwingen — MagicDNS über Tailscale lassen;  
Apps: DNS-Stub `127.0.0.1:5454` bzw. SOCKS `127.0.0.1:9050` für Tor-Protokoll.

## Tailscale Health

„can't reach configured DNS servers“ → Clearnet-Resolver (Quad9) + `tailscale set --accept-dns=true`.  
Mesh-Namen bleiben MagicDNS.

## Policy

- Operator-local (`~/.fusion/tor`)  
- Keine Logs von .onion-Inhalten  
- Kein Exit-Node-Zwang  
- Legitime Privacy / Mesh / Onion-Erreichbarkeit  

**Vermerk:** Tor ist ein Organ — nicht Gott-Layer, nicht Nummer-2-Comädchen; paralleles Privacy-Mesh.
