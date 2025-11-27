# CP-WhisperX Workflows Guide

**Date**: 2025-11-18  
**Purpose**: Complete guide to transcribe and translate workflows

---

## Overview

CP-WhisperX provides two distinct workflows for processing Indian language audio:

1. **Transcribe Workflow**: Audio → Text (in source language)
2. **Translate Workflow**: Text → Text + Subtitles (source → target language)

---

## Workflow 1: Transcribe

### Purpose
Convert Indian language audio to text transcripts **in the same source language**.

### Input
- Audio/Video file with Indian language speech
- Supported formats: MP4, MKV, AVI, MOV, etc.

### Output
- **Transcript JSON** with word-level timestamps
- Location: `out/YYYY/MM/DD/USERID/counter/transcripts/segments.json`
- Content: Text in **source language** with timing information

### Process

```bash
# Prepare transcribe job
./prepare-job.sh "movie.mp4" --transcribe -s hi

# Run pipeline
./run-pipeline.sh -j job-20251118-rpatel-0001
```

### Stages

1. **Demux** (Audio Extraction)
   - Extracts audio from video file
   - Converts to 16kHz mono WAV
   - Output: `media/audio.wav`

2. **ASR** (Automatic Speech Recognition)
   - Uses WhisperX with MLX acceleration (Apple Silicon)
   - Transcribes audio to source language text
   - Output: Initial segments with timestamps

3. **Alignment** (Word-Level Timestamps)
   - Generates precise word-level timestamps
   - Output: `transcripts/segments.json`

### Example

**Input**: Hindi movie audio  
**Output**: Hindi text transcript

```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "नमस्ते, आप कैसे हैं?",
      "words": [
        {"word": "नमस्ते", "start": 0.0, "end": 0.8},
        {"word": "आप", "start": 1.0, "end": 1.2},
        {"word": "कैसे", "start": 1.3, "end": 1.7},
        {"word": "हैं", "start": 1.8, "end": 2.0}
      ]
    }
  ]
}
```

### Supported Languages (Source)

**22 Indian Languages**:
- Hindi (hi), Tamil (ta), Telugu (te), Bengali (bn)
- Gujarati (gu), Kannada (kn), Malayalam (ml), Marathi (mr)
- Punjabi (pa), Urdu (ur), Assamese (as), Odia (or)
- Nepali (ne), Sindhi (sd), Sinhala (si), Sanskrit (sa)
- Kashmiri (ks), Dogri (doi), Manipuri (mni), Konkani (kok)
- Maithili (mai), Santali (sat)

---

## Workflow 2: Translate

### Purpose
Translate transcript text from source language to target language and generate subtitle files.

### Input
- **Transcript JSON** from Transcribe workflow (segments.json)
- Must have completed Transcribe workflow first

### Output
- **Translated Transcript**: Text in target language
- **Subtitle File**: .srt format in target language
- Location: `out/YYYY/MM/DD/USERID/counter/subtitles/output.srt`

### Process

```bash
# Prepare translate job (requires existing transcript)
./prepare-job.sh "movie.mp4" --translate -s hi -t en

# Run pipeline
./run-pipeline.sh -j job-20251118-rpatel-0002
```

### Stages

1. **Load Transcript**
   - Reads segments.json from transcribe workflow
   - Validates transcript format
   - Extracts text segments

2. **IndicTrans2 Translation**
   - Translates each text segment
   - Uses IndicTrans2 model (state-of-the-art for Indian languages)
   - Preserves timing information
   - Output: Translated segments

3. **Subtitle Generation**
   - Creates .srt subtitle file
   - Formats with proper timing codes
   - Output: `subtitles/output.srt`

### Example

**Input**: Hindi transcript (from Transcribe workflow)
```
"नमस्ते, आप कैसे हैं?"
```

**Output**: English subtitle file (.srt)
```
1
00:00:00,000 --> 00:00:03,500
Hello, how are you?
```

### Supported Languages

**Source**: Any of the 22 Indian languages  
**Target**: Primarily English (en), also supports other non-Indic languages

**Common Translation Pairs**:
- Hindi → English (hi → en)
- Tamil → English (ta → en)
- Telugu → English (te → en)
- Bengali → English (bn → en)
- And all other Indian languages → English

---

## Complete End-to-End Workflow

### Scenario: Process Hindi Movie with English Subtitles

#### Step 1: Transcribe Hindi Audio → Hindi Text

```bash
# Prepare transcribe job
./prepare-job.sh "hindi-movie.mp4" --transcribe -s hi

# Output shows job ID
Job created: job-20251118-rpatel-0001
Job directory: out/2025/11/18/rpatel/1

# Run transcribe pipeline
./run-pipeline.sh -j job-20251118-rpatel-0001

# Check output
ls out/2025/11/18/rpatel/1/transcripts/
segments.json  # Hindi text with timestamps
```

#### Step 2: Translate Hindi Text → English Subtitles

```bash
# Prepare translate job
./prepare-job.sh "hindi-movie.mp4" --translate -s hi -t en

# Output shows job ID
Job created: job-20251118-rpatel-0002
Job directory: out/2025/11/18/rpatel/2

# Run translate pipeline
./run-pipeline.sh -j job-20251118-rpatel-0002

# Check output
ls out/2025/11/18/rpatel/2/subtitles/
output.srt     # English subtitles ready to use!
```

#### Step 3: Use Subtitles

```bash
# Copy subtitle file to video location
cp out/2025/11/18/rpatel/2/subtitles/output.srt hindi-movie.en.srt

# Play with subtitles
mpv hindi-movie.mp4 --sub-file=hindi-movie.en.srt
```

---

