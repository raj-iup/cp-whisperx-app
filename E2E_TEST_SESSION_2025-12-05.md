# End-to-End Test Execution Session
**Date:** 2025-12-05  
**Session Start:** 16:51 UTC  
**Status:** 🔄 In Progress  
**Objective:** Complete E2E Testing + Performance Profiling + Test Coverage

---

## Session Plan

### Phase 1: E2E Testing (90 minutes)
1. **Test 1: Transcribe Workflow** (Sample 1 - English) - 10 minutes
2. **Test 2: Translate Workflow** (Sample 2 - Hindi→English) - 15 minutes  
3. **Test 3: Subtitle Workflow** (Sample 2 - 8 languages) - 25 minutes

### Phase 2: Performance Profiling (60 minutes)
1. **Stage-level timing analysis** - 20 minutes
2. **Resource usage profiling** - 20 minutes
3. **Bottleneck identification** - 20 minutes

### Phase 3: Test Coverage Expansion (90 minutes)
1. **Current coverage analysis** - 15 minutes
2. **New test cases** - 45 minutes
3. **Integration test expansion** - 30 minutes

**Total Estimated:** 4 hours

---

## Test Environment

**System:**
- Platform: macOS (Apple Silicon)
- Backend: WhisperX (stable, per AD-005)
- Device: MPS (Apple Silicon GPU)
- Python: 3.11+

**Test Media:**
- ✅ Sample 1: `in/Energy Demand in AI.mp4` (14 MB, English technical)
- ✅ Sample 2: `in/test_clips/jaane_tu_test_clip.mp4` (29 MB, Hinglish)

**Configuration:**
```bash
WHISPER_BACKEND=whisperx          # Stable backend (AD-005)
WHISPERX_MODEL=large-v3           # Best accuracy
WHISPER_DEVICE=mps                # Apple Silicon GPU
COMPUTE_TYPE=float32              # MPS-compatible
```

---

## Phase 1: E2E Testing

### Test 1: Transcribe Workflow ⏳

**Objective:** Validate basic ASR pipeline (stages 01-07)

**Command:**
```bash
./prepare-job.sh \
  --media "in/Energy Demand in AI.mp4" \
  --workflow transcribe \
  --source-language en
```

**Expected Stages:**
1. 01_demux - Extract audio (~2s)
2. 03_glossary_loader - Load terms (~1s)
3. 04_source_separation - Adaptive (skip if clean)
4. 05_pyannote_vad - VAD (~10s)
5. 06_whisperx_asr - Transcription (~2-3min)
6. 07_alignment - Word-level (~1min)

**Success Criteria:**
- [ ] All stages complete (exit code 0)
- [ ] English transcript generated
- [ ] ASR accuracy ≥95%
- [ ] Word-level timestamps present
- [ ] Processing time: 5-8 minutes

**Status:** ⏳ Not Started  
**Start Time:** _TBD_  
**Duration:** _TBD_  
**Result:** _TBD_

---

### Test 2: Translate Workflow ⏳

**Objective:** Validate ASR + Translation pipeline (stages 01-07, 10)

**Command:**
```bash
./prepare-job.sh \
  --media "in/test_clips/jaane_tu_test_clip.mp4" \
  --workflow translate \
  --source-language hi \
  --target-language en
```

**Expected Stages:**
1. 01_demux - Extract audio (~2s)
2. 03_glossary_loader - Load cultural terms (~1s)
3. 04_source_separation - Adaptive (likely active)
4. 05_pyannote_vad - VAD (~15s)
5. 06_whisperx_asr - Hindi transcription (~3-4min)
6. 07_alignment - Word-level (~1-2min)
7. 10_translation - Hindi→English via IndicTrans2 (~2-3min)

**Success Criteria:**
- [ ] All stages complete (exit code 0)
- [ ] Hindi transcript generated (Devanagari script)
- [ ] English translation generated
- [ ] Cultural terms preserved
- [ ] ASR accuracy ≥85% (Hindi)
- [ ] Translation BLEU ≥90%
- [ ] Processing time: 8-12 minutes

**Status:** ⏳ Not Started  
**Start Time:** _TBD_  
**Duration:** _TBD_  
**Result:** _TBD_

---

### Test 3: Subtitle Workflow ⏳

**Objective:** Validate full 12-stage pipeline with context-aware processing

**Command:**
```bash
./prepare-job.sh \
  --media "in/test_clips/jaane_tu_test_clip.mp4" \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es,ru,zh,ar
```

**Expected Stages:**
1. 01_demux - Extract audio (~2s)
2. 02_tmdb_enrichment - Fetch metadata (~5s)
3. 03_glossary_loader - Character names + terms (~1s)
4. 04_source_separation - Adaptive (~3-5min)
5. 05_pyannote_vad - VAD + diarization (~15s)
6. 06_whisperx_asr - Hindi transcription (~3-4min)
7. 07_alignment - Word-level (~1-2min)
8. 08_lyrics_detection - MANDATORY (~30s)
9. 09_hallucination_removal - MANDATORY (~30s)
10. 10_translation - 8 languages (~5-8min)
11. 11_subtitle_generation - 8 VTT files (~1min)
12. 12_mux - Soft-embed (~30s)

