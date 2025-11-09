# Architecture Overview

**System design and component organization for CP-WhisperX-App**

---

## System Design

CP-WhisperX-App is a **job-based pipeline system** for generating context-aware subtitles from Bollywood movies with mixed Hindi-English dialogue.

### Design Principles

1. **Job-Based Processing**: Each movie is a separate job with unique ID and configuration
2. **Resume Capability**: Jobs can be resumed from any completed stage
3. **Platform-Aware**: Automatically uses best execution mode for each platform
4. **Modular Stages**: 12 independent stages connected via manifest
5. **ML-Optimized**: Leverages GPU acceleration where available

---

## Execution Modes

### Native Mode (macOS & Windows)

**When**: GPU available (MPS or CUDA)

**How it works**:
```
User
  ↓
run_pipeline.sh/ps1
  ↓
Activates .bollyenv
Exports TORCH_HOME, HF_HOME
  ↓
scripts/pipeline.py (orchestrator)
  ↓
Python scripts in docker/* (native execution)
  ↓
Output files
```

**Advantages**:
- ✅ Direct GPU access (MPS/CUDA)
- ✅ Faster model loading
- ✅ Lower memory overhead
- ✅ Easier debugging
- ✅ Native file system access

**Platforms**:
- macOS with Apple Silicon (M1/M2/M3) - MPS
- Windows with NVIDIA GPU - CUDA
- Windows/macOS without GPU - CPU (fallback)

### Docker Mode (Linux)

**When**: Linux systems (preferred for consistency)

**How it works**:
```
User
  ↓
run_pipeline.sh
  ↓
scripts/pipeline.py (orchestrator)
  ↓
docker compose run <stage>
  ↓
Container with Python + dependencies
  ↓
Output files (via bind mount)
```

**Advantages**:
- ✅ Consistent environment
- ✅ Isolation from system
- ✅ GPU pass-through (nvidia-docker)
- ✅ Easy deployment

**Platforms**:
- Linux (Ubuntu, Debian, etc.)
- Can work on macOS/Windows (slower)

---

## Component Overview

### 1. Bootstrap Layer

**Files**: `scripts/bootstrap.sh`, `scripts/bootstrap.ps1`

**Purpose**: One-time environment setup

**Functions**:
- Create virtual environment (`.bollyenv`)
- Install dependencies (PyTorch, WhisperX, etc.)
- Detect hardware capabilities
- Create cache directories (`.cache/torch`, `.cache/huggingface`)
- Pre-download models (optional)

**Output**: `out/hardware_cache.json`

### 2. Job Preparation Layer

**Files**: `prepare-job.sh`, `scripts/prepare-job.py`

**Purpose**: Create and configure job from input media

**Functions**:
- Parse filename (title, year)
- Generate unique job ID (YYYYMMDD-NNNN)
- Fetch TMDB metadata (optional)
- Read hardware capabilities from cache
- Generate job configuration (`.JOB_ID.env`)
- Create job directory structure
- Initialize manifest

**Output**: Job directory in `out/YYYY/MM/DD/USER_ID/JOB_ID/`

### 3. Pipeline Orchestration Layer

**Files**: `run_pipeline.sh`, `resume-pipeline.sh`, `scripts/pipeline.py`

**Purpose**: Execute pipeline stages in sequence

**Functions**:
- Load job configuration
- Check manifest for resume capability
- Execute stages (native or Docker)
- Update manifest with progress
- Handle failures and retries
- Log all operations

**Output**: Updated manifest, stage artifacts, logs

### 4. Stage Execution Layer

**Files**: `docker/*/stage.py`, `scripts/*_integration.py`

**Purpose**: Process media through ML/utility stages

