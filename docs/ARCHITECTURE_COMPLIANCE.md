# Architecture Compliance Report

**Date:** 2025-10-29  
**Status:** ✅ **FULLY COMPLIANT** with workflow-arch.txt

## New Pipeline Implementation

**File:** `run_pipeline_arch.py`

### Architecture Comparison

| Stage | workflow-arch.txt | run_pipeline_arch.py | Status |
|-------|-------------------|---------------------|--------|
| 1 | FFmpeg Demux (16kHz mono) | ✅ Stage 1: FFmpeg Demux | ✅ |
| 2 | TMDB Metadata Fetch | ✅ Stage 2: TMDB Fetch | ✅ |
| 3 | Pre-ASR NER | ✅ Stage 3: Pre-ASR NER | ✅ |
| 4 | Silero VAD | ✅ Stage 4: Silero VAD | ✅ |
| 5 | PyAnnote VAD | ✅ Stage 5: PyAnnote VAD | ✅ |
| 6 | PyAnnote Diarization (MANDATORY) | ✅ Stage 6: Diarization | ✅ |
| 7 | WhisperX ASR + Alignment | ✅ Stage 7: WhisperX ASR | ✅ |
| 8 | Post-ASR NER | ✅ Stage 8: Post-ASR NER | ✅ |
| 9 | Subtitle Generation (.srt) | ✅ Stage 9: SRT Generation | ✅ |
| 10 | FFmpeg Mux | ✅ Stage 10: FFmpeg Mux | ✅ |

**Compliance:** 10/10 stages ✅

## Key Changes from Old Pipeline

### Old Pipeline (`run_pipeline.py`)
```
Input → Parse → Era → TMDB → Prompts → Bias Windows
  → WhisperX ASR (direct on video!)
  → Diarization (after ASR)
  → NER
  → SRT → Mux
```

**Issues:**
- ❌ No audio demux stage
- ❌ Skipped Silero VAD
- ❌ Skipped PyAnnote VAD  
- ❌ Diarization AFTER ASR (should be before)
- ❌ No Pre-ASR NER
- ❌ No Post-ASR NER distinction

### New Pipeline (`run_pipeline_arch.py`)
```
Input
  → Demux (16kHz mono audio)
  → TMDB Metadata
  → Pre-ASR NER (entities for prompts)
  → Silero VAD (coarse segments)
  → PyAnnote VAD (refined boundaries)
  → Diarization (speaker labels - MANDATORY)
  → WhisperX ASR (with enriched prompts)
  → Post-ASR NER (entity correction)
  → SRT Generation
  → Mux (embed subtitles)
```

**Fixes:**
- ✅ Proper audio extraction (16kHz mono)
- ✅ VAD stages implemented
- ✅ Diarization BEFORE ASR (correct order)
- ✅ Pre-ASR NER feeds entities to prompts
- ✅ Post-ASR NER corrects transcription

## Docker Container Usage

All containerized stages are called via `run_docker_stage()` helper:

| Container | Stage | Purpose |
|-----------|-------|---------|
| `demux` | 1 | Audio extraction |
| `pre-ner` | 3 | Entity extraction |
| `silero-vad` | 4 | Speech segmentation |
| `pyannote-vad` | 5 | Boundary refinement |
| `diarization` | 6 | Speaker labeling |
| `asr` | 7 | Transcription/translation |
| `ner` | 8 | Entity correction (post-ASR) |

Host-side stages: TMDB fetch, SRT generation, FFmpeg mux

## Data Flow

### Stage Outputs

```
out/{Movie}/
├── audio/
│   └── audio.wav                    # Stage 1: Demux
├── pre_ner/
│   └── entities.json                # Stage 3: Pre-ASR NER
├── vad/
│   ├── silero_segments.json         # Stage 4: Silero VAD
│   └── pyannote_refined_segments.json  # Stage 5: PyAnnote VAD
├── diarization/
│   └── diarization.rttm             # Stage 6: Speaker labels
├── asr/
│   └── {movie}.asr.json             # Stage 7: ASR results
├── post_ner/
│   └── corrected_entities.json      # Stage 8: Post-ASR NER
├── en_merged/
│   └── {movie}.merged.srt           # Stage 9: Subtitles
└── {movie}.subs.mp4                 # Stage 10: Final output
```

### Entity Enrichment Flow

```
TMDB cast/crew
    ↓
Pre-ASR NER (extract additional entities)
    ↓
Combined entity list → ASR initial prompt
    ↓
WhisperX transcription (entity-aware)
    ↓
Post-ASR NER (correct misspellings, match to TMDB)
    ↓
Final corrected subtitles
```

## Command Line Usage

### Full Pipeline (Architecture-Compliant)
```bash
python3 ./run_pipeline_arch.py \
  -i "in/Movie.mp4" \
  --infer-tmdb-from-filename
```

### Testing Flags
```bash
# Skip VAD stages (faster testing)
python3 ./run_pipeline_arch.py \
  -i "in/Movie.mp4" \
  --skip-vad

# Skip diarization (not recommended - breaks architecture)
python3 ./run_pipeline_arch.py \
  -i "in/Movie.mp4" \
  --skip-diarization
```

## Configuration

Uses existing `config/.env` for:
- Audio settings (16kHz, mono, WAV)
- Model selection (WhisperX large-v2)
- Device preferences (CPU/CUDA/MPS)
- HuggingFace token
- TMDB API key

## Validation

**Preflight Requirements:**
- ✅ All Docker containers built
- ✅ `config/secrets.json` with tokens
- ✅ FFmpeg installed
- ✅ Input video accessible

**Run preflight:**
```bash
python3 ./preflight.py
```

## Migration Path

### Option 1: Keep Both Pipelines
- `run_pipeline.py` - Old implementation (faster, skips stages)
- `run_pipeline_arch.py` - Architecture-compliant (full workflow)

### Option 2: Replace Old Pipeline
```bash
mv run_pipeline.py run_pipeline_legacy.py
mv run_pipeline_arch.py run_pipeline.py
```

## Architecture Compliance: ✅ VERIFIED

The new pipeline `run_pipeline_arch.py` is **100% compliant** with `workflow-arch.txt`:
- All 10 stages implemented
- Correct stage ordering
- Proper data flow between stages
- Docker containers used appropriately
- Entity enrichment at correct points

**Recommendation:** Use `run_pipeline_arch.py` for production workflows requiring full architecture compliance.

---

**Created:** 2025-10-29  
**Pipeline Version:** 2.0.0-arch-compliant
