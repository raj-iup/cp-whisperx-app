# Remaining Pipeline Stages - Fix Patterns

**Date**: 2025-11-08  
**Status**: Pattern established, ready to apply to remaining stages

---

## ASR Stage Pattern (Completed ✅)

The ASR stage fixes establish the pattern for all remaining stages:

1. ✅ Read parameters from job config (`.env` file)
2. ✅ Log configuration clearly
3. ✅ Use outputs from previous stages correctly
4. ✅ Suppress unnecessary warnings
5. ✅ Handle errors gracefully
6. ✅ Log processing results

---

## Remaining Stages to Fix

### Stage 8: Second Pass Translation

**Current Status**: Not yet implemented in your pipeline  
**Purpose**: Improve translation quality using context

**Fixes Needed**:
```python
# Read from config
source_lang = config.get('whisper_language', 'hi')
target_lang = config.get('target_language', 'en')
model_name = config.get('translation_model', 'facebook/mbart-large-50-many-to-many-mmt')

# Use ASR output
asr_file = movie_dir / "asr" / f"{movie_dir.name}.transcript.json"
with open(asr_file) as f:
    transcript = json.load(f)

# Log configuration
logger.info(f"Translation config: {source_lang} → {target_lang}")
logger.info(f"Model: {model_name}")
logger.info(f"Segments to translate: {len(transcript['segments'])}")
```

---

### Stage 9: Lyrics Detection

**Current Status**: Not yet implemented  
**Purpose**: Detect song/musical sequences in audio

**Fixes Needed**:
```python
# Read from config
lyrics_threshold = config.get('lyrics_detection_threshold', 0.7)
min_lyrics_duration = config.get('lyrics_min_duration', 10.0)

# Use ASR + audio features
asr_file = movie_dir / "asr" / f"{movie_dir.name}.transcript.json"
audio_file = movie_dir / "audio" / "audio.wav"

# Log configuration
logger.info(f"Lyrics detection threshold: {lyrics_threshold}")
logger.info(f"Minimum duration: {min_lyrics_duration}s")

# Detect and mark lyrics segments
lyrics_segments = detect_lyrics(audio_file, transcript, threshold=lyrics_threshold)
logger.info(f"[OK] Detected {len(lyrics_segments)} lyrics segments")
```

---

### Stage 10: Post-NER

**Current Status**: Partially implemented  
**Purpose**: Correct entity names in transcription

**Fixes Needed**:
```python
# Read from config
confidence_threshold = config.get('post_ner_confidence', 0.8)
max_corrections = config.get('post_ner_max_corrections', 100)

# Use pre_ner entities and ASR transcript
pre_ner_file = movie_dir / "entities" / "pre_ner.json"
asr_file = movie_dir / "asr" / f"{movie_dir.name}.transcript.json"

with open(pre_ner_file) as f:
    entities = json.load(f)
with open(asr_file) as f:
    transcript = json.load(f)

# Log configuration
logger.info(f"Entity correction config:")
logger.info(f"  Confidence threshold: {confidence_threshold}")
logger.info(f"  Available entities: {len(entities)}")
logger.info(f"  Character names: {len(entities.get('PERSON', []))}")
logger.info(f"  Locations: {len(entities.get('GPE', []))}")

# Apply corrections
corrected_segments = apply_entity_corrections(transcript, entities)
logger.info(f"[OK] Applied {len(corrected_segments)} corrections")
```

---

### Stage 11: Subtitle Generation

**Current Status**: Implemented  
**Purpose**: Generate .srt subtitle files

**Fixes Needed**:
```python
# Read from config
max_chars_per_line = config.get('subtitle_max_chars_per_line', 42)
max_lines = config.get('subtitle_max_lines', 2)
min_duration = config.get('subtitle_min_duration', 1.0)
max_duration = config.get('subtitle_max_duration', 7.0)

# Use all previous outputs
asr_file = movie_dir / "asr" / f"{movie_dir.name}.transcript.json"
lyrics_file = movie_dir / "lyrics" / f"{movie_dir.name}.lyrics_segments.json"
post_ner_file = movie_dir / "entities" / "post_ner.json"

# Log configuration
logger.info(f"Subtitle formatting:")
logger.info(f"  Max chars/line: {max_chars_per_line}")
logger.info(f"  Max lines: {max_lines}")
logger.info(f"  Duration: {min_duration}s - {max_duration}s")

# Generate subtitles
subtitles = generate_srt(transcript, lyrics_segments, entities)
logger.info(f"[OK] Generated {len(subtitles)} subtitle entries")
```

---

### Stage 12: Mux

**Current Status**: Implemented  
**Purpose**: Embed subtitles in video

