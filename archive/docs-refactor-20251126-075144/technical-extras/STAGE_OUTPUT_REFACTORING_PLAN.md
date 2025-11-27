# Pipeline Stage Output Refactoring Plan

**Date:** 2024-11-25  
**Status:** PLANNING - Major Refactoring Required  
**Impact:** High - Multiple core scripts affected

---

## Issues Identified from Logs

### 1. Directory Naming Inconsistency
**Current:** `99_source_separation/`  
**Expected:** `02_source_separation/`

**Files Affected:**
- `scripts/source_separation.py`
- `scripts/run-pipeline.py` (fallback logic)

---

### 2. Stage Outputs Not in Numbered Directories

**Current Structure:**
```
out/2025/11/24/1/1/
├── media/
│   └── audio.wav                    ← demux output (WRONG LOCATION)
├── transcripts/
│   ├── segments.json                ← asr output (WRONG LOCATION)
│   └── transcript.txt               ← export output (WRONG LOCATION)
├── subtitles/
│   └── *.srt                        ← subtitle gen output (WRONG LOCATION)
└── 99_source_separation/
    └── audio.wav                    ← WRONG NUMBER (should be 02_)
```

**Expected Structure:**
```
out/2025/11/24/1/1/
├── media/
│   └── Jaane Tu Ya Jaane Na 2008.mp4    ← Original input only
├── 01_demux/
│   └── audio.wav                         ← demux output
├── 02_source_separation/
│   ├── vocals.wav
│   ├── accompaniment.wav
│   └── audio.wav                         ← processed audio
├── 03_pyannote_vad/
│   └── speech_segments.json
├── 04_asr/
│   └── segments.json                     ← asr output
├── 05_alignment/
│   └── segments_aligned.json
├── 06_lyrics_detection/
│   └── lyrics_markers.json
├── 07_translation/
│   └── segments_en.json
├── 08_subtitle_generation/
│   ├── movie.hi.srt
│   └── movie.en.srt
├── 09_mux/
│   └── movie_subtitled.mp4
├── transcripts/                          ← Keep for final exports
│   ├── segments.json                     ← Copy from 04_asr
│   └── transcript.txt                    ← Final text
└── subtitles/                            ← Keep for final exports
    ├── movie.hi.srt                      ← Copy from 08_subtitle_generation
    └── movie.en.srt                      ← Copy from 08_subtitle_generation
```

---

### 3. No Input Path Logging

**Current:** Stages start without logging which input they're using  
**Expected:** Log input path at stage start

**Example:**
```
[INFO] ▶️  Stage 02_source_separation: STARTING
[INFO] 📥 Input: 01_demux/audio.wav
[INFO] 📤 Output: 02_source_separation/audio.wav
[INFO] Running source separation (quality: quality)...
```

---

### 4. ASR Hallucinations

**Issue:** Transcript contains repeated "local" text (hallucination)
```
[04:59.380 --> 05:01.560] 把ग� local
[05:01.560 --> 05:01.560]  local
[05:01.560 --> 05:01.560]  local
... (repeated 20+ times)
```

**Solution:** Already implemented hallucination removal stage, needs verification

---

## Refactoring Strategy

### Phase 1: Update Stage Output Directories (CRITICAL)

**Files to Modify:**

1. **scripts/run-pipeline.py**
   - `_stage_demux()` - Output to `01_demux/audio.wav`
   - `_stage_source_separation()` - Output to `02_source_separation/`
   - `_stage_pyannote_vad()` - Output to `03_pyannote_vad/`
   - `_stage_asr()` - Output to `04_asr/segments.json`
   - `_stage_alignment()` - Output to `05_alignment/`
   - `_stage_export_transcript()` - Output to `transcripts/` (keep)
   - `_stage_load_transcript()` - Read from `04_asr/segments.json`
   - `_stage_hybrid_translation()` - Output to `07_translation/`
   - `_stage_subtitle_generation()` - Output to `08_subtitle_generation/`
   - `_stage_mux()` - Output to `09_mux/`

2. **scripts/source_separation.py**
   - Change output directory from `99_source_separation` to `02_source_separation`
   - Update all references

3. **scripts/pyannote_vad.py**
   - Change output directory from `vad` to `03_pyannote_vad`

4. **scripts/demux.py** (if exists)
   - Change output directory to `01_demux`

---

### Phase 2: Add Input/Output Logging

**Pattern for All Stages:**
```python
def _stage_xxx(self) -> bool:
    """Stage N: Description"""
    stage_name = "NNstage_name"
    
    # Determine input
    input_file = self._get_previous_stage_output()
    
    # Log stage start with I/O
    self.logger.info(f"▶️  Stage {stage_name}: STARTING")
    self.logger.info(f"📥 Input: {input_file.relative_to(self.job_dir)}")
    self.logger.info(f"📤 Output: {stage_name}/output.ext")
    
    # Process...
    
    self.logger.info(f"✅ Stage {stage_name}: COMPLETED")
    return True
```

---

### Phase 3: Update Fallback Logic

**Current Fallback (multiple locations):**
```python
sep_audio_numbered = self.job_dir / "99_source_separation" / "audio.wav"
sep_audio_plain = self.job_dir / "source_separation" / "audio.wav"
if sep_audio_numbered.exists():
    audio_file = sep_audio_numbered
elif sep_audio_plain.exists():
    audio_file = sep_audio_plain
else:
    audio_file = self.job_dir / "media" / "audio.wav"
```

**New Logic (linear dependency):**
```python
# Each stage reads from previous numbered stage
if source_separation_enabled:
    audio_file = self.job_dir / "02_source_separation" / "audio.wav"
else:
    audio_file = self.job_dir / "01_demux" / "audio.wav"
```

