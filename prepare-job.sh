#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# CP-WhisperX-App Job Preparation
# ============================================================================
# Version: 2.0.0
# Date: 2025-11-25
#
# Creates job directory structure and configuration for pipeline execution.
# Delegates to Python implementation for complex logic.
# ============================================================================

# ═══════════════════════════════════════════════════════════════════════════
# COMMON LOGGING FUNCTIONS (Integrated)
# ═══════════════════════════════════════════════════════════════════════════

if [ -t 1 ]; then
    COLOR_RED='\033[0;31m'; COLOR_GREEN='\033[0;32m'
    COLOR_YELLOW='\033[1;33m'; COLOR_BLUE='\033[0;34m'
    COLOR_CYAN='\033[0;36m'; COLOR_NC='\033[0m'
else
    COLOR_RED=''; COLOR_GREEN=''; COLOR_YELLOW=''
    COLOR_BLUE=''; COLOR_CYAN=''; COLOR_NC=''
fi

LOG_LEVEL=${LOG_LEVEL:-INFO}

_get_log_level_value() {
    case "$1" in
        DEBUG) echo 0 ;; INFO) echo 1 ;; WARN) echo 2 ;;
        ERROR) echo 3 ;; CRITICAL) echo 4 ;; *) echo 1 ;;
    esac
}

CURRENT_LOG_LEVEL=$(_get_log_level_value "$LOG_LEVEL")

_should_log() {
    local msg_level=$(_get_log_level_value "$1")
    [ "$msg_level" -ge "$CURRENT_LOG_LEVEL" ]
}

log_debug() { _should_log "DEBUG" && echo -e "${COLOR_CYAN}[DEBUG]${COLOR_NC} $*" >&2 || true; }
log_info() { _should_log "INFO" && echo -e "${COLOR_BLUE}[INFO]${COLOR_NC} $*" || true; }
log_warn() { _should_log "WARN" && echo -e "${COLOR_YELLOW}[WARN]${COLOR_NC} $*" >&2 || true; }
log_error() { _should_log "ERROR" && echo -e "${COLOR_RED}[ERROR]${COLOR_NC} $*" >&2 || true; }
log_critical() { echo -e "${COLOR_RED}[CRITICAL]${COLOR_NC} $*" >&2; }
log_success() { echo -e "${COLOR_GREEN}✓${COLOR_NC} $*"; }

log_section() {
    echo ""
    echo -e "${COLOR_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_NC}"
    echo -e "${COLOR_CYAN}$*${COLOR_NC}"
    echo -e "${COLOR_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_NC}"
}

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$PROJECT_ROOT/scripts"
COMMON_VENV="$PROJECT_ROOT/venv/common"
PREPARE_JOB_SCRIPT="$SCRIPT_DIR/prepare-job.py"

# Show usage
show_usage() {
    cat << 'USAGE_EOF'
Usage: ./prepare-job.sh [OPTIONS]

Create a job configuration for the pipeline

REQUIRED OPTIONS:
  --media FILE                  Input media file (audio/video)
  --workflow MODE               Workflow: transcribe|translate|subtitle
  -s, --source-language CODE    Source language (hi, ta, te, etc.)

OPTIONAL OPTIONS:
  -t, --target-language CODE(S) Target language(s), comma-separated
                                Example: en,gu,ta (max 5 languages)
  --start-time HH:MM:SS         Clip start time (for testing)
  --end-time HH:MM:SS           Clip end time (for testing)
  --two-step                    Enable two-step transcription (Phase 2)
  --no-cache                    Force regeneration (skip cached baseline)
  --user-id ID                  User ID (default: 1). User must exist in users/{userId}/
  --log-level LEVEL             Log level: DEBUG|INFO|WARN|ERROR|CRITICAL
  --debug                       Enable debug mode (same as --log-level DEBUG)
  -h, --help                    Show this help message

WORKFLOW MODES:
  transcribe  - Speech-to-text only (fastest)
  translate   - Transcribe + translate (requires -t)
  subtitle    - Full pipeline with SRT generation (requires -t)

TWO-STEP TRANSCRIPTION:
  --two-step enables Phase 2 optimization where transcription and
  translation are performed separately for better accuracy:
    • Step 1: Transcribe in source language (e.g., Hindi)
    • Step 2: Translate using dedicated translation model
  Expected improvement: +5-8% accuracy on Hindi transcription

EXAMPLES:
  # Hindi to English subtitles (default userId=1)
  ./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
    --source-language hi --target-language en

  # Specify different userId
  ./prepare-job.sh --user-id 2 --media in/movie.mp4 --workflow subtitle \
    --source-language hi --target-language en

  # Multi-language subtitles
  ./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
    --source-language hi --target-language en,gu,ta

  # Transcription only
  ./prepare-job.sh --media in/audio.mp3 --workflow transcribe \
    --source-language hi

  # Test with clip (30 seconds)
  ./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
    --source-language hi --target-language en \
    --start-time 00:10:00 --end-time 00:10:30

SUPPORTED LANGUAGES:
  22 Indian Languages: hi, ta, te, bn, gu, kn, ml, mr, pa, or, as, ur,
                       ne, sd, si, sa, ks, doi, mni, kok, mai, sat
  Plus: 200+ global languages via NLLB

OUTPUT:
  Job directory: out/YYYY/MM/DD/user/N/
  Job ID format: job-YYYYMMDD-user-NNNN

USAGE_EOF
}

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

