# CP-WhisperX-App - Dockerized Pipeline

Complete Hindi-to-English subtitle generation pipeline with speaker diarization, following the architecture defined in `workflow-arch.txt`.

## 🏗️ Architecture

The pipeline consists of 10 containerized steps:

```
🎬 MP4 Source (Film Scene)
   ↓
[1] FFmpeg Demux — extract 16kHz mono audio
   ↓
[2] TMDB Metadata Fetch — movie data: cast, places, plot, keywords
   ↓
[3] Pre-ASR NER — extract named entities → builds smarter ASR prompt
   ↓
[4] Silero VAD — coarse speech segmentation
   ↓
[5] PyAnnote VAD — refined contextual boundaries
   ↓
[6] PyAnnote Diarization — mandatory speaker labeling
   ↓
[7] WhisperX ASR + Forced Alignment — English translation + time-aligned transcription
   ↓
[8] Post-ASR NER — entity correction & enrichment
   ↓
[9] Subtitle Generation (.srt) — speaker-prefixed, entity-corrected subtitles
   ↓
[10] FFmpeg Mux — embed English soft-subtitles into MP4
   ↓
🎞️ Final Output: movie_with_en_subs.mp4
```

## 📋 Prerequisites

- **Docker** 20.10+ with Docker Compose
- **Python** 3.11+ (for orchestrator scripts)
- **10GB+ RAM** recommended
- **10GB+ free disk space**

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repo-url>
cd cp-whisperx-app

# Create required directories
mkdir -p in out logs temp config
```

### 2. Configure Pipeline

```bash
# Copy template configuration
cp config/.env.template config/.env

# Edit configuration
nano config/.env
```

**Key settings to configure:**

```ini
# Docker Registry (change to your registry)
DOCKER_REGISTRY=rajiup
DOCKER_TAG=latest

# Input file
INPUT_FILE=./in/your-movie.mp4

# Logging
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json # Options: json, text

# Whisper Model
WHISPER_MODEL=large-v3  # Options: large-v3, large-v2, medium, small

# Enable/Disable Steps
STEP_DEMUX=true
STEP_TMDB_METADATA=true
STEP_WHISPERX=true
# ... etc
```

### 3. Setup Secrets (Optional but Recommended)

```bash
# Create secrets file
cat > config/secrets.json << EOF
{
  "TMDB_API_KEY": "your-tmdb-api-key",
  "HF_TOKEN": "your-huggingface-token"
}
EOF
```

### 4. Run Preflight Checks

```bash
python preflight.py
```

This validates:
- ✓ Docker installation and daemon
- ✓ Directory structure
- ✓ Configuration files
- ✓ Disk space and memory
- ✓ Docker images availability

### 5. Build Docker Images

```bash
# Build all images locally
./scripts/build-images.sh

# Or pull from registry
docker-compose -f docker-compose.new.yml pull
```

### 6. Run Pipeline

```bash
# Run complete pipeline
python pipeline.py in/your-movie.mp4

# Or specify custom config
python pipeline.py in/your-movie.mp4 config/.env.custom
```

## 🔧 Advanced Usage

### Build and Push Images

```bash
# Build all images
./scripts/build-images.sh

# Push to Docker registry
./scripts/push-images.sh
```

### Run Individual Steps

```bash
# Run only demux step
docker-compose -f docker-compose.new.yml run --rm demux in/movie.mp4

# Run only WhisperX ASR
docker-compose -f docker-compose.new.yml run --rm whisperx

# Run only mux step
docker-compose -f docker-compose.new.yml run --rm mux in/movie.mp4 temp/subtitles/movie.srt out/movie_with_subs.mp4
```

### Enable Debug Logging

```bash
# Edit config/.env
LOG_LEVEL=DEBUG
LOG_FORMAT=text  # Easier to read for debugging
```

### Customize Whisper Model

```bash
# For faster processing (lower accuracy)
WHISPER_MODEL=medium

# For best accuracy (slower)
WHISPER_MODEL=large-v3
```

### Enable/Disable Steps

```bash
# Skip optional steps
STEP_TMDB_METADATA=false
STEP_PRE_ASR_NER=false
STEP_POST_ASR_NER=false

# Continue on non-critical errors
AUTO_CONTINUE=true
```

## 📁 Directory Structure

```
cp-whisperx-app/
├── config/
│   ├── .env              # Main configuration
│   ├── .env.template     # Configuration template
│   └── secrets.json      # API keys (gitignored)
├── docker/
│   ├── base/             # Base Docker image
│   ├── demux/            # FFmpeg demux container
│   ├── tmdb/             # TMDB metadata container
│   ├── pre-ner/          # Pre-ASR NER container
│   ├── silero-vad/       # Silero VAD container
│   ├── pyannote-vad/     # PyAnnote VAD container
│   ├── diarization/      # Diarization container
│   ├── whisperx/         # WhisperX ASR container
│   ├── post-ner/         # Post-ASR NER container
│   ├── subtitle-gen/     # Subtitle generation container
│   └── mux/              # FFmpeg mux container
├── shared/
│   ├── config.py         # Shared configuration loader
│   ├── logger.py         # Shared logging utilities
│   └── utils.py          # Shared utility functions
├── scripts/
│   ├── build-images.sh   # Build all Docker images
│   └── push-images.sh    # Push images to registry
├── in/                   # Input videos
├── out/                  # Final outputs
├── logs/                 # All logs (per step)
├── temp/                 # Intermediate files
├── preflight.py          # Validation script
├── pipeline.py           # Main orchestrator
├── docker-compose.new.yml
└── workflow-arch.txt     # Pipeline architecture
```

## 📊 Output Files

After successful pipeline execution:

```
out/
└── your-movie_with_subs.mp4    # Final video with embedded subtitles

logs/
├── demux_20250428_120000.log   # Step-specific logs
├── whisperx_20250428_120530.log
├── subtitle-gen_20250428_121500.log
└── manifest_20250428_122000.json  # Complete pipeline metadata

temp/
├── audio/
│   └── your-movie_audio.wav    # Extracted audio
├── subtitles/
│   └── your-movie.srt          # Generated subtitles
└── metadata/
    └── tmdb_data.json          # TMDB metadata
```

## 🐛 Troubleshooting

### Preflight Check Fails

```bash
# Check Docker is running
docker ps

# Check disk space
df -h

# Check configuration
cat config/.env
```

### Pipeline Fails on Step

```bash
# Check step-specific logs
tail -f logs/whisperx_*.log

# Run step individually for debugging
LOG_LEVEL=DEBUG python pipeline.py in/movie.mp4
```

### Out of Memory Error

```bash
# Increase Docker memory limit in config/.env
DOCKER_MEMORY_LIMIT=16g

# Or use smaller Whisper model
WHISPER_MODEL=medium
```

### Docker Images Not Found

```bash
# Build images locally
./scripts/build-images.sh

# Or pull from registry
docker-compose -f docker-compose.new.yml pull
```

## 📝 Configuration Reference

See `config/.env.template` for complete configuration options with descriptions.

## 🤝 Contributing

1. Follow the workflow-arch.txt architecture
2. Each step should be independently testable
3. All configuration via .env file (no hardcoded values)
4. All logs to logs/ directory
5. Use shared utilities from shared/ module

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- WhisperX for ASR and alignment
- PyAnnote for diarization
- TMDB for metadata
- FFmpeg for media processing
