# CP-WhisperX-App

**Production-ready pipeline for automated video transcription, translation, and subtitle generation using WhisperX, PyAnnote, and spaCy NER.**

Perfect for processing movies, TV shows, podcasts, or any video content requiring high-quality transcription with speaker diarization and named entity recognition.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CUDA](https://img.shields.io/badge/CUDA-11.8+-green.svg)](https://developer.nvidia.com/cuda-downloads)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

## 🎯 What It Does

CP-WhisperX-App provides two powerful workflows:

### 1. **Transcribe Workflow** (Fast)
Extract clean transcription from video/audio in minutes.
- Audio extraction
- Voice activity detection
- High-accuracy transcription

### 2. **Subtitle Generation Workflow** (Full Quality)
Complete end-to-end subtitle creation with speaker labels.
- All transcribe features, plus:
- Speaker diarization (identify who's speaking)
- TMDB metadata (cast/crew names)
- Named entity recognition (correct names)
- Second pass translation (15-20% quality boost)
- Lyrics detection (20-25% improvement for songs)
- SRT subtitle generation
- Video muxing with embedded subtitles

**Result:** Professional-quality subtitles with speaker labels, ready for distribution!

---

## ✨ Key Features

### Cross-Platform Support
- **Windows 11 Pro** with NVIDIA GPU (CUDA)
- **Linux** with NVIDIA GPU (CUDA)
- **macOS** with Apple Silicon (MPS)
- **CPU Fallback** for any platform

### Dual Execution Modes
- **Native Mode**: Direct Python execution with GPU acceleration (fastest)
- **Docker Mode**: Containerized execution for reproducibility and isolation

### Intelligent Pipeline
- **Job-based workflow**: Isolated jobs with unique IDs
- **Manifest tracking**: Complete audit trail of all processing steps
- **Resume capability**: Automatically resume from last successful stage
- **Clip mode**: Test pipeline on short clips before full processing
- **Auto device detection**: Automatically selects best compute device

### Production Ready
- **Comprehensive logging**: Sequential stage logs with configurable verbosity
- **Error handling**: Graceful failure with detailed error reporting
- **Validation**: Pre-flight checks for dependencies and GPU
- **Monitoring**: Real-time progress tracking

### Quality Enhancements
- **NER-enhanced prompts**: Better transcription using entity hints
- **Second pass translation**: Refined translation with context
- **Lyrics detection**: Special handling for songs and music
- **Speaker diarization**: Identify and label different speakers

---

## 🏗️ Architecture

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│                     CP-WhisperX-App Pipeline                     │
└─────────────────────────────────────────────────────────────────┘

[Input Video]
     │
     ├─→ 01. DEMUX ────────────────→ Extract audio (WAV)
     │
     ├─→ 02. TMDB ─────────────────→ Fetch cast/crew metadata
     │
     ├─→ 03. PRE-NER ──────────────→ Extract entity names
     │
     ├─→ 04. SILERO VAD ───────────→ Voice activity detection
     │
     ├─→ 05. PYANNOTE VAD ─────────→ Refined VAD
     │
     ├─→ 06. DIARIZATION ──────────→ Speaker identification
     │
     ├─→ 07. ASR ──────────────────→ WhisperX transcription
     │
     ├─→ 07b. SECOND PASS ─────────→ Translation refinement
     │
     ├─→ 07c. LYRICS DETECTION ────→ Song/music handling
     │
     ├─→ 08. POST-NER ─────────────→ Entity name correction
     │
     ├─→ 09. SUBTITLE GEN ─────────→ Generate SRT subtitles
     │
     └─→ 10. MUX ──────────────────→ Embed subtitles in video
          │
[Output Video with Subtitles]
```

### Workflow Comparison

| Stage                  | Transcribe | Subtitle-Gen | ML Model | Device    |
|------------------------|:----------:|:------------:|:--------:|-----------|
| 01. Demux              | ✅         | ✅           | ❌       | CPU       |
| 02. TMDB               | ❌         | ✅           | ❌       | CPU       |
| 03. Pre-NER            | ❌         | ✅           | ✅       | CPU       |
| 04. Silero VAD         | ✅         | ✅           | ✅       | GPU/CPU   |
| 05. PyAnnote VAD       | ✅         | ✅           | ✅       | GPU/CPU   |
| 06. Diarization        | ❌         | ✅           | ✅       | GPU/CPU   |
| 07. ASR                | ✅         | ✅           | ✅       | GPU/CPU   |
| 07b. Second Pass       | ❌         | ✅           | ✅       | GPU/CPU   |
| 07c. Lyrics Detection  | ❌         | ✅           | ✅       | GPU/CPU   |
| 08. Post-NER           | ❌         | ✅           | ❌       | CPU       |
| 09. Subtitle Gen       | ❌         | ✅           | ❌       | CPU       |
| 10. Mux                | ❌         | ✅           | ❌       | CPU       |

---

## 📁 Project Structure

```
cp-whisperx-app/
├── pipeline.py                 # Main orchestrator
├── preflight.py               # System validation & setup
├── prepare-job.py             # Job preparation tool
├── docker-compose.yml         # Docker orchestration
│
├── arch/                      # Architecture documentation
│   ├── workflow-arch.txt
│   └── transcribe-workflow.txt
│
├── config/                    # Configuration files
│   ├── .env.example          # Example configuration
│   ├── .env.template         # Configuration template
│   └── secrets.example.json  # Secrets template
│
├── docker/                    # Docker containers
│   ├── base/                 # Base image
│   ├── demux/                # Stage 01: Audio extraction
│   ├── tmdb/                 # Stage 02: Metadata
│   ├── pre-ner/              # Stage 03: Pre-NER
│   ├── silero-vad/           # Stage 04: Silero VAD
│   ├── pyannote-vad/         # Stage 05: PyAnnote VAD
│   ├── diarization/          # Stage 06: Speaker diarization
│   ├── asr/                  # Stage 07: WhisperX ASR
│   ├── second-pass-translation/  # Stage 07b: Translation
│   ├── lyrics-detection/     # Stage 07c: Lyrics
│   ├── post-ner/             # Stage 08: Post-NER
│   ├── subtitle-gen/         # Stage 09: Subtitle generation
│   └── mux/                  # Stage 10: Video muxing
│
├── native/                    # Native mode execution
│   ├── scripts/              # Stage scripts (01-10)
│   │   ├── 01_demux.py
│   │   ├── 02_tmdb.py
│   │   ├── 03_pre_ner.py
│   │   ├── 04_silero_vad.py
│   │   ├── 05_pyannote_vad.py
│   │   ├── 06_diarization.py
│   │   ├── 07_asr.py
│   │   ├── 07b_second_pass_translation.py
│   │   ├── 07c_lyrics_detection.py
│   │   ├── 08_post_ner.py
│   │   ├── 09_subtitle_gen.py
│   │   └── 10_mux.py
│   └── venvs/                # Virtual environments (created by preflight)
│
├── scripts/                   # Pipeline utilities
│   ├── bootstrap.sh          # Environment setup
│   ├── build-images.sh       # Docker image builder
│   ├── common-logging.sh     # Logging utilities
│   ├── config_loader.py      # Configuration loader
│   ├── device_selector.py    # GPU detection
│   ├── logger.py             # Logging framework
│   └── pipeline-status.sh    # Status checker
│
├── shared/                    # Shared Python modules
│   ├── config.py             # Configuration loader
│   ├── logger.py             # Logging utilities
│   ├── manifest.py           # Manifest builder
│   └── utils.py              # Common utilities
│
├── in/                        # Input videos (staging)
├── out/                       # Output artifacts (both native and Docker)
│   └── YYYY/MM/DD/<user-id>/<job-id>/
│       ├── job.json           # Job definition (replaces jobs/)
│       ├── .<job-id>.env      # Job-specific configuration
│       ├── logs/              # Job-specific logs
│       ├── manifest.json      # Processing manifest
│       ├── audio/             # Demux output
│       ├── vad/               # VAD outputs
│       ├── diarization/       # Diarization output
│       └── ...                # Stage outputs
│
└── docs/                      # Documentation
    ├── JOB_ORCHESTRATION.md
    ├── LOGGING.md
    ├── MANIFEST_TRACKING.md
    ├── PIPELINE_BEST_PRACTICES.md
    ├── SECRETS_MANAGER.md
    ├── TMDB_API_SETUP.md
    └── TEST_PLAN.md
```

---

## 🚀 Quick Start

### Step 1: Installation
```bash
# Clone repository
git clone <repository-url>
cd cp-whisperx-app

# Setup configuration
cp config/.env.example config/.env
# Edit config/.env with your API keys

# Run preflight check
python preflight.py
```

### Step 2: Run Pipeline

**Transcribe Only:**
```bash
python prepare-job.py input.mp4 --transcribe --native
python pipeline.py --job <job-id>
```

**Subtitle Generation:**
```bash
python prepare-job.py input.mp4 --subtitle-gen --native
python pipeline.py --job <job-id>
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

---

## 📊 Performance

### Processing Times (2-hour movie)

| Workflow      | GPU (CUDA/MPS) | CPU     |
|---------------|----------------|---------|
| Transcribe    | 10-15 min      | 2-3 hrs |
| Subtitle-Gen  | 30-45 min      | 5-8 hrs |

**Factors affecting speed:**
- GPU model and VRAM
- Video length and audio complexity
- Number of speakers
- Language (Hindi→English vs English-only)

### Resource Requirements

| Component     | Minimum | Recommended |
|---------------|---------|-------------|
| RAM           | 16 GB   | 32 GB       |
| VRAM (GPU)    | 6 GB    | 12 GB       |
| Storage       | 20 GB   | 50 GB       |
| CPU Cores     | 4       | 8+          |

---

## 🔧 Configuration

### Environment Variables

**Core Settings:**
```bash
# Execution mode
PIPELINE_MODE=native              # native or docker
WORKFLOW=subtitle_gen             # transcribe or subtitle_gen

# Device selection
DEVICE=auto                       # auto, cuda, mps, or cpu
DEVICE_OVERRIDE=false            # Force specific device

# Processing options
CLIP_MODE=false                  # Process short clips
CLIP_DURATION=300                # Clip length in seconds
```

**API Keys:**
```bash
# Required for diarization
HF_TOKEN=hf_xxxxxxxxxxxx

# Optional for metadata
TMDB_API_KEY=xxxxxxxxxxxx
```

**Model Settings:**
```bash
# WhisperX
WHISPER_MODEL=large-v3
WHISPER_LANGUAGE=hi              # Source language
WHISPER_TASK=translate           # or transcribe

# Diarization
DIARIZATION_MODEL=pyannote/speaker-diarization-3.1
MIN_SPEAKERS=2
MAX_SPEAKERS=10
```

See [config/.env.template](config/.env.template) for all options.

---

## 📖 Documentation

### Quick References
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in minutes
- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Detailed workflow options
- **[PIPELINE_RESUME_GUIDE.md](PIPELINE_RESUME_GUIDE.md)** - Resume failed jobs

### Platform Guides
- **[WINDOWS_11_SETUP_GUIDE.md](WINDOWS_11_SETUP_GUIDE.md)** - Windows installation
- **[CUDA_ACCELERATION_GUIDE.md](CUDA_ACCELERATION_GUIDE.md)** - NVIDIA GPU setup
- **[MPS_ACCELERATION_GUIDE.md](MPS_ACCELERATION_GUIDE.md)** - Apple Silicon setup
- **[DEVICE_SELECTION_GUIDE.md](DEVICE_SELECTION_GUIDE.md)** - GPU optimization

### Architecture & Development
- **[docs/JOB_ORCHESTRATION.md](docs/JOB_ORCHESTRATION.md)** - Job system design
- **[docs/MANIFEST_TRACKING.md](docs/MANIFEST_TRACKING.md)** - Manifest system
- **[docs/LOGGING.md](docs/LOGGING.md)** - Logging architecture
- **[docs/PIPELINE_BEST_PRACTICES.md](docs/PIPELINE_BEST_PRACTICES.md)** - Best practices
- **[docs/TEST_PLAN.md](docs/TEST_PLAN.md)** - Testing & validation

### API Setup
- **[docs/TMDB_API_SETUP.md](docs/TMDB_API_SETUP.md)** - TMDB API configuration
- **[docs/SECRETS_MANAGER.md](docs/SECRETS_MANAGER.md)** - Secrets management

---

## 🧪 Testing

### Validation Checklist

```bash
# 1. System validation
python preflight.py

# 2. GPU detection
python preflight.py --check-device

# 3. API access
python native/scripts/test_tmdb.py
python native/scripts/test_pyannote_vad.py

# 4. Quick test (2-minute clip)
python prepare-job.py test.mp4 --subtitle-gen --native --clip-duration 120
python pipeline.py --job <job-id>

# 5. Full workflow test
python prepare-job.py sample.mp4 --subtitle-gen --native
python pipeline.py --job <job-id>
```

See [docs/TEST_PLAN.md](docs/TEST_PLAN.md) for comprehensive testing.

---

## 🔍 Troubleshooting

### Common Issues

**GPU Not Detected:**
```bash
python preflight.py --check-device
python prepare-job.py input.mp4 --native --device cuda  # Force CUDA
```

**PyAnnote Diarization Fails:**
```bash
# Accept license at: https://huggingface.co/pyannote/speaker-diarization
# Add HF_TOKEN to config/.env
python native/scripts/test_pyannote_vad.py
```

**Out of Memory:**
```bash
# Use CPU or smaller clip
python prepare-job.py input.mp4 --native --device cpu
python prepare-job.py input.mp4 --native --clip-duration 300
```

**Resume Failed Job:**
```bash
./resume-pipeline.sh <job-id>          # Unix/Linux/macOS
resume-pipeline.bat <job-id>           # Windows
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[WhisperX](https://github.com/m-bain/whisperX)** - Fast automatic speech recognition
- **[PyAnnote](https://github.com/pyannote/pyannote-audio)** - Speaker diarization
- **[Silero VAD](https://github.com/snakers4/silero-vad)** - Voice activity detection
- **[spaCy](https://spacy.io/)** - Named entity recognition
- **[FFmpeg](https://ffmpeg.org/)** - Audio/video processing

---

## 📞 Support

- **Documentation:** [docs/](docs/) directory
- **Issues:** Check logs in `logs/` directory  
- **Debugging:** Enable verbose logging in config/.env

---

**Ready to start?** See [QUICKSTART.md](QUICKSTART.md) to begin!
