#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# CP-WhisperX-App Bootstrap - Multi-Environment Setup
# ============================================================================
# Version: 2.0.0
# Date: 2025-11-25
# 
# Creates 8 specialized virtual environments for isolated dependency management:
#   1. venv/common       - Core utilities (job mgmt, logging, muxing)
#   2. venv/whisperx     - WhisperX ASR (CUDA/CPU transcription)
#   3. venv/mlx          - MLX Whisper (Apple Silicon GPU)
#   4. venv/pyannote     - PyAnnote VAD (voice activity)
#   5. venv/demucs       - Demucs (audio source separation)
#   6. venv/indictrans2  - IndicTrans2 (22 Indic languages)
#   7. venv/nllb         - NLLB (200+ languages)
#   8. venv/llm          - LLM integration (Claude/GPT)
# ============================================================================

# ═══════════════════════════════════════════════════════════════════════════
# COMMON LOGGING FUNCTIONS (Integrated)
# ═══════════════════════════════════════════════════════════════════════════

# Color codes (only for terminal output)
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_CYAN='\033[0;36m'
COLOR_NC='\033[0m'

# Log level configuration
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

log_debug() {
    if _should_log "DEBUG"; then
        echo -e "${COLOR_CYAN}[DEBUG]${COLOR_NC} $*" >&2
        echo "[DEBUG] $*" >> "$LOG_FILE"
    fi
}

log_info() {
    if _should_log "INFO"; then
        echo -e "${COLOR_BLUE}[INFO]${COLOR_NC} $*"
        echo "[INFO] $*" >> "$LOG_FILE"
    fi
}

log_warn() {
    if _should_log "WARN"; then
        echo -e "${COLOR_YELLOW}[WARN]${COLOR_NC} $*" >&2
        echo "[WARN] $*" >> "$LOG_FILE"
    fi
}

log_error() {
    if _should_log "ERROR"; then
        echo -e "${COLOR_RED}[ERROR]${COLOR_NC} $*" >&2
        echo "[ERROR] $*" >> "$LOG_FILE"
    fi
}

log_critical() {
    echo -e "${COLOR_RED}[CRITICAL]${COLOR_NC} $*" >&2
    echo "[CRITICAL] $*" >> "$LOG_FILE"
}

log_success() {
    if _should_log "INFO"; then
        echo -e "${COLOR_GREEN}✓${COLOR_NC} $*"
        echo "✓ $*" >> "$LOG_FILE"
    fi
}

log_section() {
    if _should_log "INFO"; then
        echo ""
        echo -e "${COLOR_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_NC}"
        echo -e "${COLOR_CYAN}$*${COLOR_NC}"
        echo -e "${COLOR_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_NC}"
        echo "" >> "$LOG_FILE"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$LOG_FILE"
        echo "$*" >> "$LOG_FILE"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$LOG_FILE"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Setup logging
mkdir -p "$PROJECT_ROOT/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$PROJECT_ROOT/logs/bootstrap_${TIMESTAMP}.log"

# Parse arguments
DEBUG_MODE=false
FORCE_RECREATE=false
SKIP_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --debug) DEBUG_MODE=true; LOG_LEVEL="DEBUG"; CURRENT_LOG_LEVEL=0; shift ;;
        --force) FORCE_RECREATE=true; shift ;;
        --skip-cache) SKIP_CACHE=true; shift ;;
        --log-level) LOG_LEVEL="$2"; CURRENT_LOG_LEVEL=$(_get_log_level_value "$LOG_LEVEL"); shift 2 ;;
        -h|--help)
            cat << 'HELP_EOF'
Usage: ./bootstrap.sh [OPTIONS]

Bootstrap CP-WhisperX-App multi-environment setup

OPTIONS:
  --debug           Enable verbose debug logging
  --force           Force recreate all environments
  --skip-cache      Skip model caching (faster, models download on first use)
  --log-level LEVEL Set log level: DEBUG|INFO|WARN|ERROR|CRITICAL
  -h, --help        Show this help message

CREATES 8 VIRTUAL ENVIRONMENTS:
  venv/common       Core utilities (~500MB)
  venv/whisperx     WhisperX ASR (~2GB)
  venv/mlx          MLX Whisper - Apple Silicon only (~1GB)
  venv/pyannote     PyAnnote VAD (~1GB)
  venv/demucs       Demucs source separation (~500MB)
  venv/indictrans2  IndicTrans2 translation (~3GB)
  venv/nllb         NLLB-200 translation (~3GB)
  venv/llm          LLM integration - optional (~200MB)

