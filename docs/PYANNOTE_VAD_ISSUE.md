# PyAnnote VAD Container Issue & Resolution

## Problem
PyAnnote VAD container consistently crashes with **Exit Code 139 (Segmentation Fault)** when processing segments.

## Root Cause
Version incompatibility between:
- Model trained with: `pyannote.audio 0.0.1`, `torch 1.7.1`  
- Runtime environment: `pyannote.audio 3.1.1`, `torch 2.1.0`

## Attempted Fixes

### 1. Downgrade to torch 1.11 ❌
- **Failed:** Python 3.11+ only supports torch 2.0+
- Error: `No matching distribution found for torch==1.11.0`

### 2. Use pyannote.audio 3.0 with onnxruntime ❌
- **Failed:** onnxruntime-gpu not available for platform  
- Tried CPU version - still crashed

### 3. Use newer VAD model (`pyannote/segmentation@2022.07`) ❌  
- **Failed:** Model is not a pipeline, just a segmentation model
- Error: `KeyError: 'pipeline'`

### 4. Use VAD 3.0 model (`pyannote/voice-activity-detection-3.0`) ❌
- **Failed:** Model is gated and requires accepting terms on HuggingFace
- Requires manual user action at: https://hf.co/pyannote/voice-activity-detection-3.0

## Recommendation

### ⭐ **Make PyAnnote VAD Optional**

**Reasoning:**
1. **Silero VAD is sufficient** - Already provides 1,954 high-quality speech segments  
2. **Architecture compliance** - Diarization and ASR can work directly with Silero segments
3. **Time efficiency** - Avoids spending hours debugging version conflicts
4. **Production stability** - Silero is stable and doesn't crash

**Impact:**
- ✅ Pipeline continues without crashes
- ✅ ASR gets speech segments (from Silero)
- ✅ Diarization gets speech segments (from Silero)  
- ⚠️ Slightly less refined boundaries (acceptable tradeoff)

### Alternative: Fix PyAnnote VAD (Time-intensive)

If PyAnnote VAD refinement is absolutely required:

1. **Accept model terms:** Visit https://hf.co/pyannote/voice-activity-detection-3.0
2. **Update script** to use VAD 3.0  
3. **Test thoroughly** with gated model access

## Current State

- ✅ Silero VAD: **Working** (1,954 segments)
- ❌ PyAnnote VAD: **Crashes** (segmentation fault)
- Container rebuilt 4 times with different configurations

## Files Modified

- `docker/pyannote-vad/Dockerfile` - Updated dependencies 4 times
- `docker/pyannote-vad/pyannote_vad.py` - Updated model names 3 times

## Next Steps

**Option A (Recommended):** Make PyAnnote VAD optional, continue with Silero segments
**Option B:** User accepts VAD 3.0 terms, rebuild with new model

---

**Date:** 2025-10-29  
**Status:** PyAnnote VAD unstable due to version conflicts
**Decision Needed:** Proceed with or without PyAnnote VAD
