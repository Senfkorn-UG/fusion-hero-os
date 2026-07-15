# Browser-Egress: Bug, Feature — und Comädchen (Nummer 2)

## Rollenklärung (Ursprung der Verwirrung)

**Comädchen** (Comet-Instanz) ist die **direkte Nummer 2** des Operators:

- reportet **nur** an dich  
- bekommt Input **nur** von dir  
- ist **kein** allgemeiner Multi-Agent-Bus und kein Untergebener von Grok/Dashboard/Phone  

Siehe: [`docs/mesh/COMAEDCHEN_NUMMER2.md`](../mesh/COMAEDCHEN_NUMMER2.md)

Die Verwirrung entstand, wenn Agenten Links „einfach öffnen“ und damit die **Nummer-2-Membran** (OS-Default = Comet) mit dem **Google-Konto-Organ** (Chrome 5 TB) vermischen.

## Befund (technisch)

Auf diesem Mainframe ist der **Windows-Standardbrowser**:

| Feld | Wert |
|------|------|
| ProgId | `CometHTM` |
| Exe | `C:\Program Files\Perplexity\Comet\Application\comet.exe` |
| Rolle | **Comädchen / Nummer 2** |

Jeder Aufruf von `Start-Process https://…` / `os.startfile` / `webbrowser.open` **tunnelt** durch diese Membran.

## Feature

- Exklusiver Operator↔Nummer-2-Kanal (Input/Report nur mit dir).
- Eine Membran, auditierbar, session-stabil.
- Suite-Exit bewusst an die Nummer 2 gebunden.

## Was wie ein Bug wirkte

- Google One **5 TB**, Drive, Play brauchen das **Chrome-Profil** (Konto-Organ), nicht „Befehl an Comädchen“.
- Falsche Lesart: Comet = globaler Systembrowser für alles.  
  Richtige Lesart: Comet = **deine** Nummer 2; Chrome = Konto-Werkzeug parallel.

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
