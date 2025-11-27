# IndicTrans2 Workflow Architecture

## Last Updated
**Date**: November 18, 2025  
**Time**: 15:21 UTC

## Overview

The IndicTrans2 workflow follows a clean **3-step architecture** with complete separation of concerns:

1. **Bootstrap** (once per system)
2. **Prepare Job** (once per media file)
3. **Run Pipeline** (once per job)

---

## Step 1: Bootstrap

### Purpose
Detect hardware capabilities and generate optimized configuration.

### Command
```bash
./scripts/bootstrap.sh
```

### What It Does
1. Detects CPU, GPU, memory
2. Runs `shared/hardware_detection.py`
3. Generates `out/hardware_cache.json`

### Output
**File**: `out/hardware_cache.json`

**Example** (Apple M1 Pro):
```json
{
  "detected_at": "2025-11-17T11:39:00",
  "platform": "Darwin",
  "gpu_type": "mps",
  "gpu_name": "Apple M1 Pro",
  "gpu_memory_gb": 10.0,
  "recommended_settings": {
    "whisper_model": "large-v3",
    "compute_type": "float16",
    "batch_size": 2,
    "whisper_backend": "mlx"
  }
}
```

### Frequency
- **Once** per system
- Re-run if hardware changes
- Re-run after system upgrades

---

## Step 2: Prepare Job

### Purpose
Create job directory structure and inject hardware-optimized configuration.

### Command
```bash
./prepare-job.sh "movie.mp4" --transcribe --source-language hi
```

### Components

#### Shell Wrapper: `prepare-job.sh`
- Validates environment (.bollyenv exists)
- Validates command-line arguments
- Calls Python script
- Displays job information

#### Python Logic: `scripts/prepare-job.py`
- **Reads** `out/hardware_cache.json`
- **Reads** `config/.env.pipeline` template
- **Creates** job directory
- **Creates** job configuration files
- **Injects** hardware settings

### What It Creates

**Directory Structure**:
```
out/
└── 2025-11-18_07-37-57/              ← Timestamp
    └── rpatel/                         ← Username
        └── job-id/                     ← Unique job ID
            ├── .job-id.env             ← Job configuration (★ KEY FILE)
            ├── job.json                ← Job metadata
            ├── manifest.json           ← Stage tracking
            ├── logs/                   ← Pipeline logs
            ├── media/                  ← Input media
            │   ├── input.mp4           ← Original file
            │   └── audio.wav           ← Extracted audio (created by demux)
            ├── transcripts/            ← Transcription outputs
            │   ├── segments.json       ← ASR results
            │   └── segments_translated.json  ← Translated (if translate workflow)
            └── subtitles/              ← Subtitle outputs
                └── output.en.srt       ← Final subtitles (if translate workflow)
```

### Key File: `.job-id.env`

This file contains **ALL configuration** the pipeline needs:

```bash
# Job Identification
JOB_ID=hindi-movie-20251118-073757
USER_ID=rpatel
WORKFLOW_MODE=transcribe
TITLE=Hindi Movie
YEAR=2008

# Paths
IN_ROOT=/path/to/job/media/input.mp4
OUTPUT_ROOT=/path/to/job
LOG_ROOT=/path/to/job/logs

# Hardware-Injected Settings (from hardware_cache.json)
WHISPERX_DEVICE=mps                  ← From gpu_type
WHISPER_MODEL=large-v3               ← From recommended_settings.whisper_model
WHISPER_COMPUTE_TYPE=float16         ← From recommended_settings.compute_type
BATCH_SIZE=2                         ← From recommended_settings.batch_size
WHISPER_BACKEND=mlx                  ← From recommended_settings.whisper_backend
WHISPER_LANGUAGE=hi                  ← From command-line --source-language

# Applied to All Stages
SILERO_DEVICE=mps
PYANNOTE_DEVICE=mps
DIARIZATION_DEVICE=mps
INDICTRANS2_DEVICE=mps

# IndicTrans2 Settings (from config/.env.pipeline)
INDICTRANS2_MODEL=ai4bharat/indictrans2-indic-en-1B
INDICTRANS2_NUM_BEAMS=4
INDICTRANS2_MAX_NEW_TOKENS=128

# ... (full .env.pipeline template with injected values)
```

