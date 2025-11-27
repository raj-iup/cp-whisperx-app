# Codebase Dependency Map
**CP-WhisperX-App Architecture & Dependencies**  
**Generated**: 2025-11-25  
**Updated for**: Phase 1 & 2 Fixes

---

## Table of Contents

1. [Overview](#overview)
2. [Bootstrap Scripts](#bootstrap-scripts)
3. [Job Preparation Scripts](#job-preparation-scripts)
4. [Pipeline Orchestration](#pipeline-orchestration)
5. [Pipeline Stage Scripts](#pipeline-stage-scripts)
6. [Shared Modules](#shared-modules)
7. [Utility Scripts](#utility-scripts)
8. [Configuration Files](#configuration-files)
9. [Dependency Graph](#dependency-graph)
10. [Virtual Environments](#virtual-environments)

---

## Overview

The CP-WhisperX-App is a multi-stage audio/video processing pipeline optimized for Indian languages. It uses multiple isolated Python virtual environments to avoid dependency conflicts.

**Key Architecture Principles**:
- **Multi-environment isolation**: 8 separate virtual environments
- **Shell wrappers**: Root scripts delegate to implementation scripts
- **Shared modules**: Common functionality in `shared/` directory
- **Stage-based pipeline**: Sequential processing with checkpoints
- **Model caching**: Offline-first with bootstrap pre-caching

---

## Bootstrap Scripts

### bootstrap.sh (root)
**Type**: Wrapper script  
**Purpose**: Delegates to scripts/bootstrap.sh for backward compatibility

**Dependencies**:
- `scripts/bootstrap.sh` (implementation)

**Config**: None  
**Requirements**: None  
**Arguments**: All passed through to scripts/bootstrap.sh

**Usage**:
```bash
./bootstrap.sh                    # Setup all environments
./bootstrap.sh --env whisperx     # Setup specific environment
./bootstrap.sh --log-level DEBUG  # Verbose logging
```

---

### scripts/bootstrap.sh
**Type**: Main bootstrap implementation  
**Purpose**: Creates virtual environments, installs dependencies, caches models

**Dependencies**:
- `scripts/common-logging.sh` (logging functions)

**Config**:
- `config/secrets.json` (optional - HF/API tokens)
- `config/hardware_cache.json` (created by script)

**Requirements Files**:
- `requirements-common.txt` → venv/common
- `requirements-whisperx.txt` → venv/whisperx
- `requirements-mlx.txt` → venv/mlx (Apple Silicon)
- `requirements-pyannote.txt` → venv/pyannote
- `requirements-demucs.txt` → venv/demucs
- `requirements-indictrans2.txt` → venv/indictrans2
- `requirements-nllb.txt` → venv/nllb
- `requirements-llm.txt` → venv/llm (optional)

**Creates**:
- Virtual environments in `.venv-*/`
- Model caches in `~/.cache/huggingface/`, `~/.cache/torch/`, `~/.cache/mlx/`
- Hardware config in `config/hardware_cache.json`
- Logs in `logs/bootstrap_*.log`

**Key Functions**:
- `setup_environment()` - Creates virtual environment
- `cache_hf_model()` - Downloads and caches HuggingFace models
- `cache_mlx_model()` - Caches MLX Whisper model ✅ **Fixed in Phase 1**
- `detect_hardware()` - Detects GPU/MPS/CPU

**Recent Changes** (Phase 1):
- ✅ Fixed MLX model caching (line 191): Changed `load_model()` to `load_models()`
- ✅ Auto-caches Indic→Indic model (line 234): `ai4bharat/indictrans2-indic-indic-1B`

---

## Job Preparation Scripts

### prepare-job.sh (root)
**Type**: Wrapper + validation script  
**Purpose**: Validates inputs, delegates to Python implementation

**Dependencies**:
- `scripts/prepare-job.py` (main implementation)
- `scripts/common-logging.sh` (logging)

**Config**:
- `config/.env.pipeline` (template)
- `config/secrets.json` (API keys)

**Requirements**: None (uses venv/common)

**Output**: Job directory in `out/YYYY/MM/DD/USER_ID/JOB_NUM/`

**Arguments**:
```bash
--media FILE              Input media file
--workflow MODE           transcribe|translate|subtitle
-s, --source-language     Source language code (hi, ta, etc.)
-t, --target-language     Target language code(s) (en, ta,gu,hi)
--start-time HH:MM:SS     Clip start time
--end-time HH:MM:SS       Clip end time
--log-level LEVEL         DEBUG|INFO|WARN|ERROR|CRITICAL ✅ Phase 2
--debug                   Enable debug mode
```

**Features** (Phase 2):
- ✅ Log level CLI argument support
- ✅ Smart defaults from environment
- ✅ Validation before delegation

---

### scripts/prepare-job.py
**Type**: Job preparation logic  
**Purpose**: Creates job directory structure, prepares configuration

**Dependencies**:
- `shared/logger.py` (logging)
- `shared/environment_manager.py` (venv management)
- `scripts/filename_parser.py` (media file parsing)
- `scripts/config_loader.py` (config loading)

**Config**:
- `config/.env.pipeline` (pipeline template)
- `config/secrets.json` (API keys)

**Requirements**: requirements-common.txt

**Creates**:
- `{job_dir}/config/job.json` (job configuration)
- `{job_dir}/manifest.json` (job metadata)
- `{job_dir}/logs/` (log directory)
- `{job_dir}/00_input/` (prepared media)

**Key Functions**:
- `create_job_directory()` - Creates job structure
- `prepare_media()` - Clips or copies media
- `create_job_config()` - Generates job.json
- `create_env_file()` - Creates environment variables
- `create_manifest()` - Generates manifest.json

**Recent Changes** (Phase 1):
- ✅ Added "Next steps" output (lines 689-691): Shows pipeline run command

**Features** (Phase 2):
- ✅ Log level argument (line 551): `--log-level` with validation

---

## Pipeline Orchestration

### run-pipeline.sh (root)
**Type**: Wrapper + orchestration script  
**Purpose**: Validates job, delegates to Python pipeline

**Dependencies**:
- `scripts/run-pipeline.py` (main implementation)
- `scripts/common-logging.sh` (logging)

**Config**:
- `{job_dir}/config/job.json` (job configuration)

**Requirements**: None (uses multiple venvs)

**Arguments**:
```bash
-j, --job-id JOB_ID       Job ID to run
--resume                  Resume from last stage
--log-level LEVEL         Override job config log level ✅ Phase 2
```

**Features** (Phase 2):
- ✅ Log level CLI argument (line 86)
- ✅ Smart defaults from job.json (line 196-202)
- ✅ Environment variable propagation

---

### scripts/run-pipeline.py
**Type**: Main pipeline orchestrator  
**Purpose**: Executes all pipeline stages sequentially

**Dependencies**:
- `shared/logger.py` - Logging infrastructure
- `shared/environment_manager.py` - Virtual environment management
- `shared/stage_utils.py` - Stage utilities
- `scripts/config_loader.py` - Configuration loading

**Stage Scripts** (in order):
1. `scripts/source_separation.py` - Demucs vocal isolation
2. `scripts/whisperx_asr.py` OR `scripts/mlx_asr.py` - Speech-to-text
3. `scripts/silero_vad.py` OR `scripts/pyannote_vad.py` - Voice activity detection
4. `scripts/diarization.py` - Speaker diarization (optional)
5. `scripts/mlx_alignment.py` - Word-level alignment ✅ Phase 1 verified
6. `scripts/indictrans2_translator.py` - Indic→English/Indic translation ✅ Phase 1 fixed
7. `scripts/nllb_translator.py` - Non-Indic language translation
8. `scripts/hybrid_translator.py` - Multi-model translation
9. `scripts/subtitle_gen.py` - SRT generation
10. `scripts/ner_extraction.py` - Named entity extraction (optional)
11. `scripts/glossary_builder.py` - Glossary generation (optional)
12. `scripts/bias_injection.py` - Glossary bias injection (optional)
13. `scripts/lyrics_detection.py` - Song detection (optional)
14. `scripts/hallucination_removal.py` - Transcript cleaning (optional)
15. `scripts/subtitle_enhancement.py` - Quality improvements (optional)

**Config**:
- `{job_dir}/config/job.json` - Job configuration
- `glossary/*.txt` - Glossary files

**Requirements**: All requirements-*.txt files (via environment manager)

**Output**: 
- Stage outputs in `{job_dir}/01_source_separation/`, `02_asr/`, etc.
- Logs in `{job_dir}/logs/pipeline.log`
- Final subtitles in `{job_dir}/subtitles/`

**Key Features**:
- Stage-based execution with checkpoints
- Automatic resume capability
- Multi-environment orchestration
- Error handling and logging
- Progress tracking

**Recent Changes** (Phase 2):
- ✅ Log level from job config (line 95-107)
- ✅ Environment variable propagation (lines 262, 640, 689, etc.)

---

## Pipeline Stage Scripts

### Audio Processing

#### scripts/source_separation.py
**Purpose**: Vocal isolation using Demucs  
**Environment**: venv/demucs  
**Input**: `00_input/media.mp4`  
**Output**: `01_source_separation/vocals.wav`

**Dependencies**: demucs, torch, torchaudio

---

#### scripts/whisperx_asr.py
**Purpose**: Speech-to-text using WhisperX  
**Environment**: venv/whisperx  
**Input**: `01_source_separation/vocals.wav`  
**Output**: `02_asr/segments.json`

**Dependencies**: whisperx, faster-whisper, torch

---

#### scripts/mlx_asr.py
**Purpose**: Speech-to-text using MLX-Whisper (Apple Silicon)  
**Environment**: venv/mlx  
**Input**: `01_source_separation/vocals.wav`  
**Output**: `02_asr/segments.json`

**Dependencies**: mlx-whisper, mlx

**Note**: Optimized for Apple Silicon with 2-4x speedup

---

### Voice Activity Detection

#### scripts/silero_vad.py
**Purpose**: Voice activity detection using Silero VAD  
**Environment**: venv/common  
**Input**: `02_asr/segments.json`  
**Output**: `03_vad/vad_segments.json`

**Dependencies**: torch, torchaudio

---

#### scripts/pyannote_vad.py
**Purpose**: Voice activity detection using PyAnnote  
**Environment**: venv/pyannote  
**Input**: `02_asr/segments.json`  
**Output**: `03_vad/vad_segments.json`

**Dependencies**: pyannote.audio

---

### Speaker Analysis

#### scripts/diarization.py
**Purpose**: Speaker diarization using PyAnnote  
**Environment**: venv/pyannote  
**Input**: `03_vad/vad_segments.json`  
**Output**: `04_diarization/speaker_segments.json`

**Dependencies**: pyannote.audio

---

### Alignment

#### scripts/mlx_alignment.py
**Purpose**: Word-level timestamp alignment  
**Environment**: venv/mlx  
**Input**: `02_asr/segments.json`, audio file  
**Output**: `05_alignment/aligned_segments.json`

**Dependencies**: mlx-whisper

**Key Features**:
- Word-level timestamps via `word_timestamps=True`
- Anti-hallucination settings
- Re-transcription for accuracy

**Status**: ✅ Phase 1 verified - correctly implemented

---

### Translation

#### scripts/indictrans2_translator.py
**Purpose**: Indic language translation (Indic→English or Indic→Indic)  
**Environment**: venv/indictrans2  
**Input**: `05_alignment/aligned_segments.json`  
**Output**: `06_translation/translated_segments_{lang}.json`

**Dependencies**: transformers, IndicTransToolkit

**Models**:
- `ai4bharat/indictrans2-indic-en-1B` (Indic→English)
- `ai4bharat/indictrans2-indic-indic-1B` (Indic→Indic) ✅ Phase 2

**Supported Languages**: 22 Indian scheduled languages

**Recent Changes** (Phase 1):
- ✅ Fixed toolkit import (lines 26-33): Added sys.path manipulation

---

#### scripts/nllb_translator.py
**Purpose**: Non-Indic language translation using NLLB-200  
**Environment**: venv/nllb  
**Input**: `05_alignment/aligned_segments.json`  
**Output**: `06_translation/translated_segments_{lang}.json`

**Dependencies**: transformers, sentencepiece

**Model**: `facebook/nllb-200-3.3B`

**Supported Languages**: 200+ languages

---

#### scripts/hybrid_translator.py
**Purpose**: Multi-model ensemble translation  
**Environment**: Multiple (venv/indictrans2, venv/nllb)  
**Input**: Segments from alignment  
**Output**: Best translation from multiple models

**Strategy**:
- Uses IndicTrans2 for Indic languages
- Falls back to NLLB for other languages
- Ensemble voting for quality

---

### Subtitle Generation

#### scripts/subtitle_gen.py
**Purpose**: SRT subtitle file generation  
**Environment**: venv/common  
**Input**: `06_translation/translated_segments_{lang}.json`  
**Output**: `subtitles/{media_name}_{lang}.srt`

**Dependencies**: srt (Python library)

**Features**:
- Multi-language support
- CPS (characters per second) optimization
- Line splitting and timing adjustments

---

### Enhancement Stages

#### scripts/ner_extraction.py
**Purpose**: Named entity extraction for glossary  
**Environment**: venv/common  
**Input**: Translation segments  
**Output**: `07_ner/entities.json`

**Dependencies**: spacy

---

#### scripts/glossary_builder.py
**Purpose**: Build glossary from NER + user glossaries  
**Environment**: venv/common  
**Input**: `07_ner/entities.json`, `glossary/*.txt`  
**Output**: `08_glossary/glossary.json`

**Dependencies**: `shared/glossary_generator.py`

---

#### scripts/bias_injection.py
**Purpose**: Inject glossary terms as biases for better translation  
**Environment**: Multiple  
**Input**: `08_glossary/glossary.json`  
**Output**: Updated translations with biases

**Dependencies**: `shared/bias_registry.py`

---

#### scripts/lyrics_detection.py
**Purpose**: Detect songs and music sections  
**Environment**: venv/common  
**Input**: Audio + segments  
**Output**: `09_lyrics/lyrics_segments.json`

**Dependencies**: librosa, torch

---

#### scripts/hallucination_removal.py
**Purpose**: Remove hallucinated transcription artifacts  
**Environment**: venv/common  
**Input**: Transcription segments  
**Output**: Cleaned segments

**Strategy**:
- Pattern matching for common hallucinations
- Repetition detection
- Confidence score filtering

---

## Shared Modules

### Core Infrastructure

#### shared/logger.py
**Purpose**: Structured logging for Python scripts  
**Used by**: All Python scripts

**Key Features**:
- Multiple log levels (DEBUG, INFO, WARN, ERROR, CRITICAL)
- File and console output
- Structured formatting
- Stage-specific loggers

**Class**: `PipelineLogger`

**Recent Changes** (Phase 2):
- ✅ Log level from arguments/config

---

#### shared/environment_manager.py
**Purpose**: Virtual environment management  
**Used by**: prepare-job.py, run-pipeline.py

**Key Features**:
- Environment validation
- Path resolution
- Environment switching
- Dependency checking

**Class**: `EnvironmentManager`

---

#### shared/config.py
**Purpose**: Configuration loading and management  
**Used by**: Most scripts

**Key Features**:
- JSON/YAML config loading
- Environment variable expansion
- Secrets management
- Validation

**Class**: `Config`

---

### Stage Utilities

#### shared/stage_utils.py
**Purpose**: Common stage operations  
**Used by**: Pipeline stage scripts

**Functions**:
- `load_segments()` - Load JSON segments
- `save_segments()` - Save JSON segments
- `create_stage_dir()` - Create output directory
- `validate_input()` - Input validation

---

### Glossary Management

#### shared/glossary_generator.py
**Purpose**: Glossary building and management  
**Used by**: scripts/glossary_builder.py

**Features**:
- NER entity extraction
- Glossary merging
- Format conversion
- Quality scoring

---

#### shared/glossary.py
**Purpose**: Basic glossary operations  
**Used by**: Translation scripts

---

#### shared/glossary_unified.py
**Purpose**: Unified glossary interface  
**Used by**: Multiple scripts

---

#### shared/glossary_advanced.py
**Purpose**: Advanced glossary features  
**Used by**: Quality enhancement

---

#### shared/glossary_ml.py
**Purpose**: ML-based glossary expansion  
**Used by**: Optional enhancement

---

### Named Entity Recognition

#### shared/ner_corrector.py
**Purpose**: NER correction and validation  
**Used by**: scripts/ner_extraction.py

**Features**:
- Post-processing of NER results
- Entity type validation
- Confidence scoring

---

### Metadata Management

#### shared/tmdb_client.py
**Purpose**: TMDB API client for movie metadata  
**Used by**: Optional enrichment

**Dependencies**: requests

---

#### shared/tmdb_cache.py
**Purpose**: TMDB data caching  
**Used by**: tmdb_client.py

---

#### shared/musicbrainz_cache.py
**Purpose**: MusicBrainz data caching for songs  
**Used by**: Optional enrichment

---

### Model Management

#### shared/model_checker.py
**Purpose**: Model availability checking  
**Used by**: Bootstrap scripts

---

#### shared/model_downloader.py
**Purpose**: Model download with progress  
**Used by**: Bootstrap scripts

---

#### shared/hardware_detection.py
**Purpose**: Hardware capability detection  
**Used by**: scripts/bootstrap.sh

**Features**:
- GPU detection (CUDA, ROCm, MPS)
- Memory checking
- CPU capabilities
- Platform detection

---

### Bias Management

#### shared/bias_registry.py
**Purpose**: Bias term registration for translation  
**Used by**: scripts/bias_injection.py

---

## Utility Scripts

### scripts/common-logging.sh
**Type**: Shared shell logging functions  
**Used by**: All shell scripts

**Functions**:
- `log_debug()` - Debug messages
- `log_info()` - Info messages
- `log_warn()` - Warnings
- `log_error()` - Errors
- `log_critical()` - Critical errors
- `log_section()` - Section headers
- `log_success()` - Success messages
- `setup_logging()` - Initialize logging

**Features** (Phase 2):
- ✅ LOG_LEVEL environment variable support
- ✅ Color-coded output
- ✅ File logging

---

### scripts/config_loader.py
**Purpose**: Configuration file loading  
**Used by**: Python scripts

**Features**:
- JSON/YAML parsing
- Environment variable substitution
- Secrets loading

---

### scripts/filename_parser.py
**Purpose**: Media filename parsing  
**Used by**: prepare-job.py

**Features**:
- Extract metadata from filenames
- Parse timestamps
- Detect language from filename

---

## Comparison Tools

### compare-beam-search.sh
**Type**: Beam search quality comparison  
**Purpose**: Compare translation quality across beam widths

**Dependencies**:
- `scripts/common-logging.sh`
- `scripts/beam_search_comparison.py`
- `scripts/indictrans2_translator.py` ✅ Phase 1 fixed

**Config**: Uses job directory

**Requirements**: requirements-indictrans2.txt

**Output**: `{job_dir}/beam_comparison/`

**Usage**:
```bash
./compare-beam-search.sh out/2025/11/25/user/1 --beam-range 4,10
```

**Features** (Phase 2):
- ✅ Generates outputs for beam widths 4-10
- ✅ Quality metrics and comparison
- ✅ Recommendation for best beam width

---

### scripts/beam_search_comparison.py
**Purpose**: Beam width comparison logic  
**Environment**: venv/indictrans2

**Features**:
- Translate with different beam widths
- Calculate quality metrics (BLEU, chrF)
- Generate comparison report

---

## Configuration Files

### Requirements Files

#### requirements-common.txt
**Environment**: venv/common  
**Purpose**: Shared utilities

**Key Packages**:
- moviepy (video processing)
- pydub (audio processing)
- spacy (NLP)
- requests (HTTP)
- srt (subtitle formatting)

---

#### requirements-whisperx.txt
**Environment**: venv/whisperx  
**Purpose**: WhisperX ASR

**Key Packages**:
- whisperx
- faster-whisper
- torch
- torchaudio

---

#### requirements-mlx.txt
**Environment**: venv/mlx  
**Purpose**: MLX-Whisper (Apple Silicon)

**Key Packages**:
- mlx
- mlx-whisper
- numpy

**Platform**: macOS with Apple Silicon only

**Recent Changes** (Phase 1):
- ✅ Model caching fix uses correct API

---

#### requirements-pyannote.txt
**Environment**: venv/pyannote  
**Purpose**: Speaker diarization and VAD

**Key Packages**:
- pyannote.audio
- torch
- torchaudio

---

#### requirements-demucs.txt
**Environment**: venv/demucs  
**Purpose**: Source separation

**Key Packages**:
- demucs
- torch
- julius

---

#### requirements-indictrans2.txt
**Environment**: venv/indictrans2  
**Purpose**: Indic language translation

**Key Packages**:
- transformers
- torch
- sentencepiece
- IndicTransToolkit ✅ Phase 1 fixed

**Models**:
- ai4bharat/indictrans2-indic-en-1B
- ai4bharat/indictrans2-indic-indic-1B ✅ Phase 2 cached

**Recent Changes** (Phase 1):
- ✅ Toolkit import path fixed in translator

---

#### requirements-nllb.txt
**Environment**: venv/nllb  
**Purpose**: Non-Indic translation

**Key Packages**:
- transformers
- torch
- sentencepiece

**Model**: facebook/nllb-200-3.3B

---

#### requirements-llm.txt
**Environment**: venv/llm (optional)  
**Purpose**: LLM-based enhancements

**Key Packages**:
- anthropic (Claude)
- openai (GPT)

---

### Configuration Templates

#### config/.env.pipeline
**Purpose**: Pipeline configuration template  
**Used by**: prepare-job.sh

**Contains**:
- Stage enable/disable flags
- Language settings
- Model parameters
- Debug flags

---

#### config/secrets.json
**Purpose**: API keys and tokens  
**Used by**: Bootstrap and pipeline

**Contains** (optional):
- HuggingFace token
- TMDB API key
- OpenAI API key
- Anthropic API key

**Format**:
```json
{
  "huggingface_token": "hf_...",
  "tmdb_api_key": "...",
  "openai_api_key": "sk-...",
  "anthropic_api_key": "sk-ant-..."
}
```

---

#### config/hardware_cache.json
**Purpose**: Detected hardware configuration  
**Created by**: scripts/bootstrap.sh

**Contains**:
- GPU type (cuda/rocm/mps/cpu)
- GPU memory
- CPU info
- Model cache paths

---

## Dependency Graph

### Bootstrap Flow
```
bootstrap.sh (root)
  └─> scripts/bootstrap.sh
       ├─> scripts/common-logging.sh
       ├─> config/secrets.json (optional)
       ├─> shared/hardware_detection.py
       ├─> shared/model_checker.py
       └─> shared/model_downloader.py
```

### Job Preparation Flow
```
prepare-job.sh (root)
  ├─> scripts/common-logging.sh
  └─> scripts/prepare-job.py
       ├─> shared/logger.py
       ├─> shared/environment_manager.py
       ├─> scripts/filename_parser.py
       ├─> scripts/config_loader.py
       └─> shared/stage_utils.py
```

### Pipeline Execution Flow
```
run-pipeline.sh (root)
  ├─> scripts/common-logging.sh
  └─> scripts/run-pipeline.py
       ├─> shared/logger.py
       ├─> shared/environment_manager.py
       ├─> shared/stage_utils.py
       ├─> scripts/config_loader.py
       │
       ├─> Stage 1: scripts/source_separation.py (venv/demucs)
       ├─> Stage 2: scripts/whisperx_asr.py (venv/whisperx)
       │            OR scripts/mlx_asr.py (venv/mlx)
       ├─> Stage 3: scripts/silero_vad.py (venv/common)
       │            OR scripts/pyannote_vad.py (venv/pyannote)
       ├─> Stage 4: scripts/diarization.py (venv/pyannote)
       ├─> Stage 5: scripts/mlx_alignment.py (venv/mlx)
       ├─> Stage 6: scripts/indictrans2_translator.py (venv/indictrans2)
       │            OR scripts/nllb_translator.py (venv/nllb)
       │            OR scripts/hybrid_translator.py (multiple)
       ├─> Stage 7: scripts/subtitle_gen.py (venv/common)
       ├─> Stage 8: scripts/ner_extraction.py (venv/common)
       ├─> Stage 9: scripts/glossary_builder.py (venv/common)
       │            └─> shared/glossary_generator.py
       ├─> Stage 10: scripts/bias_injection.py (multiple)
       │             └─> shared/bias_registry.py
       ├─> Stage 11: scripts/lyrics_detection.py (venv/common)
       ├─> Stage 12: scripts/hallucination_removal.py (venv/common)
       └─> Stage 13: scripts/subtitle_enhancement.py (venv/common)
```

### Comparison Tools Flow
```
compare-beam-search.sh
  ├─> scripts/common-logging.sh
  ├─> scripts/beam_search_comparison.py (venv/indictrans2)
  └─> scripts/indictrans2_translator.py (venv/indictrans2)
       └─> IndicTransToolkit ✅ Phase 1 fixed
```

---

## Virtual Environments

### Environment Summary

| Environment | Purpose | Key Packages | Size |
|-------------|---------|--------------|------|
| venv/common | Shared utilities | moviepy, pydub, spacy | ~500MB |
| venv/whisperx | WhisperX ASR | whisperx, faster-whisper | ~2GB |
| venv/mlx | MLX-Whisper (Apple) | mlx, mlx-whisper | ~1GB |
| venv/pyannote | Diarization & VAD | pyannote.audio | ~1GB |
| venv/demucs | Source separation | demucs | ~500MB |
| venv/indictrans2 | Indic translation | transformers, toolkit | ~3GB |
| venv/nllb | Non-Indic translation | transformers | ~3GB |
| venv/llm | LLM features (opt) | anthropic, openai | ~200MB |

**Total Disk Usage**: ~11GB (plus model caches)

---

### Environment Isolation Strategy

**Why Multiple Environments?**
1. **Dependency Conflicts**: Different PyTorch versions, CUDA compatibility
2. **Clean Separation**: Easier debugging and maintenance
3. **Selective Installation**: Install only what's needed
4. **Version Pinning**: Stable versions per component

**Trade-offs**:
- ✅ Reliable, conflict-free operation
- ✅ Easier dependency management
- ❌ Higher disk usage
- ❌ Longer bootstrap time

---

## Model Cache Structure

### HuggingFace Cache
**Location**: `~/.cache/huggingface/hub/`

**Models Cached by Bootstrap**:
```
models--openai--whisper-large-v3/
models--mlx-community--whisper-large-v3-mlx/ ✅ Phase 1 fixed
models--pyannote--speaker-diarization-3.1/
models--facebook--demucs-v4/
models--ai4bharat--indictrans2-indic-en-1B/
models--ai4bharat--indictrans2-indic-indic-1B/ ✅ Phase 2 added
models--facebook--nllb-200-3.3B/
```

**Total Cache Size**: ~15-20GB

---

### Torch Cache
**Location**: `~/.cache/torch/hub/`

**Contents**:
- Silero VAD models
- Custom model weights
- TorchScript compiled models

---

### MLX Cache
**Location**: `~/.cache/mlx/`

**Contents**:
- MLX-converted models
- Quantized weights
- Platform-specific optimizations

---

## Recent Changes Summary

### Phase 1 Fixes ✅

1. **MLX Model Caching** (scripts/bootstrap.sh:191)
   - Fixed: `load_model()` → `load_models()`
   - Impact: Bootstrap succeeds on Apple Silicon

2. **IndicTransToolkit Import** (scripts/indictrans2_translator.py:26-33)
   - Added: sys.path manipulation for venv
   - Impact: Translation and beam comparison work

3. **Pipeline Instructions** (scripts/prepare-job.py:689-691)
   - Added: "Next steps" output
   - Impact: Better user experience

4. **MLX Alignment** (scripts/mlx_alignment.py)
   - Status: Verified working correctly
   - Impact: Word-level timestamps functional

### Phase 2 Enhancements ✅

1. **Indic→Indic Model Caching** (scripts/bootstrap.sh:234)
   - Status: Already implemented
   - Impact: Offline cross-Indic translation

2. **Log Level CLI Arguments** (All scripts)
   - Status: Already implemented
   - Impact: Flexible logging control

3. **Beam Comparison Output** (compare-beam-search.sh)
   - Status: Already implemented
   - Impact: Quality optimization workflow

---

## Usage Patterns

### Complete Workflow Example

```bash
# 1. Bootstrap (one-time setup)
./bootstrap.sh --log-level INFO

# 2. Prepare job
./prepare-job.sh \
  --media movie.mp4 \
  --workflow subtitle \
  --source-language hi \
  --target-language en,ta,gu \
  --log-level DEBUG

# Output: Job ID and run command

# 3. Run pipeline
./run-pipeline.sh -j job-20251125-user-0001

# 4. Compare beam widths (optional)
./compare-beam-search.sh out/2025/11/25/user/1 --beam-range 4,10

# 5. View results
ls out/2025/11/25/user/1/subtitles/
```

---

## Troubleshooting

### Common Issues

**Issue**: Bootstrap fails  
**Check**: 
- Python 3.10+ installed
- Sufficient disk space (20GB+)
- Internet connectivity for downloads

**Issue**: Pipeline stage fails  
**Check**:
- Virtual environment activated correctly
- Model cached in `~/.cache/`
- Input files exist
- Log level set to DEBUG for details

**Issue**: Import errors  
**Check**:
- Correct virtual environment active
- Dependencies installed via bootstrap
- No conflicting system packages

**Issue**: Translation quality poor  
**Try**:
- Run beam comparison
- Check glossary files
- Verify input language correct
- Enable bias injection stage

---

## Documentation Files

**Related Documentation**:
- `COMPREHENSIVE_FIX_PLAN.md` - Complete fix plan
- `PHASES_1_2_COMPLETE.md` - Implementation summary
- `PHASE1_CRITICAL_FIXES_COMPLETE.md` - Phase 1 details
- `PHASE2_ENHANCEMENTS_STATUS.md` - Phase 2 details
- `README.md` - Project overview
- `docs/QUICKSTART.md` - Getting started guide
- `docs/user-guide/` - User documentation
- `docs/technical/` - Technical documentation

---

## Conclusion

This codebase uses a **multi-environment, stage-based architecture** to provide reliable, high-quality subtitle generation for Indian languages. The modular design allows for:

- **Flexibility**: Enable/disable stages as needed
- **Reliability**: Isolated environments prevent conflicts
- **Quality**: Multiple models and ensemble approaches
- **Offline Operation**: Pre-cached models
- **Maintainability**: Clear separation of concerns

**Recent Improvements**: Phase 1 & 2 fixes ensure all components work correctly with minimal changes to the codebase.

---

**End of Dependency Map**
