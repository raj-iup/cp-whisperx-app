# Configuration Quick Reference

Quick lookup guide for common configuration tasks in `.env.pipeline`.

## Common Configuration Changes

### Change Log Level
```bash
# Standard logging
LOG_LEVEL=INFO

# Verbose debugging
LOG_LEVEL=DEBUG

# Quiet mode (errors only)
LOG_LEVEL=ERROR
```

### Change Device
```bash
# Auto-detected (recommended)
DEVICE=mps              # Apple Silicon
DEVICE=cuda             # NVIDIA GPU
DEVICE=cpu              # CPU fallback

# Override for specific stages
WHISPERX_DEVICE=cpu     # Force CPU for ASR
DIARIZATION_DEVICE=mps  # Use GPU for diarization
```

### Adjust ASR Quality
```bash
# Model size (accuracy vs speed)
WHISPER_MODEL=large-v3  # Best quality (default)
WHISPER_MODEL=medium    # Faster, good quality
WHISPER_MODEL=small     # Fast, lower quality

# Beam search (quality vs speed)
WHISPER_BEAM_SIZE=5     # Balanced (default)
WHISPER_BEAM_SIZE=10    # Higher quality, slower
WHISPER_BEAM_SIZE=1     # Fastest, lower quality
```

### Configure Subtitle Formatting
```bash
# Line length
SUBTITLE_MAX_LINE_LENGTH=42  # Standard (default)
SUBTITLE_MAX_LINE_LENGTH=35  # Shorter for dense text
SUBTITLE_MAX_LINE_LENGTH=50  # Longer for simple text

# Reading speed (CPS = Characters Per Second)
CPS_TARGET=15.0         # Standard reading speed
CPS_TARGET=13.0         # Slower (easier to read)
CPS_TARGET=17.0         # Faster (advanced readers)

# Duration limits
SUBTITLE_MAX_DURATION=7.0    # Max display time
SUBTITLE_MIN_DURATION=1.0    # Min display time
```

### Enable/Disable Features
```bash
# Vocal extraction (improves accuracy for songs)
SOURCE_SEPARATION_ENABLED=true   # Enable (default)
SOURCE_SEPARATION_ENABLED=false  # Disable (faster)

# Speaker identification
STEP_DIARIZATION=true   # Enable speaker labels
STEP_DIARIZATION=false  # Disable (faster)

# LLM for song translation
USE_LLM_FOR_SONGS=true  # Use LLM for creative translation
USE_LLM_FOR_SONGS=false # Use IndicTrans2 for all (free)

# Hinglish glossary
GLOSSARY_ENABLED=true   # Preserve Hinglish terms
GLOSSARY_ENABLED=false  # Translate everything
```

## Parameter Lookup by Use Case

### Quality Over Speed
```bash
WHISPER_MODEL=large-v3
WHISPER_BEAM_SIZE=10
SOURCE_SEPARATION_QUALITY=quality
INDICTRANS2_NUM_BEAMS=6
STEP_DIARIZATION=true
STEP_VAD_PYANNOTE=true
```

### Speed Over Quality
```bash
WHISPER_MODEL=medium
WHISPER_BEAM_SIZE=1
SOURCE_SEPARATION_ENABLED=false
INDICTRANS2_NUM_BEAMS=1
STEP_DIARIZATION=false
STEP_VAD_PYANNOTE=false
```

### Low Memory Usage
```bash
WHISPER_MODEL=small
BATCH_SIZE=1
WHISPER_COMPUTE_TYPE=int8
DIARIZATION_MAX_SPEAKERS=5
```

### Best Name Recognition
```bash
TMDB_ENABLED=true
BIAS_ENABLED=true
BIAS_TOPK=15
BIAS_WINDOW_SECONDS=30
PRE_NER_MODEL=en_core_web_trf
POST_NER_ENTITY_CORRECTION=true
```

## Quick Diagnostics

### Pipeline is too slow?
Check these settings:
```bash
WHISPER_MODEL=           # Try smaller model
WHISPER_BEAM_SIZE=       # Reduce beam size
SOURCE_SEPARATION_ENABLED=  # Consider disabling
STEP_DIARIZATION=        # Consider disabling
BATCH_SIZE=              # Try increasing (if memory allows)
```

### Poor transcription accuracy?
Check these settings:
```bash
WHISPER_MODEL=large-v3   # Use best model
SOURCE_SEPARATION_ENABLED=true  # Enable vocal extraction
BIAS_ENABLED=true        # Enable name/term hints
TMDB_ENABLED=true        # Fetch metadata for context
SILERO_THRESHOLD=        # Adjust sensitivity
```

### Subtitles too fast/slow to read?
```bash
CPS_TARGET=15.0          # Adjust reading speed
CPS_HARD_CAP=17.0        # Set maximum speed
SUBTITLE_MAX_DURATION=   # Adjust max display time
```

### Running out of memory?
```bash
BATCH_SIZE=1             # Reduce batch size
WHISPER_MODEL=medium     # Use smaller model
WHISPER_COMPUTE_TYPE=int8  # Use 8-bit precision
DEVICE=cpu               # Force CPU (slower but more stable)
```

## Stage-Specific Quick Reference

### Stage 1: DEMUX (Audio Extraction)
```bash
AUDIO_SAMPLE_RATE=16000  # Must be 16000 for Whisper
AUDIO_CHANNELS=1         # Must be 1 (mono) for VAD
```

### Stage 5-6: VAD (Voice Detection)
```bash
# Silero (fast)
SILERO_THRESHOLD=0.5     # Sensitivity (0.3-0.7)
SILERO_MERGE_GAP_SEC=0.35  # Merge nearby segments

# PyAnnote (precise)
PYANNOTE_ONSET=0.5       # Speech start threshold
PYANNOTE_OFFSET=0.5      # Speech end threshold
```

### Stage 7: ASR (Speech Recognition)
```bash
WHISPER_MODEL=large-v3
WHISPER_LANGUAGE=hi      # Source language
TARGET_LANGUAGE=en       # Translation target
WHISPER_TASK=translate   # or 'transcribe'
```

### Stage 8: Diarization (Speaker ID)
```bash
DIARIZATION_MIN_SPEAKERS=1   # Expected min speakers
DIARIZATION_MAX_SPEAKERS=15  # Expected max speakers
```

### Stage 9: Translation
```bash
INDICTRANS2_NUM_BEAMS=4      # Quality (1-10)
SECOND_PASS_ENABLED=true     # Refinement pass
USE_HYBRID_TRANSLATION=true  # LLM for songs
```

### Stage 12: Subtitle Generation
```bash
SUBTITLE_FORMAT=srt
SUBTITLE_MAX_LINE_LENGTH=42
SUBTITLE_MAX_LINES=2
CPS_TARGET=15.0
```

## Environment-Specific Defaults

### Apple Silicon (M1/M2/M3/M4)
```bash
DEVICE=mps
WHISPER_BACKEND=mlx         # Fast, native GPU
PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
```

### NVIDIA GPU
```bash
DEVICE=cuda
WHISPER_BACKEND=whisperx    # Bias support
```

### CPU Only
```bash
DEVICE=cpu
WHISPER_MODEL=medium        # Smaller model recommended
BATCH_SIZE=1                # Reduce memory usage
```

## Related Documentation

- [Full Configuration](../config/.env.pipeline)
- [Developer Guidelines](CONFIGURATION_GUIDELINES.md)
- [Cleanup Summary](CONFIG_CLEANUP_SUMMARY.md)
- [Pipeline Architecture](ARCHITECTURE.md)

---

**Last Updated:** 2025-11-25
