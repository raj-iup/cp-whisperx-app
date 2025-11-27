# Hinglish Word-Level Language Detection

## Overview

The pipeline now includes automatic word-level language detection for Hinglish (mixed Hindi-English) content. This feature analyzes subtitles and tags each word with its detected language (Hindi/Devanagari vs English/Latin), making it easier to:

- Identify code-switching patterns
- Validate transcription quality
- Compare translation approaches
- Understand language mixing in the content

## How It Works

### Pipeline Integration

The Hinglish detection runs automatically as part of the **subtitle workflow** when:

1. **Source language is Hindi** (`source_language: "hi"` in job.json)
2. **Feature is enabled** (enabled by default)
3. **After source subtitle generation** (runs before muxing)

### Stage Execution

```
Subtitle Workflow Pipeline:
├── load_transcript
├── indictrans2_translation_en (or other target languages)
├── subtitle_generation_en
├── subtitle_generation_source (creates Hindi .srt)
├── hinglish_detection ← NEW STAGE
└── mux
```

## Configuration

### Enable/Disable in job.json

The feature is **enabled by default** for Hindi source language. To disable:

```json
{
  "source_language": "hi",
  "target_languages": ["en"],
  "hinglish_detection": {
    "enabled": false
  }
}
```

### Enable for specific job

When preparing a job:

```bash
# Default: enabled automatically for Hindi
./prepare-job.sh -i input.mp4 -l hi -t en

# Explicitly disable
# (Edit job.json after preparation and add hinglish_detection.enabled: false)
```

## Output Files

When Hinglish detection runs, it creates two additional files in the subtitles directory:

### 1. Tagged SRT File
**Filename:** `<title>.<source_lang>.tagged.srt`

Example: `Jaane Tu Ya Jaane Na.hi.tagged.srt`

Contains the same subtitles with language tags on each word:

```srt
2
00:00:19,000 --> 00:00:23,600
[EN]Sorry[/EN] [HI]यह[/HI] [HI]हमारी[/HI] [HI]ग्रूप[/HI] [HI]के[/HI] [HI]लिए[/HI] [HI]बहुत[/HI] [EN]special[/EN] [HI]गान[/HI] [HI]है[/HI]
```

**Tag Legend:**
- `[HI]...[/HI]` - Hindi word (Devanagari script)
- `[EN]...[/EN]` - English word (Latin script)
- `[MIX]...[/MIX]` - Mixed script word (rare)
- Punctuation - no tags

### 2. Analysis JSON
**Filename:** `<title>.<source_lang>.analysis.json`

Example: `Jaane Tu Ya Jaane Na.hi.analysis.json`

Detailed JSON structure with word-by-word breakdown:

```json
{
  "file": "path/to/source.srt",
  "total_subtitles": 142,
  "subtitles": [
    {
      "index": 2,
      "start": "0:00:19",
      "end": "0:00:23.600000",
      "original_text": "Sorry यह हमारी ग्रूप के लिए बहुत special गान है",
      "words": [
        {"word": "Sorry", "lang": "en"},
        {"word": "यह", "lang": "hi"},
        {"word": "हमारी", "lang": "hi"},
        {"word": "ग्रूप", "lang": "hi"},
        {"word": "के", "lang": "hi"},
        {"word": "लिए", "lang": "hi"},
        {"word": "बहुत", "lang": "hi"},
        {"word": "special", "lang": "en"},
        {"word": "गान", "lang": "hi"},
        {"word": "है", "lang": "hi"}
      ],
      "languages_detected": ["hi", "en"],
      "is_hinglish": true
    }
  ]
}
```

**Fields:**
- `original_text` - Original subtitle text
- `words` - Array of word objects with language tags
- `languages_detected` - List of unique languages in this subtitle
- `is_hinglish` - Boolean flag if subtitle mixes Hindi and English

## Standalone Usage

You can also run the Hinglish detector independently:

### Basic Usage

```bash
python scripts/hinglish_word_detector.py input.hi.srt -v
```

This creates:
- `input.hi.tagged.srt` - Tagged subtitle file
- `input.hi.analysis.json` - Detailed analysis

### Custom Output Paths

```bash
python scripts/hinglish_word_detector.py input.hi.srt \
  -o custom_output.tagged.srt \
  -j custom_analysis.json \
  -v
```

### Options

- `-o, --output` - Custom output path for tagged SRT
- `-j, --json` - Custom output path for analysis JSON
- `-v, --verbose` - Verbose output with statistics

## Statistics Output

The detection provides statistics in the pipeline logs:

