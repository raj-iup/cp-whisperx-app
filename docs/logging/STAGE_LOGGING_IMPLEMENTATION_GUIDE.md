# Stage Logging & Manifest Implementation Guide

**Version:** 1.0  
**Date:** November 27, 2025  
**Status:** READY FOR IMPLEMENTATION

---

## 📋 Quick Start

### For New Stages

```python
#!/usr/bin/env python3
"""Stage: example - Example stage implementation"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.stage_utils import StageIO

def main():
    # Initialize stage I/O (enables manifest + dual logging)
    io = StageIO("example")
    logger = io.get_stage_logger()
    
    try:
        logger.info("Starting example stage")
        
        # Track input
        input_file = io.get_input_path("input.json", from_stage="previous_stage")
        io.track_input(input_file, "json", description="Input data")
        
        # Process
        logger.info("Processing data...")
        output_file = io.get_output_path("output.json")
        # ... your processing logic ...
        
        # Track output
        io.track_output(output_file, "json", description="Processed data")
        logger.info(f"Generated output: {output_file}")
        
        # Finalize
        io.finalize(status="success")
        logger.info("Stage complete")
        return 0
        
    except Exception as e:
        logger.error(f"Stage failed: {e}", exc_info=True)
        io.add_error(str(e), e)
        io.finalize(status="failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### For Existing Stages (Migration)

**Before:**
```python
from shared.logger import PipelineLogger

logger = PipelineLogger("asr")
logger.info("Starting ASR")
```

**After:**
```python
from shared.stage_utils import StageIO

io = StageIO("asr")
logger = io.get_stage_logger()
logger.info("Starting ASR")

# Track files
io.track_input(audio_file, "audio")
io.track_output(transcript_file, "transcript")
io.finalize(status="success")
```

---

## 🎯 Implementation Checklist

### Phase 1: Core Infrastructure ✅ COMPLETE

- [x] `StageManifest` class (`shared/stage_manifest.py`)
- [x] `setup_dual_logger()` function (`shared/logger.py`)
- [x] Enhanced `StageIO` class (`shared/stage_utils.py`)
- [x] Architecture documentation
- [x] Implementation guide

### Phase 2: Stage Migration (Priority Order)

#### High Priority Stages (Complex + Frequently Debugged)

- [ ] **Stage 6: asr** (`scripts/whisperx_asr.py`)
  - **Why First:** Most complex, frequently fails, needs best debugging
  - **Changes:** Add I/O tracking, cache file tracking, model downloads
  - **Estimated Time:** 30 minutes

- [ ] **Stage 7: alignment** (`scripts/mlx_alignment.py`)
  - **Why Second:** Complex MLX backend, platform-specific issues
  - **Changes:** Track alignment inputs/outputs, intermediate files
  - **Estimated Time:** 20 minutes

- [ ] **Stage 8: lyrics_detection** (`scripts/lyrics_detection.py`)
  - **Why Third:** Complex logic, multiple outputs
  - **Changes:** Track detection results, confidence scores
  - **Estimated Time:** 20 minutes

#### Medium Priority Stages (Standard Processing)

- [ ] **Stage 1: demux** (`scripts/demux.py`)
  - **Changes:** Track media input, audio output
  - **Estimated Time:** 15 minutes

- [ ] **Stage 2: tmdb** (`scripts/tmdb_enrichment_stage.py`)
  - **Changes:** Track TMDB API calls, metadata
  - **Estimated Time:** 15 minutes

- [ ] **Stage 4: source_separation** (`scripts/source_separation.py`)
  - **Changes:** Track separated audio files
  - **Estimated Time:** 15 minutes

- [ ] **Stage 5: pyannote_vad** (`scripts/pyannote_vad.py`)
  - **Changes:** Track VAD segments
  - **Estimated Time:** 15 minutes

#### Lower Priority Stages (Simple/Working Well)

- [ ] **Stage 3: glossary_load** (`scripts/glossary_builder.py`)
- [ ] **Stage 10: translation** (`scripts/translation.py`)
- [ ] **Stage 11: subtitle_generation** (`scripts/subtitle_gen.py`)
- [ ] **Stage 12: mux** (`scripts/mux.py`)

### Phase 3: Testing & Validation

- [ ] Test dual logging (verify both logs are written)
- [ ] Test manifest generation (verify JSON structure)
- [ ] Test I/O tracking (verify file lineage)
- [ ] Test error handling (verify errors recorded in manifest)
- [ ] Test backward compatibility (existing code still works)

### Phase 4: Documentation Updates

- [ ] Update stage development guide
- [ ] Add troubleshooting guide using new logs
- [ ] Update quickstart examples
- [ ] Add manifest API reference

---

## 📝 Detailed Migration Steps

### Step 1: Update Imports

**Add:**
```python
from shared.stage_utils import StageIO
```

**Remove (optional - for now keep for compatibility):**
```python
from shared.logger import PipelineLogger  # Can keep for now
```

### Step 2: Replace Logger Initialization

**Before:**
```python
logger = PipelineLogger("stage_name")
```

**After:**
```python
io = StageIO("stage_name")
logger = io.get_stage_logger()
```

### Step 3: Add I/O Tracking

**Track Inputs:**
```python
# Track required input
input_file = io.get_input_path("audio.wav", from_stage="demux")
io.track_input(input_file, "audio", format="wav", sample_rate=48000)

