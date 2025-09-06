"""
System Health Tests - End-to-End
Tests that the entire system is healthy and operational
"""
import pytest
import subprocess
import socket
import psycopg
import os
import json
from typing import Dict, List, Tuple


class TestInfrastructureHealth:
    """Test infrastructure components health"""
    
    def test_docker_system_operational(self):
        """Test that Docker system is available"""
        try:
            result = subprocess.run(
                ["docker", "info"], 
                capture_output=True, text=True, timeout=10
            )
            assert result.returncode == 0, "Docker system is not available"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.fail("Docker system is not available")
    
    @pytest.mark.parametrize("container_name,description", [
        ("ni-postgres", "PostgreSQL database"),
        ("ni-redis", "Redis cache"),
    ])
    def test_required_services_running(self, container_name: str, description: str):
        """Test that required services are running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True, text=True, timeout=5
            )
            assert result.returncode == 0, f"Failed to check docker containers"
            
            running_containers = result.stdout.strip().split('\n')
            assert container_name in running_containers, f"{description} ({container_name}) is not running"
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.fail(f"Cannot check {description} status")


class TestDataLayerHealth:
    """Test data layer health"""
    
    def test_database_accepting_connections(self):
        """Test database is accepting connections"""
        try:
            result = subprocess.run(
                ["docker", "exec", "ni-postgres", "pg_isready", "-U", "ni", "-d", "ni"],
                capture_output=True, text=True, timeout=10
            )
            assert result.returncode == 0, "Database is not accepting connections"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.fail("Cannot check database connection status")
    
    def test_database_queries_working(self):
        """Test database queries are working"""
        try:
            result = subprocess.run(
                ["docker", "exec", "ni-postgres", "psql", "-U", "ni", "-d", "ni", 
                 "-c", "SELECT COUNT(*) FROM regions;"],
                capture_output=True, text=True, timeout=10
            )
            assert result.returncode == 0, "Database queries are not working"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.fail("Cannot execute database queries")
    
    def test_postgis_extension_operational(self):
        """Test PostGIS extension is operational"""
        try:
            result = subprocess.run(
                ["docker", "exec", "ni-postgres", "psql", "-U", "ni", "-d", "ni",
                 "-c", "SELECT PostGIS_Version();"],
                capture_output=True, text=True, timeout=10
            )
            assert result.returncode == 0, "PostGIS extension is not operational"
            assert "3.4" in result.stdout, "Expected PostGIS version not found"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.fail("Cannot check PostGIS extension")


class TestCacheLayerHealth:
    """Test cache layer health"""
    
    def test_redis_responding(self):
        """Test Redis cache is responding"""
        try:
            result = subprocess.run(
                ["docker", "exec", "ni-redis", "redis-cli", "ping"],
                capture_output=True, text=True, timeout=5
            )
            assert result.returncode == 0, "Redis cache is not responding"
            assert "PONG" in result.stdout, "Redis did not respond with PONG"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.fail("Cannot check Redis status")
    
    def test_redis_read_write_operations(self):
        """Test Redis read/write operations"""
        test_key = "system_test_key"
        test_value = "test_value"
        
        try:
            # Set value
            result = subprocess.run(
                ["docker", "exec", "ni-redis", "redis-cli", "set", test_key, test_value],
                capture_output=True, text=True, timeout=5
            )
            assert result.returncode == 0, "Redis SET operation failed"
            
            # Get value
            result = subprocess.run(
                ["docker", "exec", "ni-redis", "redis-cli", "get", test_key],
                capture_output=True, text=True, timeout=5
            )
            assert result.returncode == 0, "Redis GET operation failed"
            assert test_value in result.stdout, "Redis did not return expected value"
            
            # Delete key
            result = subprocess.run(
                ["docker", "exec", "ni-redis", "redis-cli", "del", test_key],
                capture_output=True, text=True, timeout=5
            )
            assert result.returncode == 0, "Redis DEL operation failed"
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.fail("Cannot perform Redis read/write operations")


class TestNetworkConnectivity:
    """Test network and connectivity"""
    
    def test_database_port_accessible(self):
        """Test database port is accessible"""
        host = "localhost"
        port = 5432
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            result = sock.connect_ex((host, port))
            assert result == 0, f"Database port {port} is not accessible"
        finally:
            sock.close()
    
    def test_cache_port_accessible(self):
        """Test cache port is accessible"""
        host = "localhost"
        port = 6379
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            result = sock.connect_ex((host, port))
            assert result == 0, f"Cache port {port} is not accessible"
        finally:
            sock.close()


class TestSystemResourceHealth:
    """Test system resource health"""
    
    def test_container_memory_usage(self):
        """Test system memory usage of containers"""
        try:
            # First get running containers with names
            ps_result = subprocess.run(
                ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if ps_result.returncode != 0:
                pytest.skip("Cannot access Docker - docker ps failed")
            
            # Build mapping of container IDs to names for our target containers
            target_containers = {}
            for line in ps_result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        container_id = parts[0].strip()
                        container_name = parts[1].strip()
                        if 'ni-postgres' in container_name or 'ni-redis' in container_name:
                            target_containers[container_id] = container_name
            
            if not target_containers:
                pytest.skip("No target containers (ni-postgres, ni-redis) are running")
            
            # Now get memory stats
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", 
                 "table {{.Container}}\t{{.MemUsage}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Check if we can get memory stats for our containers
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                container_stats = {}
                
                for line in lines:
                    if line.strip():
                        # Split on whitespace since docker stats uses multiple spaces, not tabs
                        parts = line.split()
                        if len(parts) >= 2:
                            container_id = parts[0].strip()
                            memory_usage = ' '.join(parts[1:]).strip()  # Join back in case memory has spaces
                            
                            # Check if this container ID matches one of our targets
                            if container_id in target_containers:
                                container_name = target_containers[container_id]
                                container_stats[container_name] = memory_usage
                            # Also check if the line contains container names directly
                            elif any(name in line for name in ['ni-postgres', 'ni-redis']):
                                container_stats[container_id] = memory_usage
                
                # Just verify we can collect stats - actual values depend on system load
                assert len(container_stats) > 0, f"Could not collect memory stats for target containers. Found containers: {list(target_containers.values())}"
            else:
                pytest.skip("Cannot check memory usage - docker stats not available")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Cannot check memory usage")


class TestSystemIntegrationHealth:
    """Test system integration health"""
    
    def test_cross_service_integration(self):
        """Test cross-service integration (database + cache)"""
        # Test database connectivity
        try:
            db_result = subprocess.run(
                ["docker", "exec", "ni-postgres", "psql", "-U", "ni", "-d", "ni", "-c", "SELECT 1;"],
                capture_output=True, text=True, timeout=5
            )
            db_ok = db_result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            db_ok = False
        
        # Test cache connectivity
        try:
            cache_result = subprocess.run(
                ["docker", "exec", "ni-redis", "redis-cli", "ping"],
                capture_output=True, text=True, timeout=5
            )
            cache_ok = cache_result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            cache_ok = False
        
        assert db_ok and cache_ok, "Cross-service integration failed - both services must be operational"
    
    @pytest.mark.integration
    def test_database_to_cache_integration(self, db_connection):
        """Test database can interact with cache system via stored functions"""
        with db_connection.cursor() as cur:
            # Test that we can call cache-related functions from database
            cur.execute("SELECT cleanup_expired_cache()")
            cleanup_result = cur.fetchone()[0]
            
            # Result should be a non-negative integer
            assert isinstance(cleanup_result, int) and cleanup_result >= 0, \
                f"Cache cleanup function returned invalid result: {cleanup_result}"


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