# CP-WhisperX Pipeline Rebuild Documentation

**Date**: October 29, 2024  
**Status**: ✅ Completed - Sequential Pipeline Configured

---

## Overview

The pipeline has been rebuilt from scratch following the architecture defined in `arch/workflow-arch.txt`. All 10 stages are now properly wired in sequential order in both `docker-compose.yml` and `pipeline.py`.

---

## Pipeline Architecture

### Sequential Flow (10 Stages)

```
🎬 MP4 Source (Film Scene)
   ↓
1. [FFmpeg Demux] — extract 16kHz mono audio
   ↓
2. [TMDB Metadata Fetch] — movie data: cast, places, plot, keywords
   ↓
3. [Pre-ASR NER] — extract named entities → builds smarter ASR initial prompt
   ↓
4. [Silero VAD] — coarse speech segmentation
   ↓
5. [PyAnnote VAD] — refined contextual boundaries
   ↓
6. [PyAnnote Diarization] — mandatory speaker labeling
   ↓
7. [WhisperX ASR] — English translation + time-aligned transcription
   ↓
8. [Post-ASR NER] — entity correction & enrichment
   ↓
9. [Subtitle Generation] — speaker-prefixed, entity-corrected .srt
   ↓
10. [FFmpeg Mux] — embed English soft-subtitles into MP4
   ↓
🎞️ Final Output: movie_with_en_subs.mp4
```

---

## Stage Details

### Stage 1: Demux
- **Service**: `demux`
- **Script**: `docker/demux/demux.py`
- **Input**: MP4 video file from `in/`
- **Output**: `out/{movie}/audio/audio.wav` (16kHz mono)
- **Timeout**: 600s (10 min)
- **Dependencies**: None

### Stage 2: TMDB
- **Service**: `tmdb`
- **Script**: `docker/tmdb/tmdb.py`
- **Input**: Movie title (parsed from filename), optional year
- **Output**: `out/{movie}/metadata/tmdb_data.json`
- **Timeout**: 120s (2 min)
- **Dependencies**: demux

### Stage 3: Pre-NER
- **Service**: `pre-ner`
- **Script**: `docker/pre-ner/pre_ner.py`
- **Input**: TMDB metadata
- **Output**: `out/{movie}/entities/pre_ner.json`, initial prompt
- **Timeout**: 300s (5 min)
- **Dependencies**: tmdb

### Stage 4: Silero VAD
- **Service**: `silero-vad`
- **Script**: `docker/silero-vad/silero_vad.py`
- **Input**: `audio/audio.wav`
- **Output**: `out/{movie}/vad/silero_segments.json`
- **Timeout**: 1800s (30 min)
- **Dependencies**: pre-ner

### Stage 5: PyAnnote VAD
- **Service**: `pyannote-vad`
- **Script**: `docker/pyannote-vad/pyannote_vad.py`
- **Input**: `audio/audio.wav`, Silero VAD segments
- **Output**: `out/{movie}/vad/pyannote_segments.json`
- **Timeout**: 3600s (60 min)
- **Dependencies**: silero-vad

### Stage 6: Diarization
- **Service**: `diarization`
- **Script**: `docker/diarization/diarization.py`
- **Input**: `audio/audio.wav`, VAD segments
- **Output**: `out/{movie}/diarization/speaker_segments.json`
- **Timeout**: 1800s (30 min)
- **Dependencies**: pyannote-vad

### Stage 7: ASR (WhisperX)
- **Service**: `asr`
- **Script**: `docker/asr/whisperx_asr.py`
- **Input**: `audio/audio.wav`, VAD segments, initial prompt
- **Output**: `out/{movie}/transcription/transcript.json`
- **Timeout**: 3600s (60 min)
- **Dependencies**: diarization
- **Memory**: 10GB limit

### Stage 8: Post-NER
- **Service**: `post-ner`
- **Script**: `docker/post-ner/post_ner.py`
- **Input**: ASR transcript, TMDB metadata
- **Output**: `out/{movie}/entities/post_ner.json`
- **Timeout**: 600s (10 min)
- **Dependencies**: asr

### Stage 9: Subtitle Generation
- **Service**: `subtitle-gen`
- **Script**: `docker/subtitle-gen/subtitle_gen.py`
- **Input**: Corrected transcript, speaker labels
- **Output**: `out/{movie}/subtitles/subtitles.srt`
- **Timeout**: 300s (5 min)
- **Dependencies**: post-ner

### Stage 10: Mux
- **Service**: `mux`
- **Script**: `docker/mux/mux.py`
- **Input**: Original video, subtitles.srt
- **Output**: `out/{movie}/final_output.mp4`
- **Timeout**: 600s (10 min)
- **Dependencies**: subtitle-gen

---

## File Changes Made

### 1. docker-compose.yml
✅ **Added TMDB service** (was missing)
✅ **Updated all dependencies** to follow sequential flow:
- demux → (no deps)
- tmdb → depends_on: demux
- pre-ner → depends_on: tmdb
- silero-vad → depends_on: pre-ner
- pyannote-vad → depends_on: silero-vad
- diarization → depends_on: pyannote-vad
- asr → depends_on: diarization
- post-ner → depends_on: asr
- subtitle-gen → depends_on: post-ner
- mux → depends_on: subtitle-gen

