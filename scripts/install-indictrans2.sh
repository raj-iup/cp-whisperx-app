#!/bin/bash
# install-indictrans2.sh - Install IndicTrans2 dependencies and cache models
# 
# ⚠️  DEPRECATED: This script is no longer needed
# 
# IndicTrans2 is now automatically installed by bootstrap.sh in the venv/indictrans2 environment
# 
# RECOMMENDED ACTION:
#   Just run: ./bootstrap.sh
# 
# This will:
#   1. Create venv/indictrans2 virtual environment
#   2. Install IndicTrans2 dependencies automatically
#   3. Configure HuggingFace authentication (interactive)
# 
# This script is kept for backward compatibility but simply forwards to bootstrap

set -e  # Exit on error

# Load common logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/scripts/common-logging.sh" ]]; then
    source "$SCRIPT_DIR/scripts/common-logging.sh"
else
    # Fallback logging functions
    log_section() { echo ""; echo "━━━ $1 ━━━"; }
    log_info() { echo "  $1"; }
    log_success() { echo "✓ $1"; }
    log_warn() { echo "⚠️  $1"; }
    log_error() { echo "✗ $1"; }
fi

log_section "INDICTRANS2 INSTALLATION (DEPRECATED)"

log_warn "This script is deprecated and no longer necessary"
log_info "IndicTrans2 is now automatically installed by ./bootstrap.sh"
echo ""

# Check if venv/indictrans2 already exists
if [ -d "$SCRIPT_DIR/venv/indictrans2" ]; then
    log_success "IndicTrans2 environment already exists at venv/indictrans2"
    log_info "To recreate, run: rm -rf venv/indictrans2 && ./bootstrap.sh"
    exit 0
fi

# Check if bootstrap has been run
if [ ! -f "$SCRIPT_DIR/config/hardware_cache.json" ]; then
    log_error "Bootstrap has not been run yet"
    log_info "Please run ./bootstrap.sh first to create all environments"
    exit 1
fi

log_info "IndicTrans2 environment not found - running bootstrap..."
log_info "This will create the venv/indictrans2 environment"
echo ""

# Forward to bootstrap - it will create all missing environments
exec "$SCRIPT_DIR/bootstrap.sh"

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

# Check HuggingFace Authentication
log_section "HuggingFace Authentication"

# Check if user is logged in
HF_TOKEN_EXISTS=false
if python -c "from huggingface_hub import HfFolder; token = HfFolder.get_token(); exit(0 if token else 1)" 2>/dev/null; then
    HF_TOKEN_EXISTS=true
    log_success "HuggingFace authentication found"
else
    log_warn "HuggingFace authentication not found"
    log_info ""
    log_info "IndicTrans2 model (ai4bharat/indictrans2-indic-en-1B) is gated and requires:"
    log_info "  1. HuggingFace account"
    log_info "  2. Model access request approval"
    log_info "  3. Authentication token"
    log_info ""
    
    if [[ "$SKIP_PROMPTS" == "false" ]] && [[ "$BOOTSTRAP_MODE" != "true" ]]; then
        log_info "To setup HuggingFace authentication:"
        log_info "  1. Create account at https://huggingface.co/join"
        log_info "  2. Request access at https://huggingface.co/ai4bharat/indictrans2-indic-en-1B"
        log_info "  3. Create token at https://huggingface.co/settings/tokens"
        log_info "  4. Run: huggingface-cli login"
        echo ""
        
        read -p "Do you want to authenticate now? (y/n) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Starting HuggingFace authentication..."
            huggingface-cli login
            
            # Verify authentication
            if python -c "from huggingface_hub import HfFolder; token = HfFolder.get_token(); exit(0 if token else 1)" 2>/dev/null; then
                HF_TOKEN_EXISTS=true
                log_success "HuggingFace authentication successful"
            else
                log_error "Authentication failed"
            fi
        else
            log_warn "Skipping authentication"
            log_info "IndicTrans2 will not be functional without authentication"
        fi
    else
        # In bootstrap mode, provide instructions
        log_info "To enable IndicTrans2, authenticate with HuggingFace:"
        log_info "  1. Visit https://huggingface.co/ai4bharat/indictrans2-indic-en-1B"
        log_info "  2. Click 'Agree and access repository'"
        log_info "  3. Run: huggingface-cli login"
        log_info "  4. Run: ./install-indictrans2.sh"
    fi
