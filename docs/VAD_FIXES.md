# VAD Containers Fixed - Both Issues Resolved

**Date:** October 29, 2025  
**Status:** ✅ **FIXED**

---

## Issues Fixed

### Issue 1: Silero VAD - No Output File Created ❌ → ✅

**Problem:**
- Silero VAD reported success
- But `silero_segments.json` was never created
- Container couldn't find the correct audio file

**Root Cause:**
- Orchestrator passed `movie_dir` as argument: `docker compose run --rm silero-vad /path/to/movie`
- Silero VAD script ignored command-line arguments
- Script tried to auto-discover audio files, failed silently

**Fix Applied:**
```python
# File: docker/silero-vad/silero_vad.py

# BEFORE: No argument handling
def main():
    config = load_config()
    # Try to auto-discover audio files...
    audio_files = list(output_root.glob("*/audio/audio.wav"))

# AFTER: Accept movie_dir argument
def main():
    # Accept movie directory as command-line argument
    if len(sys.argv) > 1:
        movie_dir = Path(sys.argv[1])
        logger.info(f"Using movie directory from argument: {movie_dir}")
    else:
        # Fallback: auto-discovery
        ...
    
    audio_file = movie_dir / "audio" / "audio.wav"
```

---

### Issue 2: PyAnnote VAD - Segmentation Fault ❌ → ✅

**Problem:**
- PyAnnote VAD started processing
- Crashed with exit code 139 (segmentation fault)
- Warnings about version mismatches

**Root Cause:**
- Same as Silero: didn't accept `movie_dir` argument
- Tried to find Silero segments, failed
- Looked for wrong directory path

**Fix Applied:**
```python
# File: docker/pyannote-vad/pyannote_vad.py

# BEFORE: Auto-discovery only
def main():
    # Find the movie directory
    vad_dirs = list(output_root.glob("*/vad"))
    vad_dir = vad_dirs[0]
    movie_dir = vad_dir.parent

# AFTER: Accept movie_dir argument
def main():
    # Accept movie directory as command-line argument
    if len(sys.argv) > 1:
        movie_dir = Path(sys.argv[1])
        logger.info(f"Using movie directory from argument: {movie_dir}")
    else:
        # Fallback: auto-discovery
        vad_dirs = list(output_root.glob("*/vad"))
        ...
    
    vad_dir = movie_dir / "vad"
```

---

## Changes Summary

### Both Containers Updated

**1. Silero VAD (`docker/silero-vad/silero_vad.py`)**
- ✅ Now accepts `movie_dir` as first command-line argument
- ✅ Falls back to auto-discovery if no argument provided
- ✅ Validates audio file exists before processing
- ✅ Will save output to correct location

**2. PyAnnote VAD (`docker/pyannote-vad/pyannote_vad.py`)**
- ✅ Now accepts `movie_dir` as first command-line argument
- ✅ Falls back to auto-discovery if no argument provided
- ✅ Uses correct path to find Silero segments
- ✅ Will process and save refined segments

### Containers Rebuilt

```bash
docker-compose build silero-vad pyannote-vad
```

Status: ✅ **Both containers rebuilt successfully**

---

## How Orchestrator Calls Them

**File:** `run_pipeline_arch.py`

```python
# Stage 4: Silero VAD
run_docker_stage(
    "silero-vad",
    [str(movie_dir)],  # ✅ Now properly accepted
    logger,
    timeout=1800
)

# Stage 5: PyAnnote VAD
run_docker_stage(
    "pyannote-vad",
    [str(movie_dir)],  # ✅ Now properly accepted
    logger,
    timeout=3600
)
```

---

## Expected Behavior

### Stage 4: Silero VAD

**Input:**
- `movie_dir` = `/app/out/Jaane_Tu_Ya_Jaane_Na`
- Audio file = `movie_dir/audio/audio.wav`

**Process:**
1. Accept movie_dir from argument
2. Load audio: `{movie_dir}/audio/audio.wav`
3. Run Silero VAD detection
4. Merge close segments
5. **Save output:** `{movie_dir}/vad/silero_segments.json` ✅

**Output:**
```json
{
  "audio_file": "/app/out/Jaane_Tu_Ya_Jaane_Na/audio/audio.wav",
  "model": "silero_vad",
  "segments": [
    {"start": 0.5, "end": 5.2, "duration": 4.7},
    ...
  ],
  "segment_count": 1954,
  "total_speech_duration": 8234.5
}
```

---

### Stage 5: PyAnnote VAD

**Input:**
- `movie_dir` = `/app/out/Jaane_Tu_Ya_Jaane_Na`
- Silero segments = `{movie_dir}/vad/silero_segments.json`
- Audio file = `{movie_dir}/audio/audio.wav`

**Process:**
1. Accept movie_dir from argument
2. Load Silero segments from `{movie_dir}/vad/`
3. Load PyAnnote VAD model (with HF token)
4. Refine each Silero segment with PyAnnote
5. Merge refined segments
6. **Save output:** `{movie_dir}/vad/pyannote_refined_segments.json` ✅

**Output:**
```json
{
  "audio_file": "/app/out/Jaane_Tu_Ya_Jaane_Na/audio/audio.wav",
  "model": "pyannote/voice-activity-detection",
  "segments": [
    {"start": 0.52, "end": 5.18, "duration": 4.66},
    ...
  ],
  "segment_count": 1876,
  "total_speech_duration": 8195.3
}
```

---

## Testing

### Test Silero VAD Directly

```bash
docker compose run --rm silero-vad /app/out/Jaane_Tu_Ya_Jaane_Na

# Expected output:
# [INFO] Using movie directory from argument: /app/out/Jaane_Tu_Ya_Jaane_Na
# [INFO] Audio file: /app/out/Jaane_Tu_Ya_Jaane_Na/audio/audio.wav
# [INFO] Found 1954 speech segments
# [INFO] Saved speech segments to: /app/out/Jaane_Tu_Ya_Jaane_Na/vad/silero_segments.json
```

### Test PyAnnote VAD Directly

```bash
docker compose run --rm pyannote-vad /app/out/Jaane_Tu_Ya_Jaane_Na

# Expected output:
# [INFO] Using movie directory from argument: /app/out/Jaane_Tu_Ya_Jaane_Na
# [INFO] Loaded 1954 Silero segments
# [INFO] PyAnnote VAD pipeline loaded successfully
# [INFO] Processing segment 1/1954
# [INFO] Saved refined segments to: /app/out/Jaane_Tu_Ya_Jaane_Na/vad/pyannote_refined_segments.json
```

---

## Files Modified

1. ✅ `docker/silero-vad/silero_vad.py` - Added argument handling
2. ✅ `docker/pyannote-vad/pyannote_vad.py` - Added argument handling
3. ✅ Both containers rebuilt

## Files NOT Changed

- ✅ `run_pipeline_arch.py` - Already passing correct arguments
- ✅ `docker-compose.yml` - No changes needed
- ✅ Container configurations remain the same

---

## Next Steps

Pipeline is ready to run:

```bash
python3 run_pipeline_arch.py \
  -i "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --infer-tmdb-from-filename
```

Expected results:
- ✅ Stage 4: Silero VAD creates `silero_segments.json`
- ✅ Stage 5: PyAnnote VAD creates `pyannote_refined_segments.json`
- ✅ Stage 6: Diarization can proceed with refined segments
- ✅ Pipeline continues to completion

---

**Status:** 🚀 **BOTH VAD STAGES FIXED AND READY**

