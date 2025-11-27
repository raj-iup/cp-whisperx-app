# CP-WhisperX-App Script Analysis
**Analysis Date:** 2025-11-14  
**Purpose:** Identify bootstrap, prepare-job, and pipeline orchestration scripts, categorizing them as relevant or unused

---

## 📊 Executive Summary

### Overall Statistics
- **Total Scripts Found:** 83 files (.sh, .ps1, .py)
- **Bootstrap Scripts:** 2 (bash + PowerShell)
- **Prepare-Job Scripts:** 3 (2 wrappers + 1 Python core)
- **Pipeline Orchestration Scripts:** 3 (2 wrappers + 1 Python core)
- **Supporting Scripts:** 8 (common logging, status, quick-start, etc.)
- **Python Stage Scripts:** 40+ (actual pipeline stages)
- **Docker/Container Scripts:** 2 (build-all-images, push-images)

---

## 🔧 Bootstrap Scripts

### ✅ ACTIVE AND RELEVANT

#### 1. **`scripts/bootstrap.sh`** (672 lines)
**Status:** ✅ **ACTIVE - PRIMARY BOOTSTRAP (macOS/Linux)**

**Purpose:** One-time environment setup with comprehensive hardware detection

**Key Functions:**
- Creates Python virtual environment (`.bollyenv`)
- Installs 70+ Python packages from requirements files
- Detects hardware (CPU, GPU type: MPS/CUDA, memory)
- Creates hardware cache (`out/hardware_cache.json`)
- Auto-configures pipeline settings in `config/.env.pipeline`
- Downloads ML models (Whisper, PyAnnote, spaCy)
- Validates FFmpeg, PyTorch, PyAnnote compatibility
- Sets up directory structure (`in/`, `out/`, `logs/`, `config/`)
- Validates glossary system
- Installs MLX-Whisper for Apple Silicon (2-4x speedup)
- Handles torch 2.8.x + numpy 2.x compatibility fixes

**Platform-Specific Enhancements:**
- macOS Apple Silicon (M1/M2/M3): MLX-Whisper installation, MPS environment optimization
- Uses `requirements-macos-pinned.txt` for faster installs on macOS

**Configuration Flow:**
```
bootstrap.sh → Hardware Detection → config/.env.pipeline → Job .env files → Runtime
```

**Dependencies:**
- Python 3.11+
- FFmpeg
- `requirements.txt` or `requirements-macos-pinned.txt`
- `requirements-optional.txt` (jellyfish, sentence-transformers)
- `shared/hardware_detection.py`
- `shared/verify_pytorch.py`
- `shared/model_downloader.py` (parallel download)

**Outputs:**
- `.bollyenv/` virtual environment
- `out/hardware_cache.json` (hardware capabilities)
- `config/.env.pipeline` (auto-configured settings)
- `.cache/torch/` and `.cache/huggingface/` (model cache)

---

#### 2. **`scripts/bootstrap.ps1`** (659 lines)
**Status:** ✅ **ACTIVE - PRIMARY BOOTSTRAP (Windows)**

**Purpose:** Windows equivalent with CUDA optimization

**Key Differences from bash version:**
- CUDA priority (detects NVIDIA GPUs first)
- Windows Developer Mode check (for HuggingFace symlinks)
- PowerShell-specific activation scripts
- CUDA environment optimization (TF32, memory allocator)
- Uses `Activate.ps1` instead of shell sourcing

**Platform-Specific:**
- CUDA-optimized for Windows with NVIDIA GPUs
- Checks for Developer Mode to enable symlinks
- Sets CUDA-specific environment variables

**Configuration Flow:** Same as bash version

---

## 📝 Prepare-Job Scripts

### ✅ ACTIVE AND RELEVANT

#### 3. **`prepare-job.sh`** (376 lines)
**Status:** ✅ **ACTIVE - JOB PREPARATION WRAPPER (macOS/Linux)**

**Purpose:** Bash wrapper for `scripts/prepare-job.py` with validation

