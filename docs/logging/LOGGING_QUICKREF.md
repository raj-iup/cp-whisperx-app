# Logging Quick Reference

## TL;DR

**Three log types per pipeline run:**
1. **Main log:** `logs/99_pipeline_*.log` - Overall progress
2. **Stage logs:** `<stage_dir>/stage.log` - Detailed execution  
3. **Manifests:** `<stage_dir>/manifest.json` - I/O tracking

## Stage Template

```python
from shared.stage_utils import StageIO

def _stage_my_stage(self) -> bool:
    """Stage: Brief description"""
    # 1. Setup
    stage_io = StageIO("my_stage", self.job_dir, enable_manifest=True)
    logger = stage_io.get_stage_logger("DEBUG" if self.debug else "INFO")
    
    # 2. Get paths
    input_file = stage_io.get_input_path("input.json", from_stage="previous_stage")
    output_file = stage_io.get_output_path("output.json")
    
    # 3. Track inputs
    stage_io.track_input(input_file, "transcript", format="json")
    
    # 4. Configure
    stage_io.set_config({
        "parameter1": value1,
        "parameter2": value2
    })
    
    # 5. Log
    self.logger.info(f"📥 Input: {input_file.relative_to(self.job_dir)}")
    self.logger.info(f"📤 Output: {output_file.relative_to(self.job_dir)}")
    logger.info(f"Processing {input_file}")
    
    try:
        # 6. Process
        result = process(input_file, output_file)
        
        # 7. Track outputs
        stage_io.track_output(output_file, "transcript", 
                             format="json",
                             items=len(result))
        
        # 8. Finalize success
        stage_io.finalize(status="success", items_processed=len(result))
        self.logger.info(f"✓ Processed {len(result)} items")
        logger.info(f"Stage completed: {stage_io.stage_log}")
        return True
        
    except Exception as e:
        # 9. Handle failure
        logger.error(f"Processing failed: {e}")
        stage_io.add_error("Processing failed", e)
        stage_io.finalize(status="failed")
        return False
```

## Common Operations

### Track Input
```python
stage_io.track_input(file_path, file_type, **metadata)

# Examples:
stage_io.track_input(audio_file, "audio", format="wav", sample_rate=16000)
stage_io.track_input(transcript, "transcript", format="json", segments=150)
stage_io.track_input(config_file, "config", format="json")
```

### Track Output
```python
stage_io.track_output(file_path, file_type, **metadata)

# Examples:
stage_io.track_output(result_file, "transcript", format="json", segments=150)
stage_io.track_output(srt_file, "subtitle", format="srt", language="hi")
stage_io.track_output(video_file, "video", format="mp4", size_mb=450.5)
```

### Track Intermediate File
```python
stage_io.track_intermediate(file_path, retained=True/False, reason="why")

# Examples:
stage_io.track_intermediate(cache_file, retained=True, 
                            reason="Model cache for faster runs")
stage_io.track_intermediate(temp_file, retained=False,
                            reason="Temporary processing file")
```

### Configure Stage
```python
# Set all config at once
stage_io.set_config({
    "model": "whisper-large-v3",
    "device": "mps",
    "batch_size": 16
})

# Add individual items
stage_io.add_config("language", "hi")
stage_io.add_config("compute_type", "float32")
```

### Log Messages
```python
# Pipeline log (INFO and above go here + console)
self.logger.info("High-level progress update")
self.logger.warning("Non-fatal issue")
self.logger.error("Stage failed")

# Stage log (ALL levels go here, including DEBUG)
logger.debug("Detailed processing step")  # Only in stage.log
logger.info("Stage progress")             # In stage.log + pipeline.log
logger.warning("Stage warning")           # In stage.log + pipeline.log
logger.error("Stage error")               # In stage.log + pipeline.log
```

### Handle Errors
```python
try:
    process()
except Exception as e:
    logger.error(f"Processing failed: {e}")
    stage_io.add_error("Processing failed", e)  # Adds to manifest
    stage_io.finalize(status="failed")
    return False
```

### Add Warnings
```python
if not optimal:
    logger.warning("Using suboptimal configuration")
    stage_io.add_warning("Using default config")  # Adds to manifest
```

### Finalize Stage
```python
# Success
stage_io.finalize(status="success", extra_field=value)
return True

# Failure  
stage_io.finalize(status="failed", error_message="reason")
return False

# Skipped
stage_io.finalize(status="skipped", reason="disabled")
return True
```

## File Type Constants

Common file types to use:

- `"audio"` - Audio files (.wav, .mp3, .flac)
- `"video"` - Video files (.mp4, .mkv, .avi)
- `"transcript"` - Transcript data (.json, .txt)
- `"subtitle"` - Subtitle files (.srt, .vtt)
- `"metadata"` - Metadata files (.json)
- `"config"` - Configuration files (.json, .yaml)
- `"model"` - Model files (.pt, .bin)
- `"cache"` - Cache files
- `"intermediate"` - Temporary/intermediate files

