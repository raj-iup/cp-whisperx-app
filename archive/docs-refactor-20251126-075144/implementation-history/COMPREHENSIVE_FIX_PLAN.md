# Comprehensive Fix Plan - CP-WhisperX-App
## Analysis Date: 2025-11-25

---

## Issues Identified

### 1. MLX Whisper Model Loading Error ❌
**Problem**: `module 'mlx_whisper' has no attribute 'load_model'`
**Location**: `scripts/bootstrap.sh` line 166-189
**Root Cause**: Incorrect API usage - mlx_whisper uses `transcribe()` not `load_model()`
**Impact**: Bootstrap fails to cache MLX models

### 2. Empty 05_alignment Directory ❌
**Problem**: `/out/2025/11/24/1/1/05_alignment` is empty
**Root Cause**: MLX backend in `scripts/mlx_alignment.py` only verifies existing alignment, doesn't create it
**Impact**: Bias injection windows aren't optimized for MLX transcriptions

### 3. compare-beam-search.sh Failures ❌
**Problem**: Translation fails with "IndicTransToolkit not available" warning
**Root Cause**: Import path issue - toolkit installed but not found
**Impact**: Cannot compare beam search quality across 4-10 widths

### 4. Missing Pipeline Run Instruction ❌
**Problem**: prepare-job.sh doesn't output "Run pipeline: ./run-pipeline.sh -j <job-id>"
**Location**: `prepare-job.sh` and `scripts/prepare-job.py`
**Impact**: User doesn't know how to start pipeline after job prep

### 5. IndicTrans2 Indic→Indic Model Not Cached ⚠️
**Problem**: Bootstrap only caches Indic→English model
**Missing**: `ai4bharat/indictrans2-indic-indic-1B`
**Impact**: Indic→Indic translations (hi→ta, etc.) will download on first use

### 6. Log Level as Environment Variable ⚠️
**Problem**: Log level set via `LOG_LEVEL` env var, not CLI arg
**Impact**: Less user-friendly, harder to set per-invocation

---

## Implementation Plan

### Phase 1: Critical Fixes (2-3 hours)

#### 1.1 Fix MLX Model Caching
**File**: `scripts/bootstrap.sh`
**Changes**:
```bash
# Replace cache_mlx_model function (lines 160-189)
cache_mlx_model() {
    log_section "Caching: MLX Whisper Model (Apple Silicon)"
    log_info "Model: mlx-community/whisper-large-v3-mlx"
    log_info "Environment: venv/mlx"
    log_info "Size: ~3GB"
    
    # Check if model already cached
    local MLX_CACHE="$HF_HOME/hub/models--mlx-community--whisper-large-v3-mlx"
    if [ -d "$MLX_CACHE" ]; then
        log_success "MLX model already cached"
        return 0
    fi
    
    log_info "Downloading MLX model (5-10 minutes)..."
    source "$PROJECT_ROOT/venv/mlx/bin/activate"
    
    python3 << 'PYEOF'
import mlx_whisper
# The model downloads automatically on first transcribe() call
# Force download by calling load_models helper
from mlx_whisper import load_models
load_models("mlx-community/whisper-large-v3-mlx")
print("✓ MLX model cached successfully")
PYEOF
    
    deactivate
}
```

#### 1.2 Implement MLX Alignment
**File**: `scripts/mlx_alignment.py`
**Current**: Only verifies existing alignment
**New**: Perform actual word-level alignment using mlx_whisper

**Changes**:
```python
def align_mlx_segments(segments, audio_path, language, device="mps"):
    """Perform actual word-level alignment for MLX transcriptions"""
    import mlx_whisper
    
    # Load MLX model with alignment task
    model_name = "mlx-community/whisper-large-v3-mlx"
    
    # Transcribe with word timestamps
    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hf_repo=model_name,
        word_timestamps=True,  # Enable word-level timestamps
        language=language
    )
    
    # Merge word timestamps into segments
    aligned_segments = []
    for segment in segments:
        # Find matching words from MLX output
        words = find_words_in_segment(result['segments'], segment)
        segment['words'] = words
        aligned_segments.append(segment)
    
    return {"segments": aligned_segments, "word_segments": aligned_segments}
```

#### 1.3 Fix IndicTransToolkit Import
**File**: `scripts/indictrans2_translator.py`
**Add at top**:
```python
import sys
from pathlib import Path

# Ensure toolkit is importable
toolkit_path = Path(__file__).parent.parent / "venv/indictrans2" / "lib"
python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
site_packages = toolkit_path / python_version / "site-packages"
if site_packages.exists():
    sys.path.insert(0, str(site_packages))
```

#### 1.4 Add Pipeline Run Instruction
**File**: `scripts/prepare-job.py`
**Add at end of main()**:
```python
    # Print success message with next steps
    logger.info("")
    logger.section("JOB PREPARATION COMPLETE")
    logger.success(f"Job ID: {job_id}")
    logger.success(f"Job directory: {job_dir}")
    logger.info("")
    logger.info("Next steps:")
    logger.info(f"  1. Run pipeline: ./run-pipeline.sh -j {job_id}")
    logger.info(f"  2. Monitor logs: tail -f {job_dir}/logs/*.log")
    logger.info(f"  3. Check status: ./scripts/pipeline-status.sh -j {job_id}")
    logger.info("")
```

