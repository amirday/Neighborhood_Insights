#!/usr/bin/env python3
"""
Test Google Maps Directions API with traffic predictions.
This script tests getting traffic-adjusted travel times for Monday 8 AM.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def calculate_next_monday_8am() -> int:
    """
    Calculate Unix timestamp for next Monday at 8 AM Israel time.

    Returns:
        Unix timestamp in seconds
    """
    now = datetime.now()

    # Calculate days until next Monday (0=Monday, 6=Sunday)
    days_ahead = 0 - now.weekday()  # 0 is Monday
    if days_ahead <= 0:  # Target day already happened this week or is today
        if now.weekday() == 0 and now.hour < 8:
            # It's Monday but before 8 AM - use today
            days_ahead = 0
        else:
            # Use next Monday
            days_ahead += 7

    next_monday = now + timedelta(days=days_ahead)
    monday_8am = next_monday.replace(hour=8, minute=0, second=0, microsecond=0)

    return int(monday_8am.timestamp())


def test_google_maps_traffic(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    api_key: str
) -> Dict[str, Any]:
    """
    Test Google Maps Directions API with traffic for Monday 8 AM.

    Args:
        origin: (latitude, longitude) of origin
        destination: (latitude, longitude) of destination
        api_key: Google Maps API key

    Returns:
        Dictionary with results including duration with/without traffic
    """
    # Calculate departure time for Monday 8 AM
    departure_time = calculate_next_monday_8am()
    monday_8am_str = datetime.fromtimestamp(departure_time).strftime("%Y-%m-%d %H:%M")

    # Format Google Maps API URL
    base_url = "https://maps.googleapis.com/maps/api/directions/json"

    params = {
        "origin": f"{origin[0]},{origin[1]}",
        "destination": f"{destination[0]},{destination[1]}",
        "departure_time": departure_time,
        "traffic_model": "best_guess",  # Options: best_guess, pessimistic, optimistic
        "key": api_key
    }

    print(f"\n{'='*60}")
    print(f"Testing Google Maps Directions API with Traffic")
    print(f"{'='*60}")
    print(f"Origin: {origin}")
    print(f"Destination: {destination}")
    print(f"Departure Time: {monday_8am_str} (Monday 8 AM)")
    print(f"Unix Timestamp: {departure_time}")
    print(f"\nMaking API request...")

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Check for API errors
        if data.get("status") != "OK":
            print(f"\n❌ API Error: {data.get('status')}")
            print(f"Error Message: {data.get('error_message', 'No message')}")
            return {
                "success": False,
                "error": data.get("status"),
                "error_message": data.get("error_message")
            }

        # Extract route information
        routes = data.get("routes", [])
        if not routes:
            print("\n❌ No routes found")
            return {"success": False, "error": "No routes found"}

        route = routes[0]
        leg = route["legs"][0]

        # Extract durations
        duration = leg.get("duration", {})
        duration_in_traffic = leg.get("duration_in_traffic", {})
        distance = leg.get("distance", {})

        duration_seconds = duration.get("value", 0)
        duration_minutes = duration_seconds / 60.0

        traffic_seconds = duration_in_traffic.get("value", duration_seconds)
        traffic_minutes = traffic_seconds / 60.0

        distance_meters = distance.get("value", 0)
        distance_km = distance_meters / 1000.0

        # Calculate traffic impact
        traffic_impact = ((traffic_minutes - duration_minutes) / duration_minutes * 100) if duration_minutes > 0 else 0

        # Display results
        print(f"\n✅ Route Found!")
        print(f"\n{'─'*60}")
        print(f"📍 Route Details:")
        print(f"   Start: {leg.get('start_address', 'N/A')}")
        print(f"   End: {leg.get('end_address', 'N/A')}")
        print(f"\n📏 Distance:")
        print(f"   {distance_km:.2f} km ({distance.get('text', 'N/A')})")
        print(f"\n⏱️  Duration (no traffic):")
        print(f"   {duration_minutes:.1f} minutes ({duration.get('text', 'N/A')})")
        print(f"\n🚦 Duration with Monday 8 AM Traffic:")
        print(f"   {traffic_minutes:.1f} minutes ({duration_in_traffic.get('text', 'N/A')})")
        print(f"\n📊 Traffic Impact:")
        if traffic_impact > 5:
            print(f"   +{traffic_impact:.1f}% slower due to traffic")
            print(f"   +{traffic_minutes - duration_minutes:.1f} minutes added")
        elif traffic_impact < -5:
            print(f"   {traffic_impact:.1f}% faster (off-peak)")
        else:
            print(f"   ~{traffic_impact:.1f}% (minimal traffic impact)")
        print(f"{'─'*60}\n")

        return {
            "success": True,
            "monday_8am": monday_8am_str,
            "distance_km": distance_km,
            "distance_text": distance.get("text"),
            "duration_minutes": duration_minutes,
            "duration_text": duration.get("text"),
            "traffic_minutes": traffic_minutes,
            "traffic_text": duration_in_traffic.get("text"),
            "traffic_impact_percent": traffic_impact,
            "start_address": leg.get("start_address"),
            "end_address": leg.get("end_address"),
            "route_geometry": route.get("overview_polyline", {}).get("points")
        }

    except requests.exceptions.Timeout:
        print("\n❌ Request timed out")
        return {"success": False, "error": "timeout"}
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return {"success": False, "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}


def main():
    """Run tests with example coordinates in Israel."""

    # Get API key from environment
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    if not api_key:
        print("\n❌ ERROR: GOOGLE_MAPS_API_KEY not found in .env file")
        print("\nPlease add your Google Maps API key to backend/.env:")
        print("GOOGLE_MAPS_API_KEY=your_api_key_here")
        return

    print("\n" + "="*60)
    print("Google Maps Traffic API Test")
    print("="*60)
    print(f"API Key: {api_key[:20]}...")

    # Test cases: Common commute routes in Israel
    test_cases = [
        {
            "name": "Tel Aviv to Jerusalem",
            "origin": (32.0853, 34.7818),  # Tel Aviv
            "destination": (31.7683, 35.2137)  # Jerusalem
        },
        {
            "name": "Haifa to Tel Aviv",
            "origin": (32.7940, 34.9896),  # Haifa
            "destination": (32.0853, 34.7818)  # Tel Aviv
        },
        {
            "name": "Petah Tikva to Herzliya",
            "origin": (32.0879, 34.8870),  # Petah Tikva
            "destination": (32.1624, 34.8446)  # Herzliya
        }
    ]

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}/{len(test_cases)}: {test['name']}")
        print(f"{'='*60}")

        result = test_google_maps_traffic(
            origin=test["origin"],
            destination=test["destination"],
            api_key=api_key
        )

        results.append({
            "name": test["name"],
            **result
        })

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}\n")

    successful = sum(1 for r in results if r.get("success"))
    print(f"Tests Run: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

    if successful > 0:
        print("\n✅ Google Maps Traffic API is working!")
        print("\nTraffic Impact Summary:")
        for r in results:
            if r.get("success"):
                impact = r.get("traffic_impact_percent", 0)
                print(f"  • {r['name']}: {impact:+.1f}% ({r.get('traffic_minutes', 0):.1f} min)")
    else:
        print("\n❌ All tests failed. Please check your API key and configuration.")


if __name__ == "__main__":
    main()
