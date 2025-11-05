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

### Production-Ready
- **Resumable Pipeline**: Continue from any failed stage
- **Comprehensive Logging**: Detailed logs for every stage
- **Automatic Fallback**: Graceful degradation from GPU to CPU
- **Manifest Tracking**: Complete job history and metadata

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ (for native mode)
- Docker Desktop (for Docker mode)
- NVIDIA GPU with CUDA 11.8+ (recommended) or CPU fallback
- 8GB+ RAM (16GB+ recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/cp-whisperx-app.git
   cd cp-whisperx-app
   ```

2. **Choose your mode**

   **Native Mode** (fastest):
   ```bash
   # Windows
   .\scripts\bootstrap.ps1
   
   # Linux/macOS
   ./scripts/bootstrap.sh
   ```

   **Docker Mode** (isolated):
   ```bash
   # Build all images
   .\scripts\build-all-images.ps1   # Windows
   ./scripts/build-all-images.sh    # Linux/macOS
   ```

3. **Run your first job**
   ```bash
   # Prepare job
   python prepare-job.py
   
   # Run pipeline
   python pipeline.py
   ```

---

## 📚 Documentation

### 🎓 User Guides
Start here if you're new to the project or want to learn how to use it effectively.

- **[Quick Start Guide](docs/guides/user/quickstart.md)** - Get up and running in 5 minutes
- **[Workflow Guide](docs/guides/user/workflow-guide.md)** - Understand the complete pipeline workflow
- **[Docker Quick Start](docs/guides/user/docker-quickstart.md)** - Using Docker mode
- **[Pipeline Resume Guide](docs/guides/user/pipeline-resume-guide.md)** - Recover from failures

### 🖥️ Hardware & Acceleration Guides
Configure your system for optimal performance.

- **[CUDA Acceleration Guide](docs/guides/hardware/cuda-acceleration.md)** - NVIDIA GPU setup (Windows/Linux)
- **[MPS Acceleration Guide](docs/guides/hardware/mps-acceleration.md)** - Apple Silicon setup (macOS)
- **[GPU Fallback Guide](docs/guides/hardware/gpu-fallback.md)** - CPU fallback configuration
- **[Device Selection Guide](docs/guides/hardware/device-selection.md)** - Choose the right device
- **[Windows 11 Setup Guide](docs/guides/hardware/windows-11-setup.md)** - Complete Windows setup

### 👨‍💻 Developer Guides
For contributors and advanced users who want to understand or modify the code.

- **[Developer Guide](docs/guides/developer/developer-guide.md)** - Architecture and development workflow
- **[Logging Locations](docs/guides/developer/logging-locations.md)** - Where to find logs
- **[Windows Scripts Guide](docs/guides/developer/windows-scripts.md)** - PowerShell scripts reference
- **[Debug Mode Guide](docs/guides/developer/debug-mode.md)** - Debugging native mode

### 🏗️ Architecture Documentation
Deep dives into system design and optimization decisions.

- **[Docker Optimization](docs/architecture/docker-optimization.md)** - Docker build optimization strategy
- **[Docker Optimization Feasibility](docs/architecture/docker-optimization-feasibility.md)** - Feasibility analysis
- **[Docker Optimization Status](docs/architecture/docker-optimization-status.md)** - Current implementation status
- **[Docker Build Optimization](docs/architecture/docker-build-optimization.md)** - Build-time optimizations

### 🐳 Docker Documentation
Everything about Docker images, builds, and scripts.

- **[Docker README](docs/docker/README.md)** - Docker overview and quick reference
- **[Build Documentation Index](docs/docker/build-documentation-index.md)** - Complete build docs
- **[Build Status](docs/docker/build-status.md)** - Current build status
- **[Build Summary](docs/docker/build-summary.md)** - Build process overview
- **[Scripts Quick Reference](docs/docker/scripts-quick-ref.md)** - Docker scripts cheat sheet
- **[Pull Scripts Summary](docs/docker/pull-scripts-summary.md)** - Image pulling documentation
- **[Ready to Build](docs/docker/ready-to-build.md)** - Build readiness checklist

### 📖 Technical Reference
Detailed technical documentation for specific features and systems.

- **[Build Fix Summary](docs/BUILD_FIX_SUMMARY.md)** - Docker build fixes applied
- **[Docker Base Image Fix](docs/DOCKER_BASE_IMAGE_FIX.md)** - Base image issues and fixes
- **[Docker Image Management](docs/DOCKER_IMAGE_MANAGEMENT.md)** - Image management strategies
- **[Docker Optimization Implementation](docs/DOCKER_OPTIMIZATION_IMPLEMENTATION.md)** - Implementation details
- **[Docker Optimization Quick Reference](docs/DOCKER_OPTIMIZATION_QUICK_REF.md)** - Quick optimization guide
- **[Docker Optimization Recommendations](docs/DOCKER_OPTIMIZATION_RECOMMENDATIONS.md)** - Best practices
- **[Hardware Optimization](docs/HARDWARE_OPTIMIZATION.md)** - Hardware-specific optimizations
- **[Implementation Uniformity](docs/IMPLEMENTATION_UNIFORMITY.md)** - Code consistency guidelines
- **[Job Orchestration](docs/JOB_ORCHESTRATION.md)** - Pipeline orchestration details
- **[Logging Standard](docs/LOGGING_STANDARD.md)** - Logging conventions
- **[Logging Documentation](docs/LOGGING.md)** - Logging system overview
- **[Manifest System Guide](docs/MANIFEST_SYSTEM_GUIDE.md)** - Job manifest documentation
- **[Manifest Tracking](docs/MANIFEST_TRACKING.md)** - Manifest tracking system
- **[Pipeline Best Practices](docs/PIPELINE_BEST_PRACTICES.md)** - Pipeline optimization tips
- **[Silero/PyAnnote VAD](docs/README-SILERO-PYANNOTE-VAD.md)** - VAD system documentation
- **[Test Plan](docs/TEST_PLAN.md)** - Testing strategy and test cases
- **[TMDB API Setup](docs/TMDB_API_SETUP.md)** - Setting up TMDB integration

### 🗂️ Historical Documentation
For reference: Previous implementations, migrations, and changes.

- **[Docker Build Fixes](docs/history/docker-build-fixes.md)** - Historical build fixes
- **[Docker Build Fix Summary](docs/history/docker-build-fix-summary.md)** - Fix summaries
- **[Docker Build Fixes Applied](docs/history/docker-build-fixes-applied.md)** - Applied fixes log
- **[Docker Build Fixes Summary](docs/history/docker-build-fixes-summary.md)** - Comprehensive summary
- **[Docker Phase 1 Summary](docs/history/docker-phase1-summary.md)** - Phase 1 implementation
- **[Docker Refactoring Summary](docs/history/docker-refactoring-summary.md)** - Refactoring changes
- **[Script Migration Summary](docs/history/script-migration-summary.md)** - Script migration log
- **[Scripts Conversion Summary](docs/history/scripts-conversion-summary.md)** - Conversion details
- **[Git Backup Record](docs/history/git-backup-record.md)** - Backup history
- **[Git Push Ready](docs/history/git-push-ready.md)** - Pre-push checklist
- **[Commit Message](docs/history/commit-message.md)** - Standard commit format
- **[Old Documentation Index](docs/history/documentation-index-old.md)** - Previous index

### 🏛️ Architecture Reference
Archived architecture documents and design notes.

- **[Architecture Verified](docs/architecture/ARCHITECTURE_VERIFIED.md)** - Verified architecture notes
- **[CUDA Environment Report](docs/architecture/cuda_env_report.md)** - CUDA environment analysis
- **[HuggingFace Gated PyAnnote](docs/architecture/HF-gated-pynote.md)** - PyAnnote access notes
- **[Transcribe Workflow](docs/architecture/transcribe-workflow.md)** - Workflow architecture
- **[Master Prompt](docs/architecture/whisper-app-master-prompt.md)** - Project prompts
- **[Workflow Architecture](docs/architecture/workflow-arch.md)** - Architecture diagrams

---

## 🎬 Usage Examples

### Basic Transcription
```bash
# Prepare a video for transcription
python prepare-job.py

# Run transcription only
python pipeline.py --workflow transcribe

# Check logs
Get-Content out/MyMovie/logs/07_asr_*.log -Tail 50
```

### Full Subtitle Generation
```bash
# Prepare with TMDB metadata
python prepare-job.py --tmdb-id 550

# Run full pipeline with speaker diarization
python pipeline.py --workflow subtitle

# Output: out/MyMovie/MyMovie.mkv (with embedded subtitles)
```

### Resume from Failure
```bash
# Pipeline failed at diarization stage?
# Just run again - it will resume automatically
python pipeline.py

# Or use resume script
.\resume-pipeline.ps1
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Device selection
DEVICE=cuda              # cuda, mps, or cpu
COMPUTE_TYPE=float16     # float16, float32

# TMDB API (for subtitle workflow)
TMDB_API_KEY=your_key_here

# Logging
LOG_LEVEL=INFO           # DEBUG, INFO, WARN, ERROR
```

### Config Files
- `config/default.yaml` - Default pipeline configuration
- `config/docker-compose.yml` - Docker service configuration
- `.env` - Environment variables (create from `.env.example`)

---

## 📊 System Requirements

### Minimum
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 20GB free
- **OS**: Windows 10+, Ubuntu 20.04+, macOS 11+

### Recommended
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **GPU**: NVIDIA RTX 3060+ (6GB VRAM) or Apple M1+
- **Storage**: 50GB+ SSD

### Performance Comparison
| Mode | Hardware | Speed | Recommended For |
|------|----------|-------|----------------|
| **Native + CUDA** | RTX 4090 | ⚡⚡⚡⚡⚡ (fastest) | Production |
| **Docker + CUDA** | RTX 4090 | ⚡⚡⚡⚡ (fast) | Development |
| **Native + MPS** | M1 Max | ⚡⚡⚡ (good) | macOS users |
| **Native + CPU** | i7-12700K | ⚡⚡ (slower) | Testing |
| **Docker + CPU** | i7-12700K | ⚡ (slow) | CI/CD |

---

## 🤝 Contributing

We welcome contributions! Please see:
- [Developer Guide](docs/guides/developer/developer-guide.md) - Development workflow
- [Implementation Uniformity](docs/IMPLEMENTATION_UNIFORMITY.md) - Code standards
- [Test Plan](docs/TEST_PLAN.md) - Testing requirements

### Quick Contribution Guide
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest`
5. Submit a pull request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with amazing open-source projects:
- **[WhisperX](https://github.com/m-bain/whisperX)** - Fast automatic speech recognition
- **[PyAnnote](https://github.com/pyannote/pyannote-audio)** - Speaker diarization
- **[spaCy](https://spacy.io/)** - Named entity recognition
- **[FFmpeg](https://ffmpeg.org/)** - Audio/video processing
- **[TMDB](https://www.themoviedb.org/)** - Movie metadata

---

## 📞 Support

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/yourusername/cp-whisperx-app/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cp-whisperx-app/discussions)

---

## 🗺️ Roadmap

- [ ] Web UI for pipeline management
- [ ] Multi-language subtitle support
- [ ] Real-time transcription mode
- [ ] Cloud deployment guides (AWS, GCP, Azure)
- [ ] Automatic quality assessment
- [ ] Batch processing improvements

---

**Made with ❤️ by the CP-WhisperX-App team**
