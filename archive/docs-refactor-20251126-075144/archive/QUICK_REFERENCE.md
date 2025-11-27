# Quick Reference Guide

**CP-WhisperX-App - Cheat Sheet**  
**Version:** 1.1.0  
**Last Updated:** 2025-11-19

---

## 📋 Quick Command Reference

### Setup & Configuration

```bash
# Bootstrap (one-time setup - auto-installs MLX on Apple Silicon)
bash:       ./bootstrap.sh
powershell: .\bootstrap.ps1

# Manual MLX install (Apple Silicon only, if bootstrap skipped it)
./install-mlx.sh            # Install MLX into .bollyenv
./bootstrap.sh              # Re-run to update config

# Install IndicTrans2 (optional)
./install-indictrans2.sh
```

### Basic Workflows

#### Transcribe (Audio → Text)
```bash
# Bash
./prepare-job.sh movie.mp4 --transcribe -s hi
./run-pipeline.sh -j <job-id>

# PowerShell
.\prepare-job.ps1 movie.mp4 -Transcribe -SourceLanguage hi
.\run-pipeline.ps1 -JobId <job-id>
```

#### Translate (Text → English Subtitles)
```bash
# Bash
./prepare-job.sh movie.mp4 --translate -s hi -t en
./run-pipeline.sh -j <job-id>

# PowerShell
.\prepare-job.ps1 movie.mp4 -Translate -SourceLanguage hi -TargetLanguage en
.\run-pipeline.ps1 -JobId <job-id>
```

#### Subtitle (Complete Workflow)
```bash
# Bash
./prepare-job.sh movie.mp4 --subtitle -s hi -t en
./run-pipeline.sh -j <job-id>

# PowerShell
.\prepare-job.ps1 movie.mp4 -Subtitle -SourceLanguage hi -TargetLanguage en
.\run-pipeline.ps1 -JobId <job-id>
```

---

## 🎬 Supported Languages

### Source Languages (22 Indian Languages)
```
hi  - Hindi          ta  - Tamil         te  - Telugu
bn  - Bengali        gu  - Gujarati      kn  - Kannada
ml  - Malayalam      mr  - Marathi       pa  - Punjabi
ur  - Urdu           as  - Assamese      or  - Odia
ne  - Nepali         sd  - Sindhi        si  - Sinhala
sa  - Sanskrit       ks  - Kashmiri      doi - Dogri
mni - Manipuri       kok - Konkani       mai - Maithili
sat - Santali
```

### Target Languages
```
en  - English (primary)
+ All 22 Indian languages above
```

---

## 🔍 Job Management

### Check Status
```bash
# Bash
./run-pipeline.sh -j <job-id> --status
./scripts/pipeline-status.sh <job-id>

# PowerShell
.\run-pipeline.ps1 -JobId <job-id> -Status
.\scripts\pipeline-status.ps1 <job-id>
```

### Resume Failed Jobs
```bash
# Bash
./run-pipeline.sh -j <job-id> --resume

# PowerShell
.\run-pipeline.ps1 -JobId <job-id> -Resume
```

### Find Jobs
```bash
# List all jobs
find out -name "job.json" | head -10

# Search by date
ls out/2025/11/19/*/*/

# PowerShell
Get-ChildItem out -Recurse -Filter "job.json" | Select-Object -First 10
```

---

## 📊 Logging & Debugging

### Enable Debug Mode
```bash
# Bash
LOG_LEVEL=DEBUG ./prepare-job.sh movie.mp4 --transcribe -s hi

# PowerShell
$env:LOG_LEVEL="DEBUG"
.\prepare-job.ps1 movie.mp4 -Transcribe -SourceLanguage hi
```

### View Logs
```bash
# Latest log
ls -lt logs/ | head -1

# View specific log
cat logs/20251119-143045-bootstrap.log

# Watch in real-time
tail -f logs/20251119-143045-bootstrap.log

# PowerShell
Get-Content logs\* | Select-Object -Last 50
Get-Content -Path logs\latest.log -Wait -Tail 20
```

### Log Management
```bash
# Rotate logs (keep 30 days)
./tools/rotate-logs.sh --keep-days 30
.\tools\rotate-logs.ps1 -KeepDays 30

# Analyze logs
python tools/analyze-logs.py --days 7 --jobs 10
python tools/analyze-logs.py --json analysis.json
```

---

## ⚙️ Configuration

### Key Configuration Files
```
config/.env.pipeline          # Pipeline settings
config/secrets.json           # API tokens (HF, TMDB)
out/hardware_cache.json       # Hardware detection cache
```

### Common Settings
```ini
# Device
DEVICE=cuda                   # cuda, mps, cpu
WHISPER_BACKEND=whisperx      # whisperx, mlx

# Models
WHISPER_MODEL=large-v3        # tiny, base, small, medium, large-v2, large-v3
WHISPER_COMPUTE_TYPE=float16  # float16, int8

# Batch Sizes
BATCH_SIZE=8                  # Default: 8
VAD_BATCH_SIZE=32             # Default: 32

# Languages
SOURCE_LANGUAGE=hi            # See supported languages
TARGET_LANGUAGE=en            # Default: English

# Logging
LOG_LEVEL=INFO                # DEBUG, INFO, WARN, ERROR
```

---

## 🚀 Performance Tips

### Optimize for Speed
```ini
# Use GPU
DEVICE=cuda                   # or mps for Apple Silicon

# Smaller model
WHISPER_MODEL=medium          # Faster than large-v3

# Increase batch size (if GPU memory allows)
BATCH_SIZE=16                 # Default: 8
```

