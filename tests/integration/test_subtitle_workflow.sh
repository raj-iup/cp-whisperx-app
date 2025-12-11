#!/usr/bin/env bash
# ============================================================================
# Phase 3 Session 4: Integration Test Script
# ============================================================================
# Tests the complete 10-stage subtitle workflow end-to-end
# ============================================================================

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_section() { echo ""; echo -e "${BLUE}$*${NC}"; echo "========================================"; }

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Test configuration
TEST_MEDIA="$PROJECT_ROOT/in/test_clips/jaane_tu_test_clip.mp4"
TEST_NAME="integration_test_$(date +%Y%m%d_%H%M%S)"
WORKFLOW="subtitle"
SOURCE_LANG="hi"
TARGET_LANGS="en"  # Start with just English for faster testing

# Validation counters
CHECKS_TOTAL=0
CHECKS_PASSED=0
CHECKS_FAILED=0

check() {
    local description="$1"
    local condition="$2"
    
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    
    if eval "$condition"; then
        log_success "✓ $description"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        log_error "✗ $description"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
        return 1
    fi
}

# ============================================================================
# Test Execution
# ============================================================================

log_section "Phase 3 Session 4: Integration Test"
log_info "Testing complete 10-stage subtitle workflow"
log_info "Test media: $TEST_MEDIA"
log_info "Workflow: $WORKFLOW ($SOURCE_LANG → $TARGET_LANGS)"

# Pre-flight checks
log_section "1. Pre-flight Checks"

check "Test media exists" "[ -f '$TEST_MEDIA' ]"
check "prepare-job.sh exists" "[ -f './prepare-job.sh' ]"
check "run-pipeline.sh exists" "[ -f './run-pipeline.sh' ]"

MEDIA_SIZE=$(stat -f%z "$TEST_MEDIA" 2>/dev/null || stat -c%s "$TEST_MEDIA" 2>/dev/null)
log_info "Test media size: $(numfmt --to=iec-i --suffix=B $MEDIA_SIZE 2>/dev/null || echo "${MEDIA_SIZE} bytes")"

# Check Python environment
log_section "2. Environment Check"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    PYTHON_VERSION=$(python3 --version)
    log_success "Python version: $PYTHON_VERSION"
else
    log_warn "Python 3.11+ recommended"
fi

# Prepare job
log_section "3. Job Preparation"

log_info "Running prepare-job.sh..."

if ./prepare-job.sh \
    --media "$TEST_MEDIA" \
    --workflow "$WORKFLOW" \
    --source-language "$SOURCE_LANG" \
    --target-language "$TARGET_LANGS" 2>&1 | tee /tmp/prepare_job.log; then
    log_success "Job prepared successfully"
else
    log_error "Job preparation failed"
    exit 1
fi

