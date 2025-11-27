# IndicTrans2 Workflow Architecture

## Overview

This document describes the simplified architecture for the IndicTrans2 workflow, focused on transcription and translation of Indian language content using the IndicTrans2 model.

## Design Principles

1. **Simplified Architecture**: Reuse existing infrastructure (bootstrap, config, logging, manifest)
2. **IndicTrans2-First**: No fallback to Whisper translation - IndicTrans2 or nothing
3. **Clear Workflows**: Separate transcribe and translate workflows
4. **Existing Artifacts**: Leverage config/.env.pipeline, config/secrets.json, logging, manifest, out/ directory structure

## Supported Workflows

### 1. Transcribe Workflow
**Purpose**: Convert Indian language audio to text transcripts

**Input**: Audio/Video file with Indian language speech
**Output**: Transcript JSON with word-level timestamps

**Languages Supported** (Source):
- Hindi (hi), Tamil (ta), Telugu (te), Bengali (bn)
- Gujarati (gu), Kannada (kn), Malayalam (ml), Marathi (mr)
- Punjabi (pa), Urdu (ur), Assamese (as), Odia (or)
- Nepali (ne), Sindhi (sd), Sinhala (si), Sanskrit (sa)
- Kashmiri (ks), Dogri (doi), Manipuri (mni), Konkani (kok)
- Maithili (mai), Santali (sat)

**Stages**:
1. **Demux**: Extract audio from video
2. **ASR (WhisperX)**: Transcribe audio to Indian language text
3. **Alignment**: Generate word-level timestamps

**Exit Condition**: If ASR fails or language not supported, pipeline stops with error

### 2. Translate Workflow
**Purpose**: Translate Indian language transcripts to English or other languages

**Input**: Transcript JSON from transcribe workflow
**Output**: Translated SRT subtitle file

**Languages Supported**:
- **Source**: Any of the 22 Indian languages above
- **Target**: Primarily English (en), other non-Indic languages supported

**Stages**:
1. **Load Transcript**: Read segments.json from transcribe workflow
2. **IndicTrans2 Translation**: Translate text using IndicTrans2 model
3. **Subtitle Generation**: Create SRT file with translated text
4. **Optional**: Video muxing with subtitles

**Exit Condition**: If IndicTrans2 unavailable or translation fails, pipeline stops with error

## Directory Structure

```
out/
└── YYYY-MM-DD_HH-MM-SS/          # Timestamp of job creation
    └── <username>/                # User who created the job
        └── <job-id>/              # Unique job identifier
            ├── job.json           # Job configuration
            ├── manifest.json      # Pipeline manifest (stages, status)
            ├── logs/              # Execution logs
            │   └── pipeline.log
            ├── media/             # Processed media
            │   ├── input.mp4
            │   └── audio.wav
            ├── transcripts/       # Transcription outputs
            │   └── segments.json  # WhisperX segments with timestamps
            └── subtitles/         # Translation outputs
                └── output.en.srt  # Translated subtitles
```

## Configuration

### Environment Variables (config/.env.pipeline)

```bash
# Job Identification
JOB_ID=<job-id>
USER_ID=<username>
WORKFLOW_MODE=transcribe|translate

# Source/Target Languages
SOURCE_LANGUAGE=hi   # Indian language code
TARGET_LANGUAGE=en   # Target language code

# IndicTrans2 Configuration
INDICTRANS2_MODEL=ai4bharat/indictrans2-indic-en-1B
INDICTRANS2_DEVICE=auto  # auto, mps, cuda, cpu
INDICTRANS2_NUM_BEAMS=4
INDICTRANS2_MAX_TOKENS=128

# Paths
INPUT_MEDIA=<path-to-input>
OUTPUT_ROOT=<output-directory>
LOG_ROOT=<log-directory>
```

### Secrets (config/secrets.json)

```json
{
  "huggingface": {
    "token": "hf_..."
  }
}
```

Note: HuggingFace token required for IndicTrans2 model access

## Logging

Uses existing `shared/logger.py` infrastructure:

