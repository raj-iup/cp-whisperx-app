# WhisperX Context-Aware Translation Comparison

## Overview

WhisperX large-v3 has built-in translation capability that provides **context-aware** translation directly from the audio signal, unlike post-transcription translation methods (NLLB, IndICTrans2, Google Translate) that only work with text.

## Why WhisperX Translation is Different

### Context-Aware Advantages:
1. **Audio Context**: Sees prosody, tone, emphasis in the original speech
2. **Timing-Aware**: Uses speech patterns and pauses for better understanding
3. **Single-Pass**: Transcribes and translates simultaneously
4. **large-v3 Model**: Latest Whisper model with improved multilingual support
5. **Hinglish-Aware**: Can better handle code-switching with audio cues

### Comparison with Other Methods:

| Method | Type | Context | Hinglish Handling |
|--------|------|---------|-------------------|
| **WhisperX** | Audio → English | Audio signal + text | Best - uses audio cues |
| **IndICTrans2** | Hindi text → English | Text only | Good - Indic specialist |
| **NLLB** | Hindi text → English | Text only | Good - general purpose |
| **Google Translate** | Hindi text → English | Text only | Fair - general purpose |

## Manual Generation (Current Approach)

Due to environment dependencies, WhisperX translation is best generated manually using the existing pipeline with modified settings.

### Method 1: Use ASR Stage with Translation Task

```bash
# In job.json, temporarily modify for translation:
{
  "source_language": "hi",
  "target_languages": ["en"],
  "asr_settings": {
    "task": "translate",  # Changed from "transcribe"
    "model": "large-v3"
  }
}

# Run just the ASR stage
cd /Users/rpatel/Projects/cp-whisperx-app
python scripts/run-pipeline.py out/2025/11/23/rpatel/4 --stage asr

# This will create English transcription directly from audio
```

### Method 2: Direct WhisperX Call

```bash
# Activate WhisperX environment
source venv/whisperx/bin/activate

# Run WhisperX CLI with translate task
whisperx audio.wav \
  --model large-v3 \
  --language hi \
  --task translate \
  --output_dir transcripts/ \
  --output_format json

# Convert to SRT
python scripts/subtitle_gen.py \
  transcripts/audio.json \
  -o subtitles/movie.en.whisperx.srt
```

### Method 3: Python Script

```python
import whisperx
import json

# Load model
device = "mps"  # or "cuda" or "cpu"
model = whisperx.load_model("large-v3", device, compute_type="float16")

# Load audio
audio = whisperx.load_audio("audio.wav")

# Transcribe with translation
result = model.transcribe(
    audio,
    language="hi",
    task="translate",  # Key parameter
    batch_size=16
)

# Align
model_a, metadata = whisperx.load_align_model(language_code="en", device=device)
result = whisperx.align(result["segments"], model_a, metadata, audio, device)

# Save
with open("segments_whisperx_translated.json", "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
```

## Automated Script (Future Enhancement)

The `whisperx_translate_comparator.py` script is included but requires:
- Proper environment setup
- All dependencies in WhisperX environment
- Module path fixes

To make it work:

1. Install missing dependencies in WhisperX environment:
```bash
source venv/whisperx/bin/activate
pip install python-json-logger
```

2. Run comparator:
```bash
python scripts/whisperx_translate_comparator.py out/2025/11/23/rpatel/4 -v
```

## Expected Output

When working, creates:
- `transcripts/segments_whisperx_translated.json` - Translated segments
- `subtitles/<title>.en.whisperx.srt` - WhisperX translation

## Comparison Analysis

Once you have all translations, compare:

```bash
# View all English translations
ls -lh out/.../subtitles/*.en*.srt

# Side-by-side comparison
diff -y movie.en.srt movie.en.whisperx.srt
diff -y movie.en.indictrans2.srt movie.en.whisperx.srt

# Word count comparison
for file in *.en*.srt; do
  echo "$file: $(wc -w < "$file") words"
done
```

## Benefits of WhisperX Translation

1. **Better Context Understanding**
   - Understands emphasis and tone
   - Better handling of ambiguous phrases
   - More natural English output

2. **Hinglish Code-Switching**
   - Audio cues help identify language boundaries
   - Better preservation of meaning in mixed language
   - More accurate treatment of English words in Hindi speech

3. **Timing Accuracy**
   - Translation aligned with original speech timing
   - Better subtitle synchronization
   - Natural pacing

## Limitations

1. **Model Constraints**
   - Limited to languages Whisper supports
   - May not preserve cultural nuances
   - General purpose vs. specialist (IndICTrans2)

2. **Resource Requirements**
   - Requires GPU/MPS for reasonable speed
   - Larger model size (large-v3)
   - More memory intensive

3. **Less Control**
   - Cannot use custom glossaries easily
   - Fixed translation approach
   - Less post-processing flexibility

## Recommended Workflow

For best results, generate **all** translations and compare:

1. **WhisperX** - Best for natural speech, audio context
2. **IndICTrans2** - Best for formal Hindi, Indic languages
3. **NLLB** - Good baseline, general purpose
4. **Google Translate** - Quick comparison reference

Then manually review and select best segments from each.

## Future Enhancements

- [ ] Fix environment dependencies in automated script
- [ ] Add batch processing for multiple jobs
- [ ] Create comparison report generator
- [ ] Integrate into pipeline as optional stage
- [ ] Add quality metrics (BLEU, etc.)

## See Also

- [Hinglish Detection](./HINGLISH_DETECTION.md)
- [Translation Configuration](./TRANSLATION.md)
- [WhisperX Documentation](https://github.com/m-bain/whisperX)