**Stages**:
1. **demux** - Extract audio with FFmpeg
2. **tmdb** - Fetch movie metadata
3. **pre_ner** - Extract entities from metadata
4. **silero_vad** - Fast voice activity detection
5. **pyannote_vad** - Refined VAD boundaries
6. **diarization** - Speaker identification
7. **asr** - WhisperX transcription + translation
8. **second_pass_translation** - Improve translation quality
9. **lyrics_detection** - Detect song sequences
10. **post_ner** - Correct entities in transcript
11. **subtitle_gen** - Generate .srt files
12. **mux** - Embed subtitles in video

**Output**: Stage-specific artifacts in job directory

### 5. Shared Utilities Layer

**Files**: `shared/*.py`

**Components**:
- `config.py` - Configuration loading (Pydantic)
- `logger.py` - Structured logging
- `manifest.py` - Job manifest management
- `hardware_detection.py` - GPU/CPU detection
- `utils.py` - Common utilities

---

## Data Flow

### Job Creation Flow

```
Input Media (in/movie.mp4)
    ↓
prepare-job.sh
    ↓
Parse filename → "Movie Title (2001)"
    ↓
Fetch TMDB metadata (optional)
    ↓
Read hardware_cache.json
    ↓
Generate job configuration
    ├── Job ID: 20251108-0001
    ├── Device: mps
    ├── Model: large-v3
    └── Settings: optimized for GPU
    ↓
Create directory structure
    ├── out/2025/11/08/1/20251108-0001/
    ├── .20251108-0001.env
    ├── job.json
    └── manifest.json (initialized)
    ↓
✓ Job ready for pipeline
```

### Pipeline Execution Flow

```
run_pipeline.sh --job 20251108-0001
    ↓
Load job configuration (.env file)
    ↓
Check manifest for resume point
    ↓
Execute stages sequentially:
    │
    ├─ Stage 1: demux
    │   ├── Input: in/movie.mp4
    │   ├── Process: FFmpeg audio extraction
    │   ├── Output: audio/audio.wav
    │   └── Manifest: mark completed
    │
    ├─ Stage 2: tmdb
    │   ├── Input: job metadata
    │   ├── Process: TMDB API fetch
    │   ├── Output: metadata/tmdb_data.json
    │   └── Manifest: mark completed
    │
    ├─ Stage 3: pre_ner
    │   ├── Input: metadata/tmdb_data.json
    │   ├── Process: spaCy NER extraction
    │   ├── Output: entities/pre_ner.json, prompts/
    │   └── Manifest: mark completed
    │
    ├─ Stage 4-6: VAD + Diarization
    │   ├── Input: audio.wav
    │   ├── Process: ML models (PyTorch)
    │   ├── Output: vad/, diarization/
    │   └── Manifest: mark completed
    │
    ├─ Stage 7: asr (WhisperX)
    │   ├── Input: audio.wav, vad, prompts
    │   ├── Process: Whisper large-v3 (MPS/CUDA)
    │   ├── Output: asr/transcript.json
    │   └── Manifest: mark completed
    │
    ├─ Stage 8-9: Translation + Lyrics
    │   ├── Input: asr/transcript.json
    │   ├── Process: ML models
    │   ├── Output: translation/, lyrics/
    │   └── Manifest: mark completed
    │
    └─ Stage 10-12: Post-processing
        ├── Input: transcript, entities
        ├── Process: Entity correction, SRT gen, mux
        ├── Output: subtitles/subtitles.srt, final_output.mp4
        └── Manifest: mark completed
    ↓
✓ Pipeline complete
```

### Resume Flow

```
resume-pipeline.sh 20251108-0001
    ↓
Load manifest.json
    ↓
Find last completed stage
    │
    ├─ Example:
    │   ✓ demux (completed)
    │   ✓ tmdb (completed)
    │   ✓ pre_ner (completed)
    │   ✓ silero_vad (completed)
    │   ✓ pyannote_vad (completed)
    │   ✓ diarization (completed)
    │   ✗ asr (failed) ← Resume from here
    │   ○ second_pass_translation (pending)
    │   ○ lyrics_detection (pending)
    │   ...
    ↓
Skip completed stages
    ↓
Start from first failed/pending stage
    ↓
Continue pipeline execution
```

---

