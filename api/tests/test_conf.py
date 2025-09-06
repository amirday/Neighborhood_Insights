"""
Pytest configuration and fixtures for API tests
"""
import pytest
import os
import psycopg
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    """FastAPI test client fixture"""
    return TestClient(app)

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
def test_region_data():
    """Test data for regions"""
    return {
        "lamas_code": "TEST_API_001",
        "name_he": "אזור בדיקה",
        "name_en": "Test Region",
        "geom": "POLYGON((34.7 32.0, 34.8 32.0, 34.8 32.1, 34.7 32.1, 34.7 32.0))"
    }

def pytest_configure(config):
    """Pytest configuration"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )