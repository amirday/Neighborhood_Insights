# Routing Module

A comprehensive routing module for the Neighborhood Insights backend that provides both straight-line distance calculations and real-world routing with road snapping using OSRM.

## Features

### Distance Calculator (Haversine)
- **Multiple coordinate formats**: Support for tuples, dictionaries, and Coordinate objects
- **Flexible distance calculations**: Calculate distances from one point to many points
- **Nearest neighbor search**: Find closest coordinates with optional limits
- **Radius search**: Get all coordinates within a specified distance
- **Distance matrix**: Calculate distances between all pairs of coordinates
- **Validated inputs**: Automatic validation of coordinate ranges

### OSRM Router (Real Roads)
- **Multiple transport modes**: Car, bicycle, and walking with different speeds
- **Road snapping**: Routes follow actual roads and paths
- **Batch processing**: Efficient calculation for multiple destinations
- **Caching**: In-memory cache with TTL for performance
- **Error handling**: Returns detailed error messages when OSRM unavailable
- **Async support**: Concurrent requests for better performance

## Quick Start

### Simple Distance (Haversine)
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

### Real-World Routing (OSRM)
```python
from routing.osrm_router import calculate_commute_time

# Calculate real driving time
tel_aviv = (32.0853, 34.7818)
jerusalem = (31.7683, 35.2137)

result = calculate_commute_time(tel_aviv, jerusalem, "driving")
print(f"Driving time: {result.duration_minutes:.1f} minutes")
print(f"Distance: {result.distance_km:.1f} km")
```

## OSRM Routing Functions

### `calculate_commute_time(origin, destination, transport_mode="driving")`
Calculate real-world commute time between two coordinates using OSRM.

**Parameters:**
- `origin`: Origin coordinate (lat, lon) tuple
- `destination`: Destination coordinate (lat, lon) tuple
- `transport_mode`: "driving", "cycling", or "walking"

**Returns:** `RouteResult` object with duration, distance, and success status

**Example:**
```python
from routing.osrm_router import calculate_commute_time

tel_aviv = (32.0853, 34.7818)
jerusalem = (31.7683, 35.2137)

# Driving time
result = calculate_commute_time(tel_aviv, jerusalem, "driving")
print(f"Drive: {result.duration_minutes:.1f} min, {result.distance_km:.1f} km")

# Cycling time
result = calculate_commute_time(tel_aviv, jerusalem, "cycling")
print(f"Bike: {result.duration_minutes:.1f} min")

# Walking time
result = calculate_commute_time(tel_aviv, jerusalem, "walking")
print(f"Walk: {result.duration_minutes:.1f} min")
```

### `calculate_routes_optimized(origin, destinations, transport_mode="driving")`
Efficiently calculate routes to multiple destinations with caching and batch processing.

**Parameters:**
- `origin`: Origin coordinate (lat, lon) tuple
- `destinations`: List of destination coordinates
- `transport_mode`: "driving", "cycling", or "walking"

**Returns:** List of `RouteResult` objects

**Example:**
```python
from routing.route_optimizer import calculate_routes_optimized

tel_aviv = (32.0853, 34.7818)
destinations = [
    (31.7683, 35.2137),  # Jerusalem
    (32.7940, 34.9896),  # Haifa
    (31.2518, 34.7915),  # Beer Sheva
]

results = calculate_routes_optimized(tel_aviv, destinations, "driving")
for i, result in enumerate(results):
    print(f"To destination {i+1}: {result.duration_minutes:.1f} minutes")
```

### Transport Modes

| Mode | Profile | Avg Speed | Max Distance | Description |
|------|---------|-----------|--------------|-------------|
| `driving` | Car/vehicle | 40 km/h | 500 km | Road routing for cars |
| `cycling` | Bicycle | 15 km/h | 100 km | Bike-friendly paths |
| `walking` | Pedestrian | 5 km/h | 25 km | Walkable routes |

### RouteResult Object

```python
@dataclass
class RouteResult:
    duration_seconds: float      # Route time in seconds
    duration_minutes: float      # Route time in minutes
    distance_meters: float       # Route distance in meters
    distance_km: float          # Route distance in kilometers
    transport_mode: str         # Transport mode used
    geometry: Optional[List]    # Route coordinates (if requested)
    success: bool              # Whether calculation succeeded
    error_message: Optional[str] # Error details if failed
    used_fallback: bool        # Whether Haversine fallback was used
```

## Advanced Usage

### Batch Processing with Caching
```python
from routing.route_optimizer import RouteBatchProcessor

processor = RouteBatchProcessor(max_workers=10, use_async=True)

# Process many destinations efficiently
origin = (32.0853, 34.7818)
many_destinations = [...]  # List of 100+ destinations

results = processor.calculate_routes_batch(origin, many_destinations, "driving")

# Check cache performance
stats = processor.get_cache_stats()
print(f"Cache size: {stats['cache_size']}")
```

### Distance Matrix
```python
from routing.route_optimizer import RouteBatchProcessor

processor = RouteBatchProcessor()
coordinates = [
    (32.0853, 34.7818),  # Tel Aviv
    (31.7683, 35.2137),  # Jerusalem
    (32.7940, 34.9896),  # Haifa
]

# Calculate all-to-all distances
matrix = processor.calculate_distance_matrix(coordinates, "driving")

# matrix[i][j] is the route from coordinate i to coordinate j
print(f"Tel Aviv to Jerusalem: {matrix[0][1].duration_minutes:.1f} minutes")
```

### Async Processing
```python
import asyncio
from routing.route_optimizer import AsyncOSRMRouter

async def calculate_async():
    router = AsyncOSRMRouter()
    origin = (32.0853, 34.7818)
    destinations = [(31.7683, 35.2137), (32.7940, 34.9896)]

    results = await router.calculate_routes_async(origin, destinations, "driving")
    return results

# Run async calculation
results = asyncio.run(calculate_async())
```

### Error Handling and Fallback
```python
from routing.osrm_router import calculate_commute_time

result = calculate_commute_time(origin, destination, "driving")

if result.success:
    if result.used_fallback:
        print(f"Used fallback calculation: {result.duration_minutes:.1f} min")
    else:
        print(f"OSRM routing: {result.duration_minutes:.1f} min")
else:
    print(f"Routing failed: {result.error_message}")
```

## Configuration

### OSRM Server Settings
Edit `transport_modes.py` to configure OSRM server URLs:

```python
# Use local OSRM server
OSRM_BASE_URL = "http://localhost:5000"

# Or use different public server
OSRM_BASE_URL = "https://your-osrm-server.com"
```

### Transport Mode Customization
```python
from routing.transport_modes import TransportModes

# Access mode configurations
driving_config = TransportModes.DRIVING
print(f"Average speed: {driving_config.average_speed_kmh} km/h")

# Check if mode is valid
if TransportModes.is_valid_mode("driving"):
    print("Valid transport mode")
```

### Cache Configuration
```python
from routing.route_optimizer import RouteCache

# Custom cache with 2-hour TTL
cache = RouteCache(ttl_seconds=7200)

# Manual cache management
cache.set("key", route_result)
cached = cache.get("key")
cache.cleanup_expired()
cache.clear()
```

## Performance Notes

- **OSRM API**: Uses public OSRM server with rate limits
- **Caching**: Results cached for 1 hour by default
- **Batch processing**: Concurrent requests for multiple destinations
- **Error handling**: Returns detailed error messages when OSRM unavailable
- **Async support**: Better performance for large batches (>5 destinations)

## Distance Calculator (Legacy)

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