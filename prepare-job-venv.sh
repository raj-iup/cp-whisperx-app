#!/usr/bin/env bash

# ============================================================================
# ⚠️  DEPRECATION NOTICE ⚠️
# ============================================================================
# This script is DEPRECATED as of Phase 1 consolidation.
# 
# The prepare-job-venv wrapper is no longer needed because:
# - Bootstrap now creates a permanent .bollyenv/ environment
# - No temporary venv creation required
# - Hardware detection is cached
# - 80-90% faster execution
#
# Please use the simplified wrapper instead:
#   ./prepare-job.sh <input_media> [options]
#
# This script will be removed in a future version.
# ============================================================================

# CP-WhisperX-App Job Preparation with Virtual Environment (DEPRECATED)
# Creates isolated Python venv, installs PyTorch with GPU support, runs prepare-job.py
# Automatically detects CUDA/MPS and falls back to CPU if needed

set -e

echo ""
echo "⚠️  DEPRECATION WARNING"
echo "======================================================================"
echo "This script (prepare-job-venv.sh) is deprecated."
echo ""
echo "Please use the simplified wrapper instead:"
echo "  ./prepare-job.sh <input_media> [options]"
echo ""
echo "Benefits of the new script:"
echo "  • 80-90% faster (5-30 sec vs 1-2 min)"
echo "  • Uses existing .bollyenv environment"
echo "  • No temporary venv creation"
echo "  • Cached hardware detection"
echo "======================================================================"
echo ""
echo "Continuing with old script for backward compatibility..."
echo ""
sleep 3

# Load common logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/common-logging.sh"

# Parse arguments
INPUT_MEDIA=""
START_TIME=""
END_TIME=""
WORKFLOW_MODE="subtitle-gen"
KEEP_VENV=false

show_usage() {
    cat << EOF
Usage: ./prepare-job-venv.sh <input_media> [OPTIONS]

Creates isolated Python venv, installs PyTorch with GPU support, and runs job preparation.

Options:
    --start-time TIME       Start time for clip (HH:MM:SS)
    --end-time TIME         End time for clip (HH:MM:SS)
    --transcribe            Transcribe-only workflow
    --subtitle-gen          Full subtitle workflow (default)
    --keep-venv             Keep virtual environment after completion

Examples:
    # Full subtitle generation
    ./prepare-job-venv.sh movie.mp4
    
    # Transcribe only with GPU
    ./prepare-job-venv.sh movie.mp4 --transcribe
    
    # Process clip and keep venv
    ./prepare-job-venv.sh movie.mp4 --start-time 00:10:00 --end-time 00:15:00 --keep-venv

EOF
    exit 1
}

# Parse arguments
if [ $# -lt 1 ]; then
    log_error "Input media is required"
    show_usage
fi

INPUT_MEDIA="$1"
shift

while [ $# -gt 0 ]; do
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
            WORKFLOW_MODE="transcribe"
            shift
            ;;
        --subtitle-gen)
            WORKFLOW_MODE="subtitle-gen"
            shift
            ;;
        --keep-venv)
            KEEP_VENV=true
            shift
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Start
log_section "CP-WHISPERX-APP JOB PREPARATION (VENV MODE)"
log_info "Creating isolated Python environment for job preparation..."
echo ""

# Validate input media
if [ ! -f "$INPUT_MEDIA" ]; then
    log_error "Input media not found: $INPUT_MEDIA"
    exit 1
fi

# Validate Python 3.9+
log_info "Validating Python installation..."
PYTHON_CMD=""

for cmd in python3 python; do
    if command -v $cmd &> /dev/null; then
        PYTHON_CMD=$cmd
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    log_error "Python not found. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
log_info "Found: $PYTHON_VERSION"

# Extract version
if [[ $PYTHON_VERSION =~ Python\ ([0-9]+)\.([0-9]+) ]]; then
    PYTHON_MAJOR=${BASH_REMATCH[1]}
    PYTHON_MINOR=${BASH_REMATCH[2]}
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        log_error "Python 3.9+ required. Found: Python $PYTHON_MAJOR.$PYTHON_MINOR"
        exit 1
    fi
fi

log_success "Python version check passed"
echo ""

# Create temporary virtual environment
VENV_PATH="$SCRIPT_DIR/.venv-prepare-job-temp"
log_section "CREATING VIRTUAL ENVIRONMENT"
log_info "Location: $VENV_PATH"

