# Log Analysis - Issues Found

**Job:** `out/2025/11/24/1/1`  
**Date:** 2024-11-24  
**Analysis Date:** 2024-11-25

---

## Critical Issues

### 1. ❌ Wrong Directory Naming: `99_source_separation`
**Found in:** `99_source_separation_20251124_195656.log`

```
[INFO] ✓ Output audio (vocals only): out/2025/11/24/1/1/99_source_separation/audio.wav
```

**Expected:** `02_source_separation/`  
**Impact:** Confusing numbering, breaks sequential stage logic  
**Fix:** Update `scripts/source_separation.py` line ~30

---

### 2. ❌ Outputs Not in Stage Directories

**Current Locations:**
```
media/audio.wav                          ← Should be in 01_demux/
transcripts/segments.json                ← Should be in 04_asr/
transcripts/transcript.txt               ← Should be in 04_asr/ or export stage
subtitles/*.srt                          ← Should be in 08_subtitle_generation/
```

**Impact:** 
- Hard to track stage outputs
- Difficult to resume from specific stage
- No clear stage isolation

---

### 3. ⚠️  ASR Hallucinations in Transcript

**Found in:** Transcript output around 05:01

```
[04:59.380 --> 05:01.560] 把ग� local
[05:01.560 --> 05:01.560]  local
[05:01.560 --> 05:01.560]  local
[05:01.560 --> 05:01.560]  local
... (repeated 20+ times)
```

**Cause:** Whisper ASR hallucination (known issue with silence/music)  
**Solution:** Hallucination removal stage exists but may need tuning  
**Fix:** Verify `_stage_hallucination_removal()` runs and filters these

---

### 4. ⚠️  No Input Path Logging

**Current:**
```
[INFO] ▶️  Stage demux: STARTING
[INFO] Extracting audio clip (from 00:04:00 to 00:10:00)...
```

**Should Be:**
```
[INFO] ▶️  Stage 01_demux: STARTING
[INFO] 📥 Input: media/Jaane Tu Ya Jaane Na 2008.mp4
[INFO] 📤 Output: 01_demux/audio.wav
[INFO] Extracting audio clip (from 00:04:00 to 00:10:00)...
```

**Impact:** Hard to debug data flow issues

---

## Minor Issues

### 5. ⚠️  Demucs Auto-Installation

**Found in:** `99_source_separation_20251124_195656.log`

```
[WARNING] Demucs is not installed
[INFO] Demucs not found. Installing...
[INFO] ✓ Demucs installed successfully
```

**Issue:** Should be installed during bootstrap, not during job execution  
**Impact:** First job takes extra time  
**Fix:** Ensure `./bootstrap.sh` installs demucs

---

### 6. ℹ️  Log File Naming

**Current:** `99_pipeline_20251124_195654.log`  
**Better:** `pipeline_20251124_195654.log` (remove 99_ prefix)

---

## Recommendations

### Immediate Fixes (Can Do Now)

1. **Fix `99_source_separation` → `02_source_separation`**
   ```bash
   # Edit scripts/source_separation.py
   # Change: output_dir = job_dir / "99_source_separation"
   # To:     output_dir = job_dir / "02_source_separation"
   ```

2. **Add Input Logging to All Stages**
   ```python
   self.logger.info(f"📥 Input: {input_file.relative_to(self.job_dir)}")
   self.logger.info(f"📤 Output: {output_file.relative_to(self.job_dir)}")
   ```

3. **Verify Hallucination Removal**
   ```bash
   # Check if stage ran
   grep "hallucination_removal" out/2025/11/24/1/1/logs/*.log
   ```

### Medium-Term Fixes (Plan & Implement)

4. **Refactor Stage Outputs to Numbered Directories**
   - See: `docs/technical/STAGE_OUTPUT_REFACTORING_PLAN.md`
   - Implement in phases over 1-2 weeks
   - Test each phase thoroughly

5. **Add Demucs to Bootstrap**
   ```bash
   # Edit bootstrap.sh
   # Add: ./install-demucs.sh
   ```

### Long-Term Improvements

6. **Add Stage Output Validation**
   - Check file exists after stage completes
   - Verify file size > 0
   - Log warnings if suspicious

7. **Add Resume Support with Stage State**
   - Track completed stages in manifest
   - Allow resume from any stage
   - Skip completed stages automatically

---

## Testing Recommendations

### Test 1: Verify Current Job Output

```bash
# Check what was actually produced
ls -la out/2025/11/24/1/1/

# Check final outputs
ls -la out/2025/11/24/1/1/subtitles/
ls -la out/2025/11/24/1/1/media/*/

# Check transcript for hallucinations
cat out/2025/11/24/1/1/transcripts/transcript.txt | grep -A 5 "local"
```

### Test 2: Re-run with Fixes

```bash
# After applying fixes
./prepare-job.sh in/"Jaane Tu Ya Jaane Na 2008.mp4" \
  --workflow subtitle \
  -s hi -t en \
  --start-time 00:04:00 \
  --end-time 00:10:00 \
  --debug \
  --user-id test_fixed

./run-pipeline.sh -j <job-id>

# Verify outputs in correct directories
ls -la out/2025/11/24/test_fixed/1/01_demux/
ls -la out/2025/11/24/test_fixed/1/02_source_separation/
ls -la out/2025/11/24/test_fixed/1/04_asr/
```

---

## Files Requiring Changes

### Critical (Fix Now)
1. `scripts/source_separation.py` - Change 99_ to 02_
2. `scripts/run-pipeline.py` - Update fallback logic to check 02_ instead of 99_

### Important (Plan & Implement)
3. `scripts/run-pipeline.py` - All `_stage_*()` methods
4. `scripts/pyannote_vad.py` - Output to 03_pyannote_vad/
5. `scripts/demux.py` - Output to 01_demux/ (if exists)

### Documentation
6. `docs/technical/PIPELINE_DATA_FLOW_ANALYSIS.md` - Update with new structure
7. `docs/technical/OUTPUT_DIRECTORY_STRUCTURE.md` - Add stage subdirectory details
8. `docs/technical/STAGE_OUTPUT_REFACTORING_PLAN.md` - Implementation guide (DONE)

---

## Summary

**Issues Found:** 6 (2 critical, 2 warnings, 2 minor)  
**Immediate Action Required:** Fix directory naming (99_ → 02_)  
**Planning Required:** Full stage output refactoring  
**Time Estimate:** 
- Immediate fixes: 30 minutes
- Full refactoring: 1-2 weeks

**Recommendation:** 
1. Fix critical issues now (directory naming)
2. Plan full refactoring in phases
3. Implement and test each phase
4. Update documentation as you go

---

**Date:** 2024-11-25  
**Analyst:** Pipeline Log Analysis  
**Status:** Issues Identified - Ready for Fixes