EXAMPLES:
  ./bootstrap.sh                  # Standard setup with model caching
  ./bootstrap.sh --skip-cache     # Fast setup without models
  ./bootstrap.sh --force --debug  # Force recreate with verbose logs
  ./bootstrap.sh --log-level WARN # Quiet mode

DISK USAGE: ~11GB for environments + ~20GB for cached models
TIME: 5-10 minutes without cache, 20-30 minutes with cache

HELP_EOF
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ═══════════════════════════════════════════════════════════════════════════
# PLATFORM DETECTION
# ═══════════════════════════════════════════════════════════════════════════

log_section "CP-WHISPERX-APP BOOTSTRAP v2.0.0"
log_info "Starting bootstrap process..."
log_info "Log file: $LOG_FILE"

OS_TYPE=$(uname -s)
ARCH_TYPE=$(uname -m)
HAS_CUDA=false
HAS_MPS=false
HAS_MLX=false

log_debug "Platform: $OS_TYPE ($ARCH_TYPE)"

# Detect hardware capabilities
if [[ "$OS_TYPE" == "Darwin" ]]; then
    HAS_MPS=true
    if [[ "$ARCH_TYPE" == "arm64" ]]; then
        HAS_MLX=true
        log_success "Detected: Apple Silicon (M1/M2/M3/M4) with MPS + MLX"
    else
        log_info "Detected: Intel Mac with MPS"
    fi
elif command -v nvidia-smi &>/dev/null; then
    HAS_CUDA=true
    GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    log_success "Detected: NVIDIA GPU - $GPU_INFO"
else
    log_info "Detected: CPU-only mode"
fi

# ═══════════════════════════════════════════════════════════════════════════
# PYTHON VERSION CHECK
# ═══════════════════════════════════════════════════════════════════════════

log_section "VALIDATING REQUIREMENTS"

if ! command -v python3 &>/dev/null; then
    log_critical "Python 3 not found. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

log_info "Python version: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    log_critical "Python 3.10+ required. Current version: $PYTHON_VERSION"
    exit 1
fi

log_success "Python version compatible"

# Check pip
if ! python3 -m pip --version &>/dev/null; then
    log_critical "pip not found. Please install pip."
    exit 1
fi

log_success "pip available"

# Check disk space
AVAILABLE_SPACE=$(df -Pk . | awk 'NR==2 {print $4}')
REQUIRED_SPACE=$((30 * 1024 * 1024))  # 30GB in KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    log_warn "Low disk space: $(($AVAILABLE_SPACE / 1024 / 1024))GB available"
    log_warn "Recommended: 30GB+ for environments and models"
fi

# ═══════════════════════════════════════════════════════════════════════════
# VIRTUAL ENVIRONMENT CREATION
# ═══════════════════════════════════════════════════════════════════════════

create_venv() {
    local env_name="$1"
    local req_file="$2"
    local description="$3"
    
    log_section "Environment: $env_name"
    log_info "$description"
    
    local venv_path="$PROJECT_ROOT/$env_name"
    
    if [ -d "$venv_path" ] && [ "$FORCE_RECREATE" = false ]; then
        log_info "Environment exists: $env_name"
        return 0
    fi
    
    if [ -d "$venv_path" ]; then
        log_warn "Removing existing environment: $env_name"
        rm -rf "$venv_path"
    fi
    
    log_info "Creating virtual environment..."
    if [ "$CURRENT_LOG_LEVEL" -eq 0 ]; then
        python3 -m venv "$venv_path" 2>&1 | tee -a "$LOG_FILE"
    else
        python3 -m venv "$venv_path" >> "$LOG_FILE" 2>&1
    fi
    
    log_info "Installing dependencies from $req_file..."
    if [ "$CURRENT_LOG_LEVEL" -eq 0 ]; then
        "$venv_path/bin/pip" install --upgrade pip 2>&1 | tee -a "$LOG_FILE"
        "$venv_path/bin/pip" install -r "$req_file" 2>&1 | tee -a "$LOG_FILE"
    else
        "$venv_path/bin/pip" install --upgrade pip >> "$LOG_FILE" 2>&1
        "$venv_path/bin/pip" install -r "$req_file" >> "$LOG_FILE" 2>&1
    fi
    
    log_success "Environment ready: $env_name"
}

