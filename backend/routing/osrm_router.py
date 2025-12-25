#!/usr/bin/env python3
"""
OSRM routing utility for calculating commute times between coordinates.
Supports multiple transport modes (car, bike, walking) with road snapping.
"""

import json
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from .transport_modes import TransportModes, OSRM_CONFIG
except ImportError:
    from transport_modes import TransportModes, OSRM_CONFIG


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


class OSRMRouter:
    """OSRM router for calculating routes between coordinates."""

    def __init__(self, cache_ttl: int = OSRM_CONFIG["cache_ttl"]):
        """Initialize the OSRM router with configured session."""
        self.session = self._create_session()
        # Import RouteCache for TTL and size-limited caching
        try:
            from .route_optimizer import RouteCache
        except ImportError:
            from route_optimizer import RouteCache
        self._cache = RouteCache(ttl_seconds=cache_ttl)

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()

        retry_strategy = Retry(
            total=OSRM_CONFIG["max_retries"],
            backoff_factor=OSRM_CONFIG["retry_delay"],
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _cache_key(self, origin: Tuple[float, float], destination: Tuple[float, float],
                   transport_mode: str) -> str:
        """Generate cache key for route."""
        return f"{origin[0]:.6f},{origin[1]:.6f}-{destination[0]:.6f},{destination[1]:.6f}-{transport_mode}"

    def _get_cached_route(self, cache_key: str) -> Optional[RouteResult]:
        """Get cached route if available and not expired."""
        return self._cache.get(cache_key)

    def _cache_route(self, cache_key: str, result: RouteResult) -> None:
        """Cache route result."""
        self._cache.set(cache_key, result)

    def _validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validate coordinate values."""
        return -90 <= lat <= 90 and -180 <= lon <= 180

    def _format_osrm_url(self, origin: Tuple[float, float], destination: Tuple[float, float],
                         transport_mode: str, include_geometry: bool = False) -> str:
        """Format OSRM API URL."""
        mode_config = TransportModes.get_mode(transport_mode)
        # OSRM expects lon,lat format
        origin_str = f"{origin[1]:.6f},{origin[0]:.6f}"
        dest_str = f"{destination[1]:.6f},{destination[0]:.6f}"

        url = f"{mode_config.base_url}/{origin_str};{dest_str}"

        params = ["steps=false"]
        if include_geometry:
            params.append("overview=full")
            params.append("geometries=geojson")
        else:
            params.append("overview=false")

        return f"{url}?{'&'.join(params)}"

    def _parse_osrm_response(self, response_data: Dict[str, Any],
                           transport_mode: str) -> RouteResult:
        """Parse OSRM API response."""
        # Check for OSRM API errors first
        if response_data.get("code") != "Ok":
            return RouteResult(
                duration_seconds=0,
                duration_minutes=0,
                distance_meters=0,
                distance_km=0,
                transport_mode=transport_mode,
                success=False,
                error_message=f"OSRM error: {response_data.get('message', 'Unknown error')}"
            )

        routes = response_data.get("routes", [])
        if not routes:
            return RouteResult(
                duration_seconds=0,
                duration_minutes=0,
                distance_meters=0,
                distance_km=0,
                transport_mode=transport_mode,
                success=False,
                error_message="No routes found"
            )

        route = routes[0]
        duration_seconds = route.get("duration", 0)
        distance_meters = route.get("distance", 0)
        # Extract geometry if available
        geometry = None
        if "geometry" in route and "coordinates" in route["geometry"]:
            # Convert from [lon, lat] to [lat, lon]
            geometry = [(coord[1], coord[0]) for coord in route["geometry"]["coordinates"]]

        return RouteResult(
            duration_seconds=duration_seconds,
            duration_minutes=duration_seconds / 60.0,
            distance_meters=distance_meters,
            distance_km=distance_meters / 1000.0,
            transport_mode=transport_mode,
            geometry=geometry,
            success=True
        )


    def calculate_route_time(self, origin: Tuple[float, float], destination: Tuple[float, float],
                           transport_mode: str = "driving",
                           return_geometry: bool = False) -> RouteResult:
        """
        Calculate route time between two coordinates.

        Args:
            origin: (latitude, longitude) of origin
            destination: (latitude, longitude) of destination
            transport_mode: 'driving', 'cycling', or 'walking'
            return_geometry: Whether to include route geometry

        Returns:
            RouteResult with timing and distance information
        """
        # Validate inputs
        if not self._validate_coordinates(origin[0], origin[1]):
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message=f"Invalid origin coordinates: {origin}"
            )

        if not self._validate_coordinates(destination[0], destination[1]):
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message=f"Invalid destination coordinates: {destination}"
            )

        if not TransportModes.is_valid_mode(transport_mode):
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message=f"Invalid transport mode: {transport_mode}"
            )

        # Check cache
        cache_key = self._cache_key(origin, destination, transport_mode)
        cached_result = self._get_cached_route(cache_key)
        if cached_result:
            return cached_result

        # Make OSRM request with error handling
        url = self._format_osrm_url(origin, destination, transport_mode, return_geometry)

        try:
            response = self.session.get(url, timeout=OSRM_CONFIG["timeout"])
            response.raise_for_status()

            response_data = response.json()
            result = self._parse_osrm_response(response_data, transport_mode)

            # Cache successful results
            if result.success:
                self._cache_route(cache_key, result)

            return result

        except requests.exceptions.Timeout:
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message="OSRM API timeout - service not responding"
            )
        except requests.exceptions.ConnectionError:
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message="OSRM API connection failed - service unreachable"
            )
        except requests.exceptions.HTTPError as e:
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message=f"OSRM API HTTP error: {e.response.status_code}"
            )
        except Exception as e:
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message=f"OSRM API error: {str(e)}"
            )

    def calculate_routes_batch(self, origin: Tuple[float, float],
                             destinations: List[Tuple[float, float]],
                             transport_mode: str = "driving") -> List[RouteResult]:
        """
        Calculate routes from one origin to multiple destinations.

        Args:
            origin: (latitude, longitude) of origin
            destinations: List of (latitude, longitude) destinations
            transport_mode: 'driving', 'cycling', or 'walking'

        Returns:
            List of RouteResult objects
        """
        results = []
        for destination in destinations:
            result = self.calculate_route_time(origin, destination, transport_mode)
            results.append(result)

        return results


# Convenience functions for each transport mode
def get_driving_time(origin: Tuple[float, float], destination: Tuple[float, float]) -> float:
    """Get driving time in minutes. Returns 0 if route calculation fails."""
    router = OSRMRouter()
    result = router.calculate_route_time(origin, destination, "driving")
    return result.duration_minutes if result.success else 0.0


def get_cycling_time(origin: Tuple[float, float], destination: Tuple[float, float]) -> float:
    """Get cycling time in minutes. Returns 0 if route calculation fails."""
    router = OSRMRouter()
    result = router.calculate_route_time(origin, destination, "cycling")
    return result.duration_minutes if result.success else 0.0


def get_walking_time(origin: Tuple[float, float], destination: Tuple[float, float]) -> float:
    """Get walking time in minutes. Returns 0 if route calculation fails."""
    router = OSRMRouter()
    result = router.calculate_route_time(origin, destination, "walking")
    return result.duration_minutes if result.success else 0.0


# Default router instance for convenience
_default_router = OSRMRouter()

def calculate_commute_time(origin: Tuple[float, float], destination: Tuple[float, float],
                          transport_mode: str = "driving") -> RouteResult:
    """
    Calculate commute time using the default router instance.

    This is the main function for calculating commute times with OSRM.
    """
    return _default_router.calculate_route_time(origin, destination, transport_mode)