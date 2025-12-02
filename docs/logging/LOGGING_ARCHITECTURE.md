# Logging Architecture

## Overview

The pipeline implements a **dual logging architecture** with comprehensive manifest tracking:

1. **Main Pipeline Log** - High-level orchestration and progress tracking
2. **Stage-Specific Logs** - Detailed execution logs in each stage subdirectory
3. **Stage Manifests** - Structured tracking of inputs, outputs, and intermediate files

## Directory Structure

```
out/<job-id>/
├── logs/
│   └── 99_pipeline_20251127_140915.log    # Main orchestration log
├── 01_demux/
│   ├── stage.log                           # Stage-specific detailed log
│   ├── manifest.json                       # I/O tracking manifest
│   ├── audio.wav                           # Output file
│   └── metadata.json                       # Stage metadata
├── 02_tmdb/
│   ├── stage.log
│   ├── manifest.json
│   ├── enrichment.json
│   └── metadata.json
├── 03_source_separation/
│   ├── stage.log
│   ├── manifest.json
│   ├── vocals.wav
│   ├── accompaniment.wav                   # Intermediate (tracked)
│   └── metadata.json
└── ...
```

## Log Types

### 1. Main Pipeline Log

**Location:** `logs/99_pipeline_<timestamp>.log`

**Purpose:** High-level orchestration, stage transitions, overall progress

**Content:**
- Workflow execution flow
- Stage start/completion status
- Overall timing and resource usage
- Critical errors and warnings
- Summary statistics

**Log Levels:**
- `INFO` - Stage transitions, progress updates
- `WARNING` - Non-fatal issues
- `ERROR` - Stage failures, critical issues

**Example:**
```
[2025-11-27 14:09:15] [pipeline] [INFO] ================================================================================
[2025-11-27 14:09:15] [pipeline] [INFO] PIPELINE LOGGING ARCHITECTURE
[2025-11-27 14:09:15] [pipeline] [INFO] ================================================================================
[2025-11-27 14:09:15] [pipeline] [INFO] 📋 Main pipeline log: logs/99_pipeline_20251127_140915.log
[2025-11-27 14:09:15] [pipeline] [INFO] 📋 Stage logs: Each stage writes to its own subdirectory
[2025-11-27 14:09:15] [pipeline] [INFO] 📋 Stage manifests: Track inputs/outputs/intermediate files
[2025-11-27 14:09:15] [pipeline] [INFO]
[2025-11-27 14:09:16] [pipeline] [INFO] ▶️  Stage demux: STARTING
[2025-11-27 14:09:16] [pipeline] [INFO] 📥 Input: in/sample.mp4
[2025-11-27 14:09:16] [pipeline] [INFO] 📤 Output: 01_demux/audio.wav
[2025-11-27 14:09:20] [pipeline] [INFO] ✅ Stage demux: COMPLETED (4.2s)
```

### 2. Stage Logs

**Location:** `<stage_dir>/stage.log`

**Purpose:** Detailed stage execution, debugging information, tool output

**Content:**
- Detailed processing steps
- Tool command output (ffmpeg, whisperx, etc.)
- Configuration parameters
- Resource usage details
- Debug information
- File paths and sizes

**Log Levels:**
- `DEBUG` - All detailed steps (only in stage log)
- `INFO` - Progress within stage
- `WARNING` - Stage-specific warnings
- `ERROR` - Stage-specific errors

**Example:**
```
[2025-11-27 14:09:16] [demux] [INFO] Input media: /Users/user/in/sample.mp4
[2025-11-27 14:09:16] [demux] [INFO] Output directory: out/job_001/01_demux
[2025-11-27 14:09:16] [demux] [INFO] Full media extraction
[2025-11-27 14:09:16] [demux] [DEBUG] FFmpeg command: ffmpeg -y -loglevel error -i ...
[2025-11-27 14:09:20] [demux] [INFO] Successfully extracted audio: 45.3 MB
[2025-11-27 14:09:20] [demux] [INFO] Stage log: 01_demux/stage.log
[2025-11-27 14:09:20] [demux] [INFO] Stage manifest: 01_demux/manifest.json
```

### 3. Stage Manifests

**Location:** `<stage_dir>/manifest.json`

**Purpose:** Structured tracking of stage inputs, outputs, and intermediate files

**Schema:**
```json
{
  "stage": "demux",
  "stage_number": 1,
  "timestamp": "2025-11-27T14:09:16.123456",
  "status": "success",
  "duration_seconds": 4.2,
  "completed_at": "2025-11-27T14:09:20.345678",
  
  "inputs": [
    {
      "type": "video",
      "path": "/Users/user/in/sample.mp4",
      "size_bytes": 52428800,
      "format": "mp4"
    }
  ],
  
  "outputs": [
    {
      "type": "audio",
      "path": "out/job_001/01_demux/audio.wav",
      "size_bytes": 47493120,
      "format": "wav",
      "sample_rate": 16000,
      "channels": 1,
      "size_mb": 45.3
    }
  ],
  
  "intermediate_files": [],
  
  "config": {
    "processing_mode": "full",
    "start_time": "",
    "end_time": "",
    "sample_rate": "16000",
    "channels": "1"
  },
  
  "resources": {},
  
  "errors": [],
  "warnings": []
}
```

