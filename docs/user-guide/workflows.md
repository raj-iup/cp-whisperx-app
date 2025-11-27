# Workflows Guide

Complete guide to transcribe, translate, and subtitle workflows in CP-WhisperX-App.

## Table of Contents

1. [Overview](#overview)
2. [Transcribe Workflow](#transcribe-workflow)
3. [Translate Workflow](#translate-workflow)
4. [Subtitle Workflow](#subtitle-workflow)
5. [Advanced Usage](#advanced-usage)
6. [Workflow Patterns](#workflow-patterns)

---

## Overview

CP-WhisperX-App supports three main workflows:

| Workflow | Input | Output | Use Case |
|----------|-------|--------|----------|
| **Transcribe** | Audio/Video | Source text transcript | ASR only |
| **Translate** | Transcript | Target language text(s) | Translation only |
| **Subtitle** | Audio/Video | Video with embedded subtitles | Complete pipeline |

### Workflow Chaining

Workflows can auto-execute prerequisites:

```
subtitle → requires → translate → requires → transcribe
```

If you run `--subtitle` without existing transcript, pipeline auto-executes `transcribe` → `translate` → `subtitle`.

---

## Transcribe Workflow

Convert audio to text in source language with word-level timestamps.

### Basic Usage

```bash
./prepare-job.sh input.mp4 --transcribe -s hi
```

### Full Example

```bash
./prepare-job.sh "Jaane Tu Ya Jaane Na 2008.mp4" \
  --transcribe \
  --source-language hi \
  --start-time 00:10:00 \
  --end-time 00:15:00 \
  --debug
```

### Workflow Stages

```
1. DEMUX (venv/common)
   ├─ Extract audio from video
   ├─ Apply time clipping if specified
   └─ Output: audio.wav (16kHz mono)

2. ASR (venv/whisperx or venv/mlx)
   ├─ Load Whisper model (large-v3)
   ├─ Transcribe audio with timestamps
   ├─ Detect language if not specified
   └─ Output: segments.json (raw WhisperX output)

3. ALIGNMENT (venv/whisperx)
   ├─ Load language-specific alignment model
   ├─ Generate word-level timestamps
   └─ Output: segments.json (updated with word timings)

4. EXPORT (venv/common)
   ├─ Convert segments to readable format
   └─ Output: transcript.txt
```

### Output Files

```
out/2025/11/20/username/1/
├── media/
│   ├── audio.wav                    # Extracted audio
│   └── Jaane Tu Ya Jaane Na 2008.mp4  # Original or clipped video
├── transcripts/
│   ├── segments.json                # WhisperX segments with timestamps
│   └── transcript.txt               # Human-readable transcript
└── logs/
    ├── 99_pipeline.log              # Main pipeline log
    ├── 01_demux.log                 # Demux stage log
    ├── 02_asr.log                   # ASR stage log
    └── 03_alignment.log             # Alignment stage log
```

### segments.json Format

```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "नमस्ते, मेरा नाम राज है",
      "words": [
        {"word": "नमस्ते", "start": 0.0, "end": 0.5},
        {"word": "मेरा", "start": 0.6, "end": 0.9},
        {"word": "नाम", "start": 1.0, "end": 1.3},
        {"word": "राज", "start": 1.4, "end": 1.7},
        {"word": "है", "start": 1.8, "end": 2.5}
      ]
    }
  ],
  "language": "hi"
}
```

### Supported Languages

All WhisperX-supported languages (90+), optimized for:
- **Indic**: hi, ta, te, bn, gu, kn, ml, mr, pa, ur, as, or, ne, etc.
- **European**: en, es, fr, de, it, pt, nl, pl, ru, etc.
- **Asian**: zh, ja, ko, th, vi, id, ms, etc.

---

## Translate Workflow

Translate existing transcript to one or more target languages.

### Basic Usage

```bash
# Single target language
./prepare-job.sh input.mp4 --translate -s hi -t en

# Multiple target languages (one-to-many)
./prepare-job.sh input.mp4 --translate -s hi -t en,gu,es
```

### Translation Routing

Pipeline automatically routes to appropriate translation engine:

#### Indic → English

```bash
./prepare-job.sh movie.mp4 --translate -s hi -t en
```

- **Engine**: IndicTrans2-en
- **Environment**: `venv/indictrans2`
- **Model**: AI4Bharat/indictrans2-en-1B
- **Quality**: Specialized for Indic languages

#### Indic → Indic

```bash
./prepare-job.sh movie.mp4 --translate -s hi -t gu
```

- **Engine**: IndicTrans2-indic
- **Environment**: `.venv-indic-indic`
- **Model**: AI4Bharat/indictrans2-indic-1B
- **Quality**: Best for Indic-to-Indic pairs

#### English → Non-Indic

```bash
./prepare-job.sh movie.mp4 --translate -s en -t es
```

- **Engine**: NLLB-200
- **Environment**: `venv/nllb`
- **Model**: facebook/nllb-200-distilled-600M
- **Coverage**: 200+ languages

#### Indic → Non-Indic (Pivot Translation)

```bash
./prepare-job.sh movie.mp4 --translate -s hi -t es
```

- **Step 1**: Hindi → English (IndicTrans2-en)
- **Step 2**: English → Spanish (NLLB-200)
- **Note**: Uses English as pivot language

### Workflow Stages

```
1. LOAD_TRANSCRIPT (venv/common)
   ├─ Load segments.json from transcribe workflow
   ├─ Extract source language text
   └─ Prepare for translation

2. TRANSLATION (environment depends on language pair)
   ├─ Route to appropriate engine
   ├─ Translate segment by segment
   ├─ Preserve timestamps
   └─ Output: segments_translated_{target}.json

3. GENERATE_SRT (venv/common)
   ├─ Convert translated segments to SRT format
   ├─ Format timestamps (HH:MM:SS,mmm)
   └─ Output: subtitle_{target}.srt

4. EXPORT (venv/common)
   └─ Output: transcript_{target}.txt
```

### One-to-Many Translation

Generate multiple target languages in single run:

```bash
./prepare-job.sh movie.mp4 --translate -s hi -t en,gu,es,ar
```

**Execution**:
1. Hindi → English (IndicTrans2-en in `venv/indictrans2`)
2. Hindi → Gujarati (IndicTrans2-indic in `.venv-indic-indic`)
3. Hindi → English → Spanish (IndicTrans2 + NLLB in both environments)
4. Hindi → English → Arabic (IndicTrans2 + NLLB in both environments)

**Output**: 4 transcript files + 4 SRT files

---

## Subtitle Workflow

Complete end-to-end pipeline: transcribe → translate → generate subtitles → embed in video.

### Basic Usage

```bash
./prepare-job.sh input.mp4 --subtitle -s hi -t en
```

### Full Example with Clipping

```bash
./prepare-job.sh "Jaane Tu Ya Jaane Na 2008.mp4" \
  --subtitle \
  --source-language hi \
  --target-language en,gu \
  --start-time 00:06:00 \
  --end-time 00:08:30 \
  --debug
```

This generates:
- English subtitles (soft-embedded, track 1)
- Gujarati subtitles (soft-embedded, track 2)
- Video file with both subtitle tracks

### Workflow Stages

```
1. TRANSCRIBE (if not exists)
   └─ See Transcribe Workflow stages above

2. TRANSLATE (for each target language)
   └─ See Translate Workflow stages above

3. MUX (venv/common)
   ├─ Load original/clipped video
   ├─ Soft-embed all subtitle tracks
   ├─ Set metadata (language codes, track names)
   ├─ Output: video_with_subtitles.mp4
   └─ Preserve original video quality
```

### Soft Subtitle Embedding

Pipeline uses FFmpeg to soft-embed subtitles (not burned in):

```bash
ffmpeg -i video.mp4 \
  -i subtitle_en.srt -i subtitle_gu.srt \
  -map 0:v -map 0:a -map 1 -map 2 \
  -c copy \
  -metadata:s:s:0 language=eng -metadata:s:s:0 title="English" \
  -metadata:s:s:1 language=guj -metadata:s:s:1 title="Gujarati" \
  output.mp4
```

**Benefits**:
- Subtitles can be toggled on/off in video player
- Multiple subtitle tracks available
- No quality loss (video not re-encoded)
- Smaller file size than hard subtitles

### Output Files

```
out/2025/11/20/username/2/
├── media/
│   ├── audio.wav
│   ├── Jaane Tu Ya Jaane Na 2008.mp4                      # Original clip
│   └── Jaane Tu Ya Jaane Na 2008_subtitled.mp4            # With subtitles
├── transcripts/
│   ├── segments.json
│   ├── transcript.txt                                      # Hindi (source)
│   ├── transcript_en.txt                                   # English
│   └── transcript_gu.txt                                   # Gujarati
├── subtitles/
│   ├── subtitle_en.srt                                     # English SRT
│   └── subtitle_gu.srt                                     # Gujarati SRT
└── logs/
    ├── 99_pipeline.log
    ├── 03_indictrans2_en.log
    ├── 04_indictrans2_gu.log
    └── 05_mux.log
```

---

## Advanced Usage

### Time Clipping

Process specific time ranges for testing:

```bash
./prepare-job.sh movie.mp4 --subtitle -s hi -t en \
  --start-time 00:10:30 \
  --end-time 00:15:45
```

### Debug Mode

Enable verbose logging:

```bash
./prepare-job.sh movie.mp4 --transcribe -s hi --debug
```

**Debug output**:
- FFmpeg commands and output
- Model loading progress
- Segment-by-segment processing
- Full error stack traces

### Resume Failed Jobs

Continue from last successful stage:

```bash
./run-pipeline.sh -j job-20251120-username-0001 --resume
```

### Check Job Status

```bash
./run-pipeline.sh -j job-20251120-username-0001 --status
```

---

## Workflow Patterns

### Pattern 1: Quick Test on Clip

```bash
# Test 2-minute clip
./prepare-job.sh movie.mp4 --subtitle -s hi -t en \
  --start-time 00:10:00 --end-time 00:12:00 --debug
```

### Pattern 2: Multi-Language Subtitles

```bash
# Generate subtitles in 4 languages
./prepare-job.sh movie.mp4 --subtitle -s hi -t en,gu,es,ar
```

### Pattern 3: Transcribe Once, Translate Multiple Times

```bash
# Step 1: Transcribe (slow, run once)
./prepare-job.sh movie.mp4 --transcribe -s hi

# Step 2: Translate to English
./prepare-job.sh movie.mp4 --translate -s hi -t en

# Step 3: Translate to Gujarati (reuses transcript)
./prepare-job.sh movie.mp4 --translate -s hi -t gu

# Step 4: Generate subtitles for both
./prepare-job.sh movie.mp4 --subtitle -s hi -t en,gu
```

### Pattern 4: Batch Processing

```bash
# Process multiple files
for file in in/*.mp4; do
  ./prepare-job.sh "$file" --subtitle -s hi -t en
done
```

---

## Troubleshooting

### Issue: "Transcript not found"

**Solution**: Run transcribe workflow first:
```bash
./prepare-job.sh movie.mp4 --transcribe -s hi
./prepare-job.sh movie.mp4 --translate -s hi -t en
```

### Issue: "IndicTrans2 does not support hi→gu"

**Solution**: Install Indic→Indic environment:
```bash
./bootstrap.sh  # Installs .venv-indic-indic
```

### Issue: "Requested float16 compute type... not supported"

**Solution**: Pipeline auto-fixes this. If error persists, check `job.json` compute type is `int8` for CPU.

### Issue: "FFmpeg not found"

**Solution**: Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

---

## Performance Tips

1. **Use GPU**: CUDA/MPS significantly faster than CPU
2. **Clip for testing**: Use `--start-time`/`--end-time` for quick tests
3. **Batch processing**: Process multiple files to amortize model loading
4. **Resume capability**: Use `--resume` to avoid reprocessing completed stages

---

**Next Steps**:
- [Pipeline Execution Details](PIPELINE_EXECUTION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Configuration Reference](CONFIGURATION.md)
