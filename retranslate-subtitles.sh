#!/bin/bash
#
# Re-translate Hinglish SRT to English using better translation model
# Fixes WhisperX translation hallucinations and missing segments
#
# Usage:
#   ./retranslate-subtitles.sh <job_dir>
#   ./retranslate-subtitles.sh out/2025/11/16/1/20251116-0002
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -f .bollyenv/bin/activate ]; then
    source .bollyenv/bin/activate
else
    echo "Error: Virtual environment not found at .bollyenv/"
    exit 1
fi

# Check if job directory provided
if [ -z "$1" ]; then
    echo "Usage: $0 <job_dir>"
    echo ""
    echo "Example:"
    echo "  $0 out/2025/11/16/1/20251116-0002"
    echo ""
    echo "This will retranslate the Hinglish SRT file to English using a better"
    echo "translation model, fixing WhisperX hallucinations and missing segments."
    exit 1
fi

JOB_DIR="$1"
ASR_DIR="${JOB_DIR}/06_asr"

# Validate directories exist
if [ ! -d "$JOB_DIR" ]; then
    echo "Error: Job directory not found: $JOB_DIR"
    exit 1
fi

if [ ! -d "$ASR_DIR" ]; then
    echo "Error: ASR directory not found: $ASR_DIR"
    exit 1
fi

# Find the Hinglish SRT file
HINGLISH_SRT=$(find "$ASR_DIR" -maxdepth 1 -name "*.srt" ! -name "*English*" ! -name "*test*" | head -1)

if [ -z "$HINGLISH_SRT" ]; then
    echo "Error: No Hinglish SRT file found in $ASR_DIR"
    exit 1
fi

# Determine output filename
BASENAME=$(basename "$HINGLISH_SRT" .srt)
OUTPUT_SRT="${ASR_DIR}/${BASENAME}-English-Retranslated.srt"
BACKUP_SRT="${ASR_DIR}/${BASENAME}-English.srt.backup"

echo "=========================================="
echo "  SRT Re-translation"
echo "=========================================="
echo "Job Directory: $JOB_DIR"
echo "Source SRT:    $HINGLISH_SRT"
echo "Output SRT:    $OUTPUT_SRT"
echo ""

# Check if original English translation exists and offer to back it up
ORIGINAL_ENGLISH="${ASR_DIR}/${BASENAME}-English.srt"
if [ -f "$ORIGINAL_ENGLISH" ]; then
    echo "Note: Original WhisperX translation found: $ORIGINAL_ENGLISH"
    if [ ! -f "$BACKUP_SRT" ]; then
        echo "      Creating backup: $BACKUP_SRT"
        cp "$ORIGINAL_ENGLISH" "$BACKUP_SRT"
    else
        echo "      Backup already exists: $BACKUP_SRT"
    fi
    echo ""
fi

# Check if deep-translator is installed
if ! python -c "import deep_translator" 2>/dev/null; then
    echo "Installing deep-translator library..."
    pip install deep-translator --quiet
    echo ""
fi

# Run the retranslation
echo "Starting translation..."
echo "This may take a few minutes for large files..."
echo ""

python scripts/retranslate_srt.py \
    "$HINGLISH_SRT" \
    -o "$OUTPUT_SRT" \
    --method deep-translator \
    --src-lang hi \
    --dest-lang en

echo ""
echo "=========================================="
echo "  Translation Complete!"
echo "=========================================="
echo "Output: $OUTPUT_SRT"
echo ""

# Show file size comparison
if [ -f "$ORIGINAL_ENGLISH" ]; then
    echo "File size comparison:"
    echo "  Original:      $(ls -lh "$ORIGINAL_ENGLISH" | awk '{print $5}')"
    echo "  Retranslated:  $(ls -lh "$OUTPUT_SRT" | awk '{print $5}')"
    echo ""
fi

# Offer to replace original
if [ -f "$ORIGINAL_ENGLISH" ]; then
    echo "To replace the original English translation with the retranslated version:"
    echo "  cp \"$OUTPUT_SRT\" \"$ORIGINAL_ENGLISH\""
    echo ""
    echo "To restore the original from backup:"
    echo "  cp \"$BACKUP_SRT\" \"$ORIGINAL_ENGLISH\""
fi

echo "=========================================="