**Key Functions:**
- Validates `.bollyenv` environment exists
- Activates virtual environment
- Parses command-line arguments
- Validates input media file
- Forwards arguments to `prepare-job.py`
- Displays stage list based on workflow mode

**Supported Arguments:**
- `--transcribe`: Fast mode (demux → vad → asr only, 3 stages)
- `--subtitle-gen`: Full pipeline (all 13 stages, default)
- `--native`: Enable GPU acceleration (auto-detects MPS/CUDA)
- `--start-time`, `--end-time`: Clip extraction
- Stage control flags:
  - `--enable-silero-vad` / `--disable-silero-vad`
  - `--enable-pyannote-vad` / `--disable-pyannote-vad`
  - `--enable-diarization` / `--disable-diarization`

**Phase 1 Enhancement:** 80-90% faster (5-30 seconds vs 1-2 minutes)
- No temporary venv creation
- No PyTorch installation
- Uses cached hardware info
- Direct execution via `.bollyenv`

**Example Usage:**
```bash
./prepare-job.sh in/movie.mp4                          # Full pipeline
./prepare-job.sh in/movie.mp4 --transcribe             # Fast mode
./prepare-job.sh in/movie.mp4 --disable-pyannote-vad   # Skip PyAnnote VAD
./prepare-job.sh in/movie.mp4 --start-time 00:10:00 --end-time 00:15:00
```

---

#### 4. **`prepare-job.ps1`** (327 lines)
**Status:** ✅ **ACTIVE - JOB PREPARATION WRAPPER (Windows)**

**Purpose:** Windows PowerShell wrapper for `scripts/prepare-job.py`

**Key Differences:**
- PowerShell parameter syntax
- Windows path handling (backslashes)
- CUDA priority messaging

**Example Usage:**
```powershell
.\prepare-job.ps1 C:\videos\movie.mp4
.\prepare-job.ps1 C:\videos\movie.mp4 -Transcribe
.\prepare-job.ps1 C:\videos\movie.mp4 -DisablePyannoteVad
```

---

#### 5. **`scripts/prepare-job.py`** (Core Python Script)
**Status:** ✅ **ACTIVE - CORE JOB PREPARATION LOGIC**

**Purpose:** Creates job directory structure and configuration

**Key Functions:**
1. **Hardware Detection:** Loads from `out/hardware_cache.json` or detects fresh
2. **Job Directory Creation:** `out/YYYY/MM/DD/<user-id>/<job-id>/`
3. **Config Customization:** Copies and customizes `config/.env.pipeline` template
4. **Media Preparation:** Clips or copies input video
5. **Job Definition:** Creates `job.json` with metadata
6. **Environment File:** Generates `.<job-id>.env` for runtime

**Job Directory Structure Created:**
```
out/YYYY/MM/DD/USER_ID/JOB_ID/
├── .JOB_ID.env              # Job-specific configuration
├── job.json                 # Job metadata (input, workflow, timestamps)
├── manifest.json            # Stage tracking (created by pipeline)
├── audio/                   # Audio extraction output
├── metadata/                # TMDB data
├── prompts/                 # NER-enhanced prompts
├── entities/                # Entity extraction (pre/post NER)
├── vad/                     # Voice activity detection
├── diarization/             # Speaker segments
├── asr/                     # Transcription
├── translation/             # Second-pass translation
├── lyrics/                  # Lyrics detection
├── subtitles/               # Generated SRT files
└── logs/                    # Stage-specific logs
```

**Configuration Hierarchy:**
1. `config/.env.pipeline` (template with hardware auto-config)
2. Job-specific `.<job-id>.env` (customized for this job)
3. Runtime environment variables (loaded by stages)

**Dependencies:**
- `shared/logger.py` (structured logging)
- `scripts/filename_parser.py` (extract metadata from filename)
- `shared/hardware_detection.py` (hardware capabilities)

---

## 🚀 Pipeline Orchestration Scripts

### ✅ ACTIVE AND RELEVANT

