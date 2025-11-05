#!/bin/bash
# CP-WhisperX-App Pipeline Resume Script
# Resume pipeline execution with consistent logging

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_message() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [resume-pipeline] [${level}] ${message}"
}

log_info() { log_message "INFO" "$@"; }
log_success() { echo -e "${GREEN}$(log_message "SUCCESS" "$@")${NC}"; }
log_error() { echo -e "${RED}$(log_message "ERROR" "$@")${NC}"; }

print_header() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

# Check arguments
if [ $# -lt 1 ]; then
    log_error "Job ID is required"
    echo "Usage: ./resume-pipeline.sh <job_id>"
    echo "Example: ./resume-pipeline.sh 20251102-0002"
    exit 1
fi

JOB_ID=$1

print_header "CP-WHISPERX-APP PIPELINE RESUME"
log_info "Resuming job: $JOB_ID"

# Validate Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Execute pipeline with resume enabled (default behavior)
log_info "Executing: python3 pipeline.py --job $JOB_ID"
echo ""

python3 pipeline.py --job "$JOB_ID"

if [ $? -eq 0 ]; then
    print_header "PIPELINE RESUMED SUCCESSFULLY"
    log_success "Job $JOB_ID completed"
    echo ""
    exit 0
else
    print_header "PIPELINE RESUME FAILED"
    log_error "Pipeline execution failed with exit code $?"
    echo ""
    exit 1
fi