# Track optional input (check existence)
glossary_file = io.get_input_path("glossary.json", from_stage="glossary_load")
if glossary_file.exists():
    io.track_input(glossary_file, "glossary")
```

**Track Outputs:**
```python
# Track main output
output_file = io.get_output_path("transcript.json")
# ... generate output ...
io.track_output(output_file, "transcript", 
               format="whisperx", segments=len(segments))

# Track additional outputs
srt_file = io.get_output_path("transcript.srt")
io.track_output(srt_file, "subtitle", format="srt")
```

**Track Intermediate Files:**
```python
# Track cached model
model_cache = Path.home() / ".cache" / "whisperx" / "large-v2"
if model_cache.exists():
    io.track_intermediate(model_cache, retained=True,
                         reason="WhisperX model cache for future runs")

# Track temporary file
temp_file = io.stage_dir / ".temp" / "processing.wav"
io.track_intermediate(temp_file, retained=False,
                     reason="Temporary audio processing buffer")
```

### Step 4: Add Configuration Tracking

```python
# Track configuration used
io.set_config({
    "model": "large-v2",
    "device": "cuda",
    "batch_size": 16,
    "language": "hi"
})
```

### Step 5: Add Error/Warning Tracking

```python
# Add warnings
if quality_score < 0.5:
    warning_msg = f"Low quality audio detected: {quality_score}"
    logger.warning(warning_msg)
    io.add_warning(warning_msg)

# Add errors
try:
    result = process_audio(audio_file)
except Exception as e:
    logger.error(f"Processing failed: {e}")
    io.add_error(f"Processing failed: {e}", e)
    io.finalize(status="failed")
    raise
```

### Step 6: Add Resource Tracking (Optional)

```python
import psutil

# Track resource usage
process = psutil.Process()
io.set_resources(
    cpu_percent=process.cpu_percent(),
    memory_mb=process.memory_info().rss / 1024 / 1024,
    gpu_used=torch.cuda.is_available()
)
```

### Step 7: Finalize Stage

```python
# Success case
io.finalize(status="success")
logger.info("Stage complete")

# Failure case
io.finalize(status="failed", error=str(e))
logger.error("Stage failed")

# Skip case
io.finalize(status="skipped", reason="No input files")
logger.info("Stage skipped")
```

---

## 🔍 Testing Your Changes

### Test 1: Verify Dual Logging

```bash
# Run your stage
./run-pipeline.sh

# Check stage log exists
ls -l out/*/baseline/1/06_asr/stage.log

# Check main log exists
ls -l out/*/baseline/1/logs/99_pipeline_*.log

# Verify DEBUG messages only in stage log
grep "DEBUG" out/*/baseline/1/06_asr/stage.log
grep "DEBUG" out/*/baseline/1/logs/99_pipeline_*.log  # Should be empty

