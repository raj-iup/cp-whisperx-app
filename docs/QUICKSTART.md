# Quick Start Guide

Get the WhisperX Speech Processing Pipeline running in 5 minutes.

## Prerequisites

- **macOS** (Apple Silicon or Intel) or **Linux**
- **Python 3.8+**
- **8GB+ RAM** (16GB recommended)
- **10GB disk space** for models

## Installation

### Step 1: Clone and Setup

```bash
# Clone repository (if not already done)
cd /path/to/cp-whisperx-app

# Run bootstrap (one-time setup)
./bootstrap.sh
```

**Bootstrap does:**
- Creates Python virtual environment
- Installs all dependencies
- Downloads required models
- Configures environment (MLX/CUDA/CPU)
- Sets up directory structure

**Time**: 5-10 minutes (first run only)

### Step 2: Prepare Audio File

Place your audio file in the `in/` directory or use any path:

```bash
# Example: Copy your audio file
cp ~/Downloads/meeting.mp3 in/

# Or just use the full path
```

### Step 3: Prepare Job

```bash
# Basic usage
./prepare-job.sh in/meeting.mp3

# With options
./prepare-job.sh --source-lang hi --target-lang en in/meeting.mp3
```

**This creates**: Job configuration file with your settings

### Step 4: Run Pipeline

```bash
# Process the audio file
./run-pipeline.sh in/meeting.mp3
```

**Pipeline stages:**
1. **Transcribe**: Speech-to-text with WhisperX
2. **Translate**: Multi-language translation
3. **Subtitles**: SRT/VTT generation

**Output location**: `out/meeting/`

## Output Files

After processing, you'll find:

```
out/meeting/
├── meeting_transcript.json          # Full transcription with timing
├── meeting_transcript.txt           # Plain text transcript
├── meeting_translation.txt          # Translated text
├── meeting_subtitles.srt           # SRT subtitles
├── meeting_subtitles.vtt           # VTT subtitles (with metadata)
├── meeting_glossary.txt            # Auto-generated glossary
└── meeting_metadata.json           # Processing metadata
```

## Common Usage Patterns

### Standard Transcription Only

```bash
./prepare-job.sh --stage transcribe audio.mp3
./run-pipeline.sh audio.mp3
```

### Transcription + Translation

```bash
./prepare-job.sh --source-lang hi --target-lang en audio.mp3
./run-pipeline.sh audio.mp3
```

### With Custom Glossary

```bash
# Create glossary file
echo "WhisperX|व्हिस्परएक्स" > glossary/my-terms.txt
echo "Pipeline|पाइपलाइन" >> glossary/my-terms.txt

# Use it
./prepare-job.sh --glossary glossary/my-terms.txt --source-lang hi audio.mp3
./run-pipeline.sh audio.mp3
```

### Process Specific Stages

```bash
# Only transcribe
./run-pipeline.sh --stage transcribe audio.mp3

# Only translate (requires existing transcript)
./run-pipeline.sh --stage translate audio.mp3

# Only generate subtitles
./run-pipeline.sh --stage subtitles audio.mp3
```

## Configuration Quick Reference

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source-lang` | Audio language code | `hi` |
| `--target-lang` | Translation target | `en` |
| `--beam-size` | Beam search width | `5` |
| `--best-of` | Best candidates | `5` |
| `--glossary` | Glossary file path | None |
| `--stage` | Run specific stage | `all` |

### Language Codes

**Indian Languages** (IndicTrans2 optimized):
- `hi` - Hindi
- `bn` - Bengali
- `ta` - Tamil
- `te` - Telugu
- `mr` - Marathi
- `gu` - Gujarati
- `kn` - Kannada
- `ml` - Malayalam
- `pa` - Punjabi
- `ur` - Urdu

**Other Languages**: Use ISO 639-1 codes (`en`, `es`, `fr`, etc.)

See [Language Support](technical/language-support.md) for complete list.

## Troubleshooting

### Bootstrap Issues

```bash
# Issue: Permission denied
chmod +x bootstrap.sh prepare-job.sh run-pipeline.sh

# Issue: Python not found
# Install Python 3.8+ first
python3 --version
```

### Model Loading Errors

```bash
# Re-run bootstrap
./bootstrap.sh