fi

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
    if [[ "$HF_TOKEN_EXISTS" == "false" ]]; then
        log_error "Cannot download model without HuggingFace authentication"
        log_info "Please authenticate first:"
        log_info "  1. Visit https://huggingface.co/ai4bharat/indictrans2-indic-en-1B"
        log_info "  2. Click 'Agree and access repository'"
        log_info "  3. Run: huggingface-cli login"
        log_info "  4. Re-run this script"
        
        if [[ "$BOOTSTRAP_MODE" != "true" ]]; then
            exit 1
        else
            log_warn "Continuing bootstrap (IndicTrans2 will not be functional)"
        fi
    else
        log_info "Downloading and caching model (this may take a few minutes)..."
        
        # Run test which will download the model
        cd "$(dirname "$0")"
        
        if python scripts/test_indictrans2.py 2>&1 | tee /tmp/indictrans2_test.log; then
            log_success "IndicTrans2 model downloaded and cached"
            log_success "Model ready for use"
        else
            # Check if it's an authentication error
            if grep -q "gated repo\|401\|Unauthorized" /tmp/indictrans2_test.log; then
                log_error "Authentication error detected"
                log_info "The model requires access approval from AI4Bharat"
                log_info "Steps to fix:"
                log_info "  1. Visit https://huggingface.co/ai4bharat/indictrans2-indic-en-1B"
                log_info "  2. Click 'Agree and access repository'"
                log_info "  3. Wait for approval (usually instant)"
                log_info "  4. Re-run this script"
            else
                log_error "Model download/test failed"
                log_info "Check /tmp/indictrans2_test.log for details"
            fi
            
            if [[ "$BOOTSTRAP_MODE" == "true" ]]; then
                log_warn "Continuing bootstrap (IndicTrans2 optional)"
            else
                exit 1
            fi
        fi
    fi
else
    log_info "Skipping model download"
    log_info "Model will be downloaded on first use (requires authentication)"
    if [[ "$HF_TOKEN_EXISTS" == "false" ]]; then
        log_warn "Remember to authenticate with HuggingFace before using IndicTrans2"
    fi
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
    if [[ "$HF_TOKEN_EXISTS" == "true" ]]; then
        log_success "IndicTrans2 is ready for use"
        log_info "Supported: 22 Indic languages → English"
        log_info "Usage: Automatically activated for Indic source languages"
        log_info "Citation: Gala et al. (2023) - See docs/CITATIONS.md"
    else
        log_warn "IndicTrans2 dependencies installed but requires authentication"
        log_info "To enable: huggingface-cli login"
        log_info "Then visit: https://huggingface.co/ai4bharat/indictrans2-indic-en-1B"
        log_info "Citation: See docs/CITATIONS.md for proper attribution"
    fi
else
    echo ""
    if [[ "$HF_TOKEN_EXISTS" == "true" ]]; then
        echo "✅ IndicTrans2 is ready to use!"
    else
        echo "⚠️  IndicTrans2 dependencies installed (authentication required)"
    fi
    echo ""
    echo "What's been configured:"
    echo "  ✓ Dependencies installed (sentencepiece, sacremoses, srt, transformers)"
    echo "  ✓ IndicTransToolkit installed (optional, recommended)"
    
    if [[ "$HF_TOKEN_EXISTS" == "true" ]]; then
        echo "  ✓ HuggingFace authenticated"
        echo "  ✓ Model cached (~2GB in ~/.cache/huggingface/)"
    else
        echo "  ⚠️  HuggingFace authentication required"
        echo "  ⚠️  Model not downloaded (requires auth)"
    fi
    
    echo "  ✓ Configuration added to config/.env.pipeline"
    echo ""
    
    if [[ "$HF_TOKEN_EXISTS" == "false" ]]; then
        echo "⚠️  IMPORTANT: Authentication Required"
        echo ""
        echo "IndicTrans2 model is gated and requires HuggingFace authentication:"
        echo "  1. Create account: https://huggingface.co/join"
        echo "  2. Request access: https://huggingface.co/ai4bharat/indictrans2-indic-en-1B"
        echo "     (Click 'Agree and access repository')"
        echo "  3. Authenticate: huggingface-cli login"
        echo "  4. Re-run: ./install-indictrans2.sh"
        echo ""
    fi
    
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
    
    if [[ "$HF_TOKEN_EXISTS" == "true" ]]; then
        echo "  1. Process Indic language content:"
        echo "     ./prepare-job.sh movie.mp4 --source-language hi --target-language en"
        echo ""
        echo "  2. Check logs for IndicTrans2 usage:"
        echo "     grep 'Using IndicTrans2' out/*/rpatel/*/logs/pipeline.log"
    else
        echo "  1. Authenticate with HuggingFace (see above)"
        echo "  2. Process Indic language content:"
        echo "     ./prepare-job.sh movie.mp4 --source-language hi --target-language en"
    fi
    echo ""
    echo "Documentation:"
    echo "  • Quick Start: docs/INDICTRANS2_QUICKSTART.md"
    echo "  • Full Guide:  docs/INDICTRANS2_IMPLEMENTATION.md"
    echo "  • Citations:   docs/CITATIONS.md"
    echo ""
    echo "📚 Citation:"
    echo "  If you use IndicTrans2 in your work, please cite:"
    echo "  Gala et al. (2023) - IndicTrans2: Towards High-Quality and"
    echo "  Accessible Machine Translation Models for all 22 Scheduled"
    echo "  Indian Languages. See docs/CITATIONS.md for BibTeX."
    echo ""
fi

exit 0
