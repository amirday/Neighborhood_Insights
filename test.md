# Testing Strategy - Neighborhood Insights IL

## Testing Philosophy
Comprehensive testing strategy ensuring reliability of location-critical features while maintaining development velocity.

## Test Pyramid Structure

### Unit Tests (70%)
**Target Coverage: 90%+**

#### Backend (`api/tests/`)
```
api/tests/
├── unit/
│   ├── test_models.py           # Pydantic model validation
│   ├── test_scoring.py          # Scoring algorithm logic
│   ├── test_geocoding.py        # Address normalization
│   ├── test_routing.py          # Routing funnel logic
│   └── test_utils.py            # Utility functions
├── integration/
│   ├── test_database.py         # PostGIS queries
│   ├── test_external_apis.py    # Google Routes, Places
│   └── test_etl_pipeline.py     # Data ingestion
└── fixtures/
    ├── sample_addresses.json
    ├── mock_routes_response.json
    └── test_regions.geojson
```

#### ETL Pipeline (`etl/tests/`)
```
etl/tests/
├── test_cbs_processor.py        # CBS statistical areas ETL
├── test_education_etl.py        # MoE schools processing
├── test_crime_etl.py            # Police data normalization
├── test_osm_processor.py        # OSM POI extraction
├── test_gtfs_processor.py       # Transit data processing
├── test_scoring_engine.py       # Neighborhood scoring
└── data/
    ├── sample_cbs.geojson
    ├── sample_schools.csv
    └── sample_osm.json
```

#### Frontend (`app/tests/`)
```
app/tests/
├── unit/
│   ├── components/
│   │   ├── AddressSearch.test.tsx
│   │   ├── MapView.test.tsx
│   │   ├── FilterDrawer.test.tsx
│   │   └── ScoreCard.test.tsx
│   ├── hooks/
│   │   ├── useGeolocation.test.ts
│   │   ├── useCommute.test.ts
│   │   └── useNeighborhoods.test.ts
│   └── utils/
│       ├── scoring.test.ts
│       ├── geocoding.test.ts
│       └── rtl.test.ts
└── setup/
    ├── test-utils.tsx           # Testing library setup
    ├── mocks/                   # API response mocks
    └── fixtures/                # Test data
```

### Integration Tests (20%)
**Focus: Critical user journeys**

#### API Integration
```python
# api/tests/integration/test_address_profile.py
def test_address_profile_flow():
    """Test complete address → profile generation"""
    response = client.post("/address/profile", {
        "address": "דיזנגוף 1, תל אביב"
    })
    assert response.status_code == 200
    profile = response.json()
    assert "score_0_100" in profile
    assert "components" in profile
    assert len(profile["nearby_pois"]) > 0
```

#### Database Integration
```python
# api/tests/integration/test_scoring.py
def test_neighborhood_scoring():
    """Test scoring algorithm with real PostGIS queries"""
    region_id = test_regions[0]["id"]
    score = compute_neighborhood_score(region_id)
    assert 0 <= score <= 100
    assert score.education_component is not None
```

#### External API Integration
```python
# api/tests/integration/test_routing.py
@mock.patch('google_routes.compute_route_matrix')
def test_commute_calculation(mock_routes):
    """Test multi-stage routing funnel"""
    mock_routes.return_value = fixtures.routes_response
    result = calculate_commute_time(origin, destinations, mode="driving")
    assert len(result) == len(destinations)
```

### End-to-End Tests (10%)
**Focus: Critical user flows in production-like environment**

#### Playwright Tests (`e2e/tests/`)
```typescript
// e2e/tests/reverse-search.spec.ts
test('Reverse search flow', async ({ page }) => {
  await page.goto('/discover');
  
  // Set filters
  await page.click('[data-testid=education-filter]');
  await page.selectOption('[data-testid=education-min]', '8');
  
  // Apply filters
  await page.click('[data-testid=apply-filters]');
  
  // Verify results
  await expect(page.locator('[data-testid=results-list]')).toBeVisible();
  await expect(page.locator('[data-testid=map-heatmap]')).toBeVisible();
});
```

