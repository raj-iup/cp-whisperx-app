# Quick Start Guide

**Get up and running with CP-WhisperX-App in 5 minutes**

---

## Prerequisites

Before starting, ensure you have:
- ✅ Python 3.11 or higher
- ✅ 16GB+ RAM (8GB minimum)
- ✅ 50GB+ free disk space
- ✅ One of:
  - macOS with Apple Silicon (M1/M2/M3) - Recommended
  - Windows 10/11 with NVIDIA GPU
  - Linux with NVIDIA GPU or CPU

---

## Step 1: Clone & Setup (2 minutes)

```bash
# Clone the repository
git clone <repository-url>
cd cp-whisperx-app

# Run bootstrap (one-time setup)
./scripts/bootstrap.sh    # macOS/Linux
# OR
.\scripts\bootstrap.ps1   # Windows
```

**What bootstrap does:**
- Creates Python virtual environment (`.bollyenv`)
- Installs all dependencies
- Detects your hardware (GPU/CPU)
- Sets up model cache directories
- Optionally pre-downloads ML models

**Expected output:**
```
✓ Python 3.11.x detected
✓ Virtual environment created
✓ Dependencies installed
✓ Hardware detected: Apple M1 Pro (MPS)
✓ Cache directories created
✓ Bootstrap complete!
```

---

## Step 2: Configure API Keys (1 minute)

Create `config/secrets.json`:

```bash
mkdir -p config
cat > config/secrets.json << 'EOF'
{
  "TMDB_API_KEY": "your-tmdb-api-key-here",
  "HF_TOKEN": "your-huggingface-token-here"
}
EOF
```

**Get API keys:**
- **TMDB**: Sign up at [themoviedb.org](https://www.themoviedb.org/settings/api) (free)
- **HuggingFace**: Get token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) (free)

---

## Step 3: Process Your First Movie (1 minute)

```bash
# 1. Place movie in input directory
cp /path/to/your/movie.mp4 in/

# 2. Prepare the job
./prepare-job.sh in/movie.mp4

# Output example:
# ✓ Parsed: Kabhi Khushi Kabhie Gham (2001)
# ✓ Job created: 20251108-0001
# ✓ Configuration: out/2025/11/08/1/20251108-0001/.20251108-0001.env

# 3. Run pipeline
./run_pipeline.sh --job 20251108-0001
```

**What happens:**
1. Audio extraction (10 min)
2. Metadata fetch (2 min)
3. Entity extraction (5 min)
4. Voice activity detection (30 min)
5. Speaker diarization (2 hours)
6. WhisperX transcription (4 hours)
7. Translation refinement (2 hours)
8. Lyrics detection (30 min)
9. Entity correction (20 min)
10. Subtitle generation (10 min)
11. Video muxing (10 min)

**Total time**: ~10 hours for a 2.5-hour movie (with GPU)

---

## Step 4: View Results (30 seconds)

```bash
# Find your subtitles
ls out/2025/11/08/1/20251108-0001/subtitles/subtitles.srt

# View final muxed video
ls out/2025/11/08/1/20251108-0001/final_output.mp4
```

**Output structure:**
```
out/2025/11/08/1/20251108-0001/
├── subtitles/
│   └── subtitles.srt          ← Your English subtitles!
├── final_output.mp4            ← Video with embedded subtitles
├── asr/
│   └── transcript.json         ← Raw transcription
└── logs/                       ← Processing logs
```

---

## Common Commands

### Check Job Status
```bash
./scripts/pipeline-status.sh 20251108-0001
```

### Resume Failed Job
```bash
# If pipeline fails, resume from checkpoint
./resume-pipeline.sh 20251108-0001
```

### Run Specific Stages
```bash
# Re-run only subtitle generation
./run_pipeline.sh --job 20251108-0001 --stages "subtitle_gen mux"
```

### Transcription Only (No Subtitles)
```bash
./prepare-job.sh --workflow transcribe in/movie.mp4
./run_pipeline.sh --job 20251108-0002
# Output: transcript.txt
```

---

## Troubleshooting Quick Fixes

### Bootstrap Fails
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Clean and retry
rm -rf .bollyenv
./scripts/bootstrap.sh
```

### "No GPU Detected" (but you have one)
```bash
# Check hardware cache
cat out/hardware_cache.json | grep gpu_type

# If wrong, delete cache and re-run bootstrap
rm out/hardware_cache.json
./scripts/bootstrap.sh
```

### Models Fail to Download
```bash
# Verify HuggingFace token
cat config/secrets.json | grep HF_TOKEN

# Check disk space
df -h .

# Verify cache permissions
ls -la .cache/
```

### Permission Errors
```bash
# Fix cache permissions
chmod 755 .cache/torch .cache/huggingface

# Fix output permissions
chmod 755 out/
```

---

## Next Steps

Now that you have your first subtitles:

1. **Learn More**: Read [Architecture Overview](ARCHITECTURE.md)
2. **Advanced Usage**: See [Running Pipeline Guide](RUNNING.md)
3. **Customize**: Review [Configuration Guide](CONFIGURATION.md)
4. **Troubleshoot**: Check [Troubleshooting Guide](TROUBLESHOOTING.md)

---

## Performance Tips

### Faster Processing
- ✅ Use GPU (MPS/CUDA) instead of CPU: 10-15x faster
- ✅ Use `large-v3` model for best quality
- ✅ Enable resume capability (default)
- ✅ Run on SSD for better I/O

### Quality Improvements
- ✅ Ensure good audio quality in source
- ✅ Use TMDB metadata for better context
- ✅ Review and update entity lists
- ✅ Fine-tune diarization settings

---

## What You've Learned

- ✅ How to set up the environment
- ✅ How to configure API keys
- ✅ How to prepare and run jobs
- ✅ Where to find output files
- ✅ Basic troubleshooting

---

## Support

- **Documentation**: Full guides in `docs/` directory
- **Status Check**: `./scripts/pipeline-status.sh [job_id]`
- **Issues**: Open an issue on GitHub
- **Community**: Join discussions (if available)

---

**Congratulations! You've successfully generated your first Bollywood subtitles! 🎉**

Return to [Documentation Index](INDEX.md) | Read [Bootstrap Guide](BOOTSTRAP.md)
