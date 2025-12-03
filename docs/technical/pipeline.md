# Pipeline Orchestrator Guide

**Document Version:** 1.0  
**Last Updated:** December 3, 2025  
**Compliance Status:** 🎊 100% Perfect Compliance  
**Pre-commit Hook:** ✅ Active

## Overview

The `run-pipeline` script executes the multi-stage processing pipeline for a prepared job. It manages stage execution, dependency tracking, error handling, and progress monitoring.

## Basic Usage

```bash
# Run a prepared job
./run-pipeline.sh -j <job-id>

# Example
./run-pipeline.sh -j job_20241120_001
```

## Pipeline Stages

---

## ⚠️ Architecture Versions

**Current Implementation:** v2.0 (Simplified 3-6 Stage Pipeline)  
**Target Architecture:** v3.0 (Modular 10-Stage Pipeline)  
**Migration Status:** 55% Complete

See: [Architecture Implementation Roadmap](../ARCHITECTURE_IMPLEMENTATION_ROADMAP.md)

---

## Current Implementation (v2.0)

The pipeline currently executes stages based on the workflow:

### Transcribe Workflow (3 stages)

**Active Stages:**
1. ✅ **Demux** - Audio extraction (`scripts/demux.py`)
2. ✅ **ASR** - Speech recognition (`scripts/whisperx_asr.py`)
3. ✅ **Alignment** - Word-level timestamps (inline in ASR)

### Translate Workflow (4-5 stages)

**Active Stages:**
1. ✅ **Demux** - Audio extraction
2. ✅ **ASR** - Speech recognition
3. ✅ **Alignment** - Word-level timestamps
4. ✅ **Translation** - IndicTrans2 translation (`scripts/indictrans2_translator.py`)
5. ✅ **Subtitle Gen** - SRT generation (inline function)

### Subtitle Workflow (6 stages)

**Active Stages:**
1. ✅ **Demux** - Audio extraction
2. ✅ **ASR** - Speech recognition
3. ✅ **Alignment** - Word-level timestamps
4. ✅ **Translation** - IndicTrans2 translation
5. ✅ **Subtitle Gen** - SRT generation
6. ✅ **Mux** - Video embedding (`scripts/mux.py`)

---

## Future Architecture (v3.0)

### Planned 10-Stage Modular Pipeline

The target architecture will support a fully modular, 10-stage pipeline with enable/disable configuration per stage:

1. ✅ **01_demux** - Audio extraction (implemented)
2. ⏳ **02_tmdb** - TMDB metadata enrichment (script exists, not integrated)
3. ⏳ **03_glossary_load** - Glossary loading (partial implementation)
4. ✅ **04_asr** - Speech recognition (implemented as `scripts/whisperx_asr.py`)
5. ⏳ **05_ner** - Named entity recognition (scripts exist, not integrated)
6. ⏳ **06_lyrics_detection** - Lyrics detection (standalone, needs integration)
7. ⏳ **07_hallucination_removal** - Remove hallucinations (standalone)
8. ⏳ **08_translation** - IndicTrans2 translation (partially integrated)
9. ⏳ **09_subtitle_gen** - Professional SRT/VTT (inline, needs module)
10. ✅ **10_mux** - Video embedding (implemented)

**Legend:**
- ✅ **Implemented and integrated** - Fully functional in current pipeline
- ⏳ **Implemented but not integrated** - Code exists but not integrated as modular stage
- ❌ **Not implemented yet** - Planned for future implementation

**Migration Path:** See [Architecture Implementation Roadmap](../ARCHITECTURE_IMPLEMENTATION_ROADMAP.md) for detailed 21-week implementation plan.

**Benefits of v3.0:**
- Selective stage enable/disable per job
- Better quality control and validation
- Modular testing and development
- Enhanced extensibility
- Stage-level dependency management

---

## Command Line Options

```bash
# Required
-j, --job-id JOB_ID        Job ID from prepare-job.sh

# Optional
--status                   Show job status and exit
--resume                   Resume from last completed stage
--force                    Restart pipeline from beginning
--stage STAGE              Run specific stage only
--debug                    Enable verbose logging
-h, --help                 Show help message
```

## Stage Details

### 1. Demux (Audio Extraction)

Extracts audio from video using FFmpeg.

**Input:** Video file (MP4, MKV, AVI, etc.)  
**Output:** `audio/audio.wav` (16kHz, mono)  
**Virtual Env:** `venv/common`

**What it does:**
- Extracts audio track
- Converts to 16kHz mono WAV
- Applies clipping if configured
- Validates audio quality

**Typical Duration:** 10-30 seconds per hour of video

### 2. ASR (Automatic Speech Recognition)

Transcribes audio using WhisperX.

**Input:** `audio/audio.wav`  
**Output:** `transcripts/raw_transcript.json`  
**Virtual Env:** `venv/whisperx` (macOS/Windows) or `venv/mlx` (macOS with MLX)

**What it does:**
- Loads WhisperX large-v3 model
- Transcribes audio to text
- Detects speaker changes
- Generates word-level timing

