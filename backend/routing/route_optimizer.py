#!/usr/bin/env python3
"""
Route optimization utilities for efficient batch processing and caching.
"""

import asyncio
import time
from typing import List, Tuple, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiohttp

try:
    from .osrm_router import OSRMRouter, RouteResult
    from .transport_modes import TransportModes, OSRM_CONFIG
except ImportError:
    from osrm_router import OSRMRouter, RouteResult
    from transport_modes import TransportModes, OSRM_CONFIG


class RouteCache:
    """Simple in-memory cache for routes with TTL support."""

    def __init__(self, ttl_seconds: int = OSRM_CONFIG["cache_ttl"]):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired."""
        return time.time() - timestamp > self.ttl_seconds

    def get(self, key: str) -> Optional[RouteResult]:
        """Get cached route result."""
        if key in self._cache:
            entry = self._cache[key]
            if not self._is_expired(entry["timestamp"]):
                return entry["result"]
            else:
                # Remove expired entry
                del self._cache[key]
        return None

    def set(self, key: str, result: RouteResult) -> None:
        """Cache route result."""
        self._cache[key] = {
            "result": result,
            "timestamp": time.time()
        }

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def size(self) -> int:
        """Get cache size."""
        return len(self._cache)

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry["timestamp"] > self.ttl_seconds
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)


class AsyncOSRMRouter:
    """Async OSRM router for concurrent requests."""

    def __init__(self, cache: Optional[RouteCache] = None):
        self.cache = cache or RouteCache()

    def _cache_key(self, origin: Tuple[float, float], destination: Tuple[float, float],
                   transport_mode: str) -> str:
        """Generate cache key for route."""
        return f"{origin[0]:.6f},{origin[1]:.6f}-{destination[0]:.6f},{destination[1]:.6f}-{transport_mode}"

    def _format_osrm_url(self, origin: Tuple[float, float], destination: Tuple[float, float],
                         transport_mode: str) -> str:
        """Format OSRM API URL."""
        mode_config = TransportModes.get_mode(transport_mode)

        # OSRM expects lon,lat format
        origin_str = f"{origin[1]:.6f},{origin[0]:.6f}"
        dest_str = f"{destination[1]:.6f},{destination[0]:.6f}"

        url = f"{mode_config.base_url}/{origin_str};{dest_str}"
        params = "overview=false&steps=false"

        return f"{url}?{params}"

    async def _make_request(self, session: aiohttp.ClientSession, url: str,
                           transport_mode: str) -> RouteResult:
        """Make async HTTP request to OSRM."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=OSRM_CONFIG["timeout"])) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get("code") != "Ok":
                    return RouteResult(
                        duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                        transport_mode=transport_mode, success=False,
                        error_message=f"OSRM API error: {data.get('message', 'Unknown error')}"
                    )

                routes = data.get("routes", [])
                if not routes:
                    return RouteResult(
                        duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                        transport_mode=transport_mode, success=False,
                        error_message="No routes found"
                    )

                route = routes[0]
                duration_seconds = route.get("duration", 0)
                distance_meters = route.get("distance", 0)

                return RouteResult(
                    duration_seconds=duration_seconds,
                    duration_minutes=duration_seconds / 60.0,
                    distance_meters=distance_meters,
                    distance_km=distance_meters / 1000.0,
                    transport_mode=transport_mode,
                    success=True
                )

        except Exception as e:
            return RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=False,
                error_message=f"Request failed: {str(e)}"
            )

    async def calculate_routes_async(self, origin: Tuple[float, float],
                                   destinations: List[Tuple[float, float]],
                                   transport_mode: str = "driving") -> List[RouteResult]:
        """
        Calculate routes asynchronously for better performance.

        Args:
            origin: (latitude, longitude) of origin
            destinations: List of (latitude, longitude) destinations
            transport_mode: 'driving', 'cycling', or 'walking'

        Returns:
            List of RouteResult objects
        """
        # Check cache first
        cached_results = []
        uncached_destinations = []
        uncached_indices = []

        for i, destination in enumerate(destinations):
            cache_key = self._cache_key(origin, destination, transport_mode)
            cached_result = self.cache.get(cache_key)

            if cached_result:
                cached_results.append((i, cached_result))
            else:
                uncached_destinations.append(destination)
                uncached_indices.append(i)

        # Make async requests for uncached routes
        uncached_results = []
        if uncached_destinations:
            connector = aiohttp.TCPConnector(limit=50)  # Limit concurrent connections
            async with aiohttp.ClientSession(connector=connector) as session:
                tasks = []

                for destination in uncached_destinations:
                    url = self._format_osrm_url(origin, destination, transport_mode)
                    task = self._make_request(session, url, transport_mode)
                    tasks.append(task)

                uncached_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Handle exceptions
                for i, result in enumerate(uncached_results):
                    if isinstance(result, Exception):
                        uncached_results[i] = RouteResult(
                            duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                            transport_mode=transport_mode, success=False,
                            error_message=f"Exception: {str(result)}"
                        )
                    else:
                        # Cache successful results
                        if result.success:
                            cache_key = self._cache_key(origin, uncached_destinations[i], transport_mode)
                            self.cache.set(cache_key, result)

        # Combine cached and uncached results in correct order
        all_results = [None] * len(destinations)

        # Place cached results
        for index, result in cached_results:
            all_results[index] = result

        # Place uncached results
        for i, result in enumerate(uncached_results):
            index = uncached_indices[i]
            all_results[index] = result

        return all_results


