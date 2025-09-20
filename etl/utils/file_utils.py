#!/usr/bin/env python3
"""
File I/O utilities for ETL processing.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd


def atomic_write_csv(df: pd.DataFrame, path: str):
    """
    Write CSV file atomically to avoid corruption during writes.

    Args:
        df: DataFrame to write
        path: Output file path
    """
    tmp = f"{path}.tmp"
    # UTF-8 with BOM helps Excel users see Hebrew correctly
    df.to_csv(tmp, index=False, encoding="utf-8-sig")
    os.replace(tmp, path)


def ensure_directory_exists(path: Path):
    """Ensure directory exists, creating if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def load_poi_data_from_csv(raw_dir: Path, poi_files: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    """
    Load POI datasets from CSV files.

    Args:
        raw_dir: Path to raw data directory
        poi_files: Dict mapping POI types to filenames

    Returns:
        Dict mapping POI types to DataFrames
    """
    pois = {}
    for poi_type, filename in poi_files.items():
        filepath = raw_dir / filename
        if filepath.exists():
            df = pd.read_csv(filepath)
            # Ensure we have lat/lon columns
            if 'latitude' in df.columns and 'longitude' in df.columns:
                pois[poi_type] = df[['id', 'name_he', 'latitude', 'longitude']].copy()
                pois[poi_type]['type'] = poi_type
                print(f"Loaded {len(pois[poi_type])} {poi_type}")
            else:
                print(f"Warning: {filename} missing latitude/longitude columns")
        else:
            print(f"Warning: {filename} not found")

    return pois


def export_geojson(data: Any, output_path: Path, description: str = "data"):
    """
    Export data as GeoJSON file.

    Args:
        data: GeoJSON-compatible data structure
        output_path: Path to write file
        description: Description for logging
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Exported {description} to {output_path}")


def export_json(data: Any, output_path: Path, description: str = "data"):
    """
    Export data as JSON file.

    Args:
        data: JSON-serializable data
        output_path: Path to write file
        description: Description for logging
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Exported {description} to {output_path}")