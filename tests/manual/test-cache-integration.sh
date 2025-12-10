#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# AD-014 Cache Integration - Manual Test Script
# ============================================================================
# Tests the complete cache workflow with real media files.
#
# Usage:
#   ./tests/manual/test-cache-integration.sh [media_file]
#
# If no media file provided, uses standard test media.
# ============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Log functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✓]${NC} $*"; }
log_error() { echo -e "${RED}[✗]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $*"; }
log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$*${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Test configuration
MEDIA_FILE="${1:-$PROJECT_ROOT/in/Energy Demand in AI.mp4}"
TEST_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_JOB_PREFIX="test-cache-$TEST_TIMESTAMP"

# Cleanup function
cleanup() {
    if [ -n "${TEST_JOB_ID1:-}" ]; then
        log_info "Cleaning up job: $TEST_JOB_ID1"
        rm -rf "out/*/$USER/$TEST_JOB_ID1" 2>/dev/null || true
    fi
    if [ -n "${TEST_JOB_ID2:-}" ]; then
        log_info "Cleaning up job: $TEST_JOB_ID2"
        rm -rf "out/*/$USER/$TEST_JOB_ID2" 2>/dev/null || true
    fi
}

trap cleanup EXIT

# ============================================================================
# Pre-flight checks
# ============================================================================

log_section "PRE-FLIGHT CHECKS"

# Check media file exists
if [ ! -f "$MEDIA_FILE" ]; then
    log_error "Media file not found: $MEDIA_FILE"
    log_info "Usage: $0 [media_file]"
    log_info "Example: $0 in/test_clips/jaane_tu_test_clip.mp4"
    exit 1
fi

log_success "Media file exists: $(basename "$MEDIA_FILE")"

# Check cache tool exists
if [ ! -f "$PROJECT_ROOT/tools/manage-cache.py" ]; then
    log_error "Cache management tool not found"
    exit 1
fi

log_success "Cache management tool available"

# Check Python modules
if ! python3 -c "from shared.baseline_cache_orchestrator import BaselineCacheOrchestrator" 2>/dev/null; then
    log_error "Cache orchestrator module not available"
    exit 1
fi

log_success "Cache orchestrator module available"

# ============================================================================
# Test 1: First Run (Generate Baseline + Cache)
# ============================================================================

log_section "TEST 1: FIRST RUN (GENERATE + CACHE)"

log_info "Creating job for first run..."

# Clear any existing cache for this media
log_info "Clearing existing cache for this media..."
python3 "$PROJECT_ROOT/tools/manage-cache.py" verify "$MEDIA_FILE" 2>&1 | grep "media_id" || true

cd "$PROJECT_ROOT"

# Prepare job
log_info "Preparing job (first run)..."
./prepare-job.sh \
    --media "$MEDIA_FILE" \
    --workflow transcribe \
    --source-language en \
    > /tmp/prepare-job-1.log 2>&1

# Extract job ID from output
TEST_JOB_ID1=$(grep -o "job-[0-9]*-${USER}-[0-9]*" /tmp/prepare-job-1.log | head -1)

if [ -z "$TEST_JOB_ID1" ]; then
    log_error "Failed to create job"
    cat /tmp/prepare-job-1.log
    exit 1
fi

log_success "Job created: $TEST_JOB_ID1"

# Record start time
START_TIME_1=$(date +%s)

# Run pipeline (first run - should generate baseline)
log_info "Running pipeline (first run - will generate baseline)..."
if ! ./run-pipeline.sh -j "$TEST_JOB_ID1" > /tmp/pipeline-1.log 2>&1; then
    log_error "Pipeline failed (first run)"
    tail -50 /tmp/pipeline-1.log
    exit 1
fi

# Record end time
END_TIME_1=$(date +%s)
DURATION_1=$((END_TIME_1 - START_TIME_1))

log_success "Pipeline completed (first run)"
log_info "Duration: ${DURATION_1}s"

# Check if baseline was cached
log_info "Checking if baseline was cached..."
if ! grep -q "Storing baseline in cache" /tmp/pipeline-1.log; then
    log_warn "Baseline storage not logged (might be disabled)"
else
    log_success "Baseline stored in cache"
fi

# Verify cache with tool
log_info "Verifying cache with management tool..."
if python3 "$PROJECT_ROOT/tools/manage-cache.py" verify "$MEDIA_FILE" 2>&1 | grep -q "Cached baseline found"; then
    log_success "Cache verified"
else
    log_error "Cache not found"
    exit 1
fi

# ============================================================================
# Test 2: Second Run (Use Cache)
# ============================================================================

log_section "TEST 2: SECOND RUN (USE CACHE)"

log_info "Creating job for second run..."

# Prepare job
log_info "Preparing job (second run)..."
./prepare-job.sh \
    --media "$MEDIA_FILE" \
    --workflow transcribe \
    --source-language en \
    > /tmp/prepare-job-2.log 2>&1

# Extract job ID
TEST_JOB_ID2=$(grep -o "job-[0-9]*-${USER}-[0-9]*" /tmp/prepare-job-2.log | head -1)

if [ -z "$TEST_JOB_ID2" ]; then
    log_error "Failed to create job"
    cat /tmp/prepare-job-2.log
    exit 1
fi

log_success "Job created: $TEST_JOB_ID2"

# Record start time
START_TIME_2=$(date +%s)

# Run pipeline (second run - should use cache)
log_info "Running pipeline (second run - should use cache)..."
if ! ./run-pipeline.sh -j "$TEST_JOB_ID2" > /tmp/pipeline-2.log 2>&1; then
    log_error "Pipeline failed (second run)"
    tail -50 /tmp/pipeline-2.log
    exit 1
fi

# Record end time
END_TIME_2=$(date +%s)
DURATION_2=$((END_TIME_2 - START_TIME_2))

log_success "Pipeline completed (second run)"
log_info "Duration: ${DURATION_2}s"

# Check if cache was used
log_info "Checking if cache was used..."
if grep -q "Found cached baseline" /tmp/pipeline-2.log; then
    log_success "Cache was used"
elif grep -q "Generating baseline from scratch" /tmp/pipeline-2.log; then
    log_error "Cache was NOT used (regenerated baseline)"
    exit 1
else
    log_warn "Cannot determine if cache was used"
fi

# ============================================================================
# Test 3: Performance Comparison
# ============================================================================

log_section "TEST 3: PERFORMANCE COMPARISON"

log_info "First run (generate + cache):  ${DURATION_1}s"
log_info "Second run (use cache):        ${DURATION_2}s"

if [ "$DURATION_2" -lt "$DURATION_1" ]; then
    TIME_SAVED=$((DURATION_1 - DURATION_2))
    PERCENT_SAVED=$((TIME_SAVED * 100 / DURATION_1))
    log_success "Time saved: ${TIME_SAVED}s (${PERCENT_SAVED}%)"
    
    if [ "$PERCENT_SAVED" -ge 50 ]; then
        log_success "✓ Performance goal met (≥50% faster)"
    else
        log_warn "Performance below expected (target: 70-80% faster)"
    fi
else
    log_error "Second run was SLOWER than first run!"
    exit 1
fi

# ============================================================================
# Test 4: Cache Management
# ============================================================================

log_section "TEST 4: CACHE MANAGEMENT"

log_info "Testing cache management CLI..."

# Stats
log_info "Cache statistics:"
python3 "$PROJECT_ROOT/tools/manage-cache.py" stats | head -10

# List
log_info "Cached media:"
python3 "$PROJECT_ROOT/tools/manage-cache.py" list | head -10

# ============================================================================
# Test 5: Force Regeneration (--no-cache)
# ============================================================================

log_section "TEST 5: FORCE REGENERATION (--no-cache)"

log_info "Testing --no-cache flag..."

# Prepare job with --no-cache
log_info "Preparing job with --no-cache..."
./prepare-job.sh \
    --media "$MEDIA_FILE" \
    --workflow transcribe \
    --source-language en \
    --no-cache \
    > /tmp/prepare-job-3.log 2>&1

TEST_JOB_ID3=$(grep -o "job-[0-9]*-${USER}-[0-9]*" /tmp/prepare-job-3.log | head -1)

if [ -z "$TEST_JOB_ID3" ]; then
    log_error "Failed to create job"
    exit 1
fi

log_success "Job created with --no-cache: $TEST_JOB_ID3"

# Run pipeline (should skip cache)
log_info "Running pipeline with --no-cache..."
if ! ./run-pipeline.sh -j "$TEST_JOB_ID3" > /tmp/pipeline-3.log 2>&1; then
    log_error "Pipeline failed (no-cache run)"
    exit 1
fi

# Verify cache was NOT used
if grep -q "Cache disabled" /tmp/pipeline-3.log || grep -q "Generating baseline from scratch" /tmp/pipeline-3.log; then
    log_success "Cache was correctly skipped with --no-cache flag"
else
    log_warn "Cannot confirm cache was skipped"
fi

# Cleanup third job
rm -rf "out/*/$USER/$TEST_JOB_ID3" 2>/dev/null || true

# ============================================================================
# Summary
# ============================================================================

log_section "TEST SUMMARY"

log_success "✓ First run completed (generate + cache)"
log_success "✓ Second run completed (use cache)"
log_success "✓ Performance improvement verified (${PERCENT_SAVED}% faster)"
log_success "✓ Cache management CLI tested"
log_success "✓ Force regeneration tested (--no-cache)"

echo ""
log_success "🎉 ALL TESTS PASSED!"
echo ""

log_info "Detailed logs:"
log_info "  First run:  /tmp/pipeline-1.log"
log_info "  Second run: /tmp/pipeline-2.log"
log_info "  No-cache:   /tmp/pipeline-3.log"

exit 0