**Typical Duration:** 
- MLX (M2): 2-5 min per hour of audio
- CUDA (RTX 4090): 3-8 min per hour
- MPS (M1): 5-12 min per hour
- CPU: 30-60 min per hour

### 3. Alignment

Refines word-level timestamps.

**Input:** `transcripts/raw_transcript.json`  
**Output:** `transcripts/aligned_transcript.json`  
**Virtual Env:** `venv/whisperx`

**What it does:**
- Aligns words with audio
- Improves timestamp accuracy
- Adds confidence scores
- Prepares for translation

**Typical Duration:** 30-90 seconds per hour of audio

### 4. Translation (IndicTrans2)

Translates transcripts to target languages.

**Input:** `transcripts/aligned_transcript.json`  
**Output:** `transcripts/transcript_{lang}.txt` per language  
**Virtual Env:** `venv/indictrans2`

**What it does:**
- Loads IndicTrans2 models
- Translates segments
- Preserves timing information
- Handles multiple target languages

**Supported Translations:**
- Indic → English
- English → Indic
- Indic → Indic

**Typical Duration:** 1-3 min per hour per target language

### 5. Subtitle Generation

Creates SRT subtitle files.

**Input:** Translated transcripts  
**Output:** `subtitles/subtitles_{lang}.srt` per language  
**Virtual Env:** `venv/common`

**What it does:**
- Formats text as SRT
- Applies timing from alignment
- Adds styling (color, bold, etc.)
- Ensures subtitle sync

**Typical Duration:** 5-15 seconds per language

### 6. Mux (Video Embedding)

Embeds subtitles in video as soft tracks.

**Input:** Video + SRT files  
**Output:** `muxed/{basename}_subtitled.mkv`  
**Virtual Env:** `venv/common`

**What it does:**
- Copies video/audio streams
- Adds subtitle tracks
- Sets track metadata (language, title)
- Creates MKV container

**Typical Duration:** 30-90 seconds per hour of video

## Monitoring Progress

### Real-Time Monitoring

```bash
# Run in one terminal
./run-pipeline.sh -j job_20241120_001

# Monitor in another terminal
tail -f logs/job_20241120_001.log

# Check status
./scripts/pipeline-status.sh job_20241120_001
```

### Stage Status

Each stage updates `manifest.json`:

```json
{
  "stages": {
    "demux": {
      "status": "success",
      "completed": true,
      "started_at": "2024-11-20T10:00:00",
      "completed_at": "2024-11-20T10:00:15"
    },
    "asr": {
      "status": "running",
      "completed": false,
      "started_at": "2024-11-20T10:00:15"
    }
  }
}
```

## Error Handling

### Stage Failure

If a stage fails:

1. **Check the log file:**
   ```bash
   tail -50 logs/job_20241120_001.log
   ```

2. **Review manifest:**
   ```bash
   cat out/2024/11/20/rpatel/001/manifest.json
   ```

3. **Fix the issue** (see Troubleshooting below)

4. **Resume pipeline:**
   ```bash
   ./run-pipeline.sh -j job_20241120_001 --resume
   ```

### Common Failure Points

**Demux fails:**
- Input file corrupted
- Unsupported codec
- Disk space exhausted

**ASR fails:**
- Out of memory
- Model not downloaded
- Audio quality too poor

**Translation fails:**
- IndicTrans2 models missing
- Unsupported language pair
- Text too long for model

**Mux fails:**
- Output directory read-only
- FFmpeg version incompatible
- Subtitle encoding issue

## Advanced Usage

### Run Specific Stage

Useful for debugging or re-running:

```bash
# Re-run translation only
./run-pipeline.sh -j job_20241120_001 --stage translation

# Re-run subtitle generation
./run-pipeline.sh -j job_20241120_001 --stage subtitle_gen
```

**Available stages:** `demux`, `asr`, `alignment`, `translation`, `subtitle_gen`, `mux`

### Force Restart

Clear all progress and restart:

```bash
./run-pipeline.sh -j job_20241120_001 --force
```

**Warning:** This deletes intermediate outputs (audio, transcripts, etc.)

### Resume After Manual Fix

If you manually fix an intermediate file:

```bash
# Update manifest to mark stage complete
# Then resume from next stage
./run-pipeline.sh -j job_20241120_001 --resume
```

## Performance Optimization

### GPU Memory

If running out of VRAM:

```bash
# Edit job.json before running
{
  "whisper": {
    "compute_type": "int8",      # Lower precision
    "batch_size": 8               # Smaller batches
  }
}
```

### CPU Usage

For CPU-only systems:

```bash
# Edit job.json
{
  "whisper": {
    "device": "cpu",
    "batch_size": 4,
    "compute_type": "int8"
  }
}
```

### Parallel Jobs

Run multiple jobs simultaneously:

```bash
# Terminal 1
./run-pipeline.sh -j job_20241120_001

# Terminal 2
./run-pipeline.sh -j job_20241120_002

# Terminal 3
./run-pipeline.sh -j job_20241120_003
```

**Note:** Monitor GPU memory usage - adjust batch sizes if needed

## Output Validation

### Check Transcript Quality

