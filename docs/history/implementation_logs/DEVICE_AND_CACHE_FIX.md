# Device Configuration and Cache Directory Fix

**Date:** 2025-11-08  
**Job ID:** 20251108-0002

## Issues Fixed

### 1. Device Mode Detection (Log Lines 6, 174, 223, 5448)
**Problem:** Orchestrator showed `Device mode: CPU` instead of `MPS` throughout the pipeline.

**Root Cause:** The job environment file (`.20251108-0002.env`) was missing the global `DEVICE` configuration variable.

**Solution Implemented:**
- Added `DEVICE` field to `shared/config.py` PipelineConfig class
- Updated `scripts/prepare-job.py` template to include `DEVICE` setting
- Updated device configuration logic in prepare-job.py to set `DEVICE` from `hardware_cache.json`
- Updated job `.env` file to include `DEVICE=mps`

### 2. Cache Directory Errors (Log Lines 5475+)
**Problem:** Native execution failed with:
```
OSError: [Errno 30] Read-only file system: '/app'
FileNotFoundError: [Errno 2] No such file or directory: '/app/LLM/whisperx'
```

**Root Cause:** Scripts attempted to use Docker-specific paths (`/app/LLM/`) when running in native mode.

**Solution Implemented:**
- Bootstrap scripts (`bootstrap.sh` and `bootstrap.ps1`) now create and export cache directories
- All pipeline and resume scripts activate venv and export cache environment variables
- ML model scripts use `TORCH_HOME` and `HF_HOME` environment variables set by bootstrap
- Cache directories are consistently located at `.cache/torch` and `.cache/huggingface`

## Architecture & Data Flow

### Hardware Detection Flow
```
bootstrap.sh/ps1
    ↓
shared/hardware_detection.py
    ↓
out/hardware_cache.json (cached, valid 1 hour)
    ↓
prepare-job.py (reads cache)
    ↓
job/.env file (DEVICE=mps)
    ↓
pipeline.py (reads from job .env)
    ↓
ML stages (use device from config)
```

### Cache Directory Flow
```
bootstrap.sh/ps1
    ↓
Creates: .cache/torch, .cache/huggingface
Exports: TORCH_HOME, HF_HOME
    ↓
run_pipeline.sh/ps1, resume-pipeline.sh/ps1
    ↓
Activates: .bollyenv
Exports: TORCH_HOME, HF_HOME
    ↓
ML scripts (whisperx, pyannote, silero)
    ↓
Use: os.environ['TORCH_HOME'], os.environ['HF_HOME']
```

## Files Modified

### 1. Configuration & Core
**shared/config.py**
- Added `device: str = Field(default="cpu", env="DEVICE")` for global device configuration

**scripts/prepare-job.py**
- Added `DEVICE=cpu` to configuration template
- Added device configuration logic to set `DEVICE` from hardware_cache.json
- Device value is read from hardware detection and written to job .env file

### 2. Bootstrap Scripts (Cache Management)
**scripts/bootstrap.sh**
- Creates `.cache/torch` and `.cache/huggingface` directories
- Exports `TORCH_HOME` and `HF_HOME` environment variables

**scripts/bootstrap.ps1**
- Creates `.cache\torch` and `.cache\huggingface` directories
- Sets `$env:TORCH_HOME` and `$env:HF_HOME` environment variables

### 3. Pipeline Orchestration Scripts
**run_pipeline.sh**
- Activates `.bollyenv` virtual environment
- Exports `TORCH_HOME` and `HF_HOME` before running pipeline

**run_pipeline.ps1**
- Activates `.bollyenv` virtual environment
- Sets `$env:TORCH_HOME` and `$env:HF_HOME` before running pipeline

**resume-pipeline.sh**
- Activates `.bollyenv` virtual environment
- Exports `TORCH_HOME` and `HF_HOME` before resuming pipeline

**resume-pipeline.ps1**
- Activates `.bollyenv` virtual environment
- Sets `$env:TORCH_HOME` and `$env:HF_HOME` before resuming pipeline

### 4. ML Model Scripts
**scripts/whisperx_integration.py**
- Uses `os.environ.get('TORCH_HOME')` instead of hardcoded path
- Respects cache directory set by bootstrap

**docker/pyannote-vad/pyannote_vad.py**
- Uses `os.environ.get('HF_HOME')` and `os.environ.get('TORCH_HOME')`
- Respects cache directories set by bootstrap

**docker/silero-vad/silero_vad.py**
- Uses `os.environ.get('TORCH_HOME')` instead of hardcoded path
- Respects cache directory set by bootstrap

### 5. Job Configuration
**out/2025/11/08/1/20251108-0002/.20251108-0002.env**
- Added `DEVICE=mps` configuration

## How to Resume the Pipeline

