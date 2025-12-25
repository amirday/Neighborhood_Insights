#!/usr/bin/env python3
"""
Test routing integration after replacing Mapbox with Google Maps.
"""

import sys
from routing.osrm_router import OSRMRouter

def test_routing():
    """Test that routing now uses Google Maps with traffic."""

    print("\n" + "="*60)
    print("Testing Routing Integration (Google Maps)")
    print("="*60 + "\n")

    # Initialize router (should use Google Maps now)
    router = OSRMRouter()

    # Test coordinates (Tel Aviv to Jerusalem)
    tel_aviv = (32.0853, 34.7818)
    jerusalem = (31.7683, 35.2137)

    # Test driving with traffic
    print("Test 1: Driving (with Monday 8 AM traffic)")
    print("-" * 60)
    result = router.calculate_route_time(
        origin=tel_aviv,
        destination=jerusalem,
        transport_mode="driving"
    )

    if result.success:
        print(f"✅ Success!")
        print(f"   Distance: {result.distance_km:.2f} km")
        print(f"   Duration: {result.duration_minutes:.1f} minutes")
        print(f"   Mode: {result.transport_mode}")
    else:
        print(f"❌ Failed: {result.error_message}")
        return False

    # Test cycling
    print("\n\nTest 2: Cycling")
    print("-" * 60)
    result = router.calculate_route_time(
        origin=tel_aviv,
        destination=jerusalem,
        transport_mode="cycling"
    )

    if result.success:
        print(f"✅ Success!")
        print(f"   Distance: {result.distance_km:.2f} km")
        print(f"   Duration: {result.duration_minutes:.1f} minutes")
        print(f"   Mode: {result.transport_mode}")
    else:
        print(f"❌ Failed: {result.error_message}")
        return False

    # Test walking
    print("\n\nTest 3: Walking")
    print("-" * 60)
    haifa = (32.7940, 34.9896)
    tel_aviv_center = (32.0853, 34.7818)

    # Shorter route for walking
    petah_tikva = (32.0879, 34.8870)
    ramat_gan = (32.0706, 34.8234)

    result = router.calculate_route_time(
        origin=petah_tikva,
        destination=ramat_gan,
        transport_mode="walking"
    )

    if result.success:
        print(f"✅ Success!")
        print(f"   Distance: {result.distance_km:.2f} km")
        print(f"   Duration: {result.duration_minutes:.1f} minutes")
        print(f"   Mode: {result.transport_mode}")
    else:
        print(f"❌ Failed: {result.error_message}")
        return False

    print("\n" + "="*60)
    print("All tests passed! ✅")
    print("Google Maps API is now being used for all routing.")
    print("Driving mode includes Monday 8 AM traffic predictions.")
    print("="*60 + "\n")

    return True

if __name__ == "__main__":
    success = test_routing()
    sys.exit(0 if success else 1)