#### 6. **`run_pipeline.sh`** (176 lines)
**Status:** ✅ **ACTIVE - MAIN PIPELINE ORCHESTRATOR (macOS/Linux)**

**Purpose:** Bash wrapper for `scripts/pipeline.py` with environment setup

**Key Functions:**
- Validates job ID
- Activates `.bollyenv` virtual environment
- Sets cache directories (`TORCH_HOME`, `HF_HOME`)
- Forwards arguments to `pipeline.py`
- Handles exit codes and completion messages

**Supported Arguments:**
- `--job <job-id>`: Job to process (required)
- `--stages "<stage1> <stage2> ..."`: Run specific stages only
- `--no-resume`: Start fresh, ignore checkpoints
- `--list-stages`: Display available stages

**Example Usage:**
```bash
./run_pipeline.sh --job 20251102-0001                     # Complete pipeline
./run_pipeline.sh --job 20251102-0001 --no-resume        # Fresh start
./run_pipeline.sh --job 20251102-0001 --stages "demux asr mux"  # Specific stages
./run_pipeline.sh --list-stages                           # List stages
```

**Resume Capability:** Automatically resumes from last completed stage using `manifest.json`

---

#### 7. **`run_pipeline.ps1`** (158 lines)
**Status:** ✅ **ACTIVE - MAIN PIPELINE ORCHESTRATOR (Windows)**

**Purpose:** Windows PowerShell wrapper for `scripts/pipeline.py`

**Key Differences:**
- PowerShell syntax
- Windows path handling
- CUDA-optimized messaging

**Example Usage:**
```powershell
.\run_pipeline.ps1 -Job 20251102-0001
.\run_pipeline.ps1 -Job 20251102-0001 -NoResume
.\run_pipeline.ps1 -Job 20251102-0001 -Stages "demux asr mux"
```

---

#### 8. **`scripts/pipeline.py`** (Core Python Orchestrator)
**Status:** ✅ **ACTIVE - CORE PIPELINE ORCHESTRATION LOGIC**

**Purpose:** Job-based pipeline execution with manifest tracking and resume

**Key Features:**
1. **Stage Definitions:** 15 total stages (13 main + 2 supporting)
2. **Manifest Tracking:** JSON-based progress tracking in `manifest.json`
3. **Resume Capability:** Continue from last completed stage
4. **Native Execution:** Runs Python scripts directly (no Docker)
5. **ML Model Detection:** Identifies ML stages for GPU acceleration
6. **Timeout Management:** Per-stage timeout enforcement
7. **Error Recovery:** Graceful handling of stage failures

**Stage Definitions (15 total):**
```python
STAGE_DEFINITIONS = [
    ("demux", "tmdb", "demux", 600, True, False),                    # 1. Audio extraction
    ("tmdb", "pre_ner", "tmdb", 120, False, False),                  # 2. Metadata fetch
    ("pre_ner", "silero_vad", "pre-ner", 300, False, False),         # 3. Entity extraction
    ("silero_vad", "pyannote_vad", "silero-vad", 1800, True, True),  # 4. Coarse VAD (ML)
    ("pyannote_vad", "asr", "pyannote-vad", 3600, True, True),       # 5. Fine VAD (ML)
    ("asr", "bias_injection", "asr", 14400, True, True),             # 6. WhisperX ASR (ML)
    ("bias_injection", "diarization", "bias-injection", 600, False, False),  # 7. Bias correction
    ("diarization", "glossary_builder", "diarization", 7200, True, True),    # 8. Speaker ID (ML)
    ("glossary_builder", "second_pass_translation", "glossary-builder", 300, False, False),  # 9. Term extraction
    ("second_pass_translation", "lyrics_detection", "second-pass-translation", 7200, False, True),  # 10. Translation (ML)
    ("lyrics_detection", "post_ner", "lyrics-detection", 1800, False, True), # 11. Song detection (ML)
    ("post_ner", "subtitle_gen", "post-ner", 1200, False, False),    # 12. Name correction
    ("subtitle_gen", "mux", "subtitle-gen", 600, True, False),       # 13. SRT generation
    ("mux", "finalize", "mux", 600, True, False),                    # 14. Video embedding
    ("finalize", None, "finalize", 60, False, False),                # 15. Output organization
]
```

