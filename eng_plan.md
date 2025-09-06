# Engineering Plan - Neighborhood Insights IL
## 45-Day Development Timeline

### Phase 1: Foundation (Days 1-10)

## ~~Day 1: Environment Setup & Accounts~~
~~**Objective**: Complete development environment and third-party accounts~~

~~**Tasks**:~~
- ~~[x] Install development tooling (Python, Node, Docker, PostGIS tools)~~
- ~~[ ] Create all external service accounts~~
- ~~[x] Configure API keys and quotas~~
- ~~[ ] Set up monitoring/alerting for cost *controls*~~

~~**Acceptance Criteria**:~~
- ~~All tools installed and version-locked~~
- ~~API keys stored securely in `.env`~~ 
- ~~[ ] Budget alerts configured (Google: $50/mo, Mapbox: 50k loads/mo)~~
- ~~Local development environment fully functional~~

**External Services Setup**:
```bash
# Required Accounts & API Access
- GitHub (repo hosting)
- Vercel (frontend hosting)  
- Fly.io/Render (backend hosting)
- Supabase (PostGIS database)
- Google Cloud (Routes API + Places API)
- Mapbox (vector tiles + GL JS)
- Sentry (error tracking)
- PostHog (analytics)
```

**Commands**:
```bash
# Install core tools
brew install docker postgresql@16 python@3.11 node@20 pnpm gdal
pipx install poetry

# Setup project
git clone <repo> && cd neighborhood-insights-il
cp .env.example .env  # Fill with real API keys
docker-compose up -d postgres
```

---

## ~~Day 2: Monorepo Structure & CI/CD~~
~~**Objective**: Complete monorepo skeleton with working CI/CD~~

~~**Tasks**:~~
- ~~[x] Finalize directory structure~~
- ~~[x] Create Docker Compose configuration~~
- ~~[ ] Set up GitHub Actions workflows~~
- ~~[x] Configure pre-commit hooks~~

~~**Acceptance Criteria**:~~
- ~~[x] `make up` starts all local services~~
- ~~[ ] GitHub Actions running lint/test/build on push~~
- ~~[x] Pre-commit hooks enforcing code quality~~

**Files Created**:
```
.github/workflows/
├── test.yml                 # Run test suite
├── deploy-api.yml           # Deploy backend
└── deploy-app.yml           # Deploy frontend

.pre-commit-config.yaml      # Code quality hooks
docker-compose.yml           # Local development
docker-compose.test.yml      # Testing environment  
Makefile                     # Common commands
```

---

## ~~Day 3: Database Schema & PostGIS Setup~~
~~**Objective**: Production-ready database schema with spatial indices~~

~~**Tasks**:~~
- ~~[x] Create comprehensive PostGIS schema~~
- ~~[x] Add spatial indices and constraints~~
- ~~[x] Create database migration system~~
- ~~[x] Set up connection pooling~~

~~**Acceptance Criteria**:~~
- ~~[x] PostGIS extension enabled~~
- ~~[x] All tables created with proper indices~~
- ~~[x] Migration system functional~~
- ~~[x] Connection pooling configured~~

**Schema Components**:
```sql
-- Core spatial entities
- regions (CBS statistical areas)
- neighborhoods_canonical (municipality-defined areas)
- centroids (representative points)

-- Data layers
- demographics, schools, crime, health_facilities
- poi_osm, stops, deals
- scores_components, scores_neighborhood

-- Performance optimizations  
- commute_cache_short (routing cache)
- Spatial indices on all geometry columns
- Composite indices for common queries
```

---

## ~~Day 4: Data Acquisition Pipeline~~
~~**Objective**: Automated data collection from all primary sources~~

~~**Tasks**:~~
- ~~[x] CBS Statistical Areas download/processing~~
- ~~[x] Ministry of Education data collection~~
- ~~[x] Israel Police crime data integration~~
- ~~[x] Ministry of Health facilities data~~
- ~~[x] OSM Israel extract processing~~
- ~~[x] GTFS Israel integration~~
- ~~[x] Tax Authority real estate data setup~~

