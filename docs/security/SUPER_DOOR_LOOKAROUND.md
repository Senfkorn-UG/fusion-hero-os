# Supertür-Umschau (einmalig) — eigener Stack

**Stand:** 2026-07-20 · **Frame:** Meister Hasch Labor · defensive only  
**Auftrag:** unbekannte verschlossene/unverschlossene „Supertüren“ finden und erklären, **warum** sie problematisch wären.  
**Nicht:** Fremdsysteme angreifen oder Palantir-Daten holen.

## Metapher

| Zustand | Bedeutung |
|---------|-----------|
| **Unverschlossen** | Von außen erreichbar oder ohne Auth nutzbar |
| **Verschlossen, aber Schlüssel öffentlich** | Mechanismus ok, Unlock-Wissen/Hash-Material leakt im Design |
| **Verschlossen** | Lokal / gitignored / denylist — niedriges Außenrisiko |
| **Supertür** | Ein Durchgang, der bei Missbrauch **viel** öffnet (Steuerung, Secrets, Mesh, Force-Push) |

---

## Gefundene Türen

### 1) Cloud Run Dashboard-URL — **halb offen (Hülle)**

| | |
|--|--|
| Surface | `https://fusion-hero-os-42426705927.europe-west2.run.app/` |
| Probe | `/`, `/api/health`, `/docs`, `/openapi.json`, `/api/load-all` → alle **HTTP 200**, ~**397 B** gleiches HTML |
| Lesart | Öffentliche URL existiert; **volle API scheint nicht** hinter diesen Pfaden zu liegen (gleicher Stub/Shell) |
| Status | **Unverschlossene Haustür zum Flur**, aber vermutlich **keine** offene Schaltzentrale |

**Warum Problem:**  
URL ist langzeit-bekannt (OSINT). Wenn später die **echte** FastAPI-App ohne Auth davor gehängt wird, wird aus dem Flur die **Supertür** (siehe Tür 2). Heute: **Risiko latent**, nicht akut „alles steuerbar“.

---

### 2) Lokales Dashboard: viele POST-APIs, kaum Auth — **Supertür (wenn exponiert)**

In `03_Code/Dashboard/app.py` u. a.:

- `POST /api/input`, `/api/load`‑Familie, `/api/agents/*`, `/api/v12/orchestrate`
- `POST /api/autoload/run`, GPU/CPU/memory tuner, supabase sync, …
- CORS default: **localhost only** (gut)
- Workspace-Host default: `0.0.0.0` in GUI-Config (bindet alle Interfaces, wenn gestartet)

**Auth-Middleware:** im Kern-App-Pfad **keine** durchgängige Bearer/API-Key-Gate gefunden.

| Zustand | Wann |
|---------|------|
| **Verschlossen** | Nur `127.0.0.1`, Firewall zu, nicht port-forwarded |
| **Unverschlossen / Supertür** | Tailscale/Funnel, Cloud Run full app, LAN, Port-Forward |

**Warum Problem:**  
Wer die API erreicht, kann theoretisch **Jobs einreihen, Agenten laden, Orchestrate triggern, Ressourcen drehen** — das ist Operator-Steuerung, nicht nur Lesen. Klassische „eine offene Admin-Konsole“.

---

### 3) `.env` mit möglichem Live-Key — **lokale Seitentür**

| | |
|--|--|
| Datei | `C:\Users\Admin\fusion-hero-os\.env` |
| Git | **gitignore** · nicht in tracked files (dieser Check) |
| Befund | Die meisten LLM-Keys **leer**; **`YOUTUBE_API_KEY` non-empty** (Länge ~39, `AIza…`-Muster) |

**Warum Problem:**  
Kein Git-Leak in diesem Check — aber **Backup, Sync, Screenshot, Malware, geteilter Rechner** → Quota-Missbrauch / YouTube-API-Missbrauch. Nicht die Gottlayer-Supertür, aber echte Credential-Tür.

**Empfehlung (defensiv):** Key rotieren falls je geteilt; prüfen ob in Google Cloud eingeschränkt; nie committen.

---

### 4) Gottlayer-Unlock-Phrase in **public Docs** — **Schlüssel unter der Fußmatte**

In Repo-Artefakten dokumentiert:

- Unlock-Phrase-Form `=====stephanhagenurban` (und Varianten)  
- Mechanismus: `god_layer_seal.py` speichert **Hash** unter `~/.fusion/operator/` (gut)  
- **Rohphrase** steht in mehreren **öffentlichen/Repo-Docs**