**ML Stages (6 total - use GPU when available):**
- `silero_vad` → `silero_vad.py`
- `pyannote_vad` → `pyannote_vad.py`
- `diarization` → `diarization.py`
- `asr` → `whisperx_asr.py`
- `second_pass_translation` → `second_pass_translation.py`
- `lyrics_detection` → `lyrics_detection.py`

**Stage Scripts Mapping:**
```python
STAGE_SCRIPTS = {
    "demux": "demux.py",
    "tmdb": "tmdb.py",
    "pre_ner": "pre_ner.py",
    "silero_vad": "silero_vad.py",
    "pyannote_vad": "pyannote_vad.py",
    "asr": "whisperx_asr.py",
    "bias_injection": "bias_injection.py",  # NEW in Phase 3
    "diarization": "diarization.py",
    "glossary_builder": "glossary_builder.py",
    "second_pass_translation": "second_pass_translation.py",
    "lyrics_detection": "lyrics_detection.py",
    "post_ner": "post_ner.py",
    "subtitle_gen": "subtitle_gen.py",
    "mux": "mux.py",
    "finalize": "finalize.py"
}
```

**Manifest Structure (`manifest.json`):**
```json
{
  "job_id": "20251102-0001",
  "created_at": "2025-11-02T10:30:00Z",
  "workflow": "subtitle-gen",
  "stages": {
    "demux": {
      "status": "success",
      "completed": true,
      "started_at": "...",
      "completed_at": "...",
      "duration_seconds": 45
    },
    ...
  }
}
```

**Class: JobOrchestrator**
- Loads job info from `job.json`
- Loads job config from `.<job-id>.env`
- Manages stage execution sequence
- Updates manifest after each stage
- Handles resume from checkpoint
- Enforces stage timeouts
- Logs to stage-specific log files

---

## 🔄 Supporting Orchestration Scripts

### ✅ ACTIVE AND RELEVANT

#### 9. **`resume-pipeline.sh`** (61 lines)
**Status:** ✅ **ACTIVE - RESUME HELPER (macOS/Linux)**

**Purpose:** Convenience wrapper for resuming interrupted pipelines

**Function:** 
- Simplified wrapper around `run_pipeline.sh` with resume enabled (default)
- Activates `.bollyenv`
- Calls `pipeline.py --job <job-id>` (resume is default behavior)

**Example Usage:**
```bash
./resume-pipeline.sh 20251102-0002
```

**Note:** Equivalent to `./run_pipeline.sh --job 20251102-0002` (resume is automatic)

---

#### 10. **`resume-pipeline.ps1`** (87 lines)
**Status:** ✅ **ACTIVE - RESUME HELPER (Windows)**

**Purpose:** Windows PowerShell equivalent

**Example Usage:**
```powershell
.\resume-pipeline.ps1 20251102-0002
```

---

#### 11. **`quick-start.sh`** (91 lines)
**Status:** ✅ **ACTIVE - ALL-IN-ONE WORKFLOW (macOS/Linux)**

**Purpose:** Complete workflow automation (bootstrap → prepare → run)

**Function:**
1. Validates input video
2. Runs bootstrap if `.bollyenv` doesn't exist
3. Calls `prepare-job.py` to create job
4. Extracts job ID from output
5. Runs `pipeline.py` with job ID

**Example Usage:**
```bash
./quick-start.sh in/movie.mp4
```

**Output:** Completed subtitle generation in one command

---

#### 12. **`quick-start.ps1`** (117 lines)
**Status:** ✅ **ACTIVE - ALL-IN-ONE WORKFLOW (Windows)**

**Purpose:** Windows PowerShell equivalent

**Example Usage:**
```powershell
.\quick-start.ps1 C:\videos\movie.mp4
```

---

#### 13. **`finalize-output.sh`** (49 lines)
**Status:** ✅ **ACTIVE - OUTPUT ORGANIZER (macOS/Linux)**

