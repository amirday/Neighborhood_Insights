#!/usr/bin/env python3
"""
Transport mode configurations for Mapbox routing.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class TransportMode:
    """Configuration for a transport mode."""
    name: str
    osrm_profile: str  # Keep field name for compatibility
    base_url: str
    average_speed_kmh: float
    max_distance_km: float
    description: str


class TransportModes:
    """Transport mode configurations for Mapbox routing."""

    # Mapbox API configuration
    MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
    MAPBOX_BASE_URL = "https://api.mapbox.com/directions/v5/mapbox"

    # Transport mode configurations
    DRIVING = TransportMode(
        name="driving",
        osrm_profile="driving",
        base_url=f"{MAPBOX_BASE_URL}/driving",
        average_speed_kmh=40.0,
        max_distance_km=500.0,
        description="Car/vehicle routing using roads"
    )

    CYCLING = TransportMode(
        name="cycling",
        osrm_profile="cycling",
        base_url=f"{MAPBOX_BASE_URL}/cycling",
        average_speed_kmh=15.0,
        max_distance_km=100.0,
        description="Bicycle routing using bike-friendly paths"
    )

    WALKING = TransportMode(
        name="walking",
        osrm_profile="walking",
        base_url=f"{MAPBOX_BASE_URL}/walking",
        average_speed_kmh=5.0,
        max_distance_km=25.0,
        description="Pedestrian routing using walkable paths"
    )

    @classmethod
    def get_all_modes(cls) -> Dict[str, TransportMode]:
        """Get all available transport modes."""
        return {
            "driving": cls.DRIVING,
            "cycling": cls.CYCLING,
            "walking": cls.WALKING
        }

    @classmethod
    def get_mode(cls, mode_name: str) -> TransportMode:
        """Get transport mode by name."""
        modes = cls.get_all_modes()
        if mode_name not in modes:
            raise ValueError(f"Unknown transport mode: {mode_name}. Available: {list(modes.keys())}")
        return modes[mode_name]

    @classmethod
    def is_valid_mode(cls, mode_name: str) -> bool:
        """Check if transport mode is valid."""
        return mode_name in cls.get_all_modes()


# Configuration for OSRM requests
OSRM_CONFIG = {
    "timeout": 10,  # seconds
    "max_retries": 3,
    "retry_delay": 1.0,  # seconds
    "cache_ttl": 3600,  # 1 hour cache
    "batch_size": 100,  # max coordinates per batch request
}

