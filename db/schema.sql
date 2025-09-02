-- Neighborhood Insights IL - Database Schema
-- PostGIS-enabled schema for Israeli neighborhood analysis

-- =============================================
-- EXTENSIONS
-- =============================================

-- Enable PostGIS for spatial operations
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Enable additional extensions for performance and functionality
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- For fuzzy text search

-- =============================================
-- ENUMS & TYPES
-- =============================================

-- Transport modes for routing
CREATE TYPE transport_mode AS ENUM (
    'driving',
    'driving_traffic', 
    'transit',
    'bicycling',
    'walking'
);

-- POI categories
CREATE TYPE poi_category AS ENUM (
    'supermarket',
    'pharmacy', 
    'clinic',
    'hospital',
    'school',
    'kindergarten',
    'park',
    'community_center',
    'bank',
    'post_office',
    'shopping_mall',
    'restaurant'
);

-- School sectors (Israeli education system)
CREATE TYPE school_sector AS ENUM (
    'jewish_secular',
    'jewish_religious', 
    'jewish_haredi',
    'arab',
    'druze',
    'circassian'
);

-- School levels
CREATE TYPE school_level AS ENUM (
    'elementary',
    'middle', 
    'high',
    'comprehensive'
);

-- =============================================
-- CORE GEOGRAPHIC ENTITIES
-- =============================================

