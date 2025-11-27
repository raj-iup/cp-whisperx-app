# Debug Logging Guide

## Overview

All three main scripts (**bootstrap**, **prepare-job**, **run-pipeline**) support debug mode with comprehensive logging to both console and log files.

## Debug Mode Behavior

### Console Output
- **Normal mode:** Clean, concise progress messages
- **Debug mode:** Verbose output including pip package installation details

### Log File Output
- **Normal mode:** Full installation/execution details (quiet on console)
- **Debug mode:** Same full details (also shown on console)

**Key Point:** Log files **always contain full debug information** regardless of mode. Debug flag only controls what's shown on console.

## Bootstrap Script

### Usage

```bash
# Normal mode
./bootstrap.sh
# Console: Clean progress
# Log: logs/bootstrap_YYYYMMDD_HHMMSS.log (full details)

# Debug mode
./bootstrap.sh --debug
# Console: Full pip output + progress
# Log: logs/bootstrap_YYYYMMDD_HHMMSS.log (same full details)
```

### What Gets Logged

**Always logged to file:**
- Platform and hardware detection
- Python version
- Virtual environment creation
- Complete pip install output (every package)
- Dependency resolution details
- Success/failure for each environment
- Hardware cache configuration
- FFmpeg validation
- Completion timestamp

**Debug mode additionally shows on console:**
- Real-time pip package downloads
- Package version resolution
- Dependency conflicts (if any)

### Log File Location

```
logs/bootstrap_20241120_045300.log
```

### Example Log Output

```
========================================
Bootstrap started: 2024-11-20 04:53:00
Platform: Darwin (arm64)
Debug mode: false
========================================

━━━ ENVIRONMENT: common ━━━
Creating virtual environment...
Collecting pip
  Downloading pip-24.0-py3-none-any.whl (2.1 MB)
Successfully installed pip-24.0 setuptools-69.0.3 wheel-0.42.0

Installing from requirements-common.txt...
Collecting ffmpeg-python>=0.2.0
  Downloading ffmpeg_python-0.2.0-py3-none-any.whl
Collecting python-dotenv>=1.0.0
  ...
Successfully installed ffmpeg-python-0.2.0 python-dotenv-1.0.1 ...

========================================
Bootstrap completed: 2024-11-20 04:58:15
Status: SUCCESS
Environments created:
  - venv/common
  - venv/whisperx
  - venv/mlx
  - venv/indictrans2
========================================
```

## Prepare Job Script

### Usage

```bash
# Normal mode
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en
# Log: out/YYYY/MM/DD/USER/NNN/logs/prepare-job.log

# Debug mode
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en --debug
# Log: Same location, DEBUG level logging
```

### What Gets Logged

**INFO level (normal mode):**
- Job configuration validation
- Workflow selection
- Language validation
- File checks
- Job directory creation
- Manifest initialization

**DEBUG level (debug mode):**
- All INFO level messages
- Detailed validation steps
- Environment variable generation
- Configuration file writes
- File system operations
- Python module imports

### Implementation

The `--debug` flag:
1. Sets `log_level = "DEBUG"` in job .env file
2. Python script uses `PipelineLogger(log_level="DEBUG")`
3. All debug messages written to file
4. Console shows verbose output

### Log File Location

```
out/2024/11/20/rpatel/001/logs/prepare-job.log
```

## Run Pipeline Script

### Usage

```bash
# Normal mode
./run-pipeline.sh -j job_20241120_001
# Log: out/YYYY/MM/DD/USER/NNN/logs/pipeline.log

# Debug mode (inherited from job config)
./run-pipeline.sh -j job_20241120_001
# If job was prepared with --debug, runs in debug mode automatically
```

### What Gets Logged

**INFO level (normal mode):**
- Stage execution start/end
- Progress percentages
- Success/failure status
- File outputs
- Performance metrics

**DEBUG level (debug mode):**
- All INFO level messages
- Environment switching details
- Model loading progress
- Batch processing details
- Memory usage
- GPU utilization
- Intermediate file creation
- Command execution details

### Stage-Specific Logs

Each stage creates its own log file:

```
out/2024/11/20/rpatel/001/logs/
├── pipeline.log              # Orchestrator
├── 01_demux_*.log           # Audio extraction
├── 06_asr_*.log             # Speech recognition
├── 10_alignment_*.log       # Timestamp alignment
├── 12_translation_*.log     # IndicTrans2
├── 14_subtitle_gen_*.log    # SRT generation
└── 15_mux_*.log             # Video embedding
```

### Implementation

The pipeline reads `DEBUG_MODE` from job's `.env` file:
1. Job prepared with `--debug` sets `DEBUG_MODE=true`
2. Pipeline Python script reads this setting
3. All stages inherit debug log level
4. Each stage logs to its own file

## Python Logger Implementation

### PipelineLogger Class

Located in `shared/logger.py`:

```python
from shared.logger import PipelineLogger

# Normal mode
logger = PipelineLogger(
    module_name="asr",
    log_file=Path("logs/asr.log"),
    log_level="INFO"
)

# Debug mode
logger = PipelineLogger(
    module_name="asr", 
    log_file=Path("logs/asr.log"),
    log_level="DEBUG"
)
```

