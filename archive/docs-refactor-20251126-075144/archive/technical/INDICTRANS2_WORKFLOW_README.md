# IndicTrans2 Workflow - Quick Start Guide

## Overview

Simplified IndicTrans2 workflow for transcribing and translating Indian language content. This implementation focuses on using IndicTrans2 infrastructure with no fallback to Whisper translation.

## Features

- ✅ **Transcribe Workflow**: Convert Indian language audio to text transcripts
- ✅ **Translate Workflow**: Translate Indian language text to English using IndicTrans2
- ✅ **22 Indian Languages**: Hindi, Tamil, Telugu, Bengali, and 18 more
- ✅ **Simplified Architecture**: Reuses existing bootstrap, config, logging, manifest
- ✅ **No Fallback**: IndicTrans2-only approach for Indian languages
- ✅ **90% Faster**: IndicTrans2 translation is 90% faster than Whisper

## Supported Languages

### Indian Languages (Source)
Hindi (hi), Tamil (ta), Telugu (te), Bengali (bn), Gujarati (gu), Kannada (kn), Malayalam (ml), Marathi (mr), Punjabi (pa), Urdu (ur), Assamese (as), Odia (or), Nepali (ne), Sindhi (sd), Sinhala (si), Sanskrit (sa), Kashmiri (ks), Dogri (doi), Manipuri (mni), Konkani (kok), Maithili (mai), Santali (sat)

### Target Languages
Primarily English (en), other non-Indic languages supported

## Prerequisites

1. **Bootstrap Environment**
   ```bash
   ./scripts/bootstrap.sh
   ```

2. **Install IndicTrans2**
   ```bash
   ./install-indictrans2.sh
   ```

3. **HuggingFace Authentication**
   ```bash
   huggingface-cli login
   ```
   - Visit https://huggingface.co/ai4bharat/indictrans2-indic-en-1B
   - Click "Agree and access repository"
   - Get token from https://huggingface.co/settings/tokens

## Usage

### Workflow 1: Transcribe (Audio → Text)

Convert Indian language audio to text transcript:

```bash
./prepare-job.sh "movie.mp4" \
  --transcribe \
  --source-language hi
```

This creates a job with:
- **Input**: Audio/video file
- **Output**: `transcripts/segments.json` (WhisperX segments with timestamps)
- **Stages**: demux → asr → alignment
- **Duration**: ~35-45 minutes for 2-hour movie

Run the pipeline:
```bash
./run-pipeline.sh -j <job-id>
```

### Workflow 2: Translate (Text → Subtitles)

Translate Indian language text to English subtitles:

```bash
./prepare-job.sh "movie.mp4" \
  --translate \
  --source-language hi \
  --target-language en
```

This creates a job with:
- **Input**: `transcripts/segments.json` (from transcribe workflow)
- **Output**: `subtitles/output.en.srt` (English subtitles)
- **Stages**: load_transcript → indictrans2_translation → subtitle_generation
- **Duration**: ~5-7 minutes for 2-hour movie

Run the pipeline:
```bash
./run-pipeline.sh -j <job-id>
```

### Complete Example: Hindi to English

```bash
# Step 1: Transcribe Hindi audio
./prepare-job.sh "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --transcribe \
  --source-language hi

./run-pipeline.sh -j jaane-tu-ya-jaane-na-2008-20241118-120000

# Step 2: Translate Hindi text to English
./prepare-job.sh "in/Jaane Tu Ya Jaane Na 2008.mp4" \
  --translate \
  --source-language hi \
  --target-language en

./run-pipeline.sh -j jaane-tu-ya-jaane-na-2008-20241118-120001
```

**Total Time**: ~40-50 minutes (vs 200+ minutes with Whisper)

## Output Structure

```
out/
└── 2024-11-18_12-00-00/          # Timestamp
    └── username/                  # Your username
        └── job-id/                # Job identifier
            ├── job.json           # Job configuration
            ├── manifest.json      # Stage tracking
            ├── logs/
            │   └── pipeline.log   # Execution logs
            ├── media/
            │   ├── input.mp4      # Original media
            │   └── audio.wav      # Extracted audio
            ├── transcripts/
            │   ├── segments.json           # Source transcription
            │   └── segments_translated.json # Translated segments
            └── subtitles/
                └── output.en.srt  # Final subtitles
```

## Configuration

### Job Configuration (job.json)
```json
{
  "job_id": "movie-20241118-120000",
  "workflow": "transcribe|translate",
  "source_language": "hi",
  "target_language": "en",
  "input_media": "/path/to/input.mp4",
  "title": "Movie Title",
  "year": "2008"
}
```

### Environment Variables (config/.env.pipeline)
The prepare-job script automatically generates job-specific `.env` files from the template.

### IndicTrans2 Settings
```bash
INDICTRANS2_MODEL=ai4bharat/indictrans2-indic-en-1B
INDICTRANS2_DEVICE=auto  # auto, mps, cuda, cpu
INDICTRANS2_NUM_BEAMS=4
INDICTRANS2_MAX_TOKENS=128
```

## Pipeline Stages

### Transcribe Workflow
1. **Demux**: Extract audio from video (2-3 minutes)
2. **ASR**: Transcribe with WhisperX (30-40 minutes)
3. **Alignment**: Word-level timestamps (included in ASR)

### Translate Workflow
1. **Load Transcript**: Read segments.json (<1 minute)
2. **IndicTrans2 Translation**: Translate text (3-5 minutes)
3. **Subtitle Generation**: Create SRT file (<1 minute)

