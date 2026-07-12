# Controller Aggregat

Die Schnittstelle zwischen Endnutzer und System (`orchestration/controller_aggregate.py`,
GUI-Panel in `app.py`). Kein KI-Modul, keine „Selbstmodifikation" — ein normales,
getestetes Python-Modul mit zwei Aufgaben:

1. **Layer-Registry**: definiert, welche Funktionen auf welcher Stufe implizit
   (automatisch, ohne expliziten Aufruf) geladen gelten.
2. **Owner-Auth**: schützt das Verändern dieser Registry per echtem Passwort-Login.

## Layer-Modell

Je höher die Layer, desto impliziter das Laden:

| Layer | Name | Bedeutung |
|---|---|---|
| 0 | Kernel | Immutable Basis, nie implizit verändert |
| 1 | Werkzeug | Nur auf direkten Aufruf |
| 2 | Vorschlag | Wird vorgeschlagen, nicht automatisch ausgeführt |
| 3 | Kontext | Lädt automatisch bei eindeutigem Kontext |
| 4 | Hintergrund | Läuft automatisch, ohne Nachfrage |
| 5 | Ambient | Vollständig implizit, Teil der Umgebung |

Ein `active_threshold` (Standard: 0) bestimmt, welche registrierten `Capability`-Objekte
gerade als „implizit aktiv" gelten (`layer <= threshold`). Das Ändern des Schwellwerts
und das Registrieren/Entfernen von Capabilities ist **owner-only**.

## Zwei Zonen

- **Öffentlich** (jeder, der die GUI öffnet): Layer-Tabelle lesen, sehen welche
  Capabilities gerade registriert und aktiv sind. Kein Login nötig.
- **Owner-only** (gültiges Session-Token nötig): `register`, `unregister`,
  `set_threshold`.

`bootstrap_register` ist die einzige Ausnahme — sie prüft kein Token, ist aber
ausschließlich für den Anwendungs-Startcode gedacht (in `app.py` werden die
eingebauten Capabilities damit registriert). Sie hängt hinter keinem GUI-Button
und keiner API-Route.

## Owner-Auth: wie es technisch funktioniert

- Erststart: Owner-Bereich zeigt „Owner noch nicht eingerichtet". Ein Passwort
  (≥ 8 Zeichen) wird per `initialize_owner()` gesetzt — **einmalig**. Ein zweiter
  Aufruf schlägt bewusst fehl (`OwnerAuthError`), damit niemand nachträglich die
  Owner-Identität übernehmen kann, solange die Credential-Datei besteht.
- Das Passwort wird nie im Klartext gespeichert: PBKDF2-HMAC-SHA256 mit
  zufälligem 16-Byte-Salt und 600.000 Iterationen (`hashlib.pbkdf2_hmac`,
  Standardbibliothek — keine neue Abhängigkeit).
- Erfolgreicher Login liefert ein zufälliges Session-Token
  (`secrets.token_urlsafe(32)`), serverseitig mit 4-Stunden-Ablauf gehalten.
  Abgelaufene oder unbekannte Tokens werden von `verify()` abgelehnt.
- Die Credential-Datei liegt standardmäßig unter `~/.fusion_hero_os/controller_owner_credentials.json`
  — außerhalb des Repos, damit nie versehentlich ein Passwort-Hash committet
  werden kann. `.gitignore` enthält zusätzlich eine Absicherung falls der Pfad
  je repo-lokal überschrieben wird.
- Fail-closed: jede Owner-Methode ruft zuerst `auth.require(token)` — ohne
  gültiges Token gibt es keine Ausnahmeregel.

## Erststart (lokal, als Owner)

1. `python app.py` starten, GUI öffnet auf `http://localhost:8080`.
2. Oben rechts auf das Hub-Icon klicken oder das Panel „Controller Aggregat"
   aufklappen.
3. Im Owner-Bereich ein Passwort setzen (`Owner einrichten`).
4. Mit diesem Passwort anmelden — danach ist der Implizitheits-Schwellwert
   änderbar.

## Was hier bewusst NICHT passiert

- Kein automatisches Ausführen von Code im Hintergrund nur weil eine Capability
  „implizit aktiv" ist — `load_active()` ist eine explizite, bewusst aufgerufene
  Operation, kein Hintergrund-Daemon.
- Keine Mehrbenutzer-Rechteverwaltung — das ist ein Ein-Personen-System mit genau
  einem Owner-Credential-Satz pro Installation.
- Keine Behauptungen über „Bewusstsein", „Selbstmodifikation" oder autonome
  Weiterentwicklung dieses Moduls. Es ist Code, den ein Mensch schreibt und ändert.
