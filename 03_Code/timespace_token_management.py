#!/usr/bin/env python3
"""
Timespace Token Management — geometrische Erweiterung des TMS v1.0.

Status (Code-Honesty):
  - IMPLEMENTIERT: 2D-Zeit-Raum-Koordinaten pro Track, euklidische Distanz als
    Kompressions-/Prioritätsfaktor, Brücke zu TokenManagementSystem.allocate_tokens.
  - KONZEPT (nicht implementiert): volle v2_beta-Zeitaum-Geometrie, 3x-Token-Fidelity
    über mehrere Zeitskalen, QUBO-gestützte Bottleneck-Vorhersage.

Exportiert aus Grok-Projekt-Anfrage (GROK_EXPORT_REQUEST.md) als ehrlicher
Minimal-Scaffold — ersetzt die Ein-Zeilen-Platzhalter in v2_beta/.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from TokenManagementSystem import ResourceState, TokenManagementSystem, TransformationType


@dataclass(frozen=True)
class TimespaceCoordinate:
    """2D-Zeit-Raum-Punkt: time_index (Diskretisierung), space_depth (Tiefe/Layer)."""

    time_index: float
    space_depth: float

    def distance_to(self, other: "TimespaceCoordinate") -> float:
        return math.hypot(self.time_index - other.time_index, self.space_depth - other.space_depth)


@dataclass
class TimespaceTrack:
    name: str
    coordinate: TimespaceCoordinate
    state: ResourceState
    transformation: TransformationType = TransformationType.HABITUATION


class TimespaceTokenManager:
    """
    Geometrische Token-Verteilung: Tracks näher am Ursprung (0,0) erhalten
    höhere Basis-Priorität; entfernte Tracks werden bei Knappheit komprimiert.
    """

    def __init__(
        self,
        base_tokens: int = 10000,
        fidelity_multiplier: float = 3.0,
        compression_radius: float = 4.0,
    ) -> None:
        self.tms = TokenManagementSystem(base_tokens=base_tokens, fidelity_multiplier=fidelity_multiplier)
        self.compression_radius = compression_radius
        self.origin = TimespaceCoordinate(0.0, 0.0)

    def geometric_priority(self, coord: TimespaceCoordinate) -> float:
        dist = coord.distance_to(self.origin)
        if dist >= self.compression_radius:
            return max(0.25, 1.0 - (dist - self.compression_radius) * 0.15)
        return 1.0 + (self.compression_radius - dist) * 0.05

    def allocate(
        self,
        tracks: List[TimespaceTrack],
        extra_priorities: Optional[Dict[str, float]] = None,
    ) -> Dict[str, int]:
        states = {t.name: t.state for t in tracks}
        priorities: Dict[str, float] = {}
        for track in tracks:
            geo = self.geometric_priority(track.coordinate)
            adapt = self.tms.detect_and_adapt_to_bottleneck_shift(states).get(track.name, 1.0)
            extra = (extra_priorities or {}).get(track.name, 1.0)
            priorities[track.name] = geo * adapt * extra
        return self.tms.allocate_tokens(states, priorities)

    def summarize_geometry(self, tracks: List[TimespaceTrack]) -> List[Dict[str, float]]:
        return [
            {
                "name": t.name,
                "time_index": t.coordinate.time_index,
                "space_depth": t.coordinate.space_depth,
                "distance": t.coordinate.distance_to(self.origin),
                "priority": self.geometric_priority(t.coordinate),
            }
            for t in tracks
        ]


if __name__ == "__main__":
    manager = TimespaceTokenManager(base_tokens=8000)
    demo = [
        TimespaceTrack(
            "layer0_foundation",
            TimespaceCoordinate(0.0, 0.0),
            ResourceState(0.9, 0.1, 1, 0.05, 0.05),
        ),
        TimespaceTrack(
            "sisyphos_oscillation",
            TimespaceCoordinate(2.5, 1.5),
            ResourceState(0.6, 0.7, 2, 0.6, 0.55),
            TransformationType.DROP_RECOVERY,
        ),
        TimespaceTrack(
            "meme_synthesis_far",
            TimespaceCoordinate(5.0, 3.0),
            ResourceState(0.85, 0.2, 4, 0.1, 0.1),
            TransformationType.MEME_SYNTHESIS,
        ),
    ]
    print("Geometry:", manager.summarize_geometry(demo))
    print("Allocations:", manager.allocate(demo))