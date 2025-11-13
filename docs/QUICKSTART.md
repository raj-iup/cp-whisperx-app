# Quick Start Guide

Get CP-WhisperX-App running in **5 minutes**!

---

## Prerequisites

- **Python 3.11+** installed
- **20GB free disk space**
- **8GB+ RAM** (16GB recommended)
- Optional: **GPU** (Apple Silicon or NVIDIA CUDA)

---

## Step 1: Clone and Bootstrap (2 minutes)

```bash
# Clone repository
git clone https://github.com/yourusername/cp-whisperx-app.git
cd cp-whisperx-app

# Run bootstrap script
./scripts/bootstrap.sh  # macOS/Linux
# OR
.\scripts\bootstrap.ps1  # Windows
```

**What bootstrap does:**
- Creates Python virtual environment (`.bollyenv`)
- Installs all dependencies
- Detects GPU capabilities
- Creates default configuration

---

## Step 2: Configure (1 minute)

```bash
# Copy template configuration
cp config/.env.pipeline.template config/.env.pipeline

# Edit configuration (optional - defaults work fine)
nano config/.env.pipeline
```

**Minimum required settings:**
```bash
# config/.env.pipeline
HF_TOKEN=your_huggingface_token  # Get from https://huggingface.co/settings/tokens
```

**Optional: Get TMDB API key** (for cast/crew metadata):
```bash
# config/secrets.json
{
  "tmdb_api_key": "your_tmdb_api_key",  # Get from https://www.themoviedb.org/settings/api
  "hf_token": "your_huggingface_token"
}
```

---

## Step 3: Prepare a Job (30 seconds)

```bash
# Prepare a job from a video file
./prepare-job.sh /path/to/movie.mp4

# Example output:
# ✓ Created job: 20251113-0001
# ✓ Job directory: out/2025/11/13/1/20251113-0001/
# ✓ Configuration: out/2025/11/13/1/20251113-0001/.20251113-0001.env
```

**What this does:**
- Creates job directory structure
- Copies video to job input
- Generates job-specific configuration
- Parses filename for metadata (title, year, etc.)

---

## Step 4: Run the Pipeline (1-4 hours depending on hardware)

```bash
# Run the complete pipeline
./run_pipeline.sh --job 20251113-0001
```

**What happens:**
```
Stage  1/14: Demux          ✓ Completed in 45s
Stage  2/14: TMDB           ✓ Completed in 12s
Stage  3/14: Pre-NER        ✓ Completed in 8s
Stage  4/14: Silero VAD     ✓ Completed in 234s
Stage  5/14: PyAnnote VAD   ✓ Completed in 456s
Stage  6/14: Diarization    ✓ Completed in 678s
Stage  7/14: ASR            ✓ Completed in 2847s (47 min)
Stage  8/14: Glossary       ✓ Completed in 45s
Stage  9/14: Translation    ✓ Completed in 567s
Stage 10/14: Lyrics         ✓ Completed in 234s
Stage 11/14: Post-NER       ✓ Completed in 123s
Stage 12/14: Subtitles      ✓ Completed in 89s
Stage 13/14: Mux            ✓ Completed in 67s
Stage 14/14: Finalize       ✓ Completed in 12s

✅ Pipeline completed successfully!
```

**Processing time estimates (2-hour movie):**
- **CPU only**: 4-6 hours
- **Apple M2 (MPS)**: 2-3 hours  
- **NVIDIA RTX 3090**: 1.5-2 hours
- **Speed mode**: 1-1.5 hours (skip VAD/diarization)

---

## Step 5: Get Your Subtitles! (instant)

```bash
# Output directory
out/2025/11/13/1/20251113-0001/

# Subtitles
├── subtitles/
│   ├── movie.srt           ← English subtitles (SRT format)
│   └── movie.vtt           ← English subtitles (VTT format)

# Video with embedded subtitles
├── movie.with_subs.mp4     ← Video with embedded subtitles

# Intermediate outputs (for debugging)
├── 01_demux/
├── 07_asr/
│   ├── transcript.json     ← Original transcript
│   └── translation.json    ← Translated transcript
└── logs/                   ← All stage logs
```

