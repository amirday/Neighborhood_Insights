#!/usr/bin/env python3
"""
Google Maps Directions API router with traffic support.
Replaces Mapbox routing with Google Maps for all transport modes.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import polyline

try:
    from .route_result import RouteResult
    from .transport_modes import OSRM_CONFIG
except ImportError:
    from route_result import RouteResult
    from transport_modes import OSRM_CONFIG

logger = logging.getLogger(__name__)


class TrafficRouter:
    """Google Maps Directions API router with traffic support."""

    GOOGLE_BASE_URL = "https://maps.googleapis.com/maps/api/directions/json"

    # Google Maps mode mapping
    GOOGLE_MODES = {
        "driving": "driving",
        "cycling": "bicycling",
        "walking": "walking",
        "transit": "transit"
    }

    def __init__(
        self,
        api_key: str,
        enable_traffic: bool = True,
        traffic_day_of_week: int = 1,  # Monday
        traffic_hour: int = 8,  # 8 AM
        cache=None
    ):
        """
        Initialize Google Maps router.

        Args:
            api_key: Google Maps API key
            enable_traffic: Whether to use traffic predictions for driving
            traffic_day_of_week: Day of week (0=Sunday, 1=Monday, etc.)
            traffic_hour: Hour of day (0-23)
            cache: Optional RouteCache instance
        """
        self.api_key = api_key
        self.enable_traffic = enable_traffic
        self.traffic_day_of_week = traffic_day_of_week
        self.traffic_hour = traffic_hour
        self._cache = cache
        self.session = self._create_session()

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

    def _calculate_next_occurrence(self) -> int:
        """
        Calculate Unix timestamp for next occurrence of configured day/time.

        Returns:
            Unix timestamp in seconds
        """
        now = datetime.now()

        # Calculate days until target day
        days_ahead = self.traffic_day_of_week - now.weekday()
        if days_ahead <= 0:  # Target day already happened this week or is today
            if now.weekday() == self.traffic_day_of_week and now.hour < self.traffic_hour:
                # It's the target day but before target hour - use today
                days_ahead = 0
            else:
                # Use next week
                days_ahead += 7

        target_date = now + timedelta(days=days_ahead)
        target_datetime = target_date.replace(
            hour=self.traffic_hour,
            minute=0,
            second=0,
            microsecond=0
        )

        return int(target_datetime.timestamp())

    def _format_google_maps_url(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        transport_mode: str,
        include_geometry: bool = False
    ) -> str:
        """
        Format Google Maps Directions API URL.

        Args:
            origin: (latitude, longitude) of origin
            destination: (latitude, longitude) of destination
            transport_mode: 'driving', 'cycling', 'walking', or 'transit'
            include_geometry: Whether to include route geometry

        Returns:
            Formatted URL with query parameters
        """
        # Google expects lat,lon format
        origin_str = f"{origin[0]},{origin[1]}"
        dest_str = f"{destination[0]},{destination[1]}"

        google_mode = self.GOOGLE_MODES.get(transport_mode, "driving")

        params = {
            "origin": origin_str,
            "destination": dest_str,
            "mode": google_mode,
            "key": self.api_key
        }

        # Add traffic for driving mode only
        if transport_mode == "driving" and self.enable_traffic:
            params["departure_time"] = self._calculate_next_occurrence()
            params["traffic_model"] = "best_guess"

        # Add alternatives for better routing
        params["alternatives"] = "false"

        return self.GOOGLE_BASE_URL, params

    def _parse_google_maps_response(
        self,
        response_data: Dict[str, Any],
        transport_mode: str
    ) -> RouteResult:
        """
        Parse Google Maps Directions API response.

        Args:
            response_data: JSON response from Google Maps API
            transport_mode: Transport mode used

        Returns:
            RouteResult with route information
        """
        # Check for API errors
        status = response_data.get("status")
        if status != "OK":
            error_message = response_data.get("error_message", f"Google Maps API error: {status}")
            return RouteResult(
                duration_seconds=0,
                duration_minutes=0,
                distance_meters=0,
                distance_km=0,
                transport_mode=transport_mode,
                success=False,
                error_message=error_message
            )

        # Extract route information
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
        leg = route["legs"][0]

        # Get duration - prefer duration_in_traffic for driving if available
        duration_data = leg.get("duration", {})
        duration_seconds = duration_data.get("value", 0)

        # For driving with traffic, use duration_in_traffic if available
        if transport_mode == "driving" and self.enable_traffic:
            traffic_duration = leg.get("duration_in_traffic", {})
            if traffic_duration:
                duration_seconds = traffic_duration.get("value", duration_seconds)

        distance_data = leg.get("distance", {})
        distance_meters = distance_data.get("value", 0)

        # Extract and decode geometry if requested
        geometry = None
        overview_polyline = route.get("overview_polyline", {})
        if overview_polyline:
            # Google returns encoded polyline - decode it to coordinate pairs
            encoded = overview_polyline.get("points")
            if encoded:
                # Decode to [[lat, lon], [lat, lon], ...] format
                geometry = polyline.decode(encoded)

        return RouteResult(
            duration_seconds=duration_seconds,
            duration_minutes=duration_seconds / 60.0,
            distance_meters=distance_meters,
            distance_km=distance_meters / 1000.0,
            transport_mode=transport_mode,
            geometry=geometry,
            success=True
        )

    def calculate_route_time(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        transport_mode: str = "driving",
        return_geometry: bool = False
    ) -> RouteResult:
        """
        Calculate route time using Google Maps Directions API.

        Args:
            origin: (latitude, longitude) of origin
            destination: (latitude, longitude) of destination
            transport_mode: 'driving', 'cycling', 'walking', or 'transit'
            return_geometry: Whether to include route geometry

        Returns:
            RouteResult with timing and distance information
        """
        # Validate coordinates
        if not (-90 <= origin[0] <= 90 and -180 <= origin[1] <= 180):
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message=f"Invalid origin coordinates: {origin}"
            )

        if not (-90 <= destination[0] <= 90 and -180 <= destination[1] <= 180):
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message=f"Invalid destination coordinates: {destination}"
            )

        # Check cache if available
        if self._cache:
            cache_key = self._cache_key(origin, destination, transport_mode)
            cached_result = self._cache.get(cache_key)
            if cached_result:
                return cached_result

        # Make Google Maps API request
        url, params = self._format_google_maps_url(
            origin, destination, transport_mode, return_geometry
        )

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=OSRM_CONFIG["timeout"]
            )
            response.raise_for_status()

            response_data = response.json()
            result = self._parse_google_maps_response(response_data, transport_mode)

            # Cache successful results
            if result.success and self._cache:
                cache_key = self._cache_key(origin, destination, transport_mode)
                self._cache.set(cache_key, result)

            return result

        except requests.exceptions.Timeout:
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message="Google Maps API timeout - service not responding"
            )
        except requests.exceptions.ConnectionError:
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message="Google Maps API connection failed - service unreachable"
            )
        except requests.exceptions.HTTPError as e:
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message=f"Google Maps API HTTP error: {e.response.status_code}"
            )
        except Exception as e:
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message=f"Google Maps API error: {str(e)}"
            )

    def _cache_key(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        transport_mode: str
    ) -> str:
        """Generate cache key for route."""
        traffic_suffix = "-traffic" if (transport_mode == "driving" and self.enable_traffic) else ""
        return f"{origin[0]:.6f},{origin[1]:.6f}-{destination[0]:.6f},{destination[1]:.6f}-{transport_mode}{traffic_suffix}"

    def calculate_routes_batch(
        self,
        origin: Tuple[float, float],
        destinations: List[Tuple[float, float]],
        transport_mode: str = "driving"
    ) -> List[RouteResult]:
        """
        Calculate routes from one origin to multiple destinations.

        Args:
            origin: (latitude, longitude) of origin
            destinations: List of (latitude, longitude) destinations
            transport_mode: 'driving', 'cycling', 'walking', or 'transit'

        Returns:
            List of RouteResult objects
        """
        results = []
        for destination in destinations:
            result = self.calculate_route_time(origin, destination, transport_mode)
            results.append(result)

        return results