~~**Acceptance Criteria**:~~
- ~~[x] All raw data sources identified and accessible~~
- ~~[x] Download scripts with checksums/validation~~
- ~~[x] Data provenance documentation~~
- ~~[x] Automated refresh capability~~

**Data Sources**:
```
CBS: Statistical Areas 2022 (boundaries + demographics)
MoE: School coordinates + Mitzav/RAMA scores  
Police: Crime by locality (data.gov.il)
MoH: Healthcare institutions registry
OSM: Israel+Palestine PBF (Geofabrik)
GTFS: Israel public transit (MoT/NPTA)
Tax Authority: Real estate transactions (Nadlan)
```

---

## ~~Day 5: CBS Statistical Areas ETL~~
~~**Objective**: Core geographic boundaries loaded and validated~~

~~**Tasks**:~~
- ~~[x] ETL pipeline for CBS statistical areas~~
- ~~[x] Geometry validation and cleanup~~  
- ~~[x] CRS transformation (ITM→WGS84)~~
- ~~[x] Centroid generation~~
- ~~[x] Quality assurance checks~~

~~**Acceptance Criteria**:~~
- ~~[x] ~4,500 statistical areas loaded~~
- ~~[x] Geometries validated (no invalid/empty)~~
- ~~[x] Centroids computed for all regions~~
- ~~[x] Spatial queries performing <100ms~~

**ETL Pipeline**:
```python
# etl/cbs_processor.py
1. Download CBS statistical areas (GeoJSON/SHP)
2. Validate geometries in ITM (EPSG:2039)  
3. Fix topology issues (buffer(0))
4. Transform to WGS84 (EPSG:4326)
5. Generate representative points
6. Load to PostGIS with validation
```

---

## ~~Day 6: Demographics & Education Data Processing~~  
~~**Objective**: Population and school data integrated with geography~~

~~**Tasks**:~~
- ~~[x] CBS demographic data processing~~
- ~~[x] School locations geocoding/validation~~
- ~~[x] Mitzav/RAMA test scores integration~~
- ~~[x] Spatial joins with statistical areas~~
- ~~[x] Data quality validation~~

~~**Acceptance Criteria**:~~
- ~~[x] Demographics loaded for all regions~~
- ~~[x] Schools geocoded with <5% failure rate~~
- ~~[x] Test scores linked to school records~~
- ~~[x] Education quality metrics computed~~

**Processing Steps**:
```python
# Demographics processing
- Population counts, household data
- Socioeconomic indices by statistical area
- Age distribution and density metrics

# Education processing  
- School coordinates validation
- Mitzav math/language scores
- School-to-region spatial assignment
- Proximity-weighted education scores
```

---

## ~~Day 7: Crime & Health Data Integration~~
~~**Objective**: Safety and healthcare accessibility data layers~~

~~**Tasks**:~~
- ~~[x] Police crime data normalization~~
- ~~[x] Crime rate calculations (per 1000 residents)~~
- ~~[x] Health facility location processing~~
- ~~[x] Healthcare accessibility metrics~~
- ~~[x] Data validation and outlier detection~~

~~**Acceptance Criteria**:~~
- ~~[x] Crime rates normalized across regions~~
- ~~[x] Health facilities geocoded and categorized~~
- ~~[x] Accessibility scores computed~~
- ~~[x] Outliers identified and flagged~~

---

## Day 8: Next.js Frontend Foundation
**Objective**: Basic UI with interactive map functionality

**Tasks**:
- [ ] Next.js 14 project initialization in `/app` directory
- [ ] PWA configuration (service worker, manifest)
- [ ] Basic routing structure setup
- [ ] Mapbox GL integration with simple map view
- [ ] Mobile-first responsive layout

**Acceptance Criteria**:
- Next.js app running on localhost:3000
- Basic map displays Israeli boundaries
- Mobile-responsive design foundation
- PWA manifest configured
- Clean, minimal UI structure

**Setup Commands**:
```bash
cd app/
npx create-next-app@14 . --typescript --tailwind --eslint --app --src-dir
npm install mapbox-gl @types/mapbox-gl
npm install @next/pwa workbox-webpack-plugin
```

---

