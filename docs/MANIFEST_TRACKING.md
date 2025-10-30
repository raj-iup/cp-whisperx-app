# Pipeline Manifest Tracking

**Status**: ✅ Implemented  
**Goal**: Each stage generates manifest.json with execution status and output tracking

---

## Overview

Every stage in the pipeline now tracks its execution in a shared `manifest.json` file located in the movie output directory. This enables:

- ✅ **Resume capability** after failures
- ✅ **Audit trail** of pipeline execution  
- ✅ **Output tracking** with full paths
- ✅ **Graceful exit handling**
- ✅ **Error tracking** for debugging

---

## Manifest Structure

### Location
```
out/{Movie_Title}/manifest.json
```

### Format
```json
{
  "version": "1.0.0",
  "created_at": "2024-10-29T20:00:00",
  "updated_at": "2024-10-29T20:30:00",
  "movie_dir": "/app/out/Movie_Title_2024",
  "stages": {
    "demux": {
      "status": "success",
      "started_at": "2024-10-29T20:00:00",
      "completed_at": "2024-10-29T20:01:30",
      "duration_seconds": 90.5,
      "outputs": {
        "audio": {
          "path": "/app/out/Movie_Title_2024/audio/audio.wav",
          "exists": true,
          "size_bytes": 52428800,
          "description": "16kHz mono audio"
        },
        "metadata": {
          "path": "/app/out/Movie_Title_2024/audio/metadata.json",
          "exists": true,
          "size_bytes": 256
        }
      },
      "metadata": {
        "sample_rate": 16000,
        "channels": 1,
        "duration_seconds": 1800
      }
    },
    "tmdb": { ... },
    "pre_ner": { ... }
  },
  "pipeline": {
    "status": "running",
    "current_stage": "asr",
    "completed_stages": ["demux", "tmdb", "pre_ner", "silero_vad"],
    "failed_stages": []
  }
}
```

---

## Stage Status Values

| Status | Description |
|--------|-------------|
| `running` | Stage is currently executing |
| `success` | Stage completed successfully |
| `failed` | Stage failed with error |
| `skipped` | Stage was skipped (optional stage) |

---

## Usage in Container Scripts

### Method 1: Context Manager (Recommended)

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, '/app/shared')

from logger import setup_logger
from config import load_config
from manifest import StageManifest

def main():
    config = load_config()
    logger = setup_logger("stage_name", ...)
    
    movie_dir = Path(sys.argv[1])  # Get from args
    
    # Context manager handles success/failure automatically
    with StageManifest("stage_name", movie_dir, logger) as manifest:
        logger.info("Starting stage")
        
        # Do stage work
        output_file = movie_dir / "output" / "result.json"
        process_data(output_file)
        
        # Record outputs
        manifest.add_output("result", output_file, "Stage output")
        
        # Record metadata
        manifest.add_metadata("records_processed", 1000)
        manifest.add_metadata("model_version", "v1.0")
        
        # On successful exit from context, manifest is saved with success status
        # On exception, manifest is saved with failed status

if __name__ == "__main__":
    main()
```

### Method 2: Manual Control

```python
def main():
    config = load_config()
    logger = setup_logger("stage_name", ...)
    movie_dir = Path(sys.argv[1])
    
    manifest = StageManifest("stage_name", movie_dir, logger)
    
    try:
        logger.info("Starting stage")
        
        # Do stage work
        output_file = process_data()
        
        # Record outputs
        manifest.add_output("result", output_file)
        
        # Save with success
        manifest.save(status="success")
        logger.info("✓ Stage completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Stage failed: {e}")
        manifest.set_error(str(e))
        manifest.save(status="failed")
        sys.exit(1)