# Create all environments
create_venv "venv/common" "requirements/requirements-common.txt" "Core utilities"
create_venv "venv/whisperx" "requirements/requirements-whisperx.txt" "WhisperX ASR"

if [ "$HAS_MLX" = true ]; then
    create_venv "venv/mlx" "requirements/requirements-mlx.txt" "MLX Whisper (Apple Silicon)"
fi

create_venv "venv/pyannote" "requirements/requirements-pyannote.txt" "PyAnnote VAD"
create_venv "venv/demucs" "requirements/requirements-demucs.txt" "Demucs source separation"
create_venv "venv/indictrans2" "requirements/requirements-indictrans2.txt" "IndicTrans2 translation"
create_venv "venv/nllb" "requirements/requirements-nllb.txt" "NLLB-200 translation"

# LLM environment (optional, for enhanced song/poetry translation)
if [ -f "requirements/requirements-llm.txt" ]; then
    create_venv "venv/llm" "requirements/requirements-llm.txt" "LLM integration"
fi

# ═══════════════════════════════════════════════════════════════════════════
# MODEL CACHING (Optional)
# ═══════════════════════════════════════════════════════════════════════════

if [ "$SKIP_CACHE" = false ]; then
    log_section "MODEL CACHING"
    log_info "Pre-caching models for offline use (~20GB, 10-15 min)"
    log_warn "Skip with --skip-cache flag for faster setup"
    
    cache_model() {
        local model_id="${1:-}"
        local venv_path="${2:-}"
        
        # Validate arguments
        if [ -z "$model_id" ] || [ -z "$venv_path" ]; then
            log_error "cache_model: Missing required arguments"
            return 1
        fi
        
        # Check if environment exists
        if [ ! -f "$PROJECT_ROOT/$venv_path/bin/python3" ]; then
            log_warn "Skipping $model_id: environment $venv_path not found"
            return 0
        fi
        
        log_info "Caching: $model_id"
        if [ "$CURRENT_LOG_LEVEL" -eq 0 ]; then
            "$PROJECT_ROOT/$venv_path/bin/python3" -c "
from huggingface_hub import snapshot_download
snapshot_download('$model_id', resume_download=True)
" 2>&1 | tee -a "$LOG_FILE"
            if [ $? -eq 0 ]; then
                log_success "Cached: $model_id"
            else
                log_warn "Failed: $model_id"
            fi
        else
            "$PROJECT_ROOT/$venv_path/bin/python3" -c "
from huggingface_hub import snapshot_download
snapshot_download('$model_id', resume_download=True)
" >> "$LOG_FILE" 2>&1
            if [ $? -eq 0 ]; then
                log_success "Cached: $model_id"
            else
                log_warn "Failed: $model_id"
            fi
        fi
    }
    
    # Cache models
    cache_model "openai/whisper-large-v3" "venv/whisperx"
    
    if [ "$HAS_MLX" = true ]; then
        cache_model "mlx-community/whisper-large-v3-mlx" "venv/mlx"
    fi
    
    cache_model "pyannote/speaker-diarization-3.1" "venv/pyannote"
    cache_model "ai4bharat/indictrans2-indic-en-1B" "venv/indictrans2"
    cache_model "ai4bharat/indictrans2-indic-indic-1B" "venv/indictrans2"
    cache_model "facebook/nllb-200-3.3B" "venv/nllb"
fi

# ═══════════════════════════════════════════════════════════════════════════
# COMPLETION
# ═══════════════════════════════════════════════════════════════════════════

log_section "BOOTSTRAP COMPLETE"
log_success "All environments created successfully"
log_info ""
log_info "Next steps:"
log_info "  1. Prepare a job: ./prepare-job.sh --media in/movie.mp4 --workflow subtitle \\"
log_info "     --source-language hi --target-language en"
log_info "  2. Run pipeline: ./run-pipeline.sh -j <job-id>"
log_info ""
log_info "Documentation: docs/INDEX.md"
log_info "Log file: $LOG_FILE"

exit 0
