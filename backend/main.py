from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import csv
from pathlib import Path
import csv
import re
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

# Paths (resolve relative to this file so CWD doesn't matter)
BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = (BASE_DIR.parent / "data" / "raw").resolve()
PROCESSED_PATH = (BASE_DIR.parent / "data" / "processed").resolve()

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

def _safe_float(value: str) -> float | None:
    try:
        v = float(value)
        if v != v:  # NaN
            return None
        return v
    except Exception:
        return None

def load_mosdot_data():
    """Load POIs from the processed mosdot.csv only.

    Expected columns include at least: 'lon', 'lat', and Hebrew name fields.
    We coerce lon/lat to floats and skip rows without valid coordinates.
    """
    mosdot_file = PROCESSED_PATH / "mosdot.csv"
    pois: list[dict] = []
    if not mosdot_file.exists():
        print(f"mosdot.csv not found at {mosdot_file}")
        return pois

    try:
        # utf-8-sig to strip potential BOM
        with open(mosdot_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=1):
                lon = _safe_float(row.get("lon", ""))
                lat = _safe_float(row.get("lat", ""))
                if lon is None or lat is None:
                    continue

                # Filter to Israel-ish bounding box to avoid geocode outliers
                if not (29.0 <= lat <= 33.8 and 33.5 <= lon <= 36.5):
                    continue

                name_field = row.get("שם וסמל מוסד") or row.get("שם מוסד") or ""
                # Try to split code from name if formatted like "1234 Name"
                code_match = None
                if isinstance(name_field, str):
                    code_match = __import__('re').match(r"^(\d{2,6})\s+(.+)$", name_field.strip()) if name_field else None
                if code_match:
                    symbol_code = code_match.group(1)
                    name_he = code_match.group(2)
                else:
                    symbol_code = ""
                    name_he = name_field or row.get("כתובת") or "מוסד חינוך"
                name_en = row.get("יישוב") or row.get("כתובת למכתבים") or "Mosdot"
                frame_type = row.get("סוג מסגרת") or row.get("שלב חינוך") or "mosdot"
                address_line = row.get("כתובת") or ""
                city = row.get("יישוב") or ""
                address = ", ".join([part for part in [address_line, city] if part])

                # Derive a compact english-ish type key for filtering
                type_key = "mosdot"
                if isinstance(frame_type, str):
                    if "גן" in frame_type:
                        type_key = "kindergartens"
                    elif any(x in frame_type for x in ["בית ספר", "יסודי", "חטיבת", "תיכון"]):
                        type_key = "schools"

                pois.append({
                    "id": idx,
                    "name_he": name_he,
                    "name_en": str(name_en),
                    "type": type_key,
                    "longitude": lon,
                    "latitude": lat,
                    "address": address,
                    "symbol": symbol_code,
                })
    except Exception as e:
        print(f"Error loading mosdot.csv: {e}")

    return pois

# Load data on startup (mosdot only)
pois_data = load_mosdot_data()

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
