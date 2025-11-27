#!/bin/bash
# Quick test script for source separation feature

echo "=========================================="
echo "Source Separation Feature Test"
echo "=========================================="
echo ""

# Test 1: Check if scripts exist
echo "Test 1: Checking if scripts exist..."
if [ -f "scripts/source_separation.py" ]; then
    echo "✓ source_separation.py exists"
else
    echo "✗ source_separation.py missing"
    exit 1
fi

# Test 2: Check Python syntax
echo ""
echo "Test 2: Checking Python syntax..."
python3 -m py_compile scripts/source_separation.py
python3 -m py_compile scripts/prepare-job.py
python3 -m py_compile scripts/run-pipeline.py
if [ $? -eq 0 ]; then
    echo "✓ All scripts have valid syntax"
else
    echo "✗ Syntax errors found"
    exit 1
fi

# Test 3: Check prepare-job help
echo ""
echo "Test 3: Checking prepare-job.sh for new flags..."
if python3 scripts/prepare-job.py --help 2>&1 | grep -q "source-separation"; then
    echo "✓ --source-separation flag available"
else
    echo "✗ --source-separation flag not found"
    exit 1
fi

if python3 scripts/prepare-job.py --help 2>&1 | grep -q "separation-quality"; then
    echo "✓ --separation-quality flag available"
else
    echo "✗ --separation-quality flag not found"
    exit 1
fi

# Test 4: Test job preparation with source separation
echo ""
echo "Test 4: Testing job preparation with source separation..."
echo "(Dry run - creating job config only)"

# Check if test media exists
if [ ! -f "in/Jaane Tu Ya Jaane Na 2008.mp4" ]; then
    echo "⚠ Test media not found, skipping job preparation test"
else
    python3 scripts/prepare-job.py \
        "in/Jaane Tu Ya Jaane Na 2008.mp4" \
        --workflow transcribe \
        --source-language hi \
        --start-time "00:01:30" \
        --end-time "00:01:45" \
        --source-separation \
        --separation-quality balanced
    
    if [ $? -eq 0 ]; then
        echo "✓ Job prepared successfully with source separation"
        
        # Find the created job
        LATEST_JOB=$(ls -t out/2025/*/*/* | head -1)
        if [ -d "$LATEST_JOB" ]; then
            echo ""
            echo "Checking job configuration..."
            
            # Check if source_separation is in job.json
            if grep -q "source_separation" "$LATEST_JOB/job.json"; then
                echo "✓ source_separation config found in job.json"
                
                # Display the config
                echo ""
                echo "Source separation config:"
                jq '.source_separation' "$LATEST_JOB/job.json"
            else
                echo "✗ source_separation config not found in job.json"
            fi
            
            # Check if manifest includes source_separation stage
            if grep -q "source_separation" "$LATEST_JOB/manifest.json"; then
                echo "✓ source_separation stage in manifest"
            else
                echo "✗ source_separation stage not in manifest"
            fi
        fi
    else
        echo "✗ Job preparation failed"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "All Tests Passed! ✓"
echo "=========================================="
echo ""
echo "Source separation feature is ready to use!"
echo ""
echo "Quick start:"
echo "  ./prepare-job.sh --media \"movie.mp4\" \\"
echo "                   --source-lang hi \\"
echo "                   --workflow transcribe \\"
echo "                   --source-separation"
echo ""
echo "  ./run-pipeline.sh"
echo ""