---

### Phase 4: Add Final Exports to Shared Directories

**Keep Shared Directories for Convenience:**
- `transcripts/` - Copy final segments.json and transcript.txt here
- `subtitles/` - Copy all .srt files here
- `media/` - Original input and final muxed output subdirectory

**Implementation:**
```python
# After stage completes, copy to shared location
import shutil

# Copy ASR output to transcripts/
shutil.copy2(
    self.job_dir / "04_asr" / "segments.json",
    self.job_dir / "transcripts" / "segments.json"
)

# Copy subtitle to subtitles/
shutil.copy2(
    self.job_dir / "08_subtitle_generation" / f"{title}.{lang}.srt",
    self.job_dir / "subtitles" / f"{title}.{lang}.srt"
)
```

---

## Implementation Order

### Step 1: Fix Directory Naming (Immediate)
1. ✅ Update `source_separation.py` to use `02_source_separation`
2. ✅ Update `run-pipeline.py` fallback logic
3. ✅ Test source separation stage

### Step 2: Refactor demux Stage
1. ✅ Update `_stage_demux()` to output to `01_demux/audio.wav`
2. ✅ Update `_stage_source_separation()` to read from `01_demux/`
3. ✅ Add input/output logging
4. ✅ Test demux → source_separation flow

### Step 3: Refactor VAD Stage
1. ✅ Update `_stage_pyannote_vad()` to output to `03_pyannote_vad/`
2. ✅ Update input reading (from `02_source_separation` or `01_demux`)
3. ✅ Add input/output logging
4. ✅ Test VAD stage

### Step 4: Refactor ASR Stage
1. ✅ Update `_stage_asr()` to output to `04_asr/segments.json`
2. ✅ Update to read VAD from `03_pyannote_vad/`
3. ✅ Copy output to `transcripts/segments.json` (for compatibility)
4. ✅ Add input/output logging
5. ✅ Test ASR stage

### Step 5: Refactor Translation Stage
1. ✅ Update `_stage_load_transcript()` to read from `04_asr/`
2. ✅ Update translation stages to output to `07_translation/`
3. ✅ Add input/output logging
4. ✅ Test translation stages

### Step 6: Refactor Subtitle Generation
1. ✅ Update to read from `07_translation/`
2. ✅ Update to output to `08_subtitle_generation/`
3. ✅ Copy outputs to `subtitles/` (for compatibility)
4. ✅ Add input/output logging
5. ✅ Test subtitle generation

### Step 7: Refactor Mux Stage
1. ✅ Update to read from `08_subtitle_generation/`
2. ✅ Confirm output already in `09_mux/` and `media/{title}/`
3. ✅ Add input/output logging
4. ✅ Test mux stage

### Step 8: Update Documentation
1. ✅ Update `PIPELINE_DATA_FLOW_ANALYSIS.md`
2. ✅ Update `OUTPUT_DIRECTORY_STRUCTURE.md`
3. ✅ Create migration guide for old jobs

---

## Testing Plan

### Test 1: Full Workflow with New Structure
```bash
./prepare-job.sh in/test.mp4 --workflow subtitle -s hi -t en --user-id test
./run-pipeline.sh -j <job-id>
```

**Verify:**
- All stages output to numbered directories
- Shared directories have copies
- Logs show input/output paths
- No broken dependencies

### Test 2: Resume from Mid-Pipeline
```bash
# Delete 07_translation and later
rm -rf out/2025/11/24/test/1/07_translation
rm -rf out/2025/11/24/test/1/08_subtitle_generation
rm -rf out/2025/11/24/test/1/09_mux

# Resume
./run-pipeline.sh -j <job-id> --resume
```

**Verify:**
- Pipeline resumes from translation
- Reads from correct 04_asr output
- Completes successfully

### Test 3: Without Source Separation
```bash
# Disable source separation in job config
./prepare-job.sh in/test.mp4 --workflow transcribe -s hi --user-id test --no-source-separation
./run-pipeline.sh -j <job-id>
```

**Verify:**
- Stages read from 01_demux directly
- No 02_source_separation directory created
- Fallback logic works correctly

---

## Backward Compatibility

### Old Jobs (Pre-Refactor)
- Fallback logic will still check old locations
- Priority: New numbered dirs → Old dirs → media/

### Migration Tool (Optional)
Create script to migrate old job structure:
```bash
# scripts/migrate-job-structure.sh
./migrate-job-structure.sh out/2025/11/24/1/1
```

This would:
1. Move `media/audio.wav` → `01_demux/audio.wav`
2. Move `99_source_separation/` → `02_source_separation/`
3. Move `transcripts/segments.json` → `04_asr/segments.json`
4. etc.

---

## Risk Assessment

### High Risk Areas
1. **Breaking existing jobs** - Old jobs may not work with new structure
2. **Stage dependencies** - One mistake breaks entire pipeline
3. **Testing coverage** - Need comprehensive testing

### Mitigation
1. Keep fallback logic for old locations
2. Add extensive logging for debugging
3. Test each stage individually before integration
4. Create migration guide

---

## Summary

**Scope:** Major refactoring of stage output directories  
**Impact:** All pipeline stages  
**Benefit:** 
- Clear stage isolation
- Better debugging
- Proper resume support
- Professional structure

**Recommendation:** Implement in phases with extensive testing

---

**Date:** 2024-11-25  
**Status:** Planning Complete - Ready for Implementation  
**Next Steps:** Begin Phase 1 - Fix Directory Naming