if [ -d "$VENV_PATH" ]; then
    log_info "Removing existing venv..."
    rm -rf "$VENV_PATH"
fi

log_info "Creating new venv..."
$PYTHON_CMD -m venv "$VENV_PATH"

if [ $? -ne 0 ]; then
    log_error "Failed to create virtual environment"
    exit 1
fi

log_success "Virtual environment created"
echo ""

# Activate venv
log_info "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

VENV_PYTHON="$VENV_PATH/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    log_error "Virtual environment Python not found"
    exit 1
fi

log_success "Virtual environment activated"
echo ""

# Detect GPU/CUDA
log_section "HARDWARE DETECTION"
log_info "Detecting available acceleration hardware..."

DEVICE_MODE="cpu"
CUDA_VERSION=""

# Detect OS
OS_TYPE=$(uname -s)

# Check for NVIDIA GPU
if command -v nvidia-smi &> /dev/null; then
    log_info "NVIDIA GPU detected (nvidia-smi available)"
    
    # Get CUDA version from nvidia-smi
    NVIDIA_SMI_OUTPUT=$(nvidia-smi 2>&1)
    if [[ $NVIDIA_SMI_OUTPUT =~ CUDA\ Version:\ ([0-9]+)\.([0-9]+) ]]; then
        CUDA_MAJOR=${BASH_REMATCH[1]}
        CUDA_MINOR=${BASH_REMATCH[2]}
        CUDA_VERSION="$CUDA_MAJOR.$CUDA_MINOR"
        log_info "CUDA Version: $CUDA_VERSION"
        DEVICE_MODE="cuda"
    fi
else
    log_info "No NVIDIA GPU detected (nvidia-smi not found)"
fi

# Check for Apple Silicon (MPS) on macOS
if [ "$OS_TYPE" = "Darwin" ]; then
    SYSTEM_INFO=$(sysctl -n machdep.cpu.brand_string 2>&1)
    if [[ $SYSTEM_INFO =~ Apple ]]; then
        log_info "Apple Silicon detected"
        DEVICE_MODE="mps"
    fi
fi

log_success "Device mode: ${DEVICE_MODE^^}"
echo ""

# Install PyTorch with appropriate backend
log_section "INSTALLING PYTORCH"

case $DEVICE_MODE in
    cuda)
        log_info "Installing PyTorch with CUDA $CUDA_VERSION support..."
        
        # Map CUDA version to PyTorch wheel
        case $CUDA_MAJOR in
            12)
                if [ "$CUDA_MINOR" -ge 6 ]; then
                    TORCH_INDEX="https://download.pytorch.org/whl/cu126"
                elif [ "$CUDA_MINOR" -ge 4 ]; then
                    TORCH_INDEX="https://download.pytorch.org/whl/cu124"
                else
                    TORCH_INDEX="https://download.pytorch.org/whl/cu121"
                fi
                ;;
            11)
                TORCH_INDEX="https://download.pytorch.org/whl/cu118"
                ;;
            *)
                log_warn "CUDA version $CUDA_VERSION not recognized, using CUDA 12.1"
                TORCH_INDEX="https://download.pytorch.org/whl/cu121"
                ;;
        esac
        
        log_info "PyTorch index: $TORCH_INDEX"
        $VENV_PYTHON -m pip install --quiet torch torchvision torchaudio --index-url $TORCH_INDEX
        
        if [ $? -ne 0 ]; then
            log_warn "Failed to install CUDA PyTorch, falling back to CPU"
            DEVICE_MODE="cpu"
            $VENV_PYTHON -m pip install --quiet torch torchvision torchaudio
        fi
        ;;
    
    mps)
        log_info "Installing PyTorch with MPS support (macOS)..."
        $VENV_PYTHON -m pip install --quiet torch torchvision torchaudio
        
        if [ $? -ne 0 ]; then
            log_warn "Failed to install MPS PyTorch, falling back to CPU"
            DEVICE_MODE="cpu"
        fi
        ;;
    
    cpu)
        log_info "Installing PyTorch (CPU-only mode)..."
        $VENV_PYTHON -m pip install --quiet torch torchvision torchaudio
        ;;
esac

if [ $? -ne 0 ]; then
    log_error "Failed to install PyTorch"
    log_info "Cleaning up virtual environment..."
    rm -rf "$VENV_PATH"
    exit 1