## Directory Structure

### Project Root

```
cp-whisperx-app/
├── in/                          # Input media files
├── out/                         # Job outputs (organized by date)
│   ├── hardware_cache.json      # Hardware detection cache
│   └── YYYY/MM/DD/USER_ID/JOB_ID/
├── scripts/                     # Python scripts
│   ├── bootstrap.sh/ps1         # Environment setup
│   ├── pipeline.py              # Orchestrator
│   ├── prepare-job.py           # Job creator
│   └── *_integration.py         # ML integrations
├── docker/                      # Stage implementations
│   ├── demux/
│   ├── tmdb/
│   ├── asr/
│   └── ...
├── shared/                      # Shared utilities
│   ├── config.py                # Configuration loader
│   ├── logger.py                # Logging
│   ├── manifest.py              # Manifest management
│   └── hardware_detection.py   # Hardware detection
├── config/                      # Configuration files
│   └── secrets.json             # API keys (user-created)
├── .cache/                      # Model cache
│   ├── torch/                   # PyTorch models
│   └── huggingface/             # HuggingFace models
├── .bollyenv/                   # Virtual environment
├── docs/                        # Documentation
├── README.md                    # Project overview
└── *.sh, *.ps1                  # Entry point scripts
```

### Job Directory

```
out/2025/11/08/1/20251108-0001/
├── .20251108-0001.env           # Job configuration
├── job.json                     # Job metadata
├── manifest.json                # Stage tracking
├── audio/                       # Stage 1 output
│   └── audio.wav
├── metadata/                    # Stage 2 output
│   └── tmdb_data.json
├── prompts/                     # Stage 3 output
│   └── ner_enhanced_prompt.txt
├── entities/                    # Stage 3 & 10 output
│   ├── pre_ner.json
│   └── post_ner.json
├── vad/                         # Stage 4-5 output
│   ├── silero_segments.json
│   └── pyannote_segments.json
├── diarization/                 # Stage 6 output
│   └── speaker_segments.json
├── asr/                         # Stage 7 output
│   └── transcript.json
├── translation/                 # Stage 8 output
│   └── refined_transcript.json
├── lyrics/                      # Stage 9 output
│   └── lyrics_segments.json
├── subtitles/                   # Stage 11 output
│   └── subtitles.srt
├── logs/                        # All stage logs
│   ├── 00_orchestrator_*.log
│   ├── 01_demux_*.log
│   ├── 02_tmdb_*.log
│   └── ...
└── final_output.mp4             # Stage 12 output (optional)
```

---

## Configuration System

### Configuration Hierarchy

```
1. Bootstrap Detection
   ↓ hardware_cache.json
   
2. Job Preparation
   ↓ .JOB_ID.env (from hardware cache + user input)
   
3. Pipeline Execution
   ↓ Python config (from .env file)
   
4. Stage Execution
   ↓ Stage-specific parameters (from config)
```

### Configuration Files

**hardware_cache.json**
- CPU/GPU detection results
- Recommended settings
- Valid for 1 hour
- Generated by bootstrap

**.JOB_ID.env**
- Job-specific settings
- Device configuration (DEVICE=mps)
- Model selection (WHISPER_MODEL=large-v3)
- All stage parameters
- Generated by prepare-job

**secrets.json**
- API keys (TMDB, HuggingFace)
- User-created
- Not committed to git

---

## Manifest System

### Manifest Structure

```json
{
  "job_id": "20251108-0001",
  "created_at": "2025-11-08T15:43:28Z",
  "stages": {
    "demux": {
      "status": "completed",
      "started_at": "2025-11-08T15:45:00Z",
      "completed_at": "2025-11-08T15:55:00Z",
      "duration_seconds": 600
    },
    "asr": {
      "status": "failed",
      "started_at": "2025-11-08T17:00:00Z",
      "failed_at": "2025-11-08T17:05:00Z",
      "error": "OSError: [Errno 30] Read-only file system"
    }
  }
}
```

### Status Values