## Day 9: Map Integration & Basic Interactivity  
**Objective**: Interactive map with neighborhood boundaries

**Tasks**:
- [ ] Load neighborhood boundaries as vector data
- [ ] Implement map click/hover interactions
- [ ] Add basic zoom and pan controls
- [ ] Create simple neighborhood info popup
- [ ] Mobile touch optimization

**Acceptance Criteria**:
- Map displays neighborhood boundaries clearly
- Click on neighborhood shows basic info
- Smooth pan/zoom on mobile devices
- Performance optimized for mobile browsers
- Basic neighborhood data visible on interaction

---

## Day 10: Database Enhancement & API Connection
**Objective**: Enhanced database with basic API endpoints

**Tasks**:
- [ ] Add missing data tables (scores, enhanced demographics)
- [ ] Create basic FastAPI endpoints for map data
- [ ] Implement neighborhood data retrieval
- [ ] Add basic search functionality
- [ ] Connect frontend to API endpoints

**Acceptance Criteria**:
- Database has all essential tables populated
- API serves neighborhood boundary data
- Frontend successfully fetches data from API
- Basic search returns neighborhood results
- Error handling for API failures

**Scoring Formula**:
```python
# Component weights (configurable)
weights = {
    'education': 0.25,    # School quality + proximity
    'crime': 0.20,        # Safety index (inverted)
    'services': 0.20,     # Supermarket/clinic/park proximity
    'transit': 0.15,      # Public transport connectivity
    'housing': 0.20       # Affordability + availability
}

composite_score = Σ(z_score_i * weight_i) * 10 + 50  # Scale to 0-100
```

---

### Phase 2: Data Processing & Advanced Features (Days 11-20)

## Day 11: OSM POI Processing & GTFS Integration
**Objective**: Services accessibility and transit connectivity data

**Tasks**:
- [ ] OSM POI extraction and categorization
- [ ] Transit stop processing from GTFS
- [ ] Service proximity calculations
- [ ] Transit accessibility scoring
- [ ] Data deduplication and validation

**Acceptance Criteria**:
- Key POI categories extracted (supermarkets, clinics, parks)
- Transit stops loaded with route information
- Proximity metrics computed (300m/500m/800m/1000m buffers)
- Service accessibility scores calculated

**Setup Commands**:
```bash
# Download and process OSM data
cd ops/osrm
wget https://download.geofabrik.de/asia/israel-and-palestine-latest.osm.pbf

# Build routing data for each profile
docker run -t -v $(pwd):/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/israel-and-palestine-latest.osm.pbf
docker run -t -v $(pwd):/data osrm/osrm-backend osrm-partition /data/israel-and-palestine-latest.osrm
docker run -t -v $(pwd):/data osrm/osrm-backend osrm-customize /data/israel-and-palestine-latest.osrm

# Start routing server
docker run -t -i -p 5000:5000 -v $(pwd):/data osrm/osrm-backend osrm-routed --algorithm mld /data/israel-and-palestine-latest.osrm
```

---

## Day 12: Real Estate Data Processing
**Objective**: Housing market data integration and price trending

**Tasks**:
- [ ] Tax Authority transaction data processing
- [ ] Price normalization and validation
- [ ] Geocoding of transaction addresses
- [ ] Price trend analysis by region
- [ ] Housing affordability metrics

**Acceptance Criteria**:
- Transaction data cleaned and geocoded
- Price per sqm calculated by region
- Trend analysis (6mo/12mo/24mo)
- Affordability indices computed

---

## Day 13: Scoring Algorithm Implementation
**Objective**: Multi-component neighborhood scoring system

**Tasks**:
- [ ] Component score calculation (education, crime, services, transit, housing)
- [ ] Z-score normalization across regions
- [ ] Weighted composite scoring (0-100 scale)
- [ ] Score validation and calibration
- [ ] Performance optimization

**Acceptance Criteria**:
- All regions have complete component scores
- Composite scores distributed appropriately (normal distribution)
- Scoring queries execute <200ms
- Score accuracy validated against known neighborhoods

## Day 14: Advanced UI Components
**Objective**: Enhanced user interface with filtering and search