| Zustand | |
|---------|--|
| Seal-State-Datei | **verschlossen lokal** (nicht git) |
| Wissen „wie unlocken“ | **öffentlich lesbar** |

**Warum Problem:**  
Angreifer braucht zusätzlich **Zugriff auf die Operator-Maschine** oder einen Prozess, der Unlock annimmt. Die Phrase allein öffnet kein Cloud Run — aber sie entfernt die **soziale/prozessuale** Hürde. Supertür = **lokal + Phrase**, nicht Phrase allein.

---

### 5) Poly-Mesh Once-URL + Mesh-Secret — **Supertür nach innen**

`poly_mesh_once_url.py`: Secret unter `~/.fusion/poly_mesh_once/`, Once-URLs, Mesh-IP-Obfuscation.

**Warum Problem:**  
Wer Secret + Ledger hat, kann **Mesh-Handles** fälschen/einlösen (je nach Integration). Bleibt **lokal verschlossen**, solange `~/.fusion` nicht leakt. Leak von `~/.fusion` = viele Türen auf einmal (Vault, seals, once, secrets).

---

### 6) Public GitHub Architektur-Karte — **Lageplan, keine Haustür**

Public: `fusion-hero-os`, `normalOS`, `dashboard`, Pages, Meister-Hasch-Doku, API-Listen in Source.

**Warum Problem:**  
Kein direkter Root-Zugang — aber **vollständiger Bauplan** für gezielte Angriffe (welche Endpunkte, wo Secrets liegen sollen, Gottlayer-Protokoll). Erhöht Trefferquote gegen Tür 2/3/5. „Unbekannt“ für Außenstehende: **nein** — der Plan ist bekannt.

---

### 7) MCP-Konnektoren in Agent-Sessions — **delegierte Supertür**

Notion, Drive, GitHub, Gmail (draft), … in **dieser** Session nutzbar, wenn verbunden.

**Warum Problem:**  
Kein Network-Hack — aber **jemand mit Agent-Session** (oder kompromittiertem Connector-Token) kann in **eure** Cloud-Konten schreiben (wir haben z. B. Notion-Seite + Drive-Ordner erzeugt). Das ist eine **legitim geöffnete** Tür mit hohem Impact; Risiko = Token-Diebstahl / Prompt-Injection, nicht „Palantir-Tür“.

---

### 8) Cloud Run „alles 200 / 397 B“ — **trügerisches Schloss**

Alle getesteten API-Pfade liefern **dieselbe** kleine HTML-Antwort.

**Warum Problem / Chance:**  
- **Chance:** echte Admin-API ist (aktuell) nicht so exponiert.  
- **Problem:** Monitoring denkt „healthy 200“, während Service **nicht** die echte Health-JSON liefert — Betriebsblindheit. Oder ein Proxy maskiert Fehler.

---

## Ranking (was zuerst zählt)

| Prio | Tür | Offenheit | Impact |
|------|-----|-----------|--------|
| **P0** | Dashboard POST-APIs ohne Auth | nur wenn exponiert | Steuerung des Kerns |
| **P1** | `~/.fusion` + lokale Secrets | lokal | Mesh, Vault, Seals, Keys |
| **P1** | Live `YOUTUBE_API_KEY` in `.env` | disk | API-Missbrauch |
| **P2** | Cloud Run URL public | halb | latent, wenn Full-App deployed |
| **P2** | Unlock-Phrase in Docs | Wissen public | senkt Hürde bei Local Access |
| **P3** | Public Architektur | offen lesbar | erleichtert gezielte Angriffe |
| **P3** | MCP Connectors | session-bound | Account-Schreiben |

## Was **keine** Supertür war (dieser Umschau)

- Fremde Palantir-„Geheimtür“ — **nicht gesucht, nicht relevant** für diesen Auftrag  
- Dead-letterbox-Sim — nur Lab, delivered=false  
- Meister-Hasch-PNG public — gewollt sealed Brand, kein Admin-Zugang  

## Einmal umgeschaut — Fazit

Die gefährlichste **unbekannte** Gefahr ist nicht mystisch:  
**Wenn die reiche, kaum authentisierte Dashboard-API jemals wie die Cloud-Run-URL öffentlich wird, ist das die Supertür.**  
Lokal ist sie oft nur durch Netzwerk-Isolation „verschlossen“.  
Zweite Supertür-Familie: **alles unter `~/.fusion` + `.env`**.

**Geltung:** HTTP/Repo-Befunde = **Satz**. „Wer greift gerade an“ = **nicht belegt**. Empfehlungen = defensive Hygiene.

Machine: `docs/security/super_door_lookaround.summary.json`