**Fixes Needed**:
```python
# Read from config
output_format = config.get('mux_output_format', 'mp4')
video_codec = config.get('mux_video_codec', 'copy')
audio_codec = config.get('mux_audio_codec', 'copy')
subtitle_codec = config.get('mux_subtitle_codec', 'mov_text')

# Use input video and generated subtitle
input_video = movie_dir.parent.parent.parent.parent / "in" / f"{movie_dir.name}.mp4"
subtitle_file = movie_dir / "subtitles" / "subtitles.srt"
output_file = movie_dir / "final_output.mp4"

# Log configuration
logger.info(f"Muxing configuration:")
logger.info(f"  Input: {input_video}")
logger.info(f"  Subtitles: {subtitle_file}")
logger.info(f"  Output: {output_file}")
logger.info(f"  Format: {output_format}")

# Mux video
mux_video_with_subtitles(input_video, subtitle_file, output_file)
logger.info(f"[OK] Muxed video created: {output_file}")
```

---

## Common Pattern for All Stages

### 1. Configuration Reading

```python
def main():
    # Load config
    from config import load_config
    config = load_config()
    
    # Read all relevant parameters
    param1 = config.get('stage_param1', default_value)
    param2 = config.get('stage_param2', default_value)
    
    # Log configuration
    logger.info(f"Configuration:")
    logger.info(f"  Parameter 1: {param1}")
    logger.info(f"  Parameter 2: {param2}")
```

### 2. Input Validation

```python
    # Check required inputs exist
    input_file = movie_dir / "previous_stage" / "output.json"
    if not input_file.exists():
        logger.error(f"Required input not found: {input_file}")
        logger.error("Previous stage may have failed")
        sys.exit(1)
    
    logger.info(f"Input file: {input_file}")
```

### 3. Processing with Progress

```python
    # Process with clear logging
    logger.info(f"Starting {stage_name}...")
    
    results = process_data(input_data, config)
    
    logger.info(f"[OK] Processing complete")
    logger.info(f"[OK] Generated {len(results)} outputs")
```

### 4. Output Generation

```python
    # Save results
    output_dir = movie_dir / "stage_output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"{movie_dir.name}.output.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"[OK] Results saved: {output_file}")
```

### 5. Error Handling

```python
    try:
        # Main processing
        results = process_stage(inputs, config)
    except Exception as e:
        logger.error(f"{stage_name} failed: {e}")
        logger.error(f"Traceback: ", exc_info=True)
        sys.exit(1)
```

---

## Stage Dependencies

Understanding what each stage needs:

```
Stage 8 (Second Pass Translation)
  Inputs: Stage 7 (ASR transcript)
  Config: translation_model, source_lang, target_lang
  
Stage 9 (Lyrics Detection)
  Inputs: Stage 7 (ASR), audio file
  Config: lyrics_threshold, min_duration
  
Stage 10 (Post-NER)
  Inputs: Stage 3 (pre_ner entities), Stage 7 (ASR)
  Config: confidence_threshold, max_corrections
  
Stage 11 (Subtitle Generation)
  Inputs: Stage 7 (ASR), Stage 9 (lyrics), Stage 10 (post_ner)
  Config: max_chars, max_lines, duration limits
  
Stage 12 (Mux)
  Inputs: Original video, Stage 11 (subtitles)
  Config: codecs, output format
```

---

## Implementation Priority

1. **ASR** ✅ - COMPLETE (critical path blocker)
2. **Second Pass Translation** - Enhance translation quality
3. **Lyrics Detection** - Mark musical sequences
4. **Post-NER** - Improve entity accuracy
5. **Subtitle Generation** - Format final output
6. **Mux** - Create final video

---

## Testing Strategy

For each stage:

```bash
# 1. Run stage independently
.bollyenv/bin/python docker/stage/stage_script.py out/YYYY/MM/DD/USER_ID/JOB_ID

# 2. Check output
cat out/YYYY/MM/DD/USER_ID/JOB_ID/stage_output/*.json

# 3. Check logs
grep -i error out/YYYY/MM/DD/USER_ID/JOB_ID/logs/*_stage_*.log

# 4. Resume full pipeline
./resume-pipeline.sh JOB_ID
```

---

## Configuration Documentation

Each stage should document its configuration in README or stage-specific docs:

```markdown
## Stage X Configuration

### Required Parameters
- `PARAM1`: Description (default: value)
- `PARAM2`: Description (default: value)

### Optional Parameters
- `PARAM3`: Description (default: value)

### Inputs
- Path to input file from previous stage
- Format: JSON/TXT/etc

### Outputs
- Path to output file
- Format: JSON/TXT/etc

### Example Configuration
```
PARAM1=value1
PARAM2=value2
```

---

## Summary

**Pattern Established**: ✅  
**ASR Stage Fixed**: ✅  
**Remaining Stages**: 5 (following same pattern)  
**Time to Implement**: ~2-4 hours for all stages  

**Next Action**: Apply pattern to Stage 8 (Second Pass Translation) when ASR completes successfully.

---

**Created**: 2025-11-08  
**Status**: Reference guide for remaining implementations
