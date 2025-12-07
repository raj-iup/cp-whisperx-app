# Task #10: Output Directory Cleanup - Implementation Plan

**Date:** 2025-12-06  
**Priority:** 🔴 HIGH (AD-001 Compliance)  
**Status:** ⏳ In Progress  
**Estimated Effort:** 45-60 minutes

---

## Executive Summary

**Problem:** Current pipeline creates legacy directories that violate AD-001 (stage isolation):
- ❌ `subtitles/` directory duplicates files from `11_subtitle_generation/`
- ❌ `logs/` directory should not exist (logs go to job root or stage dirs)
- ❌ `media/` directory duplicates files from `12_mux/`
- ❌ Translation logs saved to `logs/` instead of `10_translation/`

**Impact:** Confuses users, wastes disk space, violates architectural principles

**Goal:** Enforce strict AD-001 compliance - all outputs in stage directories only

---

## Current State (Violations)

### Directory Structure (WRONG ❌)

```
job-20251206-rpatel-0002/
├── .job-*.env                          # ✅ Correct
├── job.json                            # ✅ Correct
├── manifest.json                       # ✅ Correct
├── 01_demux/                           # ✅ Correct
├── 02_tmdb/                            # ✅ Correct
├── ...
├── 11_subtitle_generation/             # ✅ Correct
│   └── jaane tu test clip.hi.srt      # ✅ Correct (source)
├── 12_mux/                             # ✅ Correct
│   └── jaane tu test clip_subtitled.mp4  # ✅ Correct
├── logs/                               # ❌ WRONG - Should not exist
│   ├── 99_pipeline_20251206_055503.log    # ❌ Should be in job root
│   ├── 99_indictrans2_20251206_060017.log # ❌ Should be in 10_translation/
│   └── 99_nllb_20251206_061627.log        # ❌ Should be in 10_translation/
├── subtitles/                          # ❌ WRONG - Duplicates 11_subtitle_generation/
│   ├── jaane tu test clip.en.srt      # ❌ Duplicate (already in 11_subtitle_generation/)
│   ├── jaane tu test clip.gu.srt      # ❌ Duplicate
│   ├── jaane tu test clip.ta.srt      # ❌ Duplicate
│   ├── jaane tu test clip.es.srt      # ❌ Duplicate
│   ├── jaane tu test clip.ru.srt      # ❌ Duplicate
│   └── jaane tu test clip.hi.srt      # ❌ Duplicate
└── media/                              # ❌ WRONG - Duplicates 12_mux/
    └── jaane_tu_test_clip/
        └── jaane tu test clip_subtitled.mp4  # ❌ Duplicate
```

---

## Target State (AD-001 Compliant)

### Directory Structure (CORRECT ✅)

```
job-20251206-rpatel-0002/
├── .job-*.env                          # ✅ Job configuration
├── job.json                            # ✅ Job metadata
├── manifest.json                       # ✅ Job manifest
├── 99_pipeline_20251206_055503.log    # ✅ Main pipeline log (job root)
├── 01_demux/                           # ✅ Stage 01
│   ├── audio.wav
│   ├── manifest.json
│   └── stage.log
├── 02_tmdb/                            # ✅ Stage 02
│   ├── tmdb_metadata.json
│   ├── manifest.json
│   └── stage.log
├── ...
├── 10_translation/                     # ✅ Stage 10
│   ├── segments_translated_en.json
│   ├── segments_translated_gu.json
│   ├── segments_translated_ta.json
│   ├── segments_translated_es.json
│   ├── segments_translated_ru.json
│   ├── 99_indictrans2_20251206_060017.log  # ✅ Translation log in stage
│   ├── 99_nllb_20251206_061627.log         # ✅ Translation log in stage
│   ├── manifest.json
│   └── stage.log
├── 11_subtitle_generation/             # ✅ Stage 11
│   ├── jaane tu test clip.hi.srt      # ✅ Source subtitle
│   ├── jaane tu test clip.en.srt      # ✅ English subtitle
│   ├── jaane tu test clip.gu.srt      # ✅ Gujarati subtitle
│   ├── jaane tu test clip.ta.srt      # ✅ Tamil subtitle
│   ├── jaane tu test clip.es.srt      # ✅ Spanish subtitle
│   ├── jaane tu test clip.ru.srt      # ✅ Russian subtitle
│   ├── manifest.json
│   └── stage.log
└── 12_mux/                             # ✅ Stage 12
    ├── jaane tu test clip_subtitled.mp4   # ✅ Final video (ONLY location)
    ├── manifest.json
    └── stage.log
```