---

## Quick Examples

### Example 1: Basic Run

```bash
./prepare-job.sh Dilwale_Dulhania_Le_Jayenge_1995.mp4
./run_pipeline.sh --job 20251113-0001
```

### Example 2: Resume Interrupted Job

```bash
# Pipeline was interrupted at stage 7 (ASR)
./run_pipeline.sh --job 20251113-0001
# Automatically resumes from stage 7
```

### Example 3: Speed Mode (Skip VAD/Diarization)

```bash
# Edit job config before running
nano out/2025/11/13/1/20251113-0001/.20251113-0001.env

# Set:
STEP_SILERO_VAD=false
STEP_PYANNOTE_VAD=false  
STEP_DIARIZATION=false

# Run (30-50% faster, single speaker assumed)
./run_pipeline.sh --job 20251113-0001
```

### Example 4: Specific Stages Only

```bash
# Run only ASR and subtitle generation
./run_pipeline.sh --job 20251113-0001 --stages "asr subtitle_gen"
```

---

## Verification

### Check Logs

```bash
# View orchestrator log
tail -f out/2025/11/13/1/20251113-0001/logs/00_orchestrator_*.log

# View specific stage log (e.g., ASR)
cat out/2025/11/13/1/20251113-0001/logs/07_asr_*.log
```

### Check Output Quality

```bash
# View generated subtitles
cat out/2025/11/13/1/20251113-0001/subtitles/movie.srt | head -20

# Check bias prompting was active
grep "🎯 Active bias prompting" out/*/logs/07_asr_*.log

# Check transcript
jq '.segments[:5]' out/2025/11/13/1/20251113-0001/07_asr/transcript.json
```

---

## Troubleshooting

### Issue: Python version error

```bash
# Solution: Use Python 3.11+
python3.11 -m venv .bollyenv
source .bollyenv/bin/activate
pip install -r requirements.txt
```

### Issue: GPU not detected

```bash
# Check GPU availability
python3 -c "import torch; print('MPS:', torch.backends.mps.is_available())"
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Force CPU if needed
export DEVICE=cpu
./run_pipeline.sh --job <job-id>
```

### Issue: HuggingFace token error

```bash
# Get token from https://huggingface.co/settings/tokens
export HF_TOKEN=your_token_here
./run_pipeline.sh --job <job-id>
```

### Issue: Out of memory

```bash
# Use smaller Whisper model
export WHISPER_MODEL=medium  # or small, base
./run_pipeline.sh --job <job-id>
```

---

## Next Steps

Now that you have the basic pipeline running:

1. **Optimize configuration** → [Configuration Guide](docs/user-guide/CONFIGURATION.md)
2. **Understand the pipeline** → [Pipeline Stages](docs/technical/PIPELINE_STAGES.md)
3. **Improve accuracy** → [Bias System](docs/technical/BIAS_SYSTEM.md)
4. **Customize glossaries** → [Glossary System](docs/technical/GLOSSARY_SYSTEM.md)
5. **Troubleshoot issues** → [Troubleshooting Guide](docs/reference/TROUBLESHOOTING.md)

---

## Quick Command Reference

```bash
# Bootstrap
./scripts/bootstrap.sh

# Prepare job
./prepare-job.sh <video_file>

# Run pipeline
./run_pipeline.sh --job <job-id>

# Resume pipeline
./run_pipeline.sh --job <job-id>

# Start fresh
./run_pipeline.sh --job <job-id> --no-resume

# Run specific stages
./run_pipeline.sh --job <job-id> --stages "stage1 stage2"

# List available stages
./run_pipeline.sh --list-stages

# Check status
./test-pipeline-status.sh <job-id>

# View logs
tail -f out/YYYY/MM/DD/N/JOBID/logs/00_orchestrator_*.log
```

---

**Questions? See [FAQ](docs/reference/FAQ.md) or [Troubleshooting Guide](docs/reference/TROUBLESHOOTING.md)**
