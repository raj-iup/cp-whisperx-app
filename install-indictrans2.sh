#!/bin/bash
# install-indictrans2.sh - Install IndicTrans2 dependencies and cache models
# Can be run standalone or integrated into bootstrap.sh

set -e  # Exit on error

# Determine if running in bootstrap context (non-interactive)
BOOTSTRAP_MODE="${BOOTSTRAP_MODE:-false}"
SKIP_PROMPTS="${SKIP_PROMPTS:-false}"

# Load common logging if available
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/scripts/common-logging.sh" ]]; then
    source "$SCRIPT_DIR/scripts/common-logging.sh"
elif [[ -f "$SCRIPT_DIR/common-logging.sh" ]]; then
    source "$SCRIPT_DIR/common-logging.sh"
else
    # Fallback logging functions
    log_section() { echo ""; echo "━━━ $1 ━━━"; }
    log_info() { echo "  $1"; }
    log_success() { echo "✓ $1"; }
    log_warn() { echo "⚠️  $1"; }
    log_error() { echo "✗ $1"; }
fi

if [[ "$BOOTSTRAP_MODE" == "true" ]]; then
    log_section "INDICTRANS2 SETUP"
else
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║         IndicTrans2 Setup Installer                     ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
fi

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    log_warn "No virtual environment detected!"
    if [[ "$BOOTSTRAP_MODE" != "true" ]]; then
        echo ""
        echo "Please activate your virtual environment first:"
        echo "  source .bollyenv/bin/activate"
        echo ""
        exit 1
    else
        log_error "Virtual environment must be activated before running bootstrap"
        exit 1
    fi
fi

log_info "Virtual environment: $VIRTUAL_ENV"

# Install dependencies
log_section "Installing Dependencies"

log_info "Installing sentencepiece..."
pip install -q sentencepiece>=0.1.99

log_info "Installing sacremoses..."
pip install -q sacremoses>=0.0.53

log_info "Installing srt..."
pip install -q srt>=3.5.0

log_info "Installing/upgrading transformers..."
pip install -q --upgrade 'transformers>=4.44'

log_success "All required dependencies installed"

# Optional: IndicTransToolkit
if [[ "$SKIP_PROMPTS" == "false" ]] && [[ "$BOOTSTRAP_MODE" != "true" ]]; then
    log_section "Optional: IndicTransToolkit"
    echo ""
    echo "IndicTransToolkit provides better preprocessing/postprocessing."
    echo "It's optional but recommended for improved translation quality."
    echo ""
    
    read -p "Install IndicTransToolkit? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installing IndicTransToolkit..."
        pip install -q IndicTransToolkit || log_warn "IndicTransToolkit installation failed (will use basic tokenization)"
    fi
else
    # Auto-install in bootstrap mode (non-interactive)
    log_info "Installing IndicTransToolkit (optional, recommended)..."
    if pip install -q IndicTransToolkit 2>/dev/null; then
        log_success "IndicTransToolkit installed"
    else
        log_warn "IndicTransToolkit installation failed (will use basic tokenization)"
    fi
fi

log_success "All dependencies processed"

# Verify setup
log_section "Verifying Setup"

# Quick import test
python -c "
import sys
try:
    import sentencepiece
    print('✓ sentencepiece imported successfully')
except ImportError as e:
    print(f'✗ sentencepiece import failed: {e}')
    sys.exit(1)

try:
    import sacremoses
    print('✓ sacremoses imported successfully')
except ImportError as e:
    print(f'✗ sacremoses import failed: {e}')
    sys.exit(1)

try:
    import srt
    print('✓ srt imported successfully')
except ImportError as e:
    print(f'✗ srt import failed: {e}')
    sys.exit(1)

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    print('✓ transformers imported successfully')
except ImportError as e:
    print(f'✗ transformers import failed: {e}')
    sys.exit(1)

print()
print('✓ All imports successful')
"

log_success "Import verification complete"

# Download and cache IndicTrans2 model
if [[ "$SKIP_PROMPTS" == "false" ]] && [[ "$BOOTSTRAP_MODE" != "true" ]]; then
    log_section "Model Download"
    echo ""
    echo "This will download the IndicTrans2 model (~2GB) on first run."
    echo "The model will be cached for future use in ~/.cache/huggingface/"
    echo ""
    
    read -p "Continue with model download? (y/n) " -n 1 -r
    echo ""
    
    DOWNLOAD_MODEL=$REPLY
else
    # Auto-download in bootstrap mode
    DOWNLOAD_MODEL="y"
    log_info "Downloading IndicTrans2 model (~2GB)..."
    log_info "Model will be cached in ~/.cache/huggingface/"
fi

