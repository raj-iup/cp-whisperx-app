# CP-WhisperX Logging Standard

**Status**: 🔧 In Progress  
**Goal**: Unified logging across all Python scripts, shell scripts, and Docker containers

---

## Current State Analysis

### Identified Issues

1. **TWO Different Logger Implementations**:
   - `shared/logger.py` - Function-based with `setup_logger()`
   - `scripts/logger.py` - Class-based with `PipelineLogger`

2. **Inconsistent Usage**:
   - 6 containers use `shared/logger.setup_logger()`
   - 4 containers use `scripts/logger.PipelineLogger`
   - Shell scripts use ad-hoc echo statements

3. **Different Formats**:
   - `shared/logger`: Supports JSON format (via python-json-logger)
   - `scripts/logger`: Only text format
   - Shell scripts: Plain text with no timestamps

### Files Using Each Logger

**shared/logger.py** (6 containers):
- docker/demux/demux.py
- docker/mux/mux.py
- docker/pre-ner/pre_ner.py
- docker/pyannote-vad/pyannote_vad.py
- docker/silero-vad/silero_vad.py
- docker/tmdb/tmdb.py

**scripts/logger.py** (4 containers):
- docker/asr/whisperx_asr.py
- docker/diarization/diarization.py
- docker/post-ner/post_ner.py
- docker/subtitle-gen/subtitle_gen.py

---

## Recommended Standard

### 1. Unified Python Logger

**Location**: `shared/logger.py` (keep this as the single source of truth)

**Features**:
- ✅ JSON and text format support
- ✅ Console and file logging
- ✅ Configurable log levels
- ✅ Consistent timestamp format
- ✅ Integration with config system

**Format**:
```
[YYYY-MM-DD HH:MM:SS] [module_name] [LEVEL] message
```

**JSON Format**:
```json
{
  "asctime": "2024-10-29 20:30:00",
  "name": "demux",
  "levelname": "INFO",
  "message": "Starting demux: movie.mp4"
}
```

### 2. Shell Script Logging Standard

**Functions** (add to each shell script):
```bash
# Logging functions
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $*"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $*"
}

log_debug() {
    if [ "${DEBUG:-0}" = "1" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [DEBUG] $*"
    fi
}
```

**Usage**:
```bash
log_info "Starting build process"
log_error "Build failed: $error_message"
```

### 3. Docker Container Logging

**Standard Output/Error**:
- All containers log to stdout/stderr
- Docker captures and timestamps automatically
- Logs accessible via: `docker logs <container_name>`

**Log Files**:
- Each stage creates: `logs/<stage_name>_<timestamp>.log`
- Orchestrator creates: `logs/orchestrator_<timestamp>.log`
- All logs mounted from host: `./logs:/app/logs`

---

## Implementation Plan

### Phase 1: Consolidate Python Loggers ✅ READY

1. **Enhance `shared/logger.py`**:
   - Keep existing `setup_logger()` function
   - Add `PipelineLogger` class for compatibility
   - Both should use same underlying configuration

2. **Update `scripts/logger.py`**:
   - Deprecate in favor of `shared/logger.py`
   - Add deprecation warning
   - Import from shared for backward compatibility

### Phase 2: Update All Python Scripts

**6 files already using shared/logger** ✅ No change needed:
- docker/demux/demux.py
- docker/mux/mux.py
- docker/pre-ner/pre_ner.py
- docker/pyannote-vad/pyannote_vad.py
- docker/silero-vad/silero_vad.py
- docker/tmdb/tmdb.py

**4 files to update** 🔧:
- docker/asr/whisperx_asr.py
- docker/diarization/diarization.py
- docker/post-ner/post_ner.py
- docker/subtitle-gen/subtitle_gen.py

**Change**:
```python
# OLD
from scripts.logger import PipelineLogger
logger = PipelineLogger("stage_name")

# NEW
from logger import setup_logger
from config import load_config
config = load_config()
logger = setup_logger(
    "stage_name",
    log_level=config.log_level,
    log_format=config.log_format,
    log_to_console=config.log_to_console,
    log_to_file=config.log_to_file,
    log_dir=config.log_root
)
```

### Phase 3: Standardize Shell Scripts

**Files to update**:
- scripts/bootstrap.sh
- scripts/preflight.sh
- scripts/build-images.sh
- scripts/push-images.sh
- scripts/push_multiarch.sh
- scripts/docker-run.sh
- scripts/pipeline-status.sh

**Add common logging functions** to each script at the top.

### Phase 4: Pipeline Orchestrator

**File**: `pipeline.py`

Already uses proper logging via `PipelineLogger`:
```python
from logger import PipelineLogger
self.logger = PipelineLogger("orchestrator", log_file)
```

**Action**: Verify it follows the standard format.

---

## Configuration Integration

All logging should respect these config values from `config/.env`:

```bash
# Logging Configuration
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json             # json or text
LOG_TO_CONSOLE=true         # Log to stdout
LOG_TO_FILE=true            # Log to file
LOG_ROOT=/app/logs          # Log directory
```

---

## Log File Naming Convention

**Python Scripts**:
```
logs/<module_name>_<timestamp>.log
```
Example: `logs/demux_20241029_203015.log`

**Shell Scripts**:
```
logs/<script_name>_<timestamp>.log
```
Example: `logs/build_images_20241029_203015.log`

**Docker Containers**:
```
docker logs cp_whisperx_<stage>
```
Example: `docker logs cp_whisperx_asr`

---

## Benefits of Standardization

1. **Consistent Format**: Easy to parse and analyze
2. **Structured Logging**: JSON format for log aggregation tools
3. **Troubleshooting**: Quick identification of issues across stages
4. **Monitoring**: Easy integration with monitoring systems
5. **Debugging**: Consistent debug output across all components

---

## Validation Checklist

- [ ] All Python scripts use `shared/logger.py`
- [ ] All shell scripts have logging functions
- [ ] All logs follow timestamp format
- [ ] Docker logs properly captured
- [ ] Config integration works
- [ ] JSON and text formats tested
- [ ] Log files created in correct location
- [ ] No duplicate logger instances

---

## Next Steps

1. Update `shared/logger.py` with PipelineLogger class
2. Create deprecation wrapper in `scripts/logger.py`
3. Update 4 container scripts to use shared logger
4. Add logging functions to shell scripts
5. Test end-to-end logging
6. Document in README

---

**Timeline**: 1-2 hours to implement
**Priority**: High (improves maintainability and debugging)
