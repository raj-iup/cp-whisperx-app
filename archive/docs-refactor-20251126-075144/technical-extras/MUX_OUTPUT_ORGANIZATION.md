# Mux Output Organization Enhancement

**Date:** 2024-11-25  
**Feature:** Organized mux stage output with media-specific subdirectories

---

## Overview

After the mux stage completes, the output video (with embedded subtitles) is now organized in a dedicated subdirectory named after the input media file (without extension).

---

## New Output Structure

### Before (Old):
```
out/2025/11/24/user/1/
├── media/
│   ├── movie.mp4                    # Original input
│   └── movie_subtitled.mp4          # Muxed output (flat structure)
└── 09_mux/                          # Empty or not used
```

### After (New):
```
out/2025/11/24/user/1/
├── media/
│   ├── movie.mp4                    # Original input
│   └── movie/                       # ✨ NEW: Media-specific subdirectory
│       └── movie_subtitled.mp4      # Muxed output (organized)
└── 09_mux/
    └── movie_subtitled.mp4          # Copy for stage tracking
```

---

## Implementation Details

### Directory Naming

The subdirectory name is derived from the input media filename **without extension**:

| Input File | Subdirectory Name | Muxed Output Path |
|------------|-------------------|-------------------|
| `movie.mp4` | `movie/` | `media/movie/movie_subtitled.mp4` |
| `song.mkv` | `song/` | `media/song/song_subtitled.mkv` |
| `clip.avi` | `clip/` | `media/clip/clip_subtitled.mkv` |
| `My Movie (2024).mp4` | `My Movie (2024)/` | `media/My Movie (2024)/My Movie (2024)_subtitled.mp4` |

### Files Modified

**scripts/run-pipeline.py** (lines 2027-2036):
```python
# Create subdirectory with media name (without extension)
media_name = input_media.stem  # e.g., "movie" from "movie.mp4"
output_subdir = self.job_dir / "media" / media_name
output_subdir.mkdir(parents=True, exist_ok=True)

output_video = output_subdir / f"{title}_subtitled{output_ext}"

self.logger.info(f"Output directory: {output_subdir.relative_to(self.job_dir)}")
```

**scripts/run-pipeline.py** (lines 2154-2166):
```python
# Copy to 09_mux stage directory for tracking
import shutil
mux_stage_dir = self.job_dir / "09_mux"
mux_stage_dir.mkdir(parents=True, exist_ok=True)
mux_copy = mux_stage_dir / output_video.name
shutil.copy2(output_video, mux_copy)
self.logger.info(f"✓ Copy saved to: {mux_copy.relative_to(self.job_dir)}")
```

---

## Benefits

### Organization
- ✅ **Clean Structure:** Media-specific subdirectories prevent clutter
- ✅ **Scalability:** Easy to process multiple media files
- ✅ **Clarity:** Clear separation between original and processed files

### Traceability
- ✅ **Stage Copy:** Copy in `09_mux/` for stage tracking
- ✅ **Original Preserved:** Input media remains in top-level `media/`
- ✅ **Easy Identification:** Subdirectory name matches input file

### Workflow
- ✅ **Multi-File Processing:** Process multiple media files independently
- ✅ **Batch Operations:** Easy to identify outputs by media name
- ✅ **Resume Support:** Clear indication of which media has been processed

---

## Examples

### Example 1: Single Movie

**Input:**
```bash
./prepare-job.sh in/Inception.mp4 --workflow subtitle -s en -t hi,ta
./run-pipeline.sh -j job-20251125-user-0001
```

**Output Structure:**
```
out/2025/11/25/user/1/
├── media/
│   ├── Inception.mp4                          # Original
│   └── Inception/                             # ✨ NEW
│       └── Inception_subtitled.mp4            # Muxed with 3 subtitle tracks
├── subtitles/
│   ├── Inception.en.srt
│   ├── Inception.hi.srt
│   └── Inception.ta.srt
└── 09_mux/
    └── Inception_subtitled.mp4                # Stage copy
```

### Example 2: Multiple Episodes

**Input:**
```bash
./prepare-job.sh in/Episode_01.mp4 --workflow subtitle -s hi -t en
./prepare-job.sh in/Episode_02.mp4 --workflow subtitle -s hi -t en
./prepare-job.sh in/Episode_03.mp4 --workflow subtitle -s hi -t en
```

**Output Structure:**
```
out/2025/11/25/user/
├── 1/                                     # Episode 1
│   └── media/
│       ├── Episode_01.mp4
│       └── Episode_01/
│           └── Episode_01_subtitled.mp4
├── 2/                                     # Episode 2
│   └── media/
│       ├── Episode_02.mp4
│       └── Episode_02/
│           └── Episode_02_subtitled.mp4
└── 3/                                     # Episode 3
    └── media/
        ├── Episode_03.mp4
        └── Episode_03/
            └── Episode_03_subtitled.mp4
```

### Example 3: Mixed Formats

**Input:**
```bash
./prepare-job.sh in/movie.mp4 --workflow subtitle -s hi -t en
./prepare-job.sh in/clip.mkv --workflow subtitle -s hi -t en
./prepare-job.sh in/video.avi --workflow subtitle -s hi -t en
```

**Output Structure:**
```
out/2025/11/25/user/
├── 1/
│   └── media/
│       ├── movie.mp4
│       └── movie/
│           └── movie_subtitled.mp4        # MP4 format preserved
├── 2/
│   └── media/
│       ├── clip.mkv
│       └── clip/
│           └── clip_subtitled.mkv         # MKV format preserved
└── 3/
    └── media/
        ├── video.avi
        └── video/
            └── video_subtitled.mkv        # Converted to MKV (AVI doesn't support subtitle tracks)
```

