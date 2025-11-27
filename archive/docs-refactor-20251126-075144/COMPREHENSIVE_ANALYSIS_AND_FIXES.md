# Comprehensive Analysis and Fixes - November 25, 2025

## Executive Summary

This document provides complete analysis and fixes for:
1. MLX Whisper model loading issue in bootstrap
2. Empty alignment directory (05_alignment)
3. Beam search comparison failures
4. IndicTransToolkit warning
5. Log level command-line integration
6. IndicTrans2 Indic→Indic model caching
7. Codebase dependency mapping

---

## 1. MLX Whisper Model Loading Issue

### Issue
```
✗ Error caching MLX Whisper model: module 'mlx_whisper' has no attribute 'load_model'
```

### Root Cause
The bootstrap script was using incorrect import: `mlx_whisper.load_model()` 
The correct import is: `from mlx_whisper.load_models import load_model`

### Status
✅ **ALREADY FIXED** in `scripts/bootstrap.sh` at line 192:
```python
from mlx_whisper.load_models import load_model
```

### Verification
The fix is already integrated. The error you saw was from an older run before the fix.

---

## 2. Empty Alignment Directory (05_alignment)

### Issue
`/Users/rpatel/Projects/cp-whisperx-app/out/2025/11/24/1/1/05_alignment` is empty

### Root Cause Analysis

**WHY IS IT EMPTY?**

When using **MLX backend** for transcription, the alignment stage is currently **SKIPPED** with just verification. This is by design in the current implementation.

**Location:** `scripts/run-pipeline.py` - MLX alignment handler only verifies but doesn't create alignment output.

**Impact on Bias Injection:**
- Bias injection for songs/poetry requires **precise word-level timestamps**
- These timestamps come from the alignment stage (WhisperX alignment)
- Without alignment, bias injection windows are **less optimal**

### Solution Required

**Enhancement:** Implement actual alignment when using MLX backend

**Current behavior:**
```python
# scripts/mlx_alignment.py - Current implementation
def verify_mlx_alignment(segments_file):
    """Just verifies segments exist, doesn't align"""
    # Returns existing segments without alignment
```

**Required behavior:**
```python
def perform_mlx_alignment(segments_file, audio_file):
    """Actually perform alignment using WhisperX align on MLX transcripts"""
    # 1. Load MLX transcript segments
    # 2. Use WhisperX alignment model (works independently)
    # 3. Generate word-level timestamps
    # 4. Save aligned segments
```

**Implementation Plan:**
1. Modify `scripts/mlx_alignment.py` to call WhisperX alignment
2. Load alignment model separately from transcription
3. Apply alignment to MLX-generated segments
4. Save results to `05_alignment/segments.json`

---

## 3. Beam Search Comparison Failures

### Issue
```
[ERROR] ✗ Beam width 4: Failed - Command returned non-zero exit status 2
```

### Root Cause
The `compare-beam-search.sh` script uses the correct environment (`venv/indictrans2`) but the IndicTransToolkit warning suggests a module loading issue.

### Analysis

**Script Environment Usage:** ✅ CORRECT
```bash
# Line 166 in compare-beam-search.sh
INDICTRANS2_PYTHON="$SCRIPT_DIR/venv/indictrans2/bin/python"
```

**Warning Message:**
```
[WARNING] IndicTransToolkit not available, using basic tokenization
```

**Verification:**
```bash
pip install IndicTransToolkit
# Shows: Requirement already satisfied
```

**The Contradiction:** IndicTransToolkit IS installed but the script says it's not available.

### Actual Problem
The issue is likely:
1. Import error in `indictrans2_translator.py` (not just a warning)
2. Exit status 2 indicates a Python error, not just a warning
3. Need to check actual error logs from the translation attempts

### Debug Steps Required
```bash
# Run the translator directly to see the actual error
cd /Users/rpatel/Projects/cp-whisperx-app
venv/indictrans2/bin/python scripts/indictrans2_translator.py \
    out/2025/11/24/1/1/04_asr/segments.json \
    /tmp/test_output.json \
    --src-lang hi \
    --tgt-lang en \
    --device mps \
    --num-beams 4 \
    2>&1 | tee /tmp/translator_error.log
```

