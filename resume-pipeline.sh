#!/bin/bash
# CP-WhisperX-App Pipeline Resume Script
# Resume pipeline execution with consistent logging

set -e

# Load common logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/common-logging.sh"

# Check arguments
if [ $# -lt 1 ]; then
    log_error "Job ID is required"
    echo "Usage: ./resume-pipeline.sh <job_id>"
    echo "Example: ./resume-pipeline.sh 20251102-0002"
    exit 1
fi

JOB_ID=$1

log_section "CP-WHISPERX-APP PIPELINE RESUME"
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
    log_section "PIPELINE RESUMED SUCCESSFULLY"
    log_success "Job $JOB_ID completed"
    echo ""
    exit 0
else
    log_section "PIPELINE RESUME FAILED"
    log_error "Pipeline execution failed with exit code $?"
    echo ""
    exit 1
fi
