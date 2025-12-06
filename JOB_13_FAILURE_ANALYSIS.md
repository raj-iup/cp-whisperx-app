# Job 13 Failure Analysis

**Date:** 2025-12-05 17:17 UTC  
**Job ID:** job-20251205-rpatel-0013  
**Status:** ❌ FAILED - Terminated during ASR  
**Workflow:** translate (English → Hindi)

---

## Executive Summary

Job 13 failed due to **timeout during MLX-Whisper ASR stage**. The pipeline spent 5+ minutes on source separation, then was terminated by the 6-minute timeout while running ASR transcription.

**Root Cause:** Combined time of source separation (294s) + ASR start (estimated 3+ minutes) exceeded the 360-second (6 minute) timeout.

---

## Timeline Analysis

| Time | Stage | Status | Duration | Notes |
|------|-------|--------|----------|-------|
| 17:11:54 | Start | ▶️ Running | - | Pipeline started |
| 17:11:55 | Demux | ✅ Complete | 1.2s | Audio extracted |
| 17:11:55 | Source Sep | ▶️ Running | - | Started processing |
| 17:16:49 | Source Sep | ✅ Complete | **294.2s** | ⚠️ Very slow (5 min) |
| 17:16:49 | PyAnnote VAD | ▶️ Running | - | Started |
| 17:17:15 | PyAnnote VAD | ✅ Complete | 25.3s | 1 speech segment detected |
| 17:17:15 | ASR | ▶️ Running | - | MLX-Whisper started |
| 17:17:25 | ASR | 🔄 Transcribing | - | Transcription started |
| 17:17:~45 | **TIMEOUT** | ❌ **TERMINATED** | - | 360s limit reached |

**Total Runtime Before Termination:** ~351 seconds (5 min 51 sec)  
**Timeout Setting:** 360 seconds (6 minutes)

---

## Stage-by-Stage Analysis

### Stage 01: Demux ✅
- **Status:** Complete
- **Duration:** 1.2s
- **Output:** audio.wav (23 MB)
- **Issue:** None

### Stage 04: Source Separation ⚠️
- **Status:** Complete (but very slow)
- **Duration:** 294.2 seconds (4 min 54 sec)
- **Quality:** "quality" preset
- **Output:** 
  - vocals.wav (125 MB)
  - accompaniment.wav (125 MB)
- **Issue:** **Abnormally slow** - should be ~2 minutes, took ~5 minutes
- **Possible Causes:**
  - MPS device not fully utilized
  - Demucs model loading overhead
  - First run after system restart (cold cache)
  - "quality" preset is slower than "fast"

### Stage 05: PyAnnote VAD ✅
- **Status:** Complete
- **Duration:** 25.3s
- **Output:** 1 speech segment (745.3s duration)
- **Issue:** None

### Stage 06: ASR ❌
- **Status:** FAILED - Terminated during execution
- **Started:** 17:17:15
- **Last Log:** 17:17:25 ("Starting transcription")
- **Terminated:** ~17:17:45 (estimated)
- **Duration Before Timeout:** ~30 seconds
- **Model:** MLX-Whisper large-v3
- **Backend:** mlx (Apple Silicon)
- **Task:** translate (English → Hindi)
- **Issue:** Timeout before transcription could complete

---

## Configuration Analysis

### Job Configuration
```json
{
  "workflow": "translate",
  "source_language": "en",
  "target_languages": ["hi"],
  "source_separation": {
    "enabled": true,      ← Problem: Added 5 minutes
    "quality": "quality"   ← Problem: Slower than "fast"
  }
}
```

### ASR Configuration
```
Model: large-v3
Backend: mlx
Device: mps
Batch size: 2
Task: translate (English → Hindi)
Audio duration: 745.3s (12.4 minutes)
```

---

## Root Cause Analysis

### Primary Cause: Cumulative Time Exceeded Timeout

**Time Budget:** 360 seconds (6 minutes)  
**Time Used:**
- Demux: 1.2s
- Source separation: 294.2s ← **Main culprit**
- PyAnnote VAD: 25.3s
- ASR (partial): ~30s
- **Total: ~351s** (at timeout)

**Remaining time for ASR:** ~9 seconds (insufficient)

### Contributing Factors

1. **Source Separation Enabled**
   - Added 294 seconds (5 minutes)
   - Not strictly necessary for clean speech audio
   - Should have been disabled for faster processing

2. **Quality Preset**
   - "quality" preset slower than "fast"
   - For translate workflow, "fast" may be sufficient

3. **Timeout Too Short**
   - 360 seconds insufficient for:
     - Source separation (5 min) +
     - ASR (3 min expected) +
     - Other stages
   - Should be 8-10 minutes minimum

4. **MLX-Whisper Task=translate**
   - Translate task may be slower than transcribe
   - Generates output in different language (Hindi)

---

## Why Source Separation Was So Slow

**Expected:** ~2 minutes (120s)  
**Actual:** ~5 minutes (294s)  
**Slowdown:** 2.5x slower than expected

**Possible Reasons:**
1. **Cold cache:** First Demucs run since system restart
2. **MPS optimization:** Apple Silicon may not be fully optimized for Demucs
3. **Quality preset:** Higher quality = more processing time
4. **Model loading:** Large Demucs model takes time to load

---

## Comparison to Successful Jobs

### Job 12 (Transcribe - SUCCESS) ✅
- **Source separation:** DISABLED
- **Total time:** 3 min 6 sec
- **ASR time:** 161s (2.7 min)
- **Outcome:** SUCCESS

### Job 10 (Translate - SUCCESS) ✅
- **Source separation:** ENABLED (first run)
- **Used cached transcript:** Yes (from previous run)
- **Translation only:** 119s (2 min)
- **Outcome:** SUCCESS

