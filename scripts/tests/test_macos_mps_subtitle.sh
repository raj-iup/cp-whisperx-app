#!/bin/bash
# Test T01: macOS MPS Native Subtitle Generation

set -e  # Exit on error

echo "=== Test T01: macOS MPS Native Subtitle Generation ==="

# Check if running on macOS
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "✗ This test requires macOS"
    exit 1
fi

# Check for sample media
if [ ! -f "./in/sample_movie.mp4" ]; then
    echo "⚠️  Warning: ./in/sample_movie.mp4 not found"
    echo "   Place a sample video file at ./in/sample_movie.mp4"
    exit 1
fi

# Prepare job with native MPS
echo "Preparing job with native MPS acceleration..."
python prepare-job.py \
  ./in/sample_movie.mp4 \
  --start-time 00:10:00 \
  --end-time 00:15:00 \
  --subtitle-gen \
  --native

# Get job ID from most recent job
YEAR=$(date +%Y)
MONTH=$(date +%m)
DAY=$(date +%d)
JOB_ID=$(ls -t jobs/$YEAR/$MONTH/$DAY/ | head -1)

if [ -z "$JOB_ID" ]; then
    echo "✗ Failed to create job"
    exit 1
fi

echo "Job ID: $JOB_ID"

# Run pipeline
echo "Running pipeline..."
python pipeline.py --job "$JOB_ID"

# Verify outputs
echo ""
echo "Verifying outputs..."
OUTPUT_DIR="out/$YEAR/$MONTH/$DAY/$JOB_ID"

# Check for expected files
CHECKS_PASSED=0
CHECKS_FAILED=0

if [ -f "$OUTPUT_DIR/manifest.json" ]; then
    echo "✓ Manifest created"
    ((CHECKS_PASSED++))
else
    echo "✗ Manifest missing"
    ((CHECKS_FAILED++))
fi

if [ -f "$OUTPUT_DIR/subtitles/subtitles.srt" ]; then
    echo "✓ Subtitles created"
    ((CHECKS_PASSED++))
else
    echo "✗ Subtitles missing"
    ((CHECKS_FAILED++))
fi

if [ -f "$OUTPUT_DIR/final_output.mp4" ]; then
    echo "✓ Final video created"
    ((CHECKS_PASSED++))
else
    echo "✗ Final video missing"
    ((CHECKS_FAILED++))
fi

if [ -f "$OUTPUT_DIR/audio/audio.wav" ]; then
    echo "✓ Audio extracted"
    ((CHECKS_PASSED++))
else
    echo "✗ Audio missing"
    ((CHECKS_FAILED++))
fi

# Check manifest for MPS device
if grep -q '"device": "mps"' "$OUTPUT_DIR/manifest.json" 2>/dev/null; then
    echo "✓ MPS acceleration confirmed"
    ((CHECKS_PASSED++))
else
    echo "⚠️  MPS acceleration not detected in manifest"
fi

# Check pipeline status
if grep -q '"status": "completed"' "$OUTPUT_DIR/manifest.json" 2>/dev/null; then
    echo "✓ Pipeline completed successfully"
    ((CHECKS_PASSED++))
else
    echo "✗ Pipeline did not complete"
    ((CHECKS_FAILED++))
fi

echo ""
echo "=== Test T01 Summary ==="
echo "Passed: $CHECKS_PASSED"
echo "Failed: $CHECKS_FAILED"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo "✓ Test T01 PASSED"
    exit 0
else
    echo "✗ Test T01 FAILED"
    exit 1
fi
