#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# AD-014 Cache Integration - Test Suite Runner
# ============================================================================
# Runs all cache-related tests (unit, integration, manual).
#
# Usage:
#   ./tests/run-cache-tests.sh [--unit | --integration | --manual | --all]
#
# Options:
#   --unit         Run unit tests only
#   --integration  Run integration tests only
#   --manual       Run manual tests only
#   --all          Run all tests (default)
# ============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Log functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✓]${NC} $*"; }
log_error() { echo -e "${RED}[✗]${NC} $*"; }
log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$*${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Parse arguments
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_MANUAL=false

if [ $# -eq 0 ]; then
    # Default: run all tests
    RUN_UNIT=true
    RUN_INTEGRATION=true
    RUN_MANUAL=true
else
    case "$1" in
        --unit)
            RUN_UNIT=true
            ;;
        --integration)
            RUN_INTEGRATION=true
            ;;
        --manual)
            RUN_MANUAL=true
            ;;
        --all)
            RUN_UNIT=true
            RUN_INTEGRATION=true
            RUN_MANUAL=true
            ;;
        *)
            log_error "Unknown option: $1"
            log_info "Usage: $0 [--unit | --integration | --manual | --all]"
            exit 1
            ;;
    esac
fi

cd "$PROJECT_ROOT"

# Track results
TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# Unit Tests
# ============================================================================

if [ "$RUN_UNIT" = true ]; then
    log_section "RUNNING UNIT TESTS"
    
    log_info "Testing: Media Identity"
    if pytest tests/unit/test_media_identity.py -v; then
        log_success "Media identity tests passed"
        ((TESTS_PASSED++))
    else
        log_error "Media identity tests failed"
        ((TESTS_FAILED++))
    fi
    
    echo ""
    log_info "Testing: Cache Manager"
    if pytest tests/unit/test_cache_manager.py -v; then
        log_success "Cache manager tests passed"
        ((TESTS_PASSED++))
    else
        log_error "Cache manager tests failed"
        ((TESTS_FAILED++))
    fi
fi

# ============================================================================
# Integration Tests
# ============================================================================

if [ "$RUN_INTEGRATION" = true ]; then
    log_section "RUNNING INTEGRATION TESTS"
    
    log_info "Testing: Baseline Cache Orchestrator"
    if pytest tests/integration/test_baseline_cache_orchestrator.py -v; then
        log_success "Cache orchestrator tests passed"
        ((TESTS_PASSED++))
    else
        log_error "Cache orchestrator tests failed"
        ((TESTS_FAILED++))
    fi
fi

# ============================================================================
# Manual Tests
# ============================================================================

if [ "$RUN_MANUAL" = true ]; then
    log_section "RUNNING MANUAL TESTS"
    
    # Check if test media exists
    if [ ! -f "in/Energy Demand in AI.mp4" ]; then
        log_error "Standard test media not found: in/Energy Demand in AI.mp4"
        log_info "Skipping manual tests"
    else
        log_info "Testing: Full Cache Integration"
        if ./tests/manual/test-cache-integration.sh; then
            log_success "Manual cache integration test passed"
            ((TESTS_PASSED++))
        else
            log_error "Manual cache integration test failed"
            ((TESTS_FAILED++))
        fi
    fi
fi

# ============================================================================
# Summary
# ============================================================================

log_section "TEST SUMMARY"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

if [ "$TOTAL_TESTS" -eq 0 ]; then
    log_error "No tests were run"
    exit 1
fi

log_info "Tests passed: $TESTS_PASSED"
log_info "Tests failed: $TESTS_FAILED"
log_info "Total tests:  $TOTAL_TESTS"

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo ""
    log_success "🎉 ALL TESTS PASSED!"
    echo ""
    exit 0
else
    echo ""
    log_error "❌ SOME TESTS FAILED"
    echo ""
    exit 1
fi
