# API-Plane-Trennung — Hyperraum vs. Business

**Stand:** 2026-07-16 · Fusion Hero OS **v10.0.0**  
**Katalog:** `api_planes.yaml`  
**Runtime:** `fusion_hero_os.core.api_plane`  
**HTTP:** `03_Code/Dashboard/api_plane_routes.py`

## Ziel

Perspektivisch **saubere Trennung**:

| Plane | Deutsch | Privacy | Audience |
|-------|---------|---------|----------|
| **hyperraum** | Halbprivater Hyperraum | half_private | Operator (L1 / Mesh) |
| **business** | Klassische Business-API | product | Subunternehmer, Kunden, Ops |

Ein Prozess (Dashboard :8000) darf **beide** hosten — **Semantik, Auth-Posture und Payloads** dürfen sich nicht vermischen.

## Hyperraum (halbprivat)

- Operator-Identität (Rolle, nicht Legal Name)
- Grok Interconnect / Mainframe Control Plane
- Mesh-Koordination, Ascension Consent
- Comädchen, Headset-Relay, Dissertation-as-OS-Organe
- Autoload, Agents, VR, Architecture, x402 (intern)

**Pfade (kanonisch neu):** `/api/hyperraum/*`  
**Legacy (weiterhin hyperraum-klassifiziert):** `/api/grok/*`, `/api/mainframe/*`, `/mainframe/*`, …

## Business (klassisch)

- Businessplan, Energie-Kostenanker
- Subunternehmer API-Token-Preise
- Light Health / Product Metrics

**Pfade (kanonisch neu):** `/api/v1/business/*`  
**Legacy (business-klassifiziert):** `/api/businessplan`, `/api/health`, `/api/metrics`, …

## Regeln

1. **Business** liefert **keine** Operator-Vault-Felder, keine Consent-Bodies, keine Chat-Archive, keine privaten MasterSeed-Shards.
2. **Hyperraum** ist **kein** öffentliches Product-SKU; Auth = operator-local / Mesh.
3. Migration **additiv** (BCG): Legacy-Pfade bleiben; neue Clients nutzen Prefixes.
4. Classifier: `classify_path("/api/…")` — erste/längste Prefix-Regel aus `api_planes.yaml`.

## CLI / HTTP

```powershell
python -m fusion_hero_os.core.api_plane --status
python -m fusion_hero_os.core.api_plane --path /api/v1/business/pricing

# wenn Dashboard laeuft:
curl http://127.0.0.1:8000/api/planes
curl "http://127.0.0.1:8000/api/planes/classify?path=/api/grok/interconnect"
curl http://127.0.0.1:8000/api/v1/business
curl http://127.0.0.1:8000/api/hyperraum/status
```

## Headset multi-layer (Hyperraum organ)

Multi-layer headset is **allowed**; exactly **one** level is **ACTIVE** (loud banner).

| Level | Label | Route |
|-------|--------|--------|
| L1_local | LOCAL PC | host speakers |
| L2_phone | PHONE RELAY | AudioRelay headset |
| L3_comaedchen | COMAEDCHEN | phone + Comet voice |
| L4_hyperraum | HYPERRAUM | phone + control membrane |

```powershell
python -m fusion_hero_os.core.headset_layers --status
python -m fusion_hero_os.core.headset_layers --stack          # arm all
python -m fusion_hero_os.core.headset_layers --active L2      # ACTIVE = phone
python -m fusion_hero_os.core.headset_layers --active L3      # ACTIVE = Comaedchen
powershell -File workstation\headset-layer.ps1 -Active L2
# HTTP: GET /api/hyperraum/headset  POST /api/hyperraum/headset/active?level=L2
```

State: `~/.fusion/headset_layers.json` · Module: `fusion_hero_os.core.headset_layers`

## Roadmap (nicht alles jetzt)

| Stufe | Inhalt |
|-------|--------|
| **A (jetzt)** | Katalog + Classifier + duale Roots + Business-Facades |
| **B** | Middleware: `X-Fusion-Plane` Header + Audit-Log pro Plane |
| **C** | Getrennte API-Keys / Rate-Limits pro Plane |
| **D** | Optional: getrennte Ports oder Edge-Proxy (Business öffentlich, Hyperraum nur Tailscale) |

## Geltung

- Plane-Membrane: **Spezifikation**
- Konkrete Auth-Tokens pro Subunternehmer: **Bedingt** (noch product-config)
- Vollständige Port-Trennung: **Modell** / Roadmap
