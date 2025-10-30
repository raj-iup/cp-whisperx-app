# ✅ Pipeline Stage Order - VERIFIED

**Date:** October 29, 2025  
**Status:** ✅ **100% COMPLIANT WITH workflow-arch.txt**

---

## workflow-arch.txt Specified Order

```
1. FFmpeg Demux
2. TMDB Metadata Fetch
3. Pre-ASR NER
4. Silero VAD
5. PyAnnote VAD
6. PyAnnote Diarization  ← MANDATORY, BEFORE ASR
7. WhisperX ASR
8. Post-ASR NER
9. Subtitle Generation
10. FFmpeg Mux
```

---

## run_pipeline_arch.py Implementation Order

```python
# Line 153: STAGE 1 - Demux
run_docker_stage("demux", [str(input_path)], logger)

# Line 174: STAGE 2 - TMDB
enrich_from_tmdb(parsed.title, parsed.year, config)

# Line 220: STAGE 3 - Pre-ASR NER
run_docker_stage("pre-ner", [str(movie_dir)], logger)

# Line 251: STAGE 4 - Silero VAD
run_docker_stage("silero-vad", [str(movie_dir)], logger)

# Line 273: STAGE 5 - PyAnnote VAD
run_docker_stage("pyannote-vad", [str(movie_dir)], logger)

# Line 302: STAGE 6 - PyAnnote Diarization (MANDATORY)
run_docker_stage("diarization", [f"/app/out/{title}"], logger)

# Line 328: STAGE 7 - WhisperX ASR
run_docker_stage("asr", [f"/app/out/{title}"], logger)

# Line 352: STAGE 8 - Post-ASR NER
run_docker_stage("post-ner", [f"/app/out/{title}"], logger)

# Line 375: STAGE 9 - Subtitle Generation
run_docker_stage("subtitle-gen", [f"/app/out/{title}"], logger)

# Line 404: STAGE 10 - FFmpeg Mux
run_docker_stage("mux", [input, srt, output], logger)
```

---

## Verification Checklist

✅ **Stage 1: Demux** - Correct position  
✅ **Stage 2: TMDB** - Correct position  
✅ **Stage 3: Pre-ASR NER** - Correct position (called "pre-ner")  
✅ **Stage 4: Silero VAD** - Correct position  
✅ **Stage 5: PyAnnote VAD** - Correct position  
✅ **Stage 6: Diarization** - ⚠️ **CRITICAL: BEFORE ASR** ✅  
✅ **Stage 7: ASR** - Correct position (AFTER diarization)  
✅ **Stage 8: Post-ASR NER** - Correct position (called "post-ner")  
✅ **Stage 9: Subtitle-Gen** - Correct position  
✅ **Stage 10: Mux** - Correct position  

---

## Container Name Mapping

| workflow-arch.txt        | Docker Service   | Script File           |
|-------------------------|------------------|-----------------------|
| FFmpeg Demux            | `demux`          | demux.py              |
| TMDB Metadata Fetch     | `tmdb`           | (inline orchestrator) |
| Pre-ASR NER             | `pre-ner`        | pre_ner.py            |
| Silero VAD              | `silero-vad`     | silero_vad.py         |
| PyAnnote VAD            | `pyannote-vad`   | pyannote_vad.py       |
| PyAnnote Diarization    | `diarization`    | diarization.py        |
| WhisperX ASR            | `asr`            | whisperx_asr.py       |
| Post-ASR NER            | `post-ner`       | post_ner.py           |
| Subtitle Generation     | `subtitle-gen`   | subtitle_gen.py       |
| FFmpeg Mux              | `mux`            | mux.py                |

---

## Data Flow Validation

```
in/movie.mp4
  ↓
[demux] → out/Movie/audio/audio.wav
  ↓
[tmdb] → out/Movie/metadata/tmdb.json
  ↓
[pre-ner] → out/Movie/pre_ner/entities.json
  ↓
[silero-vad] → out/Movie/vad/silero_segments.json
  ↓
[pyannote-vad] → out/Movie/vad/pyannote_refined_segments.json
  ↓
[diarization] → out/Movie/diarization/speaker_segments.json
  ↓           (speaker timing information)
  ↓
[asr] → out/Movie/asr/*.asr.json (WITH speaker labels)
  ↓
[post-ner] → out/Movie/post_ner/*.corrected.json
  ↓
[subtitle-gen] → out/Movie/en_merged/*.merged.srt
  ↓
[mux] → out/Movie/Movie_Name.subs.mp4
```

---

## Critical Dependency: Diarization → ASR

**Correct Order (Current):**
```
Stage 6: Diarization runs on audio
  ↓ outputs speaker_segments.json
Stage 7: ASR loads speaker_segments.json
  ↓ assigns speakers to transcript segments
```

**Why This Order Matters:**
1. Diarization identifies WHO speaks and WHEN
2. ASR transcribes WHAT is said
3. ASR uses diarization timing to assign speakers
4. Result: Transcript with speaker labels

---

## Compliance Statement

✅ **All 10 stages implemented in correct order**  
✅ **Stage naming matches workflow-arch.txt intent**  
✅ **Diarization BEFORE ASR (critical requirement)**  
✅ **Data dependencies flow correctly**  
✅ **No stage order violations**  

**Status:** FULLY COMPLIANT

---

**Verified:** October 29, 2025  
**Pipeline:** run_pipeline_arch.py  
**Compliance:** 100%
