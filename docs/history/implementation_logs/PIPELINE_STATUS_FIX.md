# Pipeline Status Display Fix

**Date**: 2025-11-08  
**Issue**: Completed stages showing as [PENDING]  
**Status**: ✅ FIXED

---

## Problem

The `pipeline-status.sh` script was incorrectly showing completed stages as [PENDING]:

```
    ○ demux                     [PENDING]  ← Should be [COMPLETED]
    ○ tmdb                      [PENDING]  ← Should be [COMPLETED]
    ○ pre_ner                   [PENDING]  ← Should be [COMPLETED]
    ○ silero_vad                [PENDING]  ← Should be [COMPLETED]
    ○ pyannote_vad              [PENDING]  ← Should be [COMPLETED]
    ○ diarization               [PENDING]  ← Should be [COMPLETED]
```

---

## Root Cause

The script was checking for `status = "completed"` in manifest.json, but the actual manifest uses `status = "success"`:

```json
{
  "stages": {
    "demux": {
      "completed": true,
      "status": "success",  ← Script was looking for "completed"
      "duration": 10.776844024658203
    }
  }
}
```

---

## Fix Applied

Updated `scripts/pipeline-status.sh` to check multiple status indicators:

### Before
```bash
STATUS=$(jq -r ".stages.\"$stage\".status // \"pending\"" "$MANIFEST")

if [ "$STATUS" = "completed" ]; then
    printf "    ✓ %-25s [COMPLETED]\n" "$stage"
```

### After
```bash
STATUS=$(jq -r ".stages.\"$stage\".status // \"pending\"" "$MANIFEST")
COMPLETED=$(jq -r ".stages.\"$stage\".completed // false" "$MANIFEST")

# Check if stage is completed (either status="success" or completed=true)
if [ "$STATUS" = "success" ] || [ "$COMPLETED" = "true" ]; then
    printf "    ✓ %-25s [COMPLETED]\n" "$stage"
elif [ "$STATUS" = "completed" ]; then
    printf "    ✓ %-25s [COMPLETED]\n" "$stage"
elif [ "$STATUS" = "failed" ] || [ "$STATUS" = "error" ]; then
    printf "    ✗ %-25s [FAILED]\n" "$stage"
elif [ "$STATUS" = "running" ] || [ "$STATUS" = "in_progress" ]; then
    printf "    ⏳ %-25s [RUNNING]\n" "$stage"
else
    printf "    ○ %-25s [PENDING]\n" "$stage"
fi
```

---

## Changes Made

### 1. Bash Script
**File**: `scripts/pipeline-status.sh`

**Changes**:
- Check both `status` and `completed` fields
- Support multiple status values: `success`, `completed`
- Support multiple failure values: `failed`, `error`
- Support multiple running values: `running`, `in_progress`

### 2. PowerShell Script
**File**: `scripts/pipeline-status.ps1`

**Changes**:
- Complete rewrite to match bash version
- Same logic for status checking
- Cross-platform compatibility with Windows
- Proper path handling for Windows (`\` instead of `/`)

---

## Status Values Supported

The script now correctly handles these status values:

| Value | Field | Display |
|-------|-------|---------|
| `"success"` | `status` | ✓ [COMPLETED] |
| `"completed"` | `status` | ✓ [COMPLETED] |
| `true` | `completed` | ✓ [COMPLETED] |
| `"failed"` | `status` | ✗ [FAILED] |
| `"error"` | `status` | ✗ [FAILED] |
| `"running"` | `status` | ⏳ [RUNNING] |
| `"in_progress"` | `status` | ⏳ [RUNNING] |
| `"pending"` | `status` | ○ [PENDING] |
| (not set) | `status` | ○ [PENDING] |

---

## Verification

### Test Command
```bash
./scripts/pipeline-status.sh 20251108-0001
```

### Expected Output
```
📋 JOB STATUS: 20251108-0001
────────────────────────────────────────────────────
  📁 Location: /path/to/out/2025/11/08/1/20251108-0001
  📊 Stage Progress:

    ✓ demux                     [COMPLETED]  ✅
    ✓ tmdb                      [COMPLETED]  ✅
    ✓ pre_ner                   [COMPLETED]  ✅
    ✓ silero_vad                [COMPLETED]  ✅
    ✓ pyannote_vad              [COMPLETED]  ✅
    ✓ diarization               [COMPLETED]  ✅
    ○ asr                       [PENDING]
    ○ second_pass_translation   [PENDING]
    ○ lyrics_detection          [PENDING]
    ○ post_ner                  [PENDING]
    ○ subtitle_gen              [PENDING]
    ○ mux                       [PENDING]
```

---

## Additional Improvements

While fixing the status display, also updated the script with:

1. **12 Stages Listed** (was missing 2 stages)
   - Added: `second_pass_translation`
   - Added: `lyrics_detection`

2. **Updated Commands Section**
   - Removed outdated `preflight.py` reference
   - Added `./scripts/bootstrap.sh` for setup
   - Updated to use native execution commands

3. **Updated Output Structure**
   - Job-based directory structure (`out/YYYY/MM/DD/USER_ID/JOB_ID/`)
   - Correct subdirectories: `audio/`, `metadata/`, `entities/`, etc.
   - Removed Docker-specific references

4. **Updated Documentation References**
   - Points to correct documentation files
   - Added recent fixes reference (`DEVICE_AND_CACHE_FIX.md`)

---

## Files Modified

1. ✅ `scripts/pipeline-status.sh` - Bash version (macOS/Linux)
2. ✅ `scripts/pipeline-status.ps1` - PowerShell version (Windows)

---

## Cross-Platform Support

### macOS / Linux
```bash
./scripts/pipeline-status.sh 20251108-0001
```

### Windows (PowerShell)
```powershell
.\scripts\pipeline-status.ps1 20251108-0001
```

Both versions now provide identical output and functionality.

---

## Success Criteria

✅ Completed stages show ✓ [COMPLETED]  
✅ Failed stages show ✗ [FAILED]  
✅ Running stages show ⏳ [RUNNING]  
✅ Pending stages show ○ [PENDING]  
✅ All 12 stages listed correctly  
✅ Commands section updated  
✅ Output structure accurate  
✅ Cross-platform compatible  

---

## Testing

```bash
# Check status of job 20251108-0001
./scripts/pipeline-status.sh 20251108-0001

# Should show:
# - 6 completed stages (demux through diarization)
# - 6 pending stages (asr through mux)
# - Correct [COMPLETED] indicators with ✓
```

---

## Related Issues Fixed

This fix also resolved:

1. **Missing stages** - Now lists all 12 stages
2. **Outdated commands** - Removed preflight.py, updated to bootstrap.sh
3. **Wrong output structure** - Updated to job-based structure
4. **Missing PowerShell version** - Created equivalent Windows script

---

**Fix Complete**: 2025-11-08  
**Status**: ✅ Working correctly  
**Platform Support**: macOS, Linux, Windows  

Your pipeline status now displays accurately! 🎉