```bash
# View source transcript
cat out/2024/11/20/rpatel/001/transcripts/transcript_source.txt

# View translated transcript
cat out/2024/11/20/rpatel/001/transcripts/transcript_en.txt
```

### Check Subtitle Sync

```bash
# Play video with subtitles
mpv out/2024/11/20/rpatel/001/muxed/movie_subtitled.mkv

# Or use VLC, QuickTime, etc.
```

### Verify Subtitle Tracks

```bash
# List tracks in output video
ffprobe -v error -show_entries stream=index:stream_tags=language:stream=codec_name \
    out/2024/11/20/rpatel/001/muxed/movie_subtitled.mkv
```

Expected output:
```
[STREAM]
index=0
codec_name=h264
[/STREAM]

[STREAM]
index=1
codec_name=aac
[/STREAM]

[STREAM]
index=2
codec_name=subrip
language=eng
[/STREAM]

[STREAM]
index=3
codec_name=subrip
language=guj
[/STREAM]
```

## Troubleshooting

### Issue: "Job not found"

```bash
# Check job ID
ls -la out/2024/11/20/rpatel/

# Use full job ID
./run-pipeline.sh -j job_20241120_001  # Not just "001"
```

### Issue: Pipeline hangs at ASR stage

```bash
# Check GPU memory
nvidia-smi  # (NVIDIA GPU)
# or
asitop      # (Apple Silicon)

# Kill and restart with lower batch size
pkill -f run-pipeline
# Edit job.json, reduce batch_size
./run-pipeline.sh -j job_20241120_001 --resume
```

### Issue: Out of disk space

```bash
# Check space
df -h

# Clean old jobs
rm -rf out/2024/11/19/*

# Clean model cache (careful!)
rm -rf ~/.cache/huggingface/hub/*
```

### Issue: Subtitles out of sync

Usually caused by:
1. **Clipping timestamps wrong** - Check start/end times in job.json
2. **Audio quality poor** - Try larger model (medium → large-v3)
3. **Multiple speakers overlapping** - WhisperX may struggle

Fix:
```bash
# Re-run with better model
# Edit job.json, change model to "large-v3"
./run-pipeline.sh -j job_20241120_001 --stage asr --force
./run-pipeline.sh -j job_20241120_001 --resume
```

### Issue: Translation quality poor

```bash
# Check source transcript first
cat out/2024/11/20/rpatel/001/transcripts/transcript_source.txt

# If source is good but translation bad:
# 1. Check language pair is supported
# 2. Try re-running translation stage
./run-pipeline.sh -j job_20241120_001 --stage translation --force
```

## Benchmarks

Typical end-to-end times for 2-hour movie:

| Platform | Workflow | Time |
|----------|----------|------|
| M2 Max + MLX | Subtitle (hi→en) | 8-12 min |
| M1 + MPS | Subtitle (hi→en) | 15-25 min |
| RTX 4090 | Subtitle (hi→en,gu) | 12-18 min |
| RTX 3080 | Subtitle (hi→en,gu) | 18-30 min |
| CPU (16-core) | Transcribe only | 60-90 min |

Stage breakdown (2hr movie, M2 Max):
- Demux: ~15 sec
- ASR: ~5 min
- Alignment: ~45 sec
- Translation: ~2 min per language
- Subtitle Gen: ~8 sec per language
- Mux: ~30 sec

## Logs and Debugging

### Log Locations

```bash
# Pipeline execution log
logs/job_20241120_001.log

# Stage-specific logs (if --debug used)
out/2024/11/20/rpatel/001/logs/demux.log
out/2024/11/20/rpatel/001/logs/asr.log
out/2024/11/20/rpatel/001/logs/translation.log
```

### Enable Debug Logging

```bash
# Debug mode shows detailed stage execution
./run-pipeline.sh -j job_20241120_001 --debug
```

### Inspect Intermediate Files

```bash
# Check audio extraction
ffprobe out/2024/11/20/rpatel/001/audio/audio.wav

# Check raw ASR output
cat out/2024/11/20/rpatel/001/transcripts/raw_transcript.json | jq

# Check aligned output
cat out/2024/11/20/rpatel/001/transcripts/aligned_transcript.json | jq
```

## See Also

- [Prepare Job Guide](PREPARE_JOB.md) - Job configuration
- [Bootstrap Guide](BOOTSTRAP.md) - Environment setup
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

---

## Related Documents

### Core Architecture
- **[System Architecture](architecture.md)** - Overall system design and architecture
- **[Multi-Environment Setup](multi-environment.md)** - Virtual environment isolation
- **[Architecture Index](../ARCHITECTURE_INDEX.md)** - Complete documentation index

### Development & Standards
- **[Developer Standards](../developer/DEVELOPER_STANDARDS.md)** - Code patterns and best practices
- **[Code Examples](../CODE_EXAMPLES.md)** - Practical implementation examples

### Logging & Monitoring
- **[Stage Logging Architecture](../logging/STAGE_LOGGING_ARCHITECTURE.md)** - Per-stage logging patterns
- **[Logging Architecture](../logging/LOGGING_ARCHITECTURE.md)** - Main logging design

**Last Updated:** December 3, 2025
