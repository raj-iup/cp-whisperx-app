# Pipeline Consolidation Complete

## Summary

Consolidated multiple pipeline files into a single canonical pipeline file.

## Changes Made

### Files Consolidated

1. **`pipeline.py`** (NEW - Main Pipeline)
   - Source: `run_pipeline_arch.py`
   - Architecture-compliant pipeline following `workflow-arch.txt`
   - Implements all 10 stages in correct order:
     1. FFmpeg Demux
     2. TMDB Metadata Fetch
     3. Pre-ASR NER
     4. Silero VAD
     5. PyAnnote VAD
     6. PyAnnote Diarization
     7. WhisperX ASR + Forced Alignment
     8. Post-ASR NER
     9. Subtitle Generation
     10. FFmpeg Mux

### Archived Files

- `pipeline.py.old` - Previous version
- `run_pipeline.py.old2` - Complex pipeline with bias injection
- `run_pipeline.py.backup` - Backup
- `run_pipeline.py.bak` - Backup

### Documentation Updated

- **QUICKSTART.md**: Updated all references from `run_pipeline_arch.py` to `pipeline.py`

## Usage

```bash
# Full pipeline with TMDB metadata
python3 pipeline.py -i "in/Movie_Name_2006.mp4" --infer-tmdb-from-filename

# With options
python3 pipeline.py -i "in/Movie_Name_2006.mp4" \
  --infer-tmdb-from-filename \
  --skip-vad \
  --skip-diarization
```

## Architecture Compliance

The consolidated `pipeline.py` strictly follows the container architecture defined in `workflow-arch.txt`:

✅ All 10 stages in correct order
✅ Each stage runs in its own Docker container
✅ Proper path mapping between host and container
✅ PyAnnote VAD is optional (with graceful fallback)
✅ PyAnnote Diarization is MANDATORY (per architecture)
✅ Comprehensive logging and manifest generation

## Benefits

1. **Single Source of Truth**: One main pipeline file
2. **Architecture Compliant**: Follows workflow-arch.txt exactly
3. **Container-based**: Each stage runs in isolated Docker container
4. **Maintainable**: Clear separation of concerns
5. **Documented**: Inline comments explain each stage

## Next Steps

If needed, archived pipeline files can be restored from:
- `pipeline.py.old`
- `run_pipeline.py.old2`

However, the new `pipeline.py` is the recommended and supported version.
