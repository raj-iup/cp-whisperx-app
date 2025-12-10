#!/usr/bin/env bash
# AD-014 Performance Validation Test
# Measures actual speedup from caching system

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Log file
LOG_FILE="logs/testing/manual/$(date +%Y%m%d_%H%M%S)_performance_validation.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}║      AD-014 CACHING PERFORMANCE VALIDATION TEST                  ║${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test media
SUBTITLE_MEDIA="in/Jaane Tu Ya Jaane Na 2008.mp4"
TRANSCRIBE_MEDIA="in/Energy Demand in AI.mp4"

# Validate media files exist
echo -e "${BLUE}📂 Validating Test Media${NC}" | tee -a "$LOG_FILE"
if [[ ! -f "$SUBTITLE_MEDIA" ]]; then
    echo -e "${RED}❌ Subtitle media not found: $SUBTITLE_MEDIA${NC}" | tee -a "$LOG_FILE"
    exit 1
fi
if [[ ! -f "$TRANSCRIBE_MEDIA" ]]; then
    echo -e "${RED}❌ Transcribe media not found: $TRANSCRIBE_MEDIA${NC}" | tee -a "$LOG_FILE"
    exit 1
fi
echo -e "${GREEN}✅ Both test media files found${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Compute media IDs
echo -e "${BLUE}🔑 Computing Media IDs${NC}" | tee -a "$LOG_FILE"
SUBTITLE_ID=$(python3 -c "from pathlib import Path; from shared.media_identity import compute_media_id; print(compute_media_id(Path('$SUBTITLE_MEDIA')))")
TRANSCRIBE_ID=$(python3 -c "from pathlib import Path; from shared.media_identity import compute_media_id; print(compute_media_id(Path('$TRANSCRIBE_MEDIA')))")
echo -e "   Subtitle Media ID: ${SUBTITLE_ID:0:16}..." | tee -a "$LOG_FILE"
echo -e "   Transcribe Media ID: ${TRANSCRIBE_ID:0:16}..." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check cache directory
CACHE_DIR="$HOME/.cp-whisperx/cache"
echo -e "${BLUE}📦 Cache Directory Status${NC}" | tee -a "$LOG_FILE"
echo -e "   Location: $CACHE_DIR" | tee -a "$LOG_FILE"
if [[ -d "$CACHE_DIR/media/$SUBTITLE_ID/baseline" ]]; then
    echo -e "${GREEN}   ✅ Subtitle baseline EXISTS (will test cached run)${NC}" | tee -a "$LOG_FILE"
    HAS_SUBTITLE_CACHE=true
else
    echo -e "${YELLOW}   ⏳ Subtitle baseline NOT FOUND (will generate)${NC}" | tee -a "$LOG_FILE"
    HAS_SUBTITLE_CACHE=false
fi
if [[ -d "$CACHE_DIR/media/$TRANSCRIBE_ID/baseline" ]]; then
    echo -e "${GREEN}   ✅ Transcribe baseline EXISTS (will test cached run)${NC}" | tee -a "$LOG_FILE"
    HAS_TRANSCRIBE_CACHE=true
else
    echo -e "${YELLOW}   ⏳ Transcribe baseline NOT FOUND (will generate)${NC}" | tee -a "$LOG_FILE"
    HAS_TRANSCRIBE_CACHE=false
fi
echo "" | tee -a "$LOG_FILE"

# Test selection
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}                      SELECT TEST TO RUN                            ${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo -e "${YELLOW}Which test would you like to run?${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo -e "  1) ${GREEN}Transcribe Workflow${NC} - Energy Demand in AI.mp4" | tee -a "$LOG_FILE"
echo -e "     Duration: ~2-5 minutes (no cache) / ~30 seconds (with cache)" | tee -a "$LOG_FILE"
echo -e "     Status: $(if $HAS_TRANSCRIBE_CACHE; then echo -e "${GREEN}Cache available${NC}"; else echo -e "${YELLOW}No cache${NC}"; fi)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo -e "  2) ${BLUE}Subtitle Workflow${NC} - Jaane Tu Ya Jaane Na 2008.mp4" | tee -a "$LOG_FILE"
echo -e "     Duration: ~10-20 minutes (no cache) / ~2-5 minutes (with cache)" | tee -a "$LOG_FILE"
echo -e "     Status: $(if $HAS_SUBTITLE_CACHE; then echo -e "${GREEN}Cache available${NC}"; else echo -e "${YELLOW}No cache${NC}"; fi)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo -e "  3) ${CYAN}Both Tests${NC} (runs transcribe, then subtitle)" | tee -a "$LOG_FILE"
echo -e "     Duration: ~15-30 minutes total" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

