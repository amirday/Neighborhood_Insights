#!/bin/bash

# Comprehensive Test Runner - Neighborhood Insights IL
# Runs distributed tests across API, ETL, and system components

set -e

echo "🧪 Comprehensive Test Runner - Neighborhood Insights IL"
echo "====================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_section() {
    echo ""
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}$(echo "$1" | sed 's/./=/g')${NC}"
}

# Start timer
start_time=$(date +%s)

# Test counters
total_suites=0
passed_suites=0
failed_suites=0

# Function to run a test suite
run_test_suite() {
    local suite_name="$1"
    local suite_command="$2"
    local suite_dir="$3"
    
    print_status "Running $suite_name tests..."
    
    if [ ! -z "$suite_dir" ]; then
        cd "$suite_dir" || return 1
    fi
    
    if eval "$suite_command"; then
        print_success "$suite_name tests passed"
        passed_suites=$((passed_suites + 1))
    else
        print_error "$suite_name tests failed"
        failed_suites=$((failed_suites + 1))
    fi
    
    if [ ! -z "$suite_dir" ]; then
        cd - > /dev/null || true
    fi
    
    total_suites=$((total_suites + 1))
    echo ""
}

# 1. API Tests (Python/pytest)
print_section "🚀 API Component Tests"
if [ -d "api/tests" ] && [ -f "api/pyproject.toml" ]; then
    run_test_suite "API Unit" "poetry run pytest tests/ -v --tb=short" "api"
    run_test_suite "API Integration" "poetry run pytest tests/ -v --tb=short -m integration" "api"
else
    echo "⚠️  API tests not available (missing api/tests or api/pyproject.toml)"
fi

# 2. ETL Tests (Python/pytest)  
print_section "🔄 ETL Component Tests"
if [ -d "etl/tests" ] && [ -f "etl/pyproject.toml" ]; then
    run_test_suite "ETL Unit" "poetry run pytest tests/ -v --tb=short -m 'not integration'" "etl"
    run_test_suite "ETL Integration" "poetry run pytest tests/ -v --tb=short -m integration" "etl"
else
    echo "⚠️  ETL tests not available (missing etl/tests or etl/pyproject.toml)"
fi

# 3. System/End-to-End Tests (Shell scripts)
print_section "🏥 System & End-to-End Tests"
if [ -d "tests" ]; then
    e2e_test_files=$(find tests -name "*.sh" -type f | sort)
    
    if [ ! -z "$e2e_test_files" ]; then
        for test_file in $e2e_test_files; do
            test_name=$(basename "$test_file" .sh)
            run_test_suite "E2E $test_name" "bash $test_file" ""
        done
    else
        echo "⚠️  No end-to-end test files found in tests/"
    fi
else
    echo "⚠️  No tests/ directory found"
fi

# 4. Data Validation Tests (if data exists)
print_section "📊 Data Validation Tests"
if [ -f "scripts/validate-data.sh" ]; then
    run_test_suite "Data Validation" "bash scripts/validate-data.sh" ""
else
    echo "ℹ️  Data validation tests not available (no sample data yet)"
fi

# Calculate results
end_time=$(date +%s)
duration=$((end_time - start_time))

print_section "📋 Comprehensive Test Summary"
echo "Total test suites: $total_suites"
echo -e "Passed: ${GREEN}$passed_suites${NC}"
echo -e "Failed: ${RED}$failed_suites${NC}"
echo "Duration: ${duration}s"

# Test coverage summary (if available)
echo ""
echo "📈 Coverage Summary:"
if [ -f "api/coverage.xml" ] || [ -f "etl/coverage.xml" ]; then
    echo "  API Coverage: $(grep -o 'line-rate="[^"]*"' api/coverage.xml 2>/dev/null | cut -d'"' -f2 | awk '{print int($1*100)"%"}' || echo "N/A")"
    echo "  ETL Coverage: $(grep -o 'line-rate="[^"]*"' etl/coverage.xml 2>/dev/null | cut -d'"' -f2 | awk '{print int($1*100)"%"}' || echo "N/A")"
else
    echo "  Coverage reports not available (run with --cov to generate)"
fi

# Final result
echo ""
if [ $total_suites -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No test suites found or available${NC}"
    echo "💡 Set up test environments:"
    echo "   - API: cd api && poetry install"  
    echo "   - ETL: cd etl && poetry install"
    echo "   - E2E: Create .sh files in tests/"
    exit 0
elif [ $failed_suites -eq 0 ]; then
    print_success "All $total_suites test suite(s) passed! 🎉"
    echo ""
    echo -e "${GREEN}✨ System is ready for development and deployment!${NC}"
    exit 0
else
    print_error "$failed_suites out of $total_suites test suite(s) failed"
    echo ""
    echo -e "${YELLOW}💡 Fix failing tests before proceeding${NC}"
    exit 1
fi