**Purpose:** Organizes final output into title-based directory

**Function:**
- Finds job directory by job ID
- Calls `scripts/finalize_output.py`
- Organizes output by movie title

**Example Usage:**
```bash
./finalize-output.sh 20251109-0001
```

**Note:** This is also called automatically as the final stage (`finalize`) in the pipeline

---

#### 14. **`finalize-output.ps1`** (68 lines)
**Status:** ✅ **ACTIVE - OUTPUT ORGANIZER (Windows)**

**Purpose:** Windows PowerShell equivalent

---

## 📊 Status and Logging Scripts

### ✅ ACTIVE AND RELEVANT

#### 15. **`scripts/pipeline-status.sh`** (191 lines)
**Status:** ✅ **ACTIVE - STATUS DISPLAY (macOS/Linux)**

**Purpose:** Display pipeline status and quick reference

**Functions:**
1. **Job-Specific Status:** Shows stage completion progress
   - Reads `manifest.json` to display stage status
   - Shows ✓ (completed), ○ (pending), ✗ (failed), ⏳ (running)
2. **Pipeline Overview:** Lists all 12 stages with descriptions
3. **Common Commands:** Quick reference guide
4. **Execution Modes:** Platform-specific info
5. **Output Structure:** Directory layout explanation
6. **Stage Timeouts:** Timeout values for each stage
7. **Examples:** Native execution examples

**Example Usage:**
```bash
./scripts/pipeline-status.sh                # General info
./scripts/pipeline-status.sh 20251108-0002  # Job-specific status
```

**Output Example:**
```
📋 JOB STATUS: 20251108-0002
────────────────────────────────────────────────────
  📁 Location: out/2025/11/08/user123/20251108-0002
  📊 Stage Progress:

    ✓ demux                     [COMPLETED]
    ✓ tmdb                      [COMPLETED]
    ✓ pre_ner                   [COMPLETED]
    ✓ silero_vad                [COMPLETED]
    ⏳ pyannote_vad              [RUNNING]
    ○ diarization               [PENDING]
    ...
```

---

#### 16. **`scripts/pipeline-status.ps1`** (195 lines)
**Status:** ✅ **ACTIVE - STATUS DISPLAY (Windows)**

**Purpose:** Windows PowerShell equivalent

---

#### 17. **`scripts/common-logging.sh`** (158 lines)
**Status:** ✅ **ACTIVE - SHARED LOGGING FUNCTIONS (macOS/Linux)**

**Purpose:** Reusable logging functions for bash scripts

**Functions:**
- `log_section()` - Section headers with cyan color
- `log_info()` - Info messages
- `log_success()` - Success messages (green)
- `log_warning()` - Warning messages (yellow)
- `log_error()` - Error messages (red)
- `log_debug()` - Debug messages (gray, conditional)

**Usage:** Sourced by all bash scripts
```bash
source "$SCRIPT_DIR/scripts/common-logging.sh"
log_info "Starting process..."
log_success "Process completed!"
```

---

#### 18. **`scripts/common-logging.ps1`** (178 lines)
**Status:** ✅ **ACTIVE - SHARED LOGGING FUNCTIONS (Windows)**

**Purpose:** Windows PowerShell equivalent

**Functions:**
- `Write-LogSection` - Section headers
- `Write-LogInfo` - Info messages
- `Write-LogSuccess` - Success messages
- `Write-LogWarning` - Warning messages
- `Write-LogError` - Error messages
- `Write-LogDebug` - Debug messages

---

## 🐳 Docker/Container Scripts

### ⚠️ INACTIVE (Docker mode not currently used)

#### 19. **`scripts/build-all-images.ps1`** (235 lines)
**Status:** ⚠️ **INACTIVE - DOCKER BUILD SCRIPT**

**Purpose:** Build Docker images for all pipeline stages

**Reason for Inactivity:** 
- Current deployment uses **native execution** (`.bollyenv` virtual environment)
- Docker mode was original design but replaced by faster native mode
- Script builds CPU and CUDA variants for each stage