**Tasks**:
- [ ] Address search autocomplete component
- [ ] Neighborhood filter sidebar
- [ ] Score visualization (charts/gauges)
- [ ] Mobile bottom sheet UI patterns
- [ ] Real-time map updates with filters

**Acceptance Criteria**:
- Search autocomplete working smoothly
- Filters applied without page refresh
- Score visualization clear and informative
- Mobile-optimized UI components
- Smooth interactions on touch devices

**Routing Funnel Logic**:
```python
# Stage 0: Geometric prefilter
candidates = filter_by_distance(origin, max_radius=50km)

# Stage 1: OSRM batch processing  
if len(candidates) > 1000:
    candidates = osrm_matrix_filter(candidates, threshold=45min)

# Stage 2: Google Routes (traffic-aware)
if mode == "driving" and departure_time.hour in [7,8,9,17,18,19]:
    results = google_routes_matrix(candidates[:100])
else:
    results = osrm_results  # Use Stage 1 results
```

---

## Day 15-16: FastAPI Backend Implementation
**Objective**: Production-ready API with all core endpoints

**Tasks**:
- [ ] Address search and geocoding endpoint
- [ ] Address profile generation endpoint  
- [ ] Reverse search with filtering
- [ ] Commute filtering endpoint
- [ ] Neighborhood comparison API
- [ ] Request validation and error handling

**Acceptance Criteria**:
- All endpoints functional with proper validation
- Response times meet performance targets
- Error handling comprehensive
- API documentation auto-generated

**Key Endpoints**:
```python
# Core API endpoints
GET  /health                           # Health check
GET  /address/search?q={query}         # Address search
GET  /address/{id}/profile             # Address profile  
POST /search/reverse                   # Filtered neighborhood search
POST /commute/filter                   # Commute-based filtering
GET  /compare?regions={id1,id2,id3}    # Neighborhood comparison
```

---

## Day 17: Caching & Performance Optimization
**Objective**: Sub-second response times for all critical paths

**Tasks**:
- [ ] Redis caching implementation
- [ ] Database query optimization
- [ ] Spatial index tuning
- [ ] Response compression
- [ ] API rate limiting

**Acceptance Criteria**:
- Address profiles generated <2s
- Reverse search <1.5s (metro areas)
- Cache hit rates >70%
- Database queries optimized with EXPLAIN ANALYZE

---

## Day 18: Vector Tiles Generation
**Objective**: High-performance map data delivery

**Tasks**:
- [ ] Neighborhood boundaries → vector tiles
- [ ] Score data integration in tile properties
- [ ] Multi-zoom level optimization
- [ ] Tile server setup and testing
- [ ] CDN preparation

**Acceptance Criteria**:
- Tiles generated for zoom levels 6-14
- File sizes optimized (<50KB per tile avg)
- Tile server responding <100ms
- Properties include neighborhood scores

**Tile Generation**:
```bash
# Export neighborhood data
ogr2ogr -f GeoJSON tiles/neighborhoods.geojson \
  PG:"host=localhost dbname=ni" \
  -sql "SELECT neigh_id, name_he, score_0_100, geom FROM neighborhoods_canonical"

# Generate vector tiles
tippecanoe -o tiles/neighborhoods.mbtiles \
  -zg --drop-densest-as-needed \
  -l neighborhoods tiles/neighborhoods.geojson
```

---

## Day 19-20: API Testing & Documentation
**Objective**: Comprehensive testing and API documentation

**Tasks**:
- [ ] Unit test coverage >90%
- [ ] Integration tests for all endpoints
- [ ] Load testing with realistic scenarios
- [ ] API documentation with examples
- [ ] Error handling validation

**Acceptance Criteria**:
- Test suite passes with high coverage
- Load tests confirm performance targets
- API documentation complete
- All error scenarios handled gracefully

---

### Phase 3: Frontend Development (Days 21-35)

## Day 21-22: Next.js PWA Setup
**Objective**: Mobile-first PWA foundation with RTL support

**Tasks**:
- [ ] Next.js 14 project initialization
- [ ] PWA configuration (service worker, manifest)
- [ ] RTL support setup (Hebrew/Arabic)
- [ ] Tailwind CSS with RTL classes
- [ ] Base layout and routing structure