### Prerequisites
Ensure bootstrap has been run to set up cache directories:
```bash
# If not already done
./scripts/bootstrap.sh
```

### Option 1: Resume from ASR Stage (Recommended)
The pipeline failed during ASR. Previous stages (demux, tmdb, pre_ner, silero_vad, diarization) completed successfully:

```bash
./resume-pipeline.sh 20251108-0002
```

This automatically:
- Activates `.bollyenv` virtual environment
- Sets `TORCH_HOME` and `HF_HOME` environment variables
- Detects last completed stage and resumes from there

### Option 2: Resume Specific Stages
```bash
# Resume from ASR stage only
./.bollyenv/bin/python scripts/pipeline.py --job-id 20251108-0002 --stages asr

# Or run multiple stages
./.bollyenv/bin/python scripts/pipeline.py --job-id 20251108-0002 --stages asr,second_pass_translation,lyrics_detection,post_ner,subtitle_gen,mux
```

### Option 3: Check Pipeline Status First
```bash
./scripts/pipeline-status.sh 20251108-0002
```

## Expected Behavior After Fix

1. **Device Detection:**
   - Orchestrator shows: `Device mode: MPS`
   - Each ML stage reports: `Device: MPS` (not CPU)
   - No MPS-related warnings appear

2. **Cache Directories:**
   - Models cache in `.cache/torch` and `.cache/huggingface`
   - No read-only filesystem errors
   - Cache persists across runs (faster subsequent runs)
   - Bootstrap, prepare-job, and pipeline scripts all use same cache locations

3. **ASR Stage:**
   - WhisperX loads successfully with MPS device
   - Models run on Apple Silicon GPU
   - Processing significantly faster than CPU mode

## Verification Steps

After resuming:

1. **Check device detection in new log:**
   ```bash
   tail -100 out/2025/11/08/1/20251108-0002/logs/00_orchestrator_*.log | grep -i device
   ```
   Should show: `Device mode: MPS`

2. **Verify cache directories exist:**
   ```bash
   ls -la .cache/
   ```
   Should show: `torch/` and `huggingface/` directories

3. **Monitor ASR stage execution:**
   ```bash
   tail -f out/2025/11/08/1/20251108-0002/logs/00_orchestrator_*.log
   ```

4. **Verify model cache (after models download):**
   ```bash
   du -sh .cache/torch
   du -sh .cache/huggingface
   ```

## For Future Jobs

### New Job Creation
When creating new jobs with `./prepare-job.sh`:
- `DEVICE` is automatically set from `out/hardware_cache.json`
- On macOS with Apple Silicon: `DEVICE=mps`
- On Linux with NVIDIA GPU: `DEVICE=cuda`
- Fallback: `DEVICE=cpu`

### Cache Directories
- Bootstrap automatically creates and configures cache directories
- All pipeline runs use the same cache (no duplication)
- Models download once and are reused across all jobs

### Environment Setup
Bootstrap script (`./scripts/bootstrap.sh` or `.\scripts\bootstrap.ps1`) handles:
1. Virtual environment creation (`.bollyenv`)
2. Dependency installation
3. Hardware detection and caching
4. Cache directory creation
5. Environment variable configuration

## Troubleshooting

### If pipeline still shows CPU
1. Check hardware cache:
   ```bash
   cat out/hardware_cache.json | grep gpu_type
   ```

2. Check job env file:
   ```bash
   grep "^DEVICE=" out/2025/11/08/1/20251108-0002/.20251108-0002.env
   ```

3. If missing or wrong, manually edit the env file:
   ```bash
   # Add or update around line 95:
   DEVICE=mps
   ```

### If cache directory errors persist
1. Verify bootstrap was run:
   ```bash
   ls -la .cache/
   ```

2. Re-run bootstrap if needed:
   ```bash
   ./scripts/bootstrap.sh
   ```

3. Verify environment variables in pipeline script:
   ```bash
   # Should see TORCH_HOME and HF_HOME exports
   grep -A5 "Set cache directories" run_pipeline.sh
   ```

### If models fail to load
1. Check disk space (WhisperX large-v3 needs ~3GB):
   ```bash
   df -h .
   ```

2. Check cache permissions:
   ```bash
   ls -la .cache/
   chmod 755 .cache/torch .cache/huggingface
   ```

3. Check HuggingFace token (for PyAnnote models):
   ```bash
   cat config/secrets.json | grep HF_TOKEN
   ```

## Benefits of This Architecture

1. **Centralized Control:** Bootstrap manages all cache directories
2. **Consistency:** Same cache paths for Docker and native modes
3. **No Duplication:** Models download once, shared across all jobs
4. **Hardware Detection:** Device configuration comes from hardware_cache.json
5. **Cross-Platform:** Works on macOS, Windows, and Linux with same logic
6. **Maintainable:** Single source of truth for cache and device configuration
