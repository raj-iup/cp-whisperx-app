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

# Show usage function
show_usage() {
    cat << EOF
Usage: $0 <input_media> [OPTIONS]

Prepare a job for the CP-WhisperX-App pipeline

ARGUMENTS:
  input_media           Path to input media file (MP4, MKV, AVI, etc.)

OPTIONS:
  -h, --help           Show this help message
  --start-time TIME    Start time for clip (HH:MM:SS format)
  --end-time TIME      End time for clip (HH:MM:SS format)

WORKFLOW MODES:
  --transcribe         Transcribe-only workflow (faster, no subtitles)
  --subtitle-gen       Full subtitle workflow with embedded subtitles (default)
  --native             Enable native GPU acceleration (auto-detects MPS/CUDA)

STAGE CONTROL:
  --enable-silero-vad     Enable Silero VAD stage (default: enabled)
  --disable-silero-vad    Disable Silero VAD stage
  --enable-pyannote-vad   Enable PyAnnote VAD stage (default: enabled)
  --disable-pyannote-vad  Disable PyAnnote VAD stage
  --enable-diarization    Enable Diarization stage (default: enabled)
  --disable-diarization   Disable Diarization stage

EXAMPLES:
  # Process full movie with subtitle generation (default)
  $0 /path/to/movie.mp4

  # Transcribe only (faster, no subtitles)
  $0 /path/to/movie.mp4 --transcribe

  # Enable native GPU acceleration
  $0 /path/to/movie.mp4 --native

  # Fast mode (skip PyAnnote VAD for 30% speed boost)
  $0 /path/to/movie.mp4 --disable-pyannote-vad

  # Speed mode (skip diarization for 50% speed boost, no speaker labels)
  $0 /path/to/movie.mp4 --disable-diarization

  # Process 5-minute clip for testing
  $0 /path/to/movie.mp4 --start-time 00:10:00 --end-time 00:15:00

PERFORMANCE TIPS:
  - Use --transcribe for fastest processing (3 stages only)
  - Use --disable-pyannote-vad for 30% faster (slight quality trade-off)
  - Use --disable-diarization for 50% faster (no speaker labels)
  - Use --native for GPU acceleration (MPS on macOS, CUDA on Linux/Windows)

For more information, see: docs/QUICKSTART.md

EOF
    exit 0
}

# Parse arguments
INPUT_MEDIA=""
START_TIME=""
END_TIME=""
WORKFLOW="subtitle-gen"  # default
ENABLE_SILERO_VAD=""
ENABLE_PYANNOTE_VAD=""
ENABLE_DIARIZATION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            ;;
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
        --enable-silero-vad)
            ENABLE_SILERO_VAD="true"
            shift
            ;;
        --disable-silero-vad)
            ENABLE_SILERO_VAD="false"
            shift
            ;;
        --enable-pyannote-vad)
            ENABLE_PYANNOTE_VAD="true"
            shift
            ;;
        --disable-pyannote-vad)
            ENABLE_PYANNOTE_VAD="false"
            shift
            ;;
        --enable-diarization)
            ENABLE_DIARIZATION="true"
            shift
            ;;
        --disable-diarization)
            ENABLE_DIARIZATION="false"
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
    echo ""
    echo "Stage Control:"
    echo "  --enable-silero-vad      Enable Silero VAD stage"
    echo "  --disable-silero-vad     Disable Silero VAD stage"
    echo "  --enable-pyannote-vad    Enable PyAnnote VAD stage"
    echo "  --disable-pyannote-vad   Disable PyAnnote VAD stage"
    echo "  --enable-diarization     Enable Diarization stage"
    echo "  --disable-diarization    Disable Diarization stage"
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

# Add stage control flags
if [ -n "$ENABLE_SILERO_VAD" ]; then
    if [ "$ENABLE_SILERO_VAD" = "true" ]; then
        PYTHON_ARGS+=("--enable-silero-vad")
        log_info "Stage control: Silero VAD ENABLED"
    else
        PYTHON_ARGS+=("--disable-silero-vad")
        log_info "Stage control: Silero VAD DISABLED"
    fi
fi

if [ -n "$ENABLE_PYANNOTE_VAD" ]; then
    if [ "$ENABLE_PYANNOTE_VAD" = "true" ]; then
        PYTHON_ARGS+=("--enable-pyannote-vad")
        log_info "Stage control: PyAnnote VAD ENABLED"
    else
        PYTHON_ARGS+=("--disable-pyannote-vad")
        log_info "Stage control: PyAnnote VAD DISABLED"
    fi
fi

if [ -n "$ENABLE_DIARIZATION" ]; then
    if [ "$ENABLE_DIARIZATION" = "true" ]; then
        PYTHON_ARGS+=("--enable-diarization")
        log_info "Stage control: Diarization ENABLED"
    else
        PYTHON_ARGS+=("--disable-diarization")
        log_info "Stage control: Diarization DISABLED"
    fi
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
        stage_num=1
        log_info "  ${stage_num}. Demux (audio extraction)"
        stage_num=$((stage_num + 1))
        
        if [ "$ENABLE_SILERO_VAD" != "false" ]; then
            log_info "  ${stage_num}. Silero VAD (voice detection)"
        else
            log_info "  ${stage_num}. Silero VAD (voice detection) [SKIPPED]"
        fi
        stage_num=$((stage_num + 1))
        
        log_info "  ${stage_num}. ASR (transcription)"
    else
        stage_num=1
        log_info "  ${stage_num}. Demux (audio extraction)"
        stage_num=$((stage_num + 1))
        
        log_info "  ${stage_num}. TMDB (metadata fetch)"
        stage_num=$((stage_num + 1))
        
        log_info "  ${stage_num}. Pre-NER (entity extraction)"
        stage_num=$((stage_num + 1))
        
        if [ "$ENABLE_SILERO_VAD" != "false" ]; then
            log_info "  ${stage_num}. Silero VAD (voice detection)"
        else
            log_info "  ${stage_num}. Silero VAD (voice detection) [SKIPPED]"
        fi
        stage_num=$((stage_num + 1))
        
        if [ "$ENABLE_PYANNOTE_VAD" != "false" ]; then
            log_info "  ${stage_num}. PyAnnote VAD (voice refinement)"
        else
            log_info "  ${stage_num}. PyAnnote VAD (voice refinement) [SKIPPED]"
        fi
        stage_num=$((stage_num + 1))
        
        if [ "$ENABLE_DIARIZATION" != "false" ]; then
            log_info "  ${stage_num}. Diarization (speaker identification)"
        else
            log_info "  ${stage_num}. Diarization (speaker identification) [SKIPPED]"
        fi
        stage_num=$((stage_num + 1))
        
        log_info "  ${stage_num}. ASR (transcription)"
        stage_num=$((stage_num + 1))
        
        log_info "  ${stage_num}. Second Pass Translation (refinement)"
        stage_num=$((stage_num + 1))
        
        log_info "  ${stage_num}. Lyrics Detection (song identification)"
        stage_num=$((stage_num + 1))
        
        log_info "  ${stage_num}. Lyrics Translation (song translation)"
        stage_num=$((stage_num + 1))
        
        log_info "  ${stage_num}. Post-NER (name correction)"
        stage_num=$((stage_num + 1))
        
        log_info "  ${stage_num}. Subtitle Generation (SRT creation)"
        stage_num=$((stage_num + 1))
        
        log_info "  ${stage_num}. Mux (video embedding)"
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