### 2. pipeline.py
✅ **Updated STAGE_DEFINITIONS** to match arch/workflow-arch.txt exactly
✅ **Changed docker-compose reference** from `docker-compose.new.yml` → `docker-compose.yml`
✅ **Fixed stage name** `srt_generation` → `subtitle_gen` for consistency
✅ **Updated timeouts** to be more realistic for each stage
✅ **All stages marked as critical** (pipeline stops on any failure)

---

## Running the Pipeline

### Prerequisites
1. Run preflight checks:
   ```bash
   python preflight.py
   ```

2. Ensure all Docker images are built:
   ```bash
   docker compose build
   ```

### Execute Complete Pipeline
```bash
python pipeline.py in/your-movie.mp4
```

### With Custom Config
```bash
python pipeline.py in/your-movie.mp4 config/custom.yaml
```

---

## Pipeline Features

### ✅ Manifest Tracking
- Each run creates a `manifest.json` in the output directory
- Tracks completion status of each stage
- Supports resume from last successful stage

### ✅ Stage Validation
- Output files verified after each stage
- Pipeline stops if critical stage fails
- Detailed logging for each stage

### ✅ Error Handling
- Timeouts configured per stage
- Failed stages logged with duration
- Critical failures stop pipeline immediately

---

## Output Structure

```
out/{Movie_Title_Year}/
├── audio/
│   └── audio.wav                    # Stage 1: Demux
├── metadata/
│   └── tmdb_data.json              # Stage 2: TMDB
├── entities/
│   ├── pre_ner.json                # Stage 3: Pre-NER
│   └── post_ner.json               # Stage 8: Post-NER
├── vad/
│   ├── silero_segments.json        # Stage 4: Silero VAD
│   └── pyannote_segments.json      # Stage 5: PyAnnote VAD
├── diarization/
│   └── speaker_segments.json       # Stage 6: Diarization
├── transcription/
│   └── transcript.json             # Stage 7: ASR
├── subtitles/
│   └── subtitles.srt               # Stage 9: Subtitle Gen
├── final_output.mp4                # Stage 10: Mux
└── manifest.json                   # Pipeline metadata
```

---

## Next Steps: Parallelization

Once the sequential pipeline is tested and validated, we can explore:

1. **Stage-level parallelization**:
   - Run VAD and NER stages in parallel where data dependencies allow
   - Use async processing for independent operations

2. **Chunk-based parallelization**:
   - Split audio into chunks
   - Process chunks in parallel through VAD/ASR stages
   - Merge results at the end

3. **Multi-file parallelization**:
   - Process multiple movies simultaneously
   - Separate Docker Compose profiles for parallel execution

---

## Docker Image Status

All containers are built and ready:

| Stage | Image | Last Built | Size |
|-------|-------|------------|------|
| demux | rajiup/cp-whisperx-app-demux | 23h ago | 1.3GB |
| tmdb | rajiup/cp-whisperx-app-tmdb | 23h ago | 1.3GB |
| pre-ner | rajiup/cp-whisperx-app-pre-ner | 16h ago | 1.7GB |
| silero-vad | rajiup/cp-whisperx-app-silero-vad | 11h ago | 2.36GB |
| pyannote-vad | rajiup/cp-whisperx-app-pyannote-vad | 7h ago | 2.85GB |
| diarization | rajiup/cp-whisperx-app-diarization | 8h ago | 5GB |
| asr | rajiup/cp-whisperx-app-asr | 16h ago | 4.01GB |
| post-ner | rajiup/cp-whisperx-app-post-ner | 16h ago | 3.61GB |
| subtitle-gen | rajiup/cp-whisperx-app-subtitle-gen | 16h ago | 1.31GB |
| mux | rajiup/cp-whisperx-app-mux | 23h ago | 1.3GB |

**Total Size**: ~25GB

---

## Testing Checklist

- [ ] Test complete pipeline end-to-end
- [ ] Verify each stage output file
- [ ] Test resume capability after failure
- [ ] Validate manifest tracking
- [ ] Check error handling for missing inputs
- [ ] Verify timeout handling
- [ ] Test with different video formats
- [ ] Validate subtitle quality
- [ ] Check final muxed output playback

---

## Known Considerations

1. **ASR Memory**: ASR stage needs 10GB RAM (configured in docker-compose.yml)
2. **HuggingFace Token**: Required for PyAnnote diarization (stored in config/secrets.json)
3. **TMDB API Key**: Required for metadata fetch (stored in config/.env)
4. **GPU Support**: Optional but recommended for faster processing
5. **Timeouts**: May need adjustment based on video length and hardware

---

## Logs

All logs stored in `logs/` directory with timestamps:
- `orchestrator_{timestamp}.log` - Pipeline orchestrator
- Stage-specific logs created by each container

---

**✅ Pipeline is ready for sequential execution testing!**
