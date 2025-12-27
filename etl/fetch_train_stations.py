#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch all train stations in Israel from OpenStreetMap via Overpass API.
- Output: CSV with station name, coordinates (WGS84), and metadata
- Uses Overpass API to query railway=station/halt nodes in Israel

Usage:
  python fetch_train_stations.py --out data/processed/train_stations.csv

Notes:
- Free, no API key required
- Returns WGS84 coordinates (EPSG:4326) - compatible with your existing system
- Includes both active stations and railway halts
"""

from __future__ import annotations
import argparse
import time
from typing import Dict, List, Optional
import pandas as pd
import requests
from tqdm import tqdm


class OverpassClient:
    """Client for querying OpenStreetMap data via Overpass API."""

    def __init__(self, endpoint: str = "https://overpass-api.de/api/interpreter"):
        self.endpoint = endpoint
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "neighborhood-insights-il/etl (+https://github.com/yourusername/neighborhood-insights)"
        })

    def query_train_stations(self, retries: int = 3) -> List[Dict]:
        """
        Query all train stations in Israel.

        Returns list of dicts with keys:
        - id: OSM node ID
        - name: Station name (Hebrew or English)
        - name_he: Hebrew name (if available)
        - name_en: English name (if available)
        - lat: Latitude (WGS84)
        - lon: Longitude (WGS84)
        - railway: Type (station, halt, etc.)
        - operator: Railway operator
        - network: Network name
        - ref: Reference code
        """
        # Overpass QL query to get all railway stations/halts in Israel
        query = """
[out:json][timeout:60];
area["ISO3166-1"="IL"]["admin_level"="2"]->.israel;
(
  node(area.israel)["railway"="station"];
  node(area.israel)["railway"="halt"];
);
out body;
>;
out skel qt;
"""

        last_err = None
        for attempt in range(retries):
            try:
                print(f"Querying Overpass API (attempt {attempt + 1}/{retries})...")
                resp = self.session.post(
                    self.endpoint,
                    data={"data": query},
                    timeout=120
                )

                if resp.status_code == 429:
                    # Rate limited
                    wait_time = min(60, 5 * (2 ** attempt))
                    print(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                if resp.status_code == 504:
                    # Gateway timeout
                    wait_time = min(30, 3 * (2 ** attempt))
                    print(f"Gateway timeout. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                resp.raise_for_status()
                data = resp.json()

                # Parse elements
                stations = []
                elements = data.get("elements", [])

                print(f"Found {len(elements)} railway elements")

                for elem in elements:
                    if elem.get("type") != "node":
                        continue

                    tags = elem.get("tags", {})
                    if "railway" not in tags:
                        continue

                    station = {
                        "id": elem.get("id"),
                        "name": tags.get("name"),
                        "name_he": tags.get("name:he"),
                        "name_en": tags.get("name:en"),
                        "lat": elem.get("lat"),
                        "lon": elem.get("lon"),
                        "railway": tags.get("railway"),
                        "operator": tags.get("operator"),
                        "network": tags.get("network"),
                        "ref": tags.get("ref"),
                        "wikidata": tags.get("wikidata"),
                        "wikipedia": tags.get("wikipedia"),
                    }
                    stations.append(station)

                print(f"Extracted {len(stations)} train stations/halts")
                return stations

            except requests.exceptions.RequestException as e:
                last_err = str(e)
                print(f"Request failed: {e}")
                if attempt < retries - 1:
                    wait_time = min(10, 2 * (2 ** attempt))
                    print(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            except Exception as e:
                last_err = str(e)
                print(f"Error parsing response: {e}")
                if attempt < retries - 1:
                    time.sleep(2)

        raise RuntimeError(f"Failed to fetch train stations after {retries} attempts: {last_err}")


def enrich_stations(stations: List[Dict]) -> pd.DataFrame:
    """
    Convert raw station data to DataFrame and enrich with computed fields.
    """
    df = pd.DataFrame(stations)

    # Use name_he if available, otherwise fall back to name
    df["display_name"] = df["name_he"].fillna(df["name"])

    # Add type column
    df["type"] = df["railway"].map({
        "station": "תחנת רכבת",
        "halt": "תחנת עצירה"
    }).fillna("תחנת רכבת")

    # Ensure coordinates are float
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    # Drop stations without coordinates
    before = len(df)
    df = df.dropna(subset=["lat", "lon"])
    after = len(df)
    if before > after:
        print(f"Warning: Dropped {before - after} stations without valid coordinates")

    # Validate coordinates are in Israel
    # Israel bounds: approximately 29.5-33.3°N, 34.2-35.9°E
    df = df[
        (df["lat"] >= 29.0) & (df["lat"] <= 33.8) &
        (df["lon"] >= 34.2) & (df["lon"] <= 35.9)
    ]

    # Sort by name
    df = df.sort_values("display_name", na_position="last")

    return df


def main():
    ap = argparse.ArgumentParser(
        description="Fetch all train stations in Israel from OpenStreetMap Overpass API"
    )
    ap.add_argument(
        "--out",
        default="/Users/amirdaygmail.com/projects/Neighborhood_Insights/data/processed/train_stations.csv",
        help="Output CSV file path"
    )
    ap.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retry attempts for API requests"
    )
    args = ap.parse_args()

    print("=" * 60)
    print("Fetching Train Stations from OpenStreetMap")
    print("=" * 60)

    # Query Overpass API
    client = OverpassClient()
    stations = client.query_train_stations(retries=args.retries)

    if not stations:
        print("No train stations found!")
        return

    # Convert to DataFrame and enrich
    print("\nProcessing station data...")
    df = enrich_stations(stations)

    # Reorder columns for better readability
    columns = [
        "id",
        "display_name",
        "name",
        "name_he",
        "name_en",
        "lat",
        "lon",
        "type",
        "railway",
        "operator",
        "network",
        "ref",
        "wikidata",
        "wikipedia",
    ]
    # Only include columns that exist
    columns = [c for c in columns if c in df.columns]
    df = df[columns]

    # Save to CSV with UTF-8 BOM for Excel Hebrew compatibility
    df.to_csv(args.out, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total stations found: {len(df)}")
    print(f"Stations with Hebrew names: {df['name_he'].notna().sum()}")
    print(f"Stations with English names: {df['name_en'].notna().sum()}")
    print(f"\nOutput saved to: {args.out}")
    print("\nSample stations:")
    print(df[["display_name", "lat", "lon", "type"]].head(10).to_string(index=False))

    # Print stations by type
    print("\nStations by type:")
    print(df["type"].value_counts().to_string())


if __name__ == "__main__":
    main()