---

## Usage

### Accessing Muxed Output

**By Media Name:**
```bash
JOB_DIR="out/2025/11/25/user/1"
MEDIA_NAME="movie"

# Muxed video
MUXED_VIDEO="$JOB_DIR/media/$MEDIA_NAME/${MEDIA_NAME}_subtitled.mp4"

# Stage copy
STAGE_COPY="$JOB_DIR/09_mux/${MEDIA_NAME}_subtitled.mp4"
```

**Finding All Muxed Videos:**
```bash
# Find all muxed videos in a job
find out/2025/11/25/user/1/media -name "*_subtitled.*"

# Find all muxed videos across all jobs
find out -path "*/media/*" -name "*_subtitled.*"
```

### Batch Operations

**Copy All Muxed Videos:**
```bash
# Copy all muxed videos to a collection directory
find out -path "*/media/*/\*_subtitled.\*" -exec cp {} /path/to/collection/ \;
```

**Verify All Muxed Videos:**
```bash
# Check if muxing completed for all jobs
for job_dir in out/2025/11/25/user/*/; do
  if [ -f "$job_dir/09_mux/"*_subtitled.* ]; then
    echo "✓ $(basename $job_dir): Muxing complete"
  else
    echo "✗ $(basename $job_dir): Muxing incomplete"
  fi
done
```

---

## Logging

### Log Messages

When mux stage completes successfully:

```
[INFO] Output format: .mp4 (source: .mp4)
[INFO] Output directory: media/movie/
[INFO] Creating full video with 2 subtitle tracks...
[INFO]   • Track 0: Hindi (hin)
[INFO]   • Track 1: English (eng)
[INFO] Video created: movie_subtitled.mp4 (1234.5 MB)
[INFO] ✓ Video contains 2 subtitle tracks: HI, EN
[INFO] ✓ Copy saved to: 09_mux/movie_subtitled.mp4
```

### Log Location

All mux stage logs are in:
```
out/2025/11/25/user/1/logs/pipeline.log
```

---

## File Sizes

### Typical Sizes

| File Type | Typical Size | Notes |
|-----------|--------------|-------|
| Original Media | 500MB - 10GB | Depends on duration and quality |
| Muxed Output | +1-5MB | Subtitles add minimal size |
| Stage Copy | Same as muxed | Identical copy for tracking |

**Example:**
- Original: `movie.mp4` (2.5 GB)
- Muxed: `movie_subtitled.mp4` (2.502 GB) - only +2MB for 3 subtitle tracks
- Stage copy: `09_mux/movie_subtitled.mp4` (2.502 GB)

**Total Disk Usage:** ~5 GB (original + muxed + stage copy)

---

## Cleanup

### Removing Stage Copies

If disk space is a concern, remove stage copies:

```bash
# Remove all stage copies (keeps organized media subdirectories)
find out -path "*/09_mux/*_subtitled.*" -delete
```

### Removing Original Media

After successful muxing, you can remove originals:

```bash
# Remove original media (keeps muxed output)
find out -path "*/media/*.mp4" -not -path "*/media/*/*" -delete
find out -path "*/media/*.mkv" -not -path "*/media/*/*" -delete
find out -path "*/media/*.avi" -not -path "*/media/*/*" -delete
```

**Warning:** Only do this if you have backups of original media!

---

## Compatibility

### Backward Compatibility

✅ **Fully compatible** with existing workflow:
- Stage directories (`01_demux` through `09_mux`) unchanged
- Subtitle files in `subtitles/` unchanged
- Job configuration format unchanged
- Pipeline execution logic unchanged

### Future Enhancements

Potential future improvements:
- [ ] Configurable output directory (via job config)
- [ ] Option to skip stage copy (save disk space)
- [ ] Symbolic links instead of copies
- [ ] Multiple output formats (e.g., MP4 + MKV)

---

## Troubleshooting

### Issue 1: Subdirectory Not Created

**Symptom:**
```
Muxed output still in media/ root directory
```

**Diagnosis:**
```bash
# Check if new code is being used
grep "output_subdir" scripts/run-pipeline.py
```

**Solution:**
Run latest pipeline code

### Issue 2: Stage Copy Not Created

**Symptom:**
```
09_mux/ directory is empty
```

**Diagnosis:**
```bash
# Check logs
grep "Copy saved to" out/*/logs/pipeline.log
```

**Solution:**
Check for write permissions on `09_mux/`

### Issue 3: File Not Found

**Symptom:**
```
Cannot find muxed video at expected path
```

**Diagnosis:**
```bash
# Search for muxed videos
find out -name "*_subtitled.*"
```

**Solution:**
Update paths to include media subdirectory

---

## Summary

**Feature:** Mux output organized in media-specific subdirectories

**Structure:**
```
media/
├── [original_media].[ext]           # Input
└── [media_name]/                    # ✨ NEW: Subdirectory
    └── [media_name]_subtitled.[ext] # Muxed output

09_mux/
└── [media_name]_subtitled.[ext]     # Stage copy
```

**Benefits:**
- Clean organization
- Multi-file processing support
- Clear traceability
- Easy batch operations

**Files Modified:**
- `scripts/run-pipeline.py` - Mux stage output organization

---

**Date:** 2024-11-25  
**Status:** ✅ Implemented  
**Feature:** Media-specific subdirectories for mux output
