#!/usr/bin/env python3
"""
Quick test script to verify OSRM routing functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from osrm_router import calculate_commute_time, RouteResult
from transport_modes import TransportModes

def test_osrm_routing():
    """Test basic OSRM routing functionality."""
    print("Testing OSRM Routing Utility")
    print("=" * 40)

    # Test coordinates (Tel Aviv to Jerusalem)
    tel_aviv = (32.0853, 34.7818)
    jerusalem = (31.7683, 35.2137)

    print(f"Origin: Tel Aviv {tel_aviv}")
    print(f"Destination: Jerusalem {jerusalem}")
    print()

    # Test different transport modes
    transport_modes = ["driving", "cycling", "walking"]

    for mode in transport_modes:
        print(f"Testing {mode.upper()} mode:")
        result = calculate_commute_time(tel_aviv, jerusalem, mode)

        if result.success:
            print(f"  ✅ Success: {result.duration_minutes:.1f} minutes, {result.distance_km:.1f} km")
        else:
            print(f"  ❌ Failed: {result.error_message}")
        print()

    # Test invalid coordinates
    print("Testing invalid coordinates:")
    invalid_coords = (91.0, 181.0)  # Invalid lat/lon
    result = calculate_commute_time(tel_aviv, invalid_coords)
    print(f"  Expected error: {result.error_message}")
    print()

    # Test invalid transport mode
    print("Testing invalid transport mode:")
    result = calculate_commute_time(tel_aviv, jerusalem, "invalid_mode")
    print(f"  Expected error: {result.error_message}")
    print()

    print("Test completed!")

if __name__ == "__main__":
    test_osrm_routing()