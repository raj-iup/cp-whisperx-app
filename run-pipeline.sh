#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# CP-WhisperX-App Pipeline Execution
# ============================================================================
# Version: 2.0.0
# Date: 2025-11-25
#
# Executes the complete pipeline for a prepared job.
# Orchestrates multiple virtual environments for stage execution.
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
PIPELINE_SCRIPT="$SCRIPT_DIR/run-pipeline.py"

# Show usage
show_usage() {
    cat << 'USAGE_EOF'
Usage: ./run-pipeline.sh [OPTIONS]

Execute the pipeline for a prepared job

REQUIRED OPTIONS:
  -j, --job-id JOB_ID          Job ID to execute (e.g., job-20251125-user-0001)

OPTIONAL OPTIONS:
  --resume                     Resume from last completed stage
  --log-level LEVEL            Log level: DEBUG|INFO|WARN|ERROR|CRITICAL
  --debug                      Enable debug mode (same as --log-level DEBUG)
  -h, --help                   Show this help message

PIPELINE STAGES:
  01. Source Separation        Demucs vocal extraction
  02. ASR                      WhisperX/MLX speech-to-text
  03. VAD                      Voice activity detection
  04. Diarization              Speaker identification (optional)
  05. Alignment                Word-level timestamps
  06. Translation              IndicTrans2/NLLB translation
  07. Subtitle Generation      SRT file creation
  08. Enhancement              Glossary, NER, cleanup (optional)

EXAMPLES:
  # Run complete pipeline
  ./run-pipeline.sh -j job-20251125-user-0001

  # Resume from failure
  ./run-pipeline.sh -j job-20251125-user-0001 --resume

  # Debug mode
  ./run-pipeline.sh -j job-20251125-user-0001 --log-level DEBUG

  # Monitor logs in real-time
  ./run-pipeline.sh -j job-20251125-user-0001 &
  tail -f out/2025/11/25/user/1/logs/pipeline.log

OUTPUT LOCATIONS:
  Job directory:    out/YYYY/MM/DD/user/N/
  Subtitles:        out/.../subtitles/*.srt
  Transcripts:      out/.../transcripts/*.txt
  Logs:             out/.../logs/*.log

ENVIRONMENT REQUIREMENTS:
  Must run ./bootstrap.sh first to create virtual environments

USAGE_EOF
}

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

# Check if environments are set up
if [ ! -d "$COMMON_VENV" ]; then
    log_critical "Environment not found: $COMMON_VENV"
    log_error "Run bootstrap first: ./bootstrap.sh"
    exit 1
fi

if [ ! -f "$PIPELINE_SCRIPT" ]; then
    log_critical "Pipeline script not found: $PIPELINE_SCRIPT"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSING
# ═══════════════════════════════════════════════════════════════════════════

if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

JOB_ID=""
JOB_DIR=""
LOG_LEVEL_ARG=""
PYTHON_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -j|--job-id)
            JOB_ID="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL_ARG="$2"
            shift 2
            ;;
        --debug)
            LOG_LEVEL_ARG="DEBUG"
            shift
            ;;
        --resume)
            PYTHON_ARGS+=("--resume")
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate job ID
if [ -z "$JOB_ID" ]; then
    log_critical "Job ID required. Use: -j <job-id>"
    exit 1
fi

# Find job directory
OUT_DIR="$PROJECT_ROOT/out"
if [ ! -d "$OUT_DIR" ]; then
    log_critical "Output directory not found: $OUT_DIR"
    exit 1
fi

# Parse job ID to find directory: job-YYYYMMDD-user-NNNN
if [[ "$JOB_ID" =~ ^job-([0-9]{8})-([^-]+)-([0-9]+)$ ]]; then
    DATE="${BASH_REMATCH[1]}"
    USER="${BASH_REMATCH[2]}"
    NUM="${BASH_REMATCH[3]}"
    
    YEAR="${DATE:0:4}"
    MONTH="${DATE:4:2}"
    DAY="${DATE:6:2}"
    
    # Remove leading zeros from NUM for directory path
    NUM_NO_ZEROS=$((10#$NUM))
    
    JOB_DIR="$OUT_DIR/$YEAR/$MONTH/$DAY/$USER/$NUM_NO_ZEROS"
else
    log_critical "Invalid job ID format: $JOB_ID"
    log_error "Expected format: job-YYYYMMDD-user-NNNN"
    exit 1
fi

# Validate job directory exists
if [ ! -d "$JOB_DIR" ]; then
    log_critical "Job directory not found: $JOB_DIR"
    log_error "Run prepare-job.sh first"
    exit 1
fi

log_debug "Job directory: $JOB_DIR"

# Check for job.json
if [ ! -f "$JOB_DIR/job.json" ]; then
    log_critical "Job configuration not found: $JOB_DIR/job.json"
    exit 1
fi

# Set log level from job config or argument
if [ -z "$LOG_LEVEL_ARG" ] && [ -f "$JOB_DIR/job.json" ]; then
    JOB_LOG_LEVEL=$(python3 -c "import json; print(json.load(open('$JOB_DIR/job.json')).get('log_level', 'INFO'))" 2>/dev/null || echo "INFO")
    if [ -n "$JOB_LOG_LEVEL" ]; then
        export LOG_LEVEL="$JOB_LOG_LEVEL"
        CURRENT_LOG_LEVEL=$(_get_log_level_value "$LOG_LEVEL")
        log_debug "Using log level from job.json: $JOB_LOG_LEVEL"
    fi
elif [ -n "$LOG_LEVEL_ARG" ]; then
    export LOG_LEVEL="$LOG_LEVEL_ARG"
    CURRENT_LOG_LEVEL=$(_get_log_level_value "$LOG_LEVEL")
fi

# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

log_section "CP-WHISPERX-APP PIPELINE EXECUTION"
log_info "Job ID: $JOB_ID"
log_info "Job directory: $JOB_DIR"
log_info "Log level: $LOG_LEVEL"

# Prepare Python arguments
PYTHON_ARGS+=("--job-dir" "$JOB_DIR")

log_debug "Python script: $PIPELINE_SCRIPT"
log_debug "Arguments: ${PYTHON_ARGS[*]}"

# Activate common environment and run pipeline
export VIRTUAL_ENV="$COMMON_VENV"
export PATH="$COMMON_VENV/bin:$PATH"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

log_info "Starting pipeline execution..."
echo ""

# Run pipeline script
exec "$COMMON_VENV/bin/python3" "$PIPELINE_SCRIPT" "${PYTHON_ARGS[@]}"