# Check model directory
ls -lh venv/lib/python*/site-packages/whisperx/models/
```

### Memory Issues

```bash
# Reduce beam size in job config
./prepare-job.sh --beam-size 3 --best-of 3 audio.mp3
```

### Translation Failures

```bash
# Verify language code
./prepare-job.sh --source-lang hi --target-lang en audio.mp3

# Check glossary format (pipe-separated)
cat glossary/my-terms.txt
# Should be: source|target
```

See [Troubleshooting Guide](user-guide/troubleshooting.md) for detailed solutions.

## Environment Detection

The pipeline automatically detects and uses the best available environment:

1. **MLX** - Apple Silicon (M1/M2/M3) - Fastest on Mac
2. **CUDA** - NVIDIA GPU - Fastest on Linux/Windows
3. **CPU** - Universal fallback - Works everywhere

Check detected environment:

```bash
# In bootstrap output, look for:
# "Environment: MLX" or "Environment: CUDA" or "Environment: CPU"
```

## Performance Expectations

**Transcription speed** (varies by environment):

| Environment | Processing Speed | 1hr Audio |
|-------------|-----------------|-----------|
| MLX (M2)    | ~20x realtime   | ~3 min    |
| CUDA (3090) | ~30x realtime   | ~2 min    |
| CPU (8-core)| ~2x realtime    | ~30 min   |

**Translation**: 1-2 minutes per 1000 segments
**Subtitles**: Under 1 minute

## Next Steps

Now that you have the basics:

1. **Learn Workflows**: [Workflows Guide](user-guide/workflows.md)
2. **Customize Config**: [Configuration Guide](user-guide/configuration.md)
3. **Create Glossaries**: [Glossary Builder](user-guide/glossary-builder.md)
4. **Understand Architecture**: [Technical Docs](technical/README.md)

## Need Help?

- **Documentation Index**: [docs/INDEX.md](INDEX.md)
- **User Guide**: [user-guide/README.md](user-guide/README.md)
- **Troubleshooting**: [user-guide/troubleshooting.md](user-guide/troubleshooting.md)
- **Configuration**: [user-guide/configuration.md](user-guide/configuration.md)

## Example Session

Complete example from start to finish:

```bash
# 1. Bootstrap (first time only)
./bootstrap.sh
# Output: Environment setup complete. MLX detected.

# 2. Prepare job for Hindi audio
./prepare-job.sh --source-lang hi --target-lang en in/meeting.mp3
# Output: Job configuration created: config/job_meeting.conf

# 3. Run pipeline
./run-pipeline.sh in/meeting.mp3
# Output:
# [Transcribe] Processing meeting.mp3...
# [Transcribe] Complete: out/meeting/meeting_transcript.json
# [Translate] Translating 150 segments...
# [Translate] Complete: out/meeting/meeting_translation.txt
# [Subtitles] Generating SRT/VTT...
# [Subtitles] Complete: out/meeting/meeting_subtitles.srt
# Pipeline complete!

