#!/usr/bin/env bash
set -euo pipefail

# CP-WhisperX-App Job Preparation Script (Simplified)
# Phase 1 Enhancement: Uses existing .bollyenv, hardware cache, no temp venv
#
# IMPROVEMENTS:
# - 80-90% faster (5-30 seconds vs 1-2 minutes)
# - No temporary venv creation
# - No PyTorch installation
# - Uses cached hardware info
# - Direct execution via .bollyenv

# Parse arguments
INPUT_MEDIA=""
START_TIME=""
END_TIME=""
WORKFLOW="subtitle-gen"  # default

while [[ $# -gt 0 ]]; do
    case $1 in
        --start-time)
            START_TIME="$2"
            shift 2
            ;;
        --end-time)
            END_TIME="$2"
            shift 2
            ;;
        --transcribe)
            WORKFLOW="transcribe"
            shift
            ;;
        --subtitle-gen)
            WORKFLOW="subtitle-gen"
            shift
            ;;
        *)
            if [ -z "$INPUT_MEDIA" ]; then
                INPUT_MEDIA="$1"
            fi
            shift
            ;;
    esac
done

# Load common logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/common-logging.sh"

log_section "CP-WHISPERX-APP JOB PREPARATION (OPTIMIZED)"

# ============================================================================
# Step 1: Validate Environment
# ============================================================================
log_info "Validating environment..."

# Check if bootstrap has been run
VENV_PATH=".bollyenv"
if [ ! -d "$VENV_PATH" ]; then
    log_error "Bootstrap not run - virtual environment not found"
    log_info "Please run: ./scripts/bootstrap.sh"
    exit 1
fi

ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"
if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    log_error "Virtual environment incomplete"
    log_info "Please re-run: ./scripts/bootstrap.sh"
    exit 1
fi

log_success "Environment validated"

# ============================================================================
# Step 2: Activate Virtual Environment
# ============================================================================
log_info "Activating .bollyenv..."
# shellcheck source=/dev/null
source "$ACTIVATE_SCRIPT"

# ============================================================================
# Step 3: Validate Input Media
# ============================================================================
log_info "Validating input media..."

if [ -z "$INPUT_MEDIA" ]; then
    log_error "No input media specified"
    echo ""
    echo "Usage: $0 <input_media> [options]"
    echo "Options:"
    echo "  --start-time HH:MM:SS    Start time for clip"
    echo "  --end-time HH:MM:SS      End time for clip"
    echo "  --transcribe             Transcribe-only workflow"
    echo "  --subtitle-gen           Full subtitle workflow (default)"
    exit 1
fi

if [ ! -f "$INPUT_MEDIA" ]; then
    log_error "Input media not found: $INPUT_MEDIA"
    exit 1
fi

log_success "Input media validated"

# ============================================================================
# Step 4: Build Arguments for prepare-job.py
# ============================================================================
PYTHON_ARGS=("scripts/prepare-job.py" "$INPUT_MEDIA")

# Add clip times if specified
if [ -n "$START_TIME" ]; then
    PYTHON_ARGS+=("--start-time" "$START_TIME")
fi

if [ -n "$END_TIME" ]; then
    PYTHON_ARGS+=("--end-time" "$END_TIME")
fi

# Add workflow mode
if [ "$WORKFLOW" = "transcribe" ]; then
    PYTHON_ARGS+=("--transcribe")
    log_info "Workflow: TRANSCRIBE"
else
    PYTHON_ARGS+=("--subtitle-gen")
    log_info "Workflow: SUBTITLE-GEN"
fi

# Always enable native mode (using .bollyenv)
PYTHON_ARGS+=("--native")

# Display execution info
log_info "Input media: $INPUT_MEDIA"
if [ -n "$START_TIME" ] && [ -n "$END_TIME" ]; then
    log_info "Clip: $START_TIME → $END_TIME"
fi

echo ""

# ============================================================================
# Step 5: Execute prepare-job.py
# ============================================================================
log_info "Executing: python ${PYTHON_ARGS[*]}"
echo ""

if python "${PYTHON_ARGS[@]}"; then
    echo ""
    log_success "Job preparation completed successfully"
    echo ""
    log_info "Next step: Run the pipeline with the generated job ID"
    log_info "  ./run_pipeline.sh -j <job-id>"
    echo ""
    exit 0
else
    exit_code=$?
    log_error "Job preparation failed with exit code $exit_code"
    exit $exit_code
fi
