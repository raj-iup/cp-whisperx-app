# Quick Start Guide

Complete guide to get started with CP-WhisperX-App workflows.

---

## Table of Contents

1. [Installation](#installation)
2. [Transcribe Workflow](#transcribe-workflow)
3. [Translate Workflow](#translate-workflow)
4. [Subtitle Workflow](#subtitle-workflow)
5. [Common Options](#common-options)
6. [Examples](#examples)

---

## Installation

### Prerequisites

1. **Python 3.11+**
   ```bash
   python3 --version  # Should be 3.11 or higher
   ```

2. **FFmpeg**
   ```bash
   # macOS
   brew install ffmpeg
   
   # Linux
   sudo apt-get install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

### Bootstrap

Run once to set up all environments:

```bash
# macOS/Linux
./bootstrap.sh --debug

# Windows
.\bootstrap.ps1 -Debug
```

**What it does**:
- Creates 7 isolated Python environments
- Installs all dependencies automatically
- Downloads initial models (~5GB)
- Takes 15-20 minutes on first run

**Environments created**:
- `venv/common` - Core utilities (FFmpeg wrappers, logging)
- `venv/whisperx` - WhisperX ASR engine
- `venv/mlx` - Apple Silicon acceleration (macOS only)
- `venv/pyannote` - PyAnnote VAD (voice activity detection)
- `venv/demucs` - Demucs (audio source separation)
- `venv/indictrans2` - Indic language translation
- `venv/nllb` - Universal translation (200+ languages)

**All environments are automatically configured for highest quality transcription.**

---

## Transcribe Workflow

Convert audio/video to text transcript in the source language.

### Basic Usage

```bash
./prepare-job.sh in/movie.mp4 --transcribe --debug
```

### With Clip Extraction

```bash
./prepare-job.sh in/movie.mp4 --transcribe \
    --start-time 00:06:00 \
    --end-time 00:08:30 \
    --debug
```

### Specify Source Language

```bash
./prepare-job.sh in/movie.mp4 --transcribe -s hi --debug
```

### Output

```
out/
└── 2025/11/20/rpatel/1/
    ├── job.json              # Job configuration
    ├── manifest.json         # Execution status
    ├── .env                  # Environment variables
    ├── media/
    │   ├── audio.wav        # Extracted audio
    │   └── movie.mp4        # Input video (symlink or clip)
    ├── transcripts/
    │   ├── segments.json    # Timestamped segments
    │   └── transcript.txt   # Plain text transcript
    └── logs/
        └── pipeline.log     # Execution logs
```

### Example Output (transcript.txt)

```
Welcome to our presentation today.
We will discuss the latest developments in AI.
Let's begin with an overview of the technology.
```

---

## Translate Workflow

Translate source text to one or more target languages.

### Single Target Language

```bash
# Hindi to English
./prepare-job.sh in/movie.mp4 --translate -s hi -t en --debug
```

### Multiple Target Languages

```bash
# Hindi to English, Gujarati, Tamil
./prepare-job.sh in/movie.mp4 --translate \
    -s hi \
    -t en,gu,ta \
    --debug
```

### Mixed Indic and Non-Indic Targets

```bash
# Hinglish to English, Gujarati, Spanish, Arabic
./prepare-job.sh in/movie.mp4 --translate \
    -s hi \
    -t en,gu,es,ar \
    --debug
```

**Translation Routing**:
- `hi → en`: IndicTrans2-en (`venv/indictrans2`)
- `hi → gu`: IndicTrans2-indic (`.venv-indic-indic`)
- `hi → es`: NLLB-200 (`venv/nllb`)
- `hi → ar`: NLLB-200 (`venv/nllb`)

### Output

```
out/2025/11/20/rpatel/1/
├── transcripts/
│   ├── transcript.txt           # Source language
│   ├── transcript.en.txt        # English translation
│   ├── transcript.gu.txt        # Gujarati translation
│   ├── transcript.ta.txt        # Tamil translation
│   ├── segments_translated_en.json
│   ├── segments_translated_gu.json
│   └── segments_translated_ta.json
└── ...
```

---

## Subtitle Workflow

Complete end-to-end workflow: transcribe → translate → generate subtitles → embed in video.

### Basic Subtitle Generation

```bash
./prepare-job.sh in/movie.mp4 --subtitle \
    -s hi \
    -t en,gu \
    --debug
```

### With Clip Extraction

```bash
./prepare-job.sh in/"Jaane Tu Ya Jaane Na 2008.mp4" --subtitle \
    -s hi \
    -t en,gu \
    --start-time 00:06:00 \
    --end-time 00:08:30 \
    --debug
```

### Multi-Language Subtitles

```bash
# Generate subtitles in 5 languages
./prepare-job.sh in/movie.mp4 --subtitle \
    -s hi \
    -t en,gu,ta,es,ar \
    --debug
```

### Output

```
out/2025/11/20/rpatel/1/
├── media/
│   ├── input.mp4            # Original or clip
│   ├── audio.wav            # Extracted audio
│   └── output.mp4           # Final video with all subtitles
├── subtitles/
│   ├── movie.hi.srt         # Source language subtitle
│   ├── movie.en.srt         # English subtitle
│   ├── movie.gu.srt         # Gujarati subtitle
│   ├── movie.ta.srt         # Tamil subtitle
│   ├── movie.es.srt         # Spanish subtitle
│   └── movie.ar.srt         # Arabic subtitle
├── transcripts/
│   └── ...
└── logs/
    └── pipeline.log
```

### Subtitle Track Info

Video output includes soft-embedded subtitles for all languages:
```bash
ffmpeg -i out/.../media/output.mp4 2>&1 | grep "Subtitle"
```

Output:
```
Stream #0:2(eng): Subtitle: subrip
Stream #0:3(guj): Subtitle: subrip
Stream #0:4(tam): Subtitle: subrip
Stream #0:5(spa): Subtitle: subrip
Stream #0:6(ara): Subtitle: subrip
```

---

## Common Options

### Language Codes

**Source Language** (`-s, --source-language`)
- `hi` - Hindi
- `en` - English
- `bn` - Bengali
- `gu` - Gujarati
- `ta` - Tamil
- `te` - Telugu
- See [docs/LANGUAGE_CODES.md](LANGUAGE_CODES.md) for full list

**Target Languages** (`-t, --target-languages`)
- Comma-separated list (up to 5)
- Examples: `en`, `en,gu`, `en,gu,ta,es,ar`

### Time Range

**Start Time** (`--start-time`)
- Format: `HH:MM:SS` or `MM:SS`
- Examples: `00:06:00`, `06:00`, `1:30:00`

**End Time** (`--end-time`)
- Format: `HH:MM:SS` or `MM:SS`
- Examples: `00:08:30`, `08:30`, `2:00:00`

### Hardware Control

**Device** (`--device`)
- `mps` - Apple Metal Performance Shaders (default on macOS)
- `cuda` - NVIDIA GPU (default on Linux with CUDA)
- `cpu` - CPU only

**Backend** (`--backend`)
- `mlx` - Apple Silicon MLX (recommended for M1/M2/M3)
- `whisperx` - Standard WhisperX (CUDA/CPU)

### Model Selection

**ASR Model** (`--model`)
- `large-v3` - Latest Whisper model (default, best quality)
- `large-v2` - Previous version
- `medium` - Faster, slightly lower quality
- `small` - Fast, lower quality

**Compute Type** (`--compute-type`)
- Auto-detected based on device
- `float16` - GPU (CUDA, MPS, MLX)
- `int8` - CPU
- `float32` - Maximum precision (slower)

### Debug Mode

**Enable Debug** (`--debug`)
- Verbose logging
- Detailed error messages
- Performance metrics
- Full command output

```bash
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en --debug
```

---

## Examples

### Example 1: Quick Transcription

Transcribe a podcast episode:

```bash
./prepare-job.sh in/podcast-ep12.mp3 --transcribe -s en --debug
```

**Output**: `out/.../transcripts/transcript.txt`

---

### Example 2: Multi-Language Translation

Translate a Hindi news broadcast to multiple languages:

```bash
./prepare-job.sh in/news-hindi.mp4 --translate \
    -s hi \
    -t en,gu,mr,ta \
    --debug
```

**Output**: 4 translated transcripts (en, gu, mr, ta)

---

### Example 3: Movie Clip with Subtitles

Extract 2.5-minute clip and generate bilingual subtitles:

```bash
./prepare-job.sh in/"Jaane Tu Ya Jaane Na 2008.mp4" --subtitle \
    -s hi \
    -t en,gu \
    --start-time 00:06:00 \
    --end-time 00:08:30 \
    --debug
```

**Output**: 
- `output.mp4` with 3 subtitle tracks (hi, en, gu)
- 3 `.srt` files

---

### Example 4: Educational Content

Transcribe and translate educational video to multiple Indic languages:

```bash
./prepare-job.sh in/science-lesson.mp4 --subtitle \
    -s en \
    -t hi,gu,ta,te,bn \
    --debug
```

**Uses**:
- NLLB for en → hi, gu, ta, te, bn
- Generates 6 subtitle tracks

---

### Example 5: Global Audience

Create subtitles for international audience (Indic + Non-Indic):

```bash
./prepare-job.sh in/documentary.mp4 --subtitle \
    -s hi \
    -t en,gu,es,fr,ar \
    --debug
```

**Translation Engines**:
- IndicTrans2 for `hi → en, gu`
- NLLB for `hi → es, fr, ar`

---

## Next Steps

- **[Architecture](ARCHITECTURE.md)** - Understand the system design
- **[Workflows](WORKFLOWS.md)** - Deep dive into each workflow
- **[Pipeline Execution](PIPELINE.md)** - How stages are executed
- **[Troubleshooting](TROUBLESHOOTING.md)** - Fix common issues

---

**Last Updated**: November 20, 2025
