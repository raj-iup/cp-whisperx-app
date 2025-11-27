# Prepare Job Guide

## Overview

The `prepare-job` script configures a job for the pipeline by validating inputs, setting workflow parameters, and generating a job manifest. Each job gets a unique ID and dedicated output directory.

## Workflows

### 1. Transcribe Workflow

Transcribe audio to text in the source language only.

**Use Case:** Extract dialogue/narration from video without translation

```bash
./prepare-job.sh in/movie.mp4 --transcribe

# With language hint
./prepare-job.sh in/bollywood.mp4 --transcribe -s hi

# With debug logging
./prepare-job.sh in/video.mp4 --transcribe --debug
```

**Pipeline Stages:** Demux → ASR → Alignment  
**Output:** `out/YYYY/MM/DD/USER/NNN/transcripts/transcript_source.txt`

### 2. Translate Workflow

Transcribe source audio and translate to target language(s).

**Use Case:** Get text translations without generating subtitles

```bash
# Hindi to English
./prepare-job.sh in/movie.mp4 --translate -s hi -t en

# Hindi to multiple languages
./prepare-job.sh in/movie.mp4 --translate -s hi -t en,gu,ta

# Auto-detect source language
./prepare-job.sh in/movie.mp4 --translate -t en
```

**Pipeline Stages:** Demux → ASR → Alignment → Translation  
**Output:** `out/YYYY/MM/DD/USER/NNN/transcripts/transcript_{lang}.txt` per language

### 3. Subtitle Workflow (Full Pipeline)

Complete workflow: transcribe, translate, generate subtitles, and embed in video.

**Use Case:** Create multi-language subtitle tracks in video file

```bash
# Full video
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en,gu

# Clipped segment
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en \
    --start-time 00:06:00 --end-time 00:08:30

# With styling and debug
./prepare-job.sh in/"Jaane Tu Ya Jaane Na 2008.mp4" \
    --subtitle -s hi -t en,gu \
    --subtitle-style "Bold,Yellow,Black" \
    --start-time 00:06:00 --end-time 00:08:30 \
    --debug
```

**Pipeline Stages:** Demux → ASR → Alignment → Translation → Subtitle Gen → Mux  
**Output:** `out/YYYY/MM/DD/USER/NNN/muxed/movie_subtitled.mkv` with soft-embedded tracks

## Command Line Options

### Required Arguments

```bash
<input_media>              # Path to video/audio file (MP4, MKV, MP3, WAV, etc.)
--transcribe|--translate|--subtitle   # Workflow mode
```

### Language Options

```bash
-s, --source-lang LANG     # Source audio language (e.g., hi, gu, ta)
                           # Auto-detected if not specified
                           
-t, --target-langs LANGS   # Comma-separated target languages (e.g., en,gu,ta)
                           # Required for --translate and --subtitle
```

**Supported Languages:**
- **Indic:** hi (Hindi), bn (Bengali), gu (Gujarati), mr (Marathi), ta (Tamil), te (Telugu), kn (Kannada), ml (Malayalam), pa (Punjabi), or (Odia), as (Assamese), ur (Urdu)
- **Target:** en (English) + all Indic languages

### Clipping Options

```bash
--start-time HH:MM:SS      # Clip start (e.g., 00:05:30)
--end-time HH:MM:SS        # Clip end (e.g., 00:10:45)
```

**Examples:**
```bash
# First 2 minutes
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en \
    --start-time 00:00:00 --end-time 00:02:00

# Middle segment
./prepare-job.sh in/movie.mp4 --transcribe \
    --start-time 00:15:30 --end-time 00:18:00
```

### Subtitle Styling

```bash
--subtitle-style "Style,Color,OutlineColor"
```

**Parameters:**
- **Style:** Bold, Italic, Underline, Regular
- **Color:** Yellow, White, Cyan, Green, Red
- **OutlineColor:** Black, White, Gray

**Examples:**
```bash
--subtitle-style "Bold,Yellow,Black"     # Default
--subtitle-style "Italic,White,Black"    # Subtle
--subtitle-style "Bold,Cyan,Black"       # High contrast
```

### Advanced Options

```bash
--model MODEL              # WhisperX model (default: large-v3)
                           # Options: tiny, base, small, medium, large-v3

--device DEVICE            # Compute device
                           # auto (default), cuda, mps, cpu

--compute-type TYPE        # Precision level
                           # float16 (default), float32, int8

--batch-size N             # Batch size for ASR (default: 16)
                           # Lower for memory-constrained systems

--debug                    # Enable verbose logging

--log-file PATH            # Custom log file location
```

## Output Structure

Jobs are organized in a date-based hierarchy:

```
out/
└── YYYY/                  # Year
    └── MM/                # Month
        └── DD/            # Day
            └── USER/      # Username
                └── NNN/   # Job counter (001, 002, ...)
                    ├── job.json              # Job configuration
                    ├── manifest.json         # Stage tracking
                    ├── audio/                # Extracted audio
                    ├── transcripts/          # Text transcripts
                    │   ├── transcript_source.txt
                    │   ├── transcript_en.txt
                    │   └── transcript_gu.txt
                    ├── subtitles/            # SRT subtitle files
                    │   ├── subtitles_en.srt
                    │   └── subtitles_gu.srt
                    └── muxed/                # Final video (subtitle workflow)
                        └── video_subtitled.mkv
```

