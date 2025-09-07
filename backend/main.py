from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import csv
from pathlib import Path
from typing import Optional
from statistics import mean

app = FastAPI(title="Neighborhood Insights API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    # In dev, allow all origins to avoid CORS headaches
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to CSV files (resolve relative to this file so CWD doesn't matter)
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = (BASE_DIR.parent / "data" / "raw").resolve()

def is_in_israel(lat: float, lon: float) -> bool:
    """Check if coordinates are roughly within Israel's boundaries"""
    # Israel's approximate boundaries
    # Latitude: 29.5°N to 33.3°N
    # Longitude: 34.2°E to 35.9°E
    return (29.5 <= lat <= 33.3) and (34.2 <= lon <= 35.9)

def normalize_coordinates_to_israel(original_lat: float, original_lon: float, poi_id: int) -> tuple[float, float]:
    """Return the original WGS84 coordinates without modification.

    Previous versions perturbed coordinates to city centroids which caused
    POIs to appear in incorrect locations on the map. Our CSVs already
    contain WGS84 latitude/longitude, so no normalization is required.
    """
    return original_lat, original_lon

def load_csv_data():
    """Load all CSV files and combine them into a single dataset"""
    all_pois = []
    
    csv_files = list(DATA_PATH.glob("govmap_*.csv"))
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert numeric fields
                    if 'id' in row:
                        row['id'] = int(row['id'])
                    if 'latitude' in row and 'longitude' in row:
                        # Ensure numeric types; keep true coordinates
                        lat = float(row['latitude'])
                        lon = float(row['longitude'])
                        lat_norm, lon_norm = normalize_coordinates_to_israel(lat, lon, row['id'])
                        row['latitude'] = lat_norm
                        row['longitude'] = lon_norm
                        
                    all_pois.append(row)
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
    
    return all_pois

# Load data on startup
pois_data = load_csv_data()

@app.get("/")
def read_root():
    return {"message": "Neighborhood Insights API", "total_pois": len(pois_data)}

@app.get("/pois")
def get_all_pois(poi_type: Optional[str] = None, limit: Optional[int] = None):
    """Get all POIs, optionally filtered by type"""
    filtered_pois = pois_data
    
    if poi_type:
        filtered_pois = [poi for poi in pois_data if poi.get('type') == poi_type]
    
    if limit:
        filtered_pois = filtered_pois[:limit]
    
    return {
        "pois": filtered_pois,
        "total": len(filtered_pois),
        "available_types": list(set(poi.get('type') for poi in pois_data if poi.get('type')))
    }

@app.get("/pois/{poi_id}")
def get_poi_by_id(poi_id: int):
    """Get a specific POI by ID"""
    poi = next((p for p in pois_data if p.get('id') == poi_id), None)
    if not poi:
        return {"error": "POI not found"}
    return poi

@app.get("/pois/near")
def get_pois_near(lat: float, lon: float, radius_km: float = 5.0, poi_type: Optional[str] = None):
    """Get POIs within a certain radius of a point (simple distance calculation)"""
    import math
    
    def calculate_distance(lat1, lon1, lat2, lon2):
        # Simple Haversine formula
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    nearby_pois = []
    
    for poi in pois_data:
        if poi.get('latitude') and poi.get('longitude'):
            distance = calculate_distance(lat, lon, poi['latitude'], poi['longitude'])
            if distance <= radius_km:
                poi_with_distance = poi.copy()
                poi_with_distance['distance_km'] = round(distance, 2)
                if not poi_type or poi.get('type') == poi_type:
                    nearby_pois.append(poi_with_distance)
    
    # Sort by distance
    nearby_pois.sort(key=lambda x: x['distance_km'])
    
    return {
        "pois": nearby_pois,
        "total": len(nearby_pois),
        "search_center": {"latitude": lat, "longitude": lon},
        "radius_km": radius_km
    }

@app.get("/types")
def get_poi_types():
    """Get all available POI types"""
    types = list(set(poi.get('type') for poi in pois_data if poi.get('type')))
    type_counts = {poi_type: len([p for p in pois_data if p.get('type') == poi_type]) for poi_type in types}
    
    return {
        "types": types,
        "counts": type_counts,
        "total_types": len(types)
    }

@app.get("/debug/stats")
def debug_stats():
    """Return basic stats about loaded POIs to validate coordinates."""
    if not pois_data:
        return {"total": 0}

    lats = [p["latitude"] for p in pois_data if isinstance(p.get("latitude"), (int, float))]
    lons = [p["longitude"] for p in pois_data if isinstance(p.get("longitude"), (int, float))]
    types = list(set(p.get("type") for p in pois_data))
    return {
        "total": len(pois_data),
        "lat_min": min(lats),
        "lat_max": max(lats),
        "lat_mean": round(mean(lats), 6),
        "lon_min": min(lons),
        "lon_max": max(lons),
        "lon_mean": round(mean(lons), 6),
        "types": types[:10],
        "sample": pois_data[:3],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
