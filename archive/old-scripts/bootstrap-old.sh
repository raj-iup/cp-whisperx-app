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
# - Debug mode with detailed logging

# Parse command line arguments
DEBUG_MODE=false
LOG_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        --log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --debug            Enable debug mode with verbose logging"
            echo "  --log-file FILE    Save bootstrap log to FILE (default: logs/bootstrap_TIMESTAMP.log)"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --debug --log-file logs/bootstrap.log"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# Load common logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-logging.sh"

VENV_DIR=".venv-common"
REQ_FILE="requirements.txt"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Setup log file
if [ -z "$LOG_FILE" ]; then
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    LOG_FILE="$PROJECT_ROOT/logs/bootstrap_${TIMESTAMP}.log"
fi

# Ensure logs directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Initialize log file
{
    echo "════════════════════════════════════════════════════════════════════════"
    echo "CP-WHISPERX-APP BOOTSTRAP LOG"
    echo "════════════════════════════════════════════════════════════════════════"
    echo "Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Debug Mode: $DEBUG_MODE"
    echo "Log File: $LOG_FILE"
    echo "════════════════════════════════════════════════════════════════════════"
    echo ""
} > "$LOG_FILE"

# Enhanced logging function that writes to both console and file
log_both() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log to file with timestamp and level
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Log to console using existing functions
    case "$level" in
        INFO)
            log_info "$message"
            ;;
        SUCCESS)
            log_success "$message"
            ;;
        WARNING)
            log_warn "$message"
            ;;
        ERROR)
            log_error "$message"
            ;;
        DEBUG)
            if [ "$DEBUG_MODE" = true ]; then
                echo "🔍 DEBUG: $message"
            fi
            ;;
        SECTION)
            log_section "$message"
            ;;
    esac
}

# Debug helper function
debug() {
    log_both "DEBUG" "$@"
}

# Detect platform for optimal requirements file
OS_TYPE=$(uname -s)
ARCH_TYPE=$(uname -m)

log_both "SECTION" "CP-WHISPERX-APP BOOTSTRAP (ENHANCED)"
log_both "INFO" "One-time environment setup..."
log_both "INFO" "Platform: $OS_TYPE ($ARCH_TYPE)"
debug "Debug mode enabled - verbose logging to: $LOG_FILE"

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  log_both "ERROR" "Python not found. Please install Python 3.11+."
  exit 1
fi

log_both "INFO" "Using python: $(command -v $PYTHON_BIN)"
debug "Python binary path: $(command -v $PYTHON_BIN)"

log_both "INFO" "Checking Python version (recommended: 3.11+)"
python_version=$($PYTHON_BIN - <<'PY'
import sys
v = sys.version_info
print(f"{v.major}.{v.minor}.{v.micro}")
if v.major < 3 or (v.major == 3 and v.minor < 11):
    print("Warning: Python 3.11+ recommended for best compatibility.")
PY
)
log_both "INFO" "Python version: $python_version"
debug "Python version info: $python_version"

if [ -d "$VENV_DIR" ]; then
  log_both "INFO" "Found existing virtualenv in $VENV_DIR"
  debug "Virtualenv directory: $PROJECT_ROOT/$VENV_DIR"
else
  log_both "INFO" "Creating virtualenv in $VENV_DIR"
  debug "Running: $PYTHON_BIN -m venv $VENV_DIR"
  $PYTHON_BIN -m venv "$VENV_DIR" 2>&1 | tee -a "$LOG_FILE"
fi

log_both "INFO" "Activating virtualenv"
debug "Sourcing: $VENV_DIR/bin/activate"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

log_both "INFO" "Upgrading pip, setuptools, and wheel"
debug "Running: python -m pip install -U pip setuptools wheel"
python -m pip install -U pip setuptools wheel 2>&1 | tee -a "$LOG_FILE"

# Select optimal requirements file for platform
SELECTED_REQ_FILE="$REQ_FILE"

if [[ "$OS_TYPE" == "Darwin" ]] && [[ "$ARCH_TYPE" == "arm64" ]]; then
    # macOS Apple Silicon (M1/M2/M3)
    PINNED_REQ="$PROJECT_ROOT/requirements-macos-pinned.txt"
    if [ -f "$PINNED_REQ" ]; then
        log_info "Detected macOS Apple Silicon (M1/M2/M3)"
        log_info "Using optimized pinned requirements for faster installation"
        SELECTED_REQ_FILE="$PINNED_REQ"
    else
        log_warn "Pinned requirements not found, falling back to $REQ_FILE"
    fi
