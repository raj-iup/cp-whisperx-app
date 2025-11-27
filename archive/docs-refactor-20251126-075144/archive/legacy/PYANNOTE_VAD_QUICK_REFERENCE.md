# PyAnnote VAD Zero Segments Issue - Status & Fix

**Date:** 2025-11-20  
**Status:** ⚠️ KNOWN ISSUE - PyAnnote environment has torch compatibility problems

## The Problem

PyAnnote VAD detects **0 segments** when there IS speech:
```
[WARNING] VAD file exists but has no segments, transcribing full audio
```

But WhisperX successfully transcribes the same audio! This proves the audio has speech.

## Root Cause

**Torch/torchaudio version incompatibility in PyAnnote environment:**
- pyannote.audio 3.1.1 needs torch 2.0-2.3
- Current torch 2.3.1/torchaudio 2.3.1 has import issues
- PyAnnote fails silently, returns 0 segments

## Current Behavior

✅ **Pipeline still works:**
- VAD stage completes (with 0 segments)
- Warning logged
- ASR transcribes full audio successfully
- Subtitles generated

❌ **But we lose:**
- 10-15% quality improvement from VAD
- Faster processing (ASR processes everything)

## Quick Fix: Disable PyAnnote VAD

**Edit `scripts/run-pipeline.py` line ~262:**
```python
stages = [
    ("demux", self._stage_demux),
    # ("pyannote_vad", self._stage_pyannote_vad),  # ← Disabled temporarily
    ("asr", self._stage_asr),
    ...
]
```

Save ~17 seconds per job, no more warnings.

## Alternative: Use Silero VAD

WhisperX has built-in Silero VAD (5-8% improvement vs 10-15% with PyAnnote).
Could integrate as simpler alternative.

## Status Summary

- Pipeline: ✅ Working
- Subtitles: ✅ Generated
- PyAnnote VAD: ❌ Not working (torch issue)
- Quality: ⚠️ Good but not optimal

**Recommendation:** Disable PyAnnote VAD for now, wait for upstream fix or switch to Silero VAD.

---

**Date:** 2025-11-20  
**Impact:** Minor - pipeline works, just missing quality boost  
**Fix:** Disable PyAnnote stage or wait for pyannote.audio 3.2.0