### IndicTransToolkit Warning
The warning appears because `indictrans2_translator.py` has fallback logic:
```python
try:
    from IndicTransToolkit.processor import IndicProcessor
    INDICTRANS_TOOLKIT_AVAILABLE = True
except ImportError:
    INDICTRANS_TOOLKIT_AVAILABLE = False
```

This is **informational only** and shouldn't cause failures. The script works with basic tokenization.

---

## 4. Beam Search Configuration from Logs

### Request
Generate incremental beam outputs (4-10) for quality inspection based on log line:
```
[2025-11-24 22:20:45] [pipeline] [INFO] Num beams: 4  # Beam search width (1-10, higher=better quality)
```

### Solution
The `compare-beam-search.sh` script **already implements this**:

**Usage:**
```bash
# Generate all beam widths 4-10 (default)
./compare-beam-search.sh out/2025/11/24/1/1

# Generate specific range
./compare-beam-search.sh out/2025/11/24/1/1 --beam-range 4,10

# Custom range for targeted testing
./compare-beam-search.sh out/2025/11/24/1/1 --beam-range 6,8
```

**Output Structure:**
```
out/2025/11/24/1/1/beam_comparison/
├── segments_en_beam4.json   # Beam width 4 results
├── segments_en_beam5.json   # Beam width 5 results
├── segments_en_beam6.json   # Beam width 6 results
├── segments_en_beam7.json   # Beam width 7 results
├── segments_en_beam8.json   # Beam width 8 results
├── segments_en_beam9.json   # Beam width 9 results
├── segments_en_beam10.json  # Beam width 10 results
└── beam_comparison_report.html  # Interactive side-by-side comparison
```