class RouteBatchProcessor:
    """Efficient batch processing of route calculations."""

    def __init__(self, max_workers: int = 10, use_async: bool = True):
        self.max_workers = max_workers
        self.use_async = use_async
        self.cache = RouteCache()
        self.sync_router = OSRMRouter()
        self.async_router = AsyncOSRMRouter(self.cache)

    def calculate_routes_batch(self, origin: Tuple[float, float],
                             destinations: List[Tuple[float, float]],
                             transport_mode: str = "driving") -> List[RouteResult]:
        """
        Calculate routes in batch with optimal performance.

        Args:
            origin: (latitude, longitude) of origin
            destinations: List of (latitude, longitude) destinations
            transport_mode: 'driving', 'cycling', or 'walking'

        Returns:
            List of RouteResult objects
        """
        if not destinations:
            return []

        if self.use_async and len(destinations) > 5:
            # Use async for larger batches
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If already in an async context, create a new thread
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(self._run_async_batch, origin, destinations, transport_mode)
                        return future.result()
                else:
                    return loop.run_until_complete(
                        self.async_router.calculate_routes_async(origin, destinations, transport_mode)
                    )
            except Exception:
                # Fall back to sync processing
                pass

        # Use sync processing for smaller batches or if async fails
        return self._calculate_routes_sync_batch(origin, destinations, transport_mode)

    def _run_async_batch(self, origin: Tuple[float, float],
                        destinations: List[Tuple[float, float]],
                        transport_mode: str) -> List[RouteResult]:
        """Run async batch in new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.async_router.calculate_routes_async(origin, destinations, transport_mode)
            )
        finally:
            loop.close()

    def _calculate_routes_sync_batch(self, origin: Tuple[float, float],
                                   destinations: List[Tuple[float, float]],
                                   transport_mode: str) -> List[RouteResult]:
        """Calculate routes using threaded sync processing."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_dest = {
                executor.submit(self.sync_router.calculate_route_time, origin, dest, transport_mode): i
                for i, dest in enumerate(destinations)
            }

            results = [None] * len(destinations)
            for future in as_completed(future_to_dest):
                index = future_to_dest[future]
                try:
                    result = future.result()
                    results[index] = result
                except Exception as e:
                    results[index] = RouteResult(
                        duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                        transport_mode=transport_mode, success=False,
                        error_message=f"Processing error: {str(e)}"
                    )

            return results

    def calculate_distance_matrix(self, coordinates: List[Tuple[float, float]],
                                transport_mode: str = "driving") -> List[List[RouteResult]]:
        """
        Calculate distance matrix between all pairs of coordinates.

        Args:
            coordinates: List of (latitude, longitude) coordinates
            transport_mode: 'driving', 'cycling', or 'walking'

        Returns:
            2D list where matrix[i][j] is the route from coordinate i to coordinate j
        """
        n = len(coordinates)
        matrix = [[None for _ in range(n)] for _ in range(n)]

        # Calculate all pairs
        for i in range(n):
            origin = coordinates[i]
            destinations = [coord for j, coord in enumerate(coordinates) if i != j]
            destination_indices = [j for j in range(n) if i != j]

            if destinations:
                results = self.calculate_routes_batch(origin, destinations, transport_mode)

                # Place results in matrix
                for k, result in enumerate(results):
                    j = destination_indices[k]
                    matrix[i][j] = result

            # Diagonal elements (same point)
            matrix[i][i] = RouteResult(
                duration_seconds=0, duration_minutes=0, distance_meters=0, distance_km=0,
                transport_mode=transport_mode, success=True
            )

        return matrix

    def cleanup_cache(self) -> int:
        """Clean up expired cache entries."""
        return self.cache.cleanup_expired()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": self.cache.size(),
            "expired_cleaned": self.cleanup_cache()
        }


# Default batch processor instance
_default_processor = RouteBatchProcessor()

def calculate_routes_optimized(origin: Tuple[float, float],
                             destinations: List[Tuple[float, float]],
                             transport_mode: str = "driving") -> List[RouteResult]:
    """
    Calculate routes with optimal batch processing.

    This is the main function for efficient batch route calculations.
    """
    return _default_processor.calculate_routes_batch(origin, destinations, transport_mode)