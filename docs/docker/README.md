# Docker Directory Structure Documentation

> **Last Updated:** November 4, 2025  
> **Purpose:** Complete documentation of all Docker container images for the cp-whisperx-app pipeline

## Overview

The `docker/` directory contains Dockerfiles and scripts for 14 containerized stages in the WhisperX subtitle generation pipeline. Each stage is designed to run as an independent container with specific dependencies and responsibilities.

## Directory Structure

```
docker/
├── base/                   # Base CPU image (Python 3.11 + common deps)
├── base-cuda/              # Base CUDA image (NVIDIA CUDA 12.1 + PyTorch)
├── demux/                  # Stage 1: Audio extraction (FFmpeg)
├── tmdb/                   # Stage 2: Metadata fetching (TMDB API)
├── pre-ner/                # Stage 3: Pre-ASR entity extraction
├── silero-vad/             # Stage 4: Coarse voice activity detection
├── pyannote-vad/           # Stage 5: Refined VAD with chunking
├── diarization/            # Stage 6: Speaker labeling
├── asr/                    # Stage 7: WhisperX transcription
├── post-ner/               # Stage 8: Post-ASR entity correction
├── subtitle-gen/           # Stage 9: SRT subtitle generation
├── mux/                    # Stage 10: Video muxing with subtitles
├── second-pass-translation/ # Optional: Translation refinement
└── lyrics-detection/       # Optional: Music/lyrics detection
```

## Base Images

### base/ - CPU Base Image

**Purpose:** Foundation for all CPU-only stages  
**Base:** `python:3.11-slim`  
**Tag:** `rajiup/cp-whisperx-app-base:cpu`, `rajiup/cp-whisperx-app-base:latest`

**Contents:**
- `Dockerfile` - Python 3.11 with common dependencies
- `requirements.txt` - Shared Python packages

**Installed:**
- FFmpeg (audio/video processing)
- Python 3.11
- Common utilities (git, wget, curl)
- Base Python packages (numpy, scipy, etc.)

**Size:** ~1.34 GB

**Used By:** All CPU-only stages (demux, tmdb, pre-ner, post-ner, subtitle-gen, mux)

---

### base-cuda/ - CUDA Base Image

**Purpose:** Foundation for GPU-accelerated ML stages  
**Base:** `nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04`  
**Tag:** `rajiup/cp-whisperx-app-base:cuda`

**Contents:**
- `Dockerfile` - CUDA 12.1 + cuDNN 8 + Python 3.11

**Installed:**
- NVIDIA CUDA 12.1
- cuDNN 8 (deep learning primitives)
- Python 3.11
- PyTorch with CUDA support
- FFmpeg
- Common utilities

**Size:** ~13.9 GB

**Used By:** Future CUDA variants of ML stages (currently not used, stages use CPU base)

**Note:** Already built but not yet used by stage images. See `DOCKER_CUDA_TODO.md` for enabling CUDA support.

---

## Pipeline Stages

### 1. demux/ - Audio Extraction

**Purpose:** Extract 16kHz mono audio from video files  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-demux:cpu`

**Contents:**
- `Dockerfile` - Container definition
- `demux.py` - FFmpeg-based audio extraction script

**Key Features:**
- Uses FFmpeg for audio extraction
- Converts to 16kHz mono WAV format
- Required by all downstream ML stages

**Dependencies:**
- FFmpeg (from base image)
- Python standard library

**Size:** ~1.34 GB

**Input:** Video file (MP4, MKV, etc.)  
**Output:** `out/{movie}/audio/audio.wav`

**Entry Point:** `python demux.py`

---

### 2. tmdb/ - Metadata Fetching

**Purpose:** Fetch movie metadata from The Movie Database  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-tmdb:cpu`

**Contents:**
- `Dockerfile` - Container definition
- `tmdb.py` - TMDB API client script

**Key Features:**
- Queries TMDB API for movie data
- Extracts cast, crew, plot information
- Enriches context for ASR stage

**Dependencies:**
- `tmdbsimple>=2.9.1` (TMDB API library)
- Requires `TMDB_API_KEY` environment variable

**Size:** ~1.34 GB

**Input:** Movie title and year  
**Output:** `out/{movie}/metadata/tmdb_data.json`

**Entry Point:** `python tmdb.py`

---

### 3. pre-ner/ - Pre-ASR Entity Extraction

