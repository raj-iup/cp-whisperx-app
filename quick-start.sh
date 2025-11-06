#!/bin/bash
# CP-WhisperX-App Quick Start Script
# Full subtitle generation workflow with consistent logging

set -e

# Load common logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/common-logging.sh"

# Check arguments
if [ $# -lt 1 ]; then
    log_error "Input video is required"
    echo "Usage: ./quick-start.sh <input_video>"
    echo "Example: ./quick-start.sh in/movie.mp4"
    exit 1
fi

INPUT_VIDEO="$1"

log_section "CP-WHISPERX-APP QUICK START"
log_info "Input: $INPUT_VIDEO"
echo ""

# Validate input
if [ ! -f "$INPUT_VIDEO" ]; then
    log_error "Input video not found: $INPUT_VIDEO"
    exit 1
fi

# Step 1: Preflight checks
echo ""
echo "Step 1/3: Running preflight checks..."
echo "------------------------------------------------------------"
log_info "Validating system requirements..."

if python3 scripts/preflight.py; then
    log_success "Preflight checks passed"
else
    log_error "Preflight checks failed! Please fix errors before continuing."
    exit 1
fi

# Step 2: Prepare job
echo ""
echo "Step 2/3: Preparing job..."
echo "------------------------------------------------------------"
log_info "Creating job structure and configuration..."

python3 scripts/prepare-job.py "$INPUT_VIDEO" --subtitle-gen
if [ $? -ne 0 ]; then
    log_error "Job preparation failed!"
    exit 1
fi

# Extract job ID from most recent job directory
YEAR=$(date +%Y)
MONTH=$(date +%m)
DAY=$(date +%d)

JOB_ID=$(find out/$YEAR/$MONTH/$DAY -maxdepth 2 -type d -name "2*-*" 2>/dev/null | sort -r | head -1 | xargs basename)

if [ -z "$JOB_ID" ]; then
    log_error "Could not find created job directory"
    exit 1
fi

log_success "Job ID: $JOB_ID"

# Step 3: Run pipeline
echo ""
echo "Step 3/3: Running pipeline..."
echo "------------------------------------------------------------"
log_info "Executing full subtitle generation pipeline..."

python3 scripts/pipeline.py --job "$JOB_ID"
if [ $? -ne 0 ]; then
    log_error "Pipeline execution failed!"
    exit 1
fi

# Success
log_section "QUICK START COMPLETE"
log_success "Job completed successfully"
echo ""
echo "Check output directory: out/$YEAR/$MONTH/$DAY/*/$JOB_ID"
echo ""
