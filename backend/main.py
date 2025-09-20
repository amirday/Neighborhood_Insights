from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import csv
import json
from pathlib import Path
import csv
import re
from typing import Optional
from statistics import mean
import geopandas as gpd
import pandas as pd

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
STATIC_DATA_PATH = (BASE_DIR.parent / "app" / "public" / "data").resolve()

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
    mosdot_file = PROCESSED_PATH / "mosdot_2.csv"
    pois: list[dict] = []
    if not mosdot_file.exists():
        print(f"mosdot.csv not found at {mosdot_file}")
        return pois

    # Counters for debugging
    total_rows = 0
    no_coords_count = 0
    out_of_bounds_count = 0

    try:
        # utf-8-sig to strip potential BOM
        with open(mosdot_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=1):
                total_rows += 1
                lon = _safe_float(row.get("lon", ""))
                lat = _safe_float(row.get("lat", ""))
                if lon is None or lat is None:
                    no_coords_count += 1
                    continue

                # Filter to Israel-ish bounding box to avoid geocode outliers
                if not (29.0 <= lat <= 33.8 and 34.2 <= lon <= 35.9):
                    out_of_bounds_count += 1
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

    print(f"DATA LOADING SUMMARY:")
    print(f"  Total rows processed: {total_rows}")
    print(f"  Rows without coordinates: {no_coords_count}")
    print(f"  Rows outside bounds: {out_of_bounds_count}")
    print(f"  POIs loaded: {len(pois)}")
    print(f"  Success rate: {len(pois)/total_rows*100:.1f}%")

    return pois

def load_statistical_areas():
    """Load statistical areas data from processed files."""

    parquet_path = PROCESSED_PATH / "statistical_areas_2022.parquet"
    metadata_path = PROCESSED_PATH / "statistical_areas_metadata.json"

    areas_data = {}

    # Load metadata if available
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                areas_data['metadata'] = json.load(f)
        except Exception as e:
            print(f"Error loading statistical areas metadata: {e}")
            areas_data['metadata'] = {}

    # Load the actual geodata
    if parquet_path.exists():
        try:
            gdf = gpd.read_parquet(parquet_path)
            areas_data['gdf'] = gdf
            areas_data['total'] = len(gdf)
            print(f"Loaded {len(gdf)} statistical areas from parquet")
        except Exception as e:
            print(f"Error loading statistical areas parquet: {e}")
            areas_data['gdf'] = None
            areas_data['total'] = 0
    else:
        print(f"Statistical areas parquet not found at {parquet_path}")
        areas_data['gdf'] = None
        areas_data['total'] = 0

    return areas_data

def load_job_centers():
    """Load job centers data from processed files."""

    parquet_path = PROCESSED_PATH / "job_centers.parquet"
    metadata_path = PROCESSED_PATH / "job_centers_metadata.json"

    job_centers_data = {}

    # Load metadata if available
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                job_centers_data['metadata'] = json.load(f)
        except Exception as e:
            print(f"Error loading job centers metadata: {e}")
            job_centers_data['metadata'] = {}

    # Load the actual data
    if parquet_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            job_centers_data['data'] = df.to_dict('records')
            job_centers_data['total'] = len(df)
            print(f"Loaded {len(df)} job centers from parquet")
        except Exception as e:
            print(f"Error loading job centers parquet: {e}")
            job_centers_data['data'] = []
            job_centers_data['total'] = 0
    else:
        print(f"Job centers parquet not found at {parquet_path}")
        job_centers_data['data'] = []
        job_centers_data['total'] = 0

    return job_centers_data

# Load data on startup
pois_data = load_mosdot_data()
statistical_areas = load_statistical_areas()
job_centers = load_job_centers()

@app.get("/")
def read_root():
    return {
        "message": "Neighborhood Insights API",
        "total_pois": len(pois_data),
        "total_statistical_areas": statistical_areas.get('total', 0),
        "total_job_centers": job_centers.get('total', 0)
    }

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

# Statistical Areas Endpoints

@app.get("/statistical-areas/info")
def get_statistical_areas_info():
    """Get information about statistical areas data."""
    return {
        "total_areas": statistical_areas.get('total', 0),
        "metadata": statistical_areas.get('metadata', {}),
        "data_available": statistical_areas.get('gdf') is not None
    }

@app.get("/statistical-areas/geojson")
def get_statistical_areas_geojson():
    """Serve the lightweight GeoJSON file for web mapping."""
    geojson_path = STATIC_DATA_PATH / "statistical_areas.geojson"
    if geojson_path.exists():
        return FileResponse(
            geojson_path,
            media_type="application/geo+json",
            filename="statistical_areas.geojson"
        )
    return {"error": "Statistical areas GeoJSON not found"}

@app.get("/statistical-areas/boundaries")
def get_statistical_areas_boundaries():
    """Serve the boundaries-only GeoJSON file for lightweight rendering."""
    boundaries_path = STATIC_DATA_PATH / "statistical_areas_boundaries.geojson"
    if boundaries_path.exists():
        return FileResponse(
            boundaries_path,
            media_type="application/geo+json",
            filename="statistical_areas_boundaries.geojson"
        )
    return {"error": "Statistical areas boundaries not found"}

