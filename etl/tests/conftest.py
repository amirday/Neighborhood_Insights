"""
Pytest configuration and fixtures for ETL tests
"""
import pytest
import os
import psycopg

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

@pytest.fixture
def test_region():
    """Test region data for database operations"""
    return {
        "lamas_code": "TEST_ETL_001",
        "name_he": "אזור בדיקה ETL",
        "name_en": "ETL Test Region",
        "geom": "POLYGON((34.7 32.0, 34.8 32.0, 34.8 32.1, 34.7 32.1, 34.7 32.0))"
    }

@pytest.fixture(autouse=True)
def cleanup_test_data(db_connection):
    """Automatically clean up test data after each test"""
    yield
    # Cleanup test data
    try:
        with db_connection.cursor() as cur:
            cur.execute("""
                DELETE FROM demographics WHERE region_id IN (
                    SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%'
                );
                DELETE FROM centroids WHERE region_id IN (
                    SELECT region_id FROM regions WHERE lamas_code LIKE 'TEST_%'
                );
                DELETE FROM regions WHERE lamas_code LIKE 'TEST_%';
            """)
        db_connection.commit()
    except Exception:
        pass  # Ignore cleanup errors

def pytest_configure(config):
    """Pytest configuration"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests requiring database"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )