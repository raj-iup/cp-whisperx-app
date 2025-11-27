#!/bin/bash
# Quick Start Production Testing Script
# Run this to begin testing the glossary system
# Version: 1.1 (2025-11-26 - Fixed path extraction)

set -e

PROJECT_ROOT="/Users/rpatel/Projects/cp-whisperx-app"
cd "$PROJECT_ROOT"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   Glossary System - Production Testing Quick Start           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Create test results directory
echo "📁 Creating test results directory..."
mkdir -p test-results/{baseline,glossary,cache,edge-cases}
echo "✓ Created test-results/"
echo ""

# Step 1: Baseline Test
echo "═══ Step 1: Baseline Test (Without Glossary) ═══"
echo "This will run the pipeline WITHOUT glossary to establish a baseline."
echo ""
read -p "Run baseline test? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running baseline test..."
    echo "Note: Using sample clip (first 5 minutes) for faster testing"
    echo ""
    
    # Default video path
    DEFAULT_VIDEO="/Users/rpatel/Projects/cp-whisperx-app/in/Jaane Tu Ya Jaane Na 2008.mp4"
    
    echo "Default video: $DEFAULT_VIDEO"
    read -p "Press Enter to use default, or enter different path: " VIDEO_PATH
    
    # Use default if empty
    if [ -z "$VIDEO_PATH" ]; then
        VIDEO_PATH="$DEFAULT_VIDEO"
    fi
    
    if [ -z "$VIDEO_PATH" ] || [ ! -f "$VIDEO_PATH" ]; then
        echo "⚠ No video file provided. Skipping baseline test."
        echo "To run manually later:"
        echo "  ./prepare-job.sh --media YOUR_VIDEO.mp4 --workflow translate --source-language hi --target-language en --end-time 00:05:00"
        echo "  ./run-pipeline.sh -j <job-id>"
    else
        # Prepare job with 5-minute clip for faster testing
        # Capture output to extract job ID
        PREP_OUTPUT=$(./prepare-job.sh \
            --media "$VIDEO_PATH" \
            --workflow translate \
            --source-language hi \
            --target-language en \
            --start-time 00:00:00 \
            --end-time 00:05:00 \
            --user-id baseline 2>&1)
        
        echo "$PREP_OUTPUT"
        
        # Extract job ID from prepare-job output (macOS compatible)
        ACTUAL_JOB_ID=$(echo "$PREP_OUTPUT" | grep "Job created:" | awk '{print $3}')
        
        if [ -z "$ACTUAL_JOB_ID" ]; then
            # Fallback: try to extract from "Job ID:" line
            ACTUAL_JOB_ID=$(echo "$PREP_OUTPUT" | grep "Job ID:" | head -1 | awk '{print $NF}')
        fi
        
        if [ -n "$ACTUAL_JOB_ID" ]; then
            echo ""
            echo "Job ID: $ACTUAL_JOB_ID"
            
            # Extract job directory path - clean extraction with proper trimming
            FULL_JOB_PATH=$(echo "$PREP_OUTPUT" | grep -m1 "Job directory:" | sed 's/^.*Job directory:[[:space:]]*//' | tr -d '\r' | awk '{$1=$1};1')
            
            if [ -n "$FULL_JOB_PATH" ] && [ -d "$FULL_JOB_PATH" ]; then
                echo "Job path: $FULL_JOB_PATH"
                
                # Disable glossary for baseline
                cat > "$FULL_JOB_PATH/.$ACTUAL_JOB_ID.env" << 'EOF'
TMDB_ENRICHMENT_ENABLED=false
GLOSSARY_CACHE_ENABLED=false
EOF
                
                echo "Starting baseline pipeline (this may take 15-20 minutes for 5-min clip)..."
                time ./run-pipeline.sh -j "$ACTUAL_JOB_ID"
                
                # Save results
                if [ -d "$FULL_JOB_PATH/subtitles" ] && ls "$FULL_JOB_PATH/subtitles/"*.srt &>/dev/null; then
                    cp "$FULL_JOB_PATH/subtitles/"*.srt test-results/baseline/ 2>/dev/null || true
                    cp "$FULL_JOB_PATH/logs/"*pipeline*.log test-results/baseline/ 2>/dev/null || true
                    echo "✓ Baseline test complete!"
                    echo "✓ Results saved to test-results/baseline/"
                    echo "$ACTUAL_JOB_ID" > test-results/baseline/job-id.txt
                else
                    echo "⚠ Baseline test may have failed. Check logs in $FULL_JOB_PATH/logs/"
                fi
            else
                echo "⚠ Could not find job directory: $FULL_JOB_PATH"
            fi
        else
            echo "⚠ Could not determine job ID from prepare-job output"
        fi
    fi
fi

echo ""

# Step 2: Glossary Test
echo "═══ Step 2: Glossary Test (With Glossary Enabled) ═══"
echo "This will run the pipeline WITH glossary to test improvements."
echo ""
read -p "Run glossary test? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running glossary test..."
    
    # Default video path
    DEFAULT_VIDEO="/Users/rpatel/Projects/cp-whisperx-app/in/Jaane Tu Ya Jaane Na 2008.mp4"
    
    # Check if baseline was run
    if [ -f "test-results/baseline/job-id.txt" ]; then
        BASELINE_JOB=$(cat test-results/baseline/job-id.txt)
        echo "Using same video as baseline test"
        VIDEO_PATH="$DEFAULT_VIDEO"
    else
        echo "Default video: $DEFAULT_VIDEO"
        read -p "Press Enter to use default, or enter different path: " VIDEO_PATH
        
        # Use default if empty
        if [ -z "$VIDEO_PATH" ]; then
            VIDEO_PATH="$DEFAULT_VIDEO"
        fi
    fi
    
    if [ -z "$VIDEO_PATH" ] || [ ! -f "$VIDEO_PATH" ]; then
        echo "⚠ No video file provided. Skipping glossary test."
        echo "To run manually later:"
        echo "  ./prepare-job.sh --media YOUR_VIDEO.mp4 --workflow translate --source-language hi --target-language en --end-time 00:05:00"
        echo "  # Then enable glossary in job config"
        echo "  ./run-pipeline.sh -j <job-id>"
    else
        # Prepare job with glossary enabled
        echo ""
        echo "Optional: Provide TMDB film title and year for better glossary results"
        echo "Default: Jaane Tu Ya Jaane Na (2008)"
        read -p "Film title (or press Enter for default): " FILM_TITLE
        
        # Use default if empty
        if [ -z "$FILM_TITLE" ]; then
            FILM_TITLE="Jaane Tu Ya Jaane Na"
            FILM_YEAR="2008"
            echo "Using default: $FILM_TITLE ($FILM_YEAR)"
        else
            read -p "Film year: " FILM_YEAR
        fi
        
        # Prepare job
        PREP_OUTPUT=$(./prepare-job.sh \
            --media "$VIDEO_PATH" \
            --workflow translate \
            --source-language hi \
            --target-language en \
            --start-time 00:00:00 \
            --end-time 00:05:00 \
            --user-id glossary 2>&1)
        
        echo "$PREP_OUTPUT"
        
        # Extract job ID from prepare-job output (macOS compatible)
        ACTUAL_JOB_ID=$(echo "$PREP_OUTPUT" | grep "Job created:" | awk '{print $3}')
        
        if [ -z "$ACTUAL_JOB_ID" ]; then
            # Fallback: try to extract from "Job ID:" line
            ACTUAL_JOB_ID=$(echo "$PREP_OUTPUT" | grep "Job ID:" | head -1 | awk '{print $NF}')
        fi
        
        if [ -n "$ACTUAL_JOB_ID" ]; then
            echo ""
            echo "Job ID: $ACTUAL_JOB_ID"
            
            # Extract job directory path - clean extraction with proper trimming
            FULL_JOB_PATH=$(echo "$PREP_OUTPUT" | grep -m1 "Job directory:" | sed 's/^.*Job directory:[[:space:]]*//' | tr -d '\r' | awk '{$1=$1};1')
            
            if [ -n "$FULL_JOB_PATH" ] && [ -d "$FULL_JOB_PATH" ]; then
                echo "Job path: $FULL_JOB_PATH"
                
                # Add TMDB info to job.json manually
                if [ -n "$FILM_TITLE" ] && [ -n "$FILM_YEAR" ]; then
                    python3 << PYEOF
import json
job_file = "$FULL_JOB_PATH/job.json"
with open(job_file, 'r') as f:
    job_data = json.load(f)
job_data['title'] = "$FILM_TITLE"
job_data['year'] = int("$FILM_YEAR")
with open(job_file, 'w') as f:
    json.dump(job_data, f, indent=2)
print(f"Added TMDB info: $FILM_TITLE ($FILM_YEAR)")
PYEOF
                fi
                
                # Enable glossary
                cat > "$FULL_JOB_PATH/.$ACTUAL_JOB_ID.env" << 'EOF'
TMDB_ENRICHMENT_ENABLED=true
GLOSSARY_CACHE_ENABLED=true
EOF
                
                echo "Starting pipeline with glossary (this may take 15-20 minutes for 5-min clip)..."
                time ./run-pipeline.sh -j "$ACTUAL_JOB_ID"
                
                # Save results
                if [ -d "$FULL_JOB_PATH/subtitles" ] && ls "$FULL_JOB_PATH/subtitles/"*.srt &>/dev/null; then
                    cp "$FULL_JOB_PATH/subtitles/"*.srt test-results/glossary/ 2>/dev/null || true
                    cp "$FULL_JOB_PATH/logs/"*pipeline*.log test-results/glossary/ 2>/dev/null || true
                    
                    if [ -f "$FULL_JOB_PATH/03_glossary_load/glossary_snapshot.json" ]; then
                        cp "$FULL_JOB_PATH/03_glossary_load/glossary_snapshot.json" test-results/glossary/
                    fi
                    
                    echo "✓ Glossary test complete!"
                    echo "✓ Results saved to test-results/glossary/"
                    echo "$ACTUAL_JOB_ID" > test-results/glossary/job-id.txt
                    echo ""
                    
                    # Validate glossary was used
                    echo "═══ Validation ═══"
                    echo -n "Glossary snapshot exists: "
                    [ -f "test-results/glossary/glossary_snapshot.json" ] && echo "✓" || echo "✗"
                    
                    echo -n "ASR bias terms used: "
                    grep -q "bias terms" test-results/glossary/*pipeline*.log 2>/dev/null && echo "✓" || echo "✗"
                    
                    echo -n "Translation glossary applied: "
                    grep -q "Glossary applied" test-results/glossary/*pipeline*.log 2>/dev/null && echo "✓" || echo "✗"
                else
                    echo "⚠ Glossary test may have failed. Check logs in $FULL_JOB_PATH/logs/"
                fi
            else
                echo "⚠ Could not find job directory: $FULL_JOB_PATH"
            fi
        else
            echo "⚠ Could not determine job ID from prepare-job output"
        fi
    fi
fi

echo ""

# Step 3: Quick Comparison
echo "═══ Step 3: Quick Quality Comparison ═══"
if [ -f "test-results/baseline/"*.srt ] && [ -f "test-results/glossary/"*.srt ]; then
    echo "Comparing baseline vs glossary..."
    
    BASELINE_SRT=$(ls test-results/baseline/*.srt 2>/dev/null | head -1)
    GLOSSARY_SRT=$(ls test-results/glossary/*.srt 2>/dev/null | head -1)
    
    if [ -n "$BASELINE_SRT" ] && [ -n "$GLOSSARY_SRT" ]; then
        # Count differences
        BASELINE_LINES=$(wc -l < "$BASELINE_SRT")
        GLOSSARY_LINES=$(wc -l < "$GLOSSARY_SRT")
        
        diff "$BASELINE_SRT" "$GLOSSARY_SRT" > test-results/quick-diff.txt 2>&1 || true
        CHANGES=$(grep -c "^<\|^>" test-results/quick-diff.txt 2>/dev/null || echo "0")
        
        echo ""
        echo "Baseline subtitle lines: $BASELINE_LINES"
        echo "Glossary subtitle lines: $GLOSSARY_LINES"
        echo "Changes detected: $CHANGES lines"
        echo ""
        
        if [ "$CHANGES" -gt "0" ]; then
            echo "Sample differences (first 20 changes):"
            head -40 test-results/quick-diff.txt 2>/dev/null | head -20
            echo ""
            echo "Full diff saved to: test-results/quick-diff.txt"
        fi
    else
        echo "Could not find subtitle files for comparison."
    fi
else
    echo "Run baseline and glossary tests first to compare results."
fi
echo ""

# Step 4: Cache Test
echo "═══ Step 4: Cache Performance Test ═══"
echo "This will run the same film again to test cache performance."
echo ""
read -p "Run cache test? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Get film info from glossary test
    if [ -f "test-results/glossary/job-id.txt" ]; then
        GLOSSARY_JOB=$(cat test-results/glossary/job-id.txt | cut -d: -f2 | tr -d ' ')
        GLOSSARY_CONFIG="in/$GLOSSARY_JOB/job.json"
        
        if [ -f "$GLOSSARY_CONFIG" ]; then
            VIDEO_PATH=$(python3 -c "import json; data=json.load(open('$GLOSSARY_CONFIG')); print(data.get('input_media',''))" 2>/dev/null || echo "")
            FILM_TITLE=$(python3 -c "import json; data=json.load(open('$GLOSSARY_CONFIG')); print(data.get('title',''))" 2>/dev/null || echo "")
            FILM_YEAR=$(python3 -c "import json; data=json.load(open('$GLOSSARY_CONFIG')); print(data.get('year',''))" 2>/dev/null || echo "")
        fi
    fi
    
    if [ -z "$VIDEO_PATH" ] || [ ! -f "$VIDEO_PATH" ]; then
        echo "⚠ Cannot determine video path. Please provide:"
        read -p "Path to Hindi video file: " VIDEO_PATH
        read -p "Film title: " FILM_TITLE
        read -p "Film year: " FILM_YEAR
    fi
    
    if [ -n "$VIDEO_PATH" ] && [ -f "$VIDEO_PATH" ]; then
        echo "Checking cache..."
        
        if [ -n "$FILM_TITLE" ] && [ -n "$FILM_YEAR" ]; then
            CACHE_SLUG=$(echo "$FILM_TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
            CACHE_DIR="glossary/cache/tmdb/${CACHE_SLUG}_${FILM_YEAR}"
            
            if [ -d "$CACHE_DIR" ]; then
                echo "✓ Cache exists for $FILM_TITLE ($FILM_YEAR)"
                ls -lah "$CACHE_DIR"
            else
                echo "⚠ No cache found. This might be the first run."
            fi
        fi
        echo ""
        
        echo "Running cache hit test..."
        
        # Prepare job (no TMDB flags - will be added to job.json)
        PREP_OUTPUT=$(./prepare-job.sh \
            --media "$VIDEO_PATH" \
            --workflow translate \
            --source-language hi \
            --target-language en \
            --start-time 00:00:00 \
            --end-time 00:05:00 \
            --user-id cache 2>&1)
        
        echo "$PREP_OUTPUT"
        
        # Extract job ID (macOS compatible)
        ACTUAL_JOB_ID=$(echo "$PREP_OUTPUT" | grep "Job created:" | awk '{print $3}')
        
        if [ -z "$ACTUAL_JOB_ID" ]; then
            ACTUAL_JOB_ID=$(echo "$PREP_OUTPUT" | grep "Job ID:" | head -1 | awk '{print $NF}')
        fi
        
        if [ -n "$ACTUAL_JOB_ID" ]; then
            echo ""
            echo "Job ID: $ACTUAL_JOB_ID"
            
            # Extract job directory path - clean extraction with proper trimming
            FULL_JOB_PATH=$(echo "$PREP_OUTPUT" | grep -m1 "Job directory:" | sed 's/^.*Job directory:[[:space:]]*//' | tr -d '\r' | awk '{$1=$1};1')
            
            if [ -n "$FULL_JOB_PATH" ] && [ -d "$FULL_JOB_PATH" ]; then
                # Add TMDB info to job.json if available
                if [ -n "$FILM_TITLE" ] && [ -n "$FILM_YEAR" ]; then
                    python3 << PYEOF
