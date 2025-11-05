# Log Output Location Analysis

**Analysis Date**: 2025-11-05  
**Scope**: All `.ps1` and `.sh` scripts in project root and subdirectories

## Executive Summary

**Primary Log Location**: `logs/` directory (in job directory structure)  
**Log Format**: `XX_stage-name_YYYYMMDD_HHMMSS.log` (where XX = stage number 01-10)  
**Shell Scripts**: Most output to **STDOUT only** (no file logging by default)  
**Python Scripts**: Log to **both STDOUT and files** in `logs/` directory

## Log Directory Structure

```
<job-directory>/
├── logs/
│   ├── 00_orchestrator_20251105_120000.log     # Pipeline orchestrator
│   ├── prepare-job_20251105_115900.log         # Job preparation
│   ├── 01_demux_20251105_120100.log            # FFmpeg audio extraction
│   ├── 02_tmdb_20251105_120200.log             # Movie metadata
│   ├── 03_pre-ner_20251105_120300.log          # Pre-ASR NER
│   ├── 04_silero-vad_20251105_120400.log       # VAD detection
│   ├── 05_pyannote-vad_20251105_120500.log     # VAD refinement
│   ├── 06_diarization_20251105_120600.log      # Speaker diarization
│   ├── 07_asr_20251105_120700.log              # WhisperX transcription
│   ├── 08_post-ner_20251105_120800.log         # Post-ASR NER
│   ├── 09_subtitle-gen_20251105_120900.log     # SRT generation
│   └── 10_mux_20251105_121000.log              # FFmpeg subtitle mux
```

**Job Directory Examples**:
- `out/<MovieName>/`
- `jobs/<MovieName>/`

## Logging System Architecture

### Python Scripts (Primary Pipeline)

**Logger Module**: `shared/logger.py`  
**Format**: Structured logging with stage prefixes

#### Key Functions:

```python
# Generate log filename with stage prefix
get_stage_log_filename(stage_name, timestamp)
# Returns: "07_asr_20251105_120000.log"

# Setup logger with file and console output
setup_logger(name, log_level, log_format, log_to_console, log_to_file, log_dir)
# Default log_dir: "/app/logs" (in containers) or "logs/" (native)

# PipelineLogger class (high-level wrapper)
PipelineLogger(stage_name, log_file, log_level)
```

#### Stage Order Mapping:

| Stage Number | Stage Name | Log Prefix |
|--------------|------------|------------|
| 00 | orchestrator | `00_orchestrator_` |
| - | prepare-job | `prepare-job_` (no prefix) |
| 01 | demux | `01_demux_` |
| 02 | tmdb | `02_tmdb_` |
| 03 | pre-ner | `03_pre-ner_` |
| 04 | silero-vad | `04_silero-vad_` |
| 05 | pyannote-vad | `05_pyannote-vad_` |
| 06 | diarization | `06_diarization_` |
| 07 | asr | `07_asr_` |
| 08 | post-ner | `08_post-ner_` |
| 09 | subtitle-gen | `09_subtitle-gen_` |
| 10 | mux | `10_mux_` |

#### Log Format:

**JSON Format** (default for containers):
```json
{
  "asctime": "2025-11-05 12:00:00",
  "name": "asr",
  "levelname": "INFO",
  "message": "Processing audio file"
}
```

**Text Format** (human-readable):
```
[2025-11-05 12:00:00] [asr] [INFO] Processing audio file
```

### Shell Scripts (PowerShell & Bash)

**Logger Modules**:
- `scripts/common-logging.ps1` (PowerShell)
- `scripts/common-logging.sh` (Bash)

**Default Behavior**: **STDOUT only** (no file logging)

**Optional File Logging**: Set `LOG_FILE` environment variable

```powershell
# PowerShell - Enable file logging
$env:LOG_FILE = "logs/build-images.log"
.\scripts\build-all-images.ps1
```

```bash
# Bash - Enable file logging
export LOG_FILE="logs/build-images.log"
./scripts/build-all-images.sh
```

#### Shell Script Log Functions:

**PowerShell** (`scripts/common-logging.ps1`):
```powershell
Write-LogDebug "message"      # [DEBUG] level
Write-LogInfo "message"       # [INFO] level
Write-LogWarn "message"       # [WARN] level
Write-LogError "message"      # [ERROR] level
Write-LogCritical "message"   # [CRITICAL] level
Write-LogSuccess "message"    # [SUCCESS] level
Write-LogFailure "message"    # [FAILURE] level
Write-LogSection "header"     # Section separator
```