**Manifest Fields:**

- **stage** - Stage name (e.g., "demux", "asr", "translation")
- **stage_number** - Sequential stage number (1-based)
- **timestamp** - Stage start time (ISO 8601)
- **status** - Execution status: "running", "success", "failed", "skipped"
- **duration_seconds** - Total execution time
- **completed_at** - Stage completion time (ISO 8601)

**inputs** array:
- **type** - File type: "audio", "video", "transcript", "metadata", etc.
- **path** - Absolute or relative path to input file
- **size_bytes** - File size in bytes
- Custom metadata (format, sample_rate, etc.)

**outputs** array:
- **type** - File type: "audio", "transcript", "subtitle", etc.
- **path** - Path to output file
- **size_bytes** - File size in bytes
- Custom metadata

**intermediate_files** array:
- **type** - Always "intermediate"
- **path** - Path to intermediate file
- **retained** - Boolean, whether file is kept after stage
- **reason** - Explanation for creation/retention
- **size_bytes** - File size

**config** object:
- Stage-specific configuration parameters

**resources** object:
- Resource usage (cpu_percent, memory_mb, gpu_used, etc.)

**errors** array:
- **timestamp** - Error occurrence time
- **message** - Error description
- **exception_type** - Exception class name
- **exception_detail** - Exception details

**warnings** array:
- **timestamp** - Warning occurrence time
- **message** - Warning description

## Implementation Guide

### For Stage Developers

#### 1. Initialize Stage I/O

```python
from shared.stage_utils import StageIO

def my_stage_function():
    # Initialize stage I/O with manifest tracking
    stage_io = StageIO("my_stage", job_dir, enable_manifest=True)
    
    # Get dual logger (writes to stage.log + pipeline log)
    logger = stage_io.get_stage_logger("DEBUG" if debug else "INFO")
```

#### 2. Track Inputs

```python
# Track input files in manifest
input_file = Path("input/data.json")
stage_io.track_input(input_file, "transcript", format="json")

# Multiple inputs
for input_file in input_files:
    stage_io.track_input(input_file, "audio", format="wav")
```

#### 3. Track Outputs

```python
# Track output files in manifest
output_file = stage_io.get_output_path("result.json")
process_data(input_file, output_file)

stage_io.track_output(output_file, "transcript", 
                      format="json",
                      segments=len(segments))
```

#### 4. Track Intermediate Files

```python
# Track intermediate/cache files
cache_file = stage_io.get_output_path("model_cache.bin")
download_model(cache_file)

stage_io.track_intermediate(cache_file, 
                            retained=True,
                            reason="Model cache for faster subsequent runs")

# Temporary files (not retained)
temp_file = stage_io.get_output_path("temp_processing.wav")
process_audio(temp_file)

stage_io.track_intermediate(temp_file,
                            retained=False,
                            reason="Temporary processing file")
```

#### 5. Add Configuration

```python
# Track stage configuration
stage_io.set_config({
    "model": "whisper-large-v3",
    "device": "mps",
    "batch_size": 16,
    "compute_type": "float32"
})

# Add individual config items
stage_io.add_config("language", "hi")
```

#### 6. Handle Errors and Warnings

```python
try:
    process_data()
except Exception as e:
    # Log error to both logger and manifest
    logger.error(f"Processing failed: {e}")
    stage_io.add_error("Processing failed", e)
    stage_io.finalize(status="failed")
    return False

# Non-fatal warnings
if not optimal_config:
    logger.warning("Suboptimal configuration detected")
    stage_io.add_warning("Using default configuration")
```

#### 7. Finalize Stage

```python
# Success case
stage_io.finalize(status="success", 
                 segments_processed=len(segments),
                 model_version="1.0.0")
logger.info(f"Stage completed successfully")
return True

# Failure case
stage_io.finalize(status="failed",
                 error_message="Model loading failed")
return False

# Skipped case
stage_io.finalize(status="skipped",
                 reason="Feature disabled by user")
return True
```

### Complete Stage Example

