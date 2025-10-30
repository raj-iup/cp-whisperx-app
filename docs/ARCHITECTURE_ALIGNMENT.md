# Architecture Alignment - cp-whisperx-app

**Date:** 2025-10-28  
**Status:** ✅ Fully aligned with workflow-arch.txt

## Workflow Architecture Compliance

The pipeline implementation follows the exact architecture specified in `workflow-arch.txt`:

### 1. Audio File → ✅ Implemented
- **Implementation:** Input video/audio processing via ffmpeg
- **Location:** `run_pipeline.py` - Stage 5 (Video clipping/audio extraction)
- **Code:** Uses ffmpeg to extract/process audio streams

### 2. Separate VAD Model → ✅ Implemented
- **Implementation:** Silero VAD (independent of pyannote)
- **Location:** ASR container with WhisperX
- **Code:** `vad_method='silero'` in `run_pipeline.py` ASR script
- **Key Achievement:** Patched WhisperX to make pyannote optional, uses Silero VAD instead
- **Files:** `docker/asr/patch_whisperx.py` patches WhisperX to support Silero without pyannote

### 3. Speech Segments (timestamps) → ✅ Implemented
- **Implementation:** Silero VAD produces speech/silence timestamps
- **Output:** VAD segments with start/end times
- **Process:** VAD runs before transcription to identify speech regions

### 4. WhisperX ASR → ✅ Implemented
- **Implementation:** WhisperX large-v2 model for transcription + translation
- **Location:** ASR Docker container
- **Features:**
  - Transcription: Hindi audio → Hindi text
  - Translation: Hindi text → English text
  - Batch processing with int8 quantization
  - CPU-optimized execution

### 5. Text + Word Alignments → ✅ Implemented
- **Implementation:** Word-level alignment using WhisperX alignment models
- **Output Format:**
```json
{
  "segments": [
    {
      "start": 263.138,
      "end": 264.12,
      "text": " Really?",
      "words": [
        {
          "word": "Really?",
          "start": 263.138,
          "end": 264.12,
          "score": 0.53
        }
      ]
    }
  ]
}
```
- **Location:** ASR output saved to `out/<movie>/asr/<movie>.asr.json`

### 6. Optional: Speaker Diarization → ✅ Implemented (Optional)
- **Implementation:** Pyannote.audio in separate diarization container
- **Location:** Diarization Docker container
- **Process:** Can be enabled/disabled via config
- **Config:** `DEVICE_DIARIZATION=` (empty = skip, "cpu" = enable)
- **Output:** Assigns speaker labels to segments

### 7. Final Structured Transcript → ✅ Implemented
- **Implementation:** SRT subtitle generation with formatting
- **Location:** `run_pipeline.py` - Stage 11
- **Output:** `out/<movie>/en_merged/<movie>.merged.srt`
- **Format:** Standard SRT with timestamps and speaker labels (if diarization enabled)

## Architecture Enhancements

Beyond the base architecture, our implementation adds:

### Pre-Processing (Before VAD)
1. **Filename parsing** - Extract title/year
2. **Era detection** - Load decade-specific lexicons (1950s-2020s)
3. **TMDB enrichment** - Fetch cast/crew metadata
4. **Prompt assembly** - Combine context for better ASR
5. **Bias windowing** - Rolling 45s context windows with term lists

### Post-Processing (After ASR)
8. **Translation refinement** - Two-pass quality improvement (opus-mt/mbart)
9. **NER extraction** - Named entity recognition with spaCy
10. **Canonicalization** - Entity normalization and polish
11. **Video muxing** - Embed subtitles in video file

## Technical Implementation

### VAD Separation (Key Requirement)
```python
# WhisperX loaded with Silero VAD (separate from pyannote)
model = whisperx.load_model(
    'large-v2',
    device='cpu',
    compute_type='int8',
    vad_method='silero',  # Separate VAD model
    download_root=None
)
```

### Why This Matters
- **Architecture compliance:** VAD is explicitly separate from ASR
- **Dependency isolation:** Silero doesn't require pyannote.audio
- **Compatibility:** Works with torch 2.2.1 without conflicts
- **Modularity:** VAD can be swapped (silero, pyannote, or custom)

## Container Architecture

The Docker-first design enforces architectural separation:

```
ASR Container (Silero VAD + WhisperX)
  ├─ Input: Audio file
  ├─ VAD: Silero identifies speech segments
  ├─ ASR: WhisperX transcribes + translates
  └─ Output: Transcripts with word alignments

Diarization Container (Optional, Pyannote)
  ├─ Input: Audio + ASR segments
  ├─ Process: Speaker clustering
  └─ Output: Speaker-labeled segments

NER Container (spaCy)
  ├─ Input: Transcripts
  ├─ Process: Entity extraction
  └─ Output: Annotated transcripts
```

## Verification

Tested with: "Jaane Tu Ya Jaane Na 2006.mp4" (5-minute clip)

**Results:**
- ✅ VAD identified speech segments
- ✅ WhisperX transcribed 10 segments
- ✅ Word-level alignments generated
- ✅ Translation: Hindi → English
- ✅ Output: Structured JSON with timestamps

**Sample Output:**
```json
{
  "start": 264.14,
  "end": 267.505,
  "text": "That's why you guys are singing with your throats slit.",
  "words": [
    {"word": "That's", "start": 264.14, "end": 265.021, "score": 0.624},
    {"word": "why", "start": 265.081, "end": 265.241, "score": 0.264},
    ...
  ]
}
```

## Compliance Summary

| Architecture Component | Required | Implemented | Status |
|------------------------|----------|-------------|--------|
| Audio File Input | ✅ | ✅ | Complete |
| Separate VAD Model | ✅ | ✅ Silero | Complete |
| Speech Segments | ✅ | ✅ Timestamps | Complete |
| WhisperX ASR | ✅ | ✅ large-v2 | Complete |
| Word Alignments | ✅ | ✅ Per-word | Complete |
| Speaker Diarization | Optional | ✅ Optional | Complete |
| Structured Transcript | ✅ | ✅ JSON+SRT | Complete |

**Conclusion:** Implementation is **100% compliant** with workflow-arch.txt and includes significant enhancements while maintaining architectural integrity.

---

**Last Updated:** 2025-10-28  
**Pipeline Version:** 1.0.0  
**Architecture:** Verified Compliant ✅
