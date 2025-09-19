#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Process statistical areas 2022 shapefile data and convert to optimized formats for web serving.

This script:
1. Loads the statistical areas shapefile
2. Converts to WGS84 (EPSG:4326) for web compatibility
3. Simplifies geometries for better performance
4. Saves as both GeoJSON and Parquet formats
5. Creates a lightweight version for web serving

Usage:
    python process_statistical_areas.py
"""

import os
import sys
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Paths
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "statistical_areas_2022"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"
STATIC_DATA_PATH = PROJECT_ROOT / "app" / "public" / "data"

# Ensure output directories exist
PROCESSED_DATA_PATH.mkdir(parents=True, exist_ok=True)
STATIC_DATA_PATH.mkdir(parents=True, exist_ok=True)

def load_statistical_areas():
    """Load the statistical areas shapefile."""
    shapefile_path = RAW_DATA_PATH / "statistical_areas_2022.shp"

    if not shapefile_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")

    print(f"Loading shapefile: {shapefile_path}")
    gdf = gpd.read_file(shapefile_path)

    print(f"Loaded {len(gdf)} statistical areas")
    print(f"Original CRS: {gdf.crs}")
    print(f"Columns: {list(gdf.columns)}")

    return gdf

def process_statistical_areas(gdf):
    """Process and clean the statistical areas data."""

    # Convert to WGS84 for web compatibility
    if gdf.crs != 'EPSG:4326':
        print("Converting to WGS84 (EPSG:4326)...")
        gdf = gdf.to_crs('EPSG:4326')

    # Print some basic info about the data
    print(f"Bounds: {gdf.total_bounds}")
    print(f"Sample of first few rows:")
    print(gdf.head()[['geometry'] + [col for col in gdf.columns if col != 'geometry'][:5]])

    # Simplify geometries for better web performance
    # Use a small tolerance to preserve detail while reducing file size
    print("Simplifying geometries...")
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.0001, preserve_topology=True)

    # Filter to areas within Israel's bounds (approximate)
    print("Filtering to Israel bounds...")
    israel_bounds = {
        'min_lat': 29.0,
        'max_lat': 33.8,
        'min_lon': 34.2,
        'max_lon': 35.9
    }

    # Get centroids for filtering (using bounds instead of centroid to avoid projection warning)
    bounds_gdf = gdf.bounds
    mask = (
        (bounds_gdf['miny'] >= israel_bounds['min_lat']) &
        (bounds_gdf['maxy'] <= israel_bounds['max_lat']) &
        (bounds_gdf['minx'] >= israel_bounds['min_lon']) &
        (bounds_gdf['maxx'] <= israel_bounds['max_lon'])
    )

    gdf_filtered = gdf[mask].copy()
    print(f"After filtering to Israel bounds: {len(gdf_filtered)} areas")

    return gdf_filtered

def save_processed_data(gdf):
    """Save the processed data in multiple formats."""

    # Save as GeoParquet (efficient for backend processing)
    parquet_path = PROCESSED_DATA_PATH / "statistical_areas_2022.parquet"
    print(f"Saving as GeoParquet: {parquet_path}")
    gdf.to_parquet(parquet_path)

    # Save full GeoJSON for development/debugging
    geojson_path = PROCESSED_DATA_PATH / "statistical_areas_2022.geojson"
    print(f"Saving as GeoJSON: {geojson_path}")
    gdf.to_file(geojson_path, driver='GeoJSON')

    # Create a lightweight version for web serving
    # Keep only essential columns and reduce precision
    essential_columns = []

    # Try to identify essential columns (adjust based on actual data)
    for col in gdf.columns:
        if col == 'geometry':
            continue
        elif any(keyword in col.lower() for keyword in ['name', 'שם', 'code', 'קוד', 'id', 'מזהה']):
            essential_columns.append(col)

    # If we can't identify specific columns, keep the first few non-geometry columns
    if not essential_columns:
        essential_columns = [col for col in gdf.columns if col != 'geometry'][:3]

    print(f"Essential columns for web version: {essential_columns}")

    # Create lightweight version
    web_gdf = gdf[essential_columns + ['geometry']].copy()

    # Further simplify for web
    web_gdf['geometry'] = web_gdf['geometry'].simplify(tolerance=0.0005, preserve_topology=True)

    # Save lightweight GeoJSON for web serving
    web_geojson_path = STATIC_DATA_PATH / "statistical_areas.geojson"
    print(f"Saving lightweight web version: {web_geojson_path}")
    web_gdf.to_file(web_geojson_path, driver='GeoJSON')

    # Create an even smaller version with just boundaries (no fill)
    boundaries_gdf = web_gdf.copy()
    boundaries_gdf['geometry'] = boundaries_gdf['geometry'].boundary

    boundaries_path = STATIC_DATA_PATH / "statistical_areas_boundaries.geojson"
    print(f"Saving boundaries version: {boundaries_path}")
    boundaries_gdf.to_file(boundaries_path, driver='GeoJSON')

    return {
        'full_parquet': parquet_path,
        'full_geojson': geojson_path,
        'web_geojson': web_geojson_path,
        'boundaries_geojson': boundaries_path,
        'total_areas': len(gdf),
        'web_areas': len(web_gdf)
    }

def create_metadata(gdf, output_paths):
    """Create metadata file with information about the statistical areas."""

    metadata = {
        'title': 'Statistical Areas 2022 - Israel',
        'description': 'Statistical areas boundaries for Israel, processed for web mapping',
        'source': 'statistical_areas_2022 shapefile',
        'crs': str(gdf.crs),
        'total_areas': len(gdf),
        'bounds': {
            'min_longitude': float(gdf.total_bounds[0]),
            'min_latitude': float(gdf.total_bounds[1]),
            'max_longitude': float(gdf.total_bounds[2]),
            'max_latitude': float(gdf.total_bounds[3])
        },
        'columns': list(gdf.columns),
        'files': {
            'full_data': str(output_paths['full_parquet'].name),
            'web_geojson': str(output_paths['web_geojson'].name),
            'boundaries_geojson': str(output_paths['boundaries_geojson'].name)
        },
        'processing_info': {
            'simplified': True,
            'tolerance': 0.0001,
            'web_tolerance': 0.0005,
            'filtered_to_israel': True
        }
    }

    metadata_path = PROCESSED_DATA_PATH / "statistical_areas_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Saved metadata: {metadata_path}")
    return metadata

def main():
    """Main processing function."""
    print("=" * 60)
    print("Processing Statistical Areas 2022")
    print("=" * 60)

    try:
        # Load data
        gdf = load_statistical_areas()

        # Process data
        gdf_processed = process_statistical_areas(gdf)

        # Save in multiple formats
        output_paths = save_processed_data(gdf_processed)

        # Create metadata
        metadata = create_metadata(gdf_processed, output_paths)

        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Total statistical areas processed: {output_paths['total_areas']}")
        print(f"Files created:")
        for key, path in output_paths.items():
            if isinstance(path, Path):
                print(f"  - {key}: {path}")

        print(f"\nData bounds:")
        bounds = metadata['bounds']
        print(f"  Latitude: {bounds['min_latitude']:.4f} to {bounds['max_latitude']:.4f}")
        print(f"  Longitude: {bounds['min_longitude']:.4f} to {bounds['max_longitude']:.4f}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)