**Bash** (`scripts/common-logging.sh`):
```bash
log_debug "message"           # [DEBUG] level
log_info "message"            # [INFO] level
log_warn "message"            # [WARN] level
log_error "message"           # [ERROR] level
log_critical "message"        # [CRITICAL] level
log_success "message"         # [SUCCESS] level
log_failure "message"         # [FAILURE] level
log_section "header"          # Section separator
```

**Format**: `[YYYY-MM-DD HH:mm:ss] [script-name] [LEVEL] message`

**Example**:
```
[2025-11-05 12:00:00] [build-all-images] [INFO] Building base:cpu image
```

## Script-by-Script Analysis

### Root-Level Scripts

#### 1. `pipeline.py` ⭐ Main Pipeline Orchestrator
**Log Output**:
- **File**: `logs/00_orchestrator_YYYYMMDD_HHMMSS.log` (in job directory)
- **Format**: JSON + Text to console
- **Logger**: `PipelineLogger("orchestrator", log_file)`

**Location**: `<job-dir>/logs/00_orchestrator_*.log`

#### 2. `prepare-job.py` ⭐ Job Preparation
**Log Output**:
- **File**: `logs/prepare-job_YYYYMMDD_HHMMSS.log` (in job directory)
- **Format**: Text format
- **Logger**: `PipelineLogger("prepare-job", log_file)`

**Location**: `<job-dir>/logs/prepare-job_*.log`

#### 3. `preflight.py` ⭐ Preflight Checks
**Log Output**:
- **File**: `logs/preflight_YYYYMMDD_HHMMSS.json`
- **Format**: JSON report
- **Logger**: Direct JSON file write

**Location**: `logs/preflight_*.json` (project root)

#### 4. `run_pipeline.ps1` / `run_pipeline.sh`
**Log Output**: **STDOUT only**
- No file logging by default
- Wraps `pipeline.py` which handles its own logging

**To enable file logging**:
```powershell
# Redirect output
.\run_pipeline.ps1 | Tee-Object -FilePath "logs/pipeline-run.log"
```

#### 5. `quick-start.ps1` / `quick-start.sh`
**Log Output**: **STDOUT only**
- No file logging by default
- Calls `prepare-job.py` and `pipeline.py` which handle their own logging

#### 6. `resume-pipeline.ps1` / `resume-pipeline.sh`
**Log Output**: **STDOUT only**
- No file logging by default
- Resumes `pipeline.py` which handles its own logging

#### 7. `monitor-push.ps1` / `monitor_push.sh`
**Log Output**: **STDOUT only**
- Monitors: `push_all.log` file
- **Reads from**: `push_all.log` (created by push scripts)

**Note**: These scripts READ logs, don't write them

### Scripts Directory

#### Build Scripts

**1. `scripts/build-all-images.ps1` / `scripts/build-all-images.sh`**
- **Log Output**: **STDOUT only** (by default)
- **Optional File Logging**: Set `$env:LOG_FILE` (PowerShell) or `export LOG_FILE` (Bash)
- **Format**: `[YYYY-MM-DD HH:mm:ss] [build-all-images] [LEVEL] message`

**To enable file logging**:
```powershell
$env:LOG_FILE = "logs/build-images.log"
.\scripts\build-all-images.ps1
```

#### Push Scripts

**2. `scripts/push-images.ps1` / `scripts/push-images.sh`**
- **Log Output**: **STDOUT only** (by default)
- **Optional File Logging**: Set `LOG_FILE` environment variable
- **Creates**: `push_all.log` (if using push-all variant)

#### Utility Scripts

**3. `scripts/bootstrap.ps1` / `scripts/bootstrap.sh`**
- **Log Output**: **STDOUT only**
- **Purpose**: Python environment setup
- **No file logging**: Use shell redirection if needed

**4. `scripts/docker-run.ps1` / `scripts/docker-run.sh`**
- **Log Output**: **STDOUT only**
- **Purpose**: Docker service management
- **No file logging**: Use shell redirection if needed

**5. `scripts/pipeline-status.ps1` / `scripts/pipeline-status.sh`**
- **Log Output**: **STDOUT only** (informational display)
- **Purpose**: Show pipeline quick reference
- **No file logging needed**

