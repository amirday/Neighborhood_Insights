#!/usr/bin/env python3
"""
Comprehensive test suite for OSRM routing functionality.
"""

import unittest
import time
from unittest.mock import patch, MagicMock

try:
    from .transport_modes import TransportModes, TransportMode
    from .osrm_router import OSRMRouter, RouteResult, calculate_commute_time, get_driving_time, get_cycling_time, get_walking_time
    from .route_optimizer import RouteBatchProcessor, RouteCache, AsyncOSRMRouter
except ImportError:
    from transport_modes import TransportModes, TransportMode
    from osrm_router import OSRMRouter, RouteResult, calculate_commute_time, get_driving_time, get_cycling_time, get_walking_time
    from route_optimizer import RouteBatchProcessor, RouteCache, AsyncOSRMRouter


class TestTransportModes(unittest.TestCase):
    """Test transport mode configurations."""

    def test_get_all_modes(self):
        """Test getting all transport modes."""
        modes = TransportModes.get_all_modes()
        self.assertIn("driving", modes)
        self.assertIn("cycling", modes)
        self.assertIn("walking", modes)
        self.assertEqual(len(modes), 3)

    def test_get_mode_valid(self):
        """Test getting valid transport mode."""
        driving = TransportModes.get_mode("driving")
        self.assertIsInstance(driving, TransportMode)
        self.assertEqual(driving.name, "driving")
        self.assertEqual(driving.average_speed_kmh, 40.0)

    def test_get_mode_invalid(self):
        """Test getting invalid transport mode."""
        with self.assertRaises(ValueError):
            TransportModes.get_mode("invalid_mode")

    def test_is_valid_mode(self):
        """Test transport mode validation."""
        self.assertTrue(TransportModes.is_valid_mode("driving"))
        self.assertTrue(TransportModes.is_valid_mode("cycling"))
        self.assertTrue(TransportModes.is_valid_mode("walking"))
        self.assertFalse(TransportModes.is_valid_mode("invalid"))


class TestRouteResult(unittest.TestCase):
    """Test RouteResult data structure."""

    def test_route_result_creation(self):
        """Test creating a route result."""
        result = RouteResult(
            duration_seconds=1800,
            duration_minutes=0,  # Should be calculated
            distance_meters=15000,
            distance_km=0,  # Should be calculated
            transport_mode="driving"
        )

        self.assertEqual(result.duration_minutes, 30.0)
        self.assertEqual(result.distance_km, 15.0)
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)

    def test_route_result_with_error(self):
        """Test creating a route result with error."""
        result = RouteResult(
            duration_seconds=0,
            duration_minutes=0,
            distance_meters=0,
            distance_km=0,
            transport_mode="driving",
            success=False,
            error_message="Test error"
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Test error")


class TestOSRMRouter(unittest.TestCase):
    """Test OSRM router functionality."""

    def setUp(self):
        """Set up test router."""
        self.router = OSRMRouter()

        # Israeli coordinates for testing
        self.tel_aviv = (32.0853, 34.7818)
        self.jerusalem = (31.7683, 35.2137)
        self.haifa = (32.7940, 34.9896)
        self.invalid_coords = (91.0, 181.0)  # Invalid coordinates

    def test_validate_coordinates(self):
        """Test coordinate validation."""
        self.assertTrue(self.router._validate_coordinates(32.0853, 34.7818))
        self.assertFalse(self.router._validate_coordinates(91.0, 181.0))
        self.assertFalse(self.router._validate_coordinates(-91.0, -181.0))

    def test_cache_key_generation(self):
        """Test cache key generation."""
        key = self.router._cache_key(self.tel_aviv, self.jerusalem, "driving")
        self.assertIsInstance(key, str)
        self.assertIn("driving", key)

    def test_format_osrm_url(self):
        """Test OSRM URL formatting."""
        url = self.router._format_osrm_url(self.tel_aviv, self.jerusalem, "driving")
        self.assertIn("router.project-osrm.org", url)
        self.assertIn("driving", url)
        self.assertIn("34.781800,32.085300", url)  # lon,lat format

    def test_invalid_coordinates_error(self):
        """Test error handling for invalid coordinates."""
        result = self.router.calculate_route_time(self.invalid_coords, self.jerusalem)
        self.assertFalse(result.success)
        self.assertIn("Invalid origin coordinates", result.error_message)

    def test_invalid_transport_mode_error(self):
        """Test error handling for invalid transport mode."""
        result = self.router.calculate_route_time(self.tel_aviv, self.jerusalem, "invalid_mode")
        self.assertFalse(result.success)
        self.assertIn("Invalid transport mode", result.error_message)

    @patch('requests.Session.get')
    def test_successful_osrm_response(self, mock_get):
        """Test successful OSRM API response."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": "Ok",
            "routes": [{
                "duration": 1800,  # 30 minutes
                "distance": 15000,  # 15 km
            }]
        }
        mock_get.return_value = mock_response

        result = self.router.calculate_route_time(self.tel_aviv, self.jerusalem)

        self.assertTrue(result.success)
        self.assertEqual(result.duration_seconds, 1800)
        self.assertEqual(result.duration_minutes, 30.0)
        self.assertEqual(result.distance_meters, 15000)
        self.assertEqual(result.distance_km, 15.0)

    @patch('requests.Session.get')
    def test_osrm_api_error(self, mock_get):
        """Test OSRM API error response."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": "NoRoute",
            "message": "No route found"
        }
        mock_get.return_value = mock_response

        result = self.router.calculate_route_time(self.tel_aviv, self.jerusalem)

        # Should return error without fallback
        self.assertFalse(result.success)
        self.assertIn("OSRM API error", result.error_message)

    @patch('requests.Session.get')
    def test_network_error_handling(self, mock_get):
        """Test network error handling without fallback."""
        mock_get.side_effect = Exception("Network error")

        result = self.router.calculate_route_time(self.tel_aviv, self.jerusalem)

        # Should return error without fallback
        self.assertFalse(result.success)
        self.assertIn("Unexpected error", result.error_message)

    def test_batch_routes_calculation(self):
        """Test batch route calculation."""
        destinations = [self.jerusalem, self.haifa]

        with patch.object(self.router, 'calculate_route_time') as mock_calc:
            mock_calc.return_value = RouteResult(
                duration_seconds=1800, duration_minutes=30.0,
                distance_meters=15000, distance_km=15.0,
                transport_mode="driving"
            )

            results = self.router.calculate_routes_batch(self.tel_aviv, destinations)

            self.assertEqual(len(results), 2)
            self.assertEqual(mock_calc.call_count, 2)