@app.get("/statistical-areas/search")
def search_statistical_areas(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    bounds: Optional[str] = None
):
    """Search statistical areas by point or bounding box."""
    if statistical_areas.get('gdf') is None:
        return {"error": "Statistical areas data not available"}

    gdf = statistical_areas['gdf']

    if lat is not None and lon is not None:
        # Point-in-polygon search
        from shapely.geometry import Point
        point = Point(lon, lat)

        # Find areas containing the point
        contains_mask = gdf.geometry.contains(point)
        result_gdf = gdf[contains_mask]

        if len(result_gdf) > 0:
            # Convert to regular dict (without geometry for JSON response)
            results = []
            for idx, row in result_gdf.iterrows():
                area_info = row.drop('geometry').to_dict()

                # Clean NaN values for JSON serialization
                cleaned_info = {}
                for key, value in area_info.items():
                    if pd.isna(value):
                        cleaned_info[key] = None
                    elif isinstance(value, float) and (value != value):  # Check for NaN
                        cleaned_info[key] = None
                    else:
                        cleaned_info[key] = value

                # Add bounds for the area
                bounds = row.geometry.bounds
                cleaned_info['bounds'] = {
                    'min_lon': bounds[0],
                    'min_lat': bounds[1],
                    'max_lon': bounds[2],
                    'max_lat': bounds[3]
                }
                results.append(cleaned_info)

            return {
                "areas": results,
                "total": len(results),
                "search_point": {"latitude": lat, "longitude": lon}
            }
        else:
            return {
                "areas": [],
                "total": 0,
                "search_point": {"latitude": lat, "longitude": lon},
                "message": "No statistical area found at this location"
            }

    elif bounds:
        # Bounding box search
        try:
            # Expect bounds as "min_lon,min_lat,max_lon,max_lat"
            min_lon, min_lat, max_lon, max_lat = map(float, bounds.split(','))

            from shapely.geometry import box
            bbox = box(min_lon, min_lat, max_lon, max_lat)

            # Find areas that intersect with the bounding box
            intersects_mask = gdf.geometry.intersects(bbox)
            result_gdf = gdf[intersects_mask]

            # Return basic info (no geometry)
            results = []
            for idx, row in result_gdf.iterrows():
                area_info = row.drop('geometry').to_dict()

                # Clean NaN values for JSON serialization
                cleaned_info = {}
                for key, value in area_info.items():
                    if pd.isna(value):
                        cleaned_info[key] = None
                    elif isinstance(value, float) and (value != value):  # Check for NaN
                        cleaned_info[key] = None
                    else:
                        cleaned_info[key] = value

                results.append(cleaned_info)

            return {
                "areas": results,
                "total": len(results),
                "search_bounds": {
                    "min_lon": min_lon,
                    "min_lat": min_lat,
                    "max_lon": max_lon,
                    "max_lat": max_lat
                }
            }

        except ValueError:
            return {"error": "Invalid bounds format. Use: min_lon,min_lat,max_lon,max_lat"}

    else:
        return {"error": "Provide either lat/lon for point search or bounds for area search"}

# Job Centers Endpoints

@app.get("/job-centers/info")
def get_job_centers_info():
    """Get information about job centers data."""
    return {
        "total_job_centers": job_centers.get('total', 0),
        "metadata": job_centers.get('metadata', {}),
        "data_available": len(job_centers.get('data', [])) > 0
    }

@app.get("/job-centers")
def get_all_job_centers(limit: Optional[int] = None):
    """Get all job centers, optionally limited."""
    job_centers_data = job_centers.get('data', [])

    if limit:
        job_centers_data = job_centers_data[:limit]

    return {
        "job_centers": job_centers_data,
        "total": len(job_centers_data),
        "metadata": job_centers.get('metadata', {})
    }

@app.get("/job-centers/{center_id}")
def get_job_center_by_id(center_id: int):
    """Get a specific job center by ID."""
    job_centers_data = job_centers.get('data', [])
    center = next((c for c in job_centers_data if c.get('id') == center_id), None)
    if not center:
        return {"error": "Job center not found"}
    return center

@app.get("/job-centers/near")
def get_job_centers_near(lat: float, lon: float, radius_km: float = 10.0):
    """Get job centers within a certain radius of a point."""
    import math

    def calculate_distance(lat1, lon1, lat2, lon2):
        # Simple Haversine formula
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    nearby_centers = []
    job_centers_data = job_centers.get('data', [])

    for center in job_centers_data:
        if center.get('latitude') and center.get('longitude'):
            distance = calculate_distance(lat, lon, center['latitude'], center['longitude'])
            if distance <= radius_km:
                center_with_distance = center.copy()
                center_with_distance['distance_km'] = round(distance, 2)
                nearby_centers.append(center_with_distance)

    # Sort by distance
    nearby_centers.sort(key=lambda x: x['distance_km'])

    return {
        "job_centers": nearby_centers,
        "total": len(nearby_centers),
        "search_center": {"latitude": lat, "longitude": lon},
        "radius_km": radius_km
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
