# Layered Resource Guardian — Schnittstellen-Spezifikation

> **Stand:** 2026-07-13 · **Status:** Spezifikation + API/GUI implementiert,
> Kernlogik-Modul noch zu implementieren.

**Zustaendigkeitstrennung (IDE/GUI):** Die eigentliche Probing-/Schwellenwert-/
Eskalationslogik (`src/normal_os/core/layered_resource_guardian.py`) wird
lokal ueber Windows-Coding-Tools implementiert, nicht ueber diese Session.
Dieses Dokument ist der Vertrag zwischen diesem Modul und der bereits
implementierten API (`resource_guardian_routes.py`) + GUI (`/resources`).
Die API ruft `get_layered_resource_guardian()` per try/except-Import auf und
meldet "nicht verfuegbar", solange das Modul nicht existiert — GUI und API
funktionieren also schon jetzt, laufen aber erst mit Daten, sobald das
Kernmodul lokal ergaenzt wird.

## Ziel

Getakteter Selbstcheck von Temperatur, Kuehlung/Luefter, CPU, GPU und SSD in
drei Layern (sofort/kurzfristig/mittelfristig), mit der Konsequenz, dass
Prozesse (Lastverteilung, Performance-Ratio) oder Dokumente (SSD-Offload)
sich an die aktuelle Ressourcenlage anpassen. Vor jedem Layer-Aufstieg ein
Kreuz-Check: alle 5 Ressourcen frisch neu proben, nicht nur die ausloesende.

## Wiederverwendung (nicht neu erfinden)

Diese Funktionen/Klassen existieren bereits in `src/normal_os/core/` und
sollen importiert, nicht dupliziert werden:

| Ressource | Funktion | Datei |
|---|---|---|
| CPU (Last, Takt, Temperatur) | `probe_cpu()` | `cpu_adaptive_tuner.py` |
| GPU (VRAM, Compute, System-RAM) | `probe_gpu_memory()` | `gpu_memory_allocator.py` |
| RAM | `probe_ram()` | `memory_guard.py` |
| Reaktion CPU/GPU/SSD gekoppelt | `get_resource_coupler().couple_once()` | `resource_coupler.py` |
| CPU-Tuning anwenden | `get_cpu_tuner()` | `cpu_adaptive_tuner.py` |
| GPU-Allocator | `get_gpu_allocator()` | `gpu_memory_allocator.py` |

**Neu zu probende Ressourcen** (existieren noch nicht als Probe-Funktion):

- **Kuehlung/Luefter**: `psutil.sensors_fans()` (Linux; unter Windows liefert
  psutil keine Luefterdaten — Best-Effort via WMI `Win32_Fan`-Abfrage
  analog zum bestehenden WMI-Thermalzone-Fallback in `probe_cpu()`
  moeglich, ist aber auf vielen Boards leer/unzuverlaessig). Ehrlicher
  Status: wenn keine Quelle liefert, `None` zurueckgeben statt zu raten.
- **SSD**: `psutil.disk_usage(path)` fuer freien Speicher (portabel,
  zuverlaessig). Fuer die kategorisierte Aufschluesselung im
  Mittelfristig-Layer: `tools/disk_dedup_offload.py --report` als
  Subprocess aufrufen (bereits vorhanden, sicher, non-destruktiv).

## Drei Layer

Ein Tick-basierter Hintergrund-Loop (z.B. `tick_seconds=10`), Layer feuern
nach Vielfachen des Basis-Ticks:

### Layer "sofort" (jeder Tick, ~10s)
- Probes: `probe_cpu()`, `probe_gpu_memory()` (billig, hochfrequent)
- Breach-Kriterium: `cpu_temp_c >= 75` ODER `cpu_load_pct >= 85` ODER
  `vram_util_pct >= 90`
- Aktion bei Breach: `get_resource_coupler().couple_once()` (bereits
  vorhandene Reaktionslogik, keine neue Aktion noetig)

### Layer "kurzfristig" (alle N Ticks, z.B. N=12 -> ~2 min)
- Probes: neu `probe_fans()`, neu `probe_ssd()` (freier Speicher), plus
  gleitender Mittelwert der letzten Sofort-Snapshots (Trend statt Einzelwert)
- Breach-Kriterium: `avg_cpu_temp_c (letzte 12 Sofort-Samples) >= 72` ODER
  `ssd_free_pct < 15` ODER Fan-Daten verfuegbar UND Drehzahl faellt trotz
  steigender Temperatur (Luefter-Ausfall-Verdacht)
- Breach-Streak: pro Ressource mitzaehlen; erst ab `streak >= 3`
  (~6 min sustained) wird eine Eskalation zum Mittelfristig-Layer erwogen —
  einzelne Ausreisser loesen NICHTS aus.