## Path Helpers

```python
# Get input from previous stage
input_file = stage_io.get_input_path("file.json")

# Get input from specific stage
input_file = stage_io.get_input_path("file.json", from_stage="demux")

# Get output path in this stage's directory
output_file = stage_io.get_output_path("result.json")

# Load JSON from previous stage
data = stage_io.load_json("data.json")
data = stage_io.load_json("data.json", from_stage="asr")

# Save JSON to this stage's directory
stage_io.save_json(data, "output.json")

# Save metadata
stage_io.save_metadata({"key": "value"})

# Get all inputs from previous stage
input_files = stage_io.get_all_inputs()
```

## Debugging

### View Main Log
```bash
# Latest pipeline run
ls -t logs/99_pipeline_*.log | head -1 | xargs cat

# Find failures
grep "❌ Stage" logs/99_pipeline_*.log
grep "FAILED" logs/99_pipeline_*.log
```

### View Stage Log
```bash
# Specific stage
cat 04_asr/stage.log

# Search for errors
grep ERROR 04_asr/stage.log
grep -i "failed" 04_asr/stage.log
```

### View Stage Manifest
```bash
# Pretty print
cat 04_asr/manifest.json | jq .

# View inputs
cat 04_asr/manifest.json | jq '.inputs'

# View outputs
cat 04_asr/manifest.json | jq '.outputs'

# View config
cat 04_asr/manifest.json | jq '.config'

# Check errors
cat 04_asr/manifest.json | jq '.errors'

# Check warnings
cat 04_asr/manifest.json | jq '.warnings'

# View intermediate files
cat 04_asr/manifest.json | jq '.intermediate_files'
```

### Trace Data Flow
```bash
# See all outputs across stages
for manifest in */manifest.json; do
  echo "=== $(dirname $manifest) ==="
  jq -r '.outputs[] | "\(.type): \(.path)"' "$manifest"
done

# Verify output became next stage's input
cat 04_asr/manifest.json | jq '.outputs[0].path'
cat 05_alignment/manifest.json | jq '.inputs[0].path'
```

## Common Patterns

### Optional Input
```python
# Try multiple locations
input_file = stage_io.get_input_path("enhanced.json")
if not input_file.exists():
    input_file = stage_io.get_input_path("original.json")

stage_io.track_input(input_file, "transcript")
```

### Multiple Outputs
```python
# Track each output file
for lang in ["hi", "en", "gu"]:
    output_file = stage_io.get_output_path(f"subtitle_{lang}.srt")
    generate_subtitle(output_file, lang)
    stage_io.track_output(output_file, "subtitle", 
                          format="srt",
                          language=lang)
```

### Conditional Processing
```python
if feature_enabled:
    result = process_with_feature()
    stage_io.add_config("feature_enabled", True)
else:
    result = process_without_feature()
    stage_io.add_config("feature_enabled", False)
    stage_io.add_warning("Feature disabled, using fallback")
```

### Resource Tracking
```python
import time
import psutil

start_time = time.time()
start_memory = psutil.Process().memory_info().rss / 1024 / 1024

# Process...

duration = time.time() - start_time
memory_used = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory

stage_io.set_resources(
    duration_seconds=duration,
    memory_mb=memory_used,
    gpu_used=True
)
```

## Migration Checklist

Converting an existing stage:

- [ ] Import `from shared.stage_utils import StageIO`
- [ ] Initialize `stage_io = StageIO("stage_name", job_dir, enable_manifest=True)`
- [ ] Get logger with `stage_io.get_stage_logger()`
- [ ] Replace hard-coded paths with `stage_io.get_*_path()`
- [ ] Add `stage_io.track_input()` for each input file
- [ ] Add `stage_io.track_output()` for each output file
- [ ] Add `stage_io.track_intermediate()` for cache/temp files
- [ ] Add `stage_io.set_config()` with stage parameters
- [ ] Update logging to use both `self.logger` and `logger`
- [ ] Add `stage_io.finalize()` before each return
- [ ] Test stage execution
- [ ] Verify manifest.json is created
- [ ] Verify stage.log contains details

## Tips

1. **Use descriptive file types** - helps with debugging
2. **Include custom metadata** - format, counts, sizes
3. **Log important paths** - makes troubleshooting easier  
4. **Track intermediate files** - document what they're for
5. **Always finalize** - even on failure/skip
6. **Use stage logger for details** - DEBUG goes only to stage.log
7. **Use pipeline logger for progress** - INFO goes to main log
8. **Add configuration** - makes stages reproducible
9. **Document warnings** - help future debugging
10. **Test manifest structure** - use `jq` to validate

## See Also

- [Full Logging Architecture Documentation](LOGGING_ARCHITECTURE.md)
- [Stage Development Guide](developer/STAGE_DEVELOPMENT.md)
- [Developer Standards](DEVELOPER_STANDARDS.md)