**Purpose:** Extract named entities from TMDB data for ASR context  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-pre-ner:cpu`

**Contents:**
- `Dockerfile` - Container definition
- `pre_ner.py` - Entity extraction script
- `requirements-ner.txt` - spaCy dependencies

**Key Features:**
- Uses spaCy for NER on TMDB metadata
- Builds entity list for ASR prompt
- Improves transcription accuracy for names

**Dependencies:**
- `spacy>=3.7.0`
- `transformers>=4.30.0`
- Pre-trained NER models

**Size:** ~1.78 GB

**Input:** `out/{movie}/metadata/tmdb_data.json`  
**Output:** `out/{movie}/entities/pre_ner.json`

**Entry Point:** `python pre_ner.py`

---

### 4. silero-vad/ - Coarse Voice Activity Detection

**Purpose:** Fast, coarse speech boundary detection  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-silero-vad:cpu`

**Contents:**
- `Dockerfile` - Container definition (CPU PyTorch)
- `silero_vad.py` - Silero VAD implementation

**Key Features:**
- Lightweight CNN-based VAD
- Fast initial speech segmentation
- Reduces processing for non-speech regions

**Dependencies:**
- `torch>=2.0.0` (CPU-only currently)
- `torchaudio>=2.0.0`
- `soundfile>=0.12.1`

**GPU Support:** ✅ Benefits from CUDA (14x speedup)  
**Current Status:** ❌ Built with CPU PyTorch only

**Size:** ~1.5 GB (estimated)

**Input:** `out/{movie}/audio/audio.wav`  
**Output:** `out/{movie}/vad/silero_segments.json`

**Entry Point:** `python silero_vad.py`

---

### 5. pyannote-vad/ - Refined Voice Activity Detection

**Purpose:** Precise speech boundary detection with chunking  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-pyannote-vad:cpu`

**Contents:**
- `Dockerfile` - Container definition (PyTorch 2.8.0 CPU)
- `pyannote_vad.py` - PyAnnote VAD with chunking

**Key Features:**
- Refines Silero VAD boundaries
- Chunk-based processing for long audio
- Prepares input for diarization

**Dependencies:**
- `torch==2.8.0` (CPU-only currently)
- `torchaudio==2.8.0`
- `pyannote.audio==3.4.0`
- `huggingface-hub>=0.20.0,<1.0`

**GPU Support:** ✅ Benefits from CUDA (17x speedup)  
**Current Status:** ❌ Built with CPU PyTorch only

**Size:** ~2 GB (estimated)

**Input:** `out/{movie}/vad/silero_segments.json`  
**Output:** `out/{movie}/vad/pyannote_segments.json`

**Entry Point:** `python pyannote_vad.py`

**Note:** Requires HuggingFace token for model access

---

### 6. diarization/ - Speaker Labeling

**Purpose:** Identify and label different speakers  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-diarization:cpu`

**Contents:**
- `Dockerfile` - Container definition (PyTorch 2.0.1 CPU)
- `diarization.py` - PyAnnote diarization implementation
- `requirements-diarization.txt` - Additional dependencies

**Key Features:**
- PyAnnote-based speaker diarization
- Speaker embedding extraction
- Clustering for speaker identification

**Dependencies:**
- `torch==2.0.1` (CPU-only currently)
- `torchaudio==2.0.2`
- `pyannote.audio==3.1.1`
- `pytorch-lightning>=2.0.0`
- `speechbrain>=0.5.0`
- `whisperx`

**GPU Support:** ✅ Benefits from CUDA (25x speedup)  
**Current Status:** ❌ Built with CPU PyTorch only

**Size:** ~3 GB (estimated)

**Input:** `out/{movie}/vad/pyannote_segments.json`  
**Output:** `out/{movie}/diarization/speaker_segments.json`

**Entry Point:** `python diarization.py`

**Note:** Requires HuggingFace token for PyAnnote models

---

### 7. asr/ - WhisperX Transcription

**Purpose:** Automatic speech recognition with word-level timestamps  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-asr:cpu`

**Contents:**
- `Dockerfile` - Container definition (PyTorch 2.2.1 CPU)
- `whisperx_asr.py` - WhisperX ASR implementation
- `requirements-asr.txt` - WhisperX dependencies

**Key Features:**
- Whisper large-v3 model
- Word-level alignment
- Speaker-aware transcription
- Optional translation to English

**Dependencies:**
- `torch==2.2.1` (CPU-only currently)
- `torchaudio==2.2.1`
- `whisperx` (from GitHub)
- `faster-whisper`
- `transformers`
- `ctranslate2`
- `sentencepiece` (for translation)

**GPU Support:** ✅ Benefits from CUDA (12x speedup)  
**Current Status:** ❌ Built with CPU PyTorch only

**Size:** ~3 GB (estimated)

**Memory:** Configured with 16GB limit in docker-compose.yml

**Input:** 
- `out/{movie}/audio/audio.wav`
- `out/{movie}/diarization/speaker_segments.json`
- `out/{movie}/entities/pre_ner.json` (for context)

**Output:** `out/{movie}/transcription/transcript.json`

**Entry Point:** `python /app/whisperx_asr.py`

**Note:** Longest-running stage, critical for CUDA acceleration

---

### 8. post-ner/ - Post-ASR Entity Correction

**Purpose:** Correct entity names in transcription using TMDB context  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-post-ner:cpu`