# Verify INFO messages in both logs
grep "INFO" out/*/baseline/1/06_asr/stage.log
grep "INFO" out/*/baseline/1/logs/99_pipeline_*.log
```

### Test 2: Verify Manifest Generation

```bash
# Check manifest exists
ls -l out/*/baseline/1/06_asr/manifest.json

# View manifest
cat out/*/baseline/1/06_asr/manifest.json | jq .

# Verify structure
jq '.inputs, .outputs, .intermediate_files' out/*/baseline/1/06_asr/manifest.json
```

### Test 3: Verify I/O Tracking

```python
# Load and inspect manifest
import json
with open('out/.../06_asr/manifest.json') as f:
    manifest = json.load(f)

# Check inputs tracked
assert len(manifest['inputs']) > 0
print("Inputs:", [i['path'] for i in manifest['inputs']])

# Check outputs tracked
assert len(manifest['outputs']) > 0
print("Outputs:", [o['path'] for o in manifest['outputs']])

# Check intermediate files tracked
print("Intermediate:", [i['path'] for i in manifest['intermediate_files']])
```

### Test 4: Verify Error Handling

```bash
# Cause intentional error (e.g., missing input)
rm out/*/baseline/1/04_source_separation/audio.wav

# Run stage
./run-pipeline.sh

# Check error in manifest
jq '.errors' out/*/baseline/1/06_asr/manifest.json

# Check status
jq '.status' out/*/baseline/1/06_asr/manifest.json  # Should be "failed"
```

---

## 🎨 Common Patterns

### Pattern 1: Simple Stage (One Input → One Output)

```python
def main():
    io = StageIO("simple_stage")
    logger = io.get_stage_logger()
    
    try:
        logger.info("Processing")
        
        # Input
        input_file = io.get_input_path("input.json")
        io.track_input(input_file, "json")
        data = io.load_json("input.json")
        
        # Process
        result = process(data)
        
        # Output
        output_file = io.save_json(result, "output.json")
        io.track_output(output_file, "json")
        
        # Done
        io.finalize(status="success")
        return 0
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        io.finalize(status="failed")
        return 1
```

### Pattern 2: Complex Stage (Multiple Inputs/Outputs)

```python
def main():
    io = StageIO("complex_stage")
    logger = io.get_stage_logger()
    
    try:
        logger.info("Starting complex processing")
        
        # Multiple inputs
        audio = io.get_input_path("audio.wav", from_stage="demux")
        metadata = io.get_input_path("metadata.json", from_stage="demux")
        glossary = io.get_input_path("glossary.json", from_stage="glossary_load")
        
        io.track_input(audio, "audio")
        io.track_input(metadata, "metadata")
        if glossary.exists():
            io.track_input(glossary, "glossary")
        
        # Process with cache
        cache_dir = io.stage_dir / ".cache"
        cache_dir.mkdir(exist_ok=True)
        
        model_path = cache_dir / "model.bin"
        if not model_path.exists():
            logger.info("Downloading model...")
            download_model(model_path)
        io.track_intermediate(model_path, retained=True,
                             reason="Cached model for reuse")
        
        # Multiple outputs
        result1 = process_primary(audio)
        result2 = process_secondary(audio)
        
        output1 = io.save_json(result1, "primary.json")
        output2 = io.save_json(result2, "secondary.json")
        
        io.track_output(output1, "result", type="primary")
        io.track_output(output2, "result", type="secondary")
        
        # Configuration
        io.set_config({
            "model": "large-v2",
            "used_glossary": glossary.exists()
        })
        
        # Done
        io.finalize(status="success")
        return 0
        
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        io.add_error(str(e), e)
        io.finalize(status="failed")
        return 1
```

### Pattern 3: Optional Stage (Can Be Skipped)

```python
def main():
    io = StageIO("optional_stage")
    logger = io.get_stage_logger()
    
    try:
        # Check if stage should run
        enable_feature = os.environ.get("ENABLE_FEATURE", "false").lower() == "true"
        
        if not enable_feature:
            logger.info("Feature disabled, skipping stage")
            io.finalize(status="skipped", reason="Feature flag disabled")
            return 0
        
        # Normal processing
        logger.info("Feature enabled, processing")
        # ... processing logic ...
        
        io.finalize(status="success")
        return 0
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        io.finalize(status="failed")
        return 1