**Key Principles:**
- ✅ Each stage writes to its own directory ONLY
- ✅ No shared directories (subtitles/, media/, logs/)
- ✅ Pipeline log goes to job root
- ✅ Stage-specific logs go to stage directories
- ✅ No file duplication

---

## Implementation Plan

### Phase 1: Pipeline Log Location (15 minutes)

**File:** `scripts/run-pipeline.py`

**Change 1:** Move pipeline log to job root (Line 137-142)

**Before:**
```python
# Line 137
log_dir = job_dir / "logs"
log_dir.mkdir(exist_ok=True)

# Create main pipeline log file (99_pipeline_*.log for clarity)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"99_pipeline_{timestamp}.log"
```

**After:**
```python
# Line 137
# Pipeline log goes to job root (AD-001: No separate logs/ directory)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = job_dir / f"99_pipeline_{timestamp}.log"
```

**Impact:**
- ✅ Removes `logs/` directory creation
- ✅ Pipeline log now at job root: `job_dir/99_pipeline_*.log`
- ✅ AD-001 compliant

---

### Phase 2: Translation Logs Location (15 minutes)

**File:** `scripts/run-pipeline.py`

**Change 2:** Move IndicTrans2 logs to 10_translation/ (Lines ~2109, ~2385)

**Before (Line ~2109):**
```python
log_file = Path('{self.job_dir / "logs"}') / 'indictrans2_translation.log'
```

**After:**
```python
translation_dir = self.job_dir / "10_translation"
log_file = translation_dir / 'indictrans2_translation.log'
```

**Before (Line ~2385):**
```python
log_file = Path('{self.job_dir / "logs"}') / 'indictrans2_translation_{target_lang}.log'
```

**After:**
```python
translation_dir = self.job_dir / "10_translation"
log_file = translation_dir / f'indictrans2_translation_{target_lang}.log'
```

**Change 3:** Move NLLB logs to 10_translation/ (Lines ~2476, ~2564)

**Before (Line ~2476):**
```python
log_file = Path('{self.job_dir / "logs"}') / 'nllb_translation.log'
```

**After:**
```python
translation_dir = self.job_dir / "10_translation"
log_file = translation_dir / 'nllb_translation.log'
```

**Before (Line ~2564):**
```python
log_file = Path('{self.job_dir / "logs"}') / 'nllb_{target_lang}_translation.log'
```

**After:**
```python
translation_dir = self.job_dir / "10_translation"
log_file = translation_dir / f'nllb_{target_lang}_translation.log'
```

**Impact:**
- ✅ All translation logs in `10_translation/` directory
- ✅ No more `logs/` directory needed
- ✅ Stage isolation maintained

---

### Phase 3: Remove subtitles/ Directory (10 minutes)

**File:** `scripts/run-pipeline.py`

**Change 4:** Remove subtitles/ copy in translated subtitle generation (Lines 2225-2240)

**Before:**
```python
# Generate SRT file
if generate_srt_from_segments(segments, output_srt):
    # Copy to subtitles/ for compatibility
    subtitles_dir = self.job_dir / "subtitles"
    subtitles_dir.mkdir(parents=True, exist_ok=True)
    final_output = subtitles_dir / output_srt.name
    
    # Only copy if source and destination are different
    if output_srt != final_output:
        import shutil
        shutil.copy2(output_srt, final_output)
        self.logger.info(f"✓ Subtitles generated: {output_srt.relative_to(self.job_dir)}")
        self.logger.info(f"✓ Copied to: subtitles/{output_srt.name}")
    else:
        self.logger.info(f"✓ Subtitles generated: {output_srt.relative_to(self.job_dir)}")
    
    return True
```

**After:**
```python
# Generate SRT file
if generate_srt_from_segments(segments, output_srt):
    # AD-001: Keep subtitle in stage directory only (no copy to subtitles/)
    self.logger.info(f"✓ Subtitles generated: {output_srt.relative_to(self.job_dir)}")
    return True
```

**Change 5:** Remove subtitles/ copy in source subtitle generation (Lines 2280-2295)

