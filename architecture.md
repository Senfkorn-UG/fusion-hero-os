# AscensionOS / Fusion Hero OS Architektur

AscensionOS ist ein mehrschichtiges Betriebssystem für Mesh, Services und XR-Oberflächen.

## Schichten

- Mesh-Layer: Wireless Mesh Networks, Overlay-Netze, Tailnet/Poly-Mesh.
- Service-Layer: LLMs, Datenbanken, APIs, Pipelines.
- XR-Layer: WebXR/VR/AR-Interfaces für Status-, Operations- und Archivräume.
- Docs/Archiv-Layer: GitHub Pages, Kanon-Texte, Dissertation-as-OS.

## Datenfluss (High-Level)

- Telemetrie und Logs steigen aus dem Mesh-Layer in Dashboards und XR-Räume auf.
- APIs verbinden Services mit XR-Clients und Hero-Dashboards.
- Archiv-Layer verknüpft jede technische Entität mit einer semantischen Identität (Kanon).

## Ressourcen und Anbindung

- Siehe [Ressourcen-Register](resources.md) für externe Tools, Frameworks und Repositories.
- Ressourcen-Updates werden per GitHub Actions und Skript `scripts/update_resources.sh` automatisiert angestoßen.
- Externe Frameworks (Mesh, XR, Archiv) werden als Services und Clients im System verortet.

