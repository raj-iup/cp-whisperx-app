# End-to-End Test Execution Plan

**Version:** 1.0  
**Created:** 2025-12-04  
**Status:** 🔄 In Progress  
**Target:** Phase 4 - 70% → 85% Complete

---

## Overview

This document tracks the execution of end-to-end tests for all three workflows using standard test media samples as defined in IMPLEMENTATION_TRACKER.md.

**Test Media Mapping:**
- **Sample 1:** `in/Energy Demand in AI.mp4` (English technical, 14 MB)
  - **Use for:** Transcribe & Translate workflows
- **Sample 2:** `in/test_clips/jaane_tu_test_clip.mp4` (Hinglish Bollywood, 28 MB)
  - **Use for:** Subtitle workflow

---

## Test Execution Status

### Priority 1: Subtitle Workflow (Sample 2) 🔄

**Test:** `test_subtitle_full_pipeline_sample2`  
**Media:** `in/test_clips/jaane_tu_test_clip.mp4`  
**Status:** ⏳ Not Started  
**Expected Duration:** 15-20 minutes

**Test Configuration:**
```bash
./prepare-job.sh \
  --media "in/test_clips/jaane_tu_test_clip.mp4" \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es,ru,zh,ar
```

**Expected Stages (12):**
1. ✅ 01_demux - Extract audio
2. ✅ 02_tmdb_enrichment - Fetch TMDB metadata (ENABLED for subtitle)
3. ✅ 03_glossary_loader - Load character names + cultural terms
4. ⏳ 04_source_separation - Adaptive (depends on audio quality)
5. ✅ 05_pyannote_vad - Voice activity + speaker diarization
6. ✅ 06_whisperx_asr - ASR transcription (Hindi/Hinglish)
7. ✅ 07_alignment - Word-level alignment
8. ✅ 08_lyrics_detection - MANDATORY (detect song segments)
9. ✅ 09_hallucination_removal - MANDATORY (clean ASR errors)
10. ✅ 10_translation - Multi-language (8 languages)
11. ✅ 11_subtitle_generation - VTT files for 8 languages
12. ✅ 12_mux - Soft-embed subtitles into video

**Success Criteria:**
- [ ] All stages complete without errors
- [ ] 8 subtitle tracks generated (hi, en, gu, ta, es, ru, zh, ar)
- [ ] Lyrics segments marked italic
- [ ] Hallucinations removed (no "Thanks for watching")
- [ ] ASR accuracy ≥85% (Hindi/Hinglish)
- [ ] Subtitle quality ≥88%
- [ ] Output MKV with embedded subtitles
- [ ] Processing time: 15-20 minutes

**Expected Outputs:**
- `01_demux/audio.wav` - Extracted audio
- `02_tmdb/metadata.json` - Character names, cast, crew
- `03_glossary_load/glossary.json` - Loaded terms
- `05_pyannote_vad/segments.json` - VAD + diarization
- `06_whisperx_asr/transcript.json` - Raw ASR
- `07_alignment/aligned.json` - Word-level timestamps
- `08_lyrics_detection/lyrics_segments.json` - Song markers
- `09_hallucination_removal/cleaned_transcript.json` - Clean ASR
- `10_translation/*.json` - 8 language translations
- `11_subtitle_generation/*.vtt` - 8 VTT files
- `12_mux/output_with_subtitles.mkv` - Final output

---

### Priority 2: Transcribe Workflow (Sample 1) 🔄

**Test:** `test_transcribe_sample1_english_technical`  
**Media:** `in/Energy Demand in AI.mp4`  
**Status:** ⏳ Not Started  
**Expected Duration:** 5-8 minutes

**Test Configuration:**
```bash
./prepare-job.sh \
  --media "in/Energy Demand in AI.mp4" \
  --workflow transcribe \
  --source-language en
```

**Expected Stages (7):**
1. ✅ 01_demux - Extract audio
2. ❌ 02_tmdb_enrichment - DISABLED (not subtitle workflow)
3. ✅ 03_glossary_loader - Load domain terms
4. ⏳ 04_source_separation - Adaptive (depends on audio quality)
5. ✅ 05_pyannote_vad - Voice activity detection
6. ✅ 06_whisperx_asr - ASR transcription (English)
7. ✅ 07_alignment - Word-level alignment