-- CBS Statistical Areas (primary geographic unit)
CREATE TABLE regions (
    region_id SERIAL PRIMARY KEY,
    lamas_code VARCHAR(16) UNIQUE NOT NULL, -- CBS LAMAS code
    name_he TEXT NOT NULL, -- Hebrew name
    name_en TEXT, -- English name (optional)
    name_ar TEXT, -- Arabic name (optional)
    municipality_code VARCHAR(10), -- Municipal authority code
    district_code VARCHAR(2), -- District code (1-7)
    sub_district_code VARCHAR(4), -- Sub-district code  
    population_2022 INTEGER, -- Latest population count
    area_sqkm NUMERIC(10,4), -- Area in square kilometers
    density_per_sqkm NUMERIC(10,2), -- Population density
    geom GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Canonical neighborhoods (aggregated from statistical areas)
CREATE TABLE neighborhoods_canonical (
    neigh_id SERIAL PRIMARY KEY,
    name_he TEXT NOT NULL,
    name_en TEXT,
    name_ar TEXT, 
    municipality_code VARCHAR(10),
    sa_list INTEGER[] NOT NULL, -- Array of statistical area IDs
    population_total INTEGER,
    area_sqkm NUMERIC(10,4),
    geom GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Representative points for regions (for distance calculations)
CREATE TABLE centroids (
    region_id INTEGER PRIMARY KEY REFERENCES regions(region_id) ON DELETE CASCADE,
    geom GEOMETRY(POINT, 4326) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- DEMOGRAPHIC & SOCIOECONOMIC DATA
-- =============================================

CREATE TABLE demographics (
    region_id INTEGER PRIMARY KEY REFERENCES regions(region_id) ON DELETE CASCADE,
    
    -- Population breakdown
    pop_total INTEGER,
    pop_jewish INTEGER,
    pop_arab INTEGER, 
    pop_other INTEGER,
    
    -- Age groups
    pop_age_0_17 INTEGER,
    pop_age_18_64 INTEGER,
    pop_age_65_plus INTEGER,
    
    -- Households
    households_total INTEGER,
    avg_household_size NUMERIC(3,2),
    households_families INTEGER,
    households_single_person INTEGER,
    
    -- Socioeconomic indices (CBS standardized 1-20 scale)
    se_index_overall NUMERIC(4,2), -- Overall socioeconomic index
    se_index_education NUMERIC(4,2), -- Education component
    se_index_income NUMERIC(4,2), -- Income component
    se_index_employment NUMERIC(4,2), -- Employment component
    
    -- Labor force
    labor_force_participation NUMERIC(5,2), -- Percentage
    unemployment_rate NUMERIC(5,2), -- Percentage
    
    -- Education levels (percentage with degree)
    education_academic NUMERIC(5,2), -- Academic degree
    education_secondary NUMERIC(5,2), -- Secondary education
    
    data_year INTEGER DEFAULT 2022,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- EDUCATION INSTITUTIONS
-- =============================================

CREATE TABLE schools (
    school_id TEXT PRIMARY KEY, -- MoE institution ID
    name_he TEXT NOT NULL,
    name_en TEXT,
    name_ar TEXT,
    
    -- Classification
    sector school_sector,
    level school_level,
    supervision_type VARCHAR(50), -- Government/municipal/private
    
    -- Academic performance (Mitzav/RAMA scores)
    mizav_math_score NUMERIC(5,2), -- Mathematics score
    mizav_hebrew_score NUMERIC(5,2), -- Hebrew/Language score  
    mizav_english_score NUMERIC(5,2), -- English score
    mizav_science_score NUMERIC(5,2), -- Science score
    mizav_year INTEGER, -- Test year
    
    -- Enrollment
    students_total INTEGER,
    students_by_grade JSONB, -- Grade-level breakdown
    teachers_total INTEGER,
    students_per_teacher NUMERIC(4,1),
    
    -- Infrastructure
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    
    region_id INTEGER REFERENCES regions(region_id),
    geom GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- CRIME & SAFETY DATA
-- =============================================

CREATE TABLE crime (
    region_id INTEGER PRIMARY KEY REFERENCES regions(region_id) ON DELETE CASCADE,
    
    -- Total incidents
    incidents_total INTEGER,
    incidents_per_1000 NUMERIC(6,2),
    
    -- Crime categories
    violent_crime INTEGER, 
    property_crime INTEGER,
    drug_offenses INTEGER,
    traffic_violations INTEGER,
    
    -- Normalized rates (per 1000 residents)
    violent_crime_rate NUMERIC(6,2),
    property_crime_rate NUMERIC(6,2),
    drug_offenses_rate NUMERIC(6,2),
    
    -- Safety perception metrics (if available)
    safety_index NUMERIC(4,2), -- 1-10 scale
    
    data_year INTEGER DEFAULT 2022,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- HEALTH FACILITIES
-- =============================================

CREATE TABLE health_facilities (
    facility_id TEXT PRIMARY KEY, -- MoH facility ID
    name_he TEXT NOT NULL,
    name_en TEXT,
    name_ar TEXT,
    
    -- Classification
    facility_type VARCHAR(50), -- Hospital/Clinic/Emergency/Specialist
    operator VARCHAR(100), -- HMO/Government/Private
    specialties TEXT[], -- Medical specialties offered
    
    -- Services
    emergency_services BOOLEAN DEFAULT FALSE,
    intensive_care BOOLEAN DEFAULT FALSE,
    surgery BOOLEAN DEFAULT FALSE,
    maternity BOOLEAN DEFAULT FALSE,
    
    -- Contact
    address TEXT,
    phone VARCHAR(20),
    website VARCHAR(200),
    
    region_id INTEGER REFERENCES regions(region_id),
    geom GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- POINTS OF INTEREST (OSM + Official Sources)
-- =============================================

CREATE TABLE poi_osm (
    osm_id BIGINT PRIMARY KEY,
    osm_type CHAR(1), -- 'N'ode, 'W'ay, 'R'elation
    name_he TEXT,
    name_en TEXT, 
    name_ar TEXT,
    category poi_category,
    tags JSONB, -- Original OSM tags
    
    -- Derived attributes
    brand VARCHAR(100),
    opening_hours TEXT,
    wheelchair_accessible BOOLEAN,
    
    region_id INTEGER REFERENCES regions(region_id),
    geom GEOMETRY(GEOMETRY, 4326), -- Point/Polygon geometry
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- TRANSIT INFRASTRUCTURE
-- =============================================

CREATE TABLE stops (
    stop_id TEXT PRIMARY KEY, -- GTFS stop_id
    stop_name_he TEXT,
    stop_name_en TEXT,
    stop_name_ar TEXT,
    
    -- Stop characteristics
    stop_type VARCHAR(20), -- Bus/Train/Light_Rail
    wheelchair_boarding BOOLEAN DEFAULT FALSE,
    
    -- Agencies serving this stop
    agencies TEXT[], -- Array of agency names
    route_count INTEGER, -- Number of routes serving stop
    
    region_id INTEGER REFERENCES regions(region_id),
    geom GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- REAL ESTATE TRANSACTIONS
-- =============================================

CREATE TABLE deals (
    deal_id BIGSERIAL PRIMARY KEY,
    
    -- Transaction details
    deal_date DATE NOT NULL,
    price_ils NUMERIC(12,2), -- Price in Israeli Shekels
    price_per_sqm NUMERIC(10,2),
    
    -- Property characteristics  
    property_type VARCHAR(50), -- Apartment/House/Commercial
    rooms NUMERIC(3,1), -- Number of rooms
    sqm_built NUMERIC(8,2), -- Built area
    sqm_garden NUMERIC(8,2), -- Garden area (if applicable)
    floor_number INTEGER,
    total_floors INTEGER,
    parking_spaces INTEGER,
    
    -- Property condition
    property_age INTEGER, -- Years since construction
    renovation_year INTEGER,
    
    -- Location
    address TEXT,
    street VARCHAR(200),
    house_number VARCHAR(10),
    
    region_id INTEGER REFERENCES regions(region_id),
    geom GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- NEIGHBORHOOD SCORING
-- =============================================

-- Component scores (z-scores normalized across all regions)
CREATE TABLE scores_components (
    region_id INTEGER PRIMARY KEY REFERENCES regions(region_id) ON DELETE CASCADE,
    
    -- Raw z-scores (-3 to +3 typical range)
    z_education NUMERIC(6,3), -- School quality + proximity
    z_crime NUMERIC(6,3), -- Safety (inverted - lower crime = higher score)  
    z_services NUMERIC(6,3), -- POI accessibility
    z_transit NUMERIC(6,3), -- Public transport connectivity
    z_housing NUMERIC(6,3), -- Affordability + availability
    z_demographics NUMERIC(6,3), -- Socioeconomic factors
    
    -- Computed at
    computed_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Final neighborhood scores (0-100 scale)
CREATE TABLE scores_neighborhood (
    region_id INTEGER PRIMARY KEY REFERENCES regions(region_id) ON DELETE CASCADE,
    score_0_100 INTEGER CHECK (score_0_100 BETWEEN 0 AND 100),
    
    -- Component contributions (for transparency)
    education_contribution NUMERIC(5,2),
    crime_contribution NUMERIC(5,2),
    services_contribution NUMERIC(5,2),
    transit_contribution NUMERIC(5,2),
    housing_contribution NUMERIC(5,2),
    demographics_contribution NUMERIC(5,2),
    
    -- Weights used in calculation (for reproducibility)
    weights_used JSONB,
    
    computed_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- COMMUTE ROUTING CACHE
-- =============================================

-- Short-term routing cache (30-60 minutes TTL)
CREATE TABLE commute_cache_short (
    cache_key TEXT PRIMARY KEY, -- hash(origin,destination,mode,time_bucket)
    
    origin_region_id INTEGER REFERENCES regions(region_id),
    destination_coords GEOMETRY(POINT, 4326),
    mode transport_mode,
    
    -- Time bucketing (e.g., "2024-01-15 08:00" for 8-9am window)
    depart_time_bucket TIMESTAMP,
    
    -- Results
    duration_seconds INTEGER,
    distance_meters INTEGER,
    route_geometry GEOMETRY(LINESTRING, 4326), -- Optional route polyline
    
    -- Metadata
    provider VARCHAR(20), -- 'osrm', 'google_routes', 'otp'
    confidence_level NUMERIC(3,2), -- Quality indicator
    
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '30 minutes'
);

-- =============================================
-- SPATIAL INDICES
-- =============================================

-- Primary spatial indices
CREATE INDEX regions_geom_gix ON regions USING GIST (geom);
CREATE INDEX neighborhoods_canonical_geom_gix ON neighborhoods_canonical USING GIST (geom);
CREATE INDEX centroids_geom_gix ON centroids USING GIST (geom);

-- POI and facilities spatial indices
CREATE INDEX schools_geom_gix ON schools USING GIST (geom);
CREATE INDEX health_facilities_geom_gix ON health_facilities USING GIST (geom);
CREATE INDEX poi_osm_geom_gix ON poi_osm USING GIST (geom);
CREATE INDEX stops_geom_gix ON stops USING GIST (geom);
CREATE INDEX deals_geom_gix ON deals USING GIST (geom);

-- =============================================
-- PERFORMANCE INDICES
-- =============================================

-- Region lookups
CREATE INDEX regions_lamas_code_idx ON regions (lamas_code);
CREATE INDEX regions_municipality_code_idx ON regions (municipality_code);
CREATE INDEX regions_district_code_idx ON regions (district_code);

-- Name-based search indices (with trigram support)
CREATE INDEX regions_name_he_trgm_idx ON regions USING GIN (name_he gin_trgm_ops);
CREATE INDEX schools_name_he_trgm_idx ON schools USING GIN (name_he gin_trgm_ops);
CREATE INDEX poi_osm_name_he_trgm_idx ON poi_osm USING GIN (name_he gin_trgm_ops);

-- Scoring and ranking indices  
CREATE INDEX scores_neighborhood_score_idx ON scores_neighborhood (score_0_100 DESC);
CREATE INDEX schools_mizav_math_idx ON schools (mizav_math_score DESC NULLS LAST);
CREATE INDEX crime_incidents_per_1000_idx ON crime (incidents_per_1000);

-- Real estate indices
CREATE INDEX deals_deal_date_idx ON deals (deal_date DESC);
CREATE INDEX deals_price_per_sqm_idx ON deals (price_per_sqm);
CREATE INDEX deals_region_date_idx ON deals (region_id, deal_date DESC);

-- Cache management
CREATE INDEX commute_cache_short_expires_at_idx ON commute_cache_short (expires_at);
CREATE INDEX commute_cache_short_region_mode_idx ON commute_cache_short (origin_region_id, mode);

-- Composite indices for common query patterns
CREATE INDEX regions_district_pop_idx ON regions (district_code, population_2022 DESC);
CREATE INDEX schools_sector_mizav_idx ON schools (sector, mizav_math_score DESC NULLS LAST);

-- =============================================
-- CONSTRAINTS & VALIDATION
-- =============================================

-- Ensure valid geometry
ALTER TABLE regions ADD CONSTRAINT regions_valid_geom CHECK (ST_IsValid(geom));
ALTER TABLE neighborhoods_canonical ADD CONSTRAINT neighborhoods_valid_geom CHECK (ST_IsValid(geom));
ALTER TABLE centroids ADD CONSTRAINT centroids_valid_geom CHECK (ST_IsValid(geom));

-- Ensure centroids are within Israel bounds (approximate)
ALTER TABLE centroids ADD CONSTRAINT centroids_israel_bounds 
    CHECK (ST_X(geom) BETWEEN 34.0 AND 36.0 AND ST_Y(geom) BETWEEN 29.0 AND 34.0);

-- Demographic data validation
ALTER TABLE demographics ADD CONSTRAINT demographics_positive_pop CHECK (pop_total >= 0);
ALTER TABLE demographics ADD CONSTRAINT demographics_valid_se_index 
    CHECK (se_index_overall BETWEEN 1 AND 20 OR se_index_overall IS NULL);

-- Real estate data validation  
ALTER TABLE deals ADD CONSTRAINT deals_positive_price CHECK (price_ils > 0);
ALTER TABLE deals ADD CONSTRAINT deals_valid_date CHECK (deal_date >= '1948-01-01'::date);
ALTER TABLE deals ADD CONSTRAINT deals_reasonable_sqm CHECK (sqm_built > 0 AND sqm_built < 10000);

-- =============================================
-- VIEWS FOR COMMON QUERIES
-- =============================================

-- Complete region information with scores
CREATE VIEW regions_with_scores AS
SELECT 
    r.*,
    s.score_0_100,
    s.education_contribution,
    s.crime_contribution,
    s.services_contribution,
    s.transit_contribution,
    s.housing_contribution,
    s.demographics_contribution,
    d.pop_total,
    d.se_index_overall,
    ST_AsGeoJSON(r.geom)::jsonb as geom_geojson
FROM regions r
LEFT JOIN scores_neighborhood s ON r.region_id = s.region_id
LEFT JOIN demographics d ON r.region_id = d.region_id;

-- Neighborhood amenities summary
CREATE VIEW neighborhood_amenities AS
SELECT 
    r.region_id,
    r.name_he,
    COUNT(DISTINCT s.school_id) as schools_count,
    COUNT(DISTINCT h.facility_id) as health_facilities_count,
    COUNT(DISTINCT p.osm_id) FILTER (WHERE p.category = 'supermarket') as supermarkets_count,
    COUNT(DISTINCT p.osm_id) FILTER (WHERE p.category = 'pharmacy') as pharmacies_count,
    COUNT(DISTINCT p.osm_id) FILTER (WHERE p.category = 'park') as parks_count,
    COUNT(DISTINCT st.stop_id) as transit_stops_count
FROM regions r
LEFT JOIN schools s ON r.region_id = s.region_id
LEFT JOIN health_facilities h ON r.region_id = h.region_id  
LEFT JOIN poi_osm p ON r.region_id = p.region_id
LEFT JOIN stops st ON r.region_id = st.region_id
GROUP BY r.region_id, r.name_he;

-- =============================================
-- FUNCTIONS
-- =============================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to relevant tables
CREATE TRIGGER update_regions_updated_at BEFORE UPDATE ON regions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_demographics_updated_at BEFORE UPDATE ON demographics 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_schools_updated_at BEFORE UPDATE ON schools 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scores_neighborhood_updated_at BEFORE UPDATE ON scores_neighborhood 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Cache cleanup function
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM commute_cache_short WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE 'plpgsql';

-- =============================================
-- INITIAL SETUP COMPLETE
-- =============================================

-- Log schema creation
INSERT INTO pg_stat_statements_info VALUES ('schema_created', NOW()::TEXT) 
    ON CONFLICT DO NOTHING;

-- Display setup summary
DO $$
BEGIN
    RAISE NOTICE 'Neighborhood Insights IL Database Schema Created Successfully';
    RAISE NOTICE 'PostGIS Version: %', PostGIS_Version();
    RAISE NOTICE 'Total Tables: %', (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public');
    RAISE NOTICE 'Total Indices: %', (SELECT count(*) FROM pg_indexes WHERE schemaname = 'public');
    RAISE NOTICE 'Schema optimized for Israeli neighborhood analysis and spatial queries';
END;
$$;