```python
def _stage_asr(self) -> bool:
    """Stage: Automatic Speech Recognition"""
    from shared.stage_utils import StageIO
    
    # 1. Initialize
    stage_io = StageIO("asr", self.job_dir, enable_manifest=True)
    logger = stage_io.get_stage_logger("DEBUG" if self.debug else "INFO")
    
    # 2. Get input/output paths
    audio_input = stage_io.get_input_path("audio.wav", from_stage="demux")
    segments_output = stage_io.get_output_path("segments.json")
    
    # 3. Track inputs
    stage_io.track_input(audio_input, "audio", format="wav")
    
    # 4. Configure stage
    config = {
        "model": "whisper-large-v3",
        "device": "mps",
        "language": "hi",
        "batch_size": 16
    }
    stage_io.set_config(config)
    
    logger.info(f"Input: {audio_input}")
    logger.info(f"Output: {segments_output}")
    logger.info(f"Model: {config['model']}")
    
    try:
        # 5. Process
        segments = transcribe_audio(audio_input, **config)
        
        # Save output
        with open(segments_output, 'w') as f:
            json.dump(segments, f, indent=2)
        
        # 6. Track outputs
        stage_io.track_output(segments_output, "transcript",
                             format="json",
                             segments=len(segments))
        
        # 7. Finalize with success
        stage_io.finalize(status="success",
                         segments_count=len(segments))
        
        logger.info(f"✓ Transcribed {len(segments)} segments")
        return True
        
    except Exception as e:
        # 8. Handle errors
        logger.error(f"Transcription failed: {e}")
        stage_io.add_error("Transcription failed", e)
        stage_io.finalize(status="failed")
        return False
```

## Benefits

### 1. Clear Audit Trail
- Every stage documents exactly what files it used
- Easy to trace data flow through pipeline
- Clear record of intermediate files and their purpose

### 2. Debugging
- Main log: Quick overview of where pipeline failed
- Stage log: Detailed debugging information for specific stage
- Manifest: See exactly what inputs were used, what outputs were created

### 3. Reproducibility
- Manifests document exact configuration used
- Clear record of file transformations
- Easy to replay specific stages

### 4. Resource Tracking
- Monitor stage-level resource usage
- Identify bottlenecks
- Optimize resource allocation

### 5. Compliance
- Complete audit trail for production workflows
- Documentation of data lineage
- Error tracking and reporting

## Log Analysis

### Find Pipeline Issues
```bash
# Check main pipeline log for failures
grep "FAILED" logs/99_pipeline_*.log

# Find which stage failed
grep "❌ Stage" logs/99_pipeline_*.log
```

### Debug Specific Stage
```bash
# Read stage log for details
cat 04_asr/stage.log

# Check stage manifest for I/O
cat 04_asr/manifest.json | jq .

# See what inputs were used
cat 04_asr/manifest.json | jq '.inputs'

# See what outputs were created
cat 04_asr/manifest.json | jq '.outputs'

# Check for errors
cat 04_asr/manifest.json | jq '.errors'
```

### Validate Data Flow
```bash
# Check all stage manifests for missing outputs
for manifest in */manifest.json; do
  echo "Stage: $manifest"
  jq -r '.outputs[] | .path' "$manifest"
done

# Verify intermediate files
jq -r '.intermediate_files[] | "\(.path) - \(.retained) - \(.reason)"' \
  */manifest.json
```

## Migration Guide

### Updating Existing Stages

1. **Import StageIO:**
   ```python
   from shared.stage_utils import StageIO
   ```

2. **Initialize at stage start:**
   ```python
   stage_io = StageIO("stage_name", job_dir, enable_manifest=True)
   logger = stage_io.get_stage_logger()
   ```

3. **Replace hard-coded paths:**
   ```python
   # Before:
   output_dir = job_dir / "04_asr"
   output_file = output_dir / "segments.json"
   
   # After:
   output_file = stage_io.get_output_path("segments.json")
   ```

4. **Add tracking calls:**
   ```python
   stage_io.track_input(input_file, "audio")
   stage_io.track_output(output_file, "transcript")
   stage_io.set_config(config_dict)
   ```

5. **Finalize before return:**
   ```python
   stage_io.finalize(status="success")
   return True
   ```

## Best Practices

1. **Always use StageIO** for file path management
2. **Track all inputs** - even configuration files
3. **Track all outputs** - including copied files
4. **Document intermediate files** - explain why they exist
5. **Use descriptive file types** - "audio", "transcript", not just "file"
6. **Add custom metadata** - format, size, counts, etc.
7. **Log to both loggers** - stage log for details, pipeline log for progress
8. **Finalize every stage** - even on failure/skip
9. **Include configuration** - make stages reproducible
10. **Handle errors gracefully** - log, track in manifest, finalize

## Future Enhancements

- [ ] Resource usage tracking (CPU, memory, GPU)
- [ ] Automatic checksum calculation for data integrity
- [ ] Stage dependency graph generation
- [ ] Interactive log viewer
- [ ] Automated validation of manifest completeness
- [ ] Performance profiling per stage
- [ ] Cost tracking (API calls, compute time)
