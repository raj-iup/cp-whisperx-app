# Pipeline Stage Refactoring - Quick Reference

## Commands

```bash
# Check refactoring status
python3 refactor_stages.py status

# Generate template for a stage
python3 refactor_stages.py template <stage_name>

# Example: Generate pre_ner template
python3 refactor_stages.py template pre_ner > scripts/pre_ner_new.py
```

## Basic Stage Template

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config

def main():
    # 1. Initialize
    stage_io = StageIO("stage_name")
    logger = get_stage_logger("stage_name", log_level="DEBUG")
    
    logger.info("=" * 60)
    logger.info("STAGE_NAME: Description")
    logger.info("=" * 60)
    
    # 2. Load config
    config = load_config(os.environ.get('CONFIG_PATH', 'config/.env.pipeline'))
    
    # 3. Load inputs
    input_data = stage_io.load_json("input.json")
    logger.info(f"Loaded {len(input_data)} items")
    
    # 4. Process
    logger.info("Processing...")
    result = process(input_data, config, logger)
    
    # 5. Save outputs
    stage_io.save_json(result, "output.json")
    stage_io.save_metadata({'status': 'completed'})
    
    logger.info("=" * 60)
    logger.info("STAGE COMPLETED")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## StageIO Quick Reference

```python
from shared.stage_utils import StageIO, get_stage_logger

# Initialize
stage_io = StageIO("stage_name")
logger = get_stage_logger("stage_name", log_level="DEBUG")

# Load input (from previous stage)
data = stage_io.load_json("file.json")
path = stage_io.get_input_path("file.ext")
path = stage_io.get_input_path("file.ext", from_stage="specific_stage")

# Save output
stage_io.save_json(data, "output.json")
path = stage_io.get_output_path("file.ext")

# Metadata
stage_io.save_metadata({'status': 'completed', 'metric': 123})
prev_meta = stage_io.load_metadata()

# Backward compatibility
stage_io.copy_to_base("important.json")
```

## Logging

```python
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.error("Error with traceback", exc_info=True)
```

## Stage Numbers

| Stage | Number | Directory |
|-------|--------|-----------|
| demux | 01 | 01_demux/ |
| tmdb | 02 | 02_tmdb/ |
| pre_ner | 03 | 03_pre_ner/ |
| silero_vad | 04 | 04_silero_vad/ |
| pyannote_vad | 05 | 05_pyannote_vad/ |
| diarization | 06 | 06_diarization/ |
| asr | 07 | 07_asr/ |
| glossary_builder | 08 | 08_glossary_builder/ |
| second_pass_translation | 09 | 09_second_pass_translation/ |
| lyrics_detection | 10 | 10_lyrics_detection/ |
| post_ner | 11 | 11_post_ner/ |
| subtitle_gen | 12 | 12_subtitle_gen/ |
| mux | 13 | 13_mux/ |
| finalize | 14 | 14_finalize/ |

## Log Files

Sequential numbered logs in `logs/` directory:
- `00_orchestrator_YYYYMMDD_HHMMSS.log`
- `01_demux_YYYYMMDD_HHMMSS.log`
- `02_tmdb_YYYYMMDD_HHMMSS.log`
- etc.

## Refactoring Checklist

- [ ] Import `StageIO` and `get_stage_logger`
- [ ] Initialize `StageIO` with stage name
- [ ] Create logger with DEBUG level
- [ ] Add header/footer log messages
- [ ] Use `get_input_path()` for inputs
- [ ] Use `get_output_path()` for outputs
- [ ] Save metadata with `save_metadata()`
- [ ] Add debug logging throughout
- [ ] Copy critical files to base (if needed)
- [ ] Return 0 on success, 1 on failure
- [ ] Handle exceptions with logging

## Common Patterns

### Load JSON from previous stage
```python
data = stage_io.load_json("input.json")
```

### Load from specific stage
```python
data = stage_io.load_json("data.json", from_stage="tmdb")
```

### Save JSON output
```python
stage_io.save_json(result, "output.json")
```

### Save non-JSON file
```python
output_path = stage_io.get_output_path("output.txt")
output_path.write_text(content)
```

### Save metadata
```python
metadata = {
    'status': 'completed',
    'input_count': len(inputs),
    'output_count': len(outputs),
    'processing_time': elapsed
}
stage_io.save_metadata(metadata)
```

## Documentation

- **Full Guide**: `STAGE_REFACTORING_GUIDE.md`
- **Implementation**: `STAGE_REFACTORING_IMPLEMENTATION.md`
- **Summary**: `STAGE_REFACTORING_SUMMARY.md`
- **This Reference**: `QUICK_REFERENCE.md`
