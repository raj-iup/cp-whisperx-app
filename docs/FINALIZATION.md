# Output Finalization Feature

**Added**: 2025-11-09  
**Stage**: `finalize` (runs automatically after `mux`)

---

## Overview

The finalization stage automatically organizes pipeline output into a clean, title-based directory structure for easy access and sharing.

### What It Does

After the mux stage completes, the finalization stage:

1. **Extracts movie title** from orchestrator log
2. **Creates title directory** with sanitized name
3. **Moves final video** to title directory
4. **Renames video** to match title
5. **Copies subtitle files** (if present)
6. **Creates README** with job information

### Benefits

✅ **Clean organization** - One directory per movie  
✅ **Easy to find** - Named after movie title  
✅ **Ready to share** - All files in one place  
✅ **Automatic** - Runs without user intervention  
✅ **Non-critical** - Pipeline succeeds even if finalization fails  

---

## How It Works

### Automatic Execution

The finalization runs automatically as the last pipeline stage:

```bash
# Just run the pipeline normally
./run_pipeline.sh -j <job-id>

# After mux completes, finalization runs automatically
# Output is organized into title-based directory
```

### Directory Structure

**Before finalization**:
```
out/2025/11/09/1/20251109-0001/
├── final_output.mp4          # 950 MB
├── audio.wav
├── metadata.json
└── logs/
```

**After finalization**:
```
out/2025/11/09/1/20251109-0001/
├── Jaane_Tu_Ya_Jaane_Na/     # New directory
│   ├── Jaane_Tu_Ya_Jaane_Na.mp4  # 950 MB (moved & renamed)
│   └── README.txt            # Job info
├── audio.wav
├── metadata.json
└── logs/
```

### File Naming

- **Directory**: Sanitized movie title (spaces→underscores, special chars removed)
- **Video file**: `{sanitized_title}.mp4`
- **Subtitles**: Copied if present, renamed to match

**Examples**:
```
"Jaane Tu Ya Jaane Na" → Jaane_Tu_Ya_Jaane_Na/Jaane_Tu_Ya_Jaane_Na.mp4
"3 Idiots" → 3_Idiots/3_Idiots.mp4
"Dil Chahta Hai" → Dil_Chahta_Hai/Dil_Chahta_Hai.mp4
```

---

## Manual Usage

You can also run finalization manually:

### Using Helper Script

```bash
# macOS/Linux
./finalize-output.sh <job-id>

# Windows
.\finalize-output.ps1 <job-id>

# Example
./finalize-output.sh 20251109-0001
```

### Using Python Directly

```bash
python3 scripts/finalize_output.py /path/to/job/directory

# Example
python3 scripts/finalize_output.py out/2025/11/09/1/20251109-0001
```

---

## Output Files

### Video File

The final video with embedded subtitles:

```
out/2025/11/09/1/20251109-0001/Jaane_Tu_Ya_Jaane_Na/Jaane_Tu_Ya_Jaane_Na.mp4
```

### README.txt

Job information file:

```
Movie: Jaane Tu Ya Jaane Na
Processed: 2025-11-09 15:39:38
Job ID: 20251109-0001

Files:
- Jaane_Tu_Ya_Jaane_Na.mp4 (final video with subtitles)

Pipeline output directory: /path/to/job
```

### Subtitle Files (if copied)

Any `.srt` files from job directory:

```
Jaane_Tu_Ya_Jaane_Na/
├── Jaane_Tu_Ya_Jaane_Na.mp4
├── Jaane_Tu_Ya_Jaane_Na.srt  # Renamed from final_output.srt
└── README.txt
```

---

## Configuration

### Environment Variables

**In job `.env` file** (optional):

```bash
# Control finalization (default: runs automatically)
# Not yet implemented - always runs by default

# Future: FINALIZE_ENABLED=true
```

### Pipeline Integration

The finalize stage is added to `STAGE_DEFINITIONS` in `scripts/pipeline.py`:

```python
("mux", "finalize", "mux", 600, True, False),
("finalize", None, "finalize", 60, False, False),
```

**Properties**:
- **Stage name**: `finalize`
- **Previous stage**: `mux`
- **Timeout**: 60 seconds
- **Critical**: No (non-critical - pipeline succeeds even if fails)
- **ML model**: No

---

## Title Extraction

### Source

Title is extracted from **orchestrator log, line 18**:

```
logs/00_orchestrator_YYYYMMDD_HHMMSS.log
```

**Example line 18**:
```
[2025-11-09 13:36:34] [orchestrator] [INFO] Title: Jaane Tu Ya Jaane Na
```

### Sanitization

Title is sanitized for filesystem safety:

| Original | Sanitized |
|----------|-----------|
| `Jaane Tu Ya Jaane Na` | `Jaane_Tu_Ya_Jaane_Na` |
| `3 Idiots` | `3_Idiots` |
| `Dil Chahta Hai` | `Dil_Chahta_Hai` |
| `Movie: Title / Subtitle` | `Movie_Title__Subtitle` |
| `Very Long Movie Title...` | Truncated to 200 chars |