### Configuration Injection

**Function**: `create_env_file()` in `scripts/prepare-job.py`

**Process**:
1. Load `out/hardware_cache.json`
2. Extract GPU type and recommended settings
3. Load `config/.env.pipeline` template
4. Replace template values with:
   - Hardware-detected settings
   - Command-line parameters
   - Job-specific paths
5. Write to `.job-id.env`

**Code Snippet**:
```python
# Extract hardware settings
gpu_type = hardware_config.get("gpu_type", "cpu")
recommended = hardware_config.get("recommended_settings", {})
whisper_model = recommended.get("whisper_model", "large-v2")
compute_type = recommended.get("compute_type", "int8")
batch_size = recommended.get("batch_size", 16)

# Create replacements
replacements = {
    "WHISPER_MODEL=large-v3": f"WHISPER_MODEL={whisper_model}",
    "WHISPER_COMPUTE_TYPE=float16": f"WHISPER_COMPUTE_TYPE={compute_type}",
    "BATCH_SIZE=2": f"BATCH_SIZE={batch_size}",
    "WHISPERX_DEVICE=mps": f"WHISPERX_DEVICE={gpu_type}",
    # ... more replacements
}
```

### Frequency
- **Once per media file** for each workflow
- Transcribe workflow: 1 job
- Translate workflow: 1 job (separate)

---

## Step 3: Run Pipeline

### Purpose
Execute workflow stages using job configuration.

### Command
```bash
./run-pipeline.sh -j job-id
```

### Components

#### Shell Wrapper: `run-pipeline.sh`
- Finds job directory by job ID
- Validates .bollyenv exists
- Calls Python orchestrator
- Displays results

#### Python Orchestrator: `scripts/run-pipeline.py`
- **Reads ONLY** job's `.job-id.env` file
- **Does NOT** access `hardware_cache.json`
- **Does NOT** access `config/.env.pipeline`
- **Has NO** hardcoded values

### Configuration Loading

**Function**: `_load_env_config()` in `scripts/run-pipeline.py`

```python
def _load_env_config(self) -> Dict[str, str]:
    """Load job-specific .env file created by prepare-job"""
    job_id = self.job_config["job_id"]
    env_file = self.job_dir / f".{job_id}.env"
    
    config = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key] = value
    
    return config
```

### Stage Execution

#### ASR Stage Example

```python
def _stage_asr(self) -> bool:
    # Get ALL settings from job's .env
    device = self.env_config.get("WHISPERX_DEVICE", "cpu")
    model = self.env_config.get("WHISPER_MODEL", "large-v2")
    compute_type = self.env_config.get("WHISPER_COMPUTE_TYPE", "int8")
    batch_size = int(self.env_config.get("BATCH_SIZE", "16"))
    
    # Log what was loaded (for debugging)
    self.logger.info(f"Using device: {device} (from job config)")
    self.logger.info(f"Using model: {model} (from job config)")
    
    # Execute with loaded settings
    # ... (no hardcoded values)
```

#### IndicTrans2 Stage Example

```python
def _stage_indictrans2_translation(self) -> bool:
    # Get ALL settings from job's .env
    device = self.env_config.get("INDICTRANS2_DEVICE", "cpu")
    model = self.env_config.get("INDICTRANS2_MODEL", "...")
    num_beams = self.env_config.get("INDICTRANS2_NUM_BEAMS", "4")
    
    # Execute with loaded settings
    # ... (no hardcoded values)
```

### Workflows

#### Transcribe Workflow
**Stages**: demux → asr → alignment

1. **Demux**: Extract audio from video
   - Input: `media/input.mp4`
   - Output: `media/audio.wav`
   - Uses: ffmpeg (CPU-only)