**6. `scripts/run-docker-stage.ps1` / `scripts/run-docker-stage.sh`**
- **Log Output**: **STDOUT only**
- **Purpose**: Run individual Docker stage
- **Stage logs**: Handled by container (goes to `logs/` in job directory)

#### Test Scripts

**7. `scripts/tests/test_windows_*.ps1`**
- **Log Output**: **STDOUT only**
- **Purpose**: Test scripts
- **Actual logs**: Generated by pipeline stages in `logs/` directory

### Native Execution Scripts

#### `native/run_asr_debug.sh`
**Log Output**:
- **Mentions**: `logs/asr_${MOVIE_NAME}_*.log`
- **Location**: `logs/` directory in job directory
- **Format**: Stage logging via `shared/logger.py`

## Log File Locations Summary

### Production Logs (Pipeline Execution)

**Location**: `<job-directory>/logs/`

**Job Directory Structure**:
```
out/<MovieName>/                          # Output directory
├── logs/                                 # All pipeline logs here
│   ├── prepare-job_YYYYMMDD_HHMMSS.log
│   ├── 00_orchestrator_YYYYMMDD_HHMMSS.log
│   ├── 01_demux_YYYYMMDD_HHMMSS.log
│   ├── 02_tmdb_YYYYMMDD_HHMMSS.log
│   ├── ... (03-10 stage logs)
│   └── pipeline_resume_YYYYMMDD_HHMMSS.log
├── audio/                                # Extracted audio
├── chunks/                               # VAD chunks
├── transcripts/                          # ASR output
└── <MovieName>.srt                       # Final subtitle
```

### Development/Build Logs (Optional)

**Location**: Project root `logs/` directory (if enabled)

**Files**:
- `logs/preflight_*.json` - Preflight check reports
- `logs/build-images.log` - Build script logs (if `LOG_FILE` set)
- `logs/push-images.log` - Push script logs (if `LOG_FILE` set)
- `push_all.log` - Docker push progress (created by push scripts)

### Docker Container Logs

**Location**: Docker's internal logging system

**Access via**:
```bash
# View container logs
docker logs <container-name>

# Follow logs
docker logs -f <container-name>

# View specific service in docker-compose
docker-compose logs asr
docker-compose logs -f diarization
```

**Note**: Container STDOUT is also saved to job `logs/` directory via shared volume mount

## How Logging Works: Complete Flow

### 1. Job Preparation Phase

```
User runs: .\quick-start.ps1 "Movie Title"
↓
prepare-job.py executes
↓
Creates: out/Movie_Title/logs/prepare-job_YYYYMMDD_HHMMSS.log
↓
Logs written to BOTH:
  - STDOUT (console)
  - File: logs/prepare-job_*.log
```

### 2. Pipeline Execution Phase

```
pipeline.py executes
↓
Creates: logs/00_orchestrator_YYYYMMDD_HHMMSS.log
↓
For each stage (01-10):
  ├─ Docker container starts
  ├─ Container mounts: -v ./out/Movie_Title/logs:/app/logs
  ├─ Stage script creates: /app/logs/XX_stage-name_YYYYMMDD_HHMMSS.log
  ├─ Logs written to BOTH:
  │   - Container STDOUT (viewable via `docker logs`)
  │   - Shared file: out/Movie_Title/logs/XX_stage-name_*.log
  └─ Container exits
↓
All logs persist in: out/Movie_Title/logs/
```

### 3. Build/Push Scripts (Manual Operations)

```
User runs: .\scripts\build-all-images.ps1
↓
Script uses: common-logging.ps1
↓
Logs written to: STDOUT only (by default)
↓
Optional file logging:
  $env:LOG_FILE = "logs/build.log"
  .\scripts\build-all-images.ps1
  ↓
  Logs written to BOTH:
    - STDOUT (console)
    - logs/build.log
```

## Viewing Logs

### Pipeline Logs (Most Common)

**Location**: `out/<MovieName>/logs/`

```powershell
# View all logs for a job
Get-ChildItem out\Movie_Title\logs\*.log

# View specific stage log
Get-Content out\Movie_Title\logs\07_asr_*.log -Tail 50

# Follow orchestrator log
Get-Content out\Movie_Title\logs\00_orchestrator_*.log -Wait

# Search all logs
Get-ChildItem out\Movie_Title\logs\*.log | Select-String "ERROR"
```

### Real-Time Pipeline Monitoring

```powershell
# Watch latest orchestrator log
Get-Content out\Movie_Title\logs\00_orchestrator_*.log -Wait

# Monitor Docker container logs
docker-compose logs -f asr

# View all pipeline container logs
docker-compose logs -f
```

