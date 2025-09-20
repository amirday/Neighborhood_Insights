#!/usr/bin/env python3
"""
Common path utilities for ETL processing.
"""

from pathlib import Path


def get_project_paths():
    """
    Get standardized project paths for ETL processing.

    Returns:
        Dict with common project paths
    """
    project_root = Path(__file__).resolve().parent.parent.parent

    paths = {
        'project_root': project_root,
        'data_dir': project_root / "data",
        'raw_dir': project_root / "data" / "raw",
        'processed_dir': project_root / "data" / "processed",
        'static_dir': project_root / "app" / "public" / "data",
        'etl_dir': project_root / "etl",
        'backend_dir': project_root / "backend",
        'app_dir': project_root / "app"
    }

    return paths


def ensure_data_directories():
    """Ensure all data directories exist."""
    paths = get_project_paths()

    for dir_key in ['raw_dir', 'processed_dir', 'static_dir']:
        paths[dir_key].mkdir(parents=True, exist_ok=True)

    return paths