**Before:**
```python
# Generate SRT file
if generate_srt_from_segments(segments, output_srt):
    # Copy to subtitles/ for compatibility
    subtitles_dir = self.job_dir / "subtitles"
    subtitles_dir.mkdir(parents=True, exist_ok=True)
    final_output = subtitles_dir / output_srt.name
    
    # Only copy if source and destination are different
    if output_srt != final_output:
        import shutil
        shutil.copy2(output_srt, final_output)
        self.logger.info(f"✓ Source subtitles generated: {output_srt.relative_to(self.job_dir)}")
        self.logger.info(f"✓ Copied to: subtitles/{output_srt.name}")
    else:
        self.logger.info(f"✓ Source subtitles generated: {output_srt.relative_to(self.job_dir)}")
    
    return True
```

**After:**
```python
# Generate SRT file
if generate_srt_from_segments(segments, output_srt):
    # AD-001: Keep subtitle in stage directory only (no copy to subtitles/)
    self.logger.info(f"✓ Source subtitles generated: {output_srt.relative_to(self.job_dir)}")
    return True
```

**Impact:**
- ✅ No more `subtitles/` directory
- ✅ All SRT files remain in `11_subtitle_generation/`
- ✅ No file duplication

---

### Phase 4: Remove media/ Directory (10 minutes)

**File:** `scripts/run-pipeline.py`

**Change 6:** Remove media/ copy in mux stage (Lines ~2807-2815)

**Before:**
```python
# Copy to media/ directory for user convenience
media_output_subdir = self.job_dir / "media" / media_name
media_output_subdir.mkdir(parents=True, exist_ok=True)
final_copy = media_output_subdir / output_video.name
import shutil
shutil.copy2(output_video, final_copy)
self.logger.info(f"✓ Copy saved to: media/{media_name}/{output_video.name}")
```

**After:**
```python
# AD-001: Final video stays in 12_mux/ only (no copy to media/)
# Users can find output in 12_mux/ stage directory
```

**Impact:**
- ✅ No more `media/` directory
- ✅ Final video only in `12_mux/`
- ✅ No file duplication

---

### Phase 5: Update Mux Stage Input Paths (5 minutes)

**File:** `scripts/run-pipeline.py`

**Change 7:** Update mux stage to read subtitles from 11_subtitle_generation/

**Current code reads from:**
```python
subtitles_dir / f"{media_name}.{lang}.srt"  # Old: subtitles/ directory
```

**Should read from:**
```python
stage_11_dir = self.job_dir / "11_subtitle_generation"
subtitle_file = stage_11_dir / f"{media_name}.{lang}.srt"
```

**Impact:**
- ✅ Mux stage reads from correct stage directory
- ✅ No dependency on legacy `subtitles/` directory

---

## Code Changes Summary

### Files to Modify

| File | Changes | Lines | Effort |
|------|---------|-------|--------|
| `scripts/run-pipeline.py` | 7 changes | ~30 lines | 45-60 min |

### Change Breakdown

| Change | Type | Impact |
|--------|------|--------|
| 1. Pipeline log to job root | Delete 2 lines, modify 1 | Remove logs/ directory |
| 2. IndicTrans2 logs to 10_translation/ | Modify 2 locations | Move translation logs |
| 3. NLLB logs to 10_translation/ | Modify 2 locations | Move translation logs |
| 4. Remove subtitles/ copy (translated) | Delete 11 lines | No subtitles/ duplication |
| 5. Remove subtitles/ copy (source) | Delete 11 lines | No subtitles/ duplication |
| 6. Remove media/ copy | Delete 6 lines | No media/ duplication |
| 7. Update mux input paths | Modify 1 location | Read from 11_subtitle_generation/ |

**Total Lines Changed:** ~30 lines (mostly deletions)

---

## Testing Plan

### Test 1: Transcribe Workflow
```bash
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow transcribe --source-language hi

./run-pipeline.sh -j <job-id>
```

**Validation:**
- ✅ No `logs/` directory
- ✅ No `subtitles/` directory
- ✅ No `media/` directory
- ✅ Pipeline log at job root: `99_pipeline_*.log`
- ✅ Transcript in `07_alignment/transcript.txt`

### Test 2: Translate Workflow
```bash
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate --source-language hi --target-language en

./run-pipeline.sh -j <job-id>
```

**Validation:**
- ✅ No `logs/` directory
- ✅ No `subtitles/` directory
- ✅ No `media/` directory
- ✅ Translation logs in `10_translation/`
- ✅ Transcript in `07_alignment/transcript_en.txt`