```typescript
// e2e/tests/address-profile.spec.ts  
test('Address profile generation', async ({ page }) => {
  await page.goto('/');
  
  // Search for address
  await page.fill('[data-testid=address-input]', 'דיזנגוף 1, תל אביב');
  await page.click('[data-testid=search-button]');
  
  // Verify profile loads
  await expect(page.locator('[data-testid=neighborhood-score]')).toBeVisible();
  await expect(page.locator('[data-testid=score-components]')).toBeVisible();
  
  // Test mobile responsiveness
  await page.setViewportSize({ width: 375, height: 667 });
  await expect(page.locator('[data-testid=bottom-sheet]')).toBeVisible();
});
```

## Test Data Strategy

### Synthetic Test Data
```
data/test/
├── regions/
│   ├── tel_aviv_sample.geojson     # 10 representative neighborhoods
│   ├── jerusalem_sample.geojson    # Mixed urban/suburban areas
│   └── haifa_sample.geojson        # Coastal geography
├── addresses/
│   ├── valid_addresses.json        # Known geocodable addresses
│   ├── edge_cases.json             # Boundary cases, typos
│   └── rtl_addresses.json          # Hebrew/Arabic formatting
└── external_apis/
    ├── google_routes_samples.json
    ├── places_api_samples.json
    └── osrm_responses.json
```

### Test Database
- Dockerized PostGIS with sample Israeli data
- Includes ~1000 statistical areas from major metros
- Pre-computed scores and POI data for consistent testing

## Performance Testing

### Load Testing
```python
# tests/performance/test_api_load.py
@pytest.mark.performance
def test_reverse_search_load():
    """Test API performance under concurrent load"""
    # Simulate 100 concurrent reverse search requests
    # Target: 95th percentile < 1.5s for metro areas
```

### Geospatial Query Performance
```sql
-- Test spatial query performance
EXPLAIN ANALYZE 
SELECT region_id, ST_Distance(geom, ST_Point(34.7818, 32.0853))
FROM regions 
WHERE ST_DWithin(geom, ST_Point(34.7818, 32.0853), 0.01)
ORDER BY ST_Distance(geom, ST_Point(34.7818, 32.0853))
LIMIT 10;
```

## Browser Testing Matrix

### Primary Targets (MVP)
- **iOS Safari** (14+): Mobile primary
- **Android Chrome** (90+): Mobile primary  
- **Desktop Chrome** (100+): Development/admin

### Secondary Targets
- **Samsung Internet**: Android alternative
- **Firefox Mobile**: Privacy-conscious users
- **Desktop Safari**: Mac users

## CI/CD Testing Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:16-3.4
    steps:
      - uses: actions/checkout@v4
      - name: Run backend tests
        run: |
          cd api && python -m pytest tests/unit/
      - name: Run ETL tests  
        run: |
          cd etl && python -m pytest tests/
      - name: Run frontend tests
        run: |
          cd app && npm test -- --coverage

  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run API integration tests
        run: docker-compose -f docker-compose.test.yml up --abort-on-container-exit

  e2e-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run Playwright tests
        run: |
          npx playwright install
          npm run test:e2e
```

## Quality Gates

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/unit/
        language: system
        pass_filenames: false
```

### Coverage Requirements
- **Backend**: 90%+ line coverage
- **ETL**: 85%+ line coverage  
- **Frontend**: 80%+ line coverage
- **Critical paths**: 100% coverage (scoring, routing, geocoding)

## Test Environment Setup

### Local Development
```bash
# Start test dependencies
make test-setup

# Run full test suite
make test-all

# Run specific test categories
make test-unit
make test-integration  
make test-e2e
```

### Test Data Refresh
```bash
# Refresh synthetic test data
make test-data-refresh

# Validate test database
make test-db-validate
```

## Monitoring & Alerting

### Test Health Metrics
- Test execution time trends
- Flaky test identification  
- Coverage regression alerts
- Performance benchmark tracking

### Production Testing
- Synthetic user journey monitoring
- API health checks with real geography
- Performance regression detection