import json
job_file = "$FULL_JOB_PATH/job.json"
with open(job_file, 'r') as f:
    job_data = json.load(f)
job_data['title'] = "$FILM_TITLE"
job_data['year'] = int("$FILM_YEAR")
with open(job_file, 'w') as f:
    json.dump(job_data, f, indent=2)
print(f"Added TMDB info: $FILM_TITLE ($FILM_YEAR)")
PYEOF
                fi
                
                # Enable glossary and cache
                cat > "$FULL_JOB_PATH/.$ACTUAL_JOB_ID.env" << 'EOF'
TMDB_ENRICHMENT_ENABLED=true
GLOSSARY_CACHE_ENABLED=true
EOF
                
                echo "Starting pipeline (should be faster with cache hit)..."
                time ./run-pipeline.sh -j "$ACTUAL_JOB_ID" 2>&1 | tee test-results/cache-run.log
                
                # Check for cache hit
                echo ""
                echo -n "Cache hit detected: "
                grep -q "cache hit" "$FULL_JOB_PATH/logs/"*pipeline*.log 2>/dev/null && echo "✓" || echo "✗"
            else
                echo "⚠ Could not find job directory"
            fi
        else
            echo "⚠ Could not determine job ID"
        fi
    else
        echo "⚠ No video file provided. Skipping cache test."
    fi
    
else
    echo "Skipped cache test."
fi
echo ""

# Summary
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Testing Summary                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Test Results Directory: test-results/"
echo ""
echo "Completed Tests:"
[ -d "test-results/baseline" ] && echo "  ✓ Baseline test" || echo "  ✗ Baseline test (not run)"
[ -d "test-results/glossary" ] && echo "  ✓ Glossary test" || echo "  ✗ Glossary test (not run)"
[ -f "test-results/cache-run.log" ] && echo "  ✓ Cache test" || echo "  ✗ Cache test (not run)"
echo ""

echo "Next Steps:"
echo "1. Review test results in test-results/ directory"
echo "2. Compare baseline vs glossary subtitles manually"
echo "3. Check test-results/quick-diff.txt for changes"
echo "4. Follow docs/PRODUCTION_TESTING_PLAN.md for detailed testing"
echo ""

echo "Documentation:"
echo "  - docs/PRODUCTION_TESTING_PLAN.md (Full testing guide)"
echo "  - docs/GLOSSARY_IMPLEMENTATION_SUMMARY.md (Overview)"
echo ""

echo "✨ Quick start testing complete!"
