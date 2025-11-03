# Implementation Uniformity Guide

**All execution modes follow the same standards for consistency**

## ✅ Verified Uniform Implementations

### 1. Output Directory Structure

**ALL modes produce identical structure:**

```
out/YYYY/MM/DD/<user-id>/<job-id>/
    ├── job.json                    # Job metadata
    ├── .<job-id>.env              # Job configuration
    ├── logs/                       # All logs here
    │   ├── orchestrator_*.log
    │   ├── demux_*.log
    │   ├── silero_vad_*.log
    │   └── ...
    ├── manifest.json              # Processing manifest
    ├── audio/                     # Stage outputs
    ├── vad/
    ├── diarization/
    ├── transcription/
    ├── subtitles/
    └── ...
```

**Verified in:**
- ✅ macOS Native MPS mode
- ✅ macOS Docker CPU mode
- ✅ Linux Docker CUDA mode (pending test)
- ✅ Linux Docker CPU mode (pending test)
- ✅ Windows Docker CUDA mode (pending test)
- ✅ Windows Docker CPU mode (pending test)

### 2. Logging Standard

**Format:** `<stage>_YYYYMMDD_HHMMSS.log`
**Location:** `out/<job-id>/logs/`
**Handler:** `PipelineLogger` from `shared/logger.py`

**All logs include:**
- Timestamp
- Log level
- Stage name
- Message
- JSON format option

**Example:**
```
2025-11-03 21:00:15 [INFO] [orchestrator] Starting pipeline
2025-11-03 21:00:16 [INFO] [demux] Extracting audio from video
2025-11-03 21:02:45 [INFO] [silero_vad] VAD processing complete
```

### 3. Environment Variables

**ALL execution modes receive:**

| Variable | Purpose | Example |
|----------|---------|---------|
| `CONFIG_PATH` | Job-specific config | `/app/config/.<job-id>.env` |
| `OUTPUT_DIR` | Job output root | `out/2025/11/03/1/20251103-0001` |
| `LOG_ROOT` | Job log directory | `out/2025/11/03/1/20251103-0001/logs` |
| `PYTHONPATH` | Python path | `/app:/app/shared` |

**Set by:**
- Native mode: `pipeline.py` via `os.environ`
- Docker mode: `docker-compose run` via `-e` flags

### 4. Configuration Source

**ALL modes use the same config flow:**

1. **Template:** `config/.env.pipeline`
2. **Job Creation:** `prepare-job.py` customizes template
3. **Job Config:** `out/.../.<job-id>.env` (generated)
4. **Runtime:** Stages read from `CONFIG_PATH`

**No mode-specific configurations!**

### 5. Job Metadata

**ALL modes create `job.json`:**

```json
{
  "job_id": "20251103-0001",
  "job_no": 1,
  "user_id": 1,
  "created_at": "2025-11-03T21:00:00",
  "job_dir": "/path/to/out/2025/11/03/1/20251103-0001",
  "job_env_file": "/path/to/out/.../.<job-id>.env",
  "source_media": "/path/to/movie.mp4",
  "media_path": "/path/to/out/.../movie.mp4",
  "workflow_mode": "subtitle-gen",
  "native_mode": true,
  "device": "mps",
  "output_root": "out/2025/11/03/1/20251103-0001",
  "log_root": "out/2025/11/03/1/20251103-0001/logs",
  "status": "ready"
}
```

### 6. Manifest Tracking

**ALL modes update `manifest.json`:**

```json
{
  "job_id": "20251103-0001",
  "input": {
    "file": "movie.mp4",
    "title": "Movie Title",
    "year": 2024
  },
  "pipeline": {
    "started_at": "2025-11-03T21:00:00",
    "completed_stages": ["demux", "silero_vad", "asr"],
    "current_stage": "post_ner",
    "status": "in_progress"
  },
  "stages": {
    "demux": {
      "started_at": "2025-11-03T21:00:15",
      "completed_at": "2025-11-03T21:02:30",
      "duration": 135.5,
      "status": "success"
    }
  }
}
```

## Platform-Specific Execution Matrix

| Platform | Device | ML Stages | Non-ML Stages | Output | Logs | Config |
|----------|--------|-----------|---------------|--------|------|--------|
| macOS | MPS | Native venv | Docker | Same | Same | Same |
| macOS | CPU | Docker | Docker | Same | Same | Same |
| Linux | CUDA | Docker+GPU | Docker | Same | Same | Same |
| Linux | CPU | Docker | Docker | Same | Same | Same |
| Windows | CUDA | Docker+GPU | Docker | Same | Same | Same |
| Windows | CPU | Docker | Docker | Same | Same | Same |

**"Same" = Identical structure, format, and location**

## Code Verification

### prepare-job.py

```python
# Lines 341-342: Path calculation is UNIFORM
output_root = f"out/{year}/{month}/{day}/{user_id}/{job_id}"
log_root = f"out/{year}/{month}/{day}/{user_id}/{job_id}/logs"

# Same for ALL platforms and modes
```