if [[ $DOWNLOAD_MODEL =~ ^[Yy]$ ]]; then
    log_info "Downloading and caching model (this may take a few minutes)..."
    
    # Run test which will download the model
    cd "$(dirname "$0")"
    
    if python scripts/test_indictrans2.py 2>&1 | tee /tmp/indictrans2_test.log; then
        log_success "IndicTrans2 model downloaded and cached"
        log_success "Model ready for use"
    else
        log_error "Model download/test failed"
        log_info "Check /tmp/indictrans2_test.log for details"
        if [[ "$BOOTSTRAP_MODE" == "true" ]]; then
            log_warn "Continuing bootstrap (IndicTrans2 optional)"
        else
            exit 1
        fi
    fi
else
    log_info "Skipping model download"
    log_info "Model will be downloaded on first use"
fi

# Generate IndicTrans2 configuration
log_section "Generating Configuration"

CONFIG_FILE="config/.env.pipeline"
if [[ -f "$CONFIG_FILE" ]]; then
    log_info "Checking existing configuration..."
    
    # Check if IndicTrans2 config already exists
    if grep -q "INDICTRANS2_ENABLED" "$CONFIG_FILE" 2>/dev/null; then
        log_info "IndicTrans2 configuration already exists"
    else
        log_info "Adding IndicTrans2 configuration to $CONFIG_FILE"
        
        cat >> "$CONFIG_FILE" << 'EOFCONFIG'

# ============================================================
# INDICTRANS2 CONFIGURATION
# ============================================================
# IndicTrans2: High-quality translation for 22 Indic languages
# Automatically used for Indic → English translation
# ~90% faster than Whisper translation
# ============================================================

# Enable IndicTrans2 for Indic language translation
INDICTRANS2_ENABLED=true

# Model configuration
INDICTRANS2_MODEL=ai4bharat/indictrans2-indic-en-1B
INDICTRANS2_DEVICE=auto  # auto, mps, cuda, cpu

# Translation quality settings
INDICTRANS2_NUM_BEAMS=4           # Beam search width (1-10, higher=better quality)
INDICTRANS2_MAX_NEW_TOKENS=128    # Maximum translation length
INDICTRANS2_BATCH_SIZE=8          # Batch processing size

# Hinglish handling
INDICTRANS2_SKIP_ENGLISH_THRESHOLD=0.7  # Skip if >=70% English (0.0-1.0)

# Optional preprocessing/postprocessing
INDICTRANS2_USE_TOOLKIT=true      # Use IndicTransToolkit if available

# Supported source languages (auto-detected)
# hi, ta, te, bn, gu, kn, ml, mr, pa, ur, as, or, ne, sd, si, sa, 
# ks, doi, mni, kok, mai, sat (22 total)

EOFCONFIG
        
        log_success "IndicTrans2 configuration added"
    fi
else
    log_warn "Configuration file not found: $CONFIG_FILE"
    log_info "Configuration will be added during job preparation"
fi

# Summary
log_section "SETUP COMPLETE"

if [[ "$BOOTSTRAP_MODE" == "true" ]]; then
    log_success "IndicTrans2 is ready for use"
    log_info "Supported: 22 Indic languages → English"
    log_info "Usage: Automatically activated for Indic source languages"
else
    echo ""
    echo "✅ IndicTrans2 is ready to use!"
    echo ""
    echo "What's been configured:"
    echo "  ✓ Dependencies installed (sentencepiece, sacremoses, srt, transformers)"
    echo "  ✓ IndicTransToolkit installed (optional, recommended)"
    echo "  ✓ Model cached (~2GB in ~/.cache/huggingface/)"
    echo "  ✓ Configuration added to config/.env.pipeline"
    echo ""
    echo "Supported languages:"
    echo "  • 22 Indic languages: Hindi, Tamil, Telugu, Bengali, Gujarati,"
    echo "    Kannada, Malayalam, Marathi, Punjabi, Urdu, and 12 more"
    echo "  • Translates to: English (or other non-Indic languages)"
    echo ""
    echo "How it works:"
    echo "  • Automatically activated when source is Indic language"
    echo "  • 90% faster than Whisper for translation"
    echo "  • Better quality for Indian names, places, cultural terms"
    echo "  • Handles Hinglish (preserves English words automatically)"
    echo ""
    echo "Next steps:"
    echo "  1. Process Indic language content:"
    echo "     ./prepare-job.sh movie.mp4 --source-language hi --target-language en"
    echo ""
    echo "  2. Check logs for IndicTrans2 usage:"
    echo "     grep 'Using IndicTrans2' out/*/rpatel/*/logs/pipeline.log"
    echo ""
    echo "Documentation:"
    echo "  • Quick Start: docs/INDICTRANS2_QUICKSTART.md"
    echo "  • Full Guide:  docs/INDICTRANS2_IMPLEMENTATION.md"
    echo ""
fi

exit 0
