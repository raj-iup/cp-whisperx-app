# Subtitle Generation Fix - Context-Aware Transcription

## Problem
The generated subtitle file `Jaane_Tu_Ya_Jaane_Na.merged.srt` was missing dialogues and was not context-aware. The transcription was not utilizing the assembled prompts and bias terms (character names, places, etc.) that were being prepared.

## Root Causes

### 1. Class Name Mismatch
The pipeline code referenced `Canonicalizer` class, but the actual canonicalization module uses `CanonicalProcessor` class with different constructor parameters.

### 2. Missing Context in Transcription
The WhisperX transcription was not using:
- **Initial prompts** - Prepared context about the movie, characters, and era
- **Hotwords/Bias terms** - Character names, places, and important terms from TMDB and era lexicons

The inline ASR script had a comment stating "FasterWhisperPipeline doesn't support initial_prompt directly" and didn't pass any context to the transcription.

## Solution

### Fix 1: Correct Class Names
Updated `run_pipeline.py` to use the correct class and parameter names:
- Changed `Canonicalizer` → `CanonicalProcessor`
- Changed `canon_map_path` parameter → `canon_map_file` parameter

### Fix 2: Enable Context-Aware Transcription
Modified the ASR script generation in `run_pipeline.py` to:

1. **Pass initial_prompt via asr_options**: WhisperX's `load_model()` accepts `asr_options` dict that can include `initial_prompt`, which gets passed to the underlying faster-whisper model.

2. **Add hotwords from bias terms**: Collected all unique bias terms from bias windows and passed them as comma-separated `hotwords` in `asr_options`. This helps the model recognize character names, places, and other important terms.

The updated code:
```python
# Prepare ASR options with initial_prompt and hotwords
asr_options = {}
if task.get('initial_prompt'):
    asr_options['initial_prompt'] = task['initial_prompt']
    
if task.get('has_bias_windows'):
    # Collect all bias terms and pass as hotwords
    all_bias_terms = set()
    for window_file in sorted(bias_dir.glob('bias.window.*.json')):
        with open(window_file) as f:
            w = json.load(f)
            all_bias_terms.update(w.get('bias_terms', []))
    if all_bias_terms:
        hotwords = ', '.join(sorted(all_bias_terms)[:50])
        asr_options['hotwords'] = hotwords

# Load model with context options
model = whisperx.load_model(
    task['model_name'],
    device=task['device'],
    compute_type=task['compute_type'],
    vad_method='silero',
    asr_options=asr_options if asr_options else None
)
```

## Benefits

1. **Better transcription accuracy**: The model now has context about character names, places, and the movie's setting
2. **Proper name recognition**: Hotwords help correctly transcribe character and place names instead of phonetic guesses
3. **Context-aware output**: Initial prompts provide background that improves translation quality
4. **Working subtitle generation**: Fixed class names allow the NER and canonicalization pipeline to work correctly

## How to Test

Run the pipeline again with the same input:
```bash
python3 run_pipeline.py -i in/Jaane_Tu_Ya_Jaane_Na_2008_Hindi_1080p_BluRay_x264_AAC5.1_ESub_-_mkvCinemas.mkv
```

The generated subtitles should now:
- Include all dialogues (not missing content)
- Use correct character names
- Show better context awareness in translations
- Have proper formatting from the canonicalization pipeline

## Technical Details

- **WhisperX version**: Uses FasterWhisperPipeline wrapper around faster-whisper
- **faster-whisper support**: The underlying model supports `initial_prompt` and `hotwords` parameters
- **WhisperX integration**: Parameters must be passed via `asr_options` dict to `load_model()`
- **Hotwords format**: Comma-separated string of important terms (limited to top 50 to avoid overload)