### Job 13 (Translate - FAILED) ❌
- **Source separation:** ENABLED
- **Cached transcript:** NO (fresh run)
- **Timeout:** 360s (6 min)
- **Time used:** ~351s before ASR completion
- **Outcome:** TIMEOUT

---

## Impact Assessment

### What Was Lost
- ❌ 5 minutes of processing time
- ❌ No ASR transcript generated
- ❌ No translation output
- ❌ Incomplete job directory

### What Was Retained
- ✅ Demuxed audio (can be reused)
- ✅ Source-separated vocals (can be reused)
- ✅ PyAnnote VAD segments (can be reused)
- ⚠️ Job directory left in incomplete state

---

## Lessons Learned

### 1. Source Separation is Expensive
- Adds 5 minutes to processing time
- Should only be enabled for:
  - Noisy audio (background music, crowd noise)
  - Subtitle workflow (Bollywood movies)
- Should be DISABLED for:
  - Clean speech (podcasts, lectures, technical content)
  - Translate workflow with clean audio

### 2. Timeout Must Account for Full Pipeline
- Current timeout (6 min) insufficient
- Recommended timeouts:
  - Transcribe (no source sep): 5 minutes
  - Transcribe (with source sep): 10 minutes
  - Translate (no source sep): 8 minutes
  - Translate (with source sep): 12 minutes

### 3. Quality Preset Choice Matters
- "quality": Slower, better for movies
- "fast": Faster, sufficient for clean speech
- For technical content: "fast" is adequate

---

## Recommendations

### Immediate Fixes

1. **Disable Source Separation for Clean Audio**
   ```bash
   # For translate workflow with technical content
   ./prepare-job.sh \
     --media "in/Energy Demand in AI.mp4" \
     --workflow translate \
     --source-language en \
     --target-language hi \
     --no-source-separation  # Add this flag
   ```

2. **Increase Timeout**
   ```python
   # In test command
   timeout 480 ./run-pipeline.sh -j job-id  # 8 minutes instead of 6
   ```

3. **Use Cached Transcript**
   ```bash
   # Run transcribe first (faster, no source sep)
   ./prepare-job.sh --media "..." --workflow transcribe
   ./run-pipeline.sh -j job-X
   
   # Then run translate (will use cached transcript)
   ./prepare-job.sh --media "..." --workflow translate -s en -t hi
   ./run-pipeline.sh -j job-Y  # Faster (only translation)
   ```

### Long-Term Improvements

1. **Adaptive Timeouts**
   - Auto-calculate timeout based on:
     - Audio duration
     - Workflow type
     - Source separation enabled/disabled
   
2. **Smart Source Separation**
   - Auto-detect if audio is clean
   - Skip source separation for clean speech
   - Only enable for music/noise detection

3. **Resume Capability**
   - Save intermediate results
   - Resume from last completed stage
   - Don't waste source separation work

4. **Stage-Level Timeouts**
   - Per-stage timeout limits
   - Fail fast if one stage exceeds limit
   - Don't wait for global timeout

---

## How to Recover

### Option 1: Re-run Without Source Separation (RECOMMENDED)
```bash
# Disable source separation in job.json
python3 -c "
import json
with open('out/2025/12/05/rpatel/13/job.json', 'r') as f:
    data = json.load(f)
data['source_separation']['enabled'] = False
with open('out/2025/12/05/rpatel/13/job.json', 'w') as f:
    json.dump(data, f, indent=2)
"

# Re-run with longer timeout
timeout 480 ./run-pipeline.sh -j job-20251205-rpatel-0013
```

### Option 2: Create New Job
```bash
# Prepare fresh job without source separation
./prepare-job.sh \
  --media "in/Energy Demand in AI.mp4" \
  --workflow translate \
  --source-language en \
  --target-language hi

# Edit job.json to disable source separation
# Then run with adequate timeout
timeout 480 ./run-pipeline.sh -j <new-job-id>
```

### Option 3: Two-Step Process (FASTEST)
```bash
# Step 1: Transcribe (fast, ~3 minutes)
./prepare-job.sh --media "..." --workflow transcribe -s en
timeout 300 ./run-pipeline.sh -j job-transcribe

# Step 2: Translate (uses cached transcript, ~2 minutes)
./prepare-job.sh --media "..." --workflow translate -s en -t hi
timeout 300 ./run-pipeline.sh -j job-translate
```

---

## Prevention Strategy

### Pre-Job Checklist
- [ ] Is this clean speech audio? → Disable source separation
- [ ] Is timeout adequate? (5-12 min depending on workflow)
- [ ] Can I use cached transcript? → Use two-step process
- [ ] Do I need "quality" preset? → Consider "fast" for clean audio

### Job Configuration Template
```json
{
  "workflow": "translate",
  "source_separation": {
    "enabled": false,  // DISABLE for clean audio
    "quality": "fast"   // Use "fast" for speed
  }
}
```

---

## Conclusion

**Job 13 failed due to inadequate timeout** for the combined source separation + ASR processing.

**Key Findings:**
- Source separation took 294s (5 min) - much longer than expected
- Timeout of 360s (6 min) insufficient for full pipeline
- ASR never completed - only got 30s before termination

**Resolution:**
- Disable source separation for clean speech
- Increase timeout to 8-10 minutes
- Use two-step process (transcribe → translate) for efficiency

**Status:** ✅ Root cause identified, solutions documented

---

**Analysis Date:** 2025-12-05 23:30 UTC  
**Analyzed By:** GitHub Copilot  
**Related Docs:** TEST_1_FINAL_VALIDATION.md, TEST_2_FINAL_VALIDATION.md
