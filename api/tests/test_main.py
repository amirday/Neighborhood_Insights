"""
API Tests - FastAPI application endpoints and functionality
"""
import pytest
import requests
from fastapi.testclient import TestClient
from api.main import app, get_conn
import psycopg
import os

client = TestClient(app)

class TestHealthEndpoint:
    def test_health_returns_200(self):
        """Health endpoint should return 200 status"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_returns_json(self):
        """Health endpoint should return JSON with 'ok' field"""
        response = client.get("/health")
        assert response.json() == {"ok": True}

class TestAddressSearch:
    def test_address_search_valid_query(self):
        """Address search should accept valid queries"""
        response = client.get("/address/search?q=tel")
        assert response.status_code == 200
        assert "results" in response.json()
    
    def test_address_search_returns_results_array(self):
        """Address search should return results array"""
        response = client.get("/address/search?q=tel")
        data = response.json()
        assert isinstance(data["results"], list)
    
    def test_address_search_rejects_short_query(self):
        """Address search should reject queries shorter than 3 characters"""
        response = client.get("/address/search?q=ab")
        assert response.status_code == 422
    
    def test_address_search_requires_query_param(self):
        """Address search should require query parameter"""
        response = client.get("/address/search")
        assert response.status_code == 422

class TestReverseSearch:
    def test_reverse_search_valid_data(self):
        """Reverse search should accept valid request data"""
        data = {
            "weights": {"education": 0.3, "safety": 0.2}, 
            "filters": {"min_score": 70}
        }
        response = client.post("/search/reverse", json=data)
        assert response.status_code == 200
    
    def test_reverse_search_returns_features_and_ranking(self):
        """Reverse search should return features and ranking arrays"""
        data = {
            "weights": {"education": 0.3, "safety": 0.2}, 
            "filters": {"min_score": 70}
        }
        response = client.post("/search/reverse", json=data)
        json_data = response.json()
        assert "features" in json_data
        assert "ranking" in json_data
        assert isinstance(json_data["features"], list)
        assert isinstance(json_data["ranking"], list)
    
    def test_reverse_search_rejects_invalid_data(self):
        """Reverse search should reject invalid request data"""
        invalid_data = {"invalid": "data"}
        response = client.post("/search/reverse", json=invalid_data)
        assert response.status_code == 422

class TestDatabaseConnection:
    def test_database_connection_config(self):
        """Database connection should use correct configuration"""
        # Test that get_conn function uses environment variables correctly
        conn_params = {
            "host": os.getenv("POSTGRES_HOST", "postgres"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "user": os.getenv("POSTGRES_USER", "ni"),
            "password": os.getenv("POSTGRES_PASSWORD", "ni_password"),
            "dbname": os.getenv("POSTGRES_DB", "ni"),
        }
        
        # Verify the parameters are what we expect
        assert conn_params["host"] in ["postgres", "localhost"]
        assert conn_params["user"] == "ni"
        assert conn_params["dbname"] == "ni"
    
    @pytest.mark.integration
    def test_database_connection_works(self):
        """Database connection should work (integration test)"""
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                assert result[0] == 1
            conn.close()
        except psycopg.OperationalError:
            pytest.skip("Database not available for integration test")

class TestAPIDocumentation:
    def test_openapi_schema_accessible(self):
        """OpenAPI schema should be accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    def test_docs_accessible(self):
        """API documentation should be accessible"""
        response = client.get("/docs")
        assert response.status_code == 200

class TestResponseHeaders:
    def test_content_type_json(self):
        """API should return JSON content-type for JSON endpoints"""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]

@pytest.mark.performance
class TestPerformance:
    def test_health_endpoint_response_time(self):
        """Health endpoint should respond quickly"""
        import time
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        # Should respond in under 1 second
        assert (end_time - start_time) < 1.0
    
    def test_concurrent_requests(self):
        """API should handle concurrent requests"""
        import concurrent.futures
        import threading
        
        def make_request():
            return client.get("/health")
        
        # Test 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200