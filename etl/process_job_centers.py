#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Process job centers (מוקדי תעסוקה) data and convert to optimized formats for web serving.

This script:
1. Loads the job centers CSV file with coordinates
2. Cleans and validates the data
3. Filters out records without valid coordinates
4. Saves as both CSV and Parquet formats
5. Creates metadata file

Usage:
    python process_job_centers.py
"""

import sys
from pathlib import Path
import pandas as pd
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import utilities
from etl.utils.paths import get_project_paths, ensure_data_directories
from etl.utils.file_utils import atomic_write_csv, export_json


def load_job_centers():
    """Load the job centers CSV file."""
    paths = get_project_paths()
    csv_path = paths['raw_dir'] / "mokdei_taasuka_with_coords.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Job centers CSV not found: {csv_path}")

    print(f"Loading job centers CSV: {csv_path}")

    # Read with UTF-8 encoding to handle Hebrew text and BOM
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    print(f"Loaded {len(df)} job center records")
    print(f"Columns: {list(df.columns)}")

    return df


def clean_and_validate_data(df):
    """Clean and validate the job centers data."""
    print("Cleaning and validating data...")

    # Create standardized column names
    df_clean = df.copy()

    # Rename columns to match our convention
    column_mapping = {
        'שם': 'name_he',
        'כתובת': 'address',
        'מספר מועסקים (הערכה)': 'estimated_employees',
        'latitude': 'latitude',
        'longitude': 'longitude'
    }

    # Apply column mapping if columns exist
    for old_col, new_col in column_mapping.items():
        if old_col in df_clean.columns:
            df_clean = df_clean.rename(columns={old_col: new_col})

    # Add additional fields
    df_clean['type'] = 'job_center'
    df_clean['name_en'] = 'Job Center'  # Default English name

    # Add ID column
    df_clean['id'] = range(1, len(df_clean) + 1)

    # Convert coordinates to numeric, handling any string values
    df_clean['latitude'] = pd.to_numeric(df_clean['latitude'], errors='coerce')
    df_clean['longitude'] = pd.to_numeric(df_clean['longitude'], errors='coerce')
    df_clean['estimated_employees'] = pd.to_numeric(df_clean['estimated_employees'], errors='coerce')

    # Filter out records without valid coordinates
    initial_count = len(df_clean)
    df_clean = df_clean.dropna(subset=['latitude', 'longitude'])
    filtered_count = len(df_clean)

    print(f"Filtered out {initial_count - filtered_count} records without valid coordinates")
    print(f"Remaining records: {filtered_count}")

    # Filter to Israel bounds (approximate)
    israel_bounds = {
        'min_lat': 29.0,
        'max_lat': 33.8,
        'min_lon': 34.2,
        'max_lon': 35.9
    }

    before_bounds = len(df_clean)
    df_clean = df_clean[
        (df_clean['latitude'] >= israel_bounds['min_lat']) &
        (df_clean['latitude'] <= israel_bounds['max_lat']) &
        (df_clean['longitude'] >= israel_bounds['min_lon']) &
        (df_clean['longitude'] <= israel_bounds['max_lon'])
    ]
    after_bounds = len(df_clean)

    print(f"Filtered out {before_bounds - after_bounds} records outside Israel bounds")
    print(f"Final records: {after_bounds}")

    # Show sample data
    print(f"Sample of cleaned data:")
    print(df_clean.head()[['name_he', 'address', 'estimated_employees', 'latitude', 'longitude']])

    return df_clean


def save_processed_data(df):
    """Save the processed data in multiple formats."""
    paths = ensure_data_directories()

    # Save as CSV (for human readability and backup)
    csv_path = paths['processed_dir'] / "job_centers.csv"
    print(f"Saving as CSV: {csv_path}")
    atomic_write_csv(df, str(csv_path))

    # Save as Parquet (efficient for backend processing)
    parquet_path = paths['processed_dir'] / "job_centers.parquet"
    print(f"Saving as Parquet: {parquet_path}")
    df.to_parquet(parquet_path, index=False)

    return {
        'csv_path': csv_path,
        'parquet_path': parquet_path,
        'total_records': len(df)
    }


def create_metadata(df, output_paths):
    """Create metadata file with information about the job centers."""
    paths = get_project_paths()

    metadata = {
        'title': 'Job Centers - Israel',
        'description': 'Major employment centers in Israel with estimated employee counts',
        'source': 'mokdei_taasuka_with_coords.csv',
        'total_centers': len(df),
        'bounds': {
            'min_longitude': float(df['longitude'].min()),
            'min_latitude': float(df['latitude'].min()),
            'max_longitude': float(df['longitude'].max()),
            'max_latitude': float(df['latitude'].max())
        },
        'columns': list(df.columns),
        'employee_statistics': {
            'total_estimated_employees': int(df['estimated_employees'].sum()) if 'estimated_employees' in df.columns else 0,
            'avg_employees_per_center': float(df['estimated_employees'].mean()) if 'estimated_employees' in df.columns else 0,
            'max_employees': int(df['estimated_employees'].max()) if 'estimated_employees' in df.columns else 0,
            'min_employees': int(df['estimated_employees'].min()) if 'estimated_employees' in df.columns else 0
        },
        'files': {
            'processed_csv': str(output_paths['csv_path'].name),
            'processed_parquet': str(output_paths['parquet_path'].name)
        }
    }

    metadata_path = paths['processed_dir'] / "job_centers_metadata.json"
    export_json(metadata, metadata_path, "job centers metadata")

    return metadata


def main():
    """Main processing function."""
    print("=" * 60)
    print("Processing Job Centers (מוקדי תעסוקה)")
    print("=" * 60)

    try:
        # Load data
        df = load_job_centers()

        # Clean and validate data
        df_clean = clean_and_validate_data(df)

        # Save processed data
        output_paths = save_processed_data(df_clean)

        # Create metadata
        metadata = create_metadata(df_clean, output_paths)

        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Total job centers processed: {output_paths['total_records']}")
        print(f"Files created:")
        print(f"  - CSV: {output_paths['csv_path']}")
        print(f"  - Parquet: {output_paths['parquet_path']}")

        print(f"\nEmployee statistics:")
        stats = metadata['employee_statistics']
        print(f"  Total estimated employees: {stats['total_estimated_employees']:,}")
        print(f"  Average per center: {stats['avg_employees_per_center']:,.0f}")
        print(f"  Largest center: {stats['max_employees']:,} employees")
        print(f"  Smallest center: {stats['min_employees']:,} employees")

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