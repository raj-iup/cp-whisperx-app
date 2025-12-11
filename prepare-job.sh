#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# CP-WhisperX-App Job Preparation
# ============================================================================
# Version: 2.0.0
# Date: 2025-11-25
#
# Creates job directory structure and configuration for pipeline execution.
# Delegates to Python implementation for complex logic.
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
PREPARE_JOB_SCRIPT="$SCRIPT_DIR/prepare-job.py"

# Show usage
show_usage() {
    cat << 'USAGE_EOF'
Usage: ./prepare-job.sh [OPTIONS]

Create a job configuration for the pipeline

REQUIRED OPTIONS:
  --media FILE|URL              Input media file or YouTube URL
  --workflow MODE               Workflow: transcribe|translate|subtitle
  -s, --source-language CODE    Source language (hi, ta, te, etc.)

OPTIONAL OPTIONS:
  -t, --target-language CODE(S) Target language(s), comma-separated
                                Example: en,gu,ta (max 5 languages)
  --start-time HH:MM:SS         Clip start time (for testing)
  --end-time HH:MM:SS           Clip end time (for testing)
  --two-step                    Enable two-step transcription (Phase 2)
  --no-cache                    Force regeneration (skip cached baseline)
  --user-id ID                  User ID (default: 1). User must exist in users/{userId}/
  --log-level LEVEL             Log level: DEBUG|INFO|WARN|ERROR|CRITICAL
  --debug                       Enable debug mode (same as --log-level DEBUG)
  --tmdb-title "Movie Title"    TMDB movie title (for YouTube videos of movies)
  --tmdb-year YEAR              TMDB release year (improves accuracy)
  -h, --help                    Show this help message

WORKFLOW MODES:
  transcribe  - Speech-to-text only (fastest)
  translate   - Transcribe + translate (requires -t)
  subtitle    - Full pipeline with SRT generation (requires -t)

YOUTUBE INTEGRATION:
  • Pass YouTube URL directly to --media parameter
  • Auto-downloads to in/online/ directory BEFORE pipeline execution
  • Smart caching: reuses downloaded file if video_id matches
  • Uses YouTube Premium credentials from user profile (if configured)
  • Filename format: {sanitized_title}_{video_id}.mp4 (35 char title max)
  • Pipeline stages process the downloaded local file (not the URL)

TMDB FOR YOUTUBE MOVIES (NEW):
  • If YouTube video is a Bollywood/movie clip, use --tmdb-title
  • Enables character names, cast info, glossary for better accuracy
  • Example: --tmdb-title "Jaane Tu Ya Jaane Na" --tmdb-year 2008
  • Works with subtitle workflow only (auto-enabled)
  • Regular YouTube videos don't need TMDB (auto-disabled)

TWO-STEP TRANSCRIPTION:
  --two-step enables Phase 2 optimization where transcription and
  translation are performed separately for better accuracy:
    • Step 1: Transcribe in source language (e.g., Hindi)
    • Step 2: Translate using dedicated translation model
  Expected improvement: +5-8% accuracy on Hindi transcription

EXAMPLES:
  # Local file: Hindi to English subtitles (default userId=1)
  ./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
    --source-language hi --target-language en

  # YouTube URL: Download and transcribe
  ./prepare-job.sh --media "https://youtu.be/14pp1KyBmYQ" \
    --workflow transcribe --source-language hi

  # YouTube URL: Multi-language subtitles
  ./prepare-job.sh --media "https://youtube.com/watch?v=VIDEO_ID" \
    --workflow subtitle --source-language hi --target-language en,gu,ta

  # YouTube movie with TMDB enrichment (NEW)
  ./prepare-job.sh --media "https://youtu.be/VIDEO_ID" \
    --workflow subtitle --source-language hi --target-language en \
    --tmdb-title "Jaane Tu Ya Jaane Na" --tmdb-year 2008

  # Specify different userId
  ./prepare-job.sh --user-id 2 --media in/movie.mp4 --workflow subtitle \
    --source-language hi --target-language en

  # Multi-language subtitles
  ./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
    --source-language hi --target-language en,gu,ta

  # Transcription only
  ./prepare-job.sh --media in/audio.mp3 --workflow transcribe \
    --source-language hi

  # Test with clip (30 seconds)
  ./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
    --source-language hi --target-language en \
    --start-time 00:10:00 --end-time 00:10:30

SUPPORTED LANGUAGES:
  22 Indian Languages: hi, ta, te, bn, gu, kn, ml, mr, pa, or, as, ur,
                       ne, sd, si, sa, ks, doi, mni, kok, mai, sat
  Plus: 200+ global languages via NLLB

OUTPUT:
  Job directory: out/YYYY/MM/DD/user/N/
  Job ID format: job-YYYYMMDD-user-NNNN

USAGE_EOF
}

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