### Layer "mittelfristig" (alle M Ticks, z.B. M=180 -> ~30 min, ODER
vorzeitig durch eskalierten Kreuz-Check aus "kurzfristig")
- Probes: alle 5 Ressourcen frisch, plus `disk_dedup_offload.py --report`
  bei SSD-Verdacht
- Aktion "Prozesse umstrukturieren": `get_cpu_tuner()`/`get_gpu_allocator()`
  Zielwerte dauerhaft anpassen (nicht nur einmalig wie im Sofort-Layer)
- Aktion "Dokumente umstrukturieren": bei sustained SSD-Knappheit
  `disk_dedup_offload.py --offload-plan` ausfuehren (erstellt nur einen
  Plan, keine destruktive Aktion — matcht die Sicherheitsphilosophie des
  bestehenden Tools) und das Ergebnis im Status/History festhalten.

## Kreuz-Check bei Layer-Aufstieg

Vor JEDEM Aufstieg (sofort→kurzfristig-Eskalation, kurzfristig→
mittelfristig-Eskalation) werden ALLE 5 Ressourcen frisch neu geprobt
(nicht nur die ausloesende), UND es wird verlangt, dass entweder (a) die
Breach-Streak-Schwelle erreicht ist, ODER (b) mindestens eine zweite
Ressource den jeweiligen Layer-Schwellenwert ebenfalls verletzt
(Korrelation statt Einzelsignal). Das Ergebnis dieses Kreuz-Checks wird im
`LayerCheckResult.cross_check`-Feld protokolliert (welche Ressourcen
mitgeprueft wurden, was das Ergebnis war), damit Eskalationen nachvollziehbar
sind.

## Erwartete Python-Schnittstelle (`src/normal_os/core/layered_resource_guardian.py`)

```python
def get_layered_resource_guardian() -> "LayeredResourceGuardian": ...

class LayeredResourceGuardian:
    def start(self) -> bool: ...   # Hintergrund-Thread starten (wie ResourceCoupler.start_background)
    def stop(self) -> None: ...

    def get_status(self) -> dict:
        """
        {
          "running": bool,
          "tick_count": int,
          "layers": {
            "sofort":       {"last_run": iso8601, "interval_s": 10,  "last_breach": bool},
            "kurzfristig":  {"last_run": iso8601, "interval_s": 120, "last_breach": bool,
                              "breach_streaks": {"cpu": int, "gpu": int, "ram": int, "fans": int, "ssd": int}},
            "mittelfristig":{"last_run": iso8601, "interval_s": 1800,"last_breach": bool},
          },
        }
        """

    def get_layer_snapshot(self, layer: str) -> dict:
        """Letzter LayerCheckResult fuer 'sofort'|'kurzfristig'|'mittelfristig' als dict."""

    def trigger_check(self, layer: str) -> dict:
        """Manuell einen Check dieses Layers ausloesen (fuer GUI-Button), gibt LayerCheckResult zurueck."""

    def get_history(self, layer: str = None, last_n: int = None) -> list[dict]:
        """Chronologische LayerCheckResult-Eintraege, optional nach Layer gefiltert."""

    def get_escalation_log(self, last_n: int = None) -> list[dict]:
        """Nur Eintraege mit tatsaechlich durchgefuehrtem Kreuz-Check/Eskalation."""
```

`LayerCheckResult` (als dict serialisiert, siehe `get_layer_snapshot`/
`get_history`):

```python
{
  "layer": "sofort" | "kurzfristig" | "mittelfristig",
  "timestamp": "2026-07-13T...",
  "resources": {"cpu": {...probe_cpu() Ausgabe...}, "gpu": {...}, "ram": {...},
                "fans": {...} | None, "ssd": {...} | None},
  "breached": {"cpu": bool, "gpu": bool, "ram": bool, "fans": bool, "ssd": bool},
  "escalated": bool,
  "action_taken": str | None,   # z.B. "couple_once", "offload_plan_generated", "tuner_ratio_lowered"
  "cross_check": {"triggered": bool, "resources_reprobed": [...], "corroborated": bool} | None,
}
```

## Bereits vorhanden (implementiert, dieser Session)

- **API-Router** `src/normal_os/ascension/Dashboard/resource_guardian_routes.py`
  — importiert `get_layered_resource_guardian` per try/except, alle Routen
  liefern sauberes "nicht verfuegbar" bis das Kernmodul existiert.
- **GUI-Seite** `/resources` (`templates/resources.html` +
  `static/resources.js`) — zeigt Status, alle drei Layer, History,
  manueller Trigger-Button pro Layer, Escalation-Log.

Sobald `layered_resource_guardian.py` diese Schnittstelle implementiert,
funktionieren API und GUI ohne weitere Aenderungen.