**Rules**:
- Spaces → underscores
- Special characters (`<>:"/\|?*`) → removed
- Multiple spaces → single underscore
- Trailing dots/underscores → removed
- Max length: 200 characters

---

## Troubleshooting

### Finalization Failed (Non-Critical)

**Symptom**: Pipeline completes but files not organized

**Check logs**:
```bash
grep -A 10 "finalize" out/.../logs/00_orchestrator_*.log
```

**Common causes**:

1. **No orchestrator log found**
   ```
   Solution: Check logs/ directory exists
   ```

2. **Title not found on line 18**
   ```
   Solution: Verify log format
   ```

3. **final_output.mp4 missing**
   ```
   Solution: Check mux stage completed successfully
   ```

4. **Permission denied**
   ```
   Solution: Check write permissions on job directory
   ```

### Manually Re-run Finalization

If finalization failed during pipeline run:

```bash
# Re-run just the finalization
./finalize-output.sh 20251109-0001

# Or use Python directly
python3 scripts/finalize_output.py out/2025/11/09/1/20251109-0001
```

### Directory Already Exists

If title directory already exists:

- Script checks for existing files
- If video already there, reports success without moving
- Safe to run multiple times (idempotent)

---

## Examples

### Example 1: Jaane Tu Ya Jaane Na

```bash
# Pipeline run
./run_pipeline.sh -j 20251109-0001

# After mux completes, finalization runs:
[finalize] [INFO] Extracting title: Jaane Tu Ya Jaane Na
[finalize] [INFO] Creating: Jaane_Tu_Ya_Jaane_Na/
[finalize] [INFO] Moving: final_output.mp4 → Jaane_Tu_Ya_Jaane_Na.mp4
[finalize] [INFO] ✓ Organization complete

# Result:
out/2025/11/09/1/20251109-0001/Jaane_Tu_Ya_Jaane_Na/
├── Jaane_Tu_Ya_Jaane_Na.mp4  # 950 MB
└── README.txt
```

### Example 2: Multiple Movies

```bash
# Process multiple movies
./prepare-job.sh movie1.mp4  # Job ID: 20251109-0001
./prepare-job.sh movie2.mp4  # Job ID: 20251109-0002
./prepare-job.sh movie3.mp4  # Job ID: 20251109-0003

# Run pipelines
./run_pipeline.sh -j 20251109-0001  # → Dil_Chahta_Hai/
./run_pipeline.sh -j 20251109-0002  # → 3_Idiots/
./run_pipeline.sh -j 20251109-0003  # → Zindagi_Na_Milegi_Dobara/

# Each organized into own directory
out/2025/11/09/1/
├── 20251109-0001/Dil_Chahta_Hai/Dil_Chahta_Hai.mp4
├── 20251109-0002/3_Idiots/3_Idiots.mp4
└── 20251109-0003/Zindagi_Na_Milegi_Dobara/Zindagi_Na_Milegi_Dobara.mp4
```

---

## Implementation Details

### Script Location

```
scripts/finalize_output.py  # Python implementation
finalize-output.sh          # Shell wrapper (macOS/Linux)
finalize-output.ps1         # PowerShell wrapper (Windows)
```

### Integration Point

In `scripts/pipeline.py`, after mux stage:

```python
# Special handling for finalize stage
if stage_name == "finalize":
    self.logger.info("📁 Organizing final output...")
    try:
        finalize_script = PROJECT_ROOT / "scripts" / "finalize_output.py"
        result = subprocess.run(
            [sys.executable, str(finalize_script), str(self.job_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            self.logger.info("✓ Output organized successfully")
        else:
            self.logger.warning("Output organization failed (non-critical)")
    
    except Exception as e:
        self.logger.warning(f"Output organization failed (non-critical): {e}")
    
    continue  # Always continue (non-critical)
```

### Functions

**`finalize_output.py`**:
- `extract_title_from_log()` - Parse line 18 from orchestrator log
- `sanitize_title()` - Clean title for filesystem
- `find_orchestrator_log()` - Locate log file
- `organize_final_output()` - Main organization logic

---

## Future Enhancements

Potential improvements:

- [ ] Custom output directory via config
- [ ] Copy additional metadata files
- [ ] Generate thumbnail/poster image
- [ ] Create media info file (codec, resolution, duration)
- [ ] Support for multi-episode series
- [ ] Cloud upload integration (optional)

---

## Summary

The finalization stage provides automatic, clean organization of pipeline output:

✅ **Automatic** - Runs after mux  
✅ **Clean** - One directory per movie  
✅ **Named** - Uses actual movie title  
✅ **Complete** - Includes video, subtitles, README  
✅ **Safe** - Non-critical, won't break pipeline  
✅ **Manual** - Can re-run if needed  

**No configuration required - works out of the box!**

---

**Version**: 1.0  
**Date Added**: 2025-11-09  
**Status**: Production Ready