- **Pipeline logs**: `logs/pipeline.log`
- **Stage logs**: `logs/stage_<stage-name>.log`
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Format**: Timestamp, level, stage, message

## Manifest

Uses existing `shared/manifest.py` infrastructure:

```json
{
  "job_id": "<job-id>",
  "workflow": "transcribe|translate",
  "source_language": "hi",
  "target_language": "en",
  "stages": [
    {
      "name": "demux",
      "status": "completed",
      "start_time": "2024-11-18T12:00:00",
      "end_time": "2024-11-18T12:05:00",
      "duration_seconds": 300
    },
    ...
  ],
  "status": "running|completed|failed",
  "created_at": "2024-11-18T12:00:00",
  "updated_at": "2024-11-18T12:30:00"
}
```

## Error Handling

### Transcribe Workflow Errors

1. **Audio extraction fails**: Stop with error
2. **ASR fails**: Stop with error (no fallback)
3. **Language detection fails**: Stop with error

### Translate Workflow Errors

1. **IndicTrans2 not available**: Stop with error (no fallback to Whisper)
2. **Translation fails**: Stop with error
3. **Input transcript missing**: Stop with error

## Usage Examples

### Example 1: Hindi to English

```bash
# Step 1: Transcribe Hindi audio
./prepare-job-indictrans2.sh "movie.mp4" --transcribe --source-language hi

# Step 2: Translate Hindi transcript to English
./prepare-job-indictrans2.sh "movie.mp4" --translate --source-language hi --target-language en
```

### Example 2: Tamil to English

```bash
# Step 1: Transcribe Tamil audio
./prepare-job-indictrans2.sh "movie.mp4" --transcribe --source-language ta

# Step 2: Translate Tamil transcript to English
./prepare-job-indictrans2.sh "movie.mp4" --translate --source-language ta --target-language en
```

## Migration from Existing System

### Reused Components
- ✅ Bootstrap scripts (`scripts/bootstrap.sh`)
- ✅ Configuration (`config/.env.pipeline`)
- ✅ Secrets (`config/secrets.json`)
- ✅ Logging (`shared/logger.py`)
- ✅ Manifest (`shared/manifest.py`)
- ✅ Job structure (`shared/job_manager.py`)
- ✅ Output directory structure

### New Components
- 🆕 `prepare-job-indictrans2.sh` - Simplified job preparation
- 🆕 `run-pipeline-indictrans2.sh` - Simplified pipeline orchestrator
- 🆕 `scripts/transcribe_indictrans2.py` - Transcription stage
- 🆕 `scripts/translate_indictrans2.py` - Translation stage

### Removed Components (Not Used)
- ❌ Whisper translation fallback
- ❌ Complex multi-stage workflows (lyrics, NER, diarization)
- ❌ TMDB enrichment
- ❌ Glossary systems
- ❌ Video muxing (optional)

## Performance

### Expected Timings (2-hour movie)

**Transcribe Workflow**:
- Demux: 2-3 minutes
- ASR: 30-40 minutes (WhisperX)
- **Total**: ~35-45 minutes

**Translate Workflow**:
- Load transcript: <1 minute
- IndicTrans2 translation: 3-5 minutes
- Subtitle generation: <1 minute
- **Total**: ~5-7 minutes

**Combined**: ~40-50 minutes (vs 200+ minutes with Whisper translation)

## Future Enhancements

1. **Batch Processing**: Process multiple files in parallel
2. **Resume Support**: Resume failed jobs from last completed stage
3. **Quality Metrics**: Track translation quality scores
4. **Additional Languages**: Support more non-Indic target languages
5. **Optimization**: GPU batching for faster translation

## References

- **IndicTrans2 Paper**: https://openreview.net/forum?id=vfT4YuzAYA
- **IndicTrans2 Model**: https://huggingface.co/ai4bharat/indictrans2-indic-en-1B
- **WhisperX**: https://github.com/m-bain/whisperX

---

*Last Updated: 2024-11-18*
*Version: 1.0*