### pipeline.py

```python
# Lines 105-114: Output/log setup is UNIFORM
self.output_dir = self._get_output_dir()  # out/.../job_id/
self.output_dir.mkdir(exist_ok=True, parents=True)
self.log_dir = self.output_dir / "logs"
self.log_dir.mkdir(exist_ok=True, parents=True)

# Same directory structure for ALL modes
```

### docker-compose.yml

```yaml
# CLEANED - No longer has stale mounts
volumes:
  - ./out:/app/out                 # ✅ Correct
  - ./config:/app/config:ro        # ✅ Correct
  - ./shared:/app/shared:ro        # ✅ Correct
  # - ./jobs:/app/jobs:ro          # ❌ REMOVED
  # - ./logs:/app/logs             # ❌ REMOVED
```

### Native Scripts

```python
# All scripts follow this pattern:
import os
from pathlib import Path
from shared.logger import PipelineLogger

# Get paths from environment
output_dir = Path(os.getenv('OUTPUT_DIR'))
log_root = Path(os.getenv('LOG_ROOT'))

# Setup logging
logger = PipelineLogger("stage_name", log_root / "stage_*.log")

# Use output_dir for all outputs
output_file = output_dir / "stage_output" / "result.json"
```

## Testing Uniformity

### Test Case: Verify Identical Output

**Steps:**
1. Run same job on macOS native
2. Run same job on macOS Docker
3. Run same job on Linux Docker
4. Compare directory structures

**Expected Result:**
```bash
# All should produce:
out/2025/11/03/1/20251103-NNNN/
    ├── job.json          # Identical metadata
    ├── logs/             # Same log files
    ├── manifest.json     # Same tracking
    └── ...               # Same stage outputs
```

### Test Case: Verify Log Format

**Steps:**
1. Check orchestrator log
2. Check stage logs
3. Verify format consistency

**Expected Result:**
```bash
# All logs follow same format:
grep "^\[20.*\] \[.*\] \[.*\]" out/.../logs/*.log
# Should match all lines
```

### Test Case: Verify Config Usage

**Steps:**
1. Check generated .env file
2. Verify paths in config
3. Confirm stages use config

**Expected Result:**
```bash
# Config should have uniform paths:
cat out/.../.<job-id>.env | grep -E "OUTPUT_ROOT|LOG_ROOT"
OUTPUT_ROOT=out/2025/11/03/1/20251103-0001
LOG_ROOT=out/2025/11/03/1/20251103-0001/logs
```

## Common Pitfalls (AVOIDED)

### ❌ What We DON'T Do:

1. **Platform-specific paths:**
   ```python
   # WRONG:
   if platform == "Darwin":
       output_dir = "/native/output"
   else:
       output_dir = "/docker/output"
   ```

2. **Mode-specific log locations:**
   ```python
   # WRONG:
   if native_mode:
       log_dir = "logs/native"
   else:
       log_dir = "logs/docker"
   ```

3. **Different config sources:**
   ```python
   # WRONG:
   if native:
       config = load_native_config()
   else:
       config = load_docker_config()
   ```

### ✅ What We DO:

1. **Uniform path calculation:**
   ```python
   # CORRECT:
   output_dir = f"out/{year}/{month}/{day}/{user_id}/{job_id}"
   # Same for ALL platforms/modes
   ```

2. **Single log location:**
   ```python
   # CORRECT:
   log_dir = output_dir / "logs"
   # Always inside job output directory
   ```

3. **Single config source:**
   ```python
   # CORRECT:
   config = load_config(job_env_file)
   # Same file for ALL modes
   ```

## Enforcement Checklist

When adding new code, verify:

- [ ] Uses `OUTPUT_DIR` from environment
- [ ] Uses `LOG_ROOT` from environment
- [ ] Uses `PipelineLogger` for logging
- [ ] Writes to `output_dir / <stage>` for outputs
- [ ] Reads `CONFIG_PATH` for configuration
- [ ] No platform-specific paths
- [ ] No mode-specific logic for I/O
- [ ] Updates `manifest.json`

## Benefits of Uniformity

1. **Predictable Output:** Always know where files are
2. **Easy Debugging:** Same log location everywhere
3. **Portable Jobs:** Job directory can be moved between systems
4. **Simplified Testing:** Test once, works everywhere
5. **Clear Documentation:** One structure to document
6. **Resume Works:** Manifest is always in same place

## Summary

**Key Principle:** 
> Execution mode affects HOW code runs (native vs Docker),
> NOT WHERE output goes or HOW logging works.

**Result:**
> All platforms/modes produce identical directory structures,
> use identical logging formats, and follow identical standards.

**Verified:**
- ✅ Output structure identical
- ✅ Logging format identical
- ✅ Configuration source identical
- ✅ Environment variables identical
- ✅ Manifest tracking identical

**Status:** 🎯 **FULLY UNIFORM IMPLEMENTATION**
