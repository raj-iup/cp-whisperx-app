# Directory Structure Change - Job Counter Implementation (v2)

**Date**: 2025-11-18  
**Change Type**: Directory Structure & Job ID System (Updated)

---

## Overview

The output directory structure has been updated to use date-hierarchical organization with sequential job numbering and improved job ID format.

---

## Changes

### Previous Structure (v1)
```
out/
└── YYYY/MM/DD/username/job_NNNN/    # job_0001, job_0002, etc.
```

### New Structure (v2)
```
out/
└── YYYY/                             # Year (2025)
    └── MM/                           # Month (11)
        └── DD/                       # Day (18)
            └── USERID/               # User ID from job config
                └── counter/          # Sequential counter: 1, 2, 3...
```

**Job ID Format**: `job-YYYYMMDD-USERID-nnnn`  
**Example**: `job-20251118-rpatel-0001`

---

## Key Changes from v1

1. **Simpler Directory Names**: Counter numbers instead of full job IDs
   - Old: `out/2025/11/18/rpatel/job_0001/`
   - New: `out/2025/11/18/rpatel/1/`

2. **Enhanced Job ID Format**: Includes date and user
   - Old: `job_0001`
   - New: `job-20251118-rpatel-0001`

3. **Daily Counter Reset**: Counter resets daily per user
   - Counter file: `out/.job_counter_YYYYMMDD_USERID`

4. **User ID from Config**: Uses USER_ID from job environment file
   - Allows customization beyond system username

---

## Benefits

- ✅ **Cleaner directories**: Simple numeric counter (1, 2, 3...)
- ✅ **Informative job IDs**: Date and user embedded in ID
- ✅ **Daily organization**: Each day starts fresh counter
- ✅ **Multi-user support**: USER_ID in job config
- ✅ **Easy navigation**: Browse by date, then user, then counter

---

## Job Counter System

### Implementation

Counter file per user per day:
```
out/.job_counter_YYYYMMDD_USERID
```

Example: `out/.job_counter_20251118_rpatel`

### Counter Behavior

- Starts at 0 for each user each day
- First job of day: counter = 1, job_id = `job-20251118-rpatel-0001`
- Second job: counter = 2, job_id = `job-20251118-rpatel-0002`
- Next day: resets to 1, job_id = `job-20251119-rpatel-0001`

---

## Directory Examples

### Single Day Structure
```
out/2025/11/18/
└── rpatel/
    ├── 1/                    # job-20251118-rpatel-0001
    │   ├── .job-20251118-rpatel-0001.env
    │   ├── job.json          # Contains job_id
    │   ├── manifest.json
    │   ├── logs/
    │   ├── media/
    │   ├── transcripts/
    │   └── subtitles/
    └── 2/                    # job-20251118-rpatel-0002
        └── ...
```

### Multi-User Structure
```
out/2025/11/18/
├── rpatel/
│   ├── 1/                    # job-20251118-rpatel-0001
│   └── 2/                    # job-20251118-rpatel-0002
└── john/
    └── 1/                    # job-20251118-john-0001
```

---

## Job ID Resolution

Jobs are found by reading `job.json` files:

```bash
# Structure
out/2025/11/18/rpatel/1/job.json

# Content
{
  "job_id": "job-20251118-rpatel-0001",
  ...
}
```

Scripts search for matching job_id in job.json files rather than directory names.

---

## Usage Examples

### Creating Jobs

```bash
# TRANSCRIBE: Hindi audio → Hindi text
$ ./prepare-job.sh movie1.mp4 --transcribe -s hi
Job created: job-20251118-rpatel-0001
Job directory: out/2025/11/18/rpatel/1

Output: Hindi transcript with timestamps in transcripts/segments.json

# TRANSLATE: Hindi text → English text + English .srt subtitles
$ ./prepare-job.sh movie1.mp4 --translate -s hi -t en
Job created: job-20251118-rpatel-0002
Job directory: out/2025/11/18/rpatel/2

Input: Reads transcript from previous transcribe job
Output: English transcript + English .srt subtitle file
```

### Complete Workflow Example

