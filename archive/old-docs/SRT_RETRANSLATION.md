# SRT Re-translation Fix for WhisperX Hallucinations

## Problem

WhisperX's built-in translation feature can sometimes produce hallucinated or incomplete translations, especially with Hinglish content. Common issues include:

- **Missing dialogue segments**: Important dialogue is completely missing from the translation
- **Hallucinated repetitions**: The model generates repeated words (e.g., "Okay" repeated 10+ times)
- **Segment misalignment**: Translation segments don't match the source timing

### Example Issue

**Source (Hinglish)**:
```
43
00:07:55,103 --> 00:07:56,545
तो माला, क्या होता है न?

44
00:07:56,564 --> 00:08:05,935
एक टाइम, एक गर्ज, और एक बॉय, दोनों मूस, दोनों... कहानी शुरू होती है एक सपने से.
```

**WhisperX Translation (INCORRECT)**:
```
103
00:07:55,163 --> 00:07:55,502
Okay.

104
00:07:55,843 --> 00:07:56,264
Okay.

... (10+ more "Okay" repetitions) ...
```

**Re-translation (CORRECT)**:
```
43
00:07:55,103 --> 00:07:56,545
So Mala, what happens?

44
00:07:56,564 --> 00:08:05,935
A time, a thunder, and a boy, both moose, both... the story starts with a dream.
```

## Solution

We've created a re-translation tool that uses Google Translate API (via `deep-translator`) to re-translate the Hinglish SRT files to English. This provides more accurate and complete translations.

## Installation

The translation library is automatically installed when you run the retranslation script, but you can manually install it:

```bash
# Activate virtual environment
source .bollyenv/bin/activate

# Install translation library
pip install deep-translator
```

## Usage

### Quick Start (Recommended)

Use the convenience wrapper script:

```bash
# Linux/macOS
./retranslate-subtitles.sh out/2025/11/16/1/20251116-0002

# Windows PowerShell
.\retranslate-subtitles.ps1 out\2025\11\16\1\20251116-0002
```

This will:
1. Find the Hinglish SRT file in the job's `06_asr` directory
2. Create a backup of the original WhisperX translation (if it exists)
3. Generate a new English translation: `{basename}-English-Retranslated.srt`
4. Show file size comparison and instructions for replacement

### Manual Usage

Use the Python script directly for more control:

```bash
# Basic usage
python scripts/retranslate_srt.py input.srt -o output-English.srt

# Specify translation method
python scripts/retranslate_srt.py input.srt -o output.srt --method deep-translator

# Specify languages
python scripts/retranslate_srt.py input.srt -o output.srt --src-lang hi --dest-lang en

# With logging
python scripts/retranslate_srt.py input.srt -o output.srt --log translation.log
```

### Translation Methods

The script supports multiple translation backends:

| Method | Description | Notes |
|--------|-------------|-------|
| `deep-translator` | Google Translate API wrapper | **Recommended** - Most reliable |
| `googletrans` | Free Google Translate API | May have rate limits |
| `argostranslate` | Offline translation | Requires model download |
| `auto` | Auto-detect best method | Default |

## Workflow Integration

### Option 1: Manual Re-translation After Pipeline

Run the pipeline normally, then re-translate:

```bash
# Run pipeline
./run_pipeline.sh

# Re-translate afterwards
./retranslate-subtitles.sh out/2025/11/16/1/20251116-0002
```

### Option 2: Replace WhisperX Translation

To use the re-translated version as the primary English translation:

```bash
# After re-translation completes
cp out/.../06_asr/20251116-0002-English-Retranslated.srt \
   out/.../06_asr/20251116-0002-English.srt
```

The backup is saved as `*-English.srt.backup`.

## Performance

- **Translation time**: ~200-400 subtitles per minute (with rate limiting)
- **File size**: Retranslated files are typically smaller due to removal of hallucinated segments
- **Accuracy**: Significantly improved for Hinglish dialogue and mixed-language content

### Example

For a 2026 subtitle file:
- Time: ~5 minutes
- Original: 157 KB (with hallucinations)
- Retranslated: 87 KB (cleaned)

## Troubleshooting

### Rate Limiting

If you encounter rate limiting errors:

```python
# In scripts/retranslate_srt.py, increase the delay
time.sleep(0.2)  # Increase from 0.1 to 0.2
```

### Installation Issues

If `deep-translator` fails to install:

```bash
# Try alternative methods
pip install googletrans==4.0.0-rc1
# or
pip install argostranslate
```

### Unicode/Encoding Issues

The script handles UTF-8 encoding automatically. If you encounter issues:

```bash
# Check file encoding
file -I input.srt

# Convert if needed
iconv -f ISO-8859-1 -t UTF-8 input.srt > input_utf8.srt
```

## When to Use Re-translation

Use re-translation when you notice:

- ✓ Repeated words or phrases in English translation
- ✓ Missing dialogue that exists in the Hinglish source
- ✓ English translation has significantly more or fewer segments than source
- ✓ Dialogue that doesn't make sense or is out of context

## Comparison with WhisperX Translation

| Aspect | WhisperX Translation | Re-translation |
|--------|---------------------|----------------|
| Speed | Fast (single-pass) | Slower (sequential API calls) |
| Accuracy | Variable, prone to hallucinations | More consistent |
| Segment alignment | Can drift | Maintains exact alignment |
| Mixed languages | May struggle | Handles well |
| Long dialogues | Can lose context | Translates independently |

## Future Improvements

Potential enhancements:

1. **Batch translation**: Translate multiple segments at once to improve speed
2. **Context-aware translation**: Use previous segments as context
3. **Custom glossary integration**: Apply character names and terminology
4. **Parallel processing**: Multi-threaded translation for large files
5. **Alternative APIs**: Support for DeepL, Azure Translator, etc.

## Files

- `scripts/retranslate_srt.py` - Core re-translation script
- `retranslate-subtitles.sh` - Bash wrapper for easy usage
- `retranslate-subtitles.ps1` - PowerShell wrapper for Windows

## See Also

- [TRANSCRIBE_MODE_ENHANCEMENTS.md](TRANSCRIBE_MODE_ENHANCEMENTS.md) - Pipeline workflow modes
- [TWO_STEP_TRANSCRIPTION.md](TWO_STEP_TRANSCRIPTION.md) - Two-step transcription approach
- [QUICK_REFERENCE_TWO_STEP.md](QUICK_REFERENCE_TWO_STEP.md) - Quick reference guide
