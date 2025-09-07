from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import csv
from pathlib import Path
from typing import Optional

app = FastAPI(title="Neighborhood Insights API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to CSV files
DATA_PATH = Path("../data/raw")

def is_in_israel(lat: float, lon: float) -> bool:
    """Check if coordinates are roughly within Israel's boundaries"""
    # Israel's approximate boundaries
    # Latitude: 29.5°N to 33.3°N
    # Longitude: 34.2°E to 35.9°E
    return (29.5 <= lat <= 33.3) and (34.2 <= lon <= 35.9)

def normalize_coordinates_to_israel(lat: float, lon: float) -> tuple[float, float]:
    """Normalize coordinates to fall within Israel's boundaries"""
    # If coordinates are way off, place them in central Israel
    if not (25 <= lat <= 40) or not (30 <= lon <= 40):
        # Return coordinates near Jerusalem as default
        return 31.7683 + (lat % 1) * 0.5, 35.2137 + (lon % 1) * 0.5
    
    # Constrain to Israel's boundaries
    lat_normalized = max(29.5, min(33.3, lat))
    lon_normalized = max(34.2, min(35.9, lon))
    
    return lat_normalized, lon_normalized

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
                        lat = float(row['latitude'])
                        lon = float(row['longitude'])
                        
                        # Normalize coordinates to Israel
                        lat_norm, lon_norm = normalize_coordinates_to_israel(lat, lon)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)