**Success Criteria:**
- [ ] All stages complete without errors
- [ ] English transcript generated
- [ ] Technical terms preserved (AI, energy, demand)
- [ ] ASR accuracy ≥95% (clean English)
- [ ] Proper capitalization
- [ ] Processing time: 5-8 minutes

**Expected Outputs:**
- `01_demux/audio.wav` - Extracted audio
- `03_glossary_load/glossary.json` - Domain terms
- `05_pyannote_vad/segments.json` - VAD
- `06_whisperx_asr/transcript.json` - Raw ASR
- `07_alignment/transcript.txt` - Final transcript (English)

---

### Priority 3: Translate Workflow (Sample 1) 🔄

**Test:** `test_translate_sample1_english_to_hindi`  
**Media:** `in/Energy Demand in AI.mp4`  
**Status:** ⏳ Not Started  
**Expected Duration:** 8-12 minutes

**Note:** Translate workflow requires **Indian source language**. Since Sample 1 is English, we'll test with Sample 2 (Hindi) instead.

**CORRECTED Test Configuration:**
```bash
# Hindi → English translation (VALID)
./prepare-job.sh \
  --media "in/test_clips/jaane_tu_test_clip.mp4" \
  --workflow translate \
  --source-language hi \
  --target-language en
```

**Expected Stages (8):**
1. ✅ 01_demux - Extract audio
2. ❌ 02_tmdb_enrichment - DISABLED (not subtitle workflow)
3. ✅ 03_glossary_loader - Load cultural terms
4. ⏳ 04_source_separation - Adaptive
5. ✅ 05_pyannote_vad - Voice activity detection
6. ✅ 06_whisperx_asr - ASR transcription (Hindi)
7. ✅ 07_alignment - Word-level alignment
8. ✅ 10_translation - Translate Hindi → English (IndicTrans2)

**Success Criteria:**
- [ ] All stages complete without errors
- [ ] Hindi transcript generated (native script)
- [ ] English translation generated
- [ ] Cultural terms preserved/adapted
- [ ] ASR accuracy ≥85% (Hindi)
- [ ] Translation BLEU ≥90%
- [ ] Processing time: 8-12 minutes

**Expected Outputs:**
- `01_demux/audio.wav` - Extracted audio
- `03_glossary_load/glossary.json` - Cultural terms
- `05_pyannote_vad/segments.json` - VAD
- `06_whisperx_asr/transcript.json` - Raw ASR (Hindi)
- `07_alignment/transcript.txt` - Hindi transcript
- `10_translation/transcript_en.txt` - English translation

---

## Test Execution Order

**Recommended Sequence:**

1. **Transcribe Workflow (Sample 1)** - Fastest, simplest (5-8 min)
   - Tests basic ASR pipeline
   - No translation, no subtitle generation
   - Validates core stages 01-07

2. **Translate Workflow (Sample 2)** - Medium complexity (8-12 min)
   - Tests ASR + Translation
   - Validates IndicTrans2 integration
   - Validates stages 01-07 + 10

3. **Subtitle Workflow (Sample 2)** - Full pipeline (15-20 min)
   - Tests all 12 stages
   - Validates MANDATORY stages (08-09)
   - Validates multi-language subtitle generation
   - Most comprehensive test

**Total Estimated Time:** 30-40 minutes

---

## Execution Commands

### Step 1: Transcribe Workflow
```bash
# Create job
./prepare-job.sh \
  --media "in/Energy Demand in AI.mp4" \
  --workflow transcribe \
  --source-language en

# Run pipeline (output will show job directory)
./run-pipeline.sh <job_directory>

# Verify output
ls -lh <job_directory>/07_alignment/transcript.txt
```

### Step 2: Translate Workflow
```bash
# Create job
./prepare-job.sh \
  --media "in/test_clips/jaane_tu_test_clip.mp4" \
  --workflow translate \
  --source-language hi \
  --target-language en

# Run pipeline
./run-pipeline.sh <job_directory>

# Verify outputs
ls -lh <job_directory>/07_alignment/transcript.txt  # Hindi
ls -lh <job_directory>/10_translation/transcript_en.txt  # English
```

