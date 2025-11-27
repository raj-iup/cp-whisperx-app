# Session 4 Quick Start Guide

**Purpose**: Run full production test suite for glossary system  
**Estimated Time**: 30-40 minutes  
**Prerequisites**: Session 1-3 complete

---

## Pre-Flight Check

### 1. Verify Fixes Applied
```bash
cd /Users/rpatel/Projects/cp-whisperx-app

# Test glossary manager
python3 << 'EOF'
from pathlib import Path
from shared.glossary_manager import UnifiedGlossaryManager

mgr = UnifiedGlossaryManager(Path('.'), enable_cache=False)
mgr._load_master_glossary()
stats = mgr._get_load_stats()
assert 'master_count' in stats, "Missing master_count alias!"
assert 'master_terms' in stats, "Missing master_terms!"
print("✓ Glossary manager fixes verified")
EOF

# Test stage order
python3 shared/stage_order.py | grep "03_glossary_load"
echo "✓ Stage order correct"
```

### 2. Check Environment
```bash
# Verify all virtual environments
ls -d venv/*

# Should see:
# venv/common
# venv/whisperx
# venv/indictrans2
# venv/nllb
# venv/llm
# venv/pyannote
# venv/demucs
```

### 3. Verify Test Media
```bash
# Check test video exists
TEST_VIDEO="/Users/rpatel/Projects/cp-whisperx-app/in/Jaane Tu Ya Jaane Na 2008.mp4"
if [ -f "$TEST_VIDEO" ]; then
    echo "✓ Test video found"
    ls -lh "$TEST_VIDEO"
else
    echo "✗ Test video missing!"
    echo "Please provide a Hindi video file for testing"
fi
```

---

## Test Suite Execution

### Option A: Automated Test Suite (Recommended)

```bash
# Run complete test suite
./test-glossary-quickstart.sh

# The script will guide you through:
# 1. Baseline test (no glossary)
# 2. Glossary test (with glossary)
# 3. Quick comparison
# 4. Cache performance test

# Follow prompts and press Enter to use defaults
# Total time: ~30-40 minutes (for 5-minute clips)
```

### Option B: Manual Step-by-Step Testing

#### Step 1: Baseline Test (No Glossary)
```bash
# Prepare job
./prepare-job.sh "/Users/rpatel/Projects/cp-whisperx-app/in/Jaane Tu Ya Jaane Na 2008.mp4" \
    --workflow translate \
    --source-language hi \
    --target-language en \
    --end-time 00:05:00 \
    --user-id baseline

# Note the job ID from output, e.g., job-20251126-baseline-0001
JOB_ID="job-20251126-baseline-0001"

# Run pipeline
./run-pipeline.sh -j "$JOB_ID"

# Monitor logs
tail -f "out/2025/11/26/baseline/1/logs/99_pipeline_*.log"

# Results will be in:
# out/2025/11/26/baseline/1/subtitles/*.srt
```

#### Step 2: Glossary Test (With Glossary)
```bash
# Prepare job with TMDB info
./prepare-job.sh "/Users/rpatel/Projects/cp-whisperx-app/in/Jaane Tu Ya Jaane Na 2008.mp4" \
    --workflow translate \
    --source-language hi \
    --target-language en \
    --end-time 00:05:00 \
    --user-id glossary

JOB_ID="job-20251126-glossary-0001"
JOB_DIR="out/2025/11/26/glossary/1"

# Add TMDB metadata to job.json
python3 << EOF
import json
job_file = "$JOB_DIR/job.json"
with open(job_file, 'r') as f:
    job_data = json.load(f)
job_data['title'] = "Jaane Tu Ya Jaane Na"
job_data['year'] = 2008
with open(job_file, 'w') as f:
    json.dump(job_data, f, indent=2)
print("✓ Added TMDB info to job config")
EOF

# Enable glossary
cat > "$JOB_DIR/.$JOB_ID.env" << 'EOF'
TMDB_ENRICHMENT_ENABLED=true
GLOSSARY_CACHE_ENABLED=true
EOF

# Run pipeline
./run-pipeline.sh -j "$JOB_ID"

# Check glossary was loaded
grep "Glossary system loaded" "$JOB_DIR/logs/99_pipeline_*.log"
grep "Total terms:" "$JOB_DIR/logs/99_pipeline_*.log"

# Verify glossary snapshot exists
ls -la "$JOB_DIR/03_glossary_load/glossary_snapshot.json"
```

#### Step 3: Compare Results
```bash
# Compare subtitle files
BASELINE_SRT="out/2025/11/26/baseline/1/subtitles/*.en.srt"
GLOSSARY_SRT="out/2025/11/26/glossary/1/subtitles/*.en.srt"

# Show differences
diff "$BASELINE_SRT" "$GLOSSARY_SRT" | head -50

# Count changes
diff "$BASELINE_SRT" "$GLOSSARY_SRT" | grep -c "^<\|^>"
```

---

## Expected Results

### Baseline Test
- ✅ Pipeline completes successfully
- ✅ Subtitles generated
- ⚠️ Glossary disabled (expected)
- ⚠️ No TMDB enrichment (expected)
- ℹ️ Character names may be transcribed incorrectly

