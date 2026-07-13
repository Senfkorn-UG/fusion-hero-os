# Tails als „Tarnkappe" – praktischer Setup-Guide

> **TL;DR** – Tails ist ein Betriebssystem, das du vom USB-Stick startest. Es
> läuft nur im Arbeitsspeicher (RAM), leitet **alles** durch Tor und vergisst
> beim Herunterfahren restlos alles. Perfekt für die Momente, in denen keine
> Spuren auf dem Rechner bleiben sollen. Dein normales System (Haupt-PC mit
> AdGuard Home, Tailscale, Navidrome) bleibt für den Alltag – Tails kommt
> zusätzlich obendrauf, als separater Boot für die sensiblen Momente.

---

## 1. Was ist Tails – ohne Jargon

- **Amnesisch:** Läuft im RAM. Beim Ausschalten ist alles weg – keine
  Verlaufsdaten, keine Cookies, keine Dateien auf dem Rechner. Ausnahme: der
  optionale verschlüsselte Speicherbereich (Persistent Storage) *auf dem Stick*.
- **Alles über Tor:** Jede Internetverbindung läuft automatisch durch das
  Tor-Netzwerk. Programme, die versuchen würden, direkt ins Netz zu gehen,
  werden blockiert.
- **Portabel:** Du steckst den Stick in fast jeden PC, startest davon, arbeitest,
  fährst herunter, ziehst den Stick ab. Der Rechner selbst wird nicht angefasst.
- **Gemacht von einem Non-Profit:** Wird u. a. von Journalist:innen und
  Menschenrechtsaktivist:innen genutzt. Quelloffen, kostenlos.

## 2. Das Zwei-Schichten-Modell (wie Tails zu deinem Setup passt)

| Situation | Werkzeug | Warum |
|---|---|---|
| **Alltag / normale Arbeit** | Haupt-PC mit AdGuard Home + Tailscale + Navidrome | Bequem, schnell, werbe-/trackingfrei, eigener Musik-Server |
| **Tarnkappe-Momente** | Tails-USB booten | Maximale Unsichtbarkeit, keine Spuren, alles über Tor |

