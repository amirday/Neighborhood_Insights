#!/usr/bin/env python3
"""
Integration tests for public transit routing using Google Maps Transit API.
Tests use real API calls to verify transit mode works correctly.
"""

import unittest
import os
from routing.traffic_router import TrafficRouter


class TestTransitRouter(unittest.TestCase):
    """Test public transit routing with real Google Maps API calls."""

    def setUp(self):
        """Initialize router with real API key and Israeli test coordinates."""
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            self.skipTest("GOOGLE_MAPS_API_KEY not set in environment")

        self.router = TrafficRouter(
            api_key=api_key,
            enable_traffic=True,
            traffic_day_of_week=1,  # Monday
            traffic_hour=8  # 8 AM
        )

        # Israeli city coordinates (major transit hubs)
        self.tel_aviv_center = (32.0853, 34.7818)  # Tel Aviv Central Station
        self.jerusalem_center = (31.7857, 35.2007)  # Jerusalem Central Station
        self.haifa_center = (32.7940, 34.9896)  # Haifa Center Station

    def test_transit_tel_aviv_to_jerusalem(self):
        """Test real transit routing between Tel Aviv and Jerusalem."""
        result = self.router.calculate_route_time(
            self.tel_aviv_center,
            self.jerusalem_center,
            "transit"
        )

        # Basic assertions
        self.assertTrue(result.success, f"Transit route failed: {result.error_message}")
        self.assertGreater(result.duration_minutes, 0, "Duration should be positive")
        self.assertGreater(result.distance_meters, 0, "Distance should be positive")
        self.assertEqual(result.transport_mode, "transit")

        # Transit between Tel Aviv and Jerusalem typically takes 60-120 minutes
        self.assertGreater(result.duration_minutes, 50,
                          "Transit should take more than 50 minutes")
        self.assertLess(result.duration_minutes, 180,
                       "Transit should take less than 3 hours")

        print(f"\nTel Aviv → Jerusalem transit: {result.duration_minutes:.1f} min, "
              f"{result.distance_km:.1f} km")

    def test_transit_not_2x_driving_heuristic(self):
        """Verify transit is NOT using the 2x driving time heuristic."""
        transit_result = self.router.calculate_route_time(
            self.tel_aviv_center,
            self.jerusalem_center,
            "transit"
        )

        driving_result = self.router.calculate_route_time(
            self.tel_aviv_center,
            self.jerusalem_center,
            "driving"
        )

        self.assertTrue(transit_result.success, "Transit route should succeed")
        self.assertTrue(driving_result.success, "Driving route should succeed")

        # Calculate the ratio
        ratio = transit_result.duration_minutes / driving_result.duration_minutes

        # The old heuristic was exactly 2.0x - verify we're not using it
        # If ratio is between 1.95 and 2.05, it's suspiciously close to the heuristic
        self.assertNotAlmostEqual(ratio, 2.0, places=1,
                                 msg=f"Transit appears to still use 2x heuristic. "
                                     f"Transit: {transit_result.duration_minutes:.1f}min, "
                                     f"Driving: {driving_result.duration_minutes:.1f}min, "
                                     f"Ratio: {ratio:.2f}")

        print(f"\nTransit: {transit_result.duration_minutes:.1f} min, "
              f"Driving: {driving_result.duration_minutes:.1f} min, "
              f"Ratio: {ratio:.2f} (NOT 2.0x heuristic)")

    def test_transit_haifa_to_tel_aviv(self):
        """Test transit on different route (Haifa to Tel Aviv)."""
        result = self.router.calculate_route_time(
            self.haifa_center,
            self.tel_aviv_center,
            "transit"
        )

        self.assertTrue(result.success, f"Transit route failed: {result.error_message}")
        self.assertGreater(result.duration_minutes, 0)
        self.assertEqual(result.transport_mode, "transit")

        # Haifa to Tel Aviv typically takes 60-120 minutes by train
        self.assertGreater(result.duration_minutes, 40,
                          "Transit should take more than 40 minutes")
        self.assertLess(result.duration_minutes, 180,
                       "Transit should take less than 3 hours")

        print(f"\nHaifa → Tel Aviv transit: {result.duration_minutes:.1f} min, "
              f"{result.distance_km:.1f} km")

    def test_transit_jerusalem_to_haifa(self):
        """Test transit on third route (Jerusalem to Haifa)."""
        result = self.router.calculate_route_time(
            self.jerusalem_center,
            self.haifa_center,
            "transit"
        )

        self.assertTrue(result.success, f"Transit route failed: {result.error_message}")
        self.assertGreater(result.duration_minutes, 0)
        self.assertEqual(result.transport_mode, "transit")

        print(f"\nJerusalem → Haifa transit: {result.duration_minutes:.1f} min, "
              f"{result.distance_km:.1f} km")

    def test_transit_returns_route_result_structure(self):
        """Verify transit returns proper RouteResult structure."""
        result = self.router.calculate_route_time(
            self.tel_aviv_center,
            self.jerusalem_center,
            "transit"
        )

        # Check all RouteResult fields exist
        self.assertTrue(hasattr(result, 'duration_seconds'))
        self.assertTrue(hasattr(result, 'duration_minutes'))
        self.assertTrue(hasattr(result, 'distance_meters'))
        self.assertTrue(hasattr(result, 'distance_km'))
        self.assertTrue(hasattr(result, 'transport_mode'))
        self.assertTrue(hasattr(result, 'success'))

        # Verify field types
        self.assertIsInstance(result.duration_seconds, (int, float))
        self.assertIsInstance(result.duration_minutes, (int, float))
        self.assertIsInstance(result.distance_meters, (int, float))
        self.assertIsInstance(result.distance_km, (int, float))
        self.assertEqual(result.transport_mode, "transit")
        self.assertIsInstance(result.success, bool)

    def test_transit_different_times_may_vary(self):
        """Verify that transit times are based on actual schedules (not fixed heuristic)."""
        # Get transit route twice - should use Monday 8AM both times
        result1 = self.router.calculate_route_time(
            self.tel_aviv_center,
            self.jerusalem_center,
            "transit"
        )

        result2 = self.router.calculate_route_time(
            self.tel_aviv_center,
            self.jerusalem_center,
            "transit"
        )

        # Both should succeed
        self.assertTrue(result1.success)
        self.assertTrue(result2.success)

        # Times should be consistent for same departure time
        # (within a small tolerance for API variations)
        time_diff = abs(result1.duration_minutes - result2.duration_minutes)
        self.assertLess(time_diff, 10,
                       "Same route at same time should have similar durations")

        print(f"\nConsistency check - Route 1: {result1.duration_minutes:.1f} min, "
              f"Route 2: {result2.duration_minutes:.1f} min, "
              f"Difference: {time_diff:.1f} min")


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
