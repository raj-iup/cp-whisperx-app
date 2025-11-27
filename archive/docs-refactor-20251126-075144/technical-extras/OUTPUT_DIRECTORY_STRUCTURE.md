# Output Directory Structure Enhancement

**Date:** 2024-11-25  
**Feature:** Structured output directories with sequential stage subdirectories

---

## New Directory Structure

### Overview

Job outputs are now organized in a hierarchical structure:

```
out/
├── [YEAR]/          # e.g., 2025
│   ├── [MONTH]/     # e.g., 11
│   │   ├── [DAY]/   # e.g., 25
│   │   │   ├── [USERID]/      # e.g., rpatel (system username)
│   │   │   │   ├── [JOBNO]/   # e.g., 1, 2, 3...
│   │   │   │   │   ├── logs/
│   │   │   │   │   ├── media/
│   │   │   │   │   ├── transcripts/
│   │   │   │   │   ├── subtitles/
│   │   │   │   │   ├── 01_demux/
│   │   │   │   │   ├── 02_source_separation/
│   │   │   │   │   ├── 03_pyannote_vad/
│   │   │   │   │   ├── 04_asr/
│   │   │   │   │   ├── 05_alignment/
│   │   │   │   │   ├── 06_lyrics_detection/
│   │   │   │   │   ├── 07_translation/
│   │   │   │   │   ├── 08_subtitle_generation/
│   │   │   │   │   └── 09_mux/
│   │   │   │   ├── 2/
│   │   │   │   └── ...
│   │   │   └── [OTHER_USERID]/
│   │   └── [OTHER_DAY]/
│   └── [OTHER_MONTH]/
└── [OTHER_YEAR]/
```

---

## Directory Purpose

### Hierarchical Organization

| Level | Purpose | Example | Notes |
|-------|---------|---------|-------|
| **YEAR** | Year grouping | `2025` | 4-digit year |
| **MONTH** | Month grouping | `11` | 2-digit month (01-12) |
| **DAY** | Day grouping | `25` | 2-digit day (01-31) |
| **USERID** | User separation | `rpatel` | System username or provided user_id |
| **JOBNO** | Sequential job counter | `1`, `2`, `3` | Auto-increments per user per day |

### Main Directories

| Directory | Purpose | Contents |
|-----------|---------|----------|
| **logs/** | Pipeline logs | `pipeline.log`, stage logs |
| **media/** | Input media | Original or clipped media files |
| **transcripts/** | Text outputs | `transcript.txt`, `segments.json` |
| **subtitles/** | Final subtitles | `*.srt` files for all languages |

### Stage Directories (Sequential)

| Directory | Stage | Outputs |
|-----------|-------|---------|
| **01_demux/** | Audio extraction | `audio.wav`, stream info |
| **02_source_separation/** | Vocal isolation | `vocals.wav`, `accompaniment.wav` |
| **03_pyannote_vad/** | Voice activity detection | VAD segments, silence detection |
| **04_asr/** | Speech recognition | Raw transcripts, word timestamps |
| **05_alignment/** | Alignment refinement | Aligned segments with precise timing |
| **06_lyrics_detection/** | Song detection | Lyrics markers, confidence scores |
| **07_translation/** | Text translation | Translated segments (one per target language) |
| **08_subtitle_generation/** | Subtitle creation | Individual `.srt` files per language |
| **09_mux/** | Final muxing | Video with embedded subtitle tracks |

---

## Examples

### Example 1: Single Job

```
out/2025/11/25/rpatel/1/
├── logs/
│   └── pipeline.log
├── media/
│   └── movie.mp4
├── transcripts/
│   ├── transcript.txt
│   └── segments.json
├── subtitles/
│   ├── movie_hi.srt
│   └── movie_en.srt
├── 01_demux/
│   └── audio.wav
├── 02_source_separation/
│   ├── vocals.wav
│   └── accompaniment.wav
├── 03_pyannote_vad/
│   └── vad_segments.json
├── 04_asr/
│   ├── raw_transcript.json
│   └── word_timestamps.json
├── 05_alignment/
│   └── aligned_segments.json
├── 06_lyrics_detection/
│   └── lyrics_markers.json
├── 07_translation/
│   ├── segments_en.json
│   └── segments_ta.json
├── 08_subtitle_generation/
│   ├── movie_hi.srt
│   ├── movie_en.srt
│   └── movie_ta.srt
└── 09_mux/
    └── movie_subtitled.mkv
```

### Example 2: Multiple Jobs Same Day

```
out/2025/11/25/rpatel/
├── 1/          # First job
│   ├── logs/
│   ├── media/
│   └── ...
├── 2/          # Second job
│   ├── logs/
│   ├── media/
│   └── ...
└── 3/          # Third job
    ├── logs/
    ├── media/
    └── ...
```

### Example 3: Multiple Users

```
out/2025/11/25/
├── rpatel/     # User 1
│   ├── 1/
│   └── 2/
├── jsmith/     # User 2
│   ├── 1/
│   └── 2/
└── adoe/       # User 3
    └── 1/
```

---

## Job ID Format

**Format:** `job-YYYYMMDD-USERID-nnnn`

**Examples:**
- `job-20251125-rpatel-0001` - First job on 2025-11-25 by rpatel
- `job-20251125-rpatel-0002` - Second job same day by rpatel
- `job-20251125-jsmith-0001` - First job same day by jsmith

**Components:**
- `YYYYMMDD` - Date (8 digits)
- `USERID` - User identifier
- `nnnn` - 4-digit zero-padded job number

---

## Benefits

### Organization
- ✅ **Chronological:** Easy to find jobs by date
- ✅ **User Separation:** Multi-user support
- ✅ **Sequential:** Clear job ordering per day
- ✅ **Stage Tracking:** Dedicated directories for each pipeline stage

### Debugging
- ✅ **Stage Isolation:** Each stage's output in separate directory
- ✅ **Easy Navigation:** Numbered directories show execution order
- ✅ **Intermediate Files:** All intermediate outputs preserved
- ✅ **Resume Support:** Can resume from any stage

### Maintenance
- ✅ **Auto-Cleanup:** Easy to delete old jobs by date
- ✅ **Backup:** Simple to backup by date range
- ✅ **Disk Management:** Monitor usage per user/date
- ✅ **Archival:** Archive old dates to cold storage

---

## Usage

### Finding Job Output

```bash
# By job ID
JOB_ID="job-20251125-rpatel-0001"

# Extract date and user
DATE="20251125"
USER="rpatel"
JOBNO="0001"

# Build path
YEAR=${DATE:0:4}   # 2025
MONTH=${DATE:4:2}  # 11
DAY=${DATE:6:2}    # 25

# Full path
JOB_DIR="out/$YEAR/$MONTH/$DAY/$USER/${JOBNO#0}"
echo $JOB_DIR
# Output: out/2025/11/25/rpatel/1
```

### Accessing Stage Output

```bash
# Job directory
JOB_DIR="out/2025/11/25/rpatel/1"

# Stage outputs
ls $JOB_DIR/01_demux/           # Audio extraction
ls $JOB_DIR/02_source_separation/  # Vocal isolation
ls $JOB_DIR/04_asr/             # ASR transcripts
ls $JOB_DIR/07_translation/     # Translations
ls $JOB_DIR/08_subtitle_generation/  # Subtitles
```

### Listing Jobs

```bash
# All jobs today
TODAY=$(date +%Y/%m/%d)
ls -la out/$TODAY/$USER/

# All jobs for a user
find out -path "*/$USER/*" -type d -name "[0-9]*" | sort

# All jobs on a date
find out/2025/11/25 -type d -name "[0-9]*" | sort
```

### Cleanup Old Jobs

```bash
# Delete jobs older than 30 days
find out -type d -mtime +30 -path "*/[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]/*" -exec rm -rf {} \;

# Archive jobs older than 90 days
find out -type d -mtime +90 -path "*/[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]" -exec tar -czf {}.tar.gz {} \; -exec rm -rf {} \;
```

---

## Implementation

### Files Modified

**scripts/prepare-job.py** (lines 130-160):
- Added creation of sequential stage directories
- Maintains existing logs/, media/, transcripts/, subtitles/ directories
- Stage directories: 01_demux through 09_mux

### Stage Directory Names

```python
stage_dirs = [
    "01_demux",
    "02_source_separation", 
    "03_pyannote_vad",
    "04_asr",
    "05_alignment",
    "06_lyrics_detection",
    "07_translation",
    "08_subtitle_generation",
    "09_mux"
]
```

### Backward Compatibility

- ✅ Existing `logs/`, `media/`, `transcripts/`, `subtitles/` directories maintained
- ✅ Job ID format unchanged
- ✅ Stage output paths updated to use new directories
- ✅ Old jobs (if any) still accessible

---

## Migration

### For Existing Jobs

Old job structure (if exists):
```
out/
└── some-job-id/
    ├── logs/
    ├── media/
    ├── transcripts/
    └── subtitles/
