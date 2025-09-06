"""
Database Operations Tests for ETL
"""
import pytest
import os
import psycopg
from unittest.mock import patch
import tempfile

class TestDatabaseSchema:
    """Test database schema and structure"""
    
    @pytest.mark.integration
    def test_all_tables_exist(self, db_connection):
        """Test that all required tables exist"""
        expected_tables = [
            "regions", "neighborhoods_canonical", "centroids",
            "demographics", "schools", "crime", "health_facilities",
            "poi_osm", "stops", "deals", "scores_components", 
            "scores_neighborhood", "commute_cache_short", "schema_migrations"
        ]
        
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            existing_tables = [row[0] for row in cur.fetchall()]
        
        for table in expected_tables:
            assert table in existing_tables, f"Table {table} is missing"
    
    @pytest.mark.integration 
    def test_spatial_indices_exist(self, db_connection):
        """Test that spatial indices are created"""
        expected_indices = [
            "regions_geom_gix", "schools_geom_gix", "poi_osm_geom_gix",
            "stops_geom_gix", "deals_geom_gix"
        ]
        
        with db_connection.cursor() as cur:
            cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
            existing_indices = [row[0] for row in cur.fetchall()]
        
        for index in expected_indices:
            assert index in existing_indices, f"Spatial index {index} is missing"
    
    @pytest.mark.integration
    def test_postgis_extensions_loaded(self, db_connection):
        """Test that PostGIS extensions are loaded"""
        with db_connection.cursor() as cur:
            cur.execute("SELECT PostGIS_Version()")
            version = cur.fetchone()[0]
            assert version is not None
            assert "3.4" in version  # Expected PostGIS version

class TestSpatialOperations:
    """Test spatial data operations"""
    
    @pytest.mark.integration
    def test_geometry_creation_and_validation(self, db_connection):
        """Test creating and validating geometry objects"""
        with db_connection.cursor() as cur:
            # Test point creation
            cur.execute("SELECT ST_AsText(ST_Point(34.7818, 32.0853))")
            point = cur.fetchone()[0]
            assert "POINT(34.7818 32.0853)" == point
            
            # Test polygon creation and area calculation
            cur.execute("""
                SELECT ST_Area(ST_GeomFromText(
                    'POLYGON((34.7 32.0, 34.8 32.0, 34.8 32.1, 34.7 32.1, 34.7 32.0))', 
                    4326
                ))
            """)
            area = cur.fetchone()[0]
            assert area > 0
    
    @pytest.mark.integration
    def test_spatial_containment(self, db_connection, test_region):
        """Test spatial containment queries"""
        with db_connection.cursor() as cur:
            # Insert test region
            cur.execute("""
                INSERT INTO regions (lamas_code, name_he, geom) 
                VALUES (%s, %s, ST_GeomFromText(%s, 4326))
                ON CONFLICT (lamas_code) DO UPDATE SET geom = EXCLUDED.geom
            """, (test_region["lamas_code"], test_region["name_he"], test_region["geom"]))
            
            # Test point in polygon
            cur.execute("""
                SELECT COUNT(*) FROM regions 
                WHERE ST_Contains(geom, ST_Point(34.75, 32.05)) 
                AND lamas_code = %s
            """, (test_region["lamas_code"],))
            
            count = cur.fetchone()[0]
            assert count == 1

class TestDataRelationships:
    """Test foreign key relationships and data integrity"""
    
    @pytest.mark.integration
    def test_foreign_key_constraints(self, db_connection, test_region):
        """Test that foreign key constraints work properly"""
        with db_connection.cursor() as cur:
            # Insert test region
            cur.execute("""
                INSERT INTO regions (lamas_code, name_he, geom) 
                VALUES (%s, %s, ST_GeomFromText(%s, 4326))
                ON CONFLICT (lamas_code) DO NOTHING
                RETURNING region_id
            """, (test_region["lamas_code"], test_region["name_he"], test_region["geom"]))
            
            result = cur.fetchone()
            if result:
                region_id = result[0]
            else:
                cur.execute("SELECT region_id FROM regions WHERE lamas_code = %s", 
                          (test_region["lamas_code"],))
                region_id = cur.fetchone()[0]
            
            # Insert dependent records
            cur.execute("INSERT INTO demographics (region_id, pop_total) VALUES (%s, %s)", 
                       (region_id, 5000))
            cur.execute("INSERT INTO centroids (region_id, geom) VALUES (%s, ST_Point(34.75, 32.05))", 
                       (region_id,))
            
            # Verify records exist
            cur.execute("SELECT COUNT(*) FROM demographics WHERE region_id = %s", (region_id,))
            assert cur.fetchone()[0] == 1
            
            cur.execute("SELECT COUNT(*) FROM centroids WHERE region_id = %s", (region_id,))
            assert cur.fetchone()[0] == 1

class TestEnumTypes:
    """Test custom ENUM types"""
    
    @pytest.mark.integration
    def test_transport_mode_enum(self, db_connection):
        """Test transport_mode enum values"""
        with db_connection.cursor() as cur:
            # Test valid enum values
            valid_modes = ['driving', 'driving_traffic', 'transit', 'bicycling', 'walking']
            for mode in valid_modes:
                cur.execute("SELECT %s::transport_mode", (mode,))
                result = cur.fetchone()[0]
                assert result == mode
    
    @pytest.mark.integration
    def test_poi_category_enum(self, db_connection):
        """Test poi_category enum values"""
        with db_connection.cursor() as cur:
            valid_categories = [
                'supermarket', 'pharmacy', 'clinic', 'hospital', 
                'school', 'kindergarten', 'park', 'community_center'
            ]
            for category in valid_categories:
                cur.execute("SELECT %s::poi_category", (category,))
                result = cur.fetchone()[0]
                assert result == category

class TestMigrationSystem:
    """Test database migration system"""
    
    @pytest.mark.integration
    def test_migration_table_exists(self, db_connection):
        """Test that migration tracking table exists"""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'schema_migrations'
            """)
            assert cur.fetchone()[0] == 1
    
    @pytest.mark.integration
    def test_migration_functions_exist(self, db_connection):
        """Test that migration functions exist"""
        with db_connection.cursor() as cur:
            # Test get_current_schema_version function
            cur.execute("SELECT get_current_schema_version()")
            version = cur.fetchone()[0]
            # Should return a version or None
            assert version is None or isinstance(version, str)
    
    @pytest.mark.integration
    def test_cleanup_expired_cache_function(self, db_connection):
        """Test cache cleanup function"""
        with db_connection.cursor() as cur:
            cur.execute("SELECT cleanup_expired_cache()")
            cleaned_count = cur.fetchone()[0]
            assert isinstance(cleaned_count, int)
            assert cleaned_count >= 0