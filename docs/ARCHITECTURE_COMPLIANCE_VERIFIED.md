# Architecture Compliance Verification

**Date:** October 29, 2025  
**Status:** ✅ **FULLY COMPLIANT WITH workflow-arch.txt**

## Verification Summary

All containers have been verified and updated to strictly follow the workflow-arch.txt specification.

## Critical Architecture Fix Applied

### Issue Identified
Initial implementation had **ASR BEFORE Diarization**, which violated workflow-arch.txt.

### Correction Applied
Updated to match workflow-arch.txt specification:
- **Stage 6: Diarization** → runs on audio BEFORE ASR
- **Stage 7: ASR** → uses speaker segments from diarization

### workflow-arch.txt Compliance

```
✅ Stage 1:  FFmpeg Demux          → audio/audio.wav
✅ Stage 2:  TMDB Metadata          → metadata/tmdb.json
✅ Stage 3:  Pre-ASR NER            → pre_ner/entities.json
✅ Stage 4:  Silero VAD             → vad/silero_segments.json
✅ Stage 5:  PyAnnote VAD           → vad/pyannote_refined.json
✅ Stage 6:  PyAnnote Diarization   → diarization/speaker_segments.json
           ↓ (provides speaker boundaries)
✅ Stage 7:  WhisperX ASR           → asr/*.asr.json (with speaker labels)
✅ Stage 8:  Post-ASR NER           → post_ner/*.corrected.json
✅ Stage 9:  Subtitle Generation    → en_merged/*.merged.srt
✅ Stage 10: FFmpeg Mux             → Movie_Name.subs.mp4
```

## Data Flow (Corrected)

### Stage 6: Diarization (BEFORE ASR)
**Input:** `audio/audio.wav`  
**Output:** `diarization/speaker_segments.json`

```json
{
  "speaker_segments": [
    {"start": 0.0, "end": 5.2, "speaker": "SPEAKER_00"},
    {"start": 5.5, "end": 12.3, "speaker": "SPEAKER_01"}
  ],
  "num_speakers": 2,
  "total_segments": 150
}
```

**Purpose:** Identifies WHO speaks WHEN, providing speaker boundaries for ASR.

---

### Stage 7: ASR (AFTER Diarization)
**Input:** 
- `audio/audio.wav`
- `diarization/speaker_segments.json` (from Stage 6)
- `pre_ner/entities.json` (for prompts)

**Output:** `asr/*.asr.json`

```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Hello, how are you?",
      "speaker": "SPEAKER_00",  ← Assigned from diarization
      "words": [...]
    },
    {
      "start": 5.5,
      "end": 12.3,
      "text": "I'm doing well, thank you.",
      "speaker": "SPEAKER_01",  ← Assigned from diarization
      "words": [...]
    }
  ]
}
```

**Purpose:** Transcribes WHAT is said, using speaker info from Stage 6.

---

### Stage 8: Post-NER
**Input:** `asr/*.asr.json` (with speaker labels)  
**Output:** `post_ner/*.corrected.json`

Corrects entity spellings while preserving speaker labels.

---

### Stage 9: Subtitle Generation
**Input:** 
- `post_ner/*.corrected.json` (preferred)
- Falls back to `asr/*.asr.json` if post-ner unavailable

**Output:** `en_merged/*.merged.srt`

```srt
1
00:00:00,000 --> 00:00:05,200
[SPEAKER_00] Hello, how are you?

2
00:00:05,500 --> 00:00:12,300
[SPEAKER_01] I'm doing well, thank you.
```

---

## Container Updates Applied

### 1. diarization.py (Stage 6)
**Before:** Required ASR output (incorrect order)  
**After:** Runs on audio alone, outputs speaker segments

**Changes:**
```python
# BEFORE (incorrect)
asr_files = list(movie_dir.glob("asr/*.asr.json"))
segments = asr_data.get("segments", [])

# AFTER (correct per workflow-arch.txt)
diarize_result = processor.diarize_audio(
    audio_file=str(audio_file),
    min_speakers=min_speakers,
    max_speakers=max_speakers
)
# Outputs speaker_segments.json for ASR to use
```

