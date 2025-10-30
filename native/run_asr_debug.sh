#!/bin/bash
# Run Stage 7: ASR in debug mode with detailed logging

set -e

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <movie_name> [options]"
    echo ""
    echo "Arguments:"
    echo "  movie_name    Name of the movie directory in ./out/"
    echo ""
    echo "Options:"
    echo "  --model       Whisper model size (tiny, base, small, medium, large-v2, large-v3) [default: base]"
    echo "  --language    Language code (e.g., en, hi, es) [default: auto-detect]"
    echo "  --batch-size  Batch size for processing [default: 16]"
    echo ""
    echo "Example:"
    echo "  $0 My_Movie --model base --language en"
    exit 1
fi

MOVIE_NAME="$1"
shift  # Remove first argument

MOVIE_DIR="./out/$MOVIE_NAME"
VENV_PATH="native/venvs/asr"
SCRIPT_PATH="native/scripts/07_asr.py"

# Validate paths
if [ ! -d "$MOVIE_DIR" ]; then
    echo "❌ Error: Movie directory not found: $MOVIE_DIR"
    exit 1
fi

if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Error: Virtual environment not found: $VENV_PATH"
    echo "Run ./native/setup_venvs.sh first"
    exit 1
fi

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Error: Script not found: $SCRIPT_PATH"
    exit 1
fi

# Get input video path from movie directory (assume it's stored in manifest or use first mp4)
INPUT_FILE=$(find "./in" -name "*.mp4" -o -name "*.mkv" | head -1)
if [ -z "$INPUT_FILE" ]; then
    echo "⚠️  Warning: Could not find input video in ./in/"
    echo "Using placeholder path - adjust if needed"
    INPUT_FILE="./in/video.mp4"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐛 DEBUG MODE: Stage 7 - ASR (Transcription + Alignment)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📂 Movie Directory: $MOVIE_DIR"
echo "🔧 Virtual Env: $VENV_PATH"
echo "📝 Script: $SCRIPT_PATH"
echo "🎬 Input: $INPUT_FILE"
echo "📊 Arguments: $@"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Activate venv and run with DEBUG level
source "$VENV_PATH/bin/activate"

export PYTHONPATH="$PWD:$PWD/shared:$PWD/native/utils:$PYTHONPATH"
export PYTORCH_ENABLE_MPS_FALLBACK=1
export LOG_LEVEL=DEBUG  # Set debug level

echo "🚀 Starting ASR stage in DEBUG mode..."
echo "📋 Logs will be saved to: logs/asr_${MOVIE_NAME}_*.log"
echo ""

# Run Python with verbose output
python -u "$SCRIPT_PATH" \
    --input "$INPUT_FILE" \
    --movie-dir "$MOVIE_DIR" \
    "$@"

EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ASR stage completed successfully"
else
    echo "❌ ASR stage failed with exit code: $EXIT_CODE"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Check detailed logs in: logs/"
echo "📂 Output files in: $MOVIE_DIR/transcription/"
echo ""

exit $EXIT_CODE