# Check if environment is set up
if [ ! -d "$COMMON_VENV" ]; then
    log_critical "Environment not found: $COMMON_VENV"
    log_error "Run bootstrap first: ./bootstrap.sh"
    exit 1
fi

if [ ! -f "$PREPARE_JOB_SCRIPT" ]; then
    log_critical "Script not found: $PREPARE_JOB_SCRIPT"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSING
# ═══════════════════════════════════════════════════════════════════════════
# Convert shell script's --media flag to positional argument for Python script
# Python script expects: prepare-job.py <input_media> [OPTIONS]
# Shell script provides: prepare-job.sh --media <file> [OPTIONS]
# ═══════════════════════════════════════════════════════════════════════════

if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

PYTHON_ARGS=()
LOG_LEVEL_ARG=""
MEDIA_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        --media)
            # Extract media file for conversion to positional arg
            MEDIA_FILE="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL_ARG="$2"
            PYTHON_ARGS+=("$1" "$2")
            shift 2
            ;;
        --debug)
            LOG_LEVEL_ARG="DEBUG"
            PYTHON_ARGS+=("$1")
            shift
            ;;
        -s|--source-language|-t|--target-language|--workflow|--start-time|--end-time|--user-id|--two-step)
            # Pass through known arguments
            PYTHON_ARGS+=("$1")
            if [[ $# -gt 1 && ! "$2" =~ ^- ]]; then
                PYTHON_ARGS+=("$2")
                shift
            fi
            shift
            ;;
        *)
            # Pass through other arguments
            PYTHON_ARGS+=("$1")
            shift
            ;;
    esac
done

# Validate required media file
if [ -z "$MEDIA_FILE" ]; then
    log_error "Missing required argument: --media"
    echo ""
    show_usage
    exit 1
fi

# Add media file as first positional argument for Python script
# This maintains compatibility between shell and Python interfaces
PYTHON_ARGS=("$MEDIA_FILE" "${PYTHON_ARGS[@]}")

# Set log level if provided
if [ -n "$LOG_LEVEL_ARG" ]; then
    export LOG_LEVEL="$LOG_LEVEL_ARG"
    CURRENT_LOG_LEVEL=$(_get_log_level_value "$LOG_LEVEL")
fi

# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

log_section "CP-WHISPERX-APP JOB PREPARATION"

log_debug "Project root: $PROJECT_ROOT"
log_debug "Python script: $PREPARE_JOB_SCRIPT"
log_debug "Arguments: ${PYTHON_ARGS[*]}"

# Activate common environment and run Python script
export VIRTUAL_ENV="$COMMON_VENV"
export PATH="$COMMON_VENV/bin:$PATH"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

log_info "Executing job preparation..."

# Run Python script with all arguments
exec "$COMMON_VENV/bin/python3" "$PREPARE_JOB_SCRIPT" "${PYTHON_ARGS[@]}"