**Docker Image Tagging:**
- CPU-only stages: `:cpu` tag
- GPU stages: `:cuda` tag

**Stages Built:**
- Base images: `base:cpu`, `base:cuda`
- Stage images: `demux:cpu`, `asr:cuda`, etc.

**Note:** Could be reactivated if Docker deployment is needed

---

#### 20. **`scripts/push-images.ps1`** (88 lines)
**Status:** ⚠️ **INACTIVE - DOCKER PUSH SCRIPT**

**Purpose:** Push built Docker images to registry

**Reason for Inactivity:** Same as `build-all-images.ps1`

---

## 📦 Python Stage Scripts (40+ files)

### ✅ ACTIVE - CORE PIPELINE STAGES

All Python scripts in `scripts/` directory are **ACTIVE** and used by the pipeline:

#### Core Pipeline Stages (15 scripts)
1. **`demux.py`** - Audio extraction (FFmpeg)
2. **`tmdb.py`** - Metadata fetch from TMDB API
3. **`pre_ner.py`** - Pre-processing entity extraction
4. **`silero_vad.py`** - Coarse voice activity detection (ML)
5. **`pyannote_vad.py`** - Fine-grained VAD (ML)
6. **`diarization.py`** - Speaker diarization (ML)
7. **`whisperx_asr.py`** - WhisperX transcription (ML)
8. **`bias_injection.py`** - Post-ASR bias correction (NEW)
9. **`glossary_builder.py`** - Adaptive glossary generation
10. **`second_pass_translation.py`** - Translation refinement (ML)
11. **`lyrics_detection.py`** - Song sequence detection (ML)
12. **`post_ner.py`** - Post-processing name correction
13. **`subtitle_gen.py`** - SRT file generation
14. **`mux.py`** - Subtitle embedding (FFmpeg)
15. **`finalize.py`** - Output organization

#### Supporting Modules (25+ scripts)
- **Bias Injection System:** `bias_injection_core.py`, `bias_strategy_selector.py`, `bias_window_generator.py`, `adaptive_bias_strategy.py`
- **WhisperX Integration:** `whisperx_integration.py`, `whisper_backends.py`, `asr_chunker.py`
- **VAD Utilities:** `pyannote_vad_chunker.py`
- **Lyrics Detection:** `lyrics_detection_core.py`
- **NER Processing:** `ner_extraction.py`, `name_entity_correction.py`
- **Translation:** `translation_refine.py`
- **TMDB Integration:** `tmdb_enrichment.py`
- **Utilities:** `filename_parser.py`, `config_loader.py`, `manifest.py`, `device_selector.py`, `mps_utils.py`, `canonicalization.py`, `prompt_assembly.py`
- **Patches:** `patch_pyannote.py` (fixes torchaudio 2.9 compatibility)

---

## 🔧 Shared Utilities (12 files)

### ✅ ACTIVE - SHARED INFRASTRUCTURE

All files in `shared/` directory are **ACTIVE**:

1. **`config.py`** - Configuration loader (env files)
2. **`logger.py`** - Structured logging system
3. **`manifest.py`** - Manifest builder and tracker
4. **`hardware_detection.py`** - Hardware capability detection
5. **`stage_utils.py`** - Stage execution utilities
6. **`utils.py`** - General utilities
7. **`job_manager.py`** - Job management utilities
8. **`verify_pytorch.py`** - PyTorch verification
9. **`glossary.py`** - Glossary system (basic)
10. **`glossary_advanced.py`** - Advanced glossary strategies
11. **`glossary_ml.py`** - ML-based glossary selection
12. **`model_downloader.py`** - Parallel model pre-download (assumed, not listed but referenced)

---

## 🗂️ Configuration Files

### ✅ ACTIVE CONFIGURATION

1. **`config/.env.pipeline`** - Pipeline configuration template
   - Auto-generated by `bootstrap.sh`
   - Contains hardware-optimized settings
   - Template for job-specific env files

