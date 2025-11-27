# Stage Directory Numbering - Developer Standard

## Overview

All pipeline stages use **sequential numeric prefixes** for their output directories. This ensures:
- Clear workflow progression
- Easy identification of stage dependencies
- Consistent directory structure across all jobs

## Standard Directory Structure

```
out/YYYY/MM/DD/user/N/
├── 01_demux/                    # Audio extraction from video
├── 02_source_separation/        # Vocal extraction (optional, if enabled)
├── 03_tmdb/                     # TMDB metadata enrichment
├── 04_pyannote_vad/            # Voice activity detection
├── 05_asr/                      # Automatic speech recognition
├── 06_alignment/                # Word-level timestamp alignment
├── 07_lyrics_detection/         # Song segment identification
├── 08_translation/              # Translation (IndicTrans2 or Hybrid)
├── 09_subtitle_generation/      # SRT file generation
├── 10_mux/                      # Subtitle embedding in video
├── logs/                        # Stage log files
├── media/                       # Input media files
├── subtitles/                   # Final subtitle outputs
├── transcripts/                 # Transcript JSON files
├── .job-XXXXX.env              # Job configuration
├── job.json                     # Job metadata
└── manifest.json                # Pipeline state tracking
```

## Stage Numbering Rules

### 1. Sequential Numbering
- Stages are numbered in **execution order**: `01, 02, 03, ...`
- Numbers increment by 1 for each stage
- No gaps in numbering sequence

### 2. Optional Stages
Optional stages (e.g., `02_source_separation`) retain their number even when skipped:
- Directory created during job preparation
- Remains empty if stage is disabled
- Preserves consistent numbering across jobs

### 3. Two-Digit Prefixes
- Always use **two digits**: `01`, `02`, ... `09`, `10`, ...
- Supports up to 99 stages
- Ensures proper alphabetical sorting

### 4. Descriptive Names
Format: `##_stage_name`
- Use **snake_case** for multi-word names
- Be descriptive but concise
- Examples: `05_asr`, `07_lyrics_detection`, `09_subtitle_generation`

## Stage Execution Order

### Transcribe Workflow
```
01_demux → 02_source_separation* → 03_tmdb* → 04_pyannote_vad → 
05_asr → 06_alignment → 07_lyrics_detection* → export_transcript
```

### Translate Workflow
```
load_transcript → 08_translation → 09_subtitle_generation
```

### Subtitle Workflow (Complete Pipeline)
```
01_demux → 02_source_separation* → 03_tmdb* → 04_pyannote_vad →
05_asr → 06_alignment → 07_lyrics_detection* → export_transcript →
load_transcript → 08_translation → 09_subtitle_generation → 10_mux
```

**Note**: Stages marked with `*` are optional and depend on configuration.

## Implementation Files

### Files Updated (2025-11-25)

1. **`scripts/run-pipeline.py`**
   - All stage directory references
   - Path constructions for input/output

2. **`scripts/prepare-job.py`**
   - Stage directory creation list
   - Job structure initialization

3. **`scripts/tmdb_enrichment_stage.py`**
   - Output directory: `03_tmdb`
   - Log file path

4. **`scripts/bias_injection.py`**
   - TMDB file reference: `03_tmdb/enrichment.json`

5. **`scripts/lyrics_detection.py`**
   - TMDB file reference: `03_tmdb/enrichment.json`

6. **`scripts/name_entity_correction.py`**
   - TMDB metadata reference: `03_tmdb/metadata.json`

7. **`config/hardware_cache.json`**
   - Stage environment mapping

## Code Examples

### Creating Stage Output Directory

```python
from pathlib import Path

# In stage script
stage_dir = job_dir / "05_asr"
stage_dir.mkdir(parents=True, exist_ok=True)

# Save output
output_file = stage_dir / "segments.json"
with open(output_file, 'w') as f:
    json.dump(data, f, indent=2)
```

### Reading from Previous Stage

```python
# Read from previous stage
input_file = job_dir / "04_pyannote_vad" / "speech_segments.json"
if input_file.exists():
    with open(input_file) as f:
        segments = json.load(f)
```