fi

log_success "PyTorch installed successfully"
echo ""

# Verify PyTorch installation and GPU detection
log_section "VERIFYING PYTORCH INSTALLATION"
log_info "Testing PyTorch GPU detection..."

VERIFY_SCRIPT="
import torch
import sys

try:
    print(f'PyTorch version: {torch.__version__}')
    
    if torch.cuda.is_available():
        print(f'CUDA available: True')
        print(f'CUDA version: {torch.version.cuda}')
        print(f'GPU: {torch.cuda.get_device_name(0)}')
        print(f'GPU memory: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB')
        sys.exit(0)
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print(f'MPS available: True')
        print(f'Device: Apple Silicon')
        sys.exit(0)
    else:
        print(f'GPU: Not available (CPU mode)')
        sys.exit(0)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
"

$VENV_PYTHON -c "$VERIFY_SCRIPT"
VERIFY_EXIT=$?

echo ""

if [ $VERIFY_EXIT -ne 0 ]; then
    log_warn "PyTorch GPU detection failed, continuing with CPU mode"
    DEVICE_MODE="cpu"
else
    log_success "PyTorch verification passed"
fi

echo ""

# Install other required packages
log_info "Installing psutil for hardware detection..."
$VENV_PYTHON -m pip install --quiet psutil

if [ $? -ne 0 ]; then
    log_error "Failed to install psutil"
    if [ "$KEEP_VENV" = false ]; then
        rm -rf "$VENV_PATH"
    fi
    exit 1
fi

log_success "Dependencies installed"
echo ""

# Build arguments for prepare-job.py
log_section "RUNNING JOB PREPARATION"

PYTHON_ARGS=("scripts/prepare-job.py" "$INPUT_MEDIA")

if [ -n "$START_TIME" ]; then
    PYTHON_ARGS+=("--start-time" "$START_TIME")
fi

if [ -n "$END_TIME" ]; then
    PYTHON_ARGS+=("--end-time" "$END_TIME")
fi

if [ "$WORKFLOW_MODE" = "transcribe" ]; then
    PYTHON_ARGS+=("--transcribe")
    log_info "Workflow: TRANSCRIBE"
else
    PYTHON_ARGS+=("--subtitle-gen")
    log_info "Workflow: SUBTITLE-GEN"
fi

# Always enable native mode since we're using venv
PYTHON_ARGS+=("--native")
log_info "Native mode: ENABLED (using venv Python with ${DEVICE_MODE^^})"
log_info "Input media: $INPUT_MEDIA"

if [ -n "$START_TIME" ] && [ -n "$END_TIME" ]; then
    log_info "Clip: $START_TIME → $END_TIME"
fi

echo ""
log_info "Executing: python ${PYTHON_ARGS[*]}"
echo ""

# Execute prepare-job.py
$VENV_PYTHON "${PYTHON_ARGS[@]}"
PREPARE_EXIT=$?

echo ""

if [ $PREPARE_EXIT -eq 0 ]; then
    log_success "Job preparation completed successfully"
else
    log_error "Job preparation failed with exit code $PREPARE_EXIT"
    
    # Cleanup venv on failure
    if [ "$KEEP_VENV" = false ]; then
        log_info "Cleaning up virtual environment..."
        rm -rf "$VENV_PATH"
    fi
    exit $PREPARE_EXIT
fi

echo ""

# Cleanup virtual environment
if [ "$KEEP_VENV" = true ]; then
    log_section "VIRTUAL ENVIRONMENT PRESERVED"
    log_info "Virtual environment kept at: $VENV_PATH"
    log_info "To activate: source $VENV_PATH/bin/activate"
    log_info "To remove: rm -rf '$VENV_PATH'"
else
    log_section "CLEANING UP"
    log_info "Removing virtual environment..."
    
    # Deactivate first
    deactivate 2>/dev/null || true
    
    # Remove venv
    rm -rf "$VENV_PATH"
    
    if [ -d "$VENV_PATH" ]; then
        log_warn "Could not remove virtual environment (may be in use)"
        log_info "Manual cleanup: rm -rf '$VENV_PATH'"
    else
        log_success "Virtual environment removed"
    fi
fi

echo ""
log_section "JOB PREPARATION COMPLETE"
log_info "Device mode used: ${DEVICE_MODE^^}"
log_success "Ready to run pipeline"
echo ""

exit 0