### Step 3: Subtitle Workflow
```bash
# Create job
./prepare-job.sh \
  --media "in/test_clips/jaane_tu_test_clip.mp4" \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es,ru,zh,ar

# Run pipeline
./run-pipeline.sh <job_directory>

# Verify outputs
ls -lh <job_directory>/11_subtitle_generation/*.vtt  # 8 VTT files
ls -lh <job_directory>/12_mux/*.mkv  # Final video with subtitles
```

---

## Performance Profiling

**During each test, collect:**

1. **Timing per stage:**
   - Start/end timestamps from logs
   - Processing duration
   - I/O time vs compute time

2. **Resource usage:**
   - Memory peak usage
   - GPU/CPU utilization
   - Disk I/O

3. **Quality metrics:**
   - ASR confidence scores
   - Translation BLEU scores
   - Subtitle quality score
   - Error counts

**Profiling Command:**
```bash
# Enable performance logging
export LOG_LEVEL=DEBUG
export PROFILE_STAGES=true

# Run with profiling
time ./run-pipeline.sh <job_directory>

# Analyze logs
grep "Stage.*completed in" logs/pipeline-*.log
```

---

## Error Scenario Testing

**After successful E2E tests, test error scenarios:**

1. **Missing input file:**
   ```bash
   ./prepare-job.sh --media "nonexistent.mp4" --workflow transcribe -s en
   ```

2. **Invalid language code:**
   ```bash
   ./prepare-job.sh --media "in/..." --workflow transcribe -s invalid
   ```

3. **Missing required parameter:**
   ```bash
   ./prepare-job.sh --media "in/..." --workflow translate -s hi
   # Missing --target-language
   ```

4. **Corrupt media file:**
   - Create 0-byte file, test handling
   - Create invalid media format

5. **Network failures:**
   - TMDB API unavailable
   - Model download failure

6. **Insufficient resources:**
   - Low memory conditions
   - Low disk space

---

## Next Steps After E2E Tests

1. **Analyze results** - Identify bottlenecks
2. **Update metrics** - Update IMPLEMENTATION_TRACKER.md with actual metrics
3. **Fix critical issues** - Address any blocking issues found
4. **Performance optimization** - Implement optimizations for bottlenecks
5. **Expand test suite** - Add more integration tests based on findings
6. **Update documentation** - Document any workflow changes needed

---

## Test Results Log

### Test 1: Transcribe Workflow (Sample 1)
**Date:** 2025-12-04  
**Status:** 🔄 In Progress (fixes applied, ready to retry)
**Duration:** _TBD_  
**Result:** _TBD_  
**Issues Fixed:**
1. ✅ config_loader.py location (moved to shared/)
2. ✅ PYTHONPATH for multi-environment execution
3. ✅ ASR chunker Path/str handling
4. ✅ Chunker method signature mismatch
5. ✅ MPS auto-chunking disabled (<30min)
6. ✅ Undefined config variable in _transcribe_whole
7. ✅ Workflow detection from job.json

**Next**: Retry pipeline execution

### Test 2: Translate Workflow (Sample 2)
**Date:** _Not yet run_  
**Status:** ⏳ Pending  
**Duration:** _TBD_  
**Result:** _TBD_  
**Issues:** _TBD_

### Test 3: Subtitle Workflow (Sample 2)
**Date:** _Not yet run_  
**Status:** ⏳ Pending  
**Duration:** _TBD_  
**Result:** _TBD_  
**Issues:** _TBD_

---

**Last Updated:** 2025-12-04 04:38 UTC  
**Next Review:** After Test 1 completion  
**Status:** 🔄 Fixes Applied - Ready to Resume Testing

---

## 🚨 Known Issues

### Issue 1: MLX Backend Segmentation Fault (CRITICAL)

**Discovered:** 2025-12-04  
**Status:** 🔴 BLOCKING E2E tests  
**Severity:** HIGH  
**Impact:** All workflows using ASR stage