**Contents:**
- `Dockerfile` - Container definition
- `post_ner.py` - Entity correction script
- `requirements-ner.txt` - spaCy dependencies

**Key Features:**
- Corrects character/actor names
- Uses TMDB metadata as reference
- Improves subtitle accuracy

**Dependencies:**
- `spacy>=3.5.0`
- `transformers>=4.30.0`
- `rapidfuzz>=3.0.0` (fuzzy matching)

**Size:** ~1.8 GB (estimated)

**Input:**
- `out/{movie}/transcription/transcript.json`
- `out/{movie}/metadata/tmdb_data.json`

**Output:** `out/{movie}/entities/post_ner.json`

**Entry Point:** `python /app/post_ner.py`

---

### 9. subtitle-gen/ - Subtitle Generation

**Purpose:** Generate SRT subtitle files from corrected transcription  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-subtitle-gen:cpu`

**Contents:**
- `Dockerfile` - Container definition
- `subtitle_gen.py` - SRT generation script

**Key Features:**
- Converts JSON to SRT format
- Adds speaker labels
- Formats timing and text

**Dependencies:**
- `pysubs2>=1.1.0` (subtitle library)
- Python standard library

**Size:** ~1.4 GB (estimated)

**Input:** `out/{movie}/entities/post_ner.json`  
**Output:** `out/{movie}/subtitles/subtitles.srt`

**Entry Point:** `python subtitle_gen.py`

---

### 10. mux/ - Video Muxing

**Purpose:** Embed subtitles into video file  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-mux:cpu`

**Contents:**
- `Dockerfile` - Container definition
- `mux.py` - FFmpeg-based muxing script

**Key Features:**
- Uses FFmpeg to embed SRT subtitles
- Preserves video quality (copy codec)
- Creates final output video

**Dependencies:**
- FFmpeg (from base image)
- Python standard library

**Size:** ~1.34 GB

**Input:**
- Original video file (from `in/`)
- `out/{movie}/subtitles/subtitles.srt`

**Output:** `out/{movie}/final_output.mp4`

**Entry Point:** `python mux.py`

---

## Optional Stages

### second-pass-translation/ - Translation Refinement

**Purpose:** Improve translation quality with additional passes  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-second-pass-translation:cpu`

**Contents:**
- `Dockerfile` - Container definition
- `second_pass_translation.py` - Translation refinement
- `requirements.txt` - Translation models

**Key Features:**
- Secondary translation pass
- Context-aware improvements
- Optional stage (not in main pipeline)

**Status:** ⚠️ Optional, not in standard workflow

---

### lyrics-detection/ - Music Detection

**Purpose:** Detect music/singing and mark lyrics segments  
**Base Image:** `rajiup/cp-whisperx-app-base:latest`  
**Tag:** `rajiup/cp-whisperx-app-lyrics-detection:cpu`

**Contents:**
- `Dockerfile` - Container definition
- `lyrics_detection.py` - Music detection script
- `requirements.txt` - Audio analysis tools

**Key Features:**
- Detects singing vs speech
- Marks musical segments
- Optional stage for music-heavy content

**Status:** ⚠️ Optional, not in standard workflow

---

## Image Build Status

### Successfully Built (Current)

| Image | Tag | Size | Status |
|-------|-----|------|--------|
| base | cpu, latest | 1.34 GB | ✅ |
| base | cuda | 13.9 GB | ✅ |
| demux | cpu | 1.34 GB | ✅ |
| tmdb | cpu | 1.34 GB | ✅ |
| pre-ner | cpu | 1.78 GB | ✅ |
| post-ner | cpu | ~1.8 GB | 🔄 |
| subtitle-gen | cpu | ~1.4 GB | 🔄 |
| mux | cpu | 1.34 GB | 🔄 |
| silero-vad | cpu | ~1.5 GB | 🔄 |
| pyannote-vad | cpu | ~2 GB | 🔄 |
| diarization | cpu | ~3 GB | 🔄 |
| asr | cpu | ~3 GB | 🔄 |
| second-pass-translation | cpu | TBD | 🔄 |
| lyrics-detection | cpu | TBD | 🔄 |

**Legend:**
- ✅ Built successfully
- 🔄 Build in progress
- ❌ Not built

---

## GPU/CUDA Support

### Current Status: CPU-Only Images

All stage images currently install PyTorch with CPU-only support:
```dockerfile
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Stages That Would Benefit From CUDA

