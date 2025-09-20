#!/usr/bin/env python3
"""
Distance calculation functions for routing and proximity analysis.
"""

import math
from typing import List, Tuple, Union, Dict, Any
from dataclasses import dataclass


@dataclass
class Coordinate:
    """Represents a geographic coordinate."""
    latitude: float
    longitude: float

    def __post_init__(self):
        """Validate coordinate values."""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Invalid latitude: {self.latitude}. Must be between -90 and 90.")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Invalid longitude: {self.longitude}. Must be between -180 and 180.")


@dataclass
class DistanceResult:
    """Represents a distance calculation result."""
    distance_km: float
    distance_m: float
    index: int
    coordinate: Coordinate


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees

    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in kilometers
    r = 6371

    return c * r


def calculate_distances_to_coordinates(
    origin: Union[Coordinate, Tuple[float, float], Dict[str, float]],
    coordinates: List[Union[Coordinate, Tuple[float, float], Dict[str, float]]]
) -> List[DistanceResult]:
    """
    Calculate distances from a single origin point to a list of coordinates.

    Args:
        origin: Origin coordinate as Coordinate object, (lat, lon) tuple, or {'latitude': lat, 'longitude': lon} dict
        coordinates: List of target coordinates in same formats as origin

    Returns:
        List of DistanceResult objects, ordered by input sequence

    Example:
        >>> origin = (32.0853, 34.7818)  # Tel Aviv
        >>> targets = [(31.7683, 35.2137), (32.7940, 34.9896)]  # Jerusalem, Haifa
        >>> results = calculate_distances_to_coordinates(origin, targets)
        >>> print(f"Distance to Jerusalem: {results[0].distance_km:.2f} km")
    """
    # Normalize origin coordinate
    if isinstance(origin, tuple):
        origin_coord = Coordinate(latitude=origin[0], longitude=origin[1])
    elif isinstance(origin, dict):
        origin_coord = Coordinate(latitude=origin['latitude'], longitude=origin['longitude'])
    elif isinstance(origin, Coordinate):
        origin_coord = origin
    else:
        raise ValueError("Origin must be Coordinate, tuple (lat, lon), or dict with 'latitude' and 'longitude' keys")

    results = []

    for i, coord in enumerate(coordinates):
        # Normalize target coordinate
        if isinstance(coord, tuple):
            target_coord = Coordinate(latitude=coord[0], longitude=coord[1])
        elif isinstance(coord, dict):
            target_coord = Coordinate(latitude=coord['latitude'], longitude=coord['longitude'])
        elif isinstance(coord, Coordinate):
            target_coord = coord
        else:
            raise ValueError(f"Coordinate at index {i} must be Coordinate, tuple (lat, lon), or dict with 'latitude' and 'longitude' keys")

        # Calculate distance
        distance_km = haversine_distance(
            origin_coord.latitude, origin_coord.longitude,
            target_coord.latitude, target_coord.longitude
        )

        results.append(DistanceResult(
            distance_km=round(distance_km, 3),
            distance_m=round(distance_km * 1000, 1),
            index=i,
            coordinate=target_coord
        ))

    return results


def find_nearest_coordinates(
    origin: Union[Coordinate, Tuple[float, float], Dict[str, float]],
    coordinates: List[Union[Coordinate, Tuple[float, float], Dict[str, float]]],
    max_results: int = None,
    max_distance_km: float = None
) -> List[DistanceResult]:
    """
    Find the nearest coordinates to an origin point, sorted by distance.

    Args:
        origin: Origin coordinate
        coordinates: List of target coordinates
        max_results: Maximum number of results to return (default: all)
        max_distance_km: Maximum distance in kilometers to include (default: no limit)

    Returns:
        List of DistanceResult objects, sorted by distance (nearest first)
    """
    # Calculate all distances
    results = calculate_distances_to_coordinates(origin, coordinates)

    # Filter by max distance if specified
    if max_distance_km is not None:
        results = [r for r in results if r.distance_km <= max_distance_km]

    # Sort by distance
    results.sort(key=lambda x: x.distance_km)

    # Limit results if specified
    if max_results is not None:
        results = results[:max_results]

    return results


def calculate_distance_matrix(
    coordinates: List[Union[Coordinate, Tuple[float, float], Dict[str, float]]]
) -> List[List[float]]:
    """
    Calculate a distance matrix between all pairs of coordinates.

    Args:
        coordinates: List of coordinates

    Returns:
        2D list where matrix[i][j] is the distance from coordinate i to coordinate j in kilometers
    """
    n = len(coordinates)
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i != j:
                distances = calculate_distances_to_coordinates(coordinates[i], [coordinates[j]])
                matrix[i][j] = distances[0].distance_km

    return matrix


def get_coordinates_within_radius(
    center: Union[Coordinate, Tuple[float, float], Dict[str, float]],
    coordinates: List[Union[Coordinate, Tuple[float, float], Dict[str, float]]],
    radius_km: float
) -> List[DistanceResult]:
    """
    Get all coordinates within a specified radius of a center point.

    Args:
        center: Center coordinate
        coordinates: List of coordinates to check
        radius_km: Radius in kilometers

    Returns:
        List of DistanceResult objects within the radius, sorted by distance
    """
    return find_nearest_coordinates(
        origin=center,
        coordinates=coordinates,
        max_distance_km=radius_km
    )


# Convenience functions for common coordinate formats

def calculate_distances_from_dict_lists(
    origin: Dict[str, float],
    targets: List[Dict[str, float]]
) -> List[Dict[str, Any]]:
    """
    Calculate distances using dictionary format (common in APIs).

    Args:
        origin: {'latitude': lat, 'longitude': lon}
        targets: List of {'latitude': lat, 'longitude': lon} dicts

    Returns:
        List of distance result dictionaries
    """
    results = calculate_distances_to_coordinates(origin, targets)

    return [
        {
            'distance_km': result.distance_km,
            'distance_m': result.distance_m,
            'index': result.index,
            'target_coordinate': {
                'latitude': result.coordinate.latitude,
                'longitude': result.coordinate.longitude
            }
        }
        for result in results
    ]


def calculate_distances_from_tuples(
    origin: Tuple[float, float],
    targets: List[Tuple[float, float]]
) -> List[float]:
    """
    Calculate distances using tuple format, returning just distances.

    Args:
        origin: (latitude, longitude)
        targets: List of (latitude, longitude) tuples

    Returns:
        List of distances in kilometers
    """
    results = calculate_distances_to_coordinates(origin, targets)
    return [result.distance_km for result in results]