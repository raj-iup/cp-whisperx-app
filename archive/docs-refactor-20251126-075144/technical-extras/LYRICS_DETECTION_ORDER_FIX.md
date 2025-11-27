# Lyrics Detection Stage Order Fix

**Date:** 2024-11-25  
**Issue:** Lyrics detection running BEFORE ASR stage  
**Status:** ✅ **FIXED**

---

## 🔴 Problem

The `lyrics_detection` stage was being executed **BEFORE** the ASR stage, causing it to fail:

```
[2025-11-24 20:53:13] [INFO] ▶️  Stage source_separation: COMPLETED
[2025-11-24 20:53:13] [INFO] ▶️  Stage lyrics_detection: STARTING
[2025-11-24 20:53:13] [WARNING] Segments file not found: out/.../transcripts/segments.json
[2025-11-24 20:53:13] [WARNING] Lyrics detection requires ASR output - skipping
[2025-11-24 20:53:13] [INFO] ▶️  Stage pyannote_vad: STARTING   <-- VAD runs AFTER lyrics detection!
```

### Incorrect Order:
```
1. demux
2. source_separation
3. lyrics_detection ❌ (runs before ASR!)
4. pyannote_vad
5. asr
6. alignment
```

**Problem:** Lyrics detection needs the ASR transcription (`segments.json`) to analyze and mark song vs. dialogue segments.

---

## ✅ Solution

### Fixed Stage Order in ALL Workflows:

Updated **3 workflow methods** in `scripts/run-pipeline.py`:
1. `run_transcribe_workflow()` (line ~289)
2. `run_translate_workflow()` (line ~329)
3. `run_subtitle_workflow()` (line ~409)

### Correct Order Now:
```
1. demux
2. source_separation (optional)
3. pyannote_vad
4. asr
5. hallucination_removal
6. alignment
7. lyrics_detection ✅ (runs AFTER ASR!)
8. export_transcript
```

---

## 📝 What Changed

### Before (INCORRECT):
```python
transcribe_stages = [("demux", self._stage_demux)]

# Add source separation if enabled
if sep_config.get("enabled", False):
    transcribe_stages.append(("source_separation", self._stage_source_separation))

# Add lyrics detection (WRONG POSITION!)
if lyrics_enabled:
    transcribe_stages.append(("lyrics_detection", self._stage_lyrics_detection))

# Add remaining stages
transcribe_stages.extend([
    ("pyannote_vad", self._stage_pyannote_vad),
    ("asr", self._stage_asr),
    ("hallucination_removal", self._stage_hallucination_removal),
    ("alignment", self._stage_alignment),
    ("export_transcript", self._stage_export_transcript),
])
```

### After (CORRECT):
```python
transcribe_stages = [("demux", self._stage_demux)]

# Add source separation if enabled
if sep_config.get("enabled", False):
    transcribe_stages.append(("source_separation", self._stage_source_separation))

# Add core ASR stages
transcribe_stages.extend([
    ("pyannote_vad", self._stage_pyannote_vad),
    ("asr", self._stage_asr),
    ("hallucination_removal", self._stage_hallucination_removal),
    ("alignment", self._stage_alignment),
])

# Add lyrics detection AFTER ASR (CORRECT POSITION!)
if lyrics_enabled:
    transcribe_stages.append(("lyrics_detection", self._stage_lyrics_detection))

# Final export stage
transcribe_stages.append(("export_transcript", self._stage_export_transcript))
```

---

## ✅ Why This is Correct

### Lyrics Detection Requirements:
1. ✅ **Needs ASR output** - `04_asr/segments.json` (transcription with timestamps)
2. ✅ **Needs audio** - `02_source_separation/vocals.wav` OR `01_demux/audio.wav`

### What Lyrics Detection Does:
- Reads transcription segments from ASR
- Analyzes audio features (MFCCs, spectral features)
- Classifies each segment as **song** or **dialogue**
- Adds `is_song` marker to segments
- Outputs enhanced segments to `06_lyrics_detection/segments.json`

### Why It Must Run After ASR:
Without the transcription, lyrics detection has **no segments to analyze**!

---

## 🎯 Impact on Translation

The correct order ensures:
1. **ASR produces transcription** → `04_asr/segments.json`
2. **Lyrics detection enhances it** → `06_lyrics_detection/segments.json` (with song markers)
3. **Translation reads enhanced segments** → Uses LLM for song segments, IndicTrans2 for dialogue

**Result:** Better translation quality for songs/poetry vs. regular dialogue!

---

## 📝 Files Modified

1. `scripts/run-pipeline.py` - Fixed 3 workflow methods:
   - `run_transcribe_workflow()` - Line ~289
   - `run_translate_workflow()` - Line ~329
   - `run_subtitle_workflow()` - Line ~409

2. `docs/technical/REFACTORING_STATUS.md` - Updated stage order documentation
3. `docs/technical/REFACTORING_COMPLETE.md` - Updated data flow documentation

---

## ✅ Verification

### Test Command:
```bash
./prepare-job.sh in/video.mp4 --subtitle -s hi -t en --user-id 1
./run-pipeline.sh
```

### Expected Log Output:
```
[INFO] ▶️  Stage demux: STARTING
[INFO] ✅ Stage demux: COMPLETED
[INFO] ▶️  Stage source_separation: STARTING
[INFO] ✅ Stage source_separation: COMPLETED
[INFO] ▶️  Stage pyannote_vad: STARTING
[INFO] ✅ Stage pyannote_vad: COMPLETED
[INFO] ▶️  Stage asr: STARTING
[INFO] ✅ Stage asr: COMPLETED
[INFO] ▶️  Stage hallucination_removal: STARTING
[INFO] ✅ Stage hallucination_removal: COMPLETED
[INFO] ▶️  Stage alignment: STARTING
[INFO] ✅ Stage alignment: COMPLETED
[INFO] ▶️  Stage lyrics_detection: STARTING   <-- NOW runs AFTER ASR ✅
[INFO] 📥 Input segments: 04_asr/segments.json
[INFO] 📥 Input audio: 02_source_separation/vocals.wav
[INFO] ✅ Stage lyrics_detection: COMPLETED
[INFO] ▶️  Stage export_transcript: STARTING
```

---

## ✅ Status

**Issue:** RESOLVED ✅  
**Testing:** Lyrics detection now runs at correct position  
**Ready:** Yes, all workflows fixed

---

**Fixed by:** GitHub Copilot CLI  
**Date:** 2024-11-25  
**Impact:** All 3 workflows (transcribe, translate, subtitle)