# 4. Check output
ls -lh out/meeting/
# meeting_transcript.json  meeting_transcript.txt
# meeting_translation.txt  meeting_glossary.txt
# meeting_subtitles.srt   meeting_subtitles.vtt
# meeting_metadata.json
```

---

# Quickstart Guide — Glossary System

This quickstart demonstrates how to run the project's three main phases (baseline, glossary, cache) with the provided example media.

Default sample media:
- /Users/rpatel/Projects/cp-whisperx-app/in/Jaane Tu Ya Jaane Na 2008.mp4

Prerequisites:
- Ensure Python and required venvs are installed.
- Optionally run the Demucs bootstrap (if you request source separation):
  - ./scripts/bootstrap.sh venv/demucs mps

Quickstart steps (interactive or auto mode):

1) Auto-run:
   - ./test-glossary-quickstart.sh --auto
   - This runs baseline, glossary, and cache phases automatically with default clip times (00:00:00-00:05:00).

2) Run as CI (fail on cache verification):
   - ./test-glossary-quickstart.sh --auto --ci

3) Run with explicit device/device detection:
   - For MPS (Apple Silicon): --device mps
   - For CPU: --device cpu
   - If omitted, the script auto-detects env based on host.

4) Override defaults:
   - Use --video /path/to/video to test a different media.
   - Use --start-time / --end-time to test a time slice.

5) Debugging & verification:
   - Logs and manifests are under out/YYYY/MM/DD/quickstart/device_<device>/
   - SKIPPED stages are signaled via:
     - Human logs containing "SKIPPED"
     - Structured logs containing event "stage_skipped"
   - Manifests include timestamps; the quickstart script validates heavy stage manifests for equality across baseline/cache runs.

Tips:
- Use small clip durations for CI runs to keep time short (e.g., --start-time 00:00:00 --end-time 00:00:10).
- For stable runs with Demucs and PyTorch MPS, prefer using pre-built wheels and a cached venv (scripts/bootstrap.sh + CI cache).
- Use `--auto-install-demucs` to attempt installing Demucs into `venv/demucs` when a Demucs runtime isn't preinstalled (best effort; may still require platform-specific wheels).

Example:
- ./test-glossary-quickstart.sh --auto --clip 00:00:00-00:00:10 --device mps --ci

### Examples: Using the quickstart script with in/ media

- Basic auto-run (default sample)
  - Command:
    ./test-glossary-quickstart.sh --auto
  - What it does:
    - Runs baseline → glossary → cache phases for the default sample under in/
    - Produces per-slice outputs under test-results/<phase>/slice-<n> and pipeline job output under out/YYYY/MM/DD/quickstart/device_<device>/

- Process a specific media (positional arg)
  - Command:
    ./test-glossary-quickstart.sh in/Jaane\ Tu\ Ya\ Jaane\ Na\ 2008.mp4 --auto
  - Notes:
    - Uses the file in/in/ and auto-detects device (MPS on Apple Silicon when available).
    - If you want to specify log-level, chunk-size or device: add flags like `--log-level DEBUG --chunk-size 15m --device mps`.

- Process a small time slice (quick CI run)
  - Command:
    ./test-glossary-quickstart.sh in/Jaane\ Tu\ Ya\ Jaane\ Na\ 2008.mp4 --start-time 00:00:00 --end-time 00:00:10 --auto --ci --chunk-size 30s
  - What it does:
    - Auto-runs baseline → glossary → cache for a short 10-second clip.
    - CI mode causes the script to exit non-zero if cache verification fails (useful in pipelines).

- Process entire media in 15 minute chunks (default chunking)
  - Command:
    ./test-glossary-quickstart.sh in/your-video.mp4 --auto --chunk-size 15m
  - What it does:
    - The script slices the media into 15-minute ranges and sequentially runs baseline, glossary, and cache for each slice.
    - Results (subtitles/logs/manifests) are saved per slice in test-results/<phase>/slice-<n>.

- Run with TMDB enrichment (use TMDB title/year instead of derived title)
  - Command (TMDB ID approach):
    ./test-glossary-quickstart.sh in/your-video.mp4 --tmdb-id 14467 --tmdb-api-key YOUR_API_KEY --auto
  - Command (TMDB search query approach):
    ./test-glossary-quickstart.sh in/your-video.mp4 --tmdb-query "Jaane Tu Ya Jaane Na" --tmdb-api-key YOUR_API_KEY --auto
  - What it does:
    - The script queries TMDB (with the key) to get the film title/year and populates job.json accordingly.

- Force stages to re-run and bypass cache (useful to regenerate)
  - Command:
    ./test-glossary-quickstart.sh in/your-video.mp4 --auto --stages demux,tmdb --force
  - Notes:
    - Depending on run-pipeline.sh support, the script might fallback to env vars if the runner doesn't accept CLI flags.

- Enable Demucs auto-installation (best-effort)
  - Command:
    ./test-glossary-quickstart.sh in/your-video.mp4 --auto --auto-install-demucs --demucs-venv venv/demucs --device mps
  - Notes:
    - Use only when CI or your environment doesn't have Demucs pre-installed. Prefer bootstrap approach for CI (prebuilt wheel cache).

### Quick verification commands

- Check SKIPPED events (structured logs) for cache hits:
  - grep -r '"event":"stage_skipped"' out/YYYY/MM/DD/quickstart/device_* || true
  - This returns JSON lines with event=stage_skipped for cached stages.

- Validate manifest timestamps didn't change between baseline and cache phase for heavy stages (e.g., source_separation):
  - jq -r '.timestamp' out/YYYY/MM/DD/quickstart/*/01_demux/manifest.json
  - jq -r '.timestamp' out/YYYY/MM/DD/quickstart/*/04_source_separation/manifest.json
  - Compare timestamps across runs; if identical and SKIPPED messages are present, the cache was effective.

---

**Navigation**: [Home](../README.md) | [Documentation Index](INDEX.md) | [User Guide](user-guide/README.md)
