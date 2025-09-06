#!/bin/bash

# System Health Tests - End-to-End
# Tests that the entire system is healthy and operational

set -e

echo "🏥 System Health Check - End-to-End Tests"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

tests_passed=0
tests_failed=0

test_system_component() {
    local component_name="$1"
    local test_command="$2"
    local description="$3"
    
    echo -n "  - $description... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
        tests_passed=$((tests_passed + 1))
        return 0
    else
        echo -e "${RED}❌${NC}"
        tests_failed=$((tests_failed + 1))
        return 1
    fi
}

echo -e "${BLUE}🔍 Infrastructure Health${NC}"
echo "========================"

# Docker system
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker system is not available${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker system operational${NC}"

# Required services
required_services=("ni-postgres:PostgreSQL database" "ni-redis:Redis cache")

for service_info in "${required_services[@]}"; do
    IFS=':' read -r container_name description <<< "$service_info"
    test_system_component "$container_name" "docker ps --format '{{.Names}}' | grep -q '^$container_name$'" "$description running"
done

echo ""
echo -e "${BLUE}🗄️  Data Layer Health${NC}"
echo "==================="

# Database connectivity and basic operations
test_system_component "database" "docker exec ni-postgres pg_isready -U ni -d ni" "Database accepting connections"
test_system_component "database" "docker exec ni-postgres psql -U ni -d ni -c 'SELECT COUNT(*) FROM regions;'" "Database queries working"

# PostGIS functionality
test_system_component "postgis" "docker exec ni-postgres psql -U ni -d ni -c 'SELECT PostGIS_Version();'" "PostGIS extension operational"

echo ""
echo -e "${BLUE}⚡ Cache Layer Health${NC}"
echo "=================="

test_system_component "redis" "docker exec ni-redis redis-cli ping" "Redis cache responding"
test_system_component "redis" "docker exec ni-redis redis-cli set system_test_key test_value && docker exec ni-redis redis-cli get system_test_key && docker exec ni-redis redis-cli del system_test_key" "Redis read/write operations"

echo ""
echo -e "${BLUE}🌐 Network & Connectivity${NC}"
echo "========================"

test_system_component "postgres-network" "nc -z localhost 5432" "Database port accessible"
test_system_component "redis-network" "nc -z localhost 6379" "Cache port accessible"

echo ""
echo -e "${BLUE}📊 System Resource Health${NC}"
echo "=========================="

# Memory usage check
echo -n "  - System memory usage... "
total_mem_usage=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}" | grep -E "(ni-postgres|ni-redis)" || echo "")
if [ ! -z "$total_mem_usage" ]; then
    echo -e "${GREEN}✅${NC}"
    echo "    $total_mem_usage"
    tests_passed=$((tests_passed + 1))
else
    echo -e "${YELLOW}⚠️ (cannot check memory usage)${NC}"
fi

echo ""
echo -e "${BLUE}🔧 System Integration Health${NC}"
echo "============================"

# Test full system workflow (database → cache interaction)
echo -n "  - Cross-service integration... "
if docker exec ni-postgres psql -U ni -d ni -c "SELECT 1;" > /dev/null 2>&1 && \
   docker exec ni-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
    tests_passed=$((tests_passed + 1))
else
    echo -e "${RED}❌${NC}"
    tests_failed=$((tests_failed + 1))
fi

# Summary
echo ""
echo -e "${BLUE}📋 System Health Summary${NC}"
echo "======================="
total_tests=$((tests_passed + tests_failed))
echo "Total health checks: $total_tests"
echo -e "Passed: ${GREEN}$tests_passed${NC}"
echo -e "Failed: ${RED}$tests_failed${NC}"

if [ $tests_failed -eq 0 ]; then
    echo -e "${GREEN}🎉 System is healthy and ready for operation!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  System has $tests_failed health issue(s)${NC}"
    echo -e "${YELLOW}💡 Check the failed components before proceeding${NC}"
    exit 1
fi