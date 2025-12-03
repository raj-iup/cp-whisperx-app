#!/bin/bash
# Test Runner Script
# Quick script to run different test suites

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# Display help
show_help() {
    cat << EOF
Test Runner for CP-WhisperX-App

Usage: ./tests/run-tests.sh [OPTIONS]

Options:
    all             Run all tests
    unit            Run unit tests only
    integration     Run integration tests only
    smoke           Run smoke tests only
    stages          Run stage-specific tests
    fast            Run fast tests (exclude slow)
    coverage        Run tests with coverage report
    watch           Run tests in watch mode
    help            Show this help message

Examples:
    ./tests/run-tests.sh unit
    ./tests/run-tests.sh coverage
    ./tests/run-tests.sh fast

EOF
}

# Check if pytest is installed
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found. Installing test dependencies..."
        pip install -r requirements/requirements-test.txt
    fi
}

# Create test directories
setup_test_dirs() {
    mkdir -p test-results/coverage
    mkdir -p logs
}

# Run all tests
run_all() {
    print_info "Running all tests..."
    setup_test_dirs
    pytest tests/ -v \
        --cov=scripts \
        --cov=shared \
        --cov-report=html:test-results/coverage \
        --cov-report=term-missing \
        --junit-xml=test-results/junit.xml
    print_success "All tests completed"
}

# Run unit tests
run_unit() {
    print_info "Running unit tests..."
    setup_test_dirs
    pytest tests/unit -v \
        --cov=scripts \
        --cov=shared \
        --cov-report=term-missing \
        -m "unit"
    print_success "Unit tests completed"
}

# Run integration tests
run_integration() {
    print_info "Running integration tests..."
    setup_test_dirs
    pytest tests/integration -v \
        -m "integration"
    print_success "Integration tests completed"
}

# Run smoke tests
run_smoke() {
    print_info "Running smoke tests..."
    pytest tests/ -v -m "smoke"
    print_success "Smoke tests completed"
}

# Run stage tests
run_stages() {
    print_info "Running stage tests..."
    pytest tests/stages -v -m "stage"
    print_success "Stage tests completed"
}

# Run fast tests (exclude slow)
run_fast() {
    print_info "Running fast tests..."
    setup_test_dirs
    pytest tests/ -v \
        -m "not slow and not requires_gpu and not requires_models" \
        --cov=scripts \
        --cov=shared \
        --cov-report=term-missing
    print_success "Fast tests completed"
}

# Run with coverage
run_coverage() {
    print_info "Running tests with coverage report..."
    setup_test_dirs
    pytest tests/ -v \
        --cov=scripts \
        --cov=shared \
        --cov-report=html:test-results/coverage \
        --cov-report=term-missing \
        --cov-report=json:test-results/coverage.json
    
    print_success "Tests completed"
    
    # Extract coverage percentage
    if [ -f test-results/coverage.json ]; then
        COVERAGE=$(python3 -c "import json; data=json.load(open('test-results/coverage.json')); print(f\"{data['totals']['percent_covered']:.1f}\")")
        print_info "Coverage: ${COVERAGE}%"
    fi
    
    # Open coverage report
    if [ -f test-results/coverage/index.html ]; then
        print_info "Opening coverage report..."
        if command -v open &> /dev/null; then
            open test-results/coverage/index.html
        elif command -v xdg-open &> /dev/null; then
            xdg-open test-results/coverage/index.html
        else
            print_info "Coverage report: test-results/coverage/index.html"
        fi
    fi
}

# Watch mode (requires pytest-watch)
run_watch() {
    print_info "Running tests in watch mode..."
    if ! command -v ptw &> /dev/null; then
        print_warning "pytest-watch not installed. Installing..."
        pip install pytest-watch
    fi
    ptw -- -v --cov=scripts --cov=shared --cov-report=term-missing
}

# Main script
main() {
    # Check prerequisites
    check_pytest
    
    # Parse command
    case "${1:-all}" in
        all)
            run_all
            ;;
        unit)
            run_unit
            ;;
        integration)
            run_integration
            ;;
        smoke)
            run_smoke
            ;;
        stages)
            run_stages
            ;;
        fast)
            run_fast
            ;;
        coverage)
            run_coverage
            ;;
        watch)
            run_watch
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"