**Success Criteria:**
- [ ] All 12 stages complete (exit code 0)
- [ ] 8 subtitle tracks embedded (hi, en, gu, ta, es, ru, zh, ar)
- [ ] Lyrics segments marked italic
- [ ] Hallucinations removed
- [ ] ASR accuracy ≥85%
- [ ] Subtitle quality ≥88%
- [ ] Character names from TMDB used
- [ ] Processing time: 15-20 minutes

**Status:** ⏳ Not Started  
**Start Time:** _TBD_  
**Duration:** _TBD_  
**Result:** _TBD_

---

## Phase 2: Performance Profiling

### Stage Timing Analysis ⏳

**Objective:** Measure per-stage performance

**Method:**
```bash
# Extract timing from logs
grep "Stage.*completed in" logs/pipeline-*.log > timing_analysis.txt

# Analyze with script
python3 tools/analyze-stage-timing.py timing_analysis.txt
```

**Metrics to Collect:**
- Per-stage duration (min, max, avg)
- Total pipeline duration
- Stage overhead (StageIO, manifest)
- I/O vs compute time ratio

**Status:** ⏳ Not Started

---

### Resource Usage Profiling ⏳

**Objective:** Monitor system resources during pipeline execution

**Method:**
```bash
# Run with profiling
time ./run-pipeline.sh <job_dir>

# Monitor with activity monitor or:
top -pid <pipeline_pid> -stats pid,cpu,mem,time
```

**Metrics to Collect:**
- Peak memory usage per stage
- GPU utilization (MPS)
- CPU utilization
- Disk I/O patterns

**Status:** ⏳ Not Started

---

### Bottleneck Identification ⏳

**Objective:** Find optimization opportunities

**Analysis Areas:**
1. Slowest stages (>20% of total time)
2. High memory stages (>4GB peak)
3. Redundant I/O operations
4. Inefficient data transformations

**Status:** ⏳ Not Started

---

## Phase 3: Test Coverage Expansion

### Current Coverage Analysis ⏳

**Objective:** Measure existing test coverage

**Command:**
```bash
cd /Users/rpatel/Projects/Active/cp-whisperx-app
pytest tests/ --cov=scripts --cov=shared --cov-report=term-missing
```

**Current Target:** 45% → 80%

**Status:** ⏳ Not Started

---

### New Test Cases ⏳

**Objective:** Add missing test scenarios

**Test Categories:**
1. **Unit Tests** (scripts/shared modules)
   - Configuration loading
   - Stage utilities
   - Data transformations

2. **Integration Tests** (stage interactions)
   - Manifest propagation
   - Data format compatibility
   - Error handling

3. **Workflow Tests** (end-to-end scenarios)
   - Edge cases (empty audio, very long files)
   - Error recovery
   - Partial pipeline execution

**Status:** ⏳ Not Started

---

### Integration Test Expansion ⏳

**Objective:** Expand tests/integration/ directory

**Planned Tests:**
1. `test_stage_isolation.py` - Verify stage directory containment
2. `test_manifest_tracking.py` - Verify input/output tracking
3. `test_config_hierarchy.py` - Verify AD-006 compliance
4. `test_import_consistency.py` - Verify AD-007 compliance
5. `test_workflow_routing.py` - Verify workflow-aware stage execution
6. `test_error_scenarios.py` - Verify error handling

**Status:** ⏳ Not Started

---

## Success Metrics

### E2E Testing
- [ ] 3/3 workflows passing (100%)
- [ ] All quality baselines met
- [ ] Zero critical issues found

### Performance Profiling
- [ ] Per-stage timing documented
- [ ] Resource usage profiled
- [ ] Top 3 bottlenecks identified

### Test Coverage
- [ ] Coverage: 45% → 80% (+35%)
- [ ] +50 new test cases
- [ ] All critical paths covered

---

## Timeline

| Phase | Start | Duration | End | Status |
|-------|-------|----------|-----|--------|
| Phase 1: E2E Testing | 17:00 | 90 min | 18:30 | ⏳ |
| Phase 2: Profiling | 18:30 | 60 min | 19:30 | ⏳ |
| Phase 3: Coverage | 19:30 | 90 min | 21:00 | ⏳ |

**Total Session:** 4 hours (17:00 - 21:00 UTC)

---

## Results Summary

_Will be updated as tests complete_

---

**Last Updated:** 2025-12-05 16:51 UTC  
**Next Update:** After Test 1 completion  
**Status:** 🔄 IN PROGRESS