# Find the job directory
JOB_DIR=$(ls -td out/*/$(whoami)/* 2>/dev/null | head -1)

if [ -z "$JOB_DIR" ]; then
    log_error "Could not find job directory"
    exit 1
fi

log_info "Job directory: $JOB_DIR"

# Validate job structure
log_section "4. Job Structure Validation"

check "Job directory exists" "[ -d '$JOB_DIR' ]"
check ".env.pipeline exists" "[ -f '$JOB_DIR/.env.pipeline' ]"
check "job.json exists" "[ -f '$JOB_DIR/job.json' ]"

# Check job configuration
if [ -f "$JOB_DIR/job.json" ]; then
    log_info "Job configuration:"
    python3 -c "
import json
with open('$JOB_DIR/job.json') as f:
    job = json.load(f)
    print(f\"  Workflow: {job.get('workflow', 'N/A')}\")
    print(f\"  Source: {job.get('source_language', 'N/A')}\")
    print(f\"  Targets: {job.get('target_languages', 'N/A')}\")
    print(f\"  Job ID: {job.get('job_id', 'N/A')}\")
" 2>/dev/null || log_warn "Could not parse job.json"
fi

# Stage validation - check all 10 stages are ready
log_section "5. Stage Validation (10 stages)"

STAGES=(
    "01_demux"
    "02_tmdb_enrichment"
    "03_glossary_loader"
    "04_source_separation"
    "05_pyannote_vad"
    "06_whisperx_asr"
    "07_alignment"
    "08_translation"
    "09_subtitle_generation"
    "10_mux"
)

for stage in "${STAGES[@]}"; do
    check "Stage script exists: $stage.py" "[ -f 'scripts/${stage}.py' ]"
done

# Dry run validation
log_section "6. Dry Run Validation"

log_info "Validating stage entry points..."

python3 << 'EOF'
import sys
import importlib
from pathlib import Path

PROJECT_ROOT = Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT))

stages = [
    "01_demux", "02_tmdb_enrichment", "03_glossary_loader",
    "04_source_separation", "05_pyannote_vad", "06_whisperx_asr",
    "07_alignment", "08_translation", "09_subtitle_generation", "10_mux"
]

failed = []
for stage in stages:
    try:
        module = importlib.import_module(f"scripts.{stage}")
        if not hasattr(module, "run_stage"):
            failed.append(f"{stage}: missing run_stage()")
            print(f"✗ {stage}: missing run_stage()")
        else:
            print(f"✓ {stage}: has run_stage()")
    except Exception as e:
        failed.append(f"{stage}: {str(e)}")
        print(f"✗ {stage}: {str(e)}")

if failed:
    print(f"\n{len(failed)} stage(s) failed validation")
    sys.exit(1)
else:
    print(f"\nAll {len(stages)} stages validated!")
    sys.exit(0)
EOF

if [ $? -eq 0 ]; then
    log_success "All stage entry points validated"
else
    log_error "Stage validation failed"
    exit 1
fi

# Run a quick syntax check on all stages
log_section "7. Syntax Check"

SYNTAX_ERRORS=0
for stage in "${STAGES[@]}"; do
    if python3 -m py_compile "scripts/${stage}.py" 2>/dev/null; then
        echo "  ✓ ${stage}.py"
    else
        echo "  ✗ ${stage}.py - SYNTAX ERROR"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    log_success "All stages pass syntax check"
else
    log_error "$SYNTAX_ERRORS stage(s) have syntax errors"
    exit 1
fi

# Summary
log_section "Integration Test Summary"

echo ""
echo "Checks Total:  $CHECKS_TOTAL"
echo "Checks Passed: $CHECKS_PASSED"
echo "Checks Failed: $CHECKS_FAILED"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    log_success "All pre-flight checks PASSED! ✓"
    log_info ""
    log_info "Ready for full pipeline execution:"
    log_info "  ./run-pipeline.sh --job-dir \"$JOB_DIR\""
    echo ""
    echo "Job prepared at: $JOB_DIR"
    echo ""
    
    # Ask if user wants to run the full pipeline
    read -p "Run full pipeline now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_section "8. Running Full Pipeline"
        log_info "This may take several minutes..."
        
        if ./run-pipeline.sh --job-dir "$JOB_DIR" 2>&1 | tee /tmp/pipeline_run.log; then
            log_success "Pipeline completed successfully!"
            
            # Validate outputs
            log_section "9. Output Validation"
            
            for stage in "${STAGES[@]}"; do
                if [ -d "$JOB_DIR/$stage" ]; then
                    FILE_COUNT=$(find "$JOB_DIR/$stage" -type f | wc -l)
                    echo "  ✓ $stage: $FILE_COUNT file(s)"
                else
                    echo "  ✗ $stage: directory not created"
                fi
            done
            
            # Check for final output
            if [ -f "$JOB_DIR/10_mux/*/final_output.mp4" ] || [ -f "$JOB_DIR/final_output.mp4" ]; then
                log_success "Final output video created!"
            else
                log_warn "Final output video not found"
            fi
            
        else
            log_error "Pipeline execution failed"
            log_info "Check logs at: /tmp/pipeline_run.log"
            exit 1
        fi
    else
        log_info "Skipping pipeline execution"
        log_info "Run manually with: ./run-pipeline.sh --job-dir \"$JOB_DIR\""
    fi
    
    exit 0
else
    log_error "$CHECKS_FAILED check(s) failed"
    exit 1
fi
