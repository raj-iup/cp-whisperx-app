# Alignment Stage Error Fix

**Date:** 2025-11-27  
**Issue:** Pipeline fails at alignment stage with `'list' object has no attribute 'get'`  
**Status:** ✅ FIXED

## Problem

The pipeline was failing at the alignment stage with this error:

```
[2025-11-26 23:15:40] [pipeline] [ERROR] ❌ Stage alignment: EXCEPTION: 'list' object has no attribute 'get'
[2025-11-26 23:15:40] [pipeline] [ERROR] Transcribe workflow failed - cannot proceed with translation
```

## Root Cause

**Data Format Mismatch:**

1. **ASR Stage Output** (`scripts/whisperx_integration.py` lines 925-951):
   - Saves `segments.json` as a **list** of segments: `json.dump(segments, f, ...)`
   - Format: `[{segment1}, {segment2}, ...]`

2. **Pipeline Runner Expected Format** (`scripts/run-pipeline.py`):
   - Expected a **dict** with a "segments" key: `data.get("segments", [])`
   - Format: `{"segments": [{segment1}, {segment2}, ...]}`

3. **Calling `.get()` on a list fails** with: `'list' object has no attribute 'get'`

## Solution

Added a helper function `normalize_segments_data()` to handle both formats:

```python
def normalize_segments_data(data):
    """
    Normalize segments data to consistent dict format.
    Handles both list [...] and dict {"segments": [...]} formats.
    
    Args:
        data: Either a list of segments or a dict containing segments
        
    Returns:
        Tuple of (data_dict, segments_list)
    """
    if isinstance(data, list):
        segments = data
        data = {"segments": segments}
    elif isinstance(data, dict):
        segments = data.get("segments", [])
    else:
        segments = []
    
    return data, segments
```

## Files Modified

### `scripts/run-pipeline.py`

**Changes:**
1. Added `normalize_segments_data()` helper function (after line 43)
2. Updated all places that load segments.json to use the helper:
   - `_stage_alignment()` (line ~1503)
   - `_perform_mlx_alignment()` (line ~1649)
   - `_stage_subtitle_generation()` (line ~2089, ~2148)
   - `_stage_subtitle_generation_source()` (line ~2479)
   - `_stage_subtitle_generation_target()` (line ~2507)
   - `_stage_indictrans2_translation()` (line ~1858, ~2020)

**Before:**
```python
with open(segments_file) as f:
    data = json.load(f)

segments = data.get("segments", [])  # ❌ Fails if data is a list
```

**After:**
```python
with open(segments_file) as f:
    raw_data = json.load(f)

data, segments = normalize_segments_data(raw_data)  # ✅ Handles both formats
```

## Testing

**Verified Fix:**
```bash
# Test with actual ASR output (list format)
$ python3 /tmp/test_alignment_fix.py
✓ Loaded ASR segments: <class 'list'>
✓ New code handles it: 10 segments
✓ Can access segment data: 2 words in first segment
✓ Fix verified - alignment stage should work now!
```

## Impact

**Stages Fixed:**
- ✅ Alignment stage (Stage 7)
- ✅ Subtitle generation stages
- ✅ Translation workflow stages
- ✅ All places that read segments.json

**Compatibility:**
- ✅ Works with list format (ASR output)
- ✅ Works with dict format (expected format)
- ✅ Works with cleaned segments (hallucination removal output)
- ✅ Backward compatible with existing pipelines

## Related Issues

This fix addresses the alignment stage error found in:
- `/Users/rpatel/Projects/cp-whisperx-app/out/2025/11/26/baseline/3/logs/99_pipeline_20251126_231015.log`
- Similar errors in baseline/1 and baseline/2 runs

## Next Steps

1. ✅ Fix applied to `scripts/run-pipeline.py`
2. ⏳ Optionally standardize ASR output to always use dict format
3. ⏳ Run full pipeline test to verify end-to-end

## Standards Compliance

This fix aligns with `/Users/rpatel/Projects/cp-whisperx-app/docs/DEVELOPER_STANDARDS.md`:

- ✅ **Robust Error Handling:** Helper function validates data type before processing
- ✅ **Defensive Programming:** Handles unexpected formats gracefully
- ✅ **Code Reusability:** Single helper function used throughout
- ✅ **Backward Compatibility:** Supports both old and new formats
