#!/bin/bash
# Simple Glossary Testing Script with hardcoded path
set -e

VIDEO_PATH="/Users/rpatel/Projects/cp-whisperx-app/in/Jaane Tu Ya Jaane Na 2008.mp4"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   Glossary System - Simple Test                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Using video: $VIDEO_PATH"
echo ""

# Create test results directory
mkdir -p test-results/{baseline,glossary}

# Step 1: Baseline Test
echo "═══ Step 1: Baseline Test (Without Glossary) ═══"
read -p "Run baseline test? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Preparing baseline job..."
    ./prepare-job.sh "$VIDEO_PATH" --workflow translate \
        -s hi -t en --end-time 00:05:00 --user-id baseline-test
    
    # Find the job directory
    JOB_DIR=$(find out -type d -name "baseline-test" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
    FULL_JOB_PATH=$(find "$JOB_DIR" -maxdepth 1 -type d -mindepth 1 2>/dev/null | head -1)
    JOB_ID=$(python3 -c "import json; print(json.load(open('$FULL_JOB_PATH/job.json'))['job_id'])" 2>/dev/null)
    
    echo "Job ID: $JOB_ID"
    echo "Job Path: $FULL_JOB_PATH"
    
    # Disable glossary
    cat > "$FULL_JOB_PATH/.$JOB_ID.env" << 'EOF'
TMDB_ENRICHMENT_ENABLED=false
GLOSSARY_CACHE_ENABLED=false
EOF
    
    echo "Running baseline pipeline..."
    ./run-pipeline.sh -j "$JOB_ID"
    
    # Save results
    if ls "$FULL_JOB_PATH/subtitles/"*.srt &>/dev/null; then
        cp "$FULL_JOB_PATH/subtitles/"*.srt test-results/baseline/
        cp "$FULL_JOB_PATH/logs/pipeline.log" test-results/baseline/
        echo "$JOB_ID" > test-results/baseline/job-id.txt
        echo "✓ Baseline complete! Results in test-results/baseline/"
    fi
fi

echo ""

# Step 2: Glossary Test  
echo "═══ Step 2: Glossary Test (With Glossary) ═══"
read -p "Run glossary test? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Film title (e.g., Jaane Tu Ya Jaane Na): " FILM_TITLE
    read -p "Film year (e.g., 2008): " FILM_YEAR
    
    echo "Preparing glossary job..."
    
    if [ -n "$FILM_TITLE" ] && [ -n "$FILM_YEAR" ]; then
        ./prepare-job.sh "$VIDEO_PATH" --workflow translate \
            -s hi -t en --end-time 00:05:00 --user-id glossary-test \
            --tmdb-title "$FILM_TITLE" --tmdb-year "$FILM_YEAR"
    else
        ./prepare-job.sh "$VIDEO_PATH" --workflow translate \
            -s hi -t en --end-time 00:05:00 --user-id glossary-test
    fi
    
    # Find the job directory
    JOB_DIR=$(find out -type d -name "glossary-test" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
    FULL_JOB_PATH=$(find "$JOB_DIR" -maxdepth 1 -type d -mindepth 1 2>/dev/null | head -1)
    JOB_ID=$(python3 -c "import json; print(json.load(open('$FULL_JOB_PATH/job.json'))['job_id'])" 2>/dev/null)
    
    echo "Job ID: $JOB_ID"
    echo "Job Path: $FULL_JOB_PATH"
    
    # Enable glossary
    cat > "$FULL_JOB_PATH/.$JOB_ID.env" << 'EOF'
TMDB_ENRICHMENT_ENABLED=true
GLOSSARY_CACHE_ENABLED=true
EOF
    
    echo "Running glossary pipeline..."
    ./run-pipeline.sh -j "$JOB_ID"
    
    # Save results
    if ls "$FULL_JOB_PATH/subtitles/"*.srt &>/dev/null; then
        cp "$FULL_JOB_PATH/subtitles/"*.srt test-results/glossary/
        cp "$FULL_JOB_PATH/logs/pipeline.log" test-results/glossary/
        [ -f "$FULL_JOB_PATH/03b_glossary_load/glossary_snapshot.json" ] && \
            cp "$FULL_JOB_PATH/03b_glossary_load/glossary_snapshot.json" test-results/glossary/
        echo "$JOB_ID" > test-results/glossary/job-id.txt
        echo "✓ Glossary test complete! Results in test-results/glossary/"
        
        echo ""
        echo "═══ Validation ═══"
        [ -f "test-results/glossary/glossary_snapshot.json" ] && \
            echo "✓ Glossary snapshot created" || echo "✗ No glossary snapshot"
        grep -q "bias terms" test-results/glossary/pipeline.log 2>/dev/null && \
            echo "✓ ASR bias terms used" || echo "✗ No ASR bias terms"
        grep -q "Glossary applied" test-results/glossary/pipeline.log 2>/dev/null && \
            echo "✓ Translation glossary applied" || echo "✗ No translation glossary"
    fi
fi

echo ""
echo "═══ Done ═══"
echo "Check test-results/ directory for outputs"