read -p "Enter your choice (1-3): " CHOICE
echo "User selected: $CHOICE" >> "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Function to run test
run_test() {
    local WORKFLOW=$1
    local MEDIA=$2
    local MEDIA_ID=$3
    local HAS_CACHE=$4
    
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}           TESTING: ${WORKFLOW^^} WORKFLOW                         ${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Prepare job
    echo -e "${BLUE}📋 Preparing Job${NC}" | tee -a "$LOG_FILE"
    if [[ "$WORKFLOW" == "transcribe" ]]; then
        ./prepare-job.sh --media "$MEDIA" --workflow transcribe 2>&1 | tee -a "$LOG_FILE"
    else
        ./prepare-job.sh --media "$MEDIA" --workflow subtitle --source-language hi --target-languages en 2>&1 | tee -a "$LOG_FILE"
    fi
    
    # Get job ID
    JOB_ID=$(find out/ -type d -name "job-*" | sort | tail -1 | xargs basename)
    echo -e "${GREEN}✅ Job prepared: $JOB_ID${NC}" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Run pipeline with timing
    echo -e "${BLUE}⚡ Running Pipeline${NC}" | tee -a "$LOG_FILE"
    if $HAS_CACHE; then
        echo -e "${GREEN}   Cache available - expecting 70-80% speedup${NC}" | tee -a "$LOG_FILE"
    else
        echo -e "${YELLOW}   No cache - generating baseline${NC}" | tee -a "$LOG_FILE"
    fi
    echo "" | tee -a "$LOG_FILE"
    
    START_TIME=$(date +%s)
    ./run-pipeline.sh -j "$JOB_ID" 2>&1 | tee -a "$LOG_FILE"
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo "" | tee -a "$LOG_FILE"
    echo -e "${GREEN}✅ Pipeline completed in ${DURATION} seconds${NC}" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Results
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}                         RESULTS                                   ${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo -e "   Workflow: ${WORKFLOW}" | tee -a "$LOG_FILE"
    echo -e "   Media: $(basename "$MEDIA")" | tee -a "$LOG_FILE"
    echo -e "   Media ID: ${MEDIA_ID:0:16}..." | tee -a "$LOG_FILE"
    echo -e "   Job: $JOB_ID" | tee -a "$LOG_FILE"
    echo -e "   Duration: ${DURATION} seconds ($(($DURATION / 60)) min $(($DURATION % 60)) sec)" | tee -a "$LOG_FILE"
    echo -e "   Cache Used: $(if $HAS_CACHE; then echo "Yes"; else echo "No (baseline generated)"; fi)" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Check if baseline was created
    if [[ -d "$CACHE_DIR/media/$MEDIA_ID/baseline" ]]; then
        BASELINE_FILES=$(ls -1 "$CACHE_DIR/media/$MEDIA_ID/baseline/" | wc -l | tr -d ' ')
        echo -e "${GREEN}   ✅ Baseline cache created: $BASELINE_FILES files${NC}" | tee -a "$LOG_FILE"
        ls -lh "$CACHE_DIR/media/$MEDIA_ID/baseline/" | tee -a "$LOG_FILE"
    fi
    echo "" | tee -a "$LOG_FILE"
}

# Run selected tests
case $CHOICE in
    1)
        run_test "transcribe" "$TRANSCRIBE_MEDIA" "$TRANSCRIBE_ID" $HAS_TRANSCRIBE_CACHE
        ;;
    2)
        run_test "subtitle" "$SUBTITLE_MEDIA" "$SUBTITLE_ID" $HAS_SUBTITLE_CACHE
        ;;
    3)
        run_test "transcribe" "$TRANSCRIBE_MEDIA" "$TRANSCRIBE_ID" $HAS_TRANSCRIBE_CACHE
        echo "" | tee -a "$LOG_FILE"
        echo -e "${YELLOW}Waiting 5 seconds before next test...${NC}" | tee -a "$LOG_FILE"
        sleep 5
        run_test "subtitle" "$SUBTITLE_MEDIA" "$SUBTITLE_ID" $HAS_SUBTITLE_CACHE
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}" | tee -a "$LOG_FILE"
        exit 1
        ;;
esac

echo "" | tee -a "$LOG_FILE"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}                    TEST COMPLETE                                  ${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo -e "${GREEN}✅ Log file: $LOG_FILE${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

if ! $HAS_TRANSCRIBE_CACHE || ! $HAS_SUBTITLE_CACHE; then
    echo -e "${YELLOW}💡 TIP: Run this test again to see the caching speedup!${NC}" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
fi