### Build/Development Logs

```powershell
# If LOG_FILE was set during build
Get-Content logs\build-images.log

# Docker push monitor
Get-Content push_all.log -Wait

# Preflight report
Get-Content logs\preflight_*.json | ConvertFrom-Json
```

## Configuration Options

### Python Scripts

**Environment Variables**:
- `LOG_LEVEL` - Set log verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT` - Set format (json or text)

```powershell
# Example: Enable DEBUG logging
$env:LOG_LEVEL = "DEBUG"
.\quick-start.ps1 "Movie Title"
```

### Shell Scripts (PowerShell/Bash)

**Environment Variables**:
- `LOG_FILE` - Enable file logging (path to log file)
- `LOG_LEVEL` - Set minimum level (not implemented yet in common-logging modules)

```powershell
# Example: Enable file logging for build script
$env:LOG_FILE = "logs\build-$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
.\scripts\build-all-images.ps1
```

## Best Practices

### For Users

1. **Pipeline logs are automatic** - No configuration needed
2. **Logs persist** in `out/<MovieName>/logs/` directory
3. **Check logs** after failures: Look for `[ERROR]` or `[CRITICAL]` entries
4. **Monitor real-time**: Use `Get-Content -Wait` (PowerShell) or `tail -f` (Bash)

### For Developers

1. **Use shared/logger.py** for all Python scripts
2. **Use common-logging modules** for shell scripts
3. **Always log to STDOUT** - Let users choose file output
4. **Include timestamps** - Already handled by logging modules
5. **Use stage prefixes** - Helps identify which stage failed

### For CI/CD

1. **Enable file logging** for build scripts:
   ```bash
   export LOG_FILE="logs/ci-build.log"
   ./scripts/build-all-images.sh
   ```

2. **Archive logs** after pipeline runs:
   ```bash
   tar -czf logs-archive.tar.gz out/*/logs/
   ```

3. **Parse JSON logs** for metrics/errors:
   ```bash
   cat logs/*.log | jq 'select(.levelname=="ERROR")'
   ```

## Summary Table

| Script Category | Log Location | File Logging | Format |
|----------------|--------------|--------------|---------|
| **Pipeline (Python)** | `<job-dir>/logs/XX_*.log` | ✅ Always | JSON/Text |
| **Preparation (Python)** | `<job-dir>/logs/prepare-job_*.log` | ✅ Always | Text |
| **Preflight (Python)** | `logs/preflight_*.json` | ✅ Always | JSON |
| **Build Scripts (Shell)** | STDOUT | ❌ Optional | Text |
| **Push Scripts (Shell)** | STDOUT / `push_all.log` | ⚠️ Partial | Text |
| **Utility Scripts (Shell)** | STDOUT | ❌ Optional | Text |
| **Test Scripts (Shell)** | STDOUT | ❌ No | Text |
| **Docker Containers** | Container logs + shared volume | ✅ Both | JSON/Text |

## Quick Reference

**Primary Log Location**: `out/<MovieName>/logs/`  
**Python Logger**: `shared/logger.py`  
**PowerShell Logger**: `scripts/common-logging.ps1`  
**Bash Logger**: `scripts/common-logging.sh`  
**Log Format**: `[YYYY-MM-DD HH:mm:ss] [name] [LEVEL] message`  
**Stage Logs**: Prefixed with `XX_` where XX is stage number (01-10)

**Most Important Logs**:
1. `00_orchestrator_*.log` - Pipeline orchestration
2. `07_asr_*.log` - WhisperX transcription (most time-consuming)
3. `06_diarization_*.log` - Speaker identification
4. `prepare-job_*.log` - Job setup issues

**Enable File Logging for Shell Scripts**:
```powershell
# PowerShell
$env:LOG_FILE = "logs/my-script.log"

# Bash
export LOG_FILE="logs/my-script.log"
```

## Conclusion

**Default Behavior**: 
- ✅ Python pipeline scripts: **Always log to files** in `<job-dir>/logs/`
- ✅ Shell scripts: **STDOUT only** (file logging optional via `LOG_FILE`)

**Recommendation**: 
- Pipeline logs are handled automatically - no action needed
- For build/utility scripts, use shell redirection or set `LOG_FILE` if file output desired
- All logs use consistent timestamp format for easy correlation

**Log Retention**: User's responsibility - logs persist in job directories until manually deleted