```bash
# Step 1: Transcribe Tamil audio to Tamil text
$ ./prepare-job.sh tamil-movie.mp4 --transcribe -s ta
Job created: job-20251118-rpatel-0001

$ ./run-pipeline.sh -j job-20251118-rpatel-0001
# Output: out/2025/11/18/rpatel/1/transcripts/segments.json (Tamil text)

# Step 2: Translate Tamil text to English + generate subtitles
$ ./prepare-job.sh tamil-movie.mp4 --translate -s ta -t en
Job created: job-20251118-rpatel-0002

$ ./run-pipeline.sh -j job-20251118-rpatel-0002
# Output: out/2025/11/18/rpatel/2/subtitles/output.srt (English subtitles)
```

### Running Jobs

```bash
# Run with full job ID
$ ./run-pipeline.sh -j job-20251118-rpatel-0001
[INFO] Finding job directory...
[SUCCESS] ✓ Job directory: out/2025/11/18/rpatel/1
```

### Checking Status

```bash
$ ./scripts/pipeline-status.sh job-20251118-rpatel-0001
📋 JOB STATUS: job-20251118-rpatel-0001
────────────────────────────────────────────────────
  📁 Location: out/2025/11/18/rpatel/1
  📊 Stage Progress:
    ✓ demux                    [COMPLETED]
    ✓ asr                      [COMPLETED]
...
```

### Listing Jobs

```bash
# List all jobs (shows job IDs from job.json)
$ find out -name "job.json" -exec grep -h "job_id" {} \; | cut -d'"' -f4 | sort
job-20251118-rpatel-0001
job-20251118-rpatel-0002
job-20251118-john-0001

# Browse by date
$ ls -l out/2025/11/18/rpatel/
1/
2/
```

---

## MLX Model Name Fix

**Issue**: MLX-Whisper requires full HuggingFace model names, not short names.

**Error**:
```
Repository Not Found for url: https://huggingface.co/api/models/large-v3/revision/main
```

**Fix**: Model name mapping added to `scripts/run-pipeline.py`:

```python
model_map = {
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "large-v2": "mlx-community/whisper-large-v2-mlx",
    "large": "mlx-community/whisper-large-v3-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    # ...
}
```

Now `large-v3` is automatically mapped to `mlx-community/whisper-large-v3-mlx`.

---

## Backward Compatibility

All scripts support multiple directory structures:

1. **New**: `out/YYYY/MM/DD/USERID/counter/` (job ID in job.json)
2. **Legacy v1**: `out/YYYY/MM/DD/username/job_NNNN/`
3. **Legacy v0**: `out/YYYY-MM-DD_HH-MM-SS/username/job-id/`

Job finding logic:
1. Search for job_id in job.json files (new format)
2. Match directory name (legacy formats)
3. Show helpful error with available jobs

---

## Updated Files

### Core Scripts
1. **`scripts/prepare-job.py`**
   - Updated `get_next_job_number()` - daily counter per user
   - Updated `create_job_directory()` - new structure & job ID format
   
2. **`run-pipeline.sh`**
   - Updated job search to read job.json files
   - Lists available jobs by parsing job.json
   
3. **`scripts/pipeline-status.sh`**
   - Updated job search logic
   - Shows correct directory structure
   
4. **`scripts/run-pipeline.py`**
   - Added MLX model name mapping
   - Fixed HuggingFace model repository access

### Documentation
1. **`README.md`** - Updated paths and examples
2. **`docs/ARCHITECTURE.md`** - Updated directory diagrams
3. **`docs/INDICTRANS2_ARCHITECTURE.md`** - Updated structure
4. **`docs/DIRECTORY_STRUCTURE_CHANGE.md`** - This document (updated)

---

## Migration Notes

### Existing Jobs

All old jobs continue to work. No migration required.

### New Jobs

All new jobs automatically use the new structure.

---

## Testing

✅ Job counter increments correctly (daily reset per user)  
✅ New directory structure: `out/2025/11/18/rpatel/1/`  
✅ Job ID format: `job-20251118-rpatel-0001`  
✅ run-pipeline.sh finds jobs by reading job.json  
✅ pipeline-status.sh displays correct info  
✅ MLX model name mapping works correctly  
✅ Backward compatibility verified  

---

## Summary

**New Structure Benefits:**
- **Simpler navigation**: Date → User → Counter number
- **Better job IDs**: Self-documenting with date and user
- **Daily organization**: Fresh counters each day
- **MLX fix**: Model names properly mapped for HuggingFace
- **Full compatibility**: All old jobs still work

**Job ID Format:** `job-YYYYMMDD-USERID-nnnn`  
**Directory:** `out/YYYY/MM/DD/USERID/counter/`  
**Resolution:** Job ID stored in `job.json` for reliable lookup
