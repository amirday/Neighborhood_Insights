# Neighborhood Insights IL 🏠

A mobile-first webapp empowering people in Israel to explore, compare, and filter neighborhoods based on quality of life factors including education, crime, services, prices, and commute times.

## 🎯 Vision

Enable data-driven neighborhood decisions through comprehensive location intelligence, offering both address-level insights and reverse search capabilities to find areas matching specific criteria.

## ✨ Core Features

### 1. Discover (Reverse Search)
- Set filters: demographics, services proximity, crime, education, prices, commute time
- Interactive map heatmap with ranked neighborhood results
- Match scoring algorithm (0-100)
- Shareable deep links for results

### 2. Address Profile
- Enter any address → comprehensive Neighborhood Score (0–100)
- Component breakdown: demographics, education, crime, services, transit, housing
- Interactive map: region boundaries, nearby POIs, isochrone overlays
- Optional Google Places integration for ratings/photos

### 3. Commute Filter
- Set work address with multiple transport modes (car, transit, bike, walking)
- Traffic-aware routing with configurable departure times
- Map highlights for reachable neighborhoods within time thresholds
- Save commute presets for combined filtering

### 4. Compare Neighborhoods
- Side-by-side comparison of 2-3 regions
- Radar chart visualization of component scores
- Detailed comparison tables

## 🏗️ Architecture

### Backend
- **Database**: PostgreSQL with PostGIS extensions
- **API**: FastAPI with async support
- **ETL Pipeline**: Python (GeoPandas, Shapely) with nightly data refresh
- **Routing**: Multi-stage funnel (crow-flight → OSRM → Google Routes)

### Frontend
- **Framework**: Next.js with React
- **Maps**: Mapbox GL with vector tiles
- **UI**: Mobile-first PWA with RTL support
- **Features**: Bottom sheets, filter drawers, offline capability

### Data Sources
- **CBS**: Statistical areas and demographic data
- **Ministry of Education**: School locations and performance (Mitzav scores)
- **Israel Police**: Crime statistics by locality
- **Ministry of Health**: Healthcare facility registry
- **OpenStreetMap**: POI data (supermarkets, parks, services)
- **GTFS Israel**: Public transit stops and routes
- **Tax Authority**: Real estate transaction data

### Infrastructure
- **Frontend**: Vercel hosting
- **Backend**: Fly.io or Render
- **Database**: Supabase with PostGIS
- **Monitoring**: Sentry + PostHog analytics
- **Maps**: Mapbox GL vector tiles

## 🔧 Tech Stack

### Core Technologies
```
Backend:    FastAPI, PostgreSQL, PostGIS, Redis
ETL:        Python, GeoPandas, Shapely, GDAL
Routing:    OSRM, OpenTripPlanner, Google Routes API
Frontend:   Next.js, React, TypeScript, Mapbox GL
Styling:    Tailwind CSS with RTL support
Testing:    pytest, Jest, Playwright
```

### External APIs
```
Routing:    Google Routes API (traffic-aware)
Maps:       Mapbox (vector tiles, GL JS)
Places:     Google Places API (optional enrichment)
Analytics:  PostHog (behavioral analytics)
Monitoring: Sentry (error tracking)
```

## 📊 Data Model

### Core Entities
- **Regions**: CBS statistical areas with administrative boundaries
- **Neighborhoods**: Canonical neighborhood definitions
- **Demographics**: Population, household, socioeconomic indices
- **Education**: Schools with performance metrics
- **Crime**: Incident data normalized per capita
- **Health**: Medical facility locations and types
- **POI**: Points of interest from OSM and official sources
- **Transit**: Public transport stops and routes
- **Real Estate**: Transaction history with pricing trends

### Scoring Algorithm
Multi-component scoring system with configurable weights:
- Education quality (schools proximity + performance)
- Safety index (crime rates)
- Services access (supermarkets, clinics, parks)
- Transit connectivity (stop density + route coverage)
- Housing affordability (price trends + availability)

## 🚀 Success Criteria (MVP)

### Performance Targets
- Address profile generation: < 2 seconds
- Reverse search with filters: < 1.5s (metro) / < 3s (nationwide)
- Commute calculations: Accurate for all transport modes
- Mobile-first experience with PWA capabilities

### Cost Targets
- Infrastructure: < $200/month
- Google APIs: < $50/month
- Sustainable usage-based scaling

## 🔒 Privacy & Compliance

- No personal data storage
- Anonymous usage analytics only
- GDPR-compliant data handling
- Israeli data residency requirements

## 📱 Supported Platforms

- **Primary**: Mobile web browsers (iOS Safari, Android Chrome)
- **Secondary**: Desktop browsers
- **PWA**: Installable with offline capabilities
- **Languages**: Hebrew (primary), Arabic, English

## 🏁 Getting Started

See `eng_plan.md` for detailed development timeline and setup instructions.

## 📄 License

[License TBD]

## 🤝 Contributing

[Contributing guidelines TBD]