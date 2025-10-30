# Manifest Tracking Implementation - Update Plan

## Summary

Update all 10 pipeline stage containers to use `StageManifest` for tracking execution status, outputs, and graceful error handling.

---

## Implementation Status

### ✅ Completed
1. Created `shared/manifest.py` with `StageManifest` and `PipelineManifest` classes
2. Created documentation in `docs/MANIFEST_TRACKING.md`
3. Updated `docker/demux/demux.py` as reference implementation

### 🔧 To Update (9 containers)

| Stage | Script | Expected Outputs |
|-------|--------|------------------|
| tmdb | docker/tmdb/tmdb.py | tmdb_data.json |
| pre-ner | docker/pre-ner/pre_ner.py | pre_ner.json, initial_prompt.txt |
| silero-vad | docker/silero-vad/silero_vad.py | silero_segments.json |
| pyannote-vad | docker/pyannote-vad/pyannote_vad.py | pyannote_segments.json |
| diarization | docker/diarization/diarization.py | speaker_segments.json |
| asr | docker/asr/whisperx_asr.py | transcript.json |
| post-ner | docker/post-ner/post_ner.py | post_ner.json |
| subtitle-gen | docker/subtitle-gen/subtitle_gen.py | subtitles.srt |
| mux | docker/mux/mux.py | final_output.mp4 |

---

## Update Pattern

For each container:

### 1. Add manifest import
```python
from manifest import StageManifest
```

### 2. Wrap main logic in context manager
```python
def main():
    # ... setup code ...
    
    try:
        with StageManifest("stage_name", movie_dir, logger) as manifest:
            # ... existing stage logic ...
            
            # Add output recording
            manifest.add_output("key", output_file, "description")
            
            # Add metadata
            manifest.add_metadata("key", value)
            
            # Success on clean exit
    
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Stage failed: {e}")
        sys.exit(1)
    
    sys.exit(0)
```

### 3. Record all outputs
Each stage should call `manifest.add_output()` for every file it creates.

### 4. Record metadata
Call `manifest.add_metadata()` for important metrics (counts, versions, etc.).

---

## Stage-Specific Details

### TMDB (docker/tmdb/tmdb.py)
```python
# Outputs
manifest.add_output("tmdb_data", metadata_dir / "tmdb_data.json", "TMDB movie data")

# Metadata
manifest.add_metadata("tmdb_id", tmdb_id)
manifest.add_metadata("title", movie_title)
manifest.add_metadata("year", year)
manifest.add_metadata("cast_count", len(cast))
manifest.add_metadata("crew_count", len(crew))
```

### Pre-NER (docker/pre-ner/pre_ner.py)
```python
# Outputs
manifest.add_output("entities", entities_dir / "pre_ner.json", "Pre-ASR entities")
manifest.add_output("prompt", movie_dir / "initial_prompt.txt", "ASR initial prompt")

# Metadata
manifest.add_metadata("entity_count", len(entities))
manifest.add_metadata("person_count", person_count)
manifest.add_metadata("location_count", location_count)
```

### Silero VAD (docker/silero-vad/silero_vad.py)
```python
# Outputs
manifest.add_output("segments", vad_dir / "silero_segments.json", "Silero VAD segments")

# Metadata
manifest.add_metadata("segment_count", len(segments))
manifest.add_metadata("total_speech_seconds", speech_duration)
manifest.add_metadata("speech_percentage", speech_pct)
manifest.add_metadata("threshold", threshold)
```

### PyAnnote VAD (docker/pyannote-vad/pyannote_vad.py)
```python
# Outputs
manifest.add_output("segments", vad_dir / "pyannote_segments.json", "PyAnnote VAD segments")

# Metadata
manifest.add_metadata("segment_count", len(segments))
manifest.add_metadata("refined_count", refined_count)
manifest.add_metadata("model", "pyannote/voice-activity-detection")
```

### Diarization (docker/diarization/diarization.py)
```python
# Outputs
manifest.add_output("speakers", diarization_dir / "speaker_segments.json", "Speaker segments")

# Metadata
manifest.add_metadata("speaker_count", num_speakers)
manifest.add_metadata("model", "pyannote/speaker-diarization")
manifest.add_metadata("min_speakers", min_speakers)
manifest.add_metadata("max_speakers", max_speakers)
```

### ASR (docker/asr/whisperx_asr.py)
```python
# Outputs
manifest.add_output("transcript", transcription_dir / "transcript.json", "WhisperX transcript")

# Metadata
manifest.add_metadata("model", model_name)
manifest.add_metadata("language", source_language)
manifest.add_metadata("task", "translate")
manifest.add_metadata("word_count", word_count)
manifest.add_metadata("segment_count", len(segments))
```

### Post-NER (docker/post-ner/post_ner.py)
```python
# Outputs
manifest.add_output("entities", entities_dir / "post_ner.json", "Corrected entities")

# Metadata
manifest.add_metadata("corrections_made", correction_count)
manifest.add_metadata("entity_count", len(entities))
manifest.add_metadata("confidence_threshold", threshold)
```

### Subtitle Generation (docker/subtitle-gen/subtitle_gen.py)
```python
# Outputs
manifest.add_output("subtitles", subtitles_dir / "subtitles.srt", "English subtitles")

# Metadata
manifest.add_metadata("subtitle_count", len(subtitles))
manifest.add_metadata("format", "srt")
manifest.add_metadata("language", "en")
manifest.add_metadata("speaker_labels", True)
```

### Mux (docker/mux/mux.py)
```python
# Outputs
manifest.add_output("final_video", output_file, "Final video with subtitles")

# Metadata
manifest.add_metadata("input_video", str(input_file))
manifest.add_metadata("subtitle_track", "eng")
manifest.add_metadata("codec", "mov_text")
manifest.add_metadata("file_size_mb", output_file.stat().st_size / (1024*1024))
```

---

## Testing Checklist

For each updated container:

- [ ] Imports `StageManifest` from shared/manifest
- [ ] Uses context manager for graceful exit
- [ ] Records all output files with `add_output()`
- [ ] Records relevant metadata with `add_metadata()`
- [ ] Handles KeyboardInterrupt (exit code 130)
- [ ] Handles general exceptions (exit code 1)
- [ ] Exits with 0 on success
- [ ] Manifest file created/updated in movie_dir
- [ ] Can be run standalone without errors
- [ ] Can be run via docker compose
- [ ] Manifest contains correct stage status
- [ ] All output paths are absolute

---

## Validation Commands

After updating each container:

```bash
# Test container
docker compose run --rm <stage> <args>

# Check manifest
cat out/Movie_Title/manifest.json | jq '.stages.<stage>'

# Verify outputs
cat out/Movie_Title/manifest.json | jq '.stages.<stage>.outputs'

# Check status
cat out/Movie_Title/manifest.json | jq '.stages.<stage>.status'
```

---

## Priority Order

Recommended update order (based on dependencies):

1. ✅ demux (completed - reference implementation)
2. tmdb (depends on demux)
3. pre-ner (depends on tmdb)
4. silero-vad (depends on pre-ner)
5. pyannote-vad (depends on silero-vad)
6. diarization (depends on pyannote-vad)
7. asr (depends on diarization)
8. post-ner (depends on asr)
9. subtitle-gen (depends on post-ner)
10. mux (depends on subtitle-gen)

---

## Next Steps

1. Update remaining 9 containers following the pattern
2. Test each container individually
3. Run full pipeline end-to-end
4. Verify manifest.json completeness
5. Update pipeline.py to use manifest for resume
6. Document any stage-specific considerations

---

**Goal**: All 10 stages tracking execution with graceful exit and complete output recording.
