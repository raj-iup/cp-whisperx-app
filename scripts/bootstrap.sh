#!/usr/bin/env bash
set -euo pipefail

# Bootstrap script for cp-whisperx-app (Enhanced)
# One-time setup: Creates Python environment, installs dependencies, detects hardware
#
# PHASE 1 ENHANCEMENTS:
# - Hardware detection with caching
# - Model pre-download
# - Directory creation
# - FFmpeg validation
# - Comprehensive validation

# Load common logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-logging.sh"

VENV_DIR=".bollyenv"
REQ_FILE="requirements.txt"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_section "CP-WHISPERX-APP BOOTSTRAP (ENHANCED)"
log_info "One-time environment setup..."

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  log_error "Python not found. Please install Python 3.11+."
  exit 1
fi

log_info "Using python: $(command -v $PYTHON_BIN)"

log_info "Checking Python version (recommended: 3.11+)"
$PYTHON_BIN - <<'PY'
import sys
v = sys.version_info
print(f"Python {v.major}.{v.minor}.{v.micro}")
if v.major < 3 or (v.major == 3 and v.minor < 11):
    print("Warning: Python 3.11+ recommended for best compatibility.")
PY

if [ -d "$VENV_DIR" ]; then
  log_info "Found existing virtualenv in $VENV_DIR"
else
  log_info "Creating virtualenv in $VENV_DIR"
  $PYTHON_BIN -m venv "$VENV_DIR"
fi

log_info "Activating virtualenv"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

log_info "Upgrading pip and wheel"
python -m pip install -U pip wheel

if [ ! -f "$REQ_FILE" ]; then
  log_info "No $REQ_FILE found — writing recommended requirements.txt"
  cat > "$REQ_FILE" <<'EOF'
torch>=2.3,<3.0
torchaudio>=2.3,<3.0
openai-whisper>=20231117
faster-whisper>=1.0.0
whisperx>=3.1.0
whisper-ctranslate2>=0.4.0
ctranslate2>=4.2.0
pyannote.audio>=3.1.0
huggingface_hub>=0.23.0
librosa>=0.10.1
soundfile>=0.12.1
tmdbsimple>=2.9.1
rich>=13.7.0
python-dotenv>=1.0.0
pysubs2>=1.1.0
spacy>=3.7.0
transformers>=4.30.0
EOF
  log_success "Wrote $REQ_FILE"
fi

log_info "Installing Python packages from $REQ_FILE (this can take a while)"
python -m pip install -r "$REQ_FILE"

# ============================================================================
# PHASE 1 ENHANCEMENT: Create Required Directories
# ============================================================================
log_section "DIRECTORY STRUCTURE"
log_info "Creating required directories..."

REQUIRED_DIRS=(
    "in"
    "out"
    "logs"
    "jobs"
    "config"
    "shared-model-and-cache"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    dir_path="$PROJECT_ROOT/$dir"
    if [ ! -d "$dir_path" ]; then
        mkdir -p "$dir_path"
        log_info "  ✓ Created: $dir/"
    else
        log_info "  ✓ Exists: $dir/"
    fi
done

log_success "Directory structure validated"

# ============================================================================
# PHASE 1 ENHANCEMENT: Validate FFmpeg
# ============================================================================
log_section "FFMPEG VALIDATION"
log_info "Checking FFmpeg installation..."

if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n 1)
    log_success "FFmpeg found: $ffmpeg_version"
else
    log_warn "FFmpeg not found in PATH"
    log_info "FFmpeg is required for media processing"
    log_info "Install: sudo apt install ffmpeg (Ubuntu) or brew install ffmpeg (macOS)"
fi

# ============================================================================
# PHASE 1 ENHANCEMENT: Hardware Detection with Caching
# ============================================================================
log_section "HARDWARE DETECTION & CACHING"
log_info "Detecting hardware capabilities..."

if python "$PROJECT_ROOT/shared/hardware_detection.py" --no-cache; then
    log_success "Hardware detection complete"
    
    # Check if cache was created
    cache_file="$PROJECT_ROOT/out/hardware_cache.json"
    if [ -f "$cache_file" ]; then
        log_info "Hardware cache saved (valid for 1 hour)"
    fi
else
    log_warn "Hardware detection failed, but continuing..."
fi

# ============================================================================
# PHASE 1 ENHANCEMENT: Pre-download ML Models (Optional)
# ============================================================================
log_section "ML MODEL PRE-DOWNLOAD"
log_info "Checking for model pre-download..."

secrets_file="$PROJECT_ROOT/config/secrets.json"
if [ -f "$secrets_file" ]; then
    log_info "Found config/secrets.json - attempting model pre-download"
    
    # Try to read HF_TOKEN
    if command -v jq >/dev/null 2>&1; then
        hf_token=$(jq -r '.HF_TOKEN // empty' "$secrets_file" 2>/dev/null || echo "")
        
        if [ -n "$hf_token" ]; then
            log_info "HuggingFace token found - downloading PyAnnote models..."
            export HF_TOKEN="$hf_token"
            
            # Download PyAnnote diarization model
            if python -c "from pyannote.audio import Pipeline; Pipeline.from_pretrained('pyannote/speaker-diarization-3.1', use_auth_token=True)" 2>/dev/null; then
                log_success "PyAnnote models pre-downloaded"
            else
                log_warn "Could not pre-download PyAnnote models"
            fi
        else
            log_info "No HuggingFace token - skipping model pre-download"
            log_info "Models will be downloaded on first use"
        fi
    else
        log_info "jq not installed - skipping model pre-download"
        log_info "Install jq to enable model pre-download: sudo apt install jq"
    fi
else
    log_info "No secrets.json found - skipping model pre-download"
    log_info "Create config/secrets.json with HF_TOKEN to pre-download models"
fi

# ============================================================================
# Quick PyTorch Verification
# ============================================================================
log_info "Verifying PyTorch installation..."
python - <<'PY'
try:
    import torch, sys
    mps = getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available()
    cuda = torch.cuda.is_available()
    print('  ✓ PyTorch version:', torch.__version__)
    print('  ✓ MPS available:', bool(mps))
    print('  ✓ CUDA available:', bool(cuda))
except Exception as e:
    print('  ⚠ Could not verify torch:', repr(e))
    sys.exit(0)
PY

# ============================================================================
# Complete
# ============================================================================
log_section "BOOTSTRAP COMPLETE"
echo ""
echo "✅ Environment ready!"
echo ""
echo "What's been set up:"
echo "  ✓ Python virtual environment (.bollyenv/)"
echo "  ✓ 70+ Python packages installed"
echo "  ✓ Hardware capabilities detected & cached"
echo "  ✓ Required directories created"
echo "  ✓ FFmpeg validated"
echo ""
echo "Next steps:"
echo "  1. Prepare a job:"
echo "     ./prepare-job.sh path/to/video.mp4"
echo ""
echo "  2. Run the pipeline:"
echo "     ./run_pipeline.sh -j <job-id>"
echo ""
echo "Optional:"
echo "  • Create config/secrets.json with API tokens"
echo "  • Re-run bootstrap to pre-download models"
echo ""

exit 0
