# AD-014 Performance Validation

**Date:** 2025-12-08  
**Status:** ⏳ IN PROGRESS  
**Test Run:** First Run (Generating Baseline)

---

## Test Configuration

**Media:** `in/Energy Demand in AI.mp4`  
**Media ID:** `1e9af679b5d233109b03d5be25526ab5...`  
**Workflow:** Transcribe  
**Job:** job-20251208-rpatel-0004  
**Cache Status:** No cache (first run - will generate baseline)

---

## Test Execution

### Run 1: Baseline Generation (IN PROGRESS)

**Started:** 2025-12-08 08:26:31  
**Expected Duration:** 2-5 minutes  
**Purpose:** Generate baseline cache for subsequent runs

**Stages:**
- ✅ demux: 1.0s (audio extraction complete)
- ⏳ source_separation: Running...
- ⏳ pyannote_vad: Pending
- ⏳ whisperx_asr: Pending
- ⏳ alignment: Pending

**Expected Baseline Files:**
```
~/.cp-whisperx/cache/media/1e9af679b5d233109b03d5be25526ab5.../baseline/
├── audio.wav           # Extracted audio
├── vad.json            # VAD segments
├── segments.json       # ASR segments
├── aligned.json        # Aligned segments
└── metadata.json       # Baseline metadata
```

---

### Run 2: Cached Run (PLANNED)

**Status:** Will run after Run 1 completes  
**Expected Duration:** ~30 seconds (70-80% speedup)  
**Purpose:** Validate caching speedup

**Expected Behavior:**
1. Detect existing baseline via media_id
2. Restore cached files to job directory
3. Skip stages: demux, source_separation, pyannote_vad, whisperx_asr, alignment
4. Only run post-processing stages (if any)
5. Complete in ~30 seconds vs ~2-5 minutes

---

## Performance Metrics

### Expected Results

| Metric | First Run | Second Run | Speedup |
|--------|-----------|------------|---------|
| demux | 1-2s | <1s (cached) | 50%+ |
| source_separation | 30-60s | <1s (cached) | 95%+ |
| pyannote_vad | 10-30s | <1s (cached) | 95%+ |
| whisperx_asr | 60-120s | <1s (cached) | 95%+ |
| alignment | 30-60s | <1s (cached) | 95%+ |
| **Total** | **2-5 min** | **~30s** | **70-80%** |

### Actual Results

**Run 1:** ⏳ IN PROGRESS  
**Run 2:** ⏳ PENDING

---

## Test Scripts Created

### 1. Quick Validation Script
**File:** `tests/manual/caching/quick-validation.sh`  
**Purpose:** Fast validation using transcribe workflow  
**Duration:** 2-5 minutes first run, ~30 seconds second run  
**Usage:**
```bash
./tests/manual/caching/quick-validation.sh
```

### 2. Performance Validation Script
**File:** `tests/manual/caching/run-performance-validation.sh`  
**Purpose:** Interactive test selection (transcribe, subtitle, or both)  
**Duration:** Varies by workflow  
**Usage:**
```bash
./tests/manual/caching/run-performance-validation.sh
# Prompts for workflow selection
```

---

## Validation Checklist

### Integration Testing
- [x] Scripts created and executable
- [x] Media files validated (both exist)
- [x] Media IDs computed successfully
- [x] Job preparation successful
- [x] Pipeline execution started
- [ ] Baseline generation complete
- [ ] Cache files created
- [ ] Second run with cache
- [ ] Speedup measured
- [ ] Results documented

### Functional Testing
- [x] Cache detection logic works
- [ ] Baseline restoration works
- [ ] Baseline storage works
- [ ] Cache reuse works
- [ ] Graceful fallback on cache failure

### Performance Testing
- [ ] First run timing measured
- [ ] Second run timing measured
- [ ] Speedup percentage calculated
- [ ] 70-80% speedup achieved

---

## Current Status

**Pipeline Running:**
- Job: job-20251208-rpatel-0004
- Stage: source_separation (in progress)
- Log: `out/2025/12/08/rpatel/4/99_pipeline_20251208_082631.log`

**Next Steps:**
1. Wait for pipeline completion (~3-5 minutes)
2. Verify baseline cache created
3. Run second test to measure speedup
4. Document final results

---

## Test Logs

**Main Test Log:** `logs/testing/manual/20251208_082629_quick_validation.log`  
**Pipeline Log:** `out/2025/12/08/rpatel/4/99_pipeline_20251208_082631.log`

---

**Last Updated:** 2025-12-08 08:27:00 (test running)