### Phase 2: Enhancements (2-3 hours)

#### 2.1 Cache Indic→Indic Model Automatically
**File**: `scripts/bootstrap.sh`
**Add after IndicTrans2 Indic→English caching**:
```bash
# Cache Indic→Indic model (for hi→ta, etc.)
log_info ""
log_info "Caching IndicTrans2 Indic→Indic model..."
cache_hf_model \
    "ai4bharat/indictrans2-indic-indic-1B" \
    "indictrans2" \
    "IndicTrans2 Indic→Indic Translation"
```

#### 2.2 Add Log Level CLI Arguments
**Files**: `bootstrap.sh`, `prepare-job.sh`, `run-pipeline.sh`

**bootstrap.sh**:
```bash
# Add after argument parsing
--log-level)
    LOG_LEVEL="$2"
    shift 2
    ;;
```

**prepare-job.sh**:
```bash
# Add to show_usage()
  --log-level LEVEL            Set log level: DEBUG, INFO, WARN, ERROR, CRITICAL (default: INFO)

# Add to argument parsing
--log-level)
    LOG_LEVEL="$2"
    shift 2
    ;;

# Pass to Python script
"$COMMON_PYTHON" "$PREPARE_JOB_SCRIPT" \\
    --log-level "${LOG_LEVEL:-INFO}" \\
    ...
```

**scripts/prepare-job.py**:
```python
parser.add_argument(
    '--log-level',
    choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'],
    default='INFO',
    help='Logging level (default: INFO)'
)

# Use it
logger = PipelineLogger("prepare-job", log_level=args.log_level)
```

#### 2.3 Implement Beam Comparison Output
**File**: `compare-beam-search.sh`
**Enhancement**: Generate outputs for each beam width 4-10

Already implemented - just needs the IndicTransToolkit fix from 1.3

### Phase 3: Documentation (1 hour)

#### 3.1 Create Codebase Dependency Map
**File**: `CODEBASE_DEPENDENCY_MAP.md`

```markdown
# Codebase Dependency Map

## Bootstrap Scripts

### bootstrap.sh (root)
- **Type**: Wrapper script
- **Dependencies**: 
  - scripts/bootstrap.sh (actual implementation)
- **Config**: None
- **Requirements**: None

### scripts/bootstrap.sh
- **Type**: Main bootstrap implementation
- **Dependencies**:
  - scripts/common-logging.sh
- **Config**:
  - config/secrets.json (optional - for HF/API tokens)
  - config/hardware_cache.json (created)
- **Requirements**:
  - requirements-common.txt
  - requirements-whisperx.txt
  - requirements-mlx.txt
  - requirements-pyannote.txt
  - requirements-demucs.txt
  - requirements-indictrans2.txt
  - requirements-nllb.txt
  - requirements-llm.txt
- **Creates**:
  - venv/common/
  - venv/whisperx/
  - venv/mlx/
  - venv/pyannote/
  - venv/demucs/
  - venv/indictrans2/
  - venv/nllb/
  - venv/llm/
  - .cache/huggingface/
  - .cache/torch/
  - .cache/mlx/

## Prepare Job Scripts

### prepare-job.sh (root)
- **Type**: Wrapper + validation
- **Dependencies**:
  - scripts/prepare-job.py (main implementation)
  - scripts/common-logging.sh
- **Config**:
  - config/.env.pipeline (template)
  - config/secrets.json
- **Requirements**: None (uses venv/common)
- **Output**: Job directory in out/YYYY/MM/DD/USER_ID/JOB_NUM/

### scripts/prepare-job.py
- **Type**: Job preparation logic
- **Dependencies**:
  - shared/logger.py
  - shared/environment_manager.py
  - scripts/filename_parser.py
  - scripts/config_loader.py
- **Config**:
  - config/.env.pipeline
  - config/secrets.json
- **Requirements**: requirements-common.txt
- **Creates**:
  - {job_dir}/config/job.json
  - {job_dir}/manifest.json

## Pipeline Scripts

### run-pipeline.sh (root)
- **Type**: Wrapper + orchestration
- **Dependencies**:
  - scripts/run-pipeline.py (main implementation)
  - scripts/common-logging.sh
- **Config**:
  - {job_dir}/config/job.json
- **Requirements**: None (uses multiple venvs)

### scripts/run-pipeline.py
- **Type**: Main pipeline orchestrator
- **Dependencies**:
  - shared/logger.py
  - shared/environment_manager.py
  - scripts/config_loader.py
  - scripts/whisper_backends.py
  - scripts/mlx_alignment.py
  - scripts/source_separation.py
  - scripts/diarization.py
  - scripts/whisperx_asr.py
  - scripts/indictrans2_translator.py
  - scripts/nllb_translator.py
  - scripts/hybrid_translator.py
  - scripts/subtitle_gen.py
  - scripts/ner_extraction.py
  - scripts/glossary_builder.py
  - scripts/bias_injection.py
  - scripts/lyrics_detection.py
  - ... (many more)
- **Config**:
  - {job_dir}/config/job.json
  - glossary/*.txt
- **Requirements**: All requirements-*.txt files
- **Output**: Full pipeline outputs in job_dir/

## Utility Scripts

### scripts/common-logging.sh
- **Type**: Shared logging functions
- **Used by**:
  - bootstrap.sh
  - prepare-job.sh
  - run-pipeline.sh
  - compare-beam-search.sh
  - All shell scripts
- **Functions**:
  - log_debug, log_info, log_warn, log_error, log_critical
  - log_section, log_success
  - setup_logging

### shared/logger.py
- **Type**: Python logging infrastructure
- **Used by**:
  - prepare-job.py
  - run-pipeline.py
  - All Python pipeline scripts
- **Features**:
  - Structured logging
  - Multiple output formats
  - Log level control

## Comparison Tools

### compare-beam-search.sh
- **Type**: Beam search quality comparison
- **Dependencies**:
  - scripts/common-logging.sh
  - scripts/beam_search_comparison.py
  - scripts/indictrans2_translator.py
- **Config**: Uses job directory
- **Requirements**: requirements-indictrans2.txt
- **Output**: {job_dir}/beam_comparison/

## Configuration Files

### requirements-common.txt
- **Used by**: venv/common
- **Packages**: moviepy, pydub, spacy, etc.

### requirements-whisperx.txt
- **Used by**: venv/whisperx
- **Packages**: whisperx, faster-whisper

### requirements-mlx.txt
- **Used by**: venv/mlx
- **Packages**: mlx, mlx-whisper

### requirements-pyannote.txt
- **Used by**: venv/pyannote
- **Packages**: pyannote.audio

### requirements-demucs.txt
- **Used by**: venv/demucs
- **Packages**: demucs

### requirements-indictrans2.txt
- **Used by**: venv/indictrans2
- **Packages**: transformers, IndicTransToolkit

### requirements-nllb.txt
- **Used by**: venv/nllb
- **Packages**: transformers, sentencepiece

### requirements-llm.txt
- **Used by**: venv/llm
- **Packages**: anthropic, openai

## Inter-Script Dependencies

```
bootstrap.sh
  └─> scripts/bootstrap.sh
       ├─> scripts/common-logging.sh
       └─> config/secrets.json

