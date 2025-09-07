# Neighborhood Insights IL - MVP

A lightweight web app for exploring Israeli neighborhoods by proximity to key services like schools, clinics, police, bus stops, train stations, and supermarkets.

## Architecture

**Phase 1 - Lightweight MVP:**
- CSV files as data source (no database)
- React + MapLibre frontend
- Distance calculations using haversine with scikit-learn BallTree
- Mobile-first responsive design
- Client-side filtering

## Quick Start

1. **Install dependencies:**
   ```bash
   cd app && npm install
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # No external APIs needed for MVP
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Calculate distances (optional):**
   ```bash
   python etl/calculate_distances.py
   ```

## Data Structure

- `data/raw/` - CSV files with POI data from GovMap
- `data/processed/` - Pre-calculated distance matrices
- `app/public/data/` - JSON data for frontend

## Tech Stack

- **Frontend:** Next.js, React, MapLibre GL JS, TailwindCSS
- **Data Processing:** Python, Pandas, scikit-learn
- **Maps:** MapLibre (vector tiles)

## Development

The app loads neighborhood and POI data from CSV files, calculates distances on the client side, and allows users to filter areas by proximity to services. Everything runs locally without external dependencies.