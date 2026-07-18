# Fusion Hero OS Docs

Der Docs-Pfad beschreibt die technische Seite von Fusion Hero OS.

## Statusraum – Dashboards und Monitoring

- System-Health-Dashboards (z.B. Prometheus/Grafana).
- Mesh-Monitoring für Knoten, Links und Latenz (Mesh-Metrics in Grafana-Panels).
- LLM- und Service-Status-Panels.

## Operationsraum – Steuerung und Pipelines

- Starten/Stoppen von Diensten.
- Deployments und Rollbacks.
- Policy- und Sicherheits-Regeln des Hero-OS.

## XR-Interface – WebXR / A-Frame / Three.js

- Darstellung der Dashboards als immersive Boards.
- Räume für Status, Operation und Archiv.
- Einheitliches Datenschema für Nodes, Services und Dokumente.

## Mesh-API (Entwurf)

- `/api/mesh/nodes` – Liste aller Mesh-Knoten mit Status.
- `/api/mesh/links` – Topologie und Verbindungsqualität.
- `/api/mesh/events` – Ereignisse (Join, Leave, Fehler, Angriffe).

## XR-API (Entwurf)

- `/api/xr/rooms` – definierte Räume (Status, Operation, Archiv).
- `/api/xr/panels` – Panels für Dashboards und Logs.
- `/api/xr/navigation` – Pfade und Übergänge zwischen Räumen.

## Operations-API (Entwurf)

- `/api/ops/services` – Dienste mit Start/Stop/Restart-Operationen.
- `/api/ops/deployments` – Releases, Rollbacks und Pipelines.
- `/api/ops/policies` – Sicherheits- und Zugriffsregeln.

## XR Scene Understanding (Entwurf)

AscensionOS nutzt WebXR-Mesh-Detection und Scene-Understanding, um reale Räume als Basis für Hero-Räume zu verwenden.

- Raum-Mesh: Globale Mesh-Daten für Wände, Böden, Objekte.
- Objekt-Meshes: Semantisch gekennzeichnete Objekte (Panels, Konsolen, Archiv-Säulen).
- Anchors: Feste Punkte zur Verankerung von Dashboards und Hero-UI.

### Zielbild

- Statusraum: Dashboards schweben an den Wänden oder stehen als Konsolen im Raum.
- Operationsraum: Steuer-Panels sind an Anchors verankert, Aktionen sind räumlich arrangiert.
- Archivraum: Kanon-Dokumente sind als begehbare Objekte oder Regale im Raum vorhanden.