2. **ASR**: Transcribe audio
   - Input: `media/audio.wav`
   - Output: `transcripts/segments.json`
   - Uses: WhisperX with job-configured settings

3. **Alignment**: Verify timestamps
   - Input: `transcripts/segments.json`
   - Output: Validated segments
   - Uses: Built into WhisperX

#### Translate Workflow
**Stages**: load_transcript → indictrans2_translation → subtitle_generation

1. **Load Transcript**: Load segments
   - Input: `transcripts/segments.json`
   - Output: Loaded in memory

2. **IndicTrans2 Translation**: Translate text
   - Input: Segments in memory
   - Output: `transcripts/segments_translated.json`
   - Uses: IndicTrans2 with job-configured settings

3. **Subtitle Generation**: Create SRT
   - Input: `transcripts/segments_translated.json`
   - Output: `subtitles/output.en.srt`
   - Uses: Custom SRT generator

### Frequency
- **Once per job**
- Can be run multiple times (idempotent if stages succeed)
- Can resume with `--resume` flag

---

## Configuration Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ BOOTSTRAP (Once Per System)                                     │
│ ./scripts/bootstrap.sh                                          │
├─────────────────────────────────────────────────────────────────┤
│ Detects: CPU, GPU, Memory                                       │
│ Generates: out/hardware_cache.json                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ PREPARE JOB (Once Per Media File)                               │
│ ./prepare-job.sh movie.mp4 --transcribe -s hi      │
├─────────────────────────────────────────────────────────────────┤
│ Reads:                                                           │
│   ✓ out/hardware_cache.json                                     │
│   ✓ config/.env.pipeline                                        │
│                                                                  │
│ Creates:                                                         │
│   ✓ out/YYYY/MM/DD/USERID/counter/                             │
│   ✓ .job-YYYYMMDD-USERID-nnnn.env (★ with hardware settings)   │
│   ✓ job.json (contains job_id)                                 │
│   ✓ manifest.json                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ RUN PIPELINE (Once Per Job)                                     │
│ ./run-pipeline.sh -j job-id                        │
├─────────────────────────────────────────────────────────────────┤
│ Reads:                                                           │
│   ✓ .job-id.env ONLY                                           │
│   ✗ Does NOT read hardware_cache.json                          │
│   ✗ Does NOT read config/.env.pipeline                         │
│   ✗ Has NO hardcoded values                                    │
│                                                                  │
│ Executes:                                                        │
│   ✓ Demux → ASR → Alignment (transcribe)                       │
│   ✓ Load → Translate → Subtitles (translate)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Responsibilities

### `out/hardware_cache.json`
- ✅ **Created by**: `scripts/bootstrap.sh`
- ✅ **Read by**: `scripts/prepare-job.py`
- ❌ **NOT read by**: `scripts/run-pipeline.py`
- **Contains**: Hardware detection, optimized settings
- **Lifetime**: Persistent, updated on bootstrap

### `config/.env.pipeline`
- ✅ **Created by**: Manual/template
- ✅ **Read by**: `scripts/prepare-job.py`
- ❌ **NOT read by**: `scripts/run-pipeline.py`
- **Contains**: Default configuration template
- **Lifetime**: Static, version-controlled

### `out/.../job-id/.job-id.env`
- ✅ **Created by**: `scripts/prepare-job.py`
- ✅ **Read by**: `scripts/run-pipeline.py`
- **Contains**: Complete job configuration with hardware settings
- **Lifetime**: Per job, permanent

### `out/.../job-id/job.json`
- ✅ **Created by**: `scripts/prepare-job.py`
- ✅ **Read by**: `scripts/run-pipeline.py`
- **Contains**: Job metadata (title, year, languages)
- **Lifetime**: Per job, permanent

### `out/.../job-id/manifest.json`
- ✅ **Created by**: `scripts/prepare-job.py`
- ✅ **Updated by**: `scripts/run-pipeline.py`
- **Contains**: Stage status tracking
- **Lifetime**: Per job, updated during execution

