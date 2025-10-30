# Pipeline Implementation Quick Reference

## Essential Checklist for Each Stage

### Before Running Stage:
```python
if should_skip_stage("stage_name", manifest):
    logger.info("⏭️ Skipping - already completed")
else:
    # Run the stage
```

### Run Stage with Timeout:
```python
success = run_docker_stage("service", args, timeout=900)
```

### Record Success:
```python
manifest.set_pipeline_step(
    "stage_name",
    True,
    completed=True,
    next_stage="next_stage_name",  # ← CRITICAL!
    status="success",
    duration=elapsed_time
)
```

### Record Skip:
```python
manifest.set_pipeline_step(
    "stage_name",
    False,
    completed=True,
    next_stage="next_stage_name",  # ← STILL REQUIRED!
    status="skipped",
    notes="Reason for skip"
)
```

### Record Failure:
```python
manifest.set_pipeline_step(
    "stage_name",
    False,
    completed=True,
    next_stage=None,  # Stop on critical failure
    status="failed",
    error=str(exception)
)
manifest.finalize(status="failed")
```

## Common Mistakes to Avoid

❌ **Don't:** Skip without setting next_stage
```python
manifest.set_pipeline_step("pyannote_vad", False, completed=True, status="skipped")
# Missing next_stage! Pipeline won't know where to resume!
```

✅ **Do:** Always set next_stage
```python
manifest.set_pipeline_step("pyannote_vad", False, completed=True, 
                          next_stage="diarization", status="skipped")
```

❌ **Don't:** Use status="success" for skipped stages
```python
manifest.set_pipeline_step("pyannote_vad", False, completed=True,
                          next_stage="diarization", status="success")
# Will block resume even though stage didn't run!
```

✅ **Do:** Use status="skipped" for optional stages
```python
manifest.set_pipeline_step("pyannote_vad", False, completed=True,
                          next_stage="diarization", status="skipped")
```

## Recommended Timeouts

```python
STAGE_TIMEOUTS = {
    "demux": 600,           # 10 min
    "tmdb": 60,             # 1 min
    "pre_ner": 300,         # 5 min
    "silero_vad": 900,      # 15 min
    "pyannote_vad": 7200,   # 2 hours
    "diarization": 1800,    # 30 min
    "asr": 3600,            # 1 hour
    "post_ner": 600,        # 10 min
    "srt_generation": 300,  # 5 min
    "mux": 600              # 10 min
}
```

## Stage Dependencies

```
demux → tmdb → pre_ner → silero_vad → pyannote_vad* → diarization → asr → post_ner → srt_generation → mux
                                          *optional
```

## Files to Reference

- `scripts/manifest.py` - ManifestBuilder implementation
- `MANIFEST_SYSTEM_GUIDE.md` - Complete usage guide
- `MANIFEST_FIXES_COMPLETE.md` - Implementation notes
- `PIPELINE_BEST_PRACTICES.md` - Detailed best practices (this summary)

## Quick Test

```python
# Test manifest behavior
from scripts.manifest import ManifestBuilder

manifest = ManifestBuilder()

# Success
manifest.set_pipeline_step("demux", True, completed=True, 
                          next_stage="tmdb", status="success")

# Skip
manifest.set_pipeline_step("pyannote_vad", False, completed=True,
                          next_stage="diarization", status="skipped")

# Verify
assert "demux" in manifest.data["pipeline"]["completed_stages"]
assert "pyannote_vad" in manifest.data["pipeline"]["skipped_stages"]
assert "pyannote_vad" not in manifest.data["pipeline"]["completed_stages"]
```

## Session Management

For long-running pipelines, use screen or tmux:

```bash
# Start in screen
screen -S pipeline
python pipeline.py -i "input.mp4"
# Ctrl+A, D to detach

# Reattach
screen -r pipeline
```

Or use nohup:

```bash
nohup python pipeline.py -i "input.mp4" > pipeline.log 2>&1 &
tail -f pipeline.log
```
