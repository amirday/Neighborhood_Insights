#!/usr/bin/env python3
"""
Route result data structure shared across routing modules.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class RouteResult:
    """Result from a routing calculation."""
    duration_seconds: float
    duration_minutes: float
    distance_meters: float
    distance_km: float
    transport_mode: str
    geometry: Optional[List[Tuple[float, float]]] = None
    success: bool = True
    error_message: Optional[str] = None

    def __post_init__(self):
        """Calculate derived values."""
        if self.duration_minutes == 0 and self.duration_seconds > 0:
            self.duration_minutes = self.duration_seconds / 60.0
        if self.distance_km == 0 and self.distance_meters > 0:
            self.distance_km = self.distance_meters / 1000.0
