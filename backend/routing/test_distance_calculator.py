#!/usr/bin/env python3
"""
Test and demonstration of the distance calculator functions.
"""

from distance_calculator import (
    calculate_distances_to_coordinates,
    find_nearest_coordinates,
    get_coordinates_within_radius,
    calculate_distances_from_dict_lists,
    calculate_distances_from_tuples,
    Coordinate
)


def test_basic_distance_calculation():
    """Test basic distance calculation with different coordinate formats."""
    print("=== Basic Distance Calculation Test ===")

    # Tel Aviv coordinates
    tel_aviv = (32.0853, 34.7818)

    # Other Israeli cities
    cities = [
        (31.7683, 35.2137),  # Jerusalem
        (32.7940, 34.9896),  # Haifa
        (31.2518, 34.7915),  # Beer Sheva
        (32.3215, 34.8532),  # Netanya
    ]

    city_names = ["Jerusalem", "Haifa", "Beer Sheva", "Netanya"]

    results = calculate_distances_to_coordinates(tel_aviv, cities)

    print(f"Distances from Tel Aviv:")
    for i, result in enumerate(results):
        print(f"  To {city_names[i]}: {result.distance_km:.2f} km ({result.distance_m:.0f} m)")

    print()


def test_nearest_coordinates():
    """Test finding nearest coordinates."""
    print("=== Nearest Coordinates Test ===")

    # Tel Aviv
    origin = {"latitude": 32.0853, "longitude": 34.7818}

    # Various locations
    locations = [
        {"latitude": 31.7683, "longitude": 35.2137},  # Jerusalem
        {"latitude": 32.7940, "longitude": 34.9896},  # Haifa
        {"latitude": 32.0809, "longitude": 34.7806},  # Ramat Gan (very close)
        {"latitude": 31.2518, "longitude": 34.7915},  # Beer Sheva
        {"latitude": 32.0879, "longitude": 34.8017},  # Givatayim (close)
    ]

    location_names = ["Jerusalem", "Haifa", "Ramat Gan", "Beer Sheva", "Givatayim"]

    # Find 3 nearest locations
    nearest = find_nearest_coordinates(origin, locations, max_results=3)

    print("3 nearest locations to Tel Aviv:")
    for result in nearest:
        name = location_names[result.index]
        print(f"  {name}: {result.distance_km:.2f} km")

    print()


def test_radius_search():
    """Test finding coordinates within a radius."""
    print("=== Radius Search Test ===")

    # Tel Aviv center
    center = Coordinate(32.0853, 34.7818)

    # Various locations
    locations = [
        Coordinate(32.0809, 34.7806),  # Ramat Gan
        Coordinate(32.0879, 34.8017),  # Givatayim
        Coordinate(32.0667, 34.7667),  # Bat Yam
        Coordinate(31.7683, 35.2137),  # Jerusalem (far)
        Coordinate(32.1049, 34.8056),  # Petah Tikva
        Coordinate(32.7940, 34.9896),  # Haifa (far)
    ]

    location_names = ["Ramat Gan", "Givatayim", "Bat Yam", "Jerusalem", "Petah Tikva", "Haifa"]

    # Find locations within 20km
    within_radius = get_coordinates_within_radius(center, locations, radius_km=20.0)

    print("Locations within 20km of Tel Aviv:")
    for result in within_radius:
        name = location_names[result.index]
        print(f"  {name}: {result.distance_km:.2f} km")

    print()


def test_dict_format():
    """Test with dictionary format (common in APIs)."""
    print("=== Dictionary Format Test ===")

    origin = {"latitude": 32.0853, "longitude": 34.7818}  # Tel Aviv
    targets = [
        {"latitude": 31.7683, "longitude": 35.2137},  # Jerusalem
        {"latitude": 32.7940, "longitude": 34.9896},  # Haifa
    ]

    results = calculate_distances_from_dict_lists(origin, targets)

    print("Using dictionary format:")
    cities = ["Jerusalem", "Haifa"]
    for i, result in enumerate(results):
        print(f"  To {cities[i]}: {result['distance_km']:.2f} km")

    print()


def test_tuple_format():
    """Test with simple tuple format."""
    print("=== Tuple Format Test ===")

    origin = (32.0853, 34.7818)  # Tel Aviv
    targets = [
        (31.7683, 35.2137),  # Jerusalem
        (32.7940, 34.9896),  # Haifa
        (31.2518, 34.7915),  # Beer Sheva
    ]

    distances = calculate_distances_from_tuples(origin, targets)

    print("Using tuple format:")
    cities = ["Jerusalem", "Haifa", "Beer Sheva"]
    for i, distance in enumerate(distances):
        print(f"  To {cities[i]}: {distance:.2f} km")

    print()


def demo_practical_use_case():
    """Demonstrate a practical use case: finding nearest POIs."""
    print("=== Practical Use Case: Finding Nearest POIs ===")

    # User location (somewhere in Tel Aviv)
    user_location = {"latitude": 32.0740, "longitude": 34.7925}

    # Sample POIs (schools, clinics, etc.)
    pois = [
        {"name": "Tel Aviv University", "latitude": 32.1133, "longitude": 34.8044, "type": "university"},
        {"name": "Ichilov Hospital", "latitude": 32.0856, "longitude": 34.7862, "type": "hospital"},
        {"name": "Dizengoff Center", "latitude": 32.0748, "longitude": 34.7753, "type": "mall"},
        {"name": "Rabin Square", "latitude": 32.0809, "longitude": 34.7806, "type": "landmark"},
        {"name": "Port of Tel Aviv", "latitude": 32.0967, "longitude": 34.7689, "type": "port"},
    ]

    # Extract coordinates
    poi_coords = [{"latitude": poi["latitude"], "longitude": poi["longitude"]} for poi in pois]

    # Find nearest POIs
    results = calculate_distances_from_dict_lists(user_location, poi_coords)

    # Combine with POI information and sort by distance
    poi_distances = []
    for i, result in enumerate(results):
        poi_distances.append({
            "name": pois[i]["name"],
            "type": pois[i]["type"],
            "distance_km": result["distance_km"],
            "distance_m": result["distance_m"]
        })

    # Sort by distance
    poi_distances.sort(key=lambda x: x["distance_km"])

    print("Nearest POIs to user location:")
    for poi in poi_distances:
        print(f"  {poi['name']} ({poi['type']}): {poi['distance_km']:.2f} km")

    print()


if __name__ == "__main__":
    print("Distance Calculator Test Suite")
    print("=" * 50)

    test_basic_distance_calculation()
    test_nearest_coordinates()
    test_radius_search()
    test_dict_format()
    test_tuple_format()
    demo_practical_use_case()

    print("All tests completed successfully!")