## Workflow Comparison

| Aspect | Transcribe Workflow | Translate Workflow |
|--------|-------------------|-------------------|
| **Input** | Audio/Video file | Transcript JSON |
| **Output** | Source language transcript | Target language subtitles |
| **Stages** | 3 (Demux → ASR → Alignment) | 3 (Load → Translate → Subtitle) |
| **Duration** | Longer (processes audio) | Faster (text-only) |
| **Dependency** | None | Requires Transcribe first |
| **Example** | Hindi audio → Hindi text | Hindi text → English .srt |

---

## File Outputs

### Transcribe Workflow Output Structure

```
out/2025/11/18/rpatel/1/
├── job.json                    # Job metadata
├── manifest.json               # Stage status
├── .job-20251118-rpatel-0001.env
├── logs/
│   └── pipeline.log
├── media/
│   ├── movie.mp4              # Original or clipped video
│   └── audio.wav              # Extracted audio
└── transcripts/
    └── segments.json          # Hindi text with timestamps ⭐
```

### Translate Workflow Output Structure

```
out/2025/11/18/rpatel/2/
├── job.json                    # Job metadata
├── manifest.json               # Stage status
├── .job-20251118-rpatel-0002.env
├── logs/
│   └── pipeline.log
├── transcripts/
│   └── translated.json        # English text (intermediate)
└── subtitles/
    └── output.srt             # English subtitles ⭐
```

---

## Common Use Cases

### Use Case 1: Quick Test (5-minute clip)

```bash
# Test transcribe on 5-minute clip
./prepare-job.sh movie.mp4 --transcribe -s hi \
  --start-time 00:10:00 --end-time 00:15:00

./run-pipeline.sh -j job-20251118-rpatel-0001

# Test translate
./prepare-job.sh movie.mp4 --translate -s hi -t en

./run-pipeline.sh -j job-20251118-rpatel-0002
```

### Use Case 2: Multiple Languages

```bash
# Tamil movie → English subtitles
./prepare-job.sh tamil-movie.mp4 --transcribe -s ta
./run-pipeline.sh -j job-20251118-rpatel-0001

./prepare-job.sh tamil-movie.mp4 --translate -s ta -t en
./run-pipeline.sh -j job-20251118-rpatel-0002

# Telugu movie → English subtitles
./prepare-job.sh telugu-movie.mp4 --transcribe -s te
./run-pipeline.sh -j job-20251118-rpatel-0003

./prepare-job.sh telugu-movie.mp4 --translate -s te -t en
./run-pipeline.sh -j job-20251118-rpatel-0004
```

### Use Case 3: Batch Processing

```bash
# Process multiple movies
for movie in movies/*.mp4; do
  echo "Processing: $movie"
  
  # Transcribe
  ./prepare-job.sh "$movie" --transcribe -s hi
  job1=$(grep "Job created:" | tail -1 | cut -d: -f2 | xargs)
  ./run-pipeline.sh -j $job1
  
  # Translate
  ./prepare-job.sh "$movie" --translate -s hi -t en
  job2=$(grep "Job created:" | tail -1 | cut -d: -f2 | xargs)
  ./run-pipeline.sh -j $job2
done
```

---

## Troubleshooting

### Issue: "Transcript not found" during Translate

**Cause**: Translate workflow requires transcript from Transcribe workflow

**Solution**: Run Transcribe workflow first
```bash
# Step 1: Transcribe (creates transcript)
./prepare-job.sh movie.mp4 --transcribe -s hi
./run-pipeline.sh -j job-20251118-rpatel-0001

# Step 2: Translate (uses transcript from step 1)
./prepare-job.sh movie.mp4 --translate -s hi -t en
./run-pipeline.sh -j job-20251118-rpatel-0002
```

### Issue: "IndicTrans2 not available"

**Cause**: IndicTrans2 model not installed

**Solution**: Install IndicTrans2
```bash
./install-indictrans2.sh
```

### Issue: MLX model error (404 Not Found)

**Cause**: Model name mapping issue

**Solution**: Already fixed in scripts/run-pipeline.py
- Automatic mapping: large-v3 → mlx-community/whisper-large-v3-mlx

---

## Performance Tips

### Apple Silicon (M1/M2/M3)

1. **Use MLX acceleration** (automatic with bootstrap)
   - 12-15x faster than CPU
   - Requires: `./install-mlx.sh`

2. **Optimize batch size** (auto-detected)
   - Default: 2 for large-v3 model
   - Balances speed and memory

### General Tips

1. **Test with clips first**
   ```bash
   ./prepare-job.sh movie.mp4 --transcribe -s hi \
     --start-time 00:10:00 --end-time 00:15:00
   ```

2. **Monitor logs**
   ```bash
   tail -f out/YYYY/MM/DD/USERID/counter/logs/pipeline.log
   ```

3. **Check job status**
   ```bash
   ./scripts/pipeline-status.sh job-20251118-rpatel-0001
   ```

---

## Summary

**Two Workflows, One Goal**:
1. **Transcribe**: Convert audio to text (source language)
2. **Translate**: Convert text to subtitles (target language)

**Typical Flow**:
```
Audio (Hindi) 
   ↓ [Transcribe Workflow]
Text (Hindi)
   ↓ [Translate Workflow]
Subtitles (English)
```

**Remember**:
- Transcribe produces **source language** text
- Translate produces **target language** subtitles
- Always run Transcribe before Translate
- Both workflows are separate, sequential steps

For more information:
- Architecture: `docs/INDICTRANS2_ARCHITECTURE.md`
- Directory Structure: `docs/DIRECTORY_STRUCTURE_CHANGE.md`
- Main README: `README.md`
