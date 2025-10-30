# Comprehensive Logging System - Native MPS Pipeline

## Overview

The native MPS pipeline now includes comprehensive logging functionality that captures detailed information about every stage of the pipeline execution. All logs are saved to the `logs/` directory with timestamps and structured formatting.

## Features

### ✅ Dual Output System
- **Console Output**: Real-time monitoring with INFO level and above
- **File Output**: Detailed DEBUG level logs with function names and line numbers

### ✅ Per-Stage Log Files
Each pipeline stage generates its own timestamped log file:
- `demux_<movie>_<timestamp>.log`
- `tmdb_<movie>_<timestamp>.log`
- `pre-ner_<movie>_<timestamp>.log`
- `silero-vad_<movie>_<timestamp>.log`
- `pyannote-vad_<movie>_<timestamp>.log`
- `diarization_<movie>_<timestamp>.log`
- `asr_<movie>_<timestamp>.log`
- `post-ner_<movie>_<timestamp>.log`
- `subtitle-gen_<movie>_<timestamp>.log`
- `mux_<movie>_<timestamp>.log`

### ✅ Rich Logging Information
Each log entry includes:
- **Timestamp**: `YYYY-MM-DD HH:MM:SS`
- **Logger Name**: `native.<stage>.<movie>`
- **Log Level**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Function Name**: Where the log was generated (file logs only)
- **Line Number**: Exact line in source code (file logs only)
- **Message**: Descriptive log message

### ✅ Specialized Logging Methods

The `NativePipelineLogger` class provides specialized methods:

#### `log_stage_start(description)`
Logs the beginning of a stage with description
```python
logger.log_stage_start("FFmpeg audio extraction (16kHz mono)")
```

#### `log_stage_end(success)`
Logs the end of a stage with duration and status
```python
logger.log_stage_end(success=True)
```

#### `log_processing(description, duration)`
Logs a processing step with optional duration
```python
logger.log_processing("Audio extraction complete", duration)
```

#### `log_file_operation(operation, path, success)`
Logs file operations (create, read, write, delete)
```python
logger.log_file_operation("Saved audio file", output_file, success=True)
```

#### `log_model_load(model_name, device)`
Logs model loading operations
```python
logger.log_model_load("WhisperX", "mps")
```

#### `log_metric(name, value, unit)`
Logs metrics and measurements
```python
logger.log_metric("Audio file size", "281.12", "MB")
logger.log_metric("Segments detected", 42)
```

#### `log_progress(current, total, item)`
Logs progress through iterative tasks
```python
logger.log_progress(current=50, total=100, item="frames")
```

## Log Format Examples

### Console Output (Human-Readable)
```
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [INFO] ============================================================
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [INFO] Native MPS Pipeline - Stage: DEMUX
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [INFO] Movie: Jaane_Tu_Ya_Jaane_Na_2008
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [INFO] Started at: 2025-10-29 17:54:27
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [INFO] ▶️  Stage starting: FFmpeg audio extraction (16kHz mono)
[2025-10-29 17:54:39] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [INFO] ⚙️  Audio extraction complete (11.32s)
[2025-10-29 17:54:39] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [INFO] ✓ Created audio file: out/Jaane_Tu_Ya_Jaane_Na_2008/audio/audio.wav
[2025-10-29 17:54:39] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [INFO] 📊 Audio file size: 281.12 MB
[2025-10-29 17:54:39] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [INFO] ✅ Stage completed successfully in 11.33s
```

### File Output (Detailed with Function Names)
```
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [INFO] [__init__:141] ============================================================
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [INFO] [__init__:142] Native MPS Pipeline - Stage: DEMUX
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [DEBUG] [setup_native_logger:80] Logger initialized: native.demux.Jaane_Tu_Ya_Jaane_Na_2008
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [DEBUG] [setup_native_logger:81] Log file: logs/demux_Jaane_Tu_Ya_Jaane_Na_2008_20251029_175427.log
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [DEBUG] [main:57] Created audio directory: out/Jaane_Tu_Ya_Jaane_Na_2008/audio
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [DEBUG] [demux_audio:24] Input file: in/Jaane Tu Ya Jaane Na 2008.mp4
[2025-10-29 17:54:27] [native.demux.Jaane_Tu_Ya_Jaane_Na_2008] [DEBUG] [demux_audio:32] FFmpeg command: ffmpeg -i in/Jaane Tu Ya Jaane Na 2008.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 -y out/Jaane_Tu_Ya_Jaane_Na_2008/audio/audio.wav
```

## Usage in Stage Scripts

