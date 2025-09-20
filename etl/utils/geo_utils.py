#!/usr/bin/env python3
"""
Geographic data processing utilities for ETL.
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path


def get_settlement_type(status_code):
    """
    Determine settlement type based on Israeli status code.

    Args:
        status_code: Numeric status code

    Returns:
        Hebrew settlement type string
    """
    if pd.isna(status_code):
        return 'לא ידוע'

    status_code = int(status_code)

    # Common Israeli settlement type codes
    if status_code >= 10000 and status_code < 20000:
        return 'עיר'
    elif status_code >= 20000 and status_code < 30000:
        return 'מועצה מקומית'
    elif status_code >= 30000 and status_code < 40000:
        return 'מועצה אזורית'
    elif status_code >= 40000 and status_code < 50000:
        return 'קיבוץ'
    elif status_code >= 50000 and status_code < 60000:
        return 'מושב'
    elif status_code >= 70000 and status_code < 80000:
        return 'יישוב קהילתי'
    else:
        return 'אחר'


def get_region_by_coordinates(lat, lon):
    """
    Determine Israeli geographic region based on coordinates.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Hebrew region name
    """
    if lat > 32.5:
        return 'צפון'
    elif lat > 31.5:
        return 'מרכז'
    elif lat > 30.5:
        return 'שפלה ויהודה'
    else:
        return 'דרום'


def convert_crs_to_wgs84(gdf):
    """
    Convert GeoDataFrame to WGS84 (EPSG:4326) if not already.

    Args:
        gdf: GeoDataFrame to convert

    Returns:
        GeoDataFrame in WGS84 CRS
    """
    if gdf.crs != 'EPSG:4326':
        print("Converting to WGS84 (EPSG:4326)...")
        gdf = gdf.to_crs('EPSG:4326')
    return gdf


def simplify_geometries(gdf, tolerance=0.0001, preserve_topology=True):
    """
    Simplify geometries for better web performance.

    Args:
        gdf: GeoDataFrame with geometries to simplify
        tolerance: Simplification tolerance
        preserve_topology: Whether to preserve topology

    Returns:
        GeoDataFrame with simplified geometries
    """
    print(f"Simplifying geometries with tolerance {tolerance}...")
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=tolerance, preserve_topology=preserve_topology)
    return gdf


def filter_to_israel_bounds(gdf):
    """
    Filter GeoDataFrame to areas within Israel's approximate bounds.

    Args:
        gdf: GeoDataFrame to filter

    Returns:
        Filtered GeoDataFrame
    """
    print("Filtering to Israel bounds...")
    israel_bounds = {
        'min_lat': 29.0,
        'max_lat': 33.8,
        'min_lon': 34.2,
        'max_lon': 35.9
    }

    # Get bounds for filtering (using bounds instead of centroid to avoid projection warning)
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


def add_hebrew_field_mappings(gdf):
    """
    Add Hebrew field mappings and enhanced data to statistical areas GeoDataFrame.

    Args:
        gdf: GeoDataFrame with statistical areas

    Returns:
        GeoDataFrame with added Hebrew fields
    """
    print("Adding Hebrew field mappings and enhanced data...")

    # Create Hebrew field mappings as additional columns
    gdf['שם_יישוב'] = gdf['SHEM_YISHU']
    gdf['שם_יישוב_אנגלית'] = gdf['SHEM_YIS_1']
    gdf['סמל_יישוב'] = gdf['SEMEL_YISH']
    gdf['סטטיסטיקה_2022'] = gdf['STAT_2022']
    gdf['סטטוס_יישוב'] = gdf['YISHUV_STA']
    gdf['רובע'] = gdf['ROVA']
    gdf['תת_רובע'] = gdf['TAT_ROVA']
    gdf['קוד_תפקוד_עיקרי'] = gdf['COD_TIFKUD']

    # Add calculated fields
    gdf['שטח_קמ_ר'] = (gdf['SHAPE_Area'] / 1000000).round(3)  # Convert to km²
    gdf['היקף_קמ'] = (gdf['SHAPE_Leng'] / 1000).round(3)  # Convert to km

    # Add settlement type based on status code
    gdf['סוג_יישוב'] = gdf['YISHUV_STA'].apply(get_settlement_type)

    # Add region based on geographic location
    centroids = gdf.geometry.centroid
    gdf['אזור_גיאוגרפי'] = [get_region_by_coordinates(centroid.y, centroid.x) for centroid in centroids]

    return gdf


def filter_areas_with_function_code(gdf):
    """
    Filter out areas without primary function code (קוד תפקוד עיקרי).

    Args:
        gdf: GeoDataFrame to filter

    Returns:
        Filtered GeoDataFrame
    """
    print("Filtering areas with primary function code...")
    function_code_mask = (
        pd.notna(gdf['COD_TIFKUD']) &
        (gdf['COD_TIFKUD'] != 0) &
        (gdf['COD_TIFKUD'] != '')
    )

    gdf_with_function = gdf[function_code_mask].copy()

    filtered_out_count = len(gdf) - len(gdf_with_function)
    print(f"Filtered out {filtered_out_count} areas without primary function code")
    print(f"Final count: {len(gdf_with_function)} areas with primary function code")

    return gdf_with_function