#!/usr/bin/env bash
# Quick validation test for AD-014 caching
# Tests transcribe workflow only (faster)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# Log file
LOG_FILE="logs/testing/manual/$(date +%Y%m%d_%H%M%S)_quick_validation.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}" | tee "$LOG_FILE"
echo -e "${CYAN}║         AD-014 QUICK VALIDATION - TRANSCRIBE WORKFLOW           ║${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test media
MEDIA="in/Energy Demand in AI.mp4"

# Check media exists
if [[ ! -f "$MEDIA" ]]; then
    echo "❌ Media not found: $MEDIA" | tee -a "$LOG_FILE"
    exit 1
fi
echo "✅ Media file: $MEDIA" | tee -a "$LOG_FILE"

# Compute media ID
echo "" | tee -a "$LOG_FILE"
echo -e "${BLUE}🔑 Computing Media ID${NC}" | tee -a "$LOG_FILE"
MEDIA_ID=$(python3 -c "from pathlib import Path; from shared.media_identity import compute_media_id; print(compute_media_id(Path('$MEDIA')))")
echo "   Media ID: ${MEDIA_ID:0:32}..." | tee -a "$LOG_FILE"

# Check cache
CACHE_DIR="$HOME/.cp-whisperx/cache/media/$MEDIA_ID/baseline"
echo "" | tee -a "$LOG_FILE"
echo -e "${BLUE}📦 Cache Status${NC}" | tee -a "$LOG_FILE"
if [[ -d "$CACHE_DIR" ]]; then
    echo -e "${GREEN}   ✅ Baseline cache EXISTS${NC}" | tee -a "$LOG_FILE"
    echo "   Files:" | tee -a "$LOG_FILE"
    ls -lh "$CACHE_DIR" | tee -a "$LOG_FILE"
    HAS_CACHE=true
else
    echo -e "${YELLOW}   ⏳ No cache found (will generate baseline)${NC}" | tee -a "$LOG_FILE"
    HAS_CACHE=false
fi

# Prepare job
echo "" | tee -a "$LOG_FILE"
echo -e "${BLUE}📋 Preparing Job${NC}" | tee -a "$LOG_FILE"
PREP_OUTPUT=$(./prepare-job.sh --media "$MEDIA" --workflow transcribe 2>&1)
echo "$PREP_OUTPUT" | tee -a "$LOG_FILE"

# Extract job ID from preparation output
JOB_ID=$(echo "$PREP_OUTPUT" | grep -E "Job created: job-[0-9]{8}-[a-z]+-[0-9]{4}" | sed 's/.*Job created: //' | sed 's/\x1b\[[0-9;]*m//g' | tr -d '[]' | awk '{print $NF}')

if [[ -z "$JOB_ID" ]]; then
    echo -e "${RED}❌ Failed to extract job ID${NC}" | tee -a "$LOG_FILE"
    echo "Preparation output:" | tee -a "$LOG_FILE"
    echo "$PREP_OUTPUT" | tee -a "$LOG_FILE"
    exit 1
fi

echo "" | tee -a "$LOG_FILE"
echo -e "${GREEN}✅ Job: $JOB_ID${NC}" | tee -a "$LOG_FILE"

# Find job directory by job.json content
JOB_DIR=$(find out/ -type f -name "job.json" -exec grep -l "\"job_id\": \"$JOB_ID\"" {} \; 2>/dev/null | head -1 | xargs dirname)
if [[ -z "$JOB_DIR" ]]; then
    echo -e "${RED}❌ Job directory not found for: $JOB_ID${NC}" | tee -a "$LOG_FILE"
    exit 1
fi
echo "   Job directory: $JOB_DIR" | tee -a "$LOG_FILE"

# Run pipeline
echo "" | tee -a "$LOG_FILE"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}                    RUNNING PIPELINE                               ${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

if $HAS_CACHE; then
    echo -e "${GREEN}🚀 Cache available - expecting 70-80% speedup${NC}" | tee -a "$LOG_FILE"
else
    echo -e "${YELLOW}⏳ No cache - will generate baseline${NC}" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

START_TIME=$(date +%s)
./run-pipeline.sh -j "$JOB_ID" 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Results
echo "" | tee -a "$LOG_FILE"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}                         RESULTS                                   ${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "   Media: $(basename "$MEDIA")" | tee -a "$LOG_FILE"
echo "   Media ID: ${MEDIA_ID:0:32}..." | tee -a "$LOG_FILE"
echo "   Job: $JOB_ID" | tee -a "$LOG_FILE"
echo "   Duration: ${DURATION} seconds ($(($DURATION / 60)) min $(($DURATION % 60)) sec)" | tee -a "$LOG_FILE"
echo "   Exit Code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "   Cache Used: $(if $HAS_CACHE; then echo "Yes"; else echo "No"; fi)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check outputs
echo -e "${BLUE}📂 Output Files${NC}" | tee -a "$LOG_FILE"
if [[ -d "$JOB_DIR/07_alignment" ]]; then
    echo "   Alignment output:" | tee -a "$LOG_FILE"
    ls -lh "$JOB_DIR/07_alignment/" | grep -E "\.(json|txt)$" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Check baseline cache status
if [[ -d "$CACHE_DIR" ]]; then
    BASELINE_FILES=$(ls -1 "$CACHE_DIR" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}   ✅ Baseline cache: $BASELINE_FILES files${NC}" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    ls -lh "$CACHE_DIR" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}✅ Test PASSED - Log: $LOG_FILE${NC}" | tee -a "$LOG_FILE"
else
    echo -e "${RED}❌ Test FAILED (exit code: $EXIT_CODE) - Log: $LOG_FILE${NC}" | tee -a "$LOG_FILE"
fi

if ! $HAS_CACHE && [[ $EXIT_CODE -eq 0 ]]; then
    echo "" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}💡 Baseline generated! Run this script again to test caching speedup!${NC}" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
exit $EXIT_CODE
