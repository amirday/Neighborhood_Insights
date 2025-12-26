from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import csv
import json
from pathlib import Path
import re
import time
from typing import Optional
from statistics import mean
import geopandas as gpd
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Routing utilities
try:
    from routing.osrm_router import OSRMRouter, RouteResult
except Exception:
    # Fallback if relative import fails in some contexts
    from .routing.osrm_router import OSRMRouter, RouteResult

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
    mosdot_file = PROCESSED_PATH / "mosdot.csv"
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

@app.get("/health/routing")
def check_routing_health():
    """Check if Mapbox routing API is accessible"""
    router = OSRMRouter()

    # Test with a simple route in Israel (Tel Aviv to nearby point)
    tel_aviv = (32.0853, 34.7818)
    nearby = (32.0900, 34.7850)

    result = router.calculate_route_time(tel_aviv, nearby, "driving")

    return {
        "routing_available": result.success,
        "provider": "Mapbox Directions API",
        "error_message": result.error_message if not result.success else None,
        "test_route": "Tel Aviv (short distance)",
        "recommendation": "Check Mapbox token" if not result.success else "Routing API working"
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

# ---------------------------
# Routing: Areas -> Job Center
# ---------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


@app.post("/routes/areas-to-center")
def calculate_routes_areas_to_center(payload: dict):
    """
    Calculate routing times from statistical area centroids to a job center.

    Body JSON:
    - center_id: int (required)
    - threshold_minutes: float (optional, filters candidates by approx driving time)
    - approx_speed_kmh: float (optional, default 40)
    - modes: list[str] (optional, any of ["driving","cycling","walking","transit"]) – default all

    Returns JSON with per-area minutes for requested modes. Only areas whose
    approximate driving time is <= threshold_minutes are processed (if provided).
    """
    start_time = time.time()

    try:
        center_id = int(payload.get("center_id"))
    except Exception:
        return {"error": "center_id is required and must be an integer"}

    threshold_minutes = payload.get("threshold_minutes")
    try:
        threshold_minutes = float(threshold_minutes) if threshold_minutes is not None else None
    except Exception:
        return {"error": "threshold_minutes must be a number"}

    approx_speed_kmh = payload.get("approx_speed_kmh")
    try:
        approx_speed_kmh = float(approx_speed_kmh) if approx_speed_kmh is not None else 40.0
    except Exception:
        approx_speed_kmh = 40.0

    modes = payload.get("modes") or ["driving", "cycling", "walking", "transit"]
    valid_modes = {"driving", "cycling", "walking", "transit"}
    modes = [m for m in modes if m in valid_modes]
    if not modes:
        modes = ["driving", "cycling", "walking", "transit"]

    # Validate data availability
    gdf = statistical_areas.get('gdf')
    centers = job_centers.get('data', [])
    if gdf is None or not len(gdf):
        return {"error": "Statistical areas data not available"}
    if not centers:
        return {"error": "Job centers data not available"}

    center = next((c for c in centers if c.get('id') == center_id), None)
    if not center:
        return {"error": f"Job center {center_id} not found"}

    center_coord = (float(center.get('latitude')), float(center.get('longitude')))

    # Build list of candidate areas with centroids
    # Prefer OBJECTID if present; else fallback to index
    candidates = []
    for idx, row in gdf.iterrows():
        geom = row.get('geometry')
        if geom is None or geom.is_empty:
            continue
        try:
            centroid = geom.centroid
            lat, lon = float(centroid.y), float(centroid.x)
        except Exception:
            continue
        area_id = row.get('OBJECTID', idx)

        # Optional approximate filtering by driving time
        if threshold_minutes is not None and approx_speed_kmh > 0:
            dist_km = _haversine_km(lat, lon, center_coord[0], center_coord[1])
            approx_minutes = (dist_km / approx_speed_kmh) * 60.0
            if approx_minutes > threshold_minutes:
                continue

        candidates.append({
            "area_id": int(area_id) if area_id is not None else int(idx),
            "lat": lat,
            "lon": lon,
        })

    if not candidates:
        return {
            "center_id": center_id,
            "modes": modes,
            "total_candidates": 0,
            "areas": []
        }

    # Perform routing per mode using OSRM where applicable
    router = OSRMRouter()

    def _compute_mode(mode: str) -> dict:
        results: dict[int, dict] = {}
        # Use threads for concurrency (50 workers for I/O-bound OSRM requests)
        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_id = {}
            for cand in candidates:
                origin = (cand["lat"], cand["lon"])  # area -> center
                # Transit mode: use driving time × 2 as heuristic
                if mode == "transit":
                    future = executor.submit(router.calculate_route_time, origin, center_coord, "driving")
                    future_to_id[future] = (cand["area_id"], True)  # Mark as transit heuristic
                else:
                    future = executor.submit(router.calculate_route_time, origin, center_coord, mode)
                    future_to_id[future] = (cand["area_id"], False)

            for future in as_completed(future_to_id):
                area_id, is_transit_heuristic = future_to_id[future]
                try:
                    res: RouteResult = future.result()
                    if is_transit_heuristic and res.success:
                        # Double the driving time for transit estimate
                        results[area_id] = {
                            "duration_minutes": round(res.duration_minutes * 2, 1),
                            "distance_km": round(res.distance_km, 2),
                            "success": True,
                            "mode": "transit",
                            "method": "heuristic_2x_driving"
                        }
                    else:
                        results[area_id] = {
                            "duration_minutes": round(res.duration_minutes, 1) if res.success else None,
                            "distance_km": round(res.distance_km, 2) if res.success else None,
                            "success": bool(res.success),
                            "mode": mode
                        }
                except Exception as e:
                    results[area_id] = {
                        "duration_minutes": None,
                        "distance_km": None,
                        "success": False,
                        "mode": mode,
                        "error": str(e)
                    }
        return results

    per_mode_results: dict[str, dict] = {}
    for mode in modes:
        per_mode_results[mode] = _compute_mode(mode)

    # Merge per-mode results per area
    areas_out = []
    for cand in candidates:
        aid = cand["area_id"]
        entry = {
            "area_id": aid,
            "centroid": {"latitude": cand["lat"], "longitude": cand["lon"]},
            "results": {}
        }
        for mode in modes:
            if aid in per_mode_results.get(mode, {}):
                entry["results"][mode] = per_mode_results[mode][aid]
        areas_out.append(entry)

    processing_time = time.time() - start_time

    # Calculate success/failure statistics per mode
    stats = {}
    for mode in modes:
        mode_results = per_mode_results.get(mode, {})
        successful = sum(1 for r in mode_results.values() if r.get('success'))
        failed = len(mode_results) - successful
        stats[mode] = {
            "successful": successful,
            "failed": failed,
            "success_rate": round(successful / len(mode_results) * 100, 1) if mode_results else 0
        }

    # Overall stats
    total_requests = len(candidates) * len(modes)
    total_successful = sum(s["successful"] for s in stats.values())
    total_failed = sum(s["failed"] for s in stats.values())

    return {
        "center_id": center_id,
        "modes": modes,
        "total_candidates": len(candidates),
        "processing_time_seconds": round(processing_time, 2),
        "statistics": {
            "total_requests": total_requests,
            "successful": total_successful,
            "failed": total_failed,
            "success_rate": round(total_successful / total_requests * 100, 1) if total_requests else 0,
            "by_mode": stats
        },
        "areas": areas_out
    }


@app.get("/routes/area-to-center")
def calculate_route_area_to_center(center_id: int, area_id: int, modes: Optional[str] = None, include_geometry: bool = False):
    """
    Calculate routing from a specific statistical area centroid to a job center.

    Query params:
    - center_id: job center ID
    - area_id: statistical area OBJECTID
    - modes: comma-separated list among driving,cycling,walking,transit (default all)
    - include_geometry: if true, include route geometry for non-transit modes
    """
    gdf = statistical_areas.get('gdf')
    centers = job_centers.get('data', [])
    if gdf is None or not len(gdf):
        return {"error": "Statistical areas data not available"}
    if not centers:
        return {"error": "Job centers data not available"}

    center = next((c for c in centers if c.get('id') == center_id), None)
    if not center:
        return {"error": f"Job center {center_id} not found"}

    center_coord = (float(center.get('latitude')), float(center.get('longitude')))

    # Find area by OBJECTID
    try:
        # Try exact match
        sel = gdf[gdf['OBJECTID'] == area_id]
        if sel.empty:
            # Try casting OBJECTID to int (handles float/object dtypes)
            try:
                sel = gdf[gdf['OBJECTID'].astype(int) == int(area_id)]
            except Exception:
                sel = gdf
                sel = sel[sel['OBJECTID'].apply(lambda v: int(v) == int(area_id) if pd.notna(v) else False)]
        row = sel.iloc[0]
    except Exception:
        return {"error": f"Area {area_id} not found"}

    geom = row.get('geometry')
    if geom is None or geom.is_empty:
        return {"error": f"Area {area_id} has no geometry"}

    centroid = geom.centroid
    origin = (float(centroid.y), float(centroid.x))

    mode_list = ["driving", "cycling", "walking", "transit"]
    if modes:
        requested = [m.strip() for m in str(modes).split(',') if m.strip()]
        valid = {"driving", "cycling", "walking", "transit"}
        mode_list = [m for m in requested if m in valid] or mode_list

    router = OSRMRouter()
    results: dict[str, dict] = {}
    for mode in mode_list:
        if mode == "transit":
            # No graceful fallback for transit
            results[mode] = {
                "duration_minutes": None,
                "distance_km": None,
                "success": False,
                "mode": "transit",
                "error": "Transit routing not supported"
            }
            continue
        try:
            res = router.calculate_route_time(origin, center_coord, mode, return_geometry=include_geometry)
            payload = {
                "duration_minutes": round(res.duration_minutes, 1) if res.success else None,
                "distance_km": round(res.distance_km, 2) if res.success else None,
                "success": bool(res.success),
                "mode": mode,
                "error": res.error_message,
            }
            if include_geometry and res.geometry:
                # geometry is list of (lat, lon) pairs
                payload["geometry"] = res.geometry
            results[mode] = payload
        except Exception as e:
            results[mode] = {"duration_minutes": None, "distance_km": None, "success": False, "mode": mode, "error": str(e)}

    return {
        "center_id": center_id,
        "area_id": area_id,
        "origin": {"latitude": origin[0], "longitude": origin[1]},
        "destination": {"latitude": center_coord[0], "longitude": center_coord[1]},
        "results": results,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
