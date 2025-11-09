#!/bin/bash
# CP-WhisperX-App Pipeline Orchestrator
# Bash wrapper for pipeline.py with consistent logging

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_message() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [orchestrator] [${level}] ${message}"
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

# Help message
show_help() {
    cat << HELP
Usage: ./run_pipeline.sh [OPTIONS] --job <job_id>

Docker-based pipeline orchestrator for context-aware subtitle generation.

OPTIONS:
    -j, --job JOB_ID        Job ID to process (required)
    -s, --stages "..."      Run specific stages only (e.g., "demux asr mux")
    --no-resume             Start fresh, ignore previous progress
    --list-stages           List all available stages and exit
    -h, --help              Show this help message

EXAMPLES:
    # Run complete pipeline
    ./run_pipeline.sh --job 20251102-0001

    # Run specific stages
    ./run_pipeline.sh --job 20251102-0001 --stages "demux asr mux"

    # Start fresh (no resume)
    ./run_pipeline.sh --job 20251102-0001 --no-resume

    # List available stages
    ./run_pipeline.sh --list-stages

HELP
}

# Default values
JOB_ID=""
STAGES=""
NO_RESUME=false
LIST_STAGES=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -j|--job)
            JOB_ID="$2"
            shift 2
            ;;
        -s|--stages)
            STAGES="$2"
            shift 2
            ;;
        --no-resume)
            NO_RESUME=true
            shift
            ;;
        --list-stages)
            LIST_STAGES=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Handle --list-stages
if [ "$LIST_STAGES" = true ]; then
    log_info "Listing available pipeline stages..."
    python3 scripts/pipeline.py --list-stages
    exit $?
fi

# Validate job ID
if [ -z "$JOB_ID" ]; then
    log_error "Job ID is required"
    show_help
    exit 1
fi

# Start
print_header "CP-WHISPERX-APP PIPELINE ORCHESTRATOR"
log_info "Job ID: $JOB_ID"

# Set up environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f "$PROJECT_ROOT/.bollyenv/bin/activate" ]; then
    source "$PROJECT_ROOT/.bollyenv/bin/activate"
    log_info "Activated virtual environment: .bollyenv"
else
    log_warning "Virtual environment not found. Run ./scripts/bootstrap.sh first"
fi

# Set cache directories (consistent with bootstrap)
export TORCH_HOME="$PROJECT_ROOT/.cache/torch"
export HF_HOME="$PROJECT_ROOT/.cache/huggingface"

# Validate Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Build arguments
PYTHON_ARGS=("scripts/pipeline.py" "--job" "$JOB_ID")

if [ -n "$STAGES" ]; then
    PYTHON_ARGS+=("--stages" $STAGES)
    log_info "Running specific stages: $STAGES"
fi

if [ "$NO_RESUME" = true ]; then
    PYTHON_ARGS+=("--no-resume")
    log_info "Resume: DISABLED (starting fresh)"
else
    log_info "Resume: ENABLED (will continue from last checkpoint)"
fi

# Execute Python script
log_info "Executing: python3 ${PYTHON_ARGS[*]}"
echo ""

python3 "${PYTHON_ARGS[@]}"
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    print_header "PIPELINE COMPLETED SUCCESSFULLY"
    log_success "Job $JOB_ID completed"
    echo ""
    exit 0
else
    print_header "PIPELINE FAILED"
    log_error "Pipeline execution failed with exit code $EXIT_CODE"
    echo ""
    exit $EXIT_CODE
fi
