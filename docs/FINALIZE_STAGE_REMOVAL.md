# Finalize Stage Removal - November 14, 2025

## Summary

The `finalize` stage has been removed from the pipeline as it was creating duplicate output directories and was redundant with the mux stage's functionality.

## Problem

The pipeline was creating two output locations for the final video:

1. **Valid path (mux stage)**: `15_mux/Jaane Tu Ya Jaane Na 2008/Jaane Tu Ya Jaane Na 2008_subtitled.mp4`
2. **Duplicate path (finalize stage)**: `Jaane_Tu_Ya_Jaane_Na/` (containing only a symlink)

The finalize stage was:
- Creating a sanitized directory name (`Jaane_Tu_Ya_Jaane_Na`)
- Creating a symlink to the mux output
- Adding a README.txt file
- Not providing any real value beyond what mux already does

## Solution

**Removed the finalize stage entirely** because:
- The mux stage already creates proper output in `15_mux/<movie_title>/`
- The mux stage creates a `final_output.mp4` symlink at the job root
- The finalize stage was just creating unnecessary duplication

## Changes Made

### 1. Pipeline Configuration (`scripts/pipeline.py`)
- ✅ Removed finalize from STAGES list
- ✅ Updated mux to be final stage (next=None)
- ✅ Removed finalize from STAGE_SCRIPTS mapping
- ✅ Removed finalize from --stages choices
- ✅ Removed special handling code for finalize stage

### 2. Scripts Removed
- ✅ `finalize-output.sh` - Deleted
- ✅ `finalize-output.ps1` - Deleted
- ✅ `scripts/finalize_output.py` - Renamed to `_deprecated_finalize_output.py`
- ✅ `scripts/finalize.py` - Renamed to `_deprecated_finalize.py`

### 3. Documentation Updated
- ✅ `docs/ARCHITECTURE.md` - Updated to show 15 stages, mux as final
- ✅ `docs/technical/PIPELINE_REFACTOR_2025-11-14.md` - Updated stage counts
- ✅ `docs/technical/REFACTOR_QUICK_REF.md` - Updated stage table
- ✅ `README.md` - Updated pipeline stages table

### 4. Comments Updated
- ✅ `scripts/mux.py` - Removed "for finalize stage" comment

## New Pipeline Structure

### Before (16 stages)
```
01-05: Audio/Video/Metadata processing
06: ASR (transcription)
07: Song Bias Injection
08: Lyrics Detection
09: Bias Correction
10: Diarization
11: Glossary Builder
12: Second Pass Translation
13: Post-NER
14: Subtitle Generation
15: Mux (video embedding)
16: Finalize (duplicate output) ❌
```

### After (15 stages)
```
01-05: Audio/Video/Metadata processing
06: ASR (transcription)
07: Song Bias Injection
08: Lyrics Detection
09: Bias Correction
10: Diarization
11: Glossary Builder
12: Second Pass Translation
13: Post-NER
14: Subtitle Generation
15: Mux (video embedding) ✅ FINAL STAGE
```

## Output Location

Final output is now **only** in:
```
out/<date>/<user>/<job-id>/15_mux/<movie_title>/<movie_title>_subtitled.mp4
```

With a convenience symlink at:
```
out/<date>/<user>/<job-id>/final_output.mp4 → 15_mux/<movie_title>/<movie_title>_subtitled.mp4
```

## Migration

### For Existing Jobs
- Old jobs with 16 stages will continue to work
- The finalize directory can be safely deleted
- The valid output is in `15_mux/<movie_title>/`

### For New Jobs
- New jobs will use 15 stages
- No finalize directory will be created
- Output is only in `15_mux/<movie_title>/`

### For Scripts/Automation
If your scripts reference:
- `finalize-output.sh` → No longer needed, output is in `15_mux/`
- Stage 16 (finalize) → No longer exists, mux is the final stage

## Benefits

1. **Cleaner output structure** - Single canonical location for final video
2. **No duplicate directories** - Eliminates confusion about which path to use
3. **Simpler pipeline** - One less stage to maintain and document
4. **Faster execution** - Eliminates unnecessary file operations
5. **More intuitive** - Mux stage naturally produces the final output

## Testing

Verified with job: `20251114-0004`
- ✅ Valid output exists: `15_mux/Jaane Tu Ya Jaane Na 2008/Jaane Tu Ya Jaane Na 2008_subtitled.mp4`
- ✅ Duplicate directory removed: `Jaane_Tu_Ya_Jaane_Na/`
- ✅ Pipeline runs successfully with 15 stages
- ✅ Documentation updated

## Related Files

### Pipeline Implementation
- `scripts/pipeline.py` - Main orchestrator
- `scripts/mux.py` - Final stage that creates output

### Documentation
- `docs/ARCHITECTURE.md` - System architecture
- `docs/technical/PIPELINE_REFACTOR_2025-11-14.md` - Refactor details
- `docs/technical/REFACTOR_QUICK_REF.md` - Quick reference
- `README.md` - Main documentation

### Deprecated (preserved for reference)
- `scripts/_deprecated_finalize_output.py`
- `scripts/_deprecated_finalize.py`

## Notes

The finalize stage was originally created to organize output into title-based directories, but this was superseded by the mux stage's improved output organization. The removal eliminates redundancy and simplifies the pipeline while maintaining all functionality.