```

New job structure:
```
out/
└── 2025/11/25/rpatel/1/
    ├── logs/
    ├── media/
    ├── transcripts/
    ├── subtitles/
    ├── 01_demux/
    ├── 02_source_separation/
    └── ... (stage directories)
```

**Note:** Old jobs are not migrated automatically. New directory structure applies to new jobs only.

---

## Monitoring

### Disk Usage by User

```bash
# Total usage per user
for user in out/*/*/*/*; do
  [ -d "$user" ] && echo "$user: $(du -sh $user | cut -f1)"
done
```

### Jobs per Day

```bash
# Count jobs per day
find out -path "*/[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]" -type d | while read date_dir; do
  count=$(find "$date_dir" -mindepth 2 -maxdepth 2 -type d | wc -l)
  echo "$date_dir: $count jobs"
done
```

### Active Stages

```bash
# Find incomplete jobs (missing 09_mux directory)
find out -type d -path "*/*/*/*/*" -name "01_demux" | while read stage; do
  job_dir=$(dirname "$stage")
  [ ! -d "$job_dir/09_mux" ] && echo "Incomplete: $job_dir"
done
```

---

## Summary

**Feature:** Structured output directories with sequential stage subdirectories

**Structure:**
```
out/[YEAR]/[MONTH]/[DAY]/[USERID]/[JOBNO]/
├── logs/                    # Pipeline logs
├── media/                   # Input media
├── transcripts/             # Text outputs
├── subtitles/               # Final subtitles
├── 01_demux/                # Audio extraction
├── 02_source_separation/    # Vocal isolation
├── 03_pyannote_vad/         # Voice activity
├── 04_asr/                  # Speech recognition
├── 05_alignment/            # Alignment
├── 06_lyrics_detection/     # Song detection
├── 07_translation/          # Translation
├── 08_subtitle_generation/  # Subtitle creation
└── 09_mux/                  # Final muxing
```

**Benefits:**
- Chronological organization
- Multi-user support
- Sequential stage tracking
- Easy debugging and maintenance

**Files Modified:**
- `scripts/prepare-job.py` - Added stage directory creation

---

**Date:** 2024-11-25  
**Status:** ✅ Implemented  
**Feature:** Enhanced output directory structure
