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
    log_info "Workflow: TRANSCRIBE (demux → vad → asr only)"
else
    PYTHON_ARGS+=("--subtitle-gen")
    log_info "Workflow: SUBTITLE-GEN (all 13 stages, default)"
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

# Capture output for job ID extraction
output=$(python "${PYTHON_ARGS[@]}" 2>&1)
exit_code=$?

# Display output
echo "$output"

if [ $exit_code -eq 0 ]; then
    # Extract job ID from output
    job_id=""
    while IFS= read -r line; do
        if [[ "$line" =~ Job\ created:\ (.+)$ ]]; then
            job_id="${BASH_REMATCH[1]}"
            job_id=$(echo "$job_id" | xargs)  # trim whitespace
            break
        fi
    done <<< "$output"
    
    echo ""
    log_success "Job preparation completed successfully"
    echo ""
    log_info "Pipeline will execute these stages automatically:"
    
    if [ "$WORKFLOW" = "transcribe" ]; then
        log_info "  1. Demux (audio extraction)"
        log_info "  2. Silero VAD (voice detection)"
        log_info "  3. ASR (transcription)"
    else
        log_info "  1. Demux (audio extraction)"
        log_info "  2. TMDB (metadata fetch)"
        log_info "  3. Pre-NER (entity extraction)"
        log_info "  4. Silero VAD (voice detection)"
        log_info "  5. PyAnnote VAD (voice refinement)"
        log_info "  6. Diarization (speaker identification)"
        log_info "  7. ASR (transcription)"
        log_info "  8. Second Pass Translation (refinement)"
        log_info "  9. Lyrics Detection (song identification)"
        log_info "  10. Lyrics Translation (song translation)"
        log_info "  11. Post-NER (name correction)"
        log_info "  12. Subtitle Generation (SRT creation)"
        log_info "  13. Mux (video embedding)"
    fi
    
    echo ""
    log_info "Next step: Run the pipeline with the generated job ID"
    if [ -n "$job_id" ]; then
        log_info "  ./run_pipeline.sh -j $job_id"
    else
        log_info "  ./run_pipeline.sh -j <job-id>"
    fi
    echo ""
    exit 0
else
    echo ""
    log_error "Job preparation failed with exit code $exit_code"
    exit $exit_code
fi
