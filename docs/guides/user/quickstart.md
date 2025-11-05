# CP-WhisperX-App Quick Start Guide

**Complete video transcription and subtitle generation pipeline with GPU acceleration**

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Docker Desktop (for Docker mode)
- Python 3.11+ (for native mode on macOS)
- Input video file

### Option 1: Docker Mode (Recommended - Works Everywhere)

```bash
# 1. Clone repository
cd cp-whisperx-app

# 2. Setup configuration
cp config/.env.example config/.env.pipeline
# Edit config/.env.pipeline with your API keys

# 3. Prepare job
python prepare-job.py /path/to/movie.mp4

# 4. Run pipeline
python pipeline.py --job <job-id>
```

### Option 2: Native Mode (macOS with Apple Silicon)

```bash
# 1. Setup virtual environments
./native/setup_venvs.sh

# 2. Prepare job with native mode
python prepare-job.py /path/to/movie.mp4 --native

# 3. Run pipeline
python pipeline.py --job <job-id>
```

## 📋 Output Structure

```
out/YYYY/MM/DD/<user-id>/<job-id>/
├── job.json                    # Job metadata
├── logs/                       # Detailed logs
├── manifest.json               # Processing manifest
├── audio/                      # Extracted audio
├── transcription/              # Transcription results
│   ├── transcript.json
│   └── transcript.txt
└── subtitles/                  # Generated subtitles
    └── movie_with_subtitles.mkv
```

## 🎯 Common Workflows

### Full Subtitle Generation
```bash
python prepare-job.py movie.mp4 --native
python pipeline.py --job <job-id>
```

### Transcription Only
```bash
python prepare-job.py movie.mp4 --transcribe --native
python pipeline.py --job <job-id>
```

### Test with Clip
```bash
python prepare-job.py movie.mp4 --start-time 00:10:00 --end-time 00:15:00
python pipeline.py --job <job-id>
```

## 📚 More Information

- **Full Documentation**: [README.md](README.md)
- **Test Plans**: [TEST_PLAN.md](TEST_PLAN.md)
- **Docker Guide**: [DOCKER_BUILD_GUIDE.md](DOCKER_BUILD_GUIDE.md)
