# Distance Calculator

A robust distance calculation module for the Neighborhood Insights backend that provides accurate Haversine distance calculations between geographic coordinates.

## Features

- **Multiple coordinate formats**: Support for tuples, dictionaries, and Coordinate objects
- **Flexible distance calculations**: Calculate distances from one point to many points
- **Nearest neighbor search**: Find closest coordinates with optional limits
- **Radius search**: Get all coordinates within a specified distance
- **Distance matrix**: Calculate distances between all pairs of coordinates
- **Validated inputs**: Automatic validation of coordinate ranges

## Quick Start

```python
from routing.distance_calculator import calculate_distances_to_coordinates

# Simple example: Tel Aviv to other cities
tel_aviv = (32.0853, 34.7818)
cities = [
    (31.7683, 35.2137),  # Jerusalem
    (32.7940, 34.9896),  # Haifa
]

results = calculate_distances_to_coordinates(tel_aviv, cities)
for result in results:
    print(f"Distance: {result.distance_km:.2f} km")
```

## Core Functions

### `calculate_distances_to_coordinates(origin, coordinates)`
Calculate distances from a single origin to multiple target coordinates.

**Parameters:**
- `origin`: Origin coordinate (tuple, dict, or Coordinate object)
- `coordinates`: List of target coordinates

**Returns:** List of `DistanceResult` objects with distance_km, distance_m, index, and coordinate

### `find_nearest_coordinates(origin, coordinates, max_results=None, max_distance_km=None)`
Find the nearest coordinates sorted by distance.

**Parameters:**
- `origin`: Origin coordinate
- `coordinates`: List of target coordinates
- `max_results`: Maximum number of results to return
- `max_distance_km`: Maximum distance filter in kilometers

### `get_coordinates_within_radius(center, coordinates, radius_km)`
Get all coordinates within a specified radius.

### Convenience Functions

- `calculate_distances_from_dict_lists()`: For API-style dictionary format
- `calculate_distances_from_tuples()`: Simple tuple format returning just distances

## Coordinate Formats

The module supports three coordinate formats:

```python
# Tuple format (latitude, longitude)
coord_tuple = (32.0853, 34.7818)

# Dictionary format (common in APIs)
coord_dict = {"latitude": 32.0853, "longitude": 34.7818}

# Coordinate object
from routing.distance_calculator import Coordinate
coord_obj = Coordinate(latitude=32.0853, longitude=34.7818)
```

## Practical Examples

### Finding Nearest POIs
```python
user_location = {"latitude": 32.0740, "longitude": 34.7925}
poi_coords = [
    {"latitude": 32.1133, "longitude": 34.8044},  # University
    {"latitude": 32.0856, "longitude": 34.7862},  # Hospital
]

results = calculate_distances_from_dict_lists(user_location, poi_coords)
# Returns list of distance dictionaries
```

### Radius Search
```python
center = (32.0853, 34.7818)  # Tel Aviv
locations = [(32.0809, 34.7806), (31.7683, 35.2137), ...]  # Various points

nearby = get_coordinates_within_radius(center, locations, radius_km=20.0)
# Returns only locations within 20km
```

### Integration with FastAPI
```python
from fastapi import FastAPI
from routing.distance_calculator import find_nearest_coordinates

app = FastAPI()

@app.get("/nearest-pois")
def get_nearest_pois(lat: float, lon: float, limit: int = 5):
    user_location = (lat, lon)
    # poi_coordinates loaded from database

    nearest = find_nearest_coordinates(
        origin=user_location,
        coordinates=poi_coordinates,
        max_results=limit
    )

    return [
        {
            "distance_km": result.distance_km,
            "poi_index": result.index
        }
        for result in nearest
    ]
```

## Performance Notes

- Uses the Haversine formula for great-circle distances
- Accurate for distances up to several hundred kilometers
- Optimized for batch distance calculations
- Input validation ensures coordinate ranges are valid
- Results include both kilometers and meters for convenience

## Testing

Run the test suite to see examples and verify functionality:

```bash
cd backend/routing
python test_distance_calculator.py
```

This will demonstrate all features with real Israeli city coordinates.