```
[INFO] ======================================================================
[INFO] WORD-LEVEL LANGUAGE DETECTION STATISTICS
[INFO] ======================================================================
[INFO] Total words:     967
[INFO] Hindi words:     768 (79.4%)
[INFO] English words:   106 (11.0%)
[INFO] Mixed words:     0 (0.0%)
[INFO] Punctuation:     93 (9.6%)
[INFO] ======================================================================
```

## Use Cases

### 1. Translation Quality Analysis

Compare the word-level detection with translation outputs:

```bash
# View original with tags
head -50 out/.../Jaane\ Tu\ Ya\ Jaane\ Na.hi.tagged.srt

# Compare with translations
diff out/.../Jaane\ Tu\ Ya\ Jaane\ Na.hi.tagged.srt \
     out/.../Jaane\ Tu\ Ya\ Jaane\ Na.en.srt
```

### 2. Code-Switching Patterns

Analyze where English words appear in Hindi dialogue:

```bash
# Use jq to find Hinglish subtitles
cat out/.../Jaane\ Tu\ Ya\ Jaane\ Na.hi.analysis.json | \
  jq '.subtitles[] | select(.is_hinglish == true) | .original_text'
```

### 3. Transcription Validation

Identify potential transcription errors where script doesn't match expected language:

```bash
# Check for unexpected English in pure Hindi songs
cat out/.../analysis.json | \
  jq '.subtitles[] | select(.languages_detected | contains(["en"])) | 
      {index, text: .original_text}'
```

## Technical Details

### Language Detection Method

The detector uses Unicode script ranges:
- **Devanagari:** U+0900 to U+097F (Hindi/Sanskrit)
- **Latin:** a-z, A-Z (English/Roman)
- **Punctuation:** Special characters

### Word Tokenization

- Splits on whitespace
- Preserves punctuation
- Separates trailing punctuation (e.g., "word," → "word" + ",")
- Handles mixed-script scenarios

### Performance

- Fast: ~100-150 subtitles/second
- Lightweight: No ML models required
- Deterministic: Same input = same output

## Troubleshooting

### Feature Not Running

**Check:**
1. Source language is set to "hi" in job.json
2. `hinglish_detection.enabled` is not set to false
3. Source subtitle file exists before detection stage

### Empty or Missing Output

**Causes:**
- Source subtitle file not found → Detection skipped (warning logged)
- Python dependencies missing → Install srt module: `pip install srt`

### Incorrect Detection

**Notes:**
- Detection is script-based (Devanagari vs Latin), not semantic
- Transliterated Hindi in Latin script will be detected as English
- Example: "aaj" (today) in Latin → detected as English

## Environment

The Hinglish detector runs in the **common** virtual environment:
- Uses: `venv/common`
- Dependencies: `srt` module (added to requirements-common.txt)

## Future Enhancements

Potential improvements:
- [ ] Support for other Indic scripts (Tamil, Telugu, etc.)
- [ ] Machine learning-based language detection (semantic)
- [ ] Confidence scores for each word
- [ ] Integration with NER for proper nouns
- [ ] Export to other formats (VTT, ASS)

## Related Documentation

- [Translation Pipeline](./TRANSLATION.md)
- [Subtitle Generation](./SUBTITLES.md)
- [Job Configuration](./JOB_CONFIG.md)

## Examples

### Full Pipeline with Hinglish Detection

```bash
# Prepare job
./prepare-job.sh -i "movie.mp4" -l hi -t en -w subtitle

# Run pipeline (Hinglish detection runs automatically)
./run-pipeline.sh out/2025/11/23/username/job-001

# View results
ls -lh out/2025/11/23/username/job-001/subtitles/
# movie.hi.srt           - Original Hindi subtitles
# movie.hi.tagged.srt    - Tagged with [HI]/[EN] markers
# movie.hi.analysis.json - Detailed word-level analysis
# movie.en.srt           - English translation
```

### Batch Analysis

Process multiple subtitle files:

```bash
for srt in out/**/subtitles/*.hi.srt; do
  echo "Processing: $srt"
  python scripts/hinglish_word_detector.py "$srt"
done
```

### Integration with Other Tools

Export statistics to CSV:

```python
import json
import csv

with open('movie.hi.analysis.json') as f:
    data = json.load(f)

with open('hinglish_stats.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Index', 'Start', 'End', 'Is_Hinglish', 'Text'])
    
    for sub in data['subtitles']:
        writer.writerow([
            sub['index'],
            sub['start'],
            sub['end'],
            sub['is_hinglish'],
            sub['original_text']
        ])
```

## Questions?

For issues or questions:
1. Check pipeline logs: `out/<job-dir>/logs/pipeline.log`
2. Run detector standalone with `-v` flag for debugging
3. Review this documentation

## Changelog

- **2025-11-23**: Initial implementation
  - Added word-level language detection
  - Integrated into subtitle workflow
  - Created tagged SRT and analysis JSON outputs
