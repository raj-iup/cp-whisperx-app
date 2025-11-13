# CP-WhisperX-App

**Context-Aware Subtitle Generation Pipeline for Bollywood Movies**

Automatically generate high-quality English subtitles from Bollywood movies with mixed Hindi-English dialogue (Hinglish). Leverages WhisperX for accurate transcription, speaker diarization, and context-aware translation with intelligent bias prompting.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)]()

---

## 🚀 Quick Start

Get started in 5 minutes:

```bash
# Clone and setup
git clone https://github.com/yourusername/cp-whisperx-app.git
cd cp-whisperx-app
./scripts/bootstrap.sh

# Configure
cp config/.env.pipeline.template config/.env.pipeline
# Edit config/.env.pipeline with your settings

# Run
./prepare-job.sh /path/to/movie.mp4
./run_pipeline.sh --job <job-id>
```

📖 **[Complete Quick Start Guide](docs/QUICKSTART.md)**

---

## ✨ Key Features

- 🎬 **Bollywood-Optimized** - Specialized for Hindi/Hinglish cinema
- 🎯 **Active Bias Prompting** - 20-30% better name recognition using TMDB cast/crew data
- 🎙️ **Speaker Diarization** - Automatic speaker detection and labeling
- 🔤 **Context-Aware Translation** - Preserves character names and cultural terms
- 📚 **Intelligent Glossary System** - Film-specific glossary with ML-based selection
- ⚡ **GPU Acceleration** - Apple Silicon (MPS), NVIDIA CUDA, CPU fallback
- 🎵 **Lyric Detection** - Special formatting for song sequences
- 🔄 **Resume Capability** - Continue from any interrupted stage

---

## 📚 Documentation

### Getting Started

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get running in 5 minutes
- **[Installation & Bootstrap](docs/BOOTSTRAP.md)** - Detailed setup instructions
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and future roadmap

### User Guides

- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Common commands and workflows
- **[Quick Fix Reference](docs/QUICK_FIX_REFERENCE.md)** - Common issues and solutions
- **[Configuration Guide](docs/CONFIGURATION.md)** - All configuration options
- **[Glossary System](docs/GLOSSARY_BUILDER_QUICKSTART.md)** - Using the glossary features

### Technical Documentation

- **[Bias Prompting System](docs/technical/BIAS_ACTIVE_IMPLEMENTATION.md)** - Active bias prompting
- **[Pipeline Stages](docs/ARCHITECTURE.md)** - Detailed stage-by-stage processing
- **[ASR Optimization](docs/technical/ASR_CPU_ONLY_IMPLEMENTATION.md)** - CPU-only mode
- **[Recent Fixes](docs/technical/LOG_FIXES_IMPLEMENTATION.md)** - Bug fixes and improvements

### Reference

- **[Full Documentation Index](docs/INDEX.md)** - Complete documentation catalog
- **[API Reference](docs/API_REFERENCE.md)** - Python API documentation
- **[FAQ](docs/FAQ.md)** - Frequently asked questions

---

## 🎯 Basic Usage

### Prepare a Job

```bash
./prepare-job.sh /path/to/Dilwale_Dulhania_Le_Jayenge_1995.mp4

# Output:
# ✓ Created job: 20251113-0001
# ✓ Job directory: out/2025/11/13/1/20251113-0001/
```

### Run the Pipeline

```bash
./run_pipeline.sh --job 20251113-0001

# Processing stages (14 total):
#  1. Demux → 2. TMDB → 3. Pre-NER → 4-5. VAD → 6. Diarization
#  7. ASR → 8. Glossary → 9. Translation → 10. Lyrics
#  11. Post-NER → 12. Subtitles → 13. Mux → 14. Finalize
```

### Get Output

```bash
out/2025/11/13/1/20251113-0001/
├── subtitles/
│   ├── movie.srt  ← English subtitles
│   └── movie.vtt  ← WebVTT format
└── movie.with_subs.mp4  ← Video with embedded subtitles
```

---

## 🏗️ Architecture

### Current (v1.0) - CLI Pipeline

```
prepare-job.sh → Job Directory → run_pipeline.sh → 14 Stages → Output
```

**[View Current Architecture →](docs/ARCHITECTURE.md#current-architecture-v10)**

### Future (v2.0) - Web Service

```
Web UI → API → Job Queue → Distributed Workers → Database → Admin Dashboard
```

**[View Future Roadmap →](docs/ARCHITECTURE.md#future-architecture-v20)**

---

## 🔧 System Requirements

### Minimum

- **OS**: macOS 11+, Windows 10+, Linux (Ubuntu 20.04+)
- **Python**: 3.11+
- **RAM**: 8GB (16GB recommended)
- **Disk**: 20GB free space

### Recommended (GPU)

- **Apple Silicon**: M1/M2/M3 Mac (8GB+ unified memory)
- **NVIDIA GPU**: 6GB+ VRAM with CUDA support

---

## 📊 Performance

### Processing Time (2-hour movie)

| Configuration | Time | Accuracy |
|--------------|------|----------|
| CPU only | 4-6 hours | Baseline |
| Apple M2 (MPS) | 2-3 hours | +20-30% (bias) |
| NVIDIA RTX 3090 | 1.5-2 hours | +20-30% (bias) |

### Accuracy with Bias Prompting

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Proper noun recognition | Baseline | +20-30% | ⭐ NEW |
| Full name accuracy | 60% | 85% | +25% |
| Location spelling | 70% | 90% | +20% |

---

## 🤝 Contributing

We welcome contributions! See [Contributing Guidelines](docs/CONTRIBUTING.md) for details.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[WhisperX](https://github.com/m-bain/whisperX)** - Core ASR engine
- **[faster-whisper](https://github.com/guillaumekln/faster-whisper)** - CTranslate2 backend
- **[MLX](https://github.com/ml-explore/mlx)** - Apple Silicon acceleration
- **[PyAnnote](https://github.com/pyannote/pyannote-audio)** - Speaker diarization
- **[TMDB](https://www.themoviedb.org/)** - Movie metadata

---

## 📞 Support

- **Documentation**: [Full Docs](docs/INDEX.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/cp-whisperx-app/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cp-whisperx-app/discussions)

---

**Made with ❤️ for Bollywood subtitle enthusiasts**
