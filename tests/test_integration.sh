#!/bin/bash

# End-to-End Integration Tests
# Tests complete user workflows from API to database

set -e

echo "🔗 End-to-End Integration Tests"
echo "==============================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

tests_passed=0
tests_failed=0
setup_cleanup_needed=false

# Helper functions
run_integration_test() {
    local test_name="$1"
    local test_function="$2"
    
    echo -e "${BLUE}🧪 Running: $test_name${NC}"
    
    if $test_function; then
        echo -e "${GREEN}✅ $test_name passed${NC}"
        tests_passed=$((tests_passed + 1))
    else
        echo -e "${RED}❌ $test_name failed${NC}"
        tests_failed=$((tests_failed + 1))
    fi
    echo ""
}

setup_test_data() {
    echo "🏗️  Setting up test data..."
    
    # Create test region
    PGPASSWORD=ni_password psql -h localhost -U ni -d ni -c "
        INSERT INTO regions (lamas_code, name_he, name_en, geom) 
        VALUES (
            'TEST_REGION_001', 
            'תל אביב צפון', 
            'Tel Aviv North',
            ST_GeomFromText('POLYGON((34.7 32.0, 34.8 32.0, 34.8 32.1, 34.7 32.1, 34.7 32.0))', 4326)
        ) ON CONFLICT (lamas_code) DO NOTHING;
    " > /dev/null 2>&1
    
    # Get region ID for further tests
    TEST_REGION_ID=$(PGPASSWORD=ni_password psql -h localhost -U ni -d ni -t -c "
        SELECT region_id FROM regions WHERE lamas_code = 'TEST_REGION_001';
    " | tr -d ' ')
    
    setup_cleanup_needed=true
    echo "✅ Test data setup complete (region_id: $TEST_REGION_ID)"
}

cleanup_test_data() {
    if [ "$setup_cleanup_needed" = true ]; then
        echo "🧹 Cleaning up test data..."
        
        PGPASSWORD=ni_password psql -h localhost -U ni -d ni -c "
            DELETE FROM demographics WHERE region_id IN (SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%');
            DELETE FROM centroids WHERE region_id IN (SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%');
            DELETE FROM schools WHERE region_id IN (SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%');
            DELETE FROM scores_components WHERE region_id IN (SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%');
            DELETE FROM scores_neighborhood WHERE region_id IN (SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%');
            DELETE FROM regions WHERE lamas_code LIKE 'TEST_%';
        " > /dev/null 2>&1
        
        echo "✅ Test data cleanup complete"
    fi
}

# Trap to ensure cleanup happens
trap cleanup_test_data EXIT

# Test 1: Database → API Integration
test_database_api_integration() {
    echo "  Testing database to API data flow..."
    
    # Ensure API is running (start if needed)
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ⚠️  API not running, skipping API integration test"
        return 1
    fi
    
    # Test health endpoint can reach database
    local response=$(curl -s http://localhost:8000/health)
    if echo "$response" | grep -q '"ok":true'; then
        echo "  ✅ API can connect to database"
        return 0
    else
        echo "  ❌ API cannot connect to database"
        return 1
    fi
}

# Test 2: Spatial Data Workflow
test_spatial_data_workflow() {
    echo "  Testing complete spatial data workflow..."
    
    # 1. Insert region with geometry
    local test_lamas="TEST_SPATIAL_$(date +%s)"
    PGPASSWORD=ni_password psql -h localhost -U ni -d ni -c "
        INSERT INTO regions (lamas_code, name_he, geom) 
        VALUES ('$test_lamas', 'Test Spatial', 
                ST_GeomFromText('POLYGON((34.75 32.05, 34.76 32.05, 34.76 32.06, 34.75 32.06, 34.75 32.05))', 4326));
    " > /dev/null 2>&1 || return 1
    
    # 2. Generate centroid
    PGPASSWORD=ni_password psql -h localhost -U ni -d ni -c "
        INSERT INTO centroids (region_id, geom)
        SELECT region_id, ST_Centroid(geom) 
        FROM regions WHERE lamas_code = '$test_lamas';
    " > /dev/null 2>&1 || return 1
    
    # 3. Test spatial queries work
    local point_in_polygon=$(PGPASSWORD=ni_password psql -h localhost -U ni -d ni -t -c "
        SELECT COUNT(*) FROM regions 
        WHERE ST_Contains(geom, ST_Point(34.755, 32.055)) 
        AND lamas_code = '$test_lamas';
    " | tr -d ' ')
    
    # 4. Test distance calculation
    local distance=$(PGPASSWORD=ni_password psql -h localhost -U ni -d ni -t -c "
        SELECT ST_Distance(
            (SELECT geom FROM centroids WHERE region_id = (SELECT region_id FROM regions WHERE lamas_code = '$test_lamas')),
            ST_Point(34.7818, 32.0853)
        );
    " | tr -d ' ')
    
    # Cleanup
    PGPASSWORD=ni_password psql -h localhost -U ni -d ni -c "
        DELETE FROM centroids WHERE region_id IN (SELECT region_id FROM regions WHERE lamas_code = '$test_lamas');
        DELETE FROM regions WHERE lamas_code = '$test_lamas';
    " > /dev/null 2>&1
    
    # Validate results
    if [ "$point_in_polygon" = "1" ] && [ ! -z "$distance" ]; then
        echo "  ✅ Spatial workflow: insert → centroid → spatial queries"
        return 0
    else
        echo "  ❌ Spatial workflow failed (point_in_polygon: $point_in_polygon, distance: $distance)"
        return 1
    fi
}

# Test 3: Data Relationships and Foreign Keys
test_data_relationships() {
    echo "  Testing data relationships and foreign keys..."
    
    # Create test region
    local test_lamas="TEST_FK_$(date +%s)"
    PGPASSWORD=ni_password psql -h localhost -U ni -d ni -c "
        INSERT INTO regions (lamas_code, name_he, geom) 
        VALUES ('$test_lamas', 'Test FK', 
                ST_GeomFromText('POLYGON((34.7 32.0, 34.8 32.0, 34.8 32.1, 34.7 32.1, 34.7 32.0))', 4326));
    " > /dev/null 2>&1 || return 1
    
    # Get region ID
    local region_id=$(PGPASSWORD=ni_password psql -h localhost -U ni -d ni -t -c "
        SELECT region_id FROM regions WHERE lamas_code = '$test_lamas';
    " | tr -d ' ')
    
    # Test foreign key relationships
    PGPASSWORD=ni_password psql -h localhost -U ni -d ni -c "
        INSERT INTO demographics (region_id, pop_total, se_index_overall) 
        VALUES ($region_id, 5000, 12.5);
        
        INSERT INTO centroids (region_id, geom) 
        VALUES ($region_id, ST_Point(34.75, 32.05));
        
        INSERT INTO scores_components (region_id, z_education, z_crime) 
        VALUES ($region_id, 1.2, -0.5);
        
        INSERT INTO scores_neighborhood (region_id, score_0_100) 
        VALUES ($region_id, 75);
    " > /dev/null 2>&1 || return 1
    
    # Test cascade delete
    PGPASSWORD=ni_password psql -h localhost -U ni -d ni -c "
        DELETE FROM regions WHERE lamas_code = '$test_lamas';
    " > /dev/null 2>&1 || return 1
    
    # Verify cascaded deletions
    local remaining_records=$(PGPASSWORD=ni_password psql -h localhost -U ni -d ni -t -c "
        SELECT 
            (SELECT COUNT(*) FROM demographics WHERE region_id = $region_id) +
            (SELECT COUNT(*) FROM centroids WHERE region_id = $region_id) +
            (SELECT COUNT(*) FROM scores_components WHERE region_id = $region_id) +
            (SELECT COUNT(*) FROM scores_neighborhood WHERE region_id = $region_id);
    " | tr -d ' ')
    
    if [ "$remaining_records" = "0" ]; then
        echo "  ✅ Foreign key relationships and cascade deletes work"
        return 0
    else
        echo "  ❌ Foreign key cascade failed ($remaining_records records remain)"
        return 1
    fi
}

# Test 4: Scoring System Integration
test_scoring_system() {
    echo "  Testing neighborhood scoring system integration..."
    
    setup_test_data
    
    # Add component data
    PGPASSWORD=ni_password psql -h localhost -U ni -d ni -c "
        INSERT INTO demographics (region_id, pop_total, se_index_overall) 
        VALUES ($TEST_REGION_ID, 8000, 15.2);
        
        INSERT INTO scores_components (region_id, z_education, z_crime, z_services, z_transit, z_housing, z_demographics) 
        VALUES ($TEST_REGION_ID, 1.5, -0.3, 0.8, 0.2, -0.5, 1.2);
    " > /dev/null 2>&1 || return 1
    
    # Calculate composite score (simplified version)
    local composite_score=$(PGPASSWORD=ni_password psql -h localhost -U ni -d ni -t -c "
        WITH score_calc AS (
            SELECT 
                region_id,
                -- Simple weighted average scaled to 0-100
                ROUND(50 + (
                    (COALESCE(z_education, 0) * 0.25 + 
                     COALESCE(z_crime, 0) * 0.20 + 
                     COALESCE(z_services, 0) * 0.20 + 
                     COALESCE(z_transit, 0) * 0.15 + 
                     COALESCE(z_housing, 0) * 0.20) * 10
                ))::INTEGER as calculated_score
            FROM scores_components 
            WHERE region_id = $TEST_REGION_ID
        )
        SELECT calculated_score FROM score_calc;
    " | tr -d ' ')
    
    # Insert calculated score
    PGPASSWORD=ni_password psql -h localhost -U ni -d ni -c "
        INSERT INTO scores_neighborhood (region_id, score_0_100, weights_used) 
        VALUES ($TEST_REGION_ID, $composite_score, '{\"education\": 0.25, \"crime\": 0.20, \"services\": 0.20, \"transit\": 0.15, \"housing\": 0.20}');
    " > /dev/null 2>&1 || return 1
    
    # Test the view works
    local view_result=$(PGPASSWORD=ni_password psql -h localhost -U ni -d ni -t -c "
        SELECT score_0_100 FROM regions_with_scores WHERE region_id = $TEST_REGION_ID;
    " | tr -d ' ')
    
    if [ "$view_result" = "$composite_score" ] && [ "$composite_score" -ge "0" ] && [ "$composite_score" -le "100" ]; then
        echo "  ✅ Scoring system: components → composite → view ($composite_score/100)"
        return 0
    else
        echo "  ❌ Scoring system failed (view: $view_result, calculated: $composite_score)"
        return 1
    fi
}

# Test 5: Cache System
test_cache_system() {
    echo "  Testing cache system functionality..."
    
    # Test Redis connectivity
    if ! docker exec ni-redis redis-cli ping > /dev/null 2>&1; then
        echo "  ⚠️  Redis not available, skipping cache test"
        return 1
    fi
    
    # Test cache table and cleanup function
    PGPASSWORD=ni_password psql -h localhost -U ni -d ni -c "
        INSERT INTO commute_cache_short (cache_key, origin_region_id, destination_coords, mode, depart_time_bucket, duration_seconds, expires_at)
        VALUES ('test_cache_key', 1, ST_Point(34.7818, 32.0853), 'driving', NOW(), 1200, NOW() - INTERVAL '1 hour');
    " > /dev/null 2>&1 || return 1
    
    # Test cleanup function
    local cleaned_count=$(PGPASSWORD=ni_password psql -h localhost -U ni -d ni -t -c "
        SELECT cleanup_expired_cache();
    " | tr -d ' ')
    
    # Verify cleanup worked
    local remaining_expired=$(PGPASSWORD=ni_password psql -h localhost -U ni -d ni -t -c "
        SELECT COUNT(*) FROM commute_cache_short WHERE expires_at < NOW();
    " | tr -d ' ')
    
    if [ "$remaining_expired" = "0" ] && [ "$cleaned_count" -ge "1" ]; then
        echo "  ✅ Cache system: insert → cleanup → verification ($cleaned_count cleaned)"
        return 0
    else
        echo "  ❌ Cache system failed (remaining: $remaining_expired, cleaned: $cleaned_count)"
        return 1
    fi
}

# Test 6: Migration System
test_migration_system() {
    echo "  Testing migration system functionality..."
    
    # Test migration functions
    local current_version=$(PGPASSWORD=ni_password psql -h localhost -U ni -d ni -t -c "
        SELECT get_current_schema_version();
    " | tr -d ' ')
    
    # Test migration status view
    local migration_count=$(PGPASSWORD=ni_password psql -h localhost -U ni -d ni -t -c "
        SELECT COUNT(*) FROM migration_status;
    " | tr -d ' ')
    
    if [ ! -z "$current_version" ] && [ "$migration_count" -ge "0" ]; then
        echo "  ✅ Migration system: version tracking functional (version: $current_version)"
        return 0
    else
        echo "  ❌ Migration system failed (version: $current_version, count: $migration_count)"
        return 1
    fi
}

# Run all integration tests
echo "🚀 Starting integration tests..."
echo ""

# Ensure required services are running
if ! docker exec ni-postgres pg_isready -U ni -d ni > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL is not ready${NC}"
    exit 1
fi

# Run integration tests
run_integration_test "Database → API Integration" test_database_api_integration
run_integration_test "Spatial Data Workflow" test_spatial_data_workflow  
run_integration_test "Data Relationships & Foreign Keys" test_data_relationships
run_integration_test "Scoring System Integration" test_scoring_system
run_integration_test "Cache System" test_cache_system
run_integration_test "Migration System" test_migration_system

# Summary
echo "📋 Integration Test Summary"
total_tests=$((tests_passed + tests_failed))
echo "Total tests: $total_tests"
echo -e "Passed: ${GREEN}$tests_passed${NC}"
echo -e "Failed: ${RED}$tests_failed${NC}"

if [ $tests_failed -eq 0 ]; then
    echo -e "${GREEN}🎉 All integration tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $tests_failed integration test(s) failed${NC}"
    exit 1
fi