# Phase 3: Stage Pattern Adoption - Quick Start Guide

**For Developers:** How to convert a stage to the StageIO pattern in 15 minutes

---

## The Pattern (Copy & Paste Template)

```python
#!/usr/bin/env python3
"""
Stage Name: Brief description
"""
# Standard library
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local
from shared.stage_utils import StageIO
from shared.config import load_config
from shared.logger import get_logger

logger = get_logger(__name__)


def run_stage(job_dir: Path, stage_name: str = "XX_stage_name") -> int:
    """
    Stage description.
    
    Args:
        job_dir: Job directory containing inputs
        stage_name: Stage name for logging (default: "XX_stage_name")
        
    Returns:
        0 on success, 1 on failure
    """
    # 1. Initialize StageIO with manifest
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        logger.info("=" * 60)
        logger.info("STAGE NAME: Description")
        logger.info("=" * 60)
        
        # 2. Load configuration
        config = load_config()
        
        # 3. Find and track inputs
        input_file = io.job_dir / "previous_stage" / "input.ext"
        if not input_file.exists():
            raise FileNotFoundError(f"Input not found: {input_file}")
        io.track_input(input_file, "file_type", format="ext")
        
        # 4. Add config to manifest
        io.add_config("param_name", config.get("PARAM_NAME", "default"))
        
        # 5. Define outputs in stage_dir ONLY
        output_file = io.stage_dir / "output.ext"
        
        # 6. Process (your actual stage logic here)
        logger.info("Processing...")
        process_data(input_file, output_file)  # Your function
        
        # 7. Track outputs
        io.track_output(output_file, "file_type", format="ext")
        
        # 8. Success!
        logger.info("=" * 60)
        logger.info("STAGE COMPLETE")
        logger.info("=" * 60)
        
        io.finalize(status="success")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}", exc_info=True)
        io.add_error(str(e), e)
        io.finalize(status="failed")
        return 1
    except RuntimeError as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        io.add_error(str(e), e)
        io.finalize(status="failed")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        io.add_error(str(e), e)
        io.finalize(status="failed")
        return 1


def main() -> int:
    """
    Legacy wrapper for backward compatibility.
    Calls run_stage() with default output directory from environment.
    """
    import os
    output_dir = Path(os.environ.get('OUTPUT_DIR', 'out'))
    return run_stage(output_dir, "XX_stage_name")


if __name__ == "__main__":
    sys.exit(main())
```

---

## Checklist for Converting an Existing Stage

### Pre-Conversion
- [ ] Read existing code, understand inputs/outputs
- [ ] Note all configuration parameters used
- [ ] Identify all file I/O operations
- [ ] Check for subprocess calls
- [ ] Note any environment variable usage

### Conversion Steps

#### 1. Add run_stage() Function (5 min)
```python
def run_stage(job_dir: Path, stage_name: str = "XX_stage_name") -> int:
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    try:
        # ... your code here ...
        io.finalize(status="success")
        return 0
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        io.add_error(str(e), e)
        io.finalize(status="failed")
        return 1
```

#### 2. Initialize StageIO (1 min)
- ✅ Use: `io = StageIO(stage_name, job_dir, enable_manifest=True)`
- ✅ Get logger: `logger = io.get_stage_logger()`
- ❌ Don't use: `print()` anywhere

#### 3. Track Inputs (2 min)
```python
input_file = io.job_dir / "prev_stage" / "input.ext"
io.track_input(input_file, "file_type", format="ext")
```

For multiple inputs:
```python
for f in input_dir.glob("*.wav"):
    io.track_input(f, "audio", format="wav")
```

#### 4. Track Config (1 min)
```python
config = load_config()
io.add_config("param1", config.get("PARAM1", "default"))
io.add_config("param2", config.get("PARAM2", 42))
```

#### 5. Fix Output Paths (3 min)
- ✅ Change: `output_dir / "file.ext"` → `io.stage_dir / "file.ext"`
- ✅ All outputs must go to `io.stage_dir`
- ❌ Never write to `job_dir` root or `/tmp`

#### 6. Track Outputs (2 min)
```python
output_file = io.stage_dir / "output.ext"
# ... create output ...
io.track_output(output_file, "file_type", format="ext", size_mb=1.5)
```

#### 7. Finalize Manifest (1 min)
```python
# On success
io.finalize(status="success")
return 0

# On failure
except Exception as e:
    logger.error(f"Failed: {e}", exc_info=True)
    io.add_error(str(e), e)
    io.finalize(status="failed")
    return 1
```

### Post-Conversion

#### 8. Add Backward Compatible main() (2 min)
```python
def main() -> int:
    import os
    output_dir = Path(os.environ.get('OUTPUT_DIR', 'out'))
    return run_stage(output_dir, "XX_stage_name")
```

