# Hinglish Detection - Quick Start

## What is it?

Automatically detects and tags each word in your Hindi subtitles as either:
- `[HI]` Hindi (Devanagari script)
- `[EN]` English (Latin script)

Perfect for analyzing code-switching in Bollywood movies!

## When does it run?

✅ **Automatically** when you use the subtitle workflow with Hindi source language

```bash
./prepare-job.sh -i movie.mp4 -l hi -t en -w subtitle
./run-pipeline.sh out/2025/11/23/username/job-001
```

## Output Files

After pipeline completes, you'll find:

```
subtitles/
├── movie.hi.srt              # Original Hindi subtitles
├── movie.hi.tagged.srt       # NEW: With [HI]/[EN] tags
├── movie.hi.analysis.json    # NEW: Detailed word breakdown
└── movie.en.srt              # English translation
```

## Example Output

**Original:**
```srt
2
00:00:19,000 --> 00:00:23,600
Sorry यह हमारी ग्रूप के लिए बहुत special गान है
```

**Tagged:**
```srt
2
00:00:19,000 --> 00:00:23,600
[EN]Sorry[/EN] [HI]यह[/HI] [HI]हमारी[/HI] [HI]ग्रूप[/HI] [HI]के[/HI] 
[HI]लिए[/HI] [HI]बहुत[/HI] [EN]special[/EN] [HI]गान[/HI] [HI]है[/HI]
```

## Statistics in Logs

```
[INFO] Total words:     967
[INFO] Hindi words:     768 (79.4%)
[INFO] English words:   106 (11.0%)
```

## Disable It

Edit `job.json` after preparation:

```json
{
  "hinglish_detection": {
    "enabled": false
  }
}
```

## Run Manually

```bash
python scripts/hinglish_word_detector.py subtitle.hi.srt -v
```

## Full Documentation

See [HINGLISH_DETECTION.md](./HINGLISH_DETECTION.md) for complete details.

## Use Cases

1. **Quality Check**: Verify transcription is correct
2. **Pattern Analysis**: See where English words appear
3. **Translation Help**: Understand context better
4. **Research**: Analyze code-switching in Indian cinema

## Requirements

- Source language: Hindi (`hi`)
- Pipeline: Subtitle workflow
- Module: `srt` (auto-installed in common env)

That's it! Run your pipeline and get instant Hinglish analysis.