### Test 3: Subtitle Workflow
```bash
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle --source-language hi --target-language en,gu

./run-pipeline.sh -j <job-id>
```

**Validation:**
- ✅ No `logs/` directory
- ✅ No `subtitles/` directory
- ✅ No `media/` directory
- ✅ Pipeline log at job root
- ✅ Translation logs in `10_translation/`
- ✅ All SRT files in `11_subtitle_generation/`
- ✅ Final video in `12_mux/` ONLY

---

## Success Criteria

### Directory Structure Compliance

**Job Root:**
```
job-YYYYMMDD-user-NNNN/
├── 99_pipeline_YYYYMMDD_HHMMSS.log  # ✅ Pipeline log here
├── job.json                          # ✅ Metadata
├── manifest.json                     # ✅ Job manifest
├── .job-*.env                        # ✅ Config
└── [stage directories 01-12]         # ✅ All stages
```

**Stage 10 (Translation):**
```
10_translation/
├── segments_translated_*.json           # ✅ Translations
├── indictrans2_translation*.log         # ✅ IndicTrans2 logs here
├── nllb_*_translation.log               # ✅ NLLB logs here
├── manifest.json
└── stage.log
```

**Stage 11 (Subtitle Generation):**
```
11_subtitle_generation/
├── *.hi.srt                             # ✅ Source subtitle
├── *.en.srt                             # ✅ English subtitle
├── *.gu.srt                             # ✅ Gujarati subtitle
├── [other language subtitles]
├── manifest.json
└── stage.log
```

**Stage 12 (Mux):**
```
12_mux/
├── *_subtitled.mp4                      # ✅ Final video (ONLY location)
├── manifest.json
└── stage.log
```

**Must NOT Exist:**
- ❌ `logs/` directory
- ❌ `subtitles/` directory
- ❌ `media/` directory

---

## Risks & Mitigation

### Risk 1: Breaking Existing Scripts
**Risk:** External scripts may expect `subtitles/` or `media/` directories  
**Mitigation:** 
- Update documentation to specify new locations
- Add deprecation notice in CHANGELOG
- This is v3.0 breaking change (acceptable)

### Risk 2: Mux Stage Failure
**Risk:** Mux stage can't find subtitle files  
**Mitigation:**
- Test thoroughly with all 3 workflows
- Update input path resolution logic
- Validate before committing

### Risk 3: Log File Not Found
**Risk:** Tools looking for logs in `logs/` directory  
**Mitigation:**
- Update any log monitoring scripts
- Pipeline log now at predictable location (job root)
- Stage logs always in stage directories

---

## Documentation Updates

### Files to Update

1. **DEVELOPER_STANDARDS.md § 1.1**
   - Update output directory structure
   - Remove references to legacy directories

2. **CANONICAL_PIPELINE.md**
   - Update output locations for all stages
   - Remove subtitles/, media/, logs/ references

3. **IMPLEMENTATION_TRACKER.md**
   - Add Task #10 completion
   - Update progress to 100%

4. **copilot-instructions.md § 1.1**
   - Update stage directory containment rules
   - Remove legacy directory references

---

## Rollout Plan

### Step 1: Create Plan Document (5 minutes) ✅
- This document

### Step 2: Implement Changes (45-60 minutes)
- Make all 7 code changes
- Test syntax (no execution yet)

### Step 3: Validation Testing (30 minutes)
- Run Test 1 (transcribe)
- Run Test 2 (translate)
- Run Test 3 (subtitle - small sample)

### Step 4: Documentation Updates (15 minutes)
- Update 4 documentation files
- Update IMPLEMENTATION_TRACKER.md

### Step 5: Commit & Report (5 minutes)
- Git commit with detailed message
- Create completion report

**Total Time:** ~2 hours

---

## Next Steps

1. **Review this plan** ✅ (You are here)
2. **Approve implementation** ⏳
3. **Execute Phase 1-5** ⏳
4. **Run validation tests** ⏳
5. **Update documentation** ⏳
6. **Mark Task #10 complete** ⏳

---

**Plan Created:** 2025-12-06  
**Status:** ⏳ Awaiting approval  
**Priority:** 🔴 HIGH (AD-001 compliance)  
**Estimated Completion:** 2025-12-06 (same day)