#### 9. Test (5 min)
```bash
# Syntax check
python3 -m py_compile scripts/your_stage.py

# Compliance check
./scripts/validate-compliance.py scripts/your_stage.py

# Optional: Quick test run
python3 scripts/your_stage.py
```

#### 10. Update Documentation
- [ ] Update PHASE3_IMPLEMENTATION_PROGRESS.md status
- [ ] Mark task as complete in roadmap
- [ ] Note any issues or deviations

---

## Common Patterns

### Multiple Input Files
```python
trans_dir = io.job_dir / "08_translation"
for trans_file in trans_dir.glob("transcript_*.txt"):
    io.track_input(trans_file, "transcript", lang=trans_file.stem.split("_")[-1])
```

### Multiple Output Files  
```python
for lang in target_languages:
    output_file = io.stage_dir / f"output_{lang}.srt"
    generate_subtitle(transcript, output_file, lang)
    io.track_output(output_file, "subtitle", lang=lang, format="srt")
```

### Conditional Outputs
```python
if config.get("GENERATE_VTT", "false").lower() == "true":
    vtt_file = io.stage_dir / "output.vtt"
    convert_to_vtt(srt_file, vtt_file)
    io.track_output(vtt_file, "subtitle", format="vtt")
```

### Subprocess Calls
```python
cmd = ["ffmpeg", "-i", str(input_file), str(output_file)]
logger.debug(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode != 0:
    logger.error(f"Command failed: {result.stderr}")
    raise RuntimeError(f"ffmpeg failed: {result.stderr}")
```

### Performance Logging
```python
import time
start = time.time()
expensive_operation()
duration = time.time() - start
logger.info(f"Completed in {duration:.2f}s")
io.add_config("processing_time_sec", round(duration, 2))
```

---

## API Quick Reference

### StageIO Methods
```python
# Initialization
io = StageIO(stage_name, job_dir, enable_manifest=True)

# Logging
logger = io.get_stage_logger()  # Returns configured logger

# Input tracking
io.track_input(path, "type", **metadata)

# Output tracking
io.track_output(path, "type", **metadata)

# Intermediate files (cache, temp)
io.track_intermediate(path, retained=False, reason="temp file")

# Configuration
io.add_config(key, value)
io.set_config({"key1": val1, "key2": val2})

# Warnings and errors
io.add_warning("Something unexpected")
io.add_error("Something failed", exception)

# Resources
io.set_resources(gpu_memory_mb=4096, cpu_percent=85)

# Finalization
io.finalize(status="success", **kwargs)
io.finalize(status="failed", error="reason")
io.finalize(status="skipped", reason="not needed")
```

### Path Helpers
```python
# Get path from previous stage
input_path = io.get_input_path("audio.wav", from_stage="01_demux")

# Get output path in current stage
output_path = io.stage_dir / "output.ext"
# OR
output_path = io.get_output_path("output.ext")

# Properties
io.stage_dir      # Current stage directory
io.job_dir        # Job root directory  
io.output_base    # Same as job_dir
io.stage_log      # Path to stage.log
io.manifest_path  # Path to manifest.json
```

---

## Troubleshooting

### "FileNotFoundError: Input not found"
- Check if previous stage actually creates that file
- Verify stage naming matches directory structure
- Use `io.get_input_path()` helper instead of hardcoding

### "Compliance check fails"
- Run: `./scripts/validate-compliance.py your_file.py`
- Common issues:
  - Missing `io.track_input()` or `io.track_output()`
  - Missing `io.finalize()`
  - Using `print()` instead of `logger`

### "Manifest not created"
- Ensure `enable_manifest=True` in StageIO initialization
- Call `io.finalize()` in both success and error paths

### "Old files being used"
- Make sure outputs go to `io.stage_dir`, not `job_dir`
- Check no hardcoded paths like `/tmp` or `out/`

---

## Examples

### Demux Stage (Completed)
See: `scripts/demux.py` - Full working example

### TMDB Enrichment (Reference)
See: `scripts/tmdb_enrichment_stage.py` - Complete pattern

### Your Stage Here!
Copy the template above and follow the 10-step checklist

---

## Time Estimates

| Complexity | Estimated Time | Examples |
|------------|----------------|----------|
| Simple     | 15-30 min      | demux, mux |
| Medium     | 30-60 min      | subtitle_gen |
| Complex    | 1-2 hours      | ASR, translation |

**Actual vs Estimated:**
- Demux: 8h estimated → 1h actual (8x faster)

---

## Questions?

1. Check: [PHASE3_IMPLEMENTATION_PROGRESS.md](PHASE3_IMPLEMENTATION_PROGRESS.md)
2. Read: [DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md) § 3.1
3. See: [CODE_EXAMPLES.md](CODE_EXAMPLES.md) for more patterns
4. Review: [.github/copilot-instructions.md](../.github/copilot-instructions.md)

---

**Last Updated:** 2025-12-03  
**Status:** Active  
**Progress:** 1/6 tasks complete (demux ✅)
