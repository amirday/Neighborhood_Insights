"""
End-to-End Integration Tests
Tests complete user workflows from API to database
"""
import pytest
import psycopg
import requests
import os
import json
import subprocess
from datetime import datetime
from typing import Dict, Any


class TestDatabaseApiIntegration:
    """Test database to API integration"""
    
    @pytest.mark.integration
    def test_api_can_connect_to_database(self, db_connection):
        """Test that API can connect to database via health endpoint"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            health_data = response.json()
            assert health_data.get("ok") is True
            assert response.status_code == 200
        except requests.ConnectionError:
            pytest.skip("API not running, skipping API integration test")


class TestSpatialDataWorkflow:
    """Test complete spatial data workflow"""
    
    @pytest.mark.integration
    def test_spatial_data_complete_workflow(self, db_connection):
        """Test insert region → generate centroid → spatial queries"""
        test_lamas = f"TEST_SPATIAL_{int(datetime.now().timestamp())}"
        
        with db_connection.cursor() as cur:
            try:
                # 1. Insert region with geometry
                cur.execute("""
                    INSERT INTO regions (lamas_code, name_he, geom) 
                    VALUES (%s, %s, ST_GeomFromText(%s, 4326))
                """, (test_lamas, "Test Spatial", 
                     "POLYGON((34.75 32.05, 34.76 32.05, 34.76 32.06, 34.75 32.06, 34.75 32.05))"))
                
                # 2. Generate centroid
                cur.execute("""
                    INSERT INTO centroids (region_id, geom)
                    SELECT region_id, ST_Centroid(geom) 
                    FROM regions WHERE lamas_code = %s
                """, (test_lamas,))
                
                # 3. Test spatial queries work - point in polygon
                cur.execute("""
                    SELECT COUNT(*) FROM regions 
                    WHERE ST_Contains(geom, ST_Point(34.755, 32.055)) 
                    AND lamas_code = %s
                """, (test_lamas,))
                point_in_polygon = cur.fetchone()[0]
                
                # 4. Test distance calculation
                cur.execute("""
                    SELECT ST_Distance(
                        (SELECT geom FROM centroids WHERE region_id = (
                            SELECT region_id FROM regions WHERE lamas_code = %s
                        )),
                        ST_Point(34.7818, 32.0853)
                    )
                """, (test_lamas,))
                distance = cur.fetchone()[0]
                
                # Validate results
                assert point_in_polygon == 1, f"Point should be in polygon, got {point_in_polygon}"
                assert distance is not None and distance > 0, f"Distance calculation failed: {distance}"
                
            finally:
                # Cleanup
                cur.execute("""
                    DELETE FROM centroids WHERE region_id IN (
                        SELECT region_id FROM regions WHERE lamas_code = %s
                    )
                """, (test_lamas,))
                cur.execute("DELETE FROM regions WHERE lamas_code = %s", (test_lamas,))


class TestDataRelationships:
    """Test data relationships and foreign keys"""
    
    @pytest.mark.integration
    def test_foreign_key_relationships_and_cascade(self, db_connection):
        """Test foreign key relationships and cascade deletes"""
        test_lamas = f"TEST_FK_{int(datetime.now().timestamp())}"
        
        with db_connection.cursor() as cur:
            # Create test region
            cur.execute("""
                INSERT INTO regions (lamas_code, name_he, geom) 
                VALUES (%s, %s, ST_GeomFromText(%s, 4326))
                RETURNING region_id
            """, (test_lamas, "Test FK", 
                 "POLYGON((34.7 32.0, 34.8 32.0, 34.8 32.1, 34.7 32.1, 34.7 32.0))"))
            
            region_id = cur.fetchone()[0]
            
            # Test foreign key relationships - insert dependent records
            cur.execute("""
                INSERT INTO demographics (region_id, pop_total, se_index_overall) 
                VALUES (%s, %s, %s)
            """, (region_id, 5000, 12.5))
            
            cur.execute("""
                INSERT INTO centroids (region_id, geom) 
                VALUES (%s, ST_Point(34.75, 32.05))
            """, (region_id,))
            
            cur.execute("""
                INSERT INTO scores_components (region_id, z_education, z_crime) 
                VALUES (%s, %s, %s)
            """, (region_id, 1.2, -0.5))
            
            cur.execute("""
                INSERT INTO scores_neighborhood (region_id, score_0_100) 
                VALUES (%s, %s)
            """, (region_id, 75))
            
            # Test cascade delete
            cur.execute("DELETE FROM regions WHERE lamas_code = %s", (test_lamas,))
            
            # Verify cascaded deletions
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM demographics WHERE region_id = %s) +
                    (SELECT COUNT(*) FROM centroids WHERE region_id = %s) +
                    (SELECT COUNT(*) FROM scores_components WHERE region_id = %s) +
                    (SELECT COUNT(*) FROM scores_neighborhood WHERE region_id = %s)
            """, (region_id, region_id, region_id, region_id))
            
            remaining_records = cur.fetchone()[0]
            assert remaining_records == 0, f"Cascade delete failed, {remaining_records} records remain"


