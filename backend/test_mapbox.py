#!/usr/bin/env python3
"""
Test script for Mapbox Directions API.
Validates API connectivity and response format before full migration.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")

def test_mapbox_route(origin, destination, profile):
    """
    Test Mapbox Directions API with a single route.

    Args:
        origin: (lat, lon) tuple
        destination: (lat, lon) tuple
        profile: "driving", "cycling", or "walking"

    Returns:
        dict with success status and route info
    """
    # Mapbox expects lon,lat format
    origin_str = f"{origin[1]:.6f},{origin[0]:.6f}"
    dest_str = f"{destination[1]:.6f},{destination[0]:.6f}"

    url = f"https://api.mapbox.com/directions/v5/mapbox/{profile}/{origin_str};{dest_str}"
    params = {
        "access_token": MAPBOX_TOKEN,
        "geometries": "geojson",
        "overview": "full",
        "steps": "false"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Check response format (should match OSRM)
        if data.get("code") != "Ok":
            return {
                "success": False,
                "error": f"Mapbox error: {data.get('message', 'Unknown error')}"
            }

        routes = data.get("routes", [])
        if not routes:
            return {
                "success": False,
                "error": "No routes found"
            }

        route = routes[0]
        duration_seconds = route.get("duration", 0)
        distance_meters = route.get("distance", 0)

        return {
            "success": True,
            "duration_minutes": duration_seconds / 60.0,
            "distance_km": distance_meters / 1000.0,
            "profile": profile
        }

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Mapbox API timeout"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"HTTP error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


def main():
    print("=" * 60)
    print("MAPBOX DIRECTIONS API TEST")
    print("=" * 60)
    print()

    # Check token
    if not MAPBOX_TOKEN:
        print("❌ ERROR: MAPBOX_ACCESS_TOKEN not found in environment")
        print("   Create backend/.env with your Mapbox token")
        return

    print(f"✓ Token loaded: {MAPBOX_TOKEN[:20]}...")
    print()

    # Test routes
    test_cases = [
        {
            "name": "Tel Aviv → Jerusalem",
            "origin": (32.0853, 34.7818),
            "destination": (31.7683, 35.2137),
            "profiles": ["driving", "cycling", "walking"]
        },
        {
            "name": "Tel Aviv → Nearby",
            "origin": (32.0853, 34.7818),
            "destination": (32.0900, 34.7850),
            "profiles": ["driving"]
        }
    ]

    total_tests = 0
    passed_tests = 0

    for test_case in test_cases:
        print(f"Test Route: {test_case['name']}")
        print(f"  Origin: {test_case['origin']}")
        print(f"  Destination: {test_case['destination']}")
        print()

        for profile in test_case['profiles']:
            total_tests += 1
            print(f"  Testing {profile}...", end=" ")

            result = test_mapbox_route(
                test_case['origin'],
                test_case['destination'],
                profile
            )

            if result['success']:
                passed_tests += 1
                print(f"✅ SUCCESS")
                print(f"    Duration: {result['duration_minutes']:.1f} min")
                print(f"    Distance: {result['distance_km']:.1f} km")
            else:
                print(f"❌ FAILED")
                print(f"    Error: {result['error']}")
            print()

    print("=" * 60)
    print(f"RESULTS: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)

    if passed_tests == total_tests:
        print("✅ All tests passed! Mapbox API is working correctly.")
        print("   You can proceed with the full migration.")
    else:
        print("⚠️  Some tests failed. Check:")
        print("   1. Mapbox token is valid")
        print("   2. Network connectivity")
        print("   3. Mapbox API status: https://status.mapbox.com")


if __name__ == "__main__":
    main()
