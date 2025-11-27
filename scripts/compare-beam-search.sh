#!/bin/bash
# Beam Search Comparison Tool
# Compare translation quality across different beam widths (4-10)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Source common logging
source "$SCRIPT_DIR/scripts/common-logging.sh"

# Default values
BEAM_MIN=4
BEAM_MAX=10
DEVICE="mps"
SOURCE_LANG="hi"
TARGET_LANG="en"

print_usage() {
    cat << EOF
Usage: ./compare-beam-search.sh JOB_DIR [OPTIONS]

Compare translation quality across different beam search widths (4-10)
for manual quality inspection.

ARGUMENTS:
  JOB_DIR           Path to job directory (e.g., out/2025/11/24/1/1)

OPTIONS:
  --beam-range MIN,MAX    Beam width range (default: 4,10)
  --device DEVICE         Device: mps, cuda, cpu (default: mps)
  --source-lang LANG      Source language (default: hi)
  --target-lang LANG      Target language (default: en)
  -h, --help              Show this help

EXAMPLES:
  # Compare beam widths 4-10 for a job
  ./compare-beam-search.sh out/2025/11/24/1/1

  # Compare beam widths 5-8 only
  ./compare-beam-search.sh out/2025/11/24/1/1 --beam-range 5,8

  # Use CPU instead of MPS
  ./compare-beam-search.sh out/2025/11/24/1/1 --device cpu

OUTPUT:
  Creates comparison directory in job folder:
    {JOB_DIR}/beam_comparison/
      ├── segments_en_beam4.json
      ├── segments_en_beam5.json
      ├── ...
      ├── segments_en_beam10.json
      └── beam_comparison_report.html  (Interactive comparison)

WORKFLOW:
  1. Extracts segments from ASR output (04_asr/segments.json)
  2. Translates with each beam width (4, 5, 6, 7, 8, 9, 10)
  3. Generates HTML report for side-by-side comparison
  4. Opens report in browser for manual quality inspection

TIP:
  Higher beam widths (8-10) typically produce better quality
  but take 2-3x longer. Use this tool to find optimal balance.

EOF
}

# Parse arguments
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    print_usage
    exit 0
fi

JOB_DIR="$1"
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        --beam-range)
            BEAM_RANGE="$2"
            shift 2
            ;;
        --device)
            DEVICE="$2"
            shift 2
            ;;
        --source-lang)
            SOURCE_LANG="$2"
            shift 2
            ;;
        --target-lang)
            TARGET_LANG="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Verify job directory
if [ ! -d "$JOB_DIR" ]; then
    log_error "Job directory not found: $JOB_DIR"
    exit 1
fi

log_debug "Job directory verified: $JOB_DIR"

# Find segments file
SEGMENTS_FILE="$JOB_DIR/04_asr/segments.json"
if [ ! -f "$SEGMENTS_FILE" ]; then
    log_error "Segments file not found: $SEGMENTS_FILE"
    log_info "Make sure ASR stage has completed successfully"
    exit 1
fi

log_debug "Segments file found: $SEGMENTS_FILE"

# Create comparison output directory
COMPARISON_DIR="$JOB_DIR/beam_comparison"
mkdir -p "$COMPARISON_DIR"
log_debug "Comparison directory created: $COMPARISON_DIR"

log_section "BEAM SEARCH COMPARISON ANALYSIS"

log_info "Job directory:    $JOB_DIR"
log_info "Segments file:    $SEGMENTS_FILE"
log_info "Output directory: $COMPARISON_DIR"
log_info "Translation:      $SOURCE_LANG → $TARGET_LANG"
log_info "Device:           $DEVICE"

if [ -n "$BEAM_RANGE" ]; then
    log_info "Beam range:       $BEAM_RANGE"
else
    log_info "Beam range:       $BEAM_MIN-$BEAM_MAX (default)"
    BEAM_RANGE="$BEAM_MIN,$BEAM_MAX"
fi

echo ""

# Count segments
NUM_SEGMENTS=$(jq '.segments | length' "$SEGMENTS_FILE")
log_info "Found $NUM_SEGMENTS segments to translate"
log_debug "Segment count: $NUM_SEGMENTS"
echo ""

# Estimate time
BEAM_COUNT=$((${BEAM_RANGE#*,} - ${BEAM_RANGE%,*} + 1))
AVG_TIME_PER_BEAM=90  # seconds (approximate)
TOTAL_TIME=$((BEAM_COUNT * AVG_TIME_PER_BEAM))
MINUTES=$((TOTAL_TIME / 60))

log_warn "⏱️  Estimated time: ~${MINUTES} minutes ($BEAM_COUNT beam widths × ~90s each)"
log_debug "Beam count: $BEAM_COUNT, Total time: ~${TOTAL_TIME}s"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

log_info "Starting beam search comparison..."
echo ""

# Use IndicTrans2 environment's Python
INDICTRANS2_PYTHON="$SCRIPT_DIR/venv/indictrans2/bin/python"

if [ ! -f "$INDICTRANS2_PYTHON" ]; then
    log_error "IndicTrans2 environment not found: $INDICTRANS2_PYTHON"
    log_info "Please run: ./bootstrap.sh"
    exit 1
fi

log_debug "Using Python: $INDICTRANS2_PYTHON"

"$INDICTRANS2_PYTHON" "$SCRIPT_DIR/scripts/beam_search_comparison.py" \
    "$SEGMENTS_FILE" \
    "$COMPARISON_DIR" \
    --source-lang "$SOURCE_LANG" \
    --target-lang "$TARGET_LANG" \
    --beam-range "$BEAM_RANGE" \
    --device "$DEVICE"

RESULT=$?

echo ""
log_section "COMPARISON COMPLETE"

if [ $RESULT -eq 0 ]; then
    log_success "Beam search comparison completed successfully!"
    echo ""
    log_info "Results:"
    log_info "  • Comparison directory: $COMPARISON_DIR"
    log_info "  • Report: $COMPARISON_DIR/beam_comparison_report.html"
    echo ""
    log_info "Next steps:"
    log_info "  1. Open report in browser:"
    log_info "     open $COMPARISON_DIR/beam_comparison_report.html"
    echo ""
    log_info "  2. Review translations side-by-side"
    log_info "  3. Determine optimal beam width for your use case"
    log_info "  4. Update job configuration with preferred beam width"
    echo ""
    
    # Try to open report automatically
    if command -v open &> /dev/null; then
        log_info "Opening report in browser..."
        open "$COMPARISON_DIR/beam_comparison_report.html"
    fi
else
    log_failure "Beam search comparison failed"
    log_error "Check the error messages above"
    exit 1
fi

echo ""