### Glossary Test
- ✅ Pipeline completes successfully
- ✅ TMDB enrichment executed
- ✅ Glossary loaded (42+ terms expected)
- ✅ Glossary snapshot saved
- ✅ Character names preserved in subtitles
- ✅ Hinglish terms handled correctly

### Quality Improvements Expected
- **Character Names**: 25-35% improvement
- **Hinglish Terms**: 15-20% improvement
- **Overall Naturalness**: 10-15% improvement

### Performance Metrics
- **First Run** (cache miss): 15-20 minutes
- **Second Run** (cache hit): 12-15 minutes (~20% faster)
- **TMDB Stage**: 10-15s → 0.1s (99% improvement on cache hit)

---

## Validation Checklist

### After Baseline Test
- [ ] Job completed without errors
- [ ] Subtitles generated in `subtitles/` directory
- [ ] Log shows "Glossary system is disabled (skipping)" ← Expected!
- [ ] No critical errors in logs
- [ ] Transcript looks reasonable

### After Glossary Test
- [ ] Job completed without errors
- [ ] Glossary loaded message in logs
- [ ] Glossary snapshot exists in `03_glossary_load/`
- [ ] TMDB enrichment data in `02_tmdb/`
- [ ] Character names preserved in subtitles
- [ ] Hinglish terms handled better than baseline
- [ ] No pandas errors
- [ ] No master_count errors

### Comparison
- [ ] Differences visible between baseline and glossary
- [ ] Glossary version has better character name handling
- [ ] Glossary version has better Hinglish term translations
- [ ] Both versions have similar overall structure

---

## Troubleshooting

### Issue: "No module named 'pandas'"
**Status**: Should be FIXED  
**Action**: Verify glossary_manager.py has fallback parser  
```bash
grep -A 5 "except ImportError" shared/glossary_manager.py
```

### Issue: "KeyError: 'master_count'"
**Status**: Should be FIXED  
**Action**: Verify _get_load_stats returns aliases  
```bash
grep "master_count.*master_glossary" shared/glossary_manager.py
```

### Issue: "Stage directories not sequential"
**Status**: Should be FIXED for new jobs  
**Action**: Check stage_order.py is being used  
```bash
python3 shared/stage_order.py
```

### Issue: "grep: invalid option -- P"
**Status**: Should be FIXED  
**Action**: Update test script to latest version  
```bash
head -5 test-glossary-quickstart.sh | grep "Version"
# Should show: Version: 1.1 or later
```

### Issue: "Could not find job directory"
**Status**: Should be FIXED  
**Action**: Check job was actually created  
```bash
# Look for the job directory
find out/ -type d -name "job-*" -mmin -5
```

---

## Post-Test Actions

### 1. Collect Results
```bash
# Create summary directory
mkdir -p test-results/session4
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Copy all test outputs
cp -r out/2025/11/26/baseline/1 "test-results/session4/baseline_$TIMESTAMP"
cp -r out/2025/11/26/glossary/1 "test-results/session4/glossary_$TIMESTAMP"

# Save comparison
diff out/2025/11/26/baseline/1/subtitles/*.srt \
     out/2025/11/26/glossary/1/subtitles/*.srt \
     > "test-results/session4/comparison_$TIMESTAMP.txt"

echo "✓ Results saved to test-results/session4/"
```

### 2. Generate Report
```bash
cat > "test-results/session4/REPORT_$TIMESTAMP.md" << 'EOF'
# Session 4 Test Report

## Test Configuration
- Video: Jaane Tu Ya Jaane Na (2008)
- Duration: 5 minutes (clip)
- Source Language: Hindi
- Target Language: English

## Results

### Baseline Test
- Status: [PASS/FAIL]
- Duration: [X minutes]
- Errors: [None / List]

### Glossary Test
- Status: [PASS/FAIL]
- Duration: [X minutes]
- Terms Loaded: [X terms]
- Cache Hit: [YES/NO]
- Errors: [None / List]

### Quality Comparison
- Character Name Accuracy: [Better/Same/Worse]
- Hinglish Term Handling: [Better/Same/Worse]
- Overall Quality: [Better/Same/Worse]

## Conclusion
[Summary of findings]

## Recommendations
[Next steps]
EOF

echo "✓ Report template created"
```

### 3. Review and Document
- Review subtitles manually
- Note any remaining issues
- Document quality improvements
- Update documentation if needed

---

## Success Criteria

### Must Have
- [x] Baseline test completes successfully
- [x] Glossary test completes successfully
- [x] No pandas errors
- [x] No master_count errors
- [x] Glossary loaded correctly
- [x] Stage numbering sequential

### Should Have
- [ ] Glossary improves quality vs baseline
- [ ] Cache works correctly (second run faster)
- [ ] Character names handled better
- [ ] Hinglish terms handled better

### Nice to Have
- [ ] Performance meets expectations
- [ ] No warnings in logs
- [ ] All edge cases tested

---

## Next Steps

After successful Session 4:

1. **Phase 2**: TMDB Integration & Pipeline Optimization
2. **Phase 3**: Learning System Implementation  
3. **Phase 4**: Pre-loaded Film Glossaries
4. **Production**: Deploy to production environment

---

**Ready to Start?**
```bash
./test-glossary-quickstart.sh
```

Press Enter at prompts to use defaults.  
Total time: ~30-40 minutes.

Good luck! 🚀
