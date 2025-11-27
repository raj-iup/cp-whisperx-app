# Stage Order Refactoring - Centralized System

## Overview

The pipeline stage ordering has been refactored to use a **single source of truth** in `shared/stage_order.py`. This makes it much easier to add, remove, or reorder stages in the future.

## Problem Solved

Previously, stage numbers were hardcoded in multiple files:
- `scripts/prepare-job.py` - Created stage directories
- `scripts/run-pipeline.py` - Referenced stage paths (100+ locations)
- `shared/stage_utils.py` - Stage number mappings
- `scripts/hybrid_translator.py` - Used StageIO

When adding the glossary system at stage 3, we had to:
1. Update stage numbers in all files manually
2. Deal with inconsistencies (02b_glossary_load, duplicate directories)
3. Fix 100+ hardcoded paths
4. Debug mismatches between systems

## New Architecture

### Single Source of Truth: `shared/stage_order.py`

```python
STAGE_ORDER = [
    "demux",              # Stage 1
    "tmdb",               # Stage 2
    "glossary_load",      # Stage 3
    "source_separation",  # Stage 4
    ...
]
```

All stage numbers are **automatically generated** from this list.

### Key Functions

```python
from shared.stage_order import get_stage_number, get_stage_dir, get_all_stage_dirs

# Get stage number
num = get_stage_number("translation")  # Returns: 10

# Get stage directory name
dir = get_stage_dir("translation")  # Returns: "10_translation"

# Get stage path in job directory
path = get_stage_dir("translation", job_dir="/path/to/job")
# Returns: "/path/to/job/10_translation"

# Get all directories to create
dirs = get_all_stage_dirs()
# Returns: ["01_demux", "02_tmdb", "03_glossary_load", ...]
```

## Current Stage Order

```
 1. 01_demux               - Audio extraction
 2. 02_tmdb                - TMDB enrichment
 3. 03_glossary_load       - Glossary system ✨ NEW
 4. 04_source_separation   - Vocal extraction
 5. 05_pyannote_vad        - Voice detection
 6. 06_asr                 - Speech-to-text
 7. 07_alignment           - Word alignment
 8. 08_lyrics_detection    - Song detection
 9. 09_export_transcript   - Export plain text
10. 10_translation         - Translation
11. 11_subtitle_generation - SRT creation
12. 12_mux                 - Final muxing
```

### Sub-stages

Some stages are sub-operations that share their parent's number:
- `hallucination_removal` → Part of `asr` (stage 6)
- `load_transcript` → Part of `translation` (stage 10)
- `hinglish_detection` → Part of `subtitle_generation` (stage 11)

### Stage Aliases

Some stages have multiple names but share the same directory:
- `translation`, `hybrid_translation`, `indictrans2_translation`, `nllb_translation` → All use `10_translation`
- `subtitle_generation`, `subtitle_generation_source`, `subtitle_generation_target` → All use `11_subtitle_generation`

## Updated Files

### 1. `shared/stage_order.py` (NEW)
- Defines `STAGE_ORDER` list
- Auto-generates `STAGE_NUMBERS` dictionary
- Auto-generates `STAGE_DIRECTORIES` list
- Provides utility functions
- Validates consistency

### 2. `scripts/prepare-job.py`
**Before:**
```python
stage_dirs = [
    "01_demux",
    "02_tmdb",
    "03_source_separation",  # Wrong!
    ...
]
```

**After:**
```python
from shared.stage_order import get_all_stage_dirs

for stage_dir in get_all_stage_dirs():
    (job_dir / stage_dir).mkdir(exist_ok=True)
```

### 3. `shared/stage_utils.py`
**Before:**
```python
STAGE_NUMBERS = {
    "demux": 1,
    "tmdb": 2,
    ...  # Hardcoded mapping
}
```

**After:**
```python
from shared.stage_order import get_stage_number, get_stage_dir, STAGE_NUMBERS

# Uses centralized mappings
```

### 4. `scripts/run-pipeline.py`
**Before:**
```python
output_dir = self.job_dir / "08_translation"  # Hardcoded!
```

**After:**
```python
output_dir = self._stage_path("translation")  # Centralized!
```

Added helper method:
```python
def _stage_path(self, stage_name: str) -> Path:
    """Get stage directory path using centralized ordering."""
    return self.job_dir / get_stage_dir(stage_name)
```

### 5. `scripts/hybrid_translator.py`
**Fixed to use `OUTPUT_FILE` environment variable** instead of creating its own directory.

## How to Add a New Stage

### Example: Adding "quality_check" after translation

1. **Edit `shared/stage_order.py` ONLY:**

```python
STAGE_ORDER: List[str] = [
    ...
    "export_transcript",
    "translation",
    "quality_check",  # ← ADD HERE
    "subtitle_generation",
    ...
]
```

2. **That's it!** Everything else updates automatically:
   - Stage numbers renumber automatically
   - `prepare-job.py` creates the new directory
   - `stage_utils.py` knows about it
   - Pipeline can reference it with `self._stage_path("quality_check")`

3. **Implement the stage:**
```python
def _stage_quality_check(self) -> bool:
    """Stage 11: Quality check of translations"""
    output_dir = self._stage_path("quality_check")
    # ... implementation
```

## Migration Notes

### Stage Number Changes

When glossary_load was added at stage 3:

| Stage | Old Number | New Number |
|-------|------------|------------|
| demux | 1 | 1 (same) |
| tmdb | 2 | 2 (same) |
| **glossary_load** | - | **3 (NEW)** |
| source_separation | 2/3 | 4 |
| pyannote_vad | 4 | 5 |
| asr | 5 | 6 |
| alignment | 6 | 7 |
| lyrics_detection | 7 | 8 |
| export_transcript | - | 9 (NEW) |
| translation | 8 | 10 |
| subtitle_generation | 9 | 11 |
| mux | 10 | 12 |

### Breaking Changes

None! The system is backward compatible:
- Old job directories still work
- StageIO gracefully handles unknown stages (falls back to stage 99)
- Validation warns but doesn't crash

## Testing

```bash
# Test the stage order module
python3 shared/stage_order.py

# Should output:
# ======================================================================
# PIPELINE STAGE ORDER
# ======================================================================
#  1. 01_demux
#  2. 02_tmdb
#  3. 03_glossary_load
#  ...
```

## Benefits

✅ **Single Source of Truth** - One place to define stage order  
✅ **Easy to Modify** - Add/remove/reorder stages in one line  
✅ **Automatic Propagation** - All files update automatically  
✅ **No Hardcoding** - No more searching for "08_translation" in 100 files  
✅ **Validated** - Catches inconsistencies at import time  
✅ **Self-Documenting** - `python3 shared/stage_order.py` shows current order  
✅ **Type-Safe** - Functions have type hints  
✅ **Error-Resistant** - Graceful fallbacks for unknown stages  

## Future Enhancements

Possible improvements:
1. Add stage dependencies (e.g., "translation requires asr")
2. Add stage descriptions/documentation
3. Generate stage execution graph
4. Validate job manifests against stage order
5. Auto-generate stage templates

## Questions?

See `shared/stage_order.py` for implementation details.