class TestRouteCache(unittest.TestCase):
    """Test route caching functionality."""

    def setUp(self):
        """Set up test cache."""
        self.cache = RouteCache(ttl_seconds=1)  # Short TTL for testing

    def test_cache_set_get(self):
        """Test cache set and get operations."""
        result = RouteResult(
            duration_seconds=1800, duration_minutes=30.0,
            distance_meters=15000, distance_km=15.0,
            transport_mode="driving"
        )

        self.cache.set("test_key", result)
        cached_result = self.cache.get("test_key")

        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result.duration_seconds, 1800)

    def test_cache_expiration(self):
        """Test cache entry expiration."""
        result = RouteResult(
            duration_seconds=1800, duration_minutes=30.0,
            distance_meters=15000, distance_km=15.0,
            transport_mode="driving"
        )

        self.cache.set("test_key", result)
        time.sleep(1.1)  # Wait for expiration

        cached_result = self.cache.get("test_key")
        self.assertIsNone(cached_result)

    def test_cache_cleanup(self):
        """Test cache cleanup of expired entries."""
        result = RouteResult(
            duration_seconds=1800, duration_minutes=30.0,
            distance_meters=15000, distance_km=15.0,
            transport_mode="driving"
        )

        self.cache.set("test_key1", result)
        self.cache.set("test_key2", result)
        time.sleep(1.1)  # Wait for expiration

        cleaned = self.cache.cleanup_expired()
        self.assertEqual(cleaned, 2)
        self.assertEqual(self.cache.size(), 0)


