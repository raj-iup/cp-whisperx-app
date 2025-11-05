#!/bin/bash
# CP-WhisperX-App Quick Start Script
# Full subtitle generation workflow with consistent logging

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_message() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [quick-start] [${level}] ${message}"
}

log_info() { log_message "INFO" "$@"; }
log_success() { echo -e "${GREEN}$(log_message "SUCCESS" "$@")${NC}"; }
log_warning() { echo -e "${YELLOW}$(log_message "WARNING" "$@")${NC}"; }
log_error() { echo -e "${RED}$(log_message "ERROR" "$@")${NC}"; }

print_header() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

print_step() {
    echo ""
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}------------------------------------------------------------${NC}"
}

# Check arguments
if [ $# -lt 1 ]; then
    log_error "Input video is required"
    echo "Usage: ./quick-start.sh <input_video>"
    echo "Example: ./quick-start.sh in/movie.mp4"
    exit 1
fi

INPUT_VIDEO="$1"

print_header "CP-WHISPERX-APP QUICK START"
log_info "Input: $INPUT_VIDEO"
echo ""

# Validate input
if [ ! -f "$INPUT_VIDEO" ]; then
    log_error "Input video not found: $INPUT_VIDEO"
    exit 1
fi

# Step 1: Preflight checks
print_step "Step 1/3: Running preflight checks..."
log_info "Validating system requirements..."

if python3 preflight.py; then
    log_success "Preflight checks passed"
else
    log_error "Preflight checks failed! Please fix errors before continuing."
    exit 1
fi

# Step 2: Prepare job
print_step "Step 2/3: Preparing job..."
log_info "Creating job structure and configuration..."

python3 prepare-job.py "$INPUT_VIDEO" --subtitle-gen
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
print_step "Step 3/3: Running pipeline..."
log_info "Executing full subtitle generation pipeline..."

python3 pipeline.py --job "$JOB_ID"
if [ $? -ne 0 ]; then
    log_error "Pipeline execution failed!"
    exit 1
fi

# Success
print_header "QUICK START COMPLETE"
log_success "Job completed successfully"
echo ""
echo "Check output directory: out/$YEAR/$MONTH/$DAY/*/$JOB_ID"
echo ""