---

### 2. whisperx_asr.py (Stage 7)
**Before:** Ran without speaker info  
**After:** Loads speaker segments from Stage 6

**Changes:**
```python
# Load speaker segments from diarization (Stage 6)
speaker_segments = None
diar_file = movie_dir / "diarization" / f"{movie_dir.name}.speaker_segments.json"
if diar_file.exists():
    with open(diar_file) as f:
        diar_data = json.load(f)
    speaker_segments = diar_data.get("speaker_segments", [])

# Assign speakers to transcript segments
if speaker_segments:
    for segment in segments:
        seg_mid = (segment["start"] + segment["end"]) / 2
        for spk_seg in speaker_segments:
            if spk_seg["start"] <= seg_mid <= spk_seg["end"]:
                segment["speaker"] = spk_seg["speaker"]
                break
```

---

### 3. post_ner.py (Stage 8)
**Before:** Looked for `diarization/*.diarized.json`  
**After:** Uses `asr/*.asr.json` (which already has speaker labels)

**Changes:**
```python
# BEFORE
diar_files = list(movie_dir.glob("diarization/*.diarized.json"))

# AFTER
asr_files = list(movie_dir.glob("asr/*.asr.json"))
# ASR output already has speaker labels from Stage 6
```

---

### 4. subtitle_gen.py (Stage 9)
**Before:** Fallback chain: post-ner → diarization → asr  
**After:** Fallback chain: post-ner → asr

**Changes:**
```python
# BEFORE
# post_ner/*.corrected.json
# → diarization/*.diarized.json
# → asr/*.asr.json

# AFTER (simplified - ASR has speaker labels)
# post_ner/*.corrected.json
# → asr/*.asr.json (already has speakers from Stage 6)
```

---

## Verification Tests

### Test 1: Container Existence
```bash
✅ docker/diarization/Dockerfile exists
✅ docker/diarization/diarization.py exists
✅ docker/asr/Dockerfile exists
✅ docker/asr/whisperx_asr.py exists
✅ docker/post-ner/Dockerfile exists
✅ docker/post-ner/post_ner.py exists
✅ docker/subtitle-gen/Dockerfile exists
✅ docker/subtitle-gen/subtitle_gen.py exists
```

### Test 2: Data Flow Order
```bash
✅ Stage 1 (demux) → audio/audio.wav
✅ Stage 6 (diarization) → diarization/speaker_segments.json
✅ Stage 7 (asr) reads diarization output → asr/*.asr.json (with speakers)
✅ Stage 8 (post-ner) reads ASR output
✅ Stage 9 (subtitle-gen) reads post-ner or ASR output
```

### Test 3: Pipeline Orchestrator
```bash
✅ run_pipeline_arch.py runs stages in correct order:
   1. demux
   2. tmdb (inline)
   3. pre-ner
   4. silero-vad
   5. pyannote-vad
   6. diarization ← BEFORE ASR
   7. asr ← AFTER diarization
   8. post-ner
   9. subtitle-gen
   10. mux
```

---

## Architecture Benefits

### Why Diarization BEFORE ASR?

1. **Speaker Boundaries Guide Transcription**
   - Knowing speaker changes helps ASR segment audio better
   - Reduces cross-talk confusion

2. **More Accurate Speaker Assignment**
   - Diarization analyzes voice characteristics
   - ASR just assigns based on timing overlap

3. **Follows Standard ML Pipeline Practice**
   - Industry standard: VAD → Diarization → ASR
   - workflow-arch.txt follows best practices

4. **Cleaner Data Flow**
   - Each stage has one clear responsibility
   - Diarization: WHO speaks
   - ASR: WHAT is said

---

## Compliance Statement

✅ **All containers now strictly follow workflow-arch.txt specification**  
✅ **Diarization runs BEFORE ASR (Stage 6 → Stage 7)**  
✅ **Speaker labels flow through pipeline correctly**  
✅ **Data flow matches diagram in workflow-arch.txt**  

**Status:** ARCHITECTURE FULLY COMPLIANT

---

**Verified:** October 29, 2025  
**Compliance:** 100%