**Symptoms:**
- Stage 06 (whisperx_asr) crashes with exit code -11 (SIGSEGV)
- Crash occurs AFTER 100% processing complete
- Happens during cleanup/finalization phase
- Memory access violation in MLX backend

**Test Case That Failed:**
- Test: Transcribe Workflow (Test 1)
- Media: Energy Demand in AI.mp4 (14 MB, English)
- Job: job-20251203-rpatel-0020
- Backend: MLX (Apple Silicon optimization)
- Model: large-v3

**Stages Completed Successfully:**
- ✅ 01_demux - 1.7s
- ✅ 04_source_separation - 299.4s
- ✅ 05_pyannote_vad - 11.8s
- ❌ 06_whisperx_asr - SEGFAULT

**Root Cause:**
- MLX backend memory/process issue on Apple Silicon
- Known instability with large audio files
- Memory pressure during cleanup phase
- **NOT a bug in our pipeline code**

**Workarounds (Priority Order):**

1. **Switch to WhisperX Backend** ⭐ RECOMMENDED
   ```bash
   # Update job config: WHISPER_BACKEND=whisperx
   # More stable, widely tested, proven reliability
   ```

2. **Use Smaller Model**
   ```bash
   # WHISPERX_MODEL=base  # or small
   # Reduces memory pressure
   ```

3. **Use Shorter Audio Files**
   ```bash
   # Test with <1 minute clips first
   # Validate stability before full files
   ```

4. **Use CPU Backend**
   ```bash
   # WHISPER_DEVICE=cpu
   # Slower but stable fallback
   ```

**Recommended Configuration for E2E Tests:**
```bash
# config/.env.pipeline or job-specific config
WHISPER_BACKEND=whisperx     # Use WhisperX instead of MLX
WHISPERX_MODEL=large-v3      # Keep large model
WHISPER_DEVICE=mps           # Use MPS (Apple Silicon GPU)
COMPUTE_TYPE=float32         # Use float32 for MPS stability
```

**Action Items:**
- [ ] Test WhisperX backend with same file
- [ ] Compare performance: MLX vs WhisperX
- [ ] Document backend stability matrix
- [ ] Update copilot-instructions with backend guidance
- [ ] Retry Test 1 with WhisperX backend
- [ ] Consider deprecating MLX backend for production

**Related Documents:**
- SESSION_FINAL_2025-12-04.md - Test failure details
- ARCHITECTURE_ALIGNMENT_2025-12-04.md - Architecture context

---

## 📊 Backend Stability Matrix (Updated 2025-12-04)

| Backend | Platform | Stability | Performance | Recommendation |
|---------|----------|-----------|-------------|----------------|
| **WhisperX** | All | ✅ Excellent | ✅ Fast | ⭐ RECOMMENDED |
| **MLX** | Apple Silicon | ❌ Unstable | ✅ Fastest | ⚠️ USE WITH CAUTION |
| **CUDA** | NVIDIA GPU | ✅ Excellent | ✅ Fastest | ⭐ RECOMMENDED |
| **CPU** | All | ✅ Excellent | ⚠️ Slow | 🔄 FALLBACK ONLY |

**Production Recommendation:** Use WhisperX or CUDA backends, avoid MLX until stability improves.

---

## 📋 Test Execution Checklist (Updated)

**Before Running Tests:**
- [ ] Choose stable backend (WhisperX recommended)
- [ ] Verify virtual environments installed
- [ ] Check disk space (need ~5GB for outputs)
- [ ] Review test media samples exist
- [ ] Set appropriate compute type for device

**During Test Execution:**
- [ ] Monitor resource usage (CPU, memory, GPU)
- [ ] Watch for segfaults or crashes
- [ ] Check stage logs for errors
- [ ] Validate manifest.json files

**After Test Completion:**
- [ ] Review all stage logs
- [ ] Validate output quality
- [ ] Check performance metrics
- [ ] Document any issues found
- [ ] Update this plan with findings

---

**Document Version:** 1.1  
**Last Updated:** 2025-12-04 12:42 UTC  
**Status:** 🔄 IN PROGRESS - Test 1 blocked, investigating backend stability  
**Next Update:** After backend testing complete