2. **`config/secrets.json`** - API tokens (optional)
   - HF_TOKEN for HuggingFace models
   - TMDB_API_KEY for metadata
   - OPENAI_API_KEY for translation (optional)

3. **`requirements.txt`** - Python dependencies (70+ packages)
4. **`requirements-macos.txt`** - macOS-specific packages
5. **`requirements-macos-pinned.txt`** - Pinned versions (faster install)
6. **`requirements-optional.txt`** - Optional enhancements (jellyfish, sentence-transformers)
7. **`requirements-flexible.txt`** - Flexible version ranges

---

## 📝 Summary: Relevant vs. Unused

### ✅ **RELEVANT AND ACTIVELY USED (81 files)**

#### Bootstrap Scripts (2)
- ✅ `scripts/bootstrap.sh` (macOS/Linux)
- ✅ `scripts/bootstrap.ps1` (Windows)

#### Prepare-Job Scripts (3)
- ✅ `prepare-job.sh` (macOS/Linux wrapper)
- ✅ `prepare-job.ps1` (Windows wrapper)
- ✅ `scripts/prepare-job.py` (core logic)

#### Pipeline Orchestration Scripts (3)
- ✅ `run_pipeline.sh` (macOS/Linux wrapper)
- ✅ `run_pipeline.ps1` (Windows wrapper)
- ✅ `scripts/pipeline.py` (core orchestrator)

#### Supporting Orchestration Scripts (6)
- ✅ `resume-pipeline.sh` (macOS/Linux)
- ✅ `resume-pipeline.ps1` (Windows)
- ✅ `quick-start.sh` (macOS/Linux)
- ✅ `quick-start.ps1` (Windows)
- ✅ `finalize-output.sh` (macOS/Linux)
- ✅ `finalize-output.ps1` (Windows)

#### Status and Logging Scripts (4)
- ✅ `scripts/pipeline-status.sh` (macOS/Linux)
- ✅ `scripts/pipeline-status.ps1` (Windows)
- ✅ `scripts/common-logging.sh` (macOS/Linux)
- ✅ `scripts/common-logging.ps1` (Windows)

#### Python Stage Scripts (40+ files)
- ✅ All 15 core pipeline stage scripts
- ✅ All 25+ supporting module scripts

#### Shared Utilities (12 files)
- ✅ All shared infrastructure files

---

### ⚠️ **INACTIVE BUT POTENTIALLY USEFUL (2 files)**

#### Docker/Container Scripts (2)
- ⚠️ `scripts/build-all-images.ps1` - Docker image builder
- ⚠️ `scripts/push-images.ps1` - Docker image publisher

**Reason:** Native execution (`.bollyenv`) replaced Docker mode for better performance  
**Status:** Can be reactivated if Docker deployment is needed

---

### ❌ **UNUSED OR DEPRECATED (0 files)**

**No scripts identified as unused or deprecated.**

All scripts in the project are either:
1. Actively used in the current workflow
2. Platform-specific alternatives (bash vs PowerShell)
3. Potentially reusable (Docker scripts)

---

## 🔍 Script Dependencies and Flow

### Bootstrap Flow
```
User runs: bootstrap.sh/ps1
    ↓
Creates .bollyenv virtual environment
    ↓
Installs Python packages (requirements.txt)
    ↓
Runs shared/hardware_detection.py
    ↓
Creates out/hardware_cache.json
    ↓
Auto-generates config/.env.pipeline
    ↓
Downloads ML models (parallel)
    ↓
Validates PyTorch, PyAnnote, FFmpeg
    ↓
Environment ready!
```

### Prepare-Job Flow
```
User runs: prepare-job.sh/ps1 <input-media>
    ↓
Validates .bollyenv exists
    ↓
Activates virtual environment
    ↓
Parses arguments (workflow, clip times, stage flags)
    ↓
Calls scripts/prepare-job.py
    ↓
Loads hardware cache (out/hardware_cache.json)
    ↓
Creates job directory (out/YYYY/MM/DD/USER_ID/JOB_ID/)
    ↓
Copies config/.env.pipeline → .<job-id>.env
    ↓
Customizes config based on args
    ↓
Creates job.json (metadata)
    ↓
Clips or copies input media
    ↓
Job ready! Returns job ID
```