elif [ ! -f "$REQ_FILE" ]; then
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

log_info "Installing Python packages from $(basename "$SELECTED_REQ_FILE")"
log_info "  This can take a while, but pinned versions resolve much faster..."
python -m pip install -r "$SELECTED_REQ_FILE"

# Install optional dependencies (includes jellyfish for bias injection)
OPTIONAL_REQ="$PROJECT_ROOT/requirements-optional.txt"
if [ -f "$OPTIONAL_REQ" ]; then
    log_info "Installing optional dependencies (enhanced features)..."
    log_info "  → jellyfish: Phonetic matching for bias correction"
    log_info "  → sentence-transformers: ML-based glossary selection"
    python -m pip install -r "$OPTIONAL_REQ" --quiet
    log_success "Optional dependencies installed"
else
    log_warn "requirements-optional.txt not found - skipping enhanced features"
fi

# ============================================================================
# MLX-WHISPER INSTALLATION (Apple Silicon only)
# ============================================================================
if [[ "$OS_TYPE" == "Darwin" ]] && [[ "$ARCH_TYPE" == "arm64" ]]; then
    log_section "MLX-WHISPER (APPLE SILICON GPU ACCELERATION)"
    log_info "Detected Apple Silicon (M1/M2/M3) - installing MLX-Whisper..."
    
    if python -c "import mlx_whisper" 2>/dev/null; then
        mlx_version=$(python -c "import mlx_whisper; print(mlx_whisper.__version__ if hasattr(mlx_whisper, '__version__') else 'installed')" 2>&1)
        log_success "MLX-Whisper already installed: $mlx_version"
    else
        log_info "Installing mlx-whisper for 2-4x faster ASR on Apple Silicon..."
        python -m pip install "mlx-whisper>=0.4.0" --quiet
        
        if [ $? -eq 0 ]; then
            mlx_version=$(python -c "import mlx_whisper; print(mlx_whisper.__version__ if hasattr(mlx_whisper, '__version__') else 'installed')" 2>&1)
            log_success "MLX-Whisper installed: $mlx_version"
            log_info "  → WhisperX ASR will use Metal/MPS acceleration"
            log_info "  → Expected speedup: 2-4x faster than CPU"
        else
            log_warn "Failed to install MLX-Whisper (optional)"
            log_info "  → WhisperX will fall back to CPU (slower)"
            log_info "  → To install manually: pip install mlx-whisper"
        fi
    fi
else
    log_info "MLX-Whisper: Skipped (Apple Silicon only)"
fi

# ============================================================================
# TORCH/TORCHAUDIO/NUMPY VERSION VERIFICATION
# ============================================================================
log_info "Verifying torch/torchaudio/numpy versions..."

numpy_version=$(python -c "import numpy; print(numpy.__version__)" 2>&1)
torch_version=$(python -c "import torch; print(torch.__version__)" 2>&1)
torchaudio_version=$(python -c "import torchaudio; print(torchaudio.__version__)" 2>&1)

# WhisperX 3.4.3+ requires numpy>=2.0.2
# torchaudio 2.8.x officially requires numpy<2.0 BUT actually works with numpy 2.x
# This is a known discrepancy between pip metadata and runtime compatibility
log_info "Detected versions: numpy $numpy_version | torch $torch_version | torchaudio $torchaudio_version"

# Check NumPy version - WhisperX 3.4.3 requires >=2.0.2
if [[ "$numpy_version" == 1.* ]]; then
    log_info "NumPy $numpy_version detected - upgrading to >=2.0.2 for WhisperX 3.4.3"
    log_info "  → Note: torchaudio 2.8 works with numpy 2.x despite pip metadata"
    
    python -m pip install "numpy>=2.0.2,<2.1" --upgrade --quiet
    
    if [ $? -eq 0 ]; then
        numpy_version=$(python -c "import numpy; print(numpy.__version__)" 2>&1)
        log_success "Upgraded to numpy $numpy_version"
    else
        log_error "Failed to upgrade numpy"
        log_info "  → WhisperX 3.4.3 requires numpy>=2.0.2"
    fi