prepare-job.sh
  ├─> scripts/common-logging.sh
  └─> scripts/prepare-job.py
       ├─> shared/logger.py
       ├─> shared/environment_manager.py
       ├─> scripts/filename_parser.py
       └─> scripts/config_loader.py

run-pipeline.sh
  ├─> scripts/common-logging.sh
  └─> scripts/run-pipeline.py
       ├─> shared/logger.py
       ├─> scripts/*_asr.py
       ├─> scripts/*_translator.py
       ├─> scripts/*_detection.py
       └─> scripts/subtitle_gen.py

compare-beam-search.sh
  ├─> scripts/common-logging.sh
  ├─> scripts/beam_search_comparison.py
  └─> scripts/indictrans2_translator.py
```
```

---

## Testing Plan

### Test 1: Bootstrap with Model Caching
```bash
./bootstrap.sh --force --log-level DEBUG
# Should successfully cache all models including MLX
```

### Test 2: Job Preparation
```bash
./prepare-job.sh --media test.mp4 --workflow subtitle \\
  --source-language hi --target-language en --log-level INFO
# Should output "Run pipeline: ./run-pipeline.sh -j <job-id>"
```

### Test 3: Pipeline with MLX + Alignment
```bash
./run-pipeline.sh -j <job-id> --log-level DEBUG
# Should create 05_alignment directory with word-level timestamps
```

### Test 4: Beam Search Comparison
```bash
./compare-beam-search.sh out/YYYY/MM/DD/USER/JOB --beam-range 4,6
# Should successfully run without IndicTransToolkit warnings
```

---

## Priority Order

1. **CRITICAL**: Fix MLX model caching (blocks bootstrap)
2. **CRITICAL**: Fix IndicTransToolkit import (blocks beam comparison)
3. **HIGH**: Add pipeline run instruction (UX improvement)
4. **HIGH**: Implement MLX alignment (quality improvement)
5. **MEDIUM**: Add log-level CLI args (UX improvement)
6. **MEDIUM**: Cache Indic→Indic model (offline capability)
7. **LOW**: Documentation (reference)

---

## Estimated Time
- **Phase 1 (Critical)**: 2-3 hours
- **Phase 2 (Enhancements)**: 2-3 hours
- **Phase 3 (Documentation)**: 1 hour
- **Total**: 5-7 hours

---

## Next Steps

Ready to implement? Please confirm which phase(s) to start with:
- [ ] Phase 1: Critical Fixes
- [ ] Phase 2: Enhancements  
- [ ] Phase 3: Documentation
- [ ] All phases

