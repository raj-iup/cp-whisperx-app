# Stage Renumbering - Additional Fixes

**Date**: November 25, 2025  
**Status**: ✅ COMPLETE  
**Issue**: Hybrid translation failing due to old stage number references

## Problem

After renumbering stages, the `shared/stage_utils.py` STAGE_NUMBERS mapping still had old numbers, causing StageIO to look for files in wrong directories.

## Root Cause

When stages were renumbered:
- ✅ `run-pipeline.py` - Updated
- ✅ `prepare-job.py` - Updated  
- ❌ `shared/stage_utils.py` - **NOT updated**

This caused StageIO to construct wrong paths:
```python
# OLD mapping (WRONG):
"asr": 4  → looks for 04_asr/segments.json ❌

# NEW mapping (CORRECT):
"asr": 5  → looks for 05_asr/segments.json ✅
```

## Error Message

```
[ERROR] Failed to load segments from ASR: Input file not found: 
/path/to/out/2025/11/25/1/9/04_asr/segments.json
```

## Fix Applied

### File: `shared/stage_utils.py`

**Updated STAGE_NUMBERS mapping**:

```python
# Stage number mapping
STAGE_NUMBERS = {
    "demux": 1,
    "source_separation": 2,
    "tmdb": 3,                      # ✨ ADDED
    "pyannote_vad": 4,              # 3 → 4
    "asr": 5,                       # 4 → 5
    "alignment": 6,                 # 5 → 6
    "lyrics_detection": 7,          # 6 → 7
    "translation": 8,               # 7 → 8
    "hybrid_translation": 8,        # 7 → 8
    "indictrans2_translation": 8,   # 7 → 8
    "nllb_translation": 8,          # 7 → 8
    "subtitle_generation": 9,       # 8 → 9
    "subtitle_generation_source": 9,# 8 → 9
    "subtitle_generation_target": 9,# 8 → 9
    "mux": 10,                      # 9 → 10
    "hallucination_removal": 5,     # 4 → 5
    "export_transcript": 5,         # 4 → 5
    "load_transcript": 8,           # 7 → 8
    "hinglish_detection": 9,        # 8 → 9
}
```

## Impact on Existing Jobs

### Jobs Created Before Fix

Jobs created with old `prepare-job.py` will have **mixed directories**:

```
out/2025/11/25/1/9/
├── 01_demux/
├── 02_source_separation/
├── 03_pyannote_vad/         ⬅️ OLD (empty)
├── 03_tmdb/                 ⬅️ NEW
├── 04_pyannote_vad/         ⬅️ NEW (has data)
├── 05_asr/                  ⬅️ NEW (has data)
...
```

**Solution**: These old jobs will fail. Create new jobs with updated `prepare-job.py`.

### Jobs Created After Fix

New jobs will have **clean sequential structure**:

```
out/2025/11/25/1/10/
├── 01_demux/
├── 02_source_separation/
├── 03_tmdb/
├── 04_pyannote_vad/
├── 05_asr/
├── 06_alignment/
├── 07_lyrics_detection/
├── 08_translation/
├── 09_subtitle_generation/
└── 10_mux/
```

## Files Modified

1. **`shared/stage_utils.py`** - STAGE_NUMBERS mapping updated
2. **`scripts/run-pipeline.py`** - Already updated (previous fix)
3. **`scripts/prepare-job.py`** - Already updated (previous fix)
4. **6 other scripts** - Already updated (previous fix)

## Verification

### Test StageIO Path Resolution

```python
from shared.stage_utils import StageIO

# Test ASR stage
stage_io = StageIO("hybrid_translation")
asr_path = stage_io.get_input_path("segments.json", from_stage="asr")
print(f"ASR path: {asr_path}")
# Expected: .../05_asr/segments.json ✓

# Test alignment
alignment_path = stage_io.get_input_path("segments.json", from_stage="alignment")
print(f"Alignment path: {alignment_path}")
# Expected: .../06_alignment/segments_aligned.json ✓
```

### Check Stage Number Mapping

```python
from shared.stage_utils import StageIO

stages = [
    ("asr", 5),
    ("alignment", 6),
    ("lyrics_detection", 7),
    ("translation", 8),
    ("subtitle_generation", 9),
    ("mux", 10),
]

for stage_name, expected_num in stages:
    actual_num = StageIO.STAGE_NUMBERS[stage_name]
    status = "✓" if actual_num == expected_num else "❌"
    print(f"{stage_name:20} Expected:{expected_num} Actual:{actual_num} {status}")
```

## Testing

### Create New Job

```bash
# Clean test - new job with updated prepare-job.py
./prepare-job.sh -i test.mp4 -w subtitle --source-lang hi

# Check directories
ls out/YYYY/MM/DD/user/N/

# Expected: Clean sequential 01-10 directories
```

### Run Hybrid Translation

```bash
# Should now find segments at correct path
grep "Failed to load segments" out/*/logs/99_hybrid_translation_*.log

# Expected: No results (no errors)
```

## Summary

✅ **Fixed**: StageIO STAGE_NUMBERS mapping  
✅ **Impact**: All StageIO-based scripts now use correct paths  
✅ **Tested**: Syntax validated  
📝 **Note**: Create new jobs for clean directory structure  

---

**Status**: ✅ COMPLETE  
**Last Updated**: November 25, 2025