class TestScoringSystemIntegration:
    """Test neighborhood scoring system integration"""
    
    @pytest.mark.integration
    def test_scoring_system_workflow(self, db_connection, test_region_with_cleanup):
        """Test component scores → composite score → view integration"""
        region_id, test_lamas = test_region_with_cleanup
        
        with db_connection.cursor() as cur:
            # Add component data
            cur.execute("""
                INSERT INTO demographics (region_id, pop_total, se_index_overall) 
                VALUES (%s, %s, %s)
            """, (region_id, 8000, 15.2))
            
            cur.execute("""
                INSERT INTO scores_components (
                    region_id, z_education, z_crime, z_services, 
                    z_transit, z_housing, z_demographics
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (region_id, 1.5, -0.3, 0.8, 0.2, -0.5, 1.2))
            
            # Calculate composite score (simplified version)
            cur.execute("""
                WITH score_calc AS (
                    SELECT 
                        region_id,
                        ROUND(50 + (
                            (COALESCE(z_education, 0) * 0.25 + 
                             COALESCE(z_crime, 0) * 0.20 + 
                             COALESCE(z_services, 0) * 0.20 + 
                             COALESCE(z_transit, 0) * 0.15 + 
                             COALESCE(z_housing, 0) * 0.20) * 10
                        ))::INTEGER as calculated_score
                    FROM scores_components 
                    WHERE region_id = %s
                )
                SELECT calculated_score FROM score_calc
            """, (region_id,))
            
            composite_score = cur.fetchone()[0]
            
            # Insert calculated score
            weights_json = json.dumps({
                "education": 0.25, "crime": 0.20, "services": 0.20, 
                "transit": 0.15, "housing": 0.20
            })
            
            cur.execute("""
                INSERT INTO scores_neighborhood (region_id, score_0_100, weights_used) 
                VALUES (%s, %s, %s)
            """, (region_id, composite_score, weights_json))
            
            # Test the view works
            cur.execute("""
                SELECT score_0_100 FROM regions_with_scores WHERE region_id = %s
            """, (region_id,))
            
            view_result = cur.fetchone()[0]
            
            assert view_result == composite_score, f"View result {view_result} != calculated {composite_score}"
            assert 0 <= composite_score <= 100, f"Score {composite_score} not in valid range 0-100"


class TestCacheSystem:
    """Test cache system functionality"""
    
    @pytest.mark.integration
    def test_redis_cache_system(self, db_connection):
        """Test Redis connectivity and cache table cleanup function"""
        # Test Redis connectivity
        try:
            result = subprocess.run(
                ["docker", "exec", "ni-redis", "redis-cli", "ping"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                pytest.skip("Redis not available, skipping cache test")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Redis not available, skipping cache test")
        
        with db_connection.cursor() as cur:
            # Test cache table and cleanup function
            cur.execute("""
                INSERT INTO commute_cache_short (
                    cache_key, origin_region_id, destination_coords, 
                    mode, depart_time_bucket, duration_seconds, expires_at
                )
                VALUES (%s, %s, ST_Point(34.7818, 32.0853), %s, NOW(), %s, NOW() - INTERVAL '1 hour')
            """, ("test_cache_key", 1, "driving", 1200))
            
            # Test cleanup function
            cur.execute("SELECT cleanup_expired_cache()")
            cleaned_count = cur.fetchone()[0]
            
            # Verify cleanup worked
            cur.execute("SELECT COUNT(*) FROM commute_cache_short WHERE expires_at < NOW()")
            remaining_expired = cur.fetchone()[0]
            
            assert remaining_expired == 0, f"Cache cleanup failed, {remaining_expired} expired records remain"
            assert cleaned_count >= 1, f"Expected to clean at least 1 record, cleaned {cleaned_count}"


class TestMigrationSystem:
    """Test migration system functionality"""
    
    @pytest.mark.integration
    def test_migration_system_functions(self, db_connection):
        """Test migration functions and version tracking"""
        with db_connection.cursor() as cur:
            # Test migration functions
            cur.execute("SELECT get_current_schema_version()")
            current_version = cur.fetchone()[0]
            
            # Test migration status view
            cur.execute("SELECT COUNT(*) FROM migration_status")
            migration_count = cur.fetchone()[0]
            
            # Version should be string or None, and migration count should be non-negative
            assert current_version is None or isinstance(current_version, str), \
                f"Invalid version type: {type(current_version)}"
            assert migration_count >= 0, f"Invalid migration count: {migration_count}"


@pytest.fixture
def test_region_with_cleanup(db_connection):
    """Create a test region and return its ID, with automatic cleanup"""
    test_lamas = f"TEST_REGION_{int(datetime.now().timestamp())}"
    
    with db_connection.cursor() as cur:
        cur.execute("""
            INSERT INTO regions (lamas_code, name_he, name_en, geom) 
            VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326))
            RETURNING region_id
        """, (test_lamas, "תל אביב צפון", "Tel Aviv North",
             "POLYGON((34.7 32.0, 34.8 32.0, 34.8 32.1, 34.7 32.1, 34.7 32.0))"))
        
        region_id = cur.fetchone()[0]
    
    yield region_id, test_lamas
    
    # Cleanup
    with db_connection.cursor() as cur:
        cur.execute("""
            DELETE FROM demographics WHERE region_id IN (SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%');
            DELETE FROM centroids WHERE region_id IN (SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%');
            DELETE FROM schools WHERE region_id IN (SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%');
            DELETE FROM scores_components WHERE region_id IN (SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%');
            DELETE FROM scores_neighborhood WHERE region_id IN (SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%');
            DELETE FROM regions WHERE lamas_code LIKE 'TEST_%';
        """)


@pytest.fixture(scope="session")
def db_connection():
    """Database connection fixture for integration tests"""
    try:
        conn = psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            user=os.getenv("POSTGRES_USER", "ni"),
            password=os.getenv("POSTGRES_PASSWORD", "ni_password"),
            dbname=os.getenv("POSTGRES_DB", "ni"),
        )
        yield conn
        conn.close()
    except psycopg.OperationalError:
        pytest.skip("Database not available for integration tests")


def pytest_configure(config):
    """Pytest configuration"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests requiring database"
    )