# Check if environment is set up
if [ ! -d "$COMMON_VENV" ]; then
    log_critical "Environment not found: $COMMON_VENV"
    log_error "Run bootstrap first: ./bootstrap.sh"
    exit 1
fi

if [ ! -f "$PREPARE_JOB_SCRIPT" ]; then
    log_critical "Script not found: $PREPARE_JOB_SCRIPT"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSING
# ═══════════════════════════════════════════════════════════════════════════
# Convert shell script's --media flag to positional argument for Python script
# Python script expects: prepare-job.py <input_media> [OPTIONS]
# Shell script provides: prepare-job.sh --media <file> [OPTIONS]
# ═══════════════════════════════════════════════════════════════════════════

if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

PYTHON_ARGS=()
LOG_LEVEL_ARG=""
MEDIA_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        --media)
            # Extract media file for conversion to positional arg
            MEDIA_FILE="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL_ARG="$2"
            PYTHON_ARGS+=("$1" "$2")
            shift 2
            ;;
        --debug)
            LOG_LEVEL_ARG="DEBUG"
            PYTHON_ARGS+=("$1")
            shift
            ;;
        --estimate-only)
            # Cost estimation mode - estimate costs then exit
            ESTIMATE_ONLY=true
            shift
            ;;
        -s|--source-language|-t|--target-language|--workflow|--start-time|--end-time|--user-id|--two-step|--tmdb-title|--tmdb-year)
            # Pass through known arguments (including new TMDB args)
            PYTHON_ARGS+=("$1")
            if [[ $# -gt 1 && ! "$2" =~ ^- ]]; then
                PYTHON_ARGS+=("$2")
                shift
            fi
            shift
            ;;
        *)
            # Pass through other arguments
            PYTHON_ARGS+=("$1")
            shift
            ;;
    esac
done

# Validate required media file
if [ -z "$MEDIA_FILE" ]; then
    log_error "Missing required argument: --media"
    echo ""
    show_usage
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
# YOUTUBE DOWNLOAD (if URL detected)
# ═══════════════════════════════════════════════════════════════════════════

# Check if MEDIA_FILE is a URL
if [[ "$MEDIA_FILE" =~ ^https?:// ]]; then
    log_info "🌐 Online URL detected: $MEDIA_FILE"
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLAYLIST DETECTION (Week 4 Feature 3)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Check if URL is a playlist
    if [[ "$MEDIA_FILE" =~ playlist.*list= ]] || [[ "$MEDIA_FILE" =~ list=.*watch ]]; then
        log_info "📺 Playlist detected!"
        log_info "⬇️  Parsing playlist..."
        
        # Activate common environment for Python
        export VIRTUAL_ENV="$COMMON_VENV"
        export PATH="$COMMON_VENV/bin:$PATH"
        export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
        
        # Parse playlist info
        PLAYLIST_OUTPUT=$("$COMMON_VENV/bin/python3" -c "
import sys
from pathlib import Path
sys.path.insert(0, '$PROJECT_ROOT')

from shared.online_downloader import get_playlist_info, format_playlist_summary

try:
    # Get playlist info
    info = get_playlist_info('$MEDIA_FILE')
    
    # Print summary
    print(format_playlist_summary(info))
    
    # Print video count and video data (for parsing)
    print('---VIDEO_DATA---')
    print(info['video_count'])
    for video in info['videos']:
        print(f\"{video['video_id']}|{video['title']}|{video['url']}\")
    
    sys.exit(0)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)
        
        if [ $? -ne 0 ]; then
            log_error "❌ Failed to parse playlist"
            log_error "$PLAYLIST_OUTPUT"
            exit 1
        fi
        
        # Extract video count (first line after VIDEO_DATA marker)
        VIDEO_COUNT=$(echo "$PLAYLIST_OUTPUT" | grep -A1 "VIDEO_DATA" | tail -1)
        
        # Show playlist summary (everything before VIDEO_DATA marker)
        echo "$PLAYLIST_OUTPUT" | grep -B100 "VIDEO_DATA" | grep -v "VIDEO_DATA"
        
        echo ""
        log_info "📋 Found $VIDEO_COUNT videos in playlist"
        echo ""
        
        # Ask user confirmation
        read -p "Process all $VIDEO_COUNT videos? [y/N]: " -n 1 -r
        echo ""
        
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cancelled by user"
            exit 0
        fi
        
        echo ""
        log_info "🚀 Creating jobs for playlist videos..."
        echo ""
        
        # Process each video
        JOB_IDS=()
        VIDEO_NUM=0
        
        # Extract video data (lines after VIDEO_DATA marker, skip count line)
        while IFS='|' read -r video_id title url; do
            # Skip if empty or header line
            if [ -z "$video_id" ] || [ "$video_id" = "$VIDEO_COUNT" ]; then
                continue
            fi
            
            ((VIDEO_NUM++))
            
            log_info "Video $VIDEO_NUM/$VIDEO_COUNT: $title"
            
            # Create job for this video (recursively call prepare-job.sh)
            # Remove --estimate-only if present, pass all other args
            VIDEO_ARGS=()
            for arg in "${PYTHON_ARGS[@]}"; do
                if [ "$arg" != "--estimate-only" ]; then
                    VIDEO_ARGS+=("$arg")
                fi
            done
            
            # Run prepare-job for this video (silent mode)
            JOB_OUTPUT=$("$SCRIPT_DIR/prepare-job.sh" \
                --media "$url" \
                "${VIDEO_ARGS[@]}" 2>&1)
            
            # Extract job ID from output
            JOB_ID=$(echo "$JOB_OUTPUT" | grep "Job created:" | awk '{print $NF}')
            
            if [ -n "$JOB_ID" ]; then
                JOB_IDS+=("$JOB_ID")
                log_success "  ✅ Job created: $JOB_ID"
            else
                log_error "  ❌ Failed to create job for video $VIDEO_NUM"
            fi
        done < <(echo "$PLAYLIST_OUTPUT" | grep -A1000 "VIDEO_DATA" | tail -n +3)
        
        echo ""
        log_section "PLAYLIST PROCESSING COMPLETE"
        log_success "✅ Created ${#JOB_IDS[@]} jobs for $VIDEO_COUNT videos"
        echo ""
        log_info "📋 Job IDs:"
        for job_id in "${JOB_IDS[@]}"; do
            echo "   - $job_id"
        done
        
        echo ""
        log_info "💡 Run all jobs:"
        for job_id in "${JOB_IDS[@]}"; do
            echo "   ./run-pipeline.sh -j $job_id"
        done
        echo ""
        
        log_info "💡 Or use a loop:"
        echo "   for job_id in ${JOB_IDS[@]}; do"
        echo "       ./run-pipeline.sh -j \$job_id"
        echo "   done"
        echo ""
        
        exit 0
    fi
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SINGLE VIDEO DOWNLOAD
    # ═══════════════════════════════════════════════════════════════════════════
    
    log_info "⬇️  Downloading video to in/online/..."
    
    # Activate common environment for Python
    export VIRTUAL_ENV="$COMMON_VENV"
    export PATH="$COMMON_VENV/bin:$PATH"
    export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
    
    # Download using Python's online_downloader module
    # Get file path (last line of output)
    DOWNLOAD_OUTPUT=$("$COMMON_VENV/bin/python3" -c "
import sys
from pathlib import Path
sys.path.insert(0, '$PROJECT_ROOT')

from shared.online_downloader import OnlineMediaDownloader

try:
    # Create downloader
    downloader = OnlineMediaDownloader(
        cache_dir=Path('$PROJECT_ROOT/in/online'),
        format_quality='best',
        audio_only=False
    )
    
    # Download video (auto-checks cache first)
    local_path, metadata = downloader.download('$MEDIA_FILE')
    
    # Print ONLY the file path (one line, no logs)
    print(str(local_path))
    sys.exit(0)
    
except Exception as e:
    # Print error to stderr
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)
    
    DOWNLOAD_EXIT_CODE=$?
    
    # Extract only the last line (the file path)
    LOCAL_PATH=$(echo "$DOWNLOAD_OUTPUT" | tail -1)
    
    # Check exit code and path validity
    if [ $DOWNLOAD_EXIT_CODE -eq 0 ] && [ -f "$LOCAL_PATH" ]; then
        # Success - extract video ID from filename
        VIDEO_ID=$(basename "$LOCAL_PATH" | grep -oE '[A-Za-z0-9_-]{11}\.mp4' | sed 's/\.mp4//')
        log_info "📹 YouTube video ID: $VIDEO_ID"
        log_info "✅ Found cached video: $(basename "$LOCAL_PATH")"
        log_info "♻️  Using cached video (skip download)"
        log_success "✅ Video ready: $LOCAL_PATH"
        
        # Replace URL with local path for pipeline
        MEDIA_FILE="$LOCAL_PATH"
    else
        # Failure
        log_error "❌ Download failed:"
        log_error "$DOWNLOAD_RESULT"
        exit 1
    fi
else
    log_debug "Local file detected: $MEDIA_FILE"
fi

# Add media file as first positional argument for Python script
# This maintains compatibility between shell and Python interfaces
# At this point, MEDIA_FILE is always a local path (either original or downloaded)
PYTHON_ARGS=("$MEDIA_FILE" "${PYTHON_ARGS[@]}")

# Set log level if provided
if [ -n "$LOG_LEVEL_ARG" ]; then
    export LOG_LEVEL="$LOG_LEVEL_ARG"
    CURRENT_LOG_LEVEL=$(_get_log_level_value "$LOG_LEVEL")
fi

# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

log_section "CP-WHISPERX-APP JOB PREPARATION"

log_debug "Project root: $PROJECT_ROOT"
log_debug "Python script: $PREPARE_JOB_SCRIPT"
log_debug "Arguments: ${PYTHON_ARGS[*]}"

# Activate common environment and run Python script
export VIRTUAL_ENV="$COMMON_VENV"
export PATH="$COMMON_VENV/bin:$PATH"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

# ═══════════════════════════════════════════════════════════════════════════
# COST ESTIMATION (Week 4 Feature 2)
# ═══════════════════════════════════════════════════════════════════════════

if [ "${ESTIMATE_ONLY:-false}" = true ]; then
    log_info "💰 Estimating job cost..."
    
    # Extract parameters for estimation
    WORKFLOW="subtitle"  # Default
    TARGET_LANGS=""
    ENABLE_SUMMARIZATION="false"
    
    # Parse Python args to extract workflow and target languages
    i=0
    while [ $i -lt ${#PYTHON_ARGS[@]} ]; do
        case "${PYTHON_ARGS[$i]}" in
            --workflow)
                i=$((i+1))
                WORKFLOW="${PYTHON_ARGS[$i]}"
                ;;
            -t|--target-language)
                i=$((i+1))
                TARGET_LANGS="${PYTHON_ARGS[$i]}"
                ;;
        esac
        i=$((i+1))
    done
    
    # Run cost estimation
    "$COMMON_VENV/bin/python3" -c "
import sys
from pathlib import Path
sys.path.insert(0, '$PROJECT_ROOT')

from shared.cost_estimator import show_cost_estimate

# Get audio path
audio_path = Path('$MEDIA_FILE')

# Parse target languages
target_langs = []
if '$TARGET_LANGS':
    target_langs = '$TARGET_LANGS'.split(',')

# Show estimate
total = show_cost_estimate(
    audio_path=audio_path,
    workflow='$WORKFLOW',
    target_langs=target_langs if target_langs else None,
    enable_summarization=$ENABLE_SUMMARIZATION
)

print()
print('ℹ️  This is an estimate. Actual costs may vary.')
print('   To proceed with job creation, run without --estimate-only')
print()
"
    
    exit_code=$?
    log_success "✅ Cost estimation complete"
    exit 0
fi

log_info "Executing job preparation..."

# Run Python script with all arguments
exec "$COMMON_VENV/bin/python3" "$PREPARE_JOB_SCRIPT" "${PYTHON_ARGS[@]}"
