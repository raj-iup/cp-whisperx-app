#!/bin/bash
# Creates isolated virtual environments for each pipeline stage

set -e
source scripts/common-logging.sh

VENV_DIR="native/venvs"
REQ_DIR="native/requirements"
PYTHON_CMD="python3"

log_section "MPS Native Pipeline - Virtual Environment Setup"

# Check Python version
log_info "Checking Python version..."
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
log_info "Using: $PYTHON_VERSION"

if ! command -v $PYTHON_CMD &> /dev/null; then
    log_error "Python 3 not found! Please install Python 3.9+"
    exit 1
fi

# Stages list
stages=("demux" "tmdb" "pre-ner" "silero-vad" "pyannote-vad" 
        "diarization" "asr" "post-ner" "subtitle-gen" "mux")

total=${#stages[@]}
current=0

for stage in "${stages[@]}"; do
    current=$((current + 1))
    log_info "[$current/$total] Creating venv for $stage..."
    
    venv_path="$VENV_DIR/$stage"
    req_file="$REQ_DIR/${stage//-/_}.txt"
    
    # Create virtual environment
    if [ -d "$venv_path" ]; then
        log_warn "  venv already exists, skipping creation"
    else
        $PYTHON_CMD -m venv "$venv_path"
        log_success "  venv created"
    fi
    
    # Install requirements if file exists and has content
    if [ -f "$req_file" ] && [ -s "$req_file" ]; then
        # Check if requirements file has actual dependencies (not just comments)
        if grep -q "^[^#]" "$req_file"; then
            log_info "  Installing requirements..."
            "$venv_path/bin/pip" install --quiet --upgrade pip setuptools wheel
            "$venv_path/bin/pip" install --quiet -r "$req_file"
            log_success "  $stage ready with dependencies"
        else
            log_info "  No requirements (system tools only)"
        fi
    else
        log_info "  No requirements file"
    fi
done

log_section "Setup Complete!"
log_success "All virtual environments created successfully"
log_info "Total stages: $total"
log_info "Location: $VENV_DIR/"