## Job Configuration (job.json)

Example generated configuration:

```json
{
  "job_id": "job_20241120_001",
  "user": "rpatel",
  "workflow": "subtitle",
  "source_language": "hi",
  "target_languages": ["en", "gu"],
  "input_media": "/path/to/in/movie.mp4",
  "clipping": {
    "enabled": true,
    "start_time": "00:06:00",
    "end_time": "00:08:30"
  },
  "whisper": {
    "model": "large-v3",
    "device": "auto",
    "compute_type": "float16",
    "batch_size": 16
  },
  "subtitle_style": {
    "style": "Bold",
    "color": "Yellow",
    "outline": "Black"
  }
}
```

## Examples

### Example 1: Quick Transcription

Extract Hindi dialogue from a video:

```bash
./prepare-job.sh in/bollywood_movie.mp4 --transcribe -s hi
# Output: Job ID job_20241120_001
./run-pipeline.sh -j job_20241120_001
```

### Example 2: Multi-Language Translation

Translate Hindi audio to English and Gujarati:

```bash
./prepare-job.sh in/interview.mp4 --translate -s hi -t en,gu
./run-pipeline.sh -j job_20241120_002
```

### Example 3: Subtitle Scene Clip

Create English subtitles for a specific scene:

```bash
./prepare-job.sh in/"Jaane Tu Ya Jaane Na 2008.mp4" \
    --subtitle -s hi -t en \
    --start-time 00:06:00 --end-time 00:08:30 \
    --subtitle-style "Bold,Cyan,Black" \
    --debug

./run-pipeline.sh -j job_20241120_003
```

### Example 4: Full Movie with Multiple Subtitles

Process full movie with English, Gujarati, and Tamil subtitles:

```bash
./prepare-job.sh in/blockbuster.mp4 \
    --subtitle -s hi -t en,gu,ta \
    --model large-v3 \
    --batch-size 24

./run-pipeline.sh -j job_20241120_004
```

### Example 5: Low-Memory System

Optimize for systems with limited GPU memory:

```bash
./prepare-job.sh in/movie.mp4 \
    --subtitle -s hi -t en \
    --compute-type int8 \
    --batch-size 8 \
    --model medium

./run-pipeline.sh -j job_20241120_005
```

## Validation

The script validates:

1. **Input file exists** and is readable
2. **Language codes** are supported
3. **Time ranges** are valid (start < end)
4. **FFmpeg** is available
5. **Disk space** is sufficient
6. **Bootstrap** has been run (virtual environments exist)

## Troubleshooting

### Issue: "Input file not found"

```bash
# Check file path
ls -la in/

# Use absolute path
./prepare-job.sh "$(pwd)/in/movie.mp4" --transcribe

# Check filename escaping (spaces/special chars)
./prepare-job.sh in/"Movie Title (2024).mp4" --transcribe
```

### Issue: "Unsupported language"

```bash
# List supported languages
./prepare-job.sh --help

# Verify language code (2-letter ISO 639-1)
./prepare-job.sh in/movie.mp4 --translate -s hi -t en  # ✓ Correct
./prepare-job.sh in/movie.mp4 --translate -s hindi -t english  # ✗ Wrong
```

### Issue: "Invalid time format"

```bash
# Correct format: HH:MM:SS
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en \
    --start-time 00:06:00 --end-time 00:08:30  # ✓

# Common mistakes:
# --start-time 6:00        # ✗ Missing leading zeros
# --start-time 00:06       # ✗ Missing seconds
# --start-time 0:6:0       # ✗ Wrong format
```

### Issue: Job ID collision

If you see "Job already exists":

```bash
# Check existing jobs
ls -la out/$(date +%Y/%m/%d)/$(whoami)/

# Jobs increment automatically (001, 002, ...)
# If needed, clean old jobs
rm -rf out/2024/11/20/rpatel/001
```

## Performance Tips

1. **Use appropriate model size:**
   - `large-v3`: Best accuracy, slowest (10-20 min for 2hr movie)
   - `medium`: Good balance (5-10 min for 2hr movie)
   - `small`: Fast, lower accuracy (2-5 min for 2hr movie)

2. **Adjust batch size for your GPU:**
   - 24GB VRAM: `--batch-size 32`
   - 12GB VRAM: `--batch-size 16` (default)
   - 8GB VRAM: `--batch-size 8`
   - CPU only: `--batch-size 4`

3. **Use clipping for testing:**
   ```bash
   # Test on 1 minute first
   ./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en \
       --start-time 00:00:00 --end-time 00:01:00
   ```

## See Also

- [Bootstrap Guide](BOOTSTRAP.md) - Environment setup
- [Pipeline Guide](PIPELINE.md) - Running jobs
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