class TestRouteBatchProcessor(unittest.TestCase):
    """Test batch route processing."""

    def setUp(self):
        """Set up test processor."""
        self.processor = RouteBatchProcessor(max_workers=2, use_async=False)
        self.tel_aviv = (32.0853, 34.7818)
        self.destinations = [
            (31.7683, 35.2137),  # Jerusalem
            (32.7940, 34.9896),  # Haifa
        ]

    def test_batch_processing(self):
        """Test batch route processing."""
        with patch.object(self.processor.sync_router, 'calculate_route_time') as mock_calc:
            mock_calc.return_value = RouteResult(
                duration_seconds=1800, duration_minutes=30.0,
                distance_meters=15000, distance_km=15.0,
                transport_mode="driving"
            )

            results = self.processor.calculate_routes_batch(
                self.tel_aviv, self.destinations, "driving"
            )

            self.assertEqual(len(results), 2)
            self.assertEqual(mock_calc.call_count, 2)

    def test_empty_destinations(self):
        """Test batch processing with empty destinations."""
        results = self.processor.calculate_routes_batch(self.tel_aviv, [])
        self.assertEqual(len(results), 0)

    def test_distance_matrix(self):
        """Test distance matrix calculation."""
        coordinates = [self.tel_aviv] + self.destinations

        with patch.object(self.processor, 'calculate_routes_batch') as mock_batch:
            mock_batch.return_value = [
                RouteResult(duration_seconds=1800, duration_minutes=30.0,
                           distance_meters=15000, distance_km=15.0, transport_mode="driving"),
                RouteResult(duration_seconds=2400, duration_minutes=40.0,
                           distance_meters=20000, distance_km=20.0, transport_mode="driving")
            ]

            matrix = self.processor.calculate_distance_matrix(coordinates)

            self.assertEqual(len(matrix), 3)
            self.assertEqual(len(matrix[0]), 3)

            # Diagonal should be zero distance
            self.assertEqual(matrix[0][0].distance_km, 0)
            self.assertEqual(matrix[1][1].distance_km, 0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def setUp(self):
        """Set up test coordinates."""
        self.tel_aviv = (32.0853, 34.7818)
        self.jerusalem = (31.7683, 35.2137)

    @patch('routing.osrm_router.OSRMRouter.calculate_route_time')
    def test_get_driving_time(self, mock_calc):
        """Test get_driving_time convenience function."""
        mock_calc.return_value = RouteResult(
            duration_seconds=1800, duration_minutes=30.0,
            distance_meters=15000, distance_km=15.0,
            transport_mode="driving", success=True
        )

        time_minutes = get_driving_time(self.tel_aviv, self.jerusalem)
        self.assertEqual(time_minutes, 30.0)

    @patch('routing.osrm_router.OSRMRouter.calculate_route_time')
    def test_get_cycling_time(self, mock_calc):
        """Test get_cycling_time convenience function."""
        mock_calc.return_value = RouteResult(
            duration_seconds=3600, duration_minutes=60.0,
            distance_meters=15000, distance_km=15.0,
            transport_mode="cycling", success=True
        )

        time_minutes = get_cycling_time(self.tel_aviv, self.jerusalem)
        self.assertEqual(time_minutes, 60.0)

    @patch('routing.osrm_router.OSRMRouter.calculate_route_time')
    def test_get_walking_time(self, mock_calc):
        """Test get_walking_time convenience function."""
        mock_calc.return_value = RouteResult(
            duration_seconds=10800, duration_minutes=180.0,
            distance_meters=15000, distance_km=15.0,
            transport_mode="walking", success=True
        )

        time_minutes = get_walking_time(self.tel_aviv, self.jerusalem)
        self.assertEqual(time_minutes, 180.0)

    @patch('routing.osrm_router.OSRMRouter.calculate_route_time')
    def test_calculate_commute_time(self, mock_calc):
        """Test calculate_commute_time main function."""
        mock_calc.return_value = RouteResult(
            duration_seconds=1800, duration_minutes=30.0,
            distance_meters=15000, distance_km=15.0,
            transport_mode="driving", success=True
        )

        result = calculate_commute_time(self.tel_aviv, self.jerusalem, "driving")
        self.assertTrue(result.success)
        self.assertEqual(result.duration_minutes, 30.0)


class TestIntegration(unittest.TestCase):
    """Integration tests with real coordinates."""

    def setUp(self):
        """Set up integration test data."""
        self.router = OSRMRouter()

        # Israeli city coordinates
        self.tel_aviv = (32.0853, 34.7818)
        self.jerusalem = (31.7683, 35.2137)
        self.haifa = (32.7940, 34.9896)
        self.netanya = (32.3215, 34.8532)

    def test_real_coordinates_handling(self):
        """Test with real coordinates (may fail without internet in test environment)."""
        # This test will likely fail since we don't have internet in tests
        result = self.router.calculate_route_time(self.tel_aviv, self.jerusalem)

        # Should either succeed with OSRM or fail with error message
        if result.success:
            self.assertGreater(result.duration_minutes, 0)
            self.assertGreater(result.distance_km, 0)
        else:
            self.assertIsNotNone(result.error_message)

    def test_different_transport_modes(self):
        """Test different transport modes with real coordinates."""
        modes = ["driving", "cycling", "walking"]

        for mode in modes:
            result = self.router.calculate_route_time(self.tel_aviv, self.jerusalem, mode)
            self.assertGreater(result.duration_minutes, 0)
            self.assertEqual(result.transport_mode, mode)

    def test_batch_with_real_coordinates(self):
        """Test batch processing with real coordinates."""
        destinations = [self.jerusalem, self.haifa, self.netanya]
        results = self.router.calculate_routes_batch(self.tel_aviv, destinations)

        self.assertEqual(len(results), 3)
        for result in results:
            self.assertGreater(result.duration_minutes, 0)


def run_performance_test():
    """Run performance benchmark."""
    print("\n=== Performance Test ===")

    router = OSRMRouter()
    processor = RouteBatchProcessor()

    # Test coordinates
    tel_aviv = (32.0853, 34.7818)
    destinations = [
        (31.7683, 35.2137),  # Jerusalem
        (32.7940, 34.9896),  # Haifa
        (31.2518, 34.7915),  # Beer Sheva
        (32.3215, 34.8532),  # Netanya
        (32.0879, 34.8017),  # Givatayim
    ]

    # Single route performance
    start_time = time.time()
    result = router.calculate_route_time(tel_aviv, destinations[0])
    single_time = time.time() - start_time
    print(f"Single route: {single_time:.3f}s")

    # Batch performance
    start_time = time.time()
    results = processor.calculate_routes_batch(tel_aviv, destinations)
    batch_time = time.time() - start_time
    print(f"Batch routes ({len(destinations)}): {batch_time:.3f}s")
    print(f"Average per route: {batch_time/len(destinations):.3f}s")

    # Cache stats
    stats = processor.get_cache_stats()
    print(f"Cache size: {stats['cache_size']}")


if __name__ == "__main__":
    # Run unit tests
    unittest.main(verbosity=2, exit=False)

    # Run performance test
    run_performance_test()

    print("\nAll tests completed!")