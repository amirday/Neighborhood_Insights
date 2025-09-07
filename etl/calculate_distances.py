#!/usr/bin/env python3
"""
Calculate distances from neighborhood centroids to nearest POIs using haversine.
Uses scikit-learn's BallTree for efficient nearest neighbor search.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.neighbors import BallTree
from geopy.distance import geodesic
import json

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PUBLIC_DIR = Path(__file__).parent.parent / "app" / "public" / "data"

# Create directories if they don't exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate haversine distance between two points in kilometers."""
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers

def load_pois():
    """Load all POI datasets."""
    poi_files = {
        'schools': 'govmap_schools.csv',
        'kindergartens': 'govmap_kindergartens.csv', 
        'clinics': 'govmap_clinics.csv',
        'bus_stops': 'govmap_bus_stops.csv'
    }
    
    pois = {}
    for poi_type, filename in poi_files.items():
        filepath = RAW_DIR / filename
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

def create_neighborhoods():
    """Create sample neighborhood data from CBS statistical areas."""
    # For MVP, create a simplified neighborhood dataset
    # In production, this would come from CBS statistical areas
    neighborhoods = []
    
    # Sample neighborhoods across Israel (major cities)
    sample_data = [
        {"id": 1, "name_he": "רמת אביב", "name_en": "Ramat Aviv", "city": "תל אביב", "latitude": 32.113, "longitude": 34.800},
        {"id": 2, "name_he": "גבעתיים", "name_en": "Givatayim", "city": "גבעתיים", "latitude": 32.073, "longitude": 34.811},
        {"id": 3, "name_he": "רחביה", "name_en": "Rehavia", "city": "ירושלים", "latitude": 31.771, "longitude": 35.214},
        {"id": 4, "name_he": "כרמל", "name_en": "Carmel", "city": "חיפה", "latitude": 32.794, "longitude": 34.989},
        {"id": 5, "name_he": "נווה שאנן", "name_en": "Neve Sha'anan", "city": "תל אביב", "latitude": 32.058, "longitude": 34.764},
        {"id": 6, "name_he": "בקעה", "name_en": "Baka", "city": "ירושלים", "latitude": 31.756, "longitude": 35.206},
        {"id": 7, "name_he": "הדר", "name_en": "Hadar", "city": "חיפה", "latitude": 32.810, "longitude": 34.994},
        {"id": 8, "name_he": "פלורנטין", "name_en": "Florentin", "city": "תל אביב", "latitude": 32.051, "longitude": 34.768},
        {"id": 9, "name_he": "טלביה", "name_en": "Talbieh", "city": "ירושלים", "latitude": 31.770, "longitude": 35.225},
        {"id": 10, "name_he": "עיר ימים", "name_en": "Ir Yamim", "city": "נתניה", "latitude": 32.327, "longitude": 34.857},
    ]
    
    df = pd.DataFrame(sample_data)
    return df

def find_nearest_pois(neighborhoods_df, pois):
    """Calculate distance to nearest POI of each type for each neighborhood."""
    results = neighborhoods_df.copy()
    
    for poi_type, poi_df in pois.items():
        if len(poi_df) == 0:
            continue
            
        print(f"Calculating distances to {poi_type}...")
        
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
        
        results[f'{poi_type}_distance_km'] = distances
        results[f'nearest_{poi_type}'] = nearest_poi_names
        
    return results

def calculate_scores(df):
    """Calculate composite neighborhood scores based on service proximity."""
    # Define max distances for scoring (closer = better score)
    max_distances = {
        'schools_distance_km': 2.0,
        'kindergartens_distance_km': 1.0,
        'clinics_distance_km': 3.0,
        'bus_stops_distance_km': 0.5
    }
    
    scores = []
    for _, row in df.iterrows():
        score_components = []
        
        for distance_col, max_dist in max_distances.items():
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

def export_for_frontend(df, pois):
    """Export data in formats suitable for the React frontend."""
    # 1. Neighborhoods with scores as JSON
    neighborhoods_json = df.to_dict('records')
    with open(PUBLIC_DIR / 'neighborhoods.json', 'w', encoding='utf-8') as f:
        json.dump(neighborhoods_json, f, ensure_ascii=False, indent=2)
    
    # 2. POIs as GeoJSON for map display
    all_pois = []
    for poi_type, poi_df in pois.items():
        for _, poi in poi_df.iterrows():
            all_pois.append({
                "type": "Feature",
                "properties": {
                    "id": poi['id'],
                    "name_he": poi['name_he'],
                    "type": poi_type
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [poi['longitude'], poi['latitude']]
                }
            })
    
    pois_geojson = {
        "type": "FeatureCollection",
        "features": all_pois
    }
    
    with open(PUBLIC_DIR / 'pois.geojson', 'w', encoding='utf-8') as f:
        json.dump(pois_geojson, f, ensure_ascii=False, indent=2)
    
    # 3. Neighborhoods as GeoJSON (simple points for now)
    neighborhoods_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature", 
                "properties": {
                    "id": row['id'],
                    "name_he": row['name_he'],
                    "name_en": row['name_en'],
                    "city": row['city'],
                    "composite_score": row['composite_score']
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [row['longitude'], row['latitude']]
                }
            }
            for _, row in df.iterrows()
        ]
    }
    
    with open(PUBLIC_DIR / 'neighborhoods.geojson', 'w', encoding='utf-8') as f:
        json.dump(neighborhoods_geojson, f, ensure_ascii=False, indent=2)
    
    print(f"Exported data to {PUBLIC_DIR}/")
    print(f"  - {len(neighborhoods_json)} neighborhoods")
    print(f"  - {len(all_pois)} POIs")

def main():
    """Main execution function."""
    print("🏘️  Neighborhood Insights - Distance Calculator")
    print("=" * 50)
    
    # Load POI data
    print("Loading POI data...")
    pois = load_pois()
    
    if not pois:
        print("No POI data found. Please ensure CSV files exist in data/raw/")
        return
    
    # Create neighborhood data
    print("Creating neighborhood dataset...")
    neighborhoods_df = create_neighborhoods()
    
    # Calculate distances
    print("Calculating distances to nearest services...")
    neighborhoods_with_distances = find_nearest_pois(neighborhoods_df, pois)
    
    # Calculate composite scores
    print("Calculating neighborhood scores...")
    final_df = calculate_scores(neighborhoods_with_distances)
    
    # Save processed data
    final_df.to_csv(PROCESSED_DIR / 'neighborhoods_with_distances.csv', index=False)
    print(f"Saved processed data to {PROCESSED_DIR}/neighborhoods_with_distances.csv")
    
    # Export for frontend
    print("Exporting data for frontend...")
    export_for_frontend(final_df, pois)
    
    print("\n✅ Distance calculation completed!")
    print(f"Sample results:")
    print(final_df[['name_he', 'composite_score', 'schools_distance_km', 'clinics_distance_km']].head())

if __name__ == "__main__":
    main()