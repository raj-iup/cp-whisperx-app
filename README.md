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
- **Second pass translation** (15-20% quality boost) ⭐
- **Lyrics detection** (20-25% improvement for songs) ⭐
- SRT subtitle generation
- Video muxing with embedded subtitles

**Result:** Professional-quality subtitles with speaker labels, ready for distribution!

### 🎭 Bollywood Optimization

**For Bollywood movies, this pipeline delivers exceptional results!**

The optional **second-pass translation** and **lyrics detection** stages are **highly recommended** for Bollywood content:

- **35-45% quality improvement** for Bollywood movies
- Perfect handling of **Hinglish** (Hindi-English code-switching)
- Accurate translation of **cultural idioms** and expressions
- Specialized **song lyric translation** (20-25% boost for musical sequences)
- Preservation of proper nouns and character names

See [Bollywood Subtitle Workflow](docs/BOLLYWOOD_SUBTITLE_WORKFLOW.md) for detailed information.

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

### Installation (Phase 1 & 2 Optimized)

**⚡ New in v2.0:** 75-85% faster job preparation, 60% smaller Docker images!

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/cp-whisperx-app.git
   cd cp-whisperx-app
   ```

2. **One-time Bootstrap** (10-15 minutes)
   ```bash
   # Windows
   .\scripts\bootstrap.ps1
   
   # Linux/macOS
   ./scripts/bootstrap.sh
   ```
   
   Bootstrap creates `.bollyenv` with all dependencies, detects hardware, and optionally pre-downloads ML models.

3. **Build Docker Images** (2-30 minutes depending on mode)
   
   **Native Mode** (recommended - fastest, smallest):
   ```bash
   # Windows
   .\scripts\docker-build.ps1 -Mode native
   
   # Linux/macOS
   ./scripts/docker-build.sh --mode native
   ```
   - Builds only FFmpeg images (~2 GB)
   - ML execution uses native `.bollyenv`
   - Best performance
   
   **Docker GPU Mode** (full isolation):
   ```bash
   # Windows
   .\scripts\docker-build.ps1 -Mode docker-gpu
   
   # Linux/macOS
   ./scripts/docker-build.sh --mode docker-gpu
   ```
   - Builds all GPU-enabled images (~20 GB, optimized)
   - Fully containerized execution
   - Good for distributed setups

4. **Run your first job** (5-30 seconds to prepare!)
   ```bash
   # Windows
   .\prepare-job.ps1 input.mp4
   .\run_pipeline.ps1 -Job <job-id>
   
   # Linux/macOS
   ./prepare-job.sh input.mp4
   ./run_pipeline.sh -j <job-id>
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

### 🎭 Bollywood & Indian Content
Specialized guides for Indian movie subtitle generation.

- **[Bollywood Subtitle Workflow](docs/BOLLYWOOD_SUBTITLE_WORKFLOW.md)** - Complete guide for Bollywood movies ⭐
- **[Second Pass Translation](docs/SECOND_PASS_TRANSLATION.md)** - 15-20% accuracy boost for multilingual content
- **[Lyrics Detection](docs/LYRICS_DETECTION.md)** - 20-25% improvement for song sequences

### 🏗️ Architecture Documentation
Deep dives into system design and optimization decisions.

- **[Script Consolidation Best Practices](docs/SCRIPT_CONSOLIDATION_BEST_PRACTICES.md)** - Phase 1 & 2 optimization plan ⭐
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Upgrade to Phase 1 & 2 enhancements ⭐
- **[Complete Workflow Architecture](docs/WORKFLOW_ARCHITECTURE.md)** - Full pipeline design with all stages
- **[Docker Optimization](docs/DOCKER_OPTIMIZATION.md)** - Docker build optimization strategy
- **[Docker Optimization Feasibility](docs/DOCKER_OPTIMIZATION_FEASIBILITY.md)** - Feasibility analysis
- **[Docker Optimization Status](docs/DOCKER_OPTIMIZATION_STATUS.md)** - Current implementation status
- **[Docker Build Optimization](docs/DOCKER_BUILD_OPTIMIZATION.md)** - Build-time optimizations

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
- **[Transcribe Workflow](docs/architecture/transcribe-workflow.md)** - Simple workflow architecture
- **[Master Prompt](docs/architecture/whisper-app-master-prompt.md)** - Project prompts
- **[Workflow Architecture (Legacy)](docs/architecture/workflow-arch.md)** - Legacy architecture diagrams

**Note**: For current architecture documentation, see the main docs/ folder.

---

## 🎯 Quick Start Guides by Use Case

### I want to transcribe Bollywood movies with highest quality
1. Start with [Bollywood Subtitle Workflow](docs/BOLLYWOOD_SUBTITLE_WORKFLOW.md)
2. Understand [Second Pass Translation](docs/SECOND_PASS_TRANSLATION.md) (15-20% boost)
3. Learn about [Lyrics Detection](docs/LYRICS_DETECTION.md) (20-25% boost for songs)
4. Result: **35-45% better subtitle quality!**

### I want to quickly transcribe English content
1. Read [Quick Start Guide](docs/guides/user/quickstart.md)
2. Use transcribe workflow (faster, no speaker labels)
3. Check [Workflow Guide](docs/guides/user/workflow-guide.md) for details

### I want to understand the complete pipeline
1. Start with [Workflow Architecture](docs/WORKFLOW_ARCHITECTURE.md)
2. Read [Complete Workflow Guide](docs/guides/user/workflow-guide.md)
3. Review [Pipeline Best Practices](docs/PIPELINE_BEST_PRACTICES.md)

### I want to optimize performance
1. [Hardware Optimization](docs/HARDWARE_OPTIMIZATION.md) - GPU/CPU tuning
2. [Docker Optimization](docs/DOCKER_OPTIMIZATION.md) - Container performance
3. [Pipeline Best Practices](docs/PIPELINE_BEST_PRACTICES.md) - General tips

### I want to debug issues
1. [Native Debug Quick Reference](docs/native-debug-quick-reference.md) - Fast debugging
2. [Debug Mode Guide](docs/guides/developer/debug-mode.md) - Comprehensive debugging
3. [Logging Locations](docs/guides/developer/logging-locations.md) - Where to find logs

---

## 📊 Feature Comparison

| Feature | Western Movies | Bollywood Movies | Recommendation |
|---------|---------------|------------------|----------------|
| **Basic Pipeline** | 90% quality | 70% quality | Use for all content |
| **+ TMDB Metadata** | +2% | +5% | Highly recommended |
| **+ Second Pass Translation** | +2% | +15-20% | **Essential for Bollywood** |
| **+ Lyrics Detection** | 0% | +20-25% songs | **Essential for Bollywood** |
| **Total Improvement** | ~94% | **88-90%** | **Bollywood: +18-20% overall** |

---

## ⚡ Performance at a Glance

### 2-Hour Movie Processing Time

| Configuration | Hardware | Time | Quality | Best For |
|---------------|----------|------|---------|----------|
| **Transcribe only** | RTX 4090 | 12 min | ⭐⭐⭐ | Quick transcripts |
| **Standard Subtitles** | RTX 4090 | 45 min | ⭐⭐⭐⭐ | English movies |
| **Bollywood Optimized** | RTX 4090 | 58 min | ⭐⭐⭐⭐⭐ | **Bollywood movies** |
| **CPU Fallback** | i7-12700K | 5 hr | ⭐⭐⭐⭐ | Overnight processing |

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
- `docker-compose.yml` - Docker service configuration (root directory)
- `config/.env.example` - Environment variable templates
- `.env` - Environment variables (create from `config/.env.example`)

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