### Using StageIO Pattern

```python
from shared.stage_utils import StageIO

# Initialize StageIO with current stage name
stage_io = StageIO("asr")  # Automatically uses 05_asr directory

# Get input from previous stage
vad_data = stage_io.load_json("speech_segments.json", from_stage="pyannote_vad")

# Save output to current stage
stage_io.save_json(output_data, "segments.json")
```

## Migration from Old Numbering

### Renumbering Changes (November 2025)

| Old Number | New Number | Stage Name |
|------------|------------|------------|
| 02_tmdb | 03_tmdb | TMDB enrichment |
| 03_pyannote_vad | 04_pyannote_vad | Voice activity detection |
| 04_asr | 05_asr | Speech recognition |
| 05_alignment | 06_alignment | Word alignment |
| 06_lyrics_detection | 07_lyrics_detection | Lyrics detection |
| 07_translation | 08_translation | Translation |
| 08_subtitle_generation | 09_subtitle_generation | Subtitle generation |
| 09_mux | 10_mux | Video muxing |

### Backward Compatibility

**Old job directories** (created before renumbering) will continue to work:
- Pipeline reads from old paths as fallback
- No need to re-run old jobs
- New jobs use new numbering

## Validation

### Directory Structure Check

```bash
# Verify stage directories exist and are properly numbered
ls -d out/YYYY/MM/DD/user/N/[0-9][0-9]_*

# Expected output:
# 01_demux
# 02_source_separation
# 03_tmdb
# 04_pyannote_vad
# 05_asr
# 06_alignment
# 07_lyrics_detection
# 08_translation
# 09_subtitle_generation
# 10_mux
```

### Naming Convention Check

```python
import re

def validate_stage_directory(name: str) -> bool:
    """Validate stage directory naming convention"""
    pattern = r'^\d{2}_[a-z][a-z0-9_]*$'
    return bool(re.match(pattern, name))

# Valid examples
assert validate_stage_directory("05_asr")
assert validate_stage_directory("07_lyrics_detection")
assert validate_stage_directory("10_mux")

# Invalid examples
assert not validate_stage_directory("5_asr")  # Single digit
assert not validate_stage_directory("05_ASR")  # Uppercase
assert not validate_stage_directory("05_")  # No name
```

## Best Practices

### DO ✅

1. **Use sequential numbers** starting from 01
2. **Keep numbers consistent** across all code and documentation
3. **Create directories during job preparation** (even if optional)
4. **Document stage purpose** in comments
5. **Use StageIO** for path management when possible

### DON'T ❌

1. **Don't skip numbers** (e.g., 01, 02, 04 - missing 03)
2. **Don't reuse numbers** for different stages
3. **Don't hardcode paths** - use job_dir or StageIO
4. **Don't use single digits** (e.g., `1_demux` instead of `01_demux`)
5. **Don't change numbering** without updating all references

## Troubleshooting

### Issue: Stage directory not found

**Symptom**: FileNotFoundError for stage directory

**Solution**: Check if stage number changed during refactoring
```bash
# Find actual directory
ls -d out/YYYY/MM/DD/user/N/*_stage_name

# Update code to use correct number
```

### Issue: Inconsistent numbering between jobs

**Symptom**: Different jobs have different stage numbers

**Cause**: prepare-job.py not updated after renumbering

**Solution**: Regenerate job with updated prepare-job.py

### Issue: Missing stage directory

**Symptom**: Directory doesn't exist even though stage ran

**Cause**: Stage didn't create output directory

**Solution**: Ensure stage creates directory in code:
```python
stage_dir = job_dir / "05_asr"
stage_dir.mkdir(parents=True, exist_ok=True)
```

## References

- [DEVELOPER_STANDARDS_COMPLIANCE.md](DEVELOPER_STANDARDS_COMPLIANCE.md) - Compliance guidelines
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Development standards
- [shared/stage_utils.py](../shared/stage_utils.py) - StageIO implementation

---

**Last Updated**: November 25, 2025  
**Version**: 2.0  
**Status**: Active Standard