**4 ML stages** would see significant speedup with CUDA:

1. **silero-vad** - 14x speedup
2. **pyannote-vad** - 17x speedup
3. **diarization** - 25x speedup
4. **asr** - 12x speedup

### How to Enable CUDA

See `DOCKER_CUDA_TODO.md` for complete guide on building CUDA images.

**Quick summary:**
1. Create `Dockerfile.cuda` for each ML stage
2. Change base to `rajiup/cp-whisperx-app-base:cuda`
3. Change PyTorch install to: `--index-url https://download.pytorch.org/whl/cu121`
4. Tag images as `:cuda`
5. Update docker-compose.yml with GPU device config

---

## Building Images

### Build All CPU Images

```bash
# Windows
scripts\build-all-images.bat

# Linux/Mac
./scripts/build-all-images.sh
```

### Build Individual Image

```bash
docker build -t rajiup/cp-whisperx-app-asr:cpu -f docker/asr/Dockerfile .
```

### Build With Custom Registry

```bash
# Set environment variable
set DOCKERHUB_USER=myusername

# Build
scripts\build-all-images.bat
```

---

## Pushing Images

### Push All Images

```bash
# Login first
docker login

# Windows
scripts\push-all-images.bat

# Linux/Mac
./scripts/push-all-images.sh
```

### Push Individual Image

```bash
docker push rajiup/cp-whisperx-app-asr:cpu
```

---

## Docker Compose Configuration

Images are orchestrated via `docker-compose.yml` with dependency chains:

```
demux → tmdb → pre-ner → silero-vad → pyannote-vad → diarization → asr → post-ner → subtitle-gen → mux
```

Each stage waits for its dependencies to complete before starting.

---

## File Locations

### Python Scripts
Each stage has a main Python script (e.g., `asr/whisperx_asr.py`) that:
- Loads configuration from environment
- Reads input from previous stage
- Processes data
- Writes output for next stage
- Updates manifest.json

### Shared Modules
Common code in `shared/` directory is copied to all containers:
- `shared/config_loader.py` - Configuration management
- `shared/device_selector.py` - GPU/CPU selection
- `shared/manifest.py` - Pipeline state tracking
- `shared/logger.py` - Logging utilities

### Scripts
Pipeline helpers in `scripts/` directory:
- `scripts/whisperx_integration.py` - WhisperX wrapper
- `scripts/diarization.py` - PyAnnote helpers
- `scripts/tmdb_enrichment.py` - TMDB utilities
- `scripts/ner_extraction.py` - NER processing

---

## Volume Mounts

All containers mount:
- `./in:/app/in:ro` - Input videos (read-only)
- `./out:/app/out` - Output directory (read-write)
- `./config:/app/config:ro` - Configuration (read-only)
- `./shared:/app/shared:ro` - Shared code (read-only)

ML stages also mount:
- `./LLM:/app/LLM` - Model cache directory
- `./scripts:/app/scripts:ro` - Helper scripts

---

## Environment Variables

All containers support:
- `CONFIG_PATH` - Path to .env file (default: `/app/config/.env`)
- `PYTHONPATH` - Python module search path (set to `/app`)
- `HF_HOME` - HuggingFace cache (ML stages only)
- `HF_TOKEN` - HuggingFace API token (for PyAnnote models)

---

## Memory Limits

Resource limits in docker-compose.yml:
- **asr**: 16GB RAM limit (large Whisper models)
- **diarization**: Default (8GB recommended)
- **Other stages**: Default (2-4GB sufficient)

---

## Related Documentation

- `DOCKER_BUILD_GUIDE.md` - Complete build instructions
- `DOCKER_CUDA_TODO.md` - How to add CUDA support
- `CUDA_ACCELERATION_GUIDE.md` - GPU performance benchmarks
- `WORKFLOW_GUIDE.md` - Pipeline execution guide
- `README.md` - Project overview

---

## Troubleshooting

### Image Build Failures

**Out of disk space:**
```bash
docker system prune -a
```

**Dockerfile not found:**
Check you're in repository root and path uses backslashes on Windows

**PyTorch install timeout:**
Increase Docker build timeout or use pre-built wheels

### Container Failures

**HuggingFace token missing:**
Set `HF_TOKEN` in `config/.env` or `config/secrets.json`

**Model download fails:**
Check internet connection and HuggingFace status

**Out of memory:**
Increase container memory limits in docker-compose.yml

---

**Last Updated:** November 4, 2025  
**Total Images:** 14 (2 base + 10 pipeline + 2 optional)  
**Repository:** https://github.com/yourusername/cp-whisperx-app