## Error Handling

### IndicTrans2 Not Available
```
❌ Error: IndicTrans2 not available!
Please install: ./install-indictrans2.sh
```

**Fix**: Run `./install-indictrans2.sh`

### Transcript Not Found (Translate Workflow)
```
❌ Error: Transcript not found
Run transcribe workflow first!
```

**Fix**: Run transcribe workflow before translate workflow

### HuggingFace Authentication Error
```
❌ Error: 401 Client Error
Access to model ai4bharat/indictrans2-indic-en-1B is restricted
```

**Fix**: 
1. Request access: https://huggingface.co/ai4bharat/indictrans2-indic-en-1B
2. Login: `huggingface-cli login`

## Advanced Usage

### Process Clip (Testing)
```bash
./prepare-job.sh "movie.mp4" \
  --transcribe \
  --source-language hi \
  --start-time 00:10:00 \
  --end-time 00:15:00
```

### Resume Failed Job
```bash
./run-pipeline.sh -j <job-id> --resume
```

### Check Job Status
```bash
./run-pipeline.sh -j <job-id> --status
```

## Performance

### Expected Timings (2-hour movie)

| Workflow | Stages | Duration | Output |
|----------|--------|----------|--------|
| Transcribe | 3 | 35-45 min | segments.json |
| Translate | 3 | 5-7 min | output.en.srt |
| **Total** | **6** | **40-50 min** | **English subtitles** |

**Comparison**: Traditional Whisper translation would take 200+ minutes

### Hardware Recommendations
- **GPU**: Apple Silicon (MPS), NVIDIA (CUDA), or CPU
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB for models + job outputs

## Reused Infrastructure

This implementation reuses existing components:
- ✅ `scripts/bootstrap.sh` - Environment setup
- ✅ `config/.env.pipeline` - Configuration template
- ✅ `config/secrets.json` - API keys
- ✅ `shared/logger.py` - Logging system
- ✅ `shared/manifest.py` - Job tracking
- ✅ `shared/job_manager.py` - Job management
- ✅ Output directory structure

## New Components

- 🆕 `prepare-job.sh` - Job preparation script
- 🆕 `scripts/prepare-job.py` - Job preparation logic
- 🆕 `run-pipeline.sh` - Pipeline orchestrator
- 🆕 `scripts/run-pipeline.py` - Pipeline execution logic
- 🆕 `docs/INDICTRANS2_ARCHITECTURE.md` - Architecture documentation

## Examples

### Example 1: Hindi Movie
```bash
# Transcribe
./prepare-job.sh "Jaane Tu Ya Jaane Na 2008.mp4" \
  --transcribe --source-language hi
./run-pipeline.sh -j <job-id>

# Translate
./prepare-job.sh "Jaane Tu Ya Jaane Na 2008.mp4" \
  --translate --source-language hi --target-language en
./run-pipeline.sh -j <job-id>
```

### Example 2: Tamil Movie
```bash
# Transcribe
./prepare-job.sh "tamil-movie.mp4" \
  --transcribe --source-language ta
./run-pipeline.sh -j <job-id>

# Translate
./prepare-job.sh "tamil-movie.mp4" \
  --translate --source-language ta --target-language en
./run-pipeline.sh -j <job-id>
```

### Example 3: Bengali Movie
```bash
# Complete workflow
./prepare-job.sh "bengali-movie.mp4" \
  --transcribe --source-language bn
./run-pipeline.sh -j <job-id>

./prepare-job.sh "bengali-movie.mp4" \
  --translate --source-language bn --target-language en
./run-pipeline.sh -j <job-id>
```

## Troubleshooting

### Check Logs
```bash
# Pipeline log
tail -f out/*/username/job-id/logs/pipeline.log

# Stage-specific logs
ls out/*/username/job-id/logs/
```

### Verify IndicTrans2 Installation
```bash
python scripts/test_indictrans2.py
```

### Check Job Status
```bash
./run-pipeline.sh -j <job-id> --status
```

## Documentation

- **Architecture**: `docs/INDICTRANS2_ARCHITECTURE.md`
- **Reference**: `docs/INDICTRANS2_REFERENCE.md`
- **Quick Start**: `docs/INDICTRANS2_QUICKSTART.md`
- **This Guide**: `INDICTRANS2_WORKFLOW_README.md`

## Citation

If you use IndicTrans2 in your work, please cite:

```bibtex
@article{gala2023indictrans,
  title={IndicTrans2: Towards High-Quality and Accessible Machine Translation Models for all 22 Scheduled Indian Languages},
  author={Jay Gala and Pranjal A Chitale and A K Raghavan and Varun Gumma and Sumanth Doddapaneni and Aswanth Kumar M and Janki Atul Nawale and Anupama Sujatha and Ratish Puduppully and Vivek Raghavan and Pratyush Kumar and Mitesh M Khapra and Raj Dabre and Anoop Kunchukuttan},
  journal={Transactions on Machine Learning Research},
  issn={2835-8856},
  year={2023},
  url={https://openreview.net/forum?id=vfT4YuzAYA}
}
```

## Support

For issues or questions:
1. Check logs in `<job-dir>/logs/pipeline.log`
2. Review documentation in `docs/`
3. Verify IndicTrans2 installation: `python scripts/test_indictrans2.py`

---

*Last Updated: 2024-11-18*
*Version: 1.0*