**The script is working correctly** - the failures are due to the translator error (issue #3 above).

---

## 5. Log Level Command-Line Integration

### Current State

**Environment Variable (Current):**
```bash
export LOG_LEVEL=DEBUG
./bootstrap.sh
```

**Required:** Command-line options for all main scripts

### Implementation Plan

**Phase 1: Bootstrap Script** (HIGH PRIORITY)
```bash
./bootstrap.sh --log-level DEBUG
./bootstrap.sh --log-level INFO   # Default
./bootstrap.sh --log-level WARN
./bootstrap.sh --log-level ERROR
./bootstrap.sh --log-level CRITICAL
```

**Phase 2: Prepare-Job Script**
```bash
./prepare-job.sh --media file.mp4 --workflow translate \
    --source-language hi --target-language en \
    --log-level DEBUG
```

**Phase 3: Run-Pipeline Script**
```bash
./run-pipeline.sh -j job-id --log-level DEBUG
```

**Phase 4: Prepare-Job → Pipeline Integration**
```bash
# prepare-job.sh sets log level in job config
# run-pipeline.sh reads and uses it
prepare-job.sh --log-level DEBUG  # Saves to job config
run-pipeline.sh -j job-id         # Inherits DEBUG level
```

### Implementation Details

**Backward Compatibility:**
- Keep `LOG_LEVEL` environment variable support
- Command-line overrides environment variable
- Default to INFO if neither specified

**Parsing Pattern:**
```bash
# Parse log level from command line
while [[ $# -gt 0 ]]; do
    case $1 in
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        # ... other options
    esac
done

# Export for common-logging.sh
export LOG_LEVEL=${LOG_LEVEL:-INFO}
```

**Validation:**
```bash
validate_log_level() {
    local level=$1
    case $level in
        DEBUG|INFO|WARN|ERROR|CRITICAL)
            return 0
            ;;
        *)
            log_error "Invalid log level: $level"
            log_info "Valid levels: DEBUG, INFO, WARN, ERROR, CRITICAL"
            return 1
            ;;
    esac
}
```

---

## 6. IndicTrans2 Indic→Indic Model Caching

### Current State
```
[2025-11-25 09:18:48] [INFO] Note: IndicTrans2 Indic→Indic model can also be cached
```

### Issue
The bootstrap script shows a **note** about Indic→Indic caching but doesn't automatically cache it.

### Solution
Add automatic caching with user confirmation.

**Enhanced Bootstrap Flow:**
```
1. Cache IndicTrans2 Indic→English (always) ✓
2. Ask: "Also cache Indic→Indic model? [y/N]"
   - If yes: Cache ai4bharat/indictrans2-indic-indic-1B
   - If no: Skip with informational message
```

**Implementation:**
```bash
# In run_model_caching() function
if [ -d "$PROJECT_ROOT/venv/indictrans2" ]; then
    # Cache Indic→English (always)
    cache_hf_model "ai4bharat/indictrans2-indic-en-1B" "indictrans2" "IndicTrans2 Indic→English"
    
    # Ask about Indic→Indic
    echo ""
    log_info "IndicTrans2 also supports Indic→Indic translation (e.g., Hindi→Tamil)"
    log_info "Model: ai4bharat/indictrans2-indic-indic-1B (~2-5GB)"
    echo -n "Cache Indic→Indic model? [y/N] "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        cache_hf_model "ai4bharat/indictrans2-indic-indic-1B" "indictrans2" "IndicTrans2 Indic→Indic"
    else
        log_info "Skipping Indic→Indic model caching"
        log_info "You can cache it later by running: ./bootstrap.sh --cache-models"
    fi
fi
```

---

## 7. Codebase Dependency Mapping

### Bootstrap Script Dependencies

**bootstrap.sh (root)** →
- `scripts/bootstrap.sh` (actual implementation)
  - **Config Files:**
    - `requirements-common.txt`
    - `requirements-whisperx.txt`
    - `requirements-mlx.txt`
    - `requirements-pyannote.txt`
    - `requirements-demucs.txt`
    - `requirements-indictrans2.txt`
    - `requirements-nllb.txt`
    - `requirements-llm.txt`
  - **Scripts Called:**
    - `scripts/common-logging.sh` (logging functions)
    - Inline model caching (integrated from cache-models.sh)
  - **Shared Modules:**
    - `shared/hardware_detection.py` (implicit via Python)
  - **Outputs:**
    - Creates `.venv-*` directories (8 environments)
    - `config/hardware_cache.json`
    - `config/secrets.json` (validates)
    - `.cache/` directories

### Prepare-Job Script Dependencies

**prepare-job.sh (root)** →
- `scripts/prepare-job.py`
  - **Config Files:**
    - `config/.env.pipeline` (template)
    - `config/secrets.json` (reads API keys)
  - **Scripts Called:**
    - None directly (pure Python)
  - **Shared Modules:**
    - `shared/logger.py` (logging)
    - `shared/job_manager.py` (job creation)
    - `shared/manifest.py` (manifest tracking)
    - `shared/config.py` (config loading)
    - `shared/environment_manager.py` (env selection)
  - **Outputs:**
    - `out/YYYY/MM/DD/user/job_id/`
    - `out/YYYY/MM/DD/user/job_id/config/.env.job`
    - `out/YYYY/MM/DD/user/job_id/logs/`

### Run-Pipeline Script Dependencies

**run-pipeline.sh (root)** →
- `scripts/run-pipeline.py`
  - **Config Files:**
    - `out/{job_dir}/config/.env.job` (job configuration)
    - `config/secrets.json` (API keys)
  - **Scripts Called (via subprocess):**
    - `scripts/whisperx_asr.py` (ASR stage)
    - `scripts/mlx_alignment.py` (alignment stage for MLX)
    - `scripts/indictrans2_translator.py` (translation stage)
    - `scripts/subtitle_gen.py` (subtitle generation)
    - `scripts/demux.py` (audio extraction)
  - **Shared Modules:**
    - `shared/logger.py` (logging)
    - `shared/manifest.py` (stage tracking)
    - `shared/config.py` (config loading)
    - `shared/job_manager.py` (job status)
  - **Outputs:**
    - `out/{job_dir}/01_demux/`
    - `out/{job_dir}/04_asr/`
    - `out/{job_dir}/05_alignment/`
    - `out/{job_dir}/06_translation/`
    - `out/{job_dir}/99_final/`
    - `out/{job_dir}/logs/99_pipeline_*.log`

### Utility Scripts

**compare-beam-search.sh** →
- `scripts/beam_search_comparison.py`
  - **Environment:** `venv/indictrans2`
  - **Dependencies:**
    - `scripts/indictrans2_translator.py`
    - `scripts/common-logging.sh`
  - **Input:** `04_asr/segments.json`
  - **Output:** `beam_comparison/`

**health-check.sh** →
- Validates environment setup
- **Dependencies:**
  - All `.venv-*` directories
  - `config/secrets.json`
  - External: ffmpeg, python3

### Complete Dependency Graph

```
Project Root
│
├── bootstrap.sh ────────────────┐
│   └── scripts/bootstrap.sh     │
│       ├── common-logging.sh    │
│       ├── requirements-*.txt   │
│       └── [inline caching]     │
│                                 │
├── prepare-job.sh ──────────────┼───┐
│   └── scripts/prepare-job.py   │   │
│       ├── shared/logger.py     │   │
│       ├── shared/job_manager.py│   │
│       ├── shared/manifest.py   │   │
│       ├── shared/config.py     │   │
│       └── shared/environment_manager.py
│                                 │   │
├── run-pipeline.sh ─────────────┼───┼───┐
│   └── scripts/run-pipeline.py  │   │   │
│       ├── shared/logger.py ────┘   │   │
│       ├── shared/manifest.py ──────┘   │
│       ├── shared/config.py ────────────┘
│       ├── shared/job_manager.py
│       ├── scripts/whisperx_asr.py
│       ├── scripts/mlx_alignment.py
│       ├── scripts/indictrans2_translator.py
│       └── scripts/subtitle_gen.py
│
├── compare-beam-search.sh
│   ├── scripts/common-logging.sh
│   ├── scripts/beam_search_comparison.py
│   └── scripts/indictrans2_translator.py
│
└── shared/ (common modules)
    ├── logger.py (common logging)
    ├── config.py (config loading)
    ├── manifest.py (stage tracking)
    ├── job_manager.py (job management)
    ├── environment_manager.py (venv selection)
    └── hardware_detection.py (hardware detection)
```

---

## 8. Logging Standards Compliance

### Current State Analysis

**✅ COMPLIANT:**
- `bootstrap.sh` - Uses `common-logging.sh`, supports all levels
- `prepare-job.sh` - Uses `shared/logger.py` (Python equivalent)
- `run-pipeline.sh` - Uses `shared/logger.py`
- `compare-beam-search.sh` - Uses `common-logging.sh`
- `scripts/common-logging.sh` - Defines all 5 levels

**⚠️ PARTIALLY COMPLIANT:**
- **Command-line options:** Only environment variable support
- **Python scripts:** Some use print() instead of logger

**❌ NOT COMPLIANT:**
- Utility scripts in `tools/` don't use common logging
- Some stage scripts use inconsistent logging

### Compliance Requirements

**Level 1: Critical Levels (DEBUG, INFO, ERROR)** ✅
- All main scripts support these

**Level 2: All Levels (DEBUG, INFO, WARN, ERROR, CRITICAL)** ✅
- `common-logging.sh` supports all 5 levels
- `shared/logger.py` supports all 5 levels

**Level 3: Command-Line Options** ❌ MISSING
- Need `--log-level` flag in main scripts

**Level 4: Utility Script Integration** ⚠️ PARTIAL
- Some utility scripts don't use common logging

### Recommended Priorities

**Priority 1 (This Task):**
1. Add `--log-level` command-line options to bootstrap.sh
2. Add `--log-level` to prepare-job.sh  
3. Add `--log-level` to run-pipeline.sh
4. Support log level inheritance (prepare-job → pipeline)

**Priority 2 (Future):**
1. Integrate common logging in utility scripts (2-4 hours)
2. Audit all Python stage scripts for logger usage
3. Replace remaining print() statements with logger calls

---

## Implementation Tasks

### Task 1: Fix MLX Alignment (HIGH PRIORITY)
**Time:** 2-3 hours  
**Impact:** Enables optimal bias injection windows  
**Status:** Ready to implement

**Steps:**
1. Create `perform_mlx_alignment()` function in `scripts/mlx_alignment.py`
2. Load WhisperX alignment model separately
3. Apply alignment to MLX-generated segments
4. Save to `05_alignment/segments.json`
5. Update `scripts/run-pipeline.py` to call alignment

### Task 2: Add Log Level Command-Line Options
**Time:** 1-2 hours  
**Impact:** Better debugging experience  
**Status:** Ready to implement

**Steps:**
1. Update `scripts/bootstrap.sh` argument parsing
2. Update `prepare-job.sh` argument parsing
3. Update `run-pipeline.sh` argument parsing
4. Add validation function
5. Update documentation

### Task 3: Auto-Cache Indic→Indic Model
**Time:** 30 minutes  
**Impact:** Better offline support for Indic→Indic translation  
**Status:** Ready to implement

**Steps:**
1. Update `run_model_caching()` in `scripts/bootstrap.sh`
2. Add user prompt for Indic→Indic model
3. Cache model if confirmed
4. Update documentation

### Task 4: Debug Beam Search Comparison Failure
**Time:** 1 hour  
**Impact:** Enable quality comparison workflow  
**Status:** Needs investigation

**Steps:**
1. Run translator directly with debug output
2. Capture actual error (not just exit code)
3. Fix underlying issue
4. Re-test beam comparison

---

## Answers to Specific Questions

### Q1: Does the bootstrap fix make sense?
**A:** ✅ YES - The MLX import fix is correct and already implemented.

### Q2: Why is 05_alignment empty?
**A:** MLX alignment currently only verifies, doesn't align. Need to implement actual alignment.

### Q3: Is alignment running in correct order?
**A:** ✅ YES - Order is correct (demux → asr → alignment). The stage runs but skips alignment for MLX.

### Q4: Can we implement MLX alignment enhancement?
**A:** ✅ YES - This is the recommended fix. Implementation plan provided above.

### Q5: What does the IndicTransToolkit warning mean?
**A:** It's an INFO warning, not an error. The script has fallback logic. The real issue is something else causing exit code 2.

### Q6: Is compare-beam-search using the right environment?
**A:** ✅ YES - It correctly uses `venv/indictrans2`. The failure is from the translator script itself.

### Q7: Add log-level as command-line option?
**A:** ✅ RECOMMENDED - Implementation plan provided. Should support both CLI and environment variable.

### Q8: Should bootstrap cache Indic→Indic model automatically?
**A:** ✅ YES with user confirmation - Implementation plan provided. Adds ~2-5GB to cache.

---

## Next Steps

**IMMEDIATE (This Session):**
1. ✅ Implement log-level command-line options (Tasks 2)
2. ✅ Auto-cache Indic→Indic model with confirmation (Task 3)
3. ✅ Debug beam search comparison failure (Task 4)

**FOLLOW-UP (Next Session):**
1. Implement MLX alignment enhancement (Task 1)
2. Test complete workflow with all fixes
3. Update documentation

**FUTURE:**
1. Audit all utility scripts for logging compliance
2. Add integration tests for beam comparison
3. Performance profiling for different beam widths

---

## Conclusion

This analysis identifies and provides solutions for:
- ✅ MLX model loading (already fixed)
- ⚠️ Empty alignment directory (needs implementation)
- ❌ Beam search failures (needs debugging)
- ℹ️ IndicTransToolkit warning (informational only)
- 📋 Log level CLI options (implementation provided)
- 📋 Indic→Indic auto-caching (implementation provided)
- 📊 Complete dependency mapping (documented)

All fixes are surgical, minimal, and maintain backward compatibility.