```

---

## Expected Outputs Per Stage

### Stage 1: Demux
```python
manifest.add_output("audio", audio_dir / "audio.wav", "16kHz mono audio")
manifest.add_output("metadata", audio_dir / "metadata.json", "Audio metadata")
manifest.add_metadata("sample_rate", 16000)
manifest.add_metadata("duration_seconds", duration)
```

### Stage 2: TMDB
```python
manifest.add_output("tmdb_data", metadata_dir / "tmdb_data.json", "TMDB metadata")
manifest.add_metadata("tmdb_id", tmdb_id)
manifest.add_metadata("title", movie_title)
manifest.add_metadata("cast_count", len(cast))
```

### Stage 3: Pre-NER
```python
manifest.add_output("entities", entities_dir / "pre_ner.json", "Pre-ASR entities")
manifest.add_output("prompt", movie_dir / "initial_prompt.txt", "ASR initial prompt")
manifest.add_metadata("entity_count", len(entities))
```

### Stage 4: Silero VAD
```python
manifest.add_output("segments", vad_dir / "silero_segments.json", "Silero VAD segments")
manifest.add_metadata("segment_count", len(segments))
manifest.add_metadata("speech_percentage", speech_pct)
```

### Stage 5: PyAnnote VAD
```python
manifest.add_output("segments", vad_dir / "pyannote_segments.json", "PyAnnote VAD segments")
manifest.add_metadata("segment_count", len(segments))
manifest.add_metadata("refined_segments", refined_count)
```

### Stage 6: Diarization
```python
manifest.add_output("speakers", diar_dir / "speaker_segments.json", "Speaker segments")
manifest.add_metadata("speaker_count", num_speakers)
manifest.add_metadata("model", "pyannote/speaker-diarization")
```

### Stage 7: ASR
```python
manifest.add_output("transcript", trans_dir / "transcript.json", "WhisperX transcript")
manifest.add_metadata("word_count", len(words))
manifest.add_metadata("model", model_name)
manifest.add_metadata("language", language)
```

### Stage 8: Post-NER
```python
manifest.add_output("entities", entities_dir / "post_ner.json", "Corrected entities")
manifest.add_metadata("corrections_made", correction_count)
manifest.add_metadata("entity_count", len(entities))
```

### Stage 9: Subtitle Generation
```python
manifest.add_output("subtitles", subs_dir / "subtitles.srt", "English subtitles")
manifest.add_metadata("subtitle_count", len(subtitles))
manifest.add_metadata("format", "srt")
```

### Stage 10: Mux
```python
manifest.add_output("final_video", movie_dir / "final_output.mp4", "Final video with subs")
manifest.add_metadata("subtitle_track", "eng")
manifest.add_metadata("codec", "mov_text")
```

---

## Graceful Exit Patterns

### Pattern 1: Using Context Manager
```python
with StageManifest("stage", movie_dir, logger) as manifest:
    # Work here
    manifest.add_output("file", path)
    # Automatic success on clean exit
    # Automatic failure on exception
```

### Pattern 2: Explicit Try/Except
```python
manifest = StageManifest("stage", movie_dir, logger)

try:
    # Work here
    manifest.add_output("file", path)
    manifest.save(status="success")
    sys.exit(0)
    
except KeyboardInterrupt:
    logger.warning("Interrupted by user")
    manifest.save(status="failed")
    sys.exit(130)
    
except Exception as e:
    logger.error(f"Failed: {e}")
    manifest.set_error(str(e))
    manifest.save(status="failed")
    sys.exit(1)
```

### Pattern 3: Return Codes
```python
manifest = StageManifest("stage", movie_dir, logger)

success = do_work()

if success:
    manifest.add_output("file", path)
    manifest.save(status="success")
    sys.exit(0)
else:
    manifest.set_error("Processing failed")
    manifest.save(status="failed")
    sys.exit(1)
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Failure |
| 2 | Invalid arguments |
| 130 | Interrupted (Ctrl+C) |

---

## Checking Stage Completion

### From Python
```python
from manifest import is_stage_completed, load_manifest

if is_stage_completed(movie_dir, "demux"):
    print("Demux already completed, skipping")
    sys.exit(0)

# Or load full manifest
manifest_data = load_manifest(movie_dir)
if manifest_data:
    completed = manifest_data["pipeline"]["completed_stages"]
    print(f"Completed stages: {completed}")
```