**Acceptance Criteria**:
- PWA installable on mobile devices
- RTL text rendering correctly
- Base routing structure functional
- Lighthouse PWA score >90

---

## Day 23-24: Map Integration & Vector Tiles
**Objective**: Interactive map with neighborhood visualization

**Tasks**:
- [ ] Mapbox GL integration
- [ ] Vector tile rendering
- [ ] Interactive layer controls
- [ ] Heatmap visualization for scores
- [ ] Mobile touch/zoom optimization

**Acceptance Criteria**:
- Map loads <2s on mobile
- Vector tiles rendering smoothly
- Heatmap shows neighborhood scores accurately
- Touch interactions optimized for mobile

---

## Day 25-26: Address Search & Profile UI
**Objective**: Address input with comprehensive neighborhood profiles

**Tasks**:
- [ ] Address search autocomplete
- [ ] Profile page with score breakdown
- [ ] Component visualization (charts/gauges)
- [ ] Nearby POI display
- [ ] Google Places integration (optional tab)

**Acceptance Criteria**:
- Search autocomplete working smoothly
- Profile loads <2s with all components
- Score visualization clear and informative
- Mobile-optimized layout with bottom sheets

---

## Day 27-28: Filter System & Reverse Search
**Objective**: Complex filtering UI with map integration

**Tasks**:
- [ ] Filter drawer with all criteria options
- [ ] Real-time map updates as filters change
- [ ] Results list with sorting/ranking
- [ ] Filter presets and saving
- [ ] URL state management for sharing

**Acceptance Criteria**:
- Filters applied without page refresh
- Map updates smoothly with filter changes
- Results ranked by composite score
- Shareable URLs for filter combinations

---

## Day 29: Commute Filter Interface
**Objective**: Commute-based neighborhood filtering

**Tasks**:
- [ ] Work address input with autocomplete
- [ ] Transport mode selection (car/transit/bike/walk)
- [ ] Time threshold slider
- [ ] Departure time picker
- [ ] Isochrone map overlay

**Acceptance Criteria**:
- Commute calculations complete <3s
- Isochrone overlay renders smoothly
- Multiple transport modes working
- Results update in real-time

---

## Day 30: Comparison Interface
**Objective**: Side-by-side neighborhood comparison

**Tasks**:
- [ ] Multi-select neighborhood interface
- [ ] Radar chart score comparison
- [ ] Side-by-side data table
- [ ] Export/share functionality
- [ ] Mobile-optimized layout

**Acceptance Criteria**:
- Comparison supports 2-3 neighborhoods
- Radar chart renders correctly
- Data differences highlighted clearly
- Export functionality working

---

## Day 31-32: Mobile Optimization & PWA Features
**Objective**: Native-like mobile experience

**Tasks**:
- [ ] Bottom sheet UI patterns
- [ ] Swipe gestures and interactions
- [ ] Offline capability for core features
- [ ] Push notification setup (optional)
- [ ] App icon and splash screen

**Acceptance Criteria**:
- Native-like interactions on mobile
- Offline mode for cached searches
- App icon and splash screen configured
- Performance optimized for mobile devices

---

## Day 33-34: RTL & Localization
**Objective**: Hebrew/Arabic language support

**Tasks**:
- [ ] RTL layout adjustments
- [ ] Hebrew text rendering validation
- [ ] Arabic interface support (basic)
- [ ] Number formatting (Hebrew numerals)
- [ ] Date/time localization

**Acceptance Criteria**:
- Hebrew interface fully functional
- RTL layouts render correctly
- Arabic support basic but functional
- All text content localized properly

---

## Day 35: Frontend Testing & Performance
**Objective**: Comprehensive testing and performance optimization

**Tasks**:
- [ ] Component testing with Jest/Testing Library
- [ ] E2E testing with Playwright
- [ ] Performance optimization (code splitting, lazy loading)
- [ ] Lighthouse score optimization
- [ ] Cross-browser testing