Die beiden Welten bleiben **bewusst getrennt** – siehe [Abschnitt 8](#8-kombination-mit-deinem-bestehenden-setup-ehrlich), warum du Tailscale/AdGuard *nicht* in Tails hineinbauen solltest.

---

## 3. Voraussetzungen

- **USB-Stick, mindestens 8 GB** (empfohlen 16 GB+, wenn du Persistent Storage
  nutzen willst). Der Stick wird komplett überschrieben – nichts Wichtiges drauf!
- Ein Rechner zum Erstellen des Sticks (Windows, macOS oder Linux).
- Ein Rechner (kann derselbe sein), der **vom USB-Stick booten** kann. 64-bit
  x86 (Intel/AMD). Apple-Silicon-Macs (M1/M2/M3/…) werden **nicht** unterstützt.

---

## 4. Schritt für Schritt

### 4.1 Image herunterladen

1. Öffne **https://tails.net** (nur diese offizielle Seite verwenden).
2. Wähle den Weg „**Install from …**" passend zu deinem aktuellen System.
3. Lade das **USB-Image** herunter – das ist eine `.img`-Datei
   (`tails-amd64-<version>.img`). Die `.iso` ist nur für DVDs/virtuelle
   Maschinen; für einen USB-Stick brauchst du die `.img`.

### 4.2 Download prüfen (Integrität)

Damit du keine manipulierte Version erwischst, prüfe den Download. Drei Wege,
vom Einfachsten zum Gründlichsten:

- **Am einfachsten:** Auf tails.net gibt es während des Downloads eine
  eingebaute Prüfung direkt im Browser. Einfach folgen.
- **BitTorrent:** Beim Download über den Torrent wird die Integrität
  automatisch geprüft.
- **Für Genaue (OpenPGP):** Signatur `.sig` laden, Tails-Signing-Key
  importieren und prüfen:
  ```bash
  # Key und aktuelle Fingerprint-Angabe von tails.net holen, dann:
  gpg --import tails-signing.key
  gpg --verify tails-amd64-<version>.img.sig tails-amd64-<version>.img
  ```
  Den korrekten Key-Fingerprint immer von der **offiziellen** Tails-Seite
  abgleichen – nicht aus Foren o. Ä.

### 4.3 USB-Stick erstellen

**Variante A – balenaEtcher (Windows / macOS / Linux, am einfachsten):**

1. balenaEtcher von der offiziellen Seite installieren.
2. „Flash from file" → die `.img` wählen.
3. Ziel-USB-Stick auswählen (**genau prüfen, dass es der richtige ist!**).
4. „Flash!" und warten.

**Variante B – `dd` (Linux/macOS, für Terminal-Freund:innen):**

```bash
# 1. Stick einstecken, dann Geräte anzeigen und den Stick sicher identifizieren:
lsblk        # Linux   – z. B. /dev/sdX
# diskutil list   # macOS – z. B. /dev/diskN

# 2. VORSICHT: das falsche Gerät = Datenverlust auf der falschen Platte.
#    /dev/sdX unten durch dein echtes Stick-Gerät ersetzen.
sudo dd if=tails-amd64-<version>.img of=/dev/sdX bs=16M oflag=sync status=progress
sync
```

> ⚠️ `dd` fragt nicht nach. Ein falscher `of=`-Wert überschreibt gnadenlos die
> falsche Festplatte. Lieber zweimal mit `lsblk`/`diskutil` prüfen.

### 4.4 Vom Stick booten

1. Stick einstecken, Rechner neu starten.
2. Direkt beim Start das **Boot-Menü** aufrufen – Taste je nach Hersteller:
   meist `F12`, `F9`, `Esc`, `F2` oder `F10`.
3. Den USB-Stick als Boot-Gerät wählen.
4. Startet Tails nicht? Häufige Ursachen: im BIOS/UEFI **Secure Boot**
   testweise deaktivieren, „Fast Boot" aus, oder ein anderer USB-Port.

### 4.5 Willkommensbildschirm & Tor verbinden

- Sprache/Tastatur wählen.
- Tails verbindet sich mit Tor. In Netzen, die Tor blockieren (Uni, manche
  Länder/Firmen), im Verbindungsassistenten **Tor-Bridges** verwenden.

### 4.6 Optional: Persistent Storage (verschlüsselt)

Wenn du zwischen Sessions Notizen/Dateien behalten willst:

1. **Applications → Tails → Persistent Storage**.
2. Eine **starke Passphrase** setzen (das ist deine LUKS-Verschlüsselung).
3. Auswählen, *was* erhalten bleiben soll (Dokumente, Bookmarks, zusätzliche
   Software, …).
4. Passphrase merken – ohne sie sind die Daten unwiederbringlich weg.

> Persistent Storage ist verschlüsselt, aber **nicht perfekt versteckt**: Bei
> physischem Zugriff ist erkennbar, *dass* ein verschlüsselter Bereich
> existiert. Er schützt den Inhalt, nicht die Tatsache seiner Existenz.

---

## 5. Sicheres Verhalten in Tails (Do / Don't)

- ✅ **Tor Browser so lassen, wie er ist.** Er bringt bereits NoScript und
  Anti-Fingerprinting mit.
- ❌ **Keine Browser-Erweiterungen hinzufügen** (auch kein uBlock Origin) – jede
  Zusatz-Extension macht dich *unterscheidbarer* und schwächt die Anonymität.
  Der Schutz von Tor Browser beruht darauf, dass alle Nutzer:innen möglichst
  gleich aussehen.
- ❌ **Nicht in persönliche Accounts einloggen**, wenn du anonym bleiben willst –
  ein Login verknüpft die Session mit deiner Identität.
- ✅ **Bridges nutzen**, wenn Tor blockiert wird.
- ✅ **MAC-Adressen-Spoofing** ist standardmäßig an – so lassen, außer ein Netz
  verlangt eine registrierte Adresse.
- ✅ **Herunterfahren, wenn fertig** – erst dann ist die Session wirklich weg.

---

## 6. Ehrliche Grenzen

- **Langsamer:** Alles über Tor = mehr Latenz. Für Recherche/Text okay, für
  Streaming/Downloads zäh.
- **Nichts für Gaming/GPU-Last** oder schwere Grafik.
- **Kein Handy:** Tails läuft nicht auf Smartphones/Tablets.
- **Physischer Zugriff/Zwang:** Persistent Storage schützt den Inhalt, aber
  gegen jemanden, der dich zur Passphrase zwingt, hilft Technik nicht.
- **Auffälligkeit:** In manchen Umgebungen fällt Tor-Nutzung als solche auf
  (Bridges mildern das). Anonymität ≠ Unauffälligkeit.

---

## 7. Vergleich: Tails / Whonix / Qubes

| | Tails | Whonix | Qubes OS |
|---|---|---|---|
| **Modell** | Amnesischer Live-USB | Zwei VMs (Gateway + Workstation) | Betriebssystem mit strikter VM-Trennung |
| **Am besten für** | „Benutzen und verschwinden" | Täglicher anonymer Betrieb in VMs | Maximale Kompartimentierung |
| **Spuren** | Keine (RAM-only) | Bleiben in der VM | Pro Qube isoliert |
| **Aufwand** | Gering | Mittel | Hoch |
| **Deine Anforderung** | ✅ Beste Wahl | Alternative für Dauerbetrieb | Wenn du „alles getrennt" willst (kann Whonix enthalten) |

Kurzfazit: **Tails** passt am besten zu „keine Spuren, spontan, mobil".

---

## 8. Kombination mit deinem bestehenden Setup (ehrlich)

Dein Haupt-PC mit **AdGuard Home + Tailscale + Navidrome** ist dein bequemes
Alltagssystem. Tails ist die separate Tarnkappe. **Halte beides getrennt** – und
zwar mit Absicht:

- **Kein Tailscale in Tails:** Tailscale baut ein persistentes, identifizierbares
  Mesh mit stabilen Keys auf. In Tails würde das (a) die Amnesie/Tor-only-Logik
  aushebeln und (b) einen wiedererkennbaren Identifikator schaffen – genau das
  Gegenteil von „keine Spuren". Zudem überlebt es einen Neustart ohnehin nicht.
- **Kein AdGuard-DNS in Tails:** Tails macht DNS bewusst über Tor. Ein eigener
  DNS-Resolver würde den Traffic aus dem Tor-Modell herauslösen und dich
  eindeutiger machen.
- **Navidrome/Musik:** Ein Login in deinen persönlichen Musik-Server verknüpft
  die anonyme Session mit dir. In Tarnkappe-Momenten also weglassen.

**Die richtige „Verzahnung" ist Arbeitsteilung, nicht Vermischung:**

- Alltag, Medien, Heim-Dienste, Fernzugriff → Haupt-PC (AdGuard/Tailscale/Navidrome).
- Sensible Recherche, spurenfreie Sessions → Tails-USB, sauber getrennt.

So bekommst du beides: Komfort *und* eine echte Tarnkappe, ohne dass eins das
andere schwächt.

---

## 9. Weiterführende Links

- Tails offiziell: https://tails.net
- Tails-Dokumentation: https://tails.net/doc
- Tor-Projekt: https://www.torproject.org
- Whonix: https://www.whonix.org
- Qubes OS: https://www.qubes-os.org
