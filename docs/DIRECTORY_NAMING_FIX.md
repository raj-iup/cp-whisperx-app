# Output Directory Naming Fixed

**Date:** October 29, 2025  
**Status:** ✅ **FIXED**

---

## Issue

Two output directories were being created for the same movie:
- ❌ `out/Jaane_Tu_Ya_Jaane_Na` (orchestrator - missing year)
- ✅ `out/Jaane_Tu_Ya_Jaane_Na_2008` (demux container - correct)

**Input file:** `Jaane Tu Ya Jaane Na 2008.mp4`  
**Expected:** Single directory `out/Jaane_Tu_Ya_Jaane_Na_2008`

---

## Root Cause

**Orchestrator** (`run_pipeline_arch.py`):
```python
# BEFORE (wrong)
movie_dir = output_root / parsed.sanitized_title
# Result: "Jaane_Tu_Ya_Jaane_Na" (no year)
```

**Demux Container** (`docker/demux/demux.py`):
```python
# Uses shared/utils.py::get_movie_dir()
if file_info['year']:
    dir_name = f"{sanitize_dirname(file_info['title'])}_{file_info['year']}"
else:
    dir_name = sanitize_dirname(file_info['title'])
# Result: "Jaane_Tu_Ya_Jaane_Na_2008" (with year)
```

**Problem:** Orchestrator and containers used different naming logic, creating duplicate directories.

---

## Fix Applied

**File:** `run_pipeline_arch.py` (lines 125-136)

```python
# Setup output directory
output_root = ROOT / config.get("OUTPUT_ROOT", "out")

# Create directory name with year (matching demux container behavior)
if parsed.year:
    dir_name = f"{parsed.sanitized_title}_{parsed.year}"
else:
    dir_name = parsed.sanitized_title

movie_dir = output_root / dir_name
movie_dir.mkdir(parents=True, exist_ok=True)

logger.info(f"Output directory: {movie_dir}")
```

**Result:** Orchestrator now matches container naming convention.

---

## Cleanup Performed

1. **Consolidated files** from wrong directory to correct one:
   ```bash
   cp -r out/Jaane_Tu_Ya_Jaane_Na/metadata out/Jaane_Tu_Ya_Jaane_Na_2008/
   cp -r out/Jaane_Tu_Ya_Jaane_Na/entities out/Jaane_Tu_Ya_Jaane_Na_2008/
   cp -r out/Jaane_Tu_Ya_Jaane_Na/pre_ner out/Jaane_Tu_Ya_Jaane_Na_2008/
   cp -r out/Jaane_Tu_Ya_Jaane_Na/prompts out/Jaane_Tu_Ya_Jaane_Na_2008/
   ```

2. **Removed incorrect directory:**
   ```bash
   rm -rf out/Jaane_Tu_Ya_Jaane_Na
   ```

3. **Verified consolidation:**
   - Only ONE directory exists: `out/Jaane_Tu_Ya_Jaane_Na_2008/`
   - All files in correct location

---

## Current State

```
out/
└── Jaane_Tu_Ya_Jaane_Na_2008/  ✅ ONLY ONE DIRECTORY
    ├── audio/
    │   ├── audio.wav
    │   └── audio_demux_metadata.json
    ├── entities/
    │   └── pre_ner.json
    ├── metadata/
    │   └── tmdb_data.json
    ├── pre_ner/
    │   └── initial_entities.json
    ├── prompts/
    │   └── ner_enhanced_prompt.txt
    └── vad/
        └── silero_segments.json
```

---

## Verification

✅ Only ONE output directory exists  
✅ Directory name includes year: `_2008`  
✅ All files consolidated in correct location  
✅ Orchestrator now matches demux container naming  

---

## Expected Behavior

**Examples:**

| Input File | Output Directory |
|-----------|-----------------|
| `Movie Title 2010.mp4` | `out/Movie_Title_2010/` |
| `Movie Title.mp4` | `out/Movie_Title/` |
| `Jaane Tu Ya Jaane Na 2008.mp4` | `out/Jaane_Tu_Ya_Jaane_Na_2008/` ✅ |

---

## Benefits

1. **Consistency:** All stages use the SAME directory
2. **No duplicates:** Single source of truth for output
3. **Clear identification:** Year in directory name helps identify movies
4. **Matches containers:** Orchestrator aligns with container logic

---

**Status:** 🎉 **FIXED - All stages will now use consistent directory naming!**

---

## Update: October 29, 2025

### Additional Fix Applied
Also updated `run_pipeline.py` (the direct pipeline, not container-based) to match the same naming convention:

**File:** `run_pipeline.py` (lines 105-112)
```python
# 4. Assemble prompt
output_root = ROOT / config.get("OUTPUT_ROOT", "out")
# Include year in directory name to match container pipeline behavior
if parsed.year:
    movie_name = f"{parsed.sanitized_title}_{parsed.year}"
else:
    movie_name = parsed.sanitized_title
movie_dir = output_root / movie_name
movie_dir.mkdir(parents=True, exist_ok=True)
```

### Summary
✅ **ALL pipeline implementations now use consistent naming:**
- `run_pipeline_arch.py` (orchestrator) - FIXED
- `run_pipeline.py` (direct pipeline) - FIXED
- Container services (demux, etc.) - Already correct
- Shared utilities (`shared/utils.py`) - Already correct

✅ **Single output directory:** `out/Jaane_Tu_Ya_Jaane_Na_2008/`
✅ **No more duplicates:** Previous incorrect directory removed
