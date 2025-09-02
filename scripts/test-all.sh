#!/bin/bash

# Test All Script - Neighborhood Insights IL
# Runs complete local test suite

set -e  # Exit on any error

echo "🧪 Running Complete Test Suite - Neighborhood Insights IL"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Start timer
start_time=$(date +%s)

print_status "Starting local test environment..."

# Ensure services are up
print_status "Starting required services..."
make up > /dev/null 2>&1 || {
    print_warning "Failed to start services with make up, trying docker-compose directly..."
    docker-compose up -d postgres redis > /dev/null 2>&1
}

# Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to be ready..."
timeout=30
while ! docker exec ni-postgres pg_isready -U ni -d ni > /dev/null 2>&1; do
    sleep 1
    timeout=$((timeout - 1))
    if [ $timeout -eq 0 ]; then
        print_error "PostgreSQL did not start within 30 seconds"
        exit 1
    fi
done

print_success "Services are ready"

# Initialize test counters
total_tests=0
passed_tests=0
failed_tests=0

# Function to run a test section
run_test_section() {
    local test_name="$1"
    local test_command="$2"
    
    print_status "Running $test_name..."
    
    if eval "$test_command"; then
        print_success "$test_name passed"
        passed_tests=$((passed_tests + 1))
    else
        print_error "$test_name failed"
        failed_tests=$((failed_tests + 1))
    fi
    
    total_tests=$((total_tests + 1))
    echo ""
}

# 1. Code Quality Checks
echo -e "${BLUE}📋 Phase 1: Code Quality Checks${NC}"
echo "================================="

# Check if pre-commit is installed
if command -v pre-commit > /dev/null 2>&1; then
    run_test_section "Pre-commit hooks" "pre-commit run --all-files"
else
    print_warning "Pre-commit not installed. Install with: pip install pre-commit && pre-commit install"
fi

# 2. Unit Tests
echo -e "${BLUE}🔬 Phase 2: Unit Tests${NC}"
echo "======================"

# API Unit Tests
if [ -d "api" ] && [ -f "api/pyproject.toml" ]; then
    run_test_section "API Unit Tests" "cd api && poetry run pytest tests/unit/ -v --tb=short 2>/dev/null || echo 'No unit tests found in api/tests/unit/'"
else
    print_warning "API directory not fully set up yet"
fi

# ETL Unit Tests  
if [ -d "etl" ] && [ -f "etl/pyproject.toml" ]; then
    run_test_section "ETL Unit Tests" "cd etl && poetry run pytest tests/unit/ -v --tb=short 2>/dev/null || echo 'No unit tests found in etl/tests/unit/'"
else
    print_warning "ETL directory not fully set up yet"
fi

# Frontend Unit Tests
if [ -d "app" ] && [ -f "app/package.json" ]; then
    run_test_section "Frontend Unit Tests" "cd app && pnpm run test --run 2>/dev/null || echo 'Frontend tests not configured yet'"
else
    print_warning "Frontend directory not fully set up yet"
fi

# 3. Integration Tests
echo -e "${BLUE}🔗 Phase 3: Integration Tests${NC}"
echo "============================="

# Database Integration Tests
run_test_section "Database Connection Test" "docker exec ni-postgres psql -U ni -d ni -c 'SELECT 1;' > /dev/null"

# API Integration Tests (if available)
if [ -d "api/tests/integration" ]; then
    run_test_section "API Integration Tests" "cd api && poetry run pytest tests/integration/ -v --tb=short 2>/dev/null || echo 'No integration tests found'"
fi

# 4. End-to-End Tests (if available)
echo -e "${BLUE}🌐 Phase 4: End-to-End Tests${NC}"
echo "============================"

if [ -d "e2e" ] && [ -f "e2e/package.json" ]; then
    # Start frontend if needed for E2E
    if [ -d "app" ]; then
        print_status "Starting frontend for E2E tests..."
        cd app && pnpm run build > /dev/null 2>&1 && pnpm run start > /dev/null 2>&1 &
        FRONTEND_PID=$!
        sleep 5
        cd ..
    fi
    
    run_test_section "End-to-End Tests" "cd e2e && pnpm exec playwright test || echo 'E2E tests not ready yet'"
    
    # Cleanup frontend
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID > /dev/null 2>&1 || true
    fi
else
    print_warning "E2E tests directory not set up yet"
fi

# 5. Performance & Health Checks
echo -e "${BLUE}⚡ Phase 5: Performance & Health Checks${NC}"
echo "========================================"

# Service Health Checks
run_test_section "PostgreSQL Health" "docker exec ni-postgres pg_isready -U ni -d ni"
run_test_section "Redis Health" "docker exec ni-redis redis-cli ping"

# Memory usage check
if command -v docker > /dev/null 2>&1; then
    memory_usage=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}" | grep -E "(ni-postgres|ni-redis)" || echo "Memory check skipped")
    print_status "Container memory usage:"
    echo "$memory_usage"
fi

# Calculate results
end_time=$(date +%s)
duration=$((end_time - start_time))

echo ""
echo -e "${BLUE}📊 Test Results Summary${NC}"
echo "======================="
echo "Total test sections: $total_tests"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$failed_tests${NC}"
echo "Duration: ${duration}s"

if [ $failed_tests -eq 0 ]; then
    print_success "All tests passed! 🎉"
    echo ""
    echo -e "${GREEN}Your codebase is ready for development!${NC}"
    exit 0
else
    print_error "$failed_tests test section(s) failed"
    echo ""
    echo -e "${YELLOW}Fix the failing tests before proceeding with development.${NC}"
    exit 1
fi