**Acceptance Criteria**:
- Test coverage >80% for components
- E2E tests covering critical user journeys
- Lighthouse scores: Performance >90, PWA >90
- Works on iOS Safari, Android Chrome

---

### Phase 4: Integration & Deployment (Days 36-45)

## Day 36-37: API Deployment & Infrastructure
**Objective**: Production API deployment with monitoring

**Tasks**:
- [ ] Fly.io/Render deployment configuration
- [ ] Environment variable management
- [ ] Database migration on production
- [ ] Health checks and monitoring
- [ ] Automated deployment pipeline

**Acceptance Criteria**:
- API deployed and accessible
- Database successfully migrated
- Health checks passing
- Deployment pipeline functional

---

## Day 38-39: Frontend Deployment & CDN
**Objective**: Production frontend with global delivery

**Tasks**:
- [ ] Vercel deployment configuration
- [ ] Environment-specific builds
- [ ] CDN setup for vector tiles
- [ ] SSL/HTTPS configuration
- [ ] Domain setup and DNS

**Acceptance Criteria**:
- Frontend deployed and accessible
- CDN serving tiles globally
- HTTPS properly configured
- Custom domain functional

---

## Day 40-41: End-to-End Testing & QA
**Objective**: Comprehensive testing of production system

**Tasks**:
- [ ] End-to-end user journey testing
- [ ] Performance testing under load
- [ ] Mobile device testing (iOS/Android)
- [ ] API rate limiting validation
- [ ] Error handling and recovery testing

**Acceptance Criteria**:
- All critical user journeys working
- Performance targets met under load
- Mobile experience validated
- Error handling comprehensive

---

## Day 42-43: Analytics & Monitoring Setup
**Objective**: Production monitoring and user analytics

**Tasks**:
- [ ] Sentry error tracking integration
- [ ] PostHog analytics implementation
- [ ] Performance monitoring setup
- [ ] Cost monitoring and alerting
- [ ] Usage analytics dashboard

**Acceptance Criteria**:
- Error tracking capturing all issues
- User analytics functional
- Performance metrics monitored
- Cost alerts configured

---

## Day 44: Documentation & Launch Preparation
**Objective**: Complete documentation and launch readiness

**Tasks**:
- [ ] User guide and help documentation
- [ ] Technical documentation updates
- [ ] Launch checklist completion
- [ ] Marketing materials preparation
- [ ] Beta user recruitment

**Acceptance Criteria**:
- Documentation complete and accessible
- Launch checklist verified
- Beta testing group ready
- Marketing materials prepared

---

## Day 45: MVP Launch & Post-Launch Monitoring
**Objective**: Production launch with immediate monitoring

**Tasks**:
- [ ] Production deployment verification
- [ ] Launch announcement and user onboarding
- [ ] Real-time monitoring and issue response
- [ ] User feedback collection setup
- [ ] Post-launch retrospective

**Acceptance Criteria**:
- MVP successfully launched
- No critical issues in first 24 hours
- User feedback collection active
- Monitoring systems fully operational

---

## Risk Mitigation & Contingency Plans

### High-Risk Items
1. **Google API Costs**: Stage 2 routing could exceed budget
   - Mitigation: Aggressive caching, request throttling, Stage 1 fallback

2. **Data Quality**: Some data sources may have gaps/errors
   - Mitigation: Multiple validation layers, manual QA for major cities

3. **Performance**: Complex spatial queries may be slow
   - Mitigation: Aggressive indexing, query optimization, caching layers

4. **Mobile Performance**: Map rendering may be slow on older devices
   - Mitigation: Progressive loading, simplified mobile rendering

### Fallback Plans
- **Routing**: OSRM-only mode if Google API costs too high
- **Data**: Focus on major metro areas first if full coverage problematic
- **Features**: Core address profile + basic search as minimum viable

### Success Metrics
- **Technical**: Response times, uptime, error rates
- **User**: Search success rate, session duration, return usage
- **Business**: Cost per user, conversion to engaged user, geographic coverage

---

## Daily Standups & Progress Tracking
- Daily progress check against acceptance criteria
- Blocker identification and resolution
- Scope adjustment if needed to meet timeline
- Regular stakeholder updates on progress and risks