### From Shell
```bash
MANIFEST="out/Movie_Title/manifest.json"

if jq -e '.pipeline.completed_stages | contains(["demux"])' "$MANIFEST" > /dev/null 2>&1; then
    echo "Demux already completed"
fi
```

---

## Pipeline Orchestrator Integration

The orchestrator (`pipeline.py`) uses `PipelineManifest` to:
- Check which stages are completed
- Resume from last successful stage
- Track overall pipeline status

```python
from manifest import PipelineManifest

manifest = PipelineManifest(movie_dir / "manifest.json")
manifest.set_input(input_file, title, year)

for stage in stages:
    if manifest.is_stage_completed(stage):
        logger.info(f"Skipping {stage} - already completed")
        continue
    
    run_stage(stage)

manifest.finalize(status="completed")
```

---

## Benefits

1. **Resume Capability**: Pipeline can resume from last successful stage
2. **Audit Trail**: Complete record of what ran when
3. **Output Tracking**: Know exactly what files were created
4. **Error Tracking**: Detailed error messages for debugging
5. **Progress Monitoring**: See which stage is currently running
6. **Validation**: Verify all expected outputs exist

---

## Validation

After each stage runs, the manifest contains:
- ✅ Stage status (success/failed)
- ✅ Start and end timestamps
- ✅ Duration in seconds
- ✅ All output files with full paths
- ✅ File existence verification
- ✅ File sizes
- ✅ Stage-specific metadata
- ✅ Error details (if failed)

---

## Example: Complete Manifest After 3 Stages

```json
{
  "version": "1.0.0",
  "created_at": "2024-10-29T20:00:00",
  "updated_at": "2024-10-29T20:05:30",
  "movie_dir": "/app/out/Inception_2010",
  "stages": {
    "demux": {
      "status": "success",
      "started_at": "2024-10-29T20:00:00",
      "completed_at": "2024-10-29T20:01:30",
      "duration_seconds": 90.5,
      "outputs": {
        "audio": {
          "path": "/app/out/Inception_2010/audio/audio.wav",
          "exists": true,
          "size_bytes": 52428800,
          "description": "16kHz mono audio"
        }
      },
      "metadata": {
        "sample_rate": 16000,
        "channels": 1
      }
    },
    "tmdb": {
      "status": "success",
      "started_at": "2024-10-29T20:01:30",
      "completed_at": "2024-10-29T20:02:00",
      "duration_seconds": 30.0,
      "outputs": {
        "tmdb_data": {
          "path": "/app/out/Inception_2010/metadata/tmdb_data.json",
          "exists": true,
          "size_bytes": 4096
        }
      },
      "metadata": {
        "tmdb_id": 27205,
        "title": "Inception",
        "cast_count": 50
      }
    },
    "pre_ner": {
      "status": "success",
      "started_at": "2024-10-29T20:02:00",
      "completed_at": "2024-10-29T20:05:30",
      "duration_seconds": 210.0,
      "outputs": {
        "entities": {
          "path": "/app/out/Inception_2010/entities/pre_ner.json",
          "exists": true,
          "size_bytes": 2048
        }
      },
      "metadata": {
        "entity_count": 150
      }
    }
  },
  "pipeline": {
    "status": "running",
    "current_stage": "silero_vad",
    "completed_stages": ["demux", "tmdb", "pre_ner"],
    "failed_stages": []
  }
}
```

---

## Testing Manifest Tracking

```bash
# Run a single stage
docker compose run --rm demux in/movie.mp4

# Check manifest
cat out/Movie_Title/manifest.json | jq '.stages.demux'

# Verify outputs exist
cat out/Movie_Title/manifest.json | jq '.stages.demux.outputs'

# Check completion status
cat out/Movie_Title/manifest.json | jq '.pipeline.completed_stages'
```

---

**✅ All stages now track execution in manifest.json with graceful exit handling!**