```

---

## 🐛 Troubleshooting

### Issue: No stage.log created

**Cause:** StageIO not initialized or logger not used
**Fix:** Ensure you call `io.get_stage_logger()` and use the returned logger

### Issue: Manifest empty or missing fields

**Cause:** Forgot to call `io.track_input()`, `io.track_output()`, or `io.finalize()`
**Fix:** Add tracking calls throughout your stage

### Issue: Logs duplicated to console

**Cause:** Multiple handler registration
**Fix:** Don't create additional handlers, use `io.get_stage_logger()` only once

### Issue: Permission denied writing logs

**Cause:** Stage directory not writable
**Fix:** Check OUTPUT_DIR permissions, ensure stage can create subdirectories

### Issue: Manifest shows wrong status

**Cause:** Didn't call `io.finalize()`
**Fix:** Always call `io.finalize()` at the end (both success and failure cases)

---

## 📚 API Reference

### StageIO

```python
class StageIO:
    def __init__(self, stage_name: str, output_base: Optional[Path] = None,
                 enable_manifest: bool = True)
    
    def get_stage_logger(self, log_level: str = "INFO") -> logging.Logger
    def get_input_path(self, filename: str, from_stage: Optional[str] = None) -> Path
    def get_output_path(self, filename: str) -> Path
    
    def track_input(self, file_path: Path, file_type: str = "file", **metadata)
    def track_output(self, file_path: Path, file_type: str = "file", **metadata)
    def track_intermediate(self, file_path: Path, retained: bool = False, reason: str = "")
    
    def add_config(self, key: str, value: Any)
    def set_config(self, config_dict: Dict[str, Any])
    def add_warning(self, message: str)
    def add_error(self, message: str, exception: Optional[Exception] = None)
    def set_resources(self, **resources)
    
    def finalize(self, status: str = "success", save_manifest: bool = True, **kwargs)
    
    def save_json(self, data: Any, filename: str) -> Path
    def load_json(self, filename: str, from_stage: Optional[str] = None) -> Any
    def save_metadata(self, metadata: Dict[str, Any]) -> Path
```

### StageManifest

```python
class StageManifest:
    def __init__(self, stage_name: str, stage_number: int)
    
    def add_input(self, file_path: Path, file_type: str = "file", **metadata)
    def add_output(self, file_path: Path, file_type: str = "file", **metadata)
    def add_intermediate(self, file_path: Path, retained: bool = False, reason: str = "")
    
    def add_config(self, key: str, value: Any)
    def set_config(self, config_dict: Dict[str, Any])
    
    def add_warning(self, message: str)
    def add_error(self, message: str, exception: Optional[Exception] = None)
    def set_resources(self, **resources)
    
    def finalize(self, status: str = "success", **kwargs)
    def save(self, path: Path)
    def load(self, path: Path)
    
    def to_dict(self) -> Dict[str, Any]
    def get_inputs(self) -> List[Dict[str, Any]]
    def get_outputs(self) -> List[Dict[str, Any]]
    def get_intermediate_files(self) -> List[Dict[str, Any]]
    def has_errors(self) -> bool
    def has_warnings(self) -> bool
```

---

## ✅ Migration Checklist (Per Stage)

Use this checklist when migrating each stage:

- [ ] Import `StageIO`
- [ ] Replace logger initialization with `io = StageIO()` and `logger = io.get_stage_logger()`
- [ ] Add `io.track_input()` for all input files
- [ ] Add `io.track_output()` for all output files
- [ ] Add `io.track_intermediate()` for cache/temp files
- [ ] Add `io.set_config()` for stage configuration
- [ ] Add `io.add_warning()` for warnings
- [ ] Add `io.add_error()` in exception handlers
- [ ] Add `io.finalize(status="success")` on success
- [ ] Add `io.finalize(status="failed")` on failure
- [ ] Test: Verify `stage.log` created
- [ ] Test: Verify `manifest.json` created
- [ ] Test: Verify logs in main pipeline log
- [ ] Test: Verify I/O tracking complete
- [ ] Update stage documentation

---

**Status:** READY FOR USE  
**Next Action:** Begin Phase 2 migration starting with ASR stage  
**Support:** See architecture doc for detailed design rationale