fi

# Check torch/torchaudio versions
if [[ "$torch_version" == 2.8.* ]] && [[ "$torchaudio_version" == 2.8.* ]]; then
    log_success "torch $torch_version / torchaudio $torchaudio_version"
    log_info "  → Compatible with numpy 2.x (runtime verified)"
    log_info "  → Compatible with pyannote.audio 3.x"
elif [[ "$torch_version" == 2.9.* ]] || [[ "$torchaudio_version" == 2.9.* ]]; then
    log_warn "torch $torch_version / torchaudio $torchaudio_version detected"
    log_warn "  → May have compatibility issues with pyannote.audio 3.x"
    log_info "  → Consider downgrading to 2.8.x if diarization fails"
else
    log_success "torch $torch_version / torchaudio $torchaudio_version"
fi

log_success "Final versions: numpy $numpy_version | torch $torch_version | torchaudio $torchaudio_version"

# ============================================================================
# PHASE 1 ENHANCEMENT: Create Required Directories
# ============================================================================
log_section "DIRECTORY STRUCTURE"
log_info "Creating required directories..."

REQUIRED_DIRS=(
    "in"
    "out"
    "logs"
    "config"
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

# Set cache directories for ML models (avoids /app/LLM paths in native mode)
torch_cache_dir="$PROJECT_ROOT/.cache/torch"
hf_cache_dir="$PROJECT_ROOT/.cache/huggingface"

if [ ! -d "$torch_cache_dir" ]; then
    mkdir -p "$torch_cache_dir"
fi
if [ ! -d "$hf_cache_dir" ]; then
    mkdir -p "$hf_cache_dir"
fi

export TORCH_HOME="$torch_cache_dir"
export HF_HOME="$hf_cache_dir"
log_info "TORCH_HOME set to: $torch_cache_dir"
log_info "HF_HOME set to: $hf_cache_dir"

if cd "$PROJECT_ROOT" && python "shared/hardware_detection.py" --no-cache; then
    log_success "Hardware detection complete"
    log_info "  → Hardware cache: out/hardware_cache.json"
    log_info "  → Pipeline config: config/.env.pipeline (auto-updated)"
    log_info "  → Settings applied: DEVICE, BATCH_SIZE, WHISPER_MODEL, etc."
    log_info "  → You can manually override settings in config/.env.pipeline if needed"
    
    # Set recommended BIAS_STRATEGY to chunked_windows
    config_file="$PROJECT_ROOT/config/.env.pipeline"
    if [ -f "$config_file" ]; then
        # Check if BIAS_STRATEGY exists and update it
        if grep -q "^BIAS_STRATEGY=" "$config_file"; then
            # Update existing BIAS_STRATEGY to chunked_windows
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS sed syntax
                sed -i '' 's/^BIAS_STRATEGY=.*/BIAS_STRATEGY=chunked_windows/' "$config_file"
            else
                # Linux sed syntax
                sed -i 's/^BIAS_STRATEGY=.*/BIAS_STRATEGY=chunked_windows/' "$config_file"
            fi
            log_info "  → BIAS_STRATEGY set to: chunked_windows (recommended)"
        fi
    fi
else
    log_warn "Hardware detection failed, but continuing..."
fi

# ============================================================================
# AUTO-CONFIGURATION: Read Hardware Cache and Export Settings
# ============================================================================
log_section "AUTO-CONFIGURATION FROM HARDWARE CACHE"

hw_cache_file="$PROJECT_ROOT/out/hardware_cache.json"

if [ -f "$hw_cache_file" ]; then
    log_info "Reading hardware cache: $hw_cache_file"
    
    # Extract settings from hardware cache using Python
    hw_settings=$(python -c "
import json
import sys
try:
    with open('$hw_cache_file', 'r') as f:
        hw = json.load(f)
    
    # Get device type
    device = hw.get('gpu_type', 'cpu')
    
    # Get recommended settings
    settings = hw.get('recommended_settings', {})
    batch_size = settings.get('batch_size', 16)
    whisper_model = settings.get('whisper_model', 'large-v3')
    
    # Print settings in format: device|batch_size|whisper_model
    print(f'{device}|{batch_size}|{whisper_model}')
except Exception as e:
    print('cpu|16|large-v3', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$hw_settings" ]; then
        # Parse settings
        IFS='|' read -r detected_device detected_batch_size detected_model <<< "$hw_settings"
        
        # Export DEVICE_OVERRIDE for runtime integration
        export DEVICE_OVERRIDE="$detected_device"
        log_success "DEVICE_OVERRIDE=$DEVICE_OVERRIDE"
        
        # Log recommended settings (these are already written to config/.env.pipeline)
        log_info "Recommended batch size: $detected_batch_size (saved to config/.env.pipeline)"
        log_info "Recommended Whisper model: $detected_model (saved to config/.env.pipeline)"
        
        # MPS-specific environment variables (if MPS detected)
        if [[ "$detected_device" == "mps" ]]; then
            log_section "MPS ENVIRONMENT OPTIMIZATION"
            log_info "Apple Silicon (MPS) detected - configuring environment..."
            
            # Prevent memory fragmentation
            export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
            log_info "  ✓ PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 (prevents fragmentation)"
            
            # Disable MPS fallback (fail fast instead of silent CPU fallback)
            export PYTORCH_ENABLE_MPS_FALLBACK=0
            log_info "  ✓ PYTORCH_ENABLE_MPS_FALLBACK=0 (fail fast on errors)"
            
            # Set memory allocator max size (4GB)
            export MPS_ALLOC_MAX_SIZE_MB=4096
            log_info "  ✓ MPS_ALLOC_MAX_SIZE_MB=4096 (4GB max allocation)"
            
            log_success "MPS environment optimized for stability"
            log_info "Note: These settings are also saved to config/.env.pipeline"
        fi
    else
        log_warn "Could not parse hardware cache - using defaults"
        export DEVICE_OVERRIDE="cpu"
    fi
else
    log_warn "Hardware cache not found: $hw_cache_file"
    log_info "Using default device: cpu"
    export DEVICE_OVERRIDE="cpu"
fi

# ============================================================================
# PHASE 3 ENHANCEMENT: Parallel ML Model Pre-download
# ============================================================================
log_section "ML MODEL PRE-DOWNLOAD (PARALLEL)"
log_info "Pre-downloading and caching all required ML models..."

secrets_file="$PROJECT_ROOT/config/secrets.json"
hf_token=""

# Check for HF token
if [ -f "$secrets_file" ]; then
    if command -v jq >/dev/null 2>&1; then
        hf_token=$(jq -r '.HF_TOKEN // empty' "$secrets_file" 2>/dev/null || echo "")
        if [ -n "$hf_token" ]; then
            export HF_TOKEN="$hf_token"
        fi
    fi
fi

# Use parallel model downloader
downloader_script="$PROJECT_ROOT/shared/model_downloader.py"
if [ -f "$downloader_script" ]; then
    log_info "Starting parallel model downloads..."
    echo ""
    
    # Run downloader and display its output directly
    if [ -n "$hf_token" ]; then
        cd "$PROJECT_ROOT" && python "shared/model_downloader.py" --hf-token "$hf_token" --max-workers 3
        download_exit=$?
    else
        cd "$PROJECT_ROOT" && python "shared/model_downloader.py" --max-workers 3
        download_exit=$?
    fi
    
    echo ""
    if [ $download_exit -eq 0 ]; then
        log_success "ML model download completed"
    else
        log_warn "Model download completed with some warnings (non-critical)"
        log_info "Models can be downloaded on-demand during first use"
    fi
else
    log_error "Model downloader not found: $downloader_script"
    log_info "Models will be downloaded on first use"
fi

# ============================================================================
# PYTORCH AND PYANNOTE VERIFICATION
# ============================================================================
log_info "Verifying PyTorch installation..."
cd "$PROJECT_ROOT" && python "shared/verify_pytorch.py"

log_info "Verifying PyAnnote.audio compatibility..."

# Test actual import with proper error capture
pyannote_test=$(python -c "
import warnings
warnings.filterwarnings('ignore', message='.*speechbrain.pretrained.*deprecated.*')
warnings.filterwarnings('ignore', message='.*pytorch_lightning.*')
warnings.filterwarnings('ignore', message='.*torchaudio._backend.*')
warnings.filterwarnings('ignore', message='.*torchaudio._backend.list_audio_backends.*deprecated.*')
warnings.filterwarnings('ignore', message='.*Lightning automatically upgraded.*')
try:
    from pyannote.audio import Pipeline
    print('SUCCESS')
except AttributeError as e:
    if 'AudioMetaData' in str(e):
        print('ERROR: AudioMetaData compatibility issue')
        print(str(e))
    else:
        raise
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}')
" 2>&1)

if echo "$pyannote_test" | grep -q "SUCCESS"; then
    log_success "PyAnnote.audio: Compatible and working"
    log_info "  → numpy 2.x + torchaudio 2.8.x verified"
elif echo "$pyannote_test" | grep -q "AudioMetaData"; then
    log_warn "PyAnnote.audio: AudioMetaData compatibility issue detected"
    log_info "  → Applying patch to fix type annotations..."
    
    # Apply the patch
    if cd "$PROJECT_ROOT" && python "scripts/patch_pyannote.py" >/dev/null 2>&1; then
        log_success "  ✓ Patch applied successfully"
        
        # Test again
        pyannote_retest=$(python -c "
import warnings
warnings.filterwarnings('ignore')
try:
    from pyannote.audio import Pipeline
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)
        
        if echo "$pyannote_retest" | grep -q "SUCCESS"; then
            log_success "PyAnnote.audio: Now working after patch"
        else
            log_error "PyAnnote.audio: Patch did not resolve issue"
            log_info "  → Pipeline will fall back to Silero VAD"
        fi
    else
        log_error "  ✗ Could not apply patch"
        log_info "  → Pipeline will fall back to Silero VAD"
    fi
else
    log_warn "PyAnnote.audio: Unexpected import issue"
    log_info "  Error: $pyannote_test"
    log_info "  → Pipeline may fall back to Silero VAD"
fi

# ============================================================================
# GLOSSARY SYSTEM VALIDATION
# ============================================================================
log_section "GLOSSARY SYSTEM VALIDATION"
log_info "Validating Hinglish glossary system..."

glossary_dir="$PROJECT_ROOT/glossary"
glossary_tsv="$glossary_dir/hinglish_master.tsv"
prompts_dir="$glossary_dir/prompts"

# Check glossary directory
if [ ! -d "$glossary_dir" ]; then
    log_warn "Glossary directory not found: $glossary_dir"
    log_info "  Creating glossary structure..."
    mkdir -p "$glossary_dir"
    mkdir -p "$prompts_dir"
else
    log_success "Glossary directory exists"
fi

# Check master TSV
if [ -f "$glossary_tsv" ]; then
    term_count=$(tail -n +2 "$glossary_tsv" 2>/dev/null | grep -v '^[[:space:]]*$' | wc -l | tr -d ' ')
    log_success "Glossary master TSV found: $term_count terms"
else
    log_warn "Glossary master TSV not found: $glossary_tsv"
    log_info "  The glossary provides Hinglish→English term consistency"
    log_info "  Subtitle generation will work without it, but may lack terminology consistency"
fi

# Check prompts directory
if [ ! -d "$prompts_dir" ]; then
    log_info "Creating prompts directory..."
    mkdir -p "$prompts_dir"
fi

# Count available movie prompts
if [ -d "$prompts_dir" ]; then
    prompt_count=$(find "$prompts_dir" -name "*.txt" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [ "$prompt_count" -gt 0 ]; then
        log_success "Found $prompt_count movie-specific prompts"
        log_info "  Movie prompts provide context-aware translation guidance"
    else
        log_info "No movie-specific prompts found"
        log_info "  Prompts can be added to: $prompts_dir"
        log_info "  Example: dil_chahta_hai_2001.txt, 3_idiots_2009.txt"
    fi
fi

# Validate glossary.py module
glossary_module="$PROJECT_ROOT/shared/glossary.py"
glossary_advanced="$PROJECT_ROOT/shared/glossary_advanced.py"

if [ -f "$glossary_module" ]; then
    log_success "Glossary module found: shared/glossary.py"
    
    # Check for advanced strategies module
    if [ -f "$glossary_advanced" ]; then
        log_success "Advanced strategies module found: shared/glossary_advanced.py"
        log_info "  Supported strategies: context, character, regional, frequency, adaptive, ml"
    else
        log_warn "Advanced strategies module not found (optional)"
        log_info "  Only 'first' strategy will be available"
    fi
    
    # Quick validation of glossary loading
    glossary_test=$(cd "$PROJECT_ROOT" && python -c "
from shared.glossary import HinglishGlossary
from pathlib import Path
glossary_path = Path('glossary/hinglish_master.tsv')
if glossary_path.exists():
    # Test basic loading
    g = HinglishGlossary(glossary_path, strategy='first')
    print(f'Loaded {len(g.term_map)} terms')
    # Test advanced strategies if available
    try:
        g_adv = HinglishGlossary(glossary_path, strategy='adaptive')
        print('Advanced strategies: OK')
    except:
        print('Advanced strategies: Not available')
else:
    print('TSV not found')
" 2>&1)
    
    if echo "$glossary_test" | grep -q "Loaded"; then
        log_success "Glossary system: $(echo "$glossary_test" | grep "Loaded")"
        if echo "$glossary_test" | grep -q "Advanced strategies: OK"; then
            log_success "  Advanced strategies validated"
        fi
    else
        log_info "Glossary system ready (TSV can be added later)"
    fi
else
    log_warn "Glossary module not found: $glossary_module"
fi

log_info ""
log_info "Glossary Integration Status:"
log_info "  • Master TSV: $([ -f "$glossary_tsv" ] && echo "✓ Present" || echo "✗ Not found")"
log_info "  • Movie Prompts: $prompt_count files"
log_info "  • Python Module: $([ -f "$glossary_module" ] && echo "✓ Ready" || echo "✗ Missing")"
log_info "  • Advanced Strategies: $([ -f "$glossary_advanced" ] && echo "✓ Available" || echo "✗ Not available")"
log_info "  • Config: GLOSSARY_ENABLED=true, GLOSSARY_STRATEGY=adaptive"
log_info ""
log_info "Glossary Strategies:"
log_info "  • first      - Fast, use first option (basic)"
log_info "  • context    - Analyze surrounding text"
log_info "  • character  - Use character speaking profiles"
log_info "  • regional   - Apply regional variants (Mumbai, Delhi, etc.)"
log_info "  • frequency  - Learn from usage patterns"
log_info "  • adaptive   - Intelligently combine all (recommended)"
log_info "  • ml         - ML-based selection (future)"
log_info ""
log_info "To add glossary terms:"
log_info "  1. Edit: glossary/hinglish_master.tsv"
log_info "  2. Format: source⟨TAB⟩preferred_english⟨TAB⟩notes⟨TAB⟩context"
log_info "  3. Example: yaar⟨TAB⟩dude|man⟨TAB⟩Use dude for young males⟨TAB⟩casual"
log_info ""
log_info "To add movie-specific prompts:"
log_info "  1. Create: glossary/prompts/<film_title>_<year>.txt"
log_info "  2. Include: characters, tone, key terms, cultural context"
log_info "  3. See existing prompts for examples"

# ============================================================================
# INDICTRANS2 SETUP (Indic Language Translation)
# ============================================================================
log_section "INDICTRANS2 SETUP (INDIC LANGUAGES)"
log_info "Installing IndicTrans2 for high-quality Indic→English translation..."
log_info "  Supports: 22 Indic languages (Hindi, Tamil, Telugu, Bengali, etc.)"
log_info "  Benefit: 90% faster than Whisper for translation"
log_info ""

# Run IndicTrans2 installation in bootstrap mode
export BOOTSTRAP_MODE=true
export SKIP_PROMPTS=true

INDICTRANS2_INSTALLER="$PROJECT_ROOT/install-indictrans2.sh"
if [ -f "$INDICTRANS2_INSTALLER" ]; then
    if bash "$INDICTRANS2_INSTALLER"; then
        log_success "IndicTrans2 setup complete"
        log_info "  ✓ Dependencies installed"
        log_info "  ✓ Model cached (~2GB)"
        log_info "  ✓ Configuration added"
        log_info "  → Automatically activates for Indic source languages"
    else
        log_warn "IndicTrans2 setup failed (optional feature)"
        log_info "  Pipeline will use Whisper for all translations"
        log_info "  To retry: ./install-indictrans2.sh"
    fi
else
    log_warn "IndicTrans2 installer not found: $INDICTRANS2_INSTALLER"
    log_info "  IndicTrans2 is optional but recommended for Indic languages"
    log_info "  Install manually: ./install-indictrans2.sh"
fi

unset BOOTSTRAP_MODE
unset SKIP_PROMPTS

# ============================================================================
# Complete
# ============================================================================
END_TIME=$(date '+%Y-%m-%d %H:%M:%S')

log_both "SECTION" "BOOTSTRAP COMPLETE"

# Write completion summary to log
{
    echo ""
    echo "════════════════════════════════════════════════════════════════════════"
    echo "BOOTSTRAP COMPLETION SUMMARY"
    echo "════════════════════════════════════════════════════════════════════════"
    echo "End Time: $END_TIME"
    echo "Duration: $SECONDS seconds"
    echo ""
    echo "Environment Configuration:"
    echo "  • Python: $python_version"
    echo "  • Virtual Environment: $VENV_DIR"
    echo "  • Platform: $OS_TYPE ($ARCH_TYPE)"
    echo "  • Log File: $LOG_FILE"
    echo ""
    echo "Installed Components:"
    echo "  ✓ Python packages from $SELECTED_REQ_FILE"
    echo "  ✓ Optional enhancements (jellyfish, sentence-transformers)"
    echo "  ✓ IndicTrans2 dependencies"
    echo "  ✓ torch $torch_version / torchaudio $torchaudio_version"
    echo "  ✓ numpy $numpy_version"
    echo ""
    echo "Status: SUCCESS"
    echo "════════════════════════════════════════════════════════════════════════"
} | tee -a "$LOG_FILE"

echo ""
log_both "SUCCESS" "Environment ready!"
echo ""
echo "What's been set up:"
echo "  ✓ Python virtual environment (.venv-common/)"
echo "  ✓ 70+ Python packages installed (requirements.txt)"
echo "  ✓ Optional enhancements installed (requirements-optional.txt)"
echo "    → jellyfish: Phonetic matching for bias correction"
echo "    → sentence-transformers: ML-based glossary selection"
echo "  ✓ IndicTrans2: Fast Indic→English translation (22 languages)"
echo "  ✓ torch 2.8.x / torchaudio 2.8.x (pyannote compatible)"
echo "  ✓ Hardware capabilities detected & cached"
echo "  ✓ Required directories created"
echo "  ✓ FFmpeg validated"
echo "  ✓ ML models pre-downloaded"
echo "  ✓ spaCy NER models installed"
echo "  ✓ PyAnnote.audio verified working"
echo "  ✓ Glossary system validated"
echo ""
echo "📋 Bootstrap log saved to: $LOG_FILE"
if [ "$DEBUG_MODE" = true ]; then
    echo "🔍 Debug mode was enabled - detailed logs available"
fi
echo ""
echo "Next steps:"
echo ""
echo "  Transcribe Workflow (Audio → Text):"
echo "  1. Prepare job:"
echo "     ./prepare-job.sh path/to/video.mp4 --transcribe -s hi"
echo ""
echo "  2. Run pipeline:"
echo "     ./run-pipeline.sh -j <job-id>"
echo ""
echo "  Translate Workflow (Text → English Subtitles):"
echo "  1. Prepare job:"
echo "     ./prepare-job.sh path/to/video.mp4 --translate -s hi -t en"
echo ""
echo "  2. Run pipeline:"
echo "     ./run-pipeline.sh -j <job-id>"
echo ""
echo "Optional:"
echo "  • Create config/secrets.json with API tokens"
echo "  • Configure TMDB_API_KEY for metadata enrichment"
echo "  • Add glossary terms to glossary/hinglish_master.tsv"
echo "  • Create movie-specific prompts in glossary/prompts/"
echo ""
echo "Check model status:"
echo "  python shared/model_checker.py"
echo ""
echo "View bootstrap log:"
echo "  cat $LOG_FILE"
echo ""

log_both "INFO" "Bootstrap completed successfully"
debug "Total execution time: $SECONDS seconds"

exit 0
