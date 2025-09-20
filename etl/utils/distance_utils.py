#!/usr/bin/env python3
"""
Distance calculation utilities for ETL processing.
"""

import numpy as np
from geopy.distance import geodesic
from sklearn.neighbors import BallTree


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate haversine distance between two points in kilometers."""
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers


def find_nearest_pois_with_balltree(neighborhoods_df, poi_df, poi_type):
    """
    Calculate distance to nearest POI of a specific type for each neighborhood using BallTree.

    Args:
        neighborhoods_df: DataFrame with neighborhood coordinates
        poi_df: DataFrame with POI coordinates
        poi_type: String identifier for POI type

    Returns:
        tuple: (distances, nearest_poi_names) lists
    """
    if len(poi_df) == 0:
        return [], []

    # Create BallTree for efficient nearest neighbor search
    # Convert lat/lon to radians for haversine distance
    poi_coords = np.radians(poi_df[['latitude', 'longitude']].values)
    tree = BallTree(poi_coords, metric='haversine')

    distances = []
    nearest_poi_names = []

    for _, neighborhood in neighborhoods_df.iterrows():
        # Query the tree for nearest POI
        hood_coord = np.radians([[neighborhood['latitude'], neighborhood['longitude']]])
        dist, ind = tree.query(hood_coord, k=1)

        # Convert distance from radians to kilometers
        distance_km = dist[0][0] * 6371  # Earth radius in km
        distances.append(round(distance_km, 2))

        # Get the name of the nearest POI
        nearest_poi_names.append(poi_df.iloc[ind[0][0]]['name_he'])

    return distances, nearest_poi_names


def calculate_composite_scores(df, score_config=None):
    """
    Calculate composite neighborhood scores based on service proximity.

    Args:
        df: DataFrame with distance columns
        score_config: Dict mapping distance column names to max distances for scoring

    Returns:
        DataFrame with added 'composite_score' column
    """
    if score_config is None:
        # Define default max distances for scoring (closer = better score)
        score_config = {
            'schools_distance_km': 2.0,
            'kindergartens_distance_km': 1.0,
            'clinics_distance_km': 3.0,
            'bus_stops_distance_km': 0.5
        }

    scores = []
    for _, row in df.iterrows():
        score_components = []

        for distance_col, max_dist in score_config.items():
            if distance_col in df.columns:
                distance = row[distance_col]
                # Score: 100 for distance 0, linearly decreases to 0 at max_distance
                score = max(0, 100 * (1 - distance / max_dist))
                score_components.append(score)

        # Average score across all available services
        composite_score = np.mean(score_components) if score_components else 0
        scores.append(round(composite_score, 1))

    df['composite_score'] = scores
    return df