### What Gets Logged at Each Level

**INFO:**
- Major operations
- Stage transitions
- Success/error conditions
- File outputs
- Summary statistics

**DEBUG:**
- Function entry/exit
- Variable values
- Loop iterations
- Model predictions
- API calls
- File I/O operations

## Log File Analysis

### Finding Errors

```bash
# Check bootstrap logs
grep -i "error\|fail" logs/bootstrap_*.log

# Check job preparation
grep -i "error\|fail" out/2024/11/20/rpatel/001/logs/prepare-job.log

# Check specific pipeline stage
grep -i "error\|fail" out/2024/11/20/rpatel/001/logs/06_asr_*.log
```

### Performance Analysis

```bash
# Stage execution times
grep "completed in\|took" out/2024/11/20/rpatel/001/logs/*.log

# Memory usage (if debug mode)
grep -i "memory\|ram" out/2024/11/20/rpatel/001/logs/*.log
```

### Package Installation Issues

```bash
# See what packages failed to install
grep -i "could not\|failed to\|error:" logs/bootstrap_*.log

# Check dependency conflicts
grep -i "conflict\|incompatible" logs/bootstrap_*.log
```

## Best Practices

### When to Use Debug Mode

**Use `--debug` when:**
- ❌ Bootstrap fails with unclear error
- ❌ Job preparation validation fails
- ❌ Pipeline stage hangs or crashes
- ❌ Unexpected output or behavior
- ❌ Troubleshooting performance issues
- ❌ Contributing to the project

**Normal mode is fine when:**
- ✅ First-time setup working normally
- ✅ Standard workflow execution
- ✅ Production environments
- ✅ Batch processing multiple jobs

### Reading Log Files

**For bootstrap issues:**
```bash
# Start from the end (shows completion status)
tail -50 logs/bootstrap_20241120_045300.log

# Find where it failed
grep -B 5 -i "error\|fail" logs/bootstrap_20241120_045300.log
```

**For pipeline issues:**
```bash
# Check orchestrator log first
cat out/2024/11/20/rpatel/001/logs/pipeline.log

# Then check failed stage
cat out/2024/11/20/rpatel/001/logs/06_asr_*.log
```

### Log Retention

Logs accumulate over time. Clean up periodically:

```bash
# Remove old bootstrap logs (keep last 10)
ls -t logs/bootstrap_*.log | tail -n +11 | xargs rm

# Remove old job logs (jobs older than 30 days)
find out/ -name "*.log" -mtime +30 -delete
```

## Troubleshooting Examples

### Example 1: Bootstrap Failure

**Symptom:** Bootstrap fails during whisperx environment creation

**Steps:**
1. Re-run with debug:
   ```bash
   ./bootstrap.sh --debug 2>&1 | tee bootstrap_debug.log
   ```

2. Check where it failed:
   ```bash
   grep -B 10 -i "error" bootstrap_debug.log
   ```

3. Look for package conflicts:
   ```bash
   grep -i "conflict\|incompatible\|version" bootstrap_debug.log
   ```

### Example 2: Pipeline Stage Hangs

**Symptom:** ASR stage appears to hang at 50%

**Steps:**
1. Check if job has debug enabled:
   ```bash
   grep "DEBUG_MODE" out/2024/11/20/rpatel/001/.job_20241120_001.env
   ```

2. If not, prepare a new job with debug:
   ```bash
   ./prepare-job.sh in/movie.mp4 --transcribe --debug
   ```

3. Monitor log in real-time:
   ```bash
   tail -f out/2024/11/20/rpatel/002/logs/06_asr_*.log
   ```

4. Look for memory/GPU issues:
   ```bash
   grep -i "memory\|oom\|cuda" out/2024/11/20/rpatel/002/logs/06_asr_*.log
   ```

### Example 3: Translation Quality Issues

**Symptom:** Translations seem incorrect

**Steps:**
1. Check source transcript first:
   ```bash
   cat out/2024/11/20/rpatel/001/transcripts/transcript_source.txt
   ```

2. Check translation log for warnings:
   ```bash
   grep -i "warn\|skip\|error" out/2024/11/20/rpatel/001/logs/12_translation_*.log
   ```

3. Re-run with debug to see sentence-by-sentence translation:
   ```bash
   # Prepare new job with debug
   ./prepare-job.sh in/movie.mp4 --translate -s hi -t en --debug
   ./run-pipeline.sh -j <new-job-id>
   ```

## Summary

| Script | Normal Mode | Debug Mode | Log Location |
|--------|-------------|------------|--------------|
| bootstrap.sh | Clean console, full log | Verbose console, full log | `logs/bootstrap_*.log` |
| prepare-job.sh | Basic console, INFO log | Verbose console, DEBUG log | `out/.../logs/prepare-job.log` |
| run-pipeline.sh | Progress console, INFO log | Detailed console, DEBUG log | `out/.../logs/pipeline.log` + stage logs |

**Key Takeaway:** Log files always contain comprehensive information. Debug mode primarily affects console output verbosity.