- `pending` - Not started yet
- `running` - Currently executing
- `completed` - Finished successfully
- `failed` - Encountered error
- `skipped` - Skipped (optional stage)

### Resume Logic

1. Load manifest
2. Find stages with `completed` status
3. Find first `failed` or `pending` stage
4. Start execution from that stage
5. Update manifest as stages complete

---

## ML Model Architecture

### Model Loading

```
Bootstrap
    ↓
Download models to .cache/
    ├── .cache/torch/
    │   ├── whisper/large-v3/
    │   └── silero-vad/
    └── .cache/huggingface/
        ├── pyannote/
        └── spacy/
    ↓
Pipeline Execution
    ↓
Set environment variables
    ├── TORCH_HOME=.cache/torch
    └── HF_HOME=.cache/huggingface
    ↓
Stage loads model
    ├── Check cache first
    ├── Download if missing
    └── Load to GPU/CPU
```

### Model Selection

**Whisper Models** (ASR):
- `large-v3` - Best quality, needs 10GB VRAM
- `large-v2` - Good quality, needs 8GB VRAM
- `medium` - Balanced, needs 5GB VRAM
- `small` - Fast, needs 2GB VRAM
- `base` - Fastest, CPU-friendly

**PyAnnote Models** (VAD/Diarization):
- `voice-activity-detection` - Required
- `speaker-diarization-3.1` - Required
- Both need ~2GB VRAM each

**spaCy Models** (NER):
- `en_core_web_trf` - Transformer-based, best quality
- `en_core_web_lg` - Large, good quality
- `en_core_web_sm` - Small, fastest

---

## Performance Characteristics

### Processing Time (2.5-hour movie)

| Hardware | Mode | Total Time | Speedup |
|----------|------|------------|---------|
| M1 Pro (10GB) | Native MPS | ~10 hours | 15x |
| RTX 3090 (24GB) | Native CUDA | ~6 hours | 25x |
| RTX 3060 (12GB) | Native CUDA | ~12 hours | 12x |
| CPU (16-core) | Native CPU | ~150 hours | 1x |

### Memory Requirements

| Stage | RAM | VRAM (GPU) |
|-------|-----|------------|
| demux | 2GB | - |
| VAD | 4GB | 2GB |
| diarization | 8GB | 4GB |
| asr (large-v3) | 16GB | 10GB |
| translation | 8GB | 4GB |
| Other stages | <4GB | - |

### Disk Requirements

| Component | Size |
|-----------|------|
| Dependencies | 5-8 GB |
| Models (cached) | 5-10 GB |
| Job output | 1-3 GB per job |
| **Total** | **15-20 GB + jobs** |

---

## Security Considerations

### API Keys
- Stored in `config/secrets.json`
- Not committed to git
- Read-only by pipeline
- Never logged or exposed

### File Permissions
- Cache directories: 755
- Output directories: 755
- Config files: 644
- Secrets: 600 (recommended)

### Network Access
- TMDB API (movie metadata)
- HuggingFace Hub (model downloads)
- PyPI (package installation)
- No outbound data transmission

---

## Error Handling

### Stage Failure
1. Log error details
2. Update manifest (status=failed)
3. Retry once (configurable)
4. Exit pipeline if retry fails
5. User can resume after fixing issue

### System Failure
1. Pipeline exits gracefully
2. Manifest saved with last state
3. Logs written to disk
4. Resume recovers from last checkpoint

### Resource Exhaustion
1. Out of memory → Reduce batch size
2. Out of disk → Clean cache
3. GPU out of memory → Fallback to CPU
4. Network timeout → Retry with backoff

---

## Related Documentation

- [Workflow Guide](WORKFLOW.md) - Detailed stage descriptions
- [Configuration Guide](CONFIGURATION.md) - Settings reference
- [Bootstrap Guide](BOOTSTRAP.md) - Environment setup
- [Running Pipeline](RUNNING.md) - Execution guide

---

Return to [Documentation Index](INDEX.md)
