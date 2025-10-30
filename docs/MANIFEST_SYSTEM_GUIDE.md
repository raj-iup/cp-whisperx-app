# Manifest System - Complete Guide

## Overview

The manifest system tracks pipeline execution with:
- ✅ Per-stage completion tracking
- ✅ Success/skip/failure distinction  
- ✅ Automatic resume capability
- ✅ Next-stage pointers
- ✅ Timestamps and audit trail

## Manifest Structure

```json
{
  "timestamp": "2025-10-29T10:16:22.442988",
  "version": "0.1.0",
  "pipeline": {
    "current_stage": null,
    "next_stage": "diarization",
    "completed_stages": ["demux", "tmdb", "pre_ner", "silero_vad"],
    "skipped_stages": ["pyannote_vad"],
    "status": "running"
  },
  "steps": {
    "demux": {
      "enabled": true,
      "completed": true,
      "next_stage": "tmdb",
      "status": "success",
      "completed_at": "2025-10-29T10:17:01.781679"
    },
    "pyannote_vad": {
      "enabled": false,
      "completed": true,
      "next_stage": "diarization",
      "status": "skipped",
      "notes": "Failed - using Silero segments",
      "completed_at": "2025-10-29T10:42:42.039325"
    }
  }
}
```

## Usage in Pipeline

### Initialize Manifest

```python
from scripts.manifest import ManifestBuilder

# Create with auto-save
manifest_file = movie_dir / "manifest.json"
manifest = ManifestBuilder(manifest_file)
```

### Recording Stage Success

```python
manifest.set_pipeline_step(
    "stage_name",
    True,                        # enabled
    completed=True,
    next_stage="next_stage",
    status="success"
)
# Auto-saves to manifest.json
```

### Recording Stage Skip

```python
manifest.set_pipeline_step(
    "pyannote_vad",
    False,                       # not enabled/skipped
    completed=True,
    next_stage="diarization",    # IMPORTANT: Always set next!
    status="skipped",
    notes="Optional stage skipped"
)
```

### Recording Stage Failure

```python
manifest.set_pipeline_step(
    "stage_name",
    False,
    completed=True,
    next_stage=None,             # No next stage on critical failure
    status="failed",
    error="Error description"
)
manifest.finalize(status="failed")
```

## Resume Logic

### Check Completion

```python
completed = set(manifest.data["pipeline"]["completed_stages"])
skipped = set(manifest.data["pipeline"]["skipped_stages"])

if "stage_name" in completed:
    logger.info("Stage already completed - skipping")
    # Don't re-run
elif "stage_name" in skipped:
    logger.info("Stage was skipped previously - you can re-run if needed")
```

### Get Next Stage

```python
next_stage = manifest.get_next_stage()
if next_stage:
    logger.info(f"Resuming from: {next_stage}")
else:
    logger.info("All stages completed!")
```

## Stage Order

```python
STAGE_ORDER = [
    "demux",           # 1. Extract audio
    "tmdb",            # 2. Fetch metadata
    "pre_ner",         # 3. Extract entities
    "silero_vad",      # 4. Coarse VAD
    "pyannote_vad",    # 5. Refined VAD (optional)
    "diarization",     # 6. Speaker labels
    "asr",             # 7. Transcription
    "post_ner",        # 8. Entity correction
    "srt_generation",  # 9. Subtitle generation
    "mux"              # 10. Embed subtitles
]
```

## Best Practices

### 1. Always Set next_stage

Even when skipping or failing, set `next_stage`:
```python
# ✅ Good
manifest.set_pipeline_step("optional_stage", False, completed=True,
                          next_stage="next_required_stage", status="skipped")

# ❌ Bad - missing next_stage
manifest.set_pipeline_step("optional_stage", False, completed=True, status="skipped")
```

### 2. Use Correct Status Values

- `status="success"` → Added to `completed_stages`, won't re-run
- `status="skipped"` → Added to `skipped_stages`, can re-run
- `status="failed"` → Added to `skipped_stages`, indicates error

### 3. Finalize on Completion

```python
# At end of pipeline
manifest.finalize(status="completed")
```

## Troubleshooting

### Issue: Stage re-runs even though completed
**Solution:** Check that `status="success"` was set when recording completion

### Issue: Can't resume from middle
**Solution:** Ensure all stages set `next_stage` parameter

### Issue: Skipped stage blocks resume
**Solution:** Use `status="skipped"` instead of `status="success"` for optional stages

## Implementation Checklist

For each pipeline stage:
- [ ] Check if stage in `completed_stages` before running
- [ ] Call `manifest.set_pipeline_step()` with all parameters
- [ ] Always set `next_stage` (even on skip/fail)
- [ ] Use correct `status` value
- [ ] Handle errors with `status="failed"`

## Example: Complete Stage Implementation

```python
# Check if should skip
if "diarization" in manifest.data["pipeline"]["completed_stages"]:
    logger.info("⏭️ Skipping diarization - already completed")
else:
    # Run stage
    logger.info("Running diarization...")
    try:
        run_docker_stage("diarization", args, logger)
        
        # Record success
        manifest.set_pipeline_step(
            "diarization",
            True,
            completed=True,
            next_stage="asr",
            status="success"
        )
        logger.info("✓ Diarization complete")
        
    except Exception as e:
        # Record failure
        manifest.set_pipeline_step(
            "diarization",
            False,
            completed=True,
            next_stage=None,
            status="failed",
            error=str(e)
        )
        manifest.finalize(status="failed")
        raise
```

## Files

- `scripts/manifest.py` - ManifestBuilder implementation
- `out/{movie}/manifest.json` - Per-movie manifest
- `MANIFEST_FIXES_COMPLETE.md` - Implementation notes
- `MANIFEST_SYSTEM_GUIDE.md` - This guide

## Testing

Run the test to verify manifest behavior:
```bash
python3 -c "import sys; sys.path.insert(0, '.'); from scripts.manifest import ManifestBuilder; # ... test code"
```

See MANIFEST_FIXES_COMPLETE.md for test code.
