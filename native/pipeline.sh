#!/bin/bash
# MPS-optimized native pipeline orchestrator

set -e
source scripts/common-logging.sh

INPUT_FILE="$1"
OUTPUT_ROOT="./out"
VENV_DIR="native/venvs"
SCRIPT_DIR="native/scripts"

# Validate input
if [ -z "$INPUT_FILE" ]; then
    log_error "Usage: $0 <input_video.mp4>"
    echo "Example: $0 'in/movie.mp4'"
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    log_error "Input file not found: $INPUT_FILE"
    exit 1
fi

# Extract movie directory name
MOVIE_NAME=$(basename "$INPUT_FILE" | sed 's/\.[^.]*$//' | sed 's/ /_/g')
MOVIE_DIR="$OUTPUT_ROOT/$MOVIE_NAME"
mkdir -p "$MOVIE_DIR"

log_section "MPS Native Pipeline"
log_info "Input: $INPUT_FILE"
log_info "Output: $MOVIE_DIR"
log_info "Mode: Sequential execution with MPS GPU acceleration"

# Stage definitions: name:script:description
stages=(
    "demux:01_demux.py:Audio extraction"
    "tmdb:02_tmdb.py:Metadata fetch"
    "pre-ner:03_pre_ner.py:Entity extraction"
    "silero-vad:04_silero_vad.py:Coarse VAD"
    "pyannote-vad:05_pyannote_vad.py:Refined VAD"
    "diarization:06_diarization.py:Speaker labeling"
    "asr:07_asr.py:Transcription + translation"
    "post-ner:08_post_ner.py:Entity correction"
    "subtitle-gen:09_subtitle_gen.py:Subtitle generation"
    "mux:10_mux.py:Video muxing"
)

total=${#stages[@]}
current=0

# Run stages sequentially
for stage_info in "${stages[@]}"; do
    IFS=: read -r stage_name script_name description <<< "$stage_info"
    current=$((current + 1))
    
    log_section "Stage $current/$total: $stage_name"
    log_info "$description"
    
    venv_path="$VENV_DIR/${stage_name}"
    script_path="$SCRIPT_DIR/$script_name"
    
    # Validate venv exists
    if [ ! -d "$venv_path" ]; then
        log_error "Virtual environment not found: $venv_path"
        log_error "Run ./native/setup_venvs.sh first"
        exit 1
    fi
    
    # Validate script exists
    if [ ! -f "$script_path" ]; then
        log_error "Script not found: $script_path"
        exit 1
    fi
    
    # Activate venv and run stage
    start_time=$(date +%s)
    
    (
        source "$venv_path/bin/activate"
        export PYTHONPATH="$PWD:$PWD/shared:$PWD/native/utils:$PYTHONPATH"
        
        python "$script_path" \
            --input "$INPUT_FILE" \
            --movie-dir "$MOVIE_DIR"
    )
    
    exit_code=$?
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    if [ $exit_code -eq 0 ]; then
        log_success "$stage_name completed in ${duration}s"
    else
        log_failure "$stage_name failed after ${duration}s"
        log_error "Pipeline stopped at stage $current/$total"
        exit 1
    fi
done

log_section "Pipeline Complete!"
log_success "All $total stages completed successfully"
log_info "Output directory: $MOVIE_DIR"
