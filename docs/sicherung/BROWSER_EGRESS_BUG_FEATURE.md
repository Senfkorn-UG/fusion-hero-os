# Browser-Egress: Bug und Feature

## Befund

Auf diesem Mainframe ist der **Windows-Standardbrowser** nicht Chrome, sondern:

| Feld | Wert |
|------|------|
| ProgId | `CometHTM` |
| Exe | `C:\Program Files\Perplexity\Comet\Application\comet.exe` |
| Label | **Perplexity Comet** |

Jeder Aufruf von:

- `Start-Process https://…`
- `os.startfile(url)`
- `webbrowser.open(url)`

**tunnelt** die URL durch **Comet**.

## Feature

- Eine **Membran**: alle Agent-Links laufen denselben Browser-Kanal.
- Session/Cookies/Policy zentral.
- Auditable „alles geht hier raus“.
- Passt zur Suite-Idee (ein Business-Browser als Exit).

## Bug

- Google One **5 TB**, Drive, Play Store brauchen oft das **Chrome-Profil** mit dem Google-Konto (`stephan95g@googlemail.com` / Default), nicht die Comet-Session.
- Falscher Account → „nicht eingeloggt“ / anderer Storage / Handy-Links im falschen Kontext.

## Fix (Spezifikation)

| Artefakt | Rolle |
|----------|--------|
| `browser_egress.yaml` | Policy: `active` + URL-Routen |
| `fusion_hero_os/core/browser_egress.py` | Öffnet URL mit gewähltem Profil |
| `google_one_sicherung` | nutzt Egress statt blindem Default |

### Profile

| id | Wirkung |
|----|---------|
| `default` | OS-Default = **Comet-Tunnel** (Feature behalten) |
| `chrome_personal` | Chrome `Default` (Google-One-Konto) |
| `chrome_work` | Chrome `Profile 1` |
| `comet` | Comet erzwingen |
| `edge` | Edge |
| `none` | nichts öffnen |

Aktuell: **`active: chrome_personal`** für Google-Routen; Dashboard darf weiter `default` (Comet) nutzen.

### CLI

```powershell
python -m fusion_hero_os.core.browser_egress --status
python -m fusion_hero_os.core.browser_egress --google-one-bundle
python -m fusion_hero_os.core.browser_egress --url "https://one.google.com/" --profile comet
python -m fusion_hero_os.core.browser_egress --url "http://127.0.0.1:8000" --profile default
```

**Vermerk:** Bug ≡ unkontrollierter Default · Feature ≡ bewusster Tunnel · Steuerung ≡ Egress-YAML.