---

## Benefits of This Architecture

### 1. Separation of Concerns
- **Bootstrap**: Hardware detection only
- **Prepare-Job**: Configuration creation only
- **Run-Pipeline**: Execution only

### 2. No Hardcoded Values
- ❌ NO hardcoded devices
- ❌ NO hardcoded models
- ❌ NO hardcoded compute types
- ✅ ALL from job configuration

### 3. Job Isolation
- Each job has independent configuration
- Jobs don't interfere with each other
- Different jobs can have different settings

### 4. Reproducibility
- Job .env captures all settings at creation
- Re-running same job uses same settings
- Changing hardware_cache doesn't affect existing jobs

### 5. Testability
- Can create test jobs with custom settings
- Can override by editing job .env
- Can run same job on different machines

### 6. Debugging
- All settings visible in job .env
- Pipeline logs show loaded values
- Easy to trace configuration issues

---

## Verification Commands

### 1. Check Hardware Detection
```bash
cat out/hardware_cache.json | jq '.recommended_settings'
```

Expected output:
```json
{
  "whisper_model": "large-v3",
  "compute_type": "float16",
  "batch_size": 2,
  "whisper_backend": "mlx"
}
```

### 2. Check Job Configuration
```bash
# After prepare-job
cat out/2025-11-18_*/rpatel/job-id/.job-id.env | grep -E "DEVICE|MODEL|COMPUTE|BATCH"
```

Expected output:
```
WHISPERX_DEVICE=mps
WHISPER_MODEL=large-v3
WHISPER_COMPUTE_TYPE=float16
BATCH_SIZE=2
WHISPER_BACKEND=mlx
INDICTRANS2_DEVICE=mps
```

### 3. Check Pipeline Logs
```bash
# After run-pipeline
tail -30 out/2025-11-18_*/rpatel/job-id/logs/pipeline.log
```

Expected log entries:
```
[INFO] Using device: mps (from job config)
[INFO] Using model: large-v3 (from job config)
[INFO] Compute type: float16 (from job config)
[INFO] Batch size: 2 (from job config)
```

---

## Complete Workflow Example

### Hindi to English Translation

```bash
# Step 1: Bootstrap (if not done)
./scripts/bootstrap.sh

# Step 2: Prepare transcribe job
./prepare-job.sh "in/Hindi_Movie_2008.mp4" \
  --transcribe \
  --source-language hi

# Output: Job ID = hindi-movie-2008_20251118-073757

# Step 3: Run transcribe pipeline
./run-pipeline.sh -j hindi-movie-2008_20251118-073757

# Step 4: Prepare translate job
./prepare-job.sh "in/Hindi_Movie_2008.mp4" \
  --translate \
  --source-language hi \
  --target-language en

# Output: Job ID = hindi-movie-2008_20251118-073801

# Step 5: Run translate pipeline
./run-pipeline.sh -j hindi-movie-2008_20251118-073801

# Result: subtitles/output.en.srt
```

---

## Troubleshooting

### Issue: Hardware cache not found
**Symptom**: prepare-job uses default CPU settings  
**Solution**: Run `./scripts/bootstrap.sh`

### Issue: Job .env not found
**Symptom**: run-pipeline fails to load configuration  
**Solution**: Re-run `./prepare-job.sh`

### Issue: Wrong hardware settings
**Symptom**: Pipeline uses incorrect device/model  
**Solution**:
1. Check `out/hardware_cache.json`
2. Delete job directory
3. Re-run prepare-job

### Issue: Pipeline fails to load config
**Symptom**: Missing WHISPERX_DEVICE or similar  
**Solution**: Check job .env file exists and is complete

---

**Status**: ✅ Complete Configuration-Driven Architecture  
**No Hardcoded Values**: ✅ Verified  
**Last Updated**: November 18, 2025, 15:21 UTC