### Pipeline Execution Flow
```
User runs: run_pipeline.sh/ps1 --job <job-id>
    ↓
Validates .bollyenv exists
    ↓
Activates virtual environment
    ↓
Sets cache directories (TORCH_HOME, HF_HOME)
    ↓
Calls scripts/pipeline.py --job <job-id>
    ↓
Loads job.json and .<job-id>.env
    ↓
Checks manifest.json for resume point
    ↓
Executes stages sequentially:
    1. demux.py → audio/audio.wav
    2. tmdb.py → metadata/tmdb_data.json
    3. pre_ner.py → entities/pre_ner.json
    4. silero_vad.py → vad/silero_segments.json
    5. pyannote_vad.py → vad/pyannote_segments.json
    6. diarization.py → diarization/speaker_segments.json
    7. whisperx_asr.py → asr/transcript.json
    8. bias_injection.py → asr/transcript_biased.json (NEW)
    9. glossary_builder.py → glossary/adaptive_glossary.json
    10. second_pass_translation.py → translation/refined_transcript.json
    11. lyrics_detection.py → lyrics/lyrics_segments.json
    12. post_ner.py → entities/post_ner.json
    13. subtitle_gen.py → subtitles/subtitles.srt
    14. mux.py → final_output.mp4
    15. finalize.py → Organize output
    ↓
Updates manifest.json after each stage
    ↓
Pipeline complete!
```

---

## 🎯 Key Findings

### 1. **All Scripts Are Relevant**
- No unused or deprecated scripts found
- All scripts serve specific purposes in the workflow
- Platform-specific alternatives (bash/PowerShell) provide cross-platform support

### 2. **Well-Organized Architecture**
- Clear separation: bootstrap → prepare → orchestrate → execute
- Wrappers (bash/PowerShell) handle environment, core logic in Python
- Consistent logging and error handling across all scripts

### 3. **Native Execution Model**
- Docker scripts inactive but preserved for potential reactivation
- `.bollyenv` virtual environment provides faster execution
- Direct Python execution without container overhead

### 4. **Comprehensive Feature Set**
- Hardware auto-detection and optimization
- Resume capability with manifest tracking
- Flexible workflow modes (transcribe vs. subtitle-gen)
- Stage-level control (enable/disable individual stages)
- Parallel model downloads (Phase 3 optimization)

### 5. **Cross-Platform Support**
- Bash scripts for macOS/Linux
- PowerShell scripts for Windows
- Platform-specific optimizations (MPS for macOS, CUDA for Windows)

---

## 📚 Recommendations

### For Code Maintenance
1. **Keep all current scripts** - they are all actively used
2. **Maintain Docker scripts** - useful for future deployment options
3. **Document version compatibility** - track torch/numpy/torchaudio versions
4. **Centralize configuration** - continue using `.env` files and hardware cache

### For Documentation
1. **Create flowcharts** - visualize bootstrap → prepare → run flow
2. **Document stage dependencies** - which stages depend on previous outputs
3. **Maintain changelog** - track Phase 1, 2, 3 enhancements
4. **Add troubleshooting guide** - common issues and solutions

### For Future Development
1. **Consider consolidation** - merge common-logging into shared module
2. **Add validation scripts** - verify environment before pipeline execution
3. **Implement parallel stage execution** - some stages (tmdb, pre_ner) could run in parallel
4. **Add monitoring dashboard** - real-time pipeline progress visualization

---

## 📅 Version Information

**Script Analysis Version:** 1.0  
**Last Updated:** 2025-11-14  
**Pipeline Version:** Phase 3 (Bias Injection + Parallel Downloads)  
**Python Version:** 3.11+  
**PyTorch Version:** 2.8.x (with numpy 2.x compatibility)

---

**END OF ANALYSIS**