### Basic Usage
```python
from native_logger import NativePipelineLogger

# Initialize logger
logger = NativePipelineLogger('stage-name', 'Movie_Name_2024')

try:
    logger.log_stage_start("Stage description")
    
    # Your stage processing here
    logger.info("Processing started")
    logger.debug("Detailed debug information")
    
    logger.log_stage_end(success=True)
    
except Exception as e:
    logger.error(f"Stage failed: {e}")
    logger.log_stage_end(success=False)
    raise
```

### Advanced Usage with Metrics
```python
from native_logger import NativePipelineLogger
import time

logger = NativePipelineLogger('asr', 'My_Movie_2024')

try:
    logger.log_stage_start("WhisperX ASR + Forced Alignment")
    
    # Load model
    logger.log_model_load("WhisperX Large-v2", "mps")
    
    # Process segments
    total_segments = 100
    for i, segment in enumerate(segments, 1):
        # Process segment
        start = time.time()
        result = process_segment(segment)
        duration = time.time() - start
        
        # Log progress
        logger.log_progress(i, total_segments, "segments")
        logger.log_processing(f"Segment {i} processed", duration)
    
    # Log final metrics
    logger.log_metric("Total segments", total_segments)
    logger.log_metric("Average time per segment", avg_time, "seconds")
    logger.log_metric("Word count", word_count)
    
    logger.log_stage_end(success=True)
    
except Exception as e:
    logger.error(f"ASR failed: {e}")
    logger.log_stage_end(success=False)
    raise
```

## Log Levels

### DEBUG
Detailed diagnostic information for debugging
- Function entry/exit
- Variable values
- Internal state changes

### INFO
General informational messages
- Stage start/end
- Progress updates
- Successful operations

### WARNING
Warning messages for non-critical issues
- Using fallback implementations
- Performance warnings
- Deprecated features

### ERROR
Error messages for recoverable errors
- Failed operations
- Validation failures
- External service errors

### CRITICAL
Critical errors that require immediate attention
- System failures
- Data corruption
- Unrecoverable errors

## Log Directory Structure

```
logs/
├── demux_Movie_Name_20251029_175427.log
├── tmdb_Movie_Name_20251029_175504.log
├── pre-ner_Movie_Name_20251029_175507.log
├── silero-vad_Movie_Name_20251029_175511.log
├── pyannote-vad_Movie_Name_20251029_175530.log
├── diarization_Movie_Name_20251029_175533.log
├── asr_Movie_Name_20251029_175537.log
├── post-ner_Movie_Name_20251029_175538.log
├── subtitle-gen_Movie_Name_20251029_175551.log
└── mux_Movie_Name_20251029_175551.log
```

## Log Retention

- Logs are never automatically deleted
- Developers should implement log rotation if needed
- Recommended: Archive logs older than 30 days
- Consider compressing old logs to save space

## Troubleshooting

### Missing Log Files
If log files are not created, check:
1. `logs/` directory exists and is writable
2. `python-json-logger` package is installed in venv
3. Logger is properly initialized in the script

### Incomplete Logs
If logs are truncated:
1. Check disk space
2. Ensure proper exception handling
3. Verify `log_stage_end()` is called

### Performance Impact
Logging has minimal performance impact:
- Console output: ~1-2ms per log entry
- File output: ~2-5ms per log entry
- Use DEBUG level sparingly in production

## Best Practices

1. **Always use try-except blocks** with `log_stage_end()`
2. **Log at appropriate levels** - use DEBUG for development, INFO for production
3. **Include context** in log messages (file names, IDs, sizes)
4. **Use specialized logging methods** for consistency
5. **Log metrics** for performance analysis
6. **Don't log sensitive data** (passwords, tokens, personal info)
7. **Use meaningful descriptions** in log messages

## JSON Logging Support

The logger supports JSON format for structured logging:

```python
logger = NativePipelineLogger('stage', 'movie', log_format='json')
```

JSON logs are ideal for:
- Log aggregation systems (ELK, Splunk)
- Automated log analysis
- Machine learning on logs

## Future Enhancements

- [ ] Log aggregation support
- [ ] Real-time log streaming
- [ ] Log search and filtering tools
- [ ] Performance dashboards
- [ ] Automatic log rotation
- [ ] Cloud storage integration
- [ ] Log-based alerts and notifications

## Related Documentation

- [Pipeline Architecture](arch/workflow-arch.txt)
- [Stage Implementation Guide](docs/STAGES.md)
- [Error Handling Guide](docs/ERROR_HANDLING.md)

---

**Last Updated**: 2025-10-29  
**Version**: 1.0.0  
**Maintainer**: Pipeline Team
