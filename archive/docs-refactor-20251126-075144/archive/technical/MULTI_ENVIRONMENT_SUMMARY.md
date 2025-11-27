# Multi-Environment Solution - Implementation Summary

## Problem Statement

WhisperX and IndicTrans2 have **conflicting dependency requirements**:

- **WhisperX**: `numpy < 2.1`, `torch ~= 2.0.0`
- **IndicTrans2**: `numpy >= 2.1`, `torch >= 2.5.0`

These cannot coexist in a single Python environment.

## Solution: Three Isolated Environments

### Environment 1: whisperx (venv/whisperx)
- **Purpose**: Audio transcription
- **Stages**: demux, asr, alignment, export_transcript
- **Key Deps**: whisperx 3.1.1, torch 2.0, numpy < 2.1

### Environment 2: indictrans2 (venv/indictrans2)
- **Purpose**: Translation
- **Stages**: All indictrans2_translation_* stages
- **Key Deps**: IndicTransToolkit, torch 2.5+, numpy 2.1+

### Environment 3: common (venv/common)
- **Purpose**: Utilities
- **Stages**: subtitle_generation_*, mux
- **Key Deps**: ffmpeg-python, pydantic (no ML)

## Files Created

1. **config/hardware_cache.json**
   - Defines all environments
   - Maps stages to environments
   - Maps workflows to required environments

2. **bootstrap.sh**
   - Creates all virtual environments
   - Installs dependencies per environment
   - Validates installations

3. **shared/environment_manager.py**
   - Python API for environment management
   - Used by pipeline to switch environments
   - Validates environments before running

4. **requirements-whisperx.txt**
   - WhisperX-compatible dependencies

5. **requirements-indictrans2.txt**
   - IndicTrans2-compatible dependencies

6. **requirements-common.txt**
   - Lightweight utility dependencies

7. **docs/MULTI_ENVIRONMENT_ARCHITECTURE.md**
   - Complete architecture documentation

## How It Works

### Setup Phase
```bash
./bootstrap.sh  # Creates all 3 environments
```

### Job Preparation
```bash
./prepare-job.sh movie.mp4 --subtitle -s hi -t en
```
- Reads hardware_cache.json
- Validates required environments exist
- Stores environment info in job.json

### Pipeline Execution
```bash
./run-pipeline.sh -j <job-id>
```
- For each stage:
  1. Lookup environment from job config
  2. Activate that environment
  3. Run stage
  4. Deactivate environment

### Example Flow (Subtitle Workflow)
```
demux           → venv/whisperx    (audio extraction)
asr             → venv/whisperx    (transcription)
translation_en  → venv/indictrans2 (translate)
subtitle_gen_en → venv/common      (SRT file)
mux             → venv/common      (video embedding)
```

## Key Benefits

✅ **No Conflicts**: Each environment has compatible versions
✅ **Automatic**: Pipeline switches environments per stage
✅ **Transparent**: No changes to user workflow
✅ **Maintainable**: Easy to update environments independently
✅ **Scalable**: Easy to add new environments

## Usage

### First-Time Setup
```bash
# Install all environments
./bootstrap.sh

# Check status
./bootstrap.sh --check
```

### Regular Use
```bash
# Works exactly as before!
./prepare-job.sh movie.mp4 --subtitle -s hi -t en
./run-pipeline.sh -j <job-id>
```

### Maintenance
```bash
# Rebuild specific environment
./bootstrap.sh --clean
./bootstrap.sh --env whisperx

# Check environments
python shared/environment_manager.py list
```

## Migration from Old Setup

```bash
# Remove old single environment
rm -rf .bollyenv

# Create new multi-environments
./bootstrap.sh

# Continue using as before
# Pipeline automatically uses correct environments
```

## Next Steps

1. **Run bootstrap.sh** to create environments
2. **Test with a job** to verify it works
3. **Update any documentation** that references .bollyenv

## Implementation Status

✅ Hardware cache configuration
✅ Bootstrap script with environment creation
✅ Environment manager Python API
✅ Requirements files for each environment
✅ Complete architecture documentation
⏳ Pipeline integration (needs update to run-pipeline.py)
⏳ Job preparation integration (needs update to prepare-job.py)

The foundation is complete - next step is integrating the environment manager into the pipeline orchestrator.
