# Timespace Upgrade Proposal (v2_beta)

**Status:** Scaffold implementiert in `03_Code/timespace_token_management.py` (2026-07-05).
Volle Zeitaum-Geometrie aus Grok-Projekten war nicht exportierbar — dieses Dokument
ersetzt den Ein-Zeilen-Platzhalter ehrlich.

## Ziel

Token-Budgets nicht nur nach Kosten (TMS v1.0), sondern nach **Zeit-Raum-Position**
im evolutionären Stack verteilen: Layer-0-Nähe = höhere Priorität; entfernte
Meme-/Sisyphos-Tracks werden bei Knappheit geometrisch komprimiert.

## Implementiert (Minimal)

- `TimespaceCoordinate(time_index, space_depth)` — 2D-Koordinaten
- `TimespaceTokenManager` — geometrische Priorität × TMS-Bottleneck-Adaptation
- Brücke zu `TokenManagementSystem.allocate_tokens`

## Offen (Konzept)

- Mehrdimensionale Zeitaum-Manifolds (v2_beta-Vision)
- QUBO-gestützte Bottleneck-Vorhersage über Zeitskalen
- 3×-Fidelity-Regel über geometrische Nachbarschaft

## Code-Honesty

| Teil | Status |
|------|--------|
| TMS v1.0 Basis | Implementiert (`03_Code/TokenManagementSystem.py`) |
| Geometrische Erweiterung | Minimal-Scaffold (`timespace_token_management.py`) |
| Volle v2_beta-Vision | Konzept — kein Grok-Export eingegangen |