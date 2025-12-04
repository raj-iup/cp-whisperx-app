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
**Date:** _Not yet run_  
**Status:** ⏳ Pending  
**Duration:** _TBD_  
**Result:** _TBD_  
**Issues:** _TBD_

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

**Last Updated:** 2025-12-04 03:45 UTC  
**Next Review:** After Test 1 completion  
**Status:** 🔄 Ready to Execute