### Optimize for Quality
```ini
# Use largest model
WHISPER_MODEL=large-v3

# Use float16 precision
WHISPER_COMPUTE_TYPE=float16

# Reduce batch size
BATCH_SIZE=4                  # More stable
```

### Handle Out of Memory (OOM)
```ini
# Reduce batch size
BATCH_SIZE=2

# Use smaller model
WHISPER_MODEL=medium

# Reduce VAD batch size
VAD_BATCH_SIZE=16
```

---

## 🐛 Troubleshooting Quick Fixes

### Virtual Environment Not Found
```bash
# Re-run bootstrap
./bootstrap.sh                 # macOS/Linux
.\bootstrap.ps1                # Windows
```

### FFmpeg Not Found
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
choco install ffmpeg
# Or download from: https://ffmpeg.org/download.html
```

### CUDA Out of Memory
```bash
# Edit job's .env file
BATCH_SIZE=2
WHISPER_MODEL=medium
```

### Python Module Not Found
```bash
# Re-run bootstrap (it handles all dependencies)
./bootstrap.sh                     # macOS/Linux
.\bootstrap.ps1                    # Windows

# Or manually reinstall (if needed)
source .bollyenv/bin/activate      # macOS/Linux
.\.bollyenv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
```

### HuggingFace Token Error
```bash
# Create config/secrets.json
{
  "HF_TOKEN": "your_token_here"
}

# Get token from: https://huggingface.co/settings/tokens
# Accept model licenses: pyannote/speaker-diarization-3.1
```

---

## 📂 Directory Structure

```
cp-whisperx-app/
├── in/                       # Input media files
├── out/                      # Output (transcripts, subtitles, logs)
│   └── YYYY/MM/DD/USER/ID/  # Job-based structure
├── logs/                     # Script logs
├── config/                   # Configuration files
├── scripts/                  # Pipeline scripts
├── shared/                   # Shared utilities
├── tools/                    # Management tools
├── docs/                     # Documentation
├── prepare-job.sh/.ps1       # Job preparation
└── run-pipeline.sh/.ps1      # Pipeline execution
```

---

## 🎯 Common Use Cases

### Short Clip (5 minutes)
```bash
# Test transcription on short clip
./prepare-job.sh movie.mp4 --transcribe -s hi \
  --start-time 00:10:00 --end-time 00:15:00
./run-pipeline.sh -j <job-id>
```

### Full Movie (2+ hours)
```bash
# Use GPU, large model for best quality
# Set in config/.env.pipeline:
DEVICE=cuda
WHISPER_MODEL=large-v3
BATCH_SIZE=8

./prepare-job.sh movie.mp4 --translate -s hi -t en
./run-pipeline.sh -j <job-id>
```

### Batch Processing
```bash
# Process multiple files
for file in in/*.mp4; do
  ./prepare-job.sh "$file" --transcribe -s hi
done

# Run all jobs
for job in $(find out -name "job.json" | grep pending); do
  job_id=$(jq -r '.job_id' "$job")
  ./run-pipeline.sh -j "$job_id"
done
```

---

## 📱 Platform-Specific Commands

### macOS (Apple Silicon)
```bash
# Install MLX for GPU acceleration
./install-mlx.sh

# Check MPS availability
python -c "import torch; print(torch.backends.mps.is_available())"

# Monitor GPU
sudo powermetrics --samplers gpu_power -i 1000
```

### Windows (NVIDIA GPU)
```powershell
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Monitor GPU
nvidia-smi -l 1

# Install CUDA
# Download from: https://developer.nvidia.com/cuda-downloads
```

### Linux (NVIDIA GPU)
```bash
# Check CUDA
nvidia-smi

# Install CUDA (Ubuntu)
sudo apt install nvidia-cuda-toolkit

# Monitor GPU
watch -n 1 nvidia-smi
```

---

## 📖 Documentation Links

| Topic | Document |
|-------|----------|
| **Setup** | [README.md](README.md) |
| **Windows Setup** | [docs/WINDOWS_SETUP.md](docs/WINDOWS_SETUP.md) |
| **Logging** | [docs/LOGGING_STANDARDS.md](docs/LOGGING_STANDARDS.md) |
| **Troubleshooting** | [docs/LOGGING_TROUBLESHOOTING.md](docs/LOGGING_TROUBLESHOOTING.md) |
| **Architecture** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **MLX Guide** | [docs/MLX_ACCELERATION_GUIDE.md](docs/MLX_ACCELERATION_GUIDE.md) |
| **IndicTrans2** | [docs/INDICTRANS2_WORKFLOW_README.md](docs/INDICTRANS2_WORKFLOW_README.md) |
| **Changelog** | [CHANGELOG.md](CHANGELOG.md) |

---

## 🆘 Getting Help

1. **Check Documentation:** See `docs/` directory
2. **Search Issues:** GitHub Issues
3. **Ask Community:** GitHub Discussions
4. **Report Bug:** Create new issue with:
   - Command run
   - Error message
   - Log file (if available)
   - System info (OS, Python version, GPU)

---

## 💡 Pro Tips

1. **Use DEBUG mode** for first-time setup to see detailed logs
2. **Start with small clips** (5 min) to test configuration
3. **Monitor GPU usage** to ensure hardware acceleration is working
4. **Clean old logs** regularly with `rotate-logs` tool
5. **Enable Developer Mode** on Windows for better HuggingFace cache
6. **Use hardware cache** - re-run bootstrap only when hardware changes
7. **Check job status** before resuming to see which stage failed
8. **Keep logs** for at least 7 days for debugging

---

**Need more help?** Check the full documentation in the `docs/` directory!

**Version:** 1.1.0 | **Platform:** Cross-platform | **Status:** Production Ready
