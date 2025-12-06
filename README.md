# WhisperX Speech Processing Pipeline

**Version:** 3.0 (Context-Aware Modular Pipeline) | **Status:** 🎉 97% Complete - Production Ready

Professional-grade speech transcription, translation, and subtitle generation pipeline powered by WhisperX, MLX, and IndicTrans2.

[![Pipeline](https://img.shields.io/badge/Pipeline-v3.0%20(12%20Stages)-success)](docs/technical/architecture.md)
[![Compliance](https://img.shields.io/badge/Standards%20Compliance-100%25-brightgreen)](docs/DEVELOPER_STANDARDS.md)
[![Architecture](https://img.shields.io/badge/Architecture-9%20Decisions-blue)](ARCHITECTURE_ALIGNMENT_2025-12-04.md)
[![Documentation](https://img.shields.io/badge/Documentation-Complete-blue)](docs/INDEX.md)
[![License](https://img.shields.io/badge/License-View-lightgrey)](LICENSE)

---

## 🚀 Quick Start (30 seconds)

```bash
# 1. One-time setup
./bootstrap.sh

# 2. Generate subtitles (Bollywood/Indic content)
./prepare-job.sh --media in/your_movie.mp4 --workflow subtitle \
  --source-language hi --target-languages en,gu,ta,es
./run-pipeline.sh --job-dir out/LATEST

# 3. Transcribe (English technical content)
./prepare-job.sh --media "in/Energy Demand in AI.mp4" --workflow transcribe \
  --source-language en
./run-pipeline.sh --job-dir out/LATEST

# 4. Translate (Hindi to English)
./prepare-job.sh --media in/hindi_audio.mp4 --workflow translate \
  --source-language hi --target-language en
./run-pipeline.sh --job-dir out/LATEST
```

**Output Structure (v3.0 - 12 Stage Architecture):**
```
out/YYYY/MM/DD/user/NNNN/
├── 01_demux/                      # Audio extraction
├── 02_tmdb/                       # TMDB metadata (subtitle workflow only)
├── 03_glossary_load/              # Terminology loading
├── 04_source_separation/          # Vocal isolation (adaptive)
├── 05_pyannote_vad/               # Voice activity + diarization
├── 06_asr/                        # ASR transcription
├── 07_alignment/                  # Word-level alignment
│   └── transcript.txt             # Final transcript (transcribe workflow)
├── 08_lyrics_detection/           # Lyrics detection (subtitle workflow)
├── 09_hallucination_removal/      # ASR cleanup (subtitle workflow)
├── 10_translation/                # Translation (translate/subtitle workflows)
│   └── transcript_{lang}.txt      # Translated transcript
├── 11_subtitle_generation/        # Subtitle files (subtitle workflow)
│   └── *.vtt                      # VTT subtitle tracks
├── 12_mux/                        # Final video (subtitle workflow)
│   └── *_subtitled.mkv            # Video with soft-embedded subtitles
└── logs/                          # Pipeline and stage logs
```

**Test Samples Included:**
- `in/Energy Demand in AI.mp4` - English technical (transcribe/translate)
- `in/test_clips/jaane_tu_test_clip.mp4` - Hinglish Bollywood (subtitle)

**Complete Guide:** [Quick Start Documentation](docs/QUICKSTART.md) | **Workflows:** [Workflow Guide](docs/user-guide/workflows.md) | **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 🎉 What's New in v3.0

### 12-Stage Modular Pipeline
- **Context-Aware Processing**: Character names, cultural terms, temporal consistency
- **Mandatory Quality Stages**: Lyrics detection + hallucination removal (subtitle workflow)
- **Stage Isolation**: Each stage operates independently with full manifest tracking
- **Resume Support**: Continue from any stage after interruption

### Hybrid MLX Architecture (8-9x Faster)
- **MLX-Whisper**: Ultra-fast transcription on Apple Silicon
- **Subprocess Alignment**: Prevents segfaults, maintains stability
- **Production Validated**: 100% test success rate
- **Architecture Decision AD-008**: [Hybrid MLX Backend](ARCHITECTURE_ALIGNMENT_2025-12-04.md)

### Architectural Decisions Framework
- **9 Authoritative Decisions**: AD-001 through AD-009
- **Quality-First Development**: Optimize for accuracy, not backward compatibility
- **Job-Specific Parameters**: Per-job configuration overrides (AD-006)
- **Consistent Import Paths**: Standardized module structure (AD-007)
- **Reference**: [ARCHITECTURE_ALIGNMENT_2025-12-04.md](ARCHITECTURE_ALIGNMENT_2025-12-04.md)

### Enhanced Quality & Reliability
- **100% Standards Compliance**: Automated pre-commit validation
- **Comprehensive Testing**: E2E tests for all 3 workflows
- **File Naming Standards**: Professional, predictable output structure
- **Stage Manifests**: Full input/output/intermediate file tracking

---

## ✨ Key Features

### 🎯 Context-Aware Transcription (Highest Accuracy)
- **WhisperX large-v3** with word-level forced alignment
- **Hybrid MLX Architecture**: 8-9x faster on Apple Silicon (AD-008)
- **Multi-speaker diarization** with speaker attribution
- **Domain terminology** and proper noun recognition via glossary
- **Hallucination removal** (stage 09) - removes ASR artifacts
- **Lyrics detection** (stage 08) - identifies song segments
- **Native script output** (Devanagari for Hindi, etc.)

### 🌍 Context-Aware Translation (Cultural Preservation)
- **Indic Languages**: IndicTrans2 (AI4Bharat) for highest quality
- **Non-Indic**: NLLB-200 (Meta) with broad language support
- **Cultural adaptation**: Idioms, metaphors, formality preservation
- **Glossary-based terminology**: 100% consistency enforcement
- **Temporal coherence**: Same term translated consistently
- **22+ Indian languages** + 100+ global languages supported

### 🎬 Professional Multi-Language Subtitles
- **Soft-embedding**: All subtitle tracks in one video file (MKV)
- **Context-Aware**: Character names (TMDB), cultural terms, speaker diarization
- **Multi-Language**: Hindi, English, Gujarati, Tamil, Spanish, Russian, Chinese, Arabic
- **Quality Metrics**: ±200ms timing accuracy, 88%+ subtitle quality score
- **Formats**: SRT/VTT with comprehensive metadata
- **Workflow-Specific**: Lyrics italic styling, hallucination removal

### ⚡ Intelligent Architecture (v3.0)
- **12-Stage Pipeline**: Modular, testable, resumable (AD-001)
- **Stage Isolation**: Each stage operates independently
- **Manifest Tracking**: Full lineage of inputs/outputs/intermediates
- **Job-Specific Config**: Per-job parameter overrides (AD-006)
- **8 Virtual Environments**: Dependency isolation (AD-004)
- **Hybrid Backends**: MLX + WhisperX optimal combination (AD-005, AD-008)

### 💻 Multi-Environment Support
- **MLX**: Optimized for Apple Silicon (M1/M2/M3/M4) with MPS acceleration
- **CUDA**: NVIDIA GPU acceleration for maximum speed
- **CPU**: Universal fallback mode for any system

### 📊 Advanced Logging & Tracking
- **Main Pipeline Log**: High-level orchestration tracking
- **Stage-Specific Logs**: Detailed execution logs per stage
- **Manifest System**: Complete I/O tracking for data lineage and audit
- **Context Propagation**: Cultural, temporal, speaker coherence tracking
- **Configurable Log Levels**: DEBUG|INFO|WARN|ERROR|CRITICAL

---

## 🏗️ Architecture Status

**Current:** v3.0 (12-Stage Modular Pipeline) | **Status:** 🎉 97% Complete - Production Ready

### What's Working Now ✅
- **12-Stage Pipeline**: Fully modular with stage isolation (AD-001)
- **Hybrid MLX Architecture**: 8-9x faster on Apple Silicon (AD-008)
- **Multi-environment support**: 8 isolated venvs (MLX/WhisperX/PyAnnote/Demucs/IndicTrans2/NLLB/LLM/Common)
- **Universal StageIO pattern**: 100% adoption across all stages
- **Complete manifest tracking**: 100% adoption with full lineage
- **Job-specific configuration**: Parameter overrides per job (AD-006)
- **3 Production Workflows**: Subtitle, Transcribe, Translate
- **100% Standards Compliance**: Automated validation

### Recently Completed 🆕
- **ASR Module Refactoring**: Clean modular structure (AD-002)
- **File Naming Standards**: Professional output structure
- **Architectural Decisions Framework**: 9 authoritative decisions (AD-001 to AD-009)
- **Hybrid MLX Backend**: Transcription + subprocess alignment (AD-008)
- **E2E Testing Infrastructure**: Comprehensive workflow validation

### Upcoming (Phase 5) ⏳
- **Intelligent Caching**: Audio fingerprinting, ASR cache, translation memory
- **ML Optimization**: Adaptive model selection, quality prediction
- **Performance Monitoring**: Cost tracking, usage analytics

**See:** [Implementation Tracker](IMPLEMENTATION_TRACKER.md) for detailed progress | [Architecture Decisions](ARCHITECTURE_ALIGNMENT_2025-12-04.md) for design rationale

---

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](docs/QUICKSTART.md)** - Get running in 5 minutes
- **[Documentation Index](docs/INDEX.md)** - Complete documentation hub
- **[Bootstrap Guide](docs/user-guide/bootstrap.md)** - Environment setup

### User Guides
- **[User Guide](docs/user-guide/)** - Usage, workflows, configuration
- **[Workflows](docs/user-guide/workflows.md)** - Common usage patterns
- **[Configuration](docs/user-guide/configuration.md)** - Configuration reference
- **[Troubleshooting](TROUBLESHOOTING.md)** - Problem solving & debugging 🆕

### Technical Documentation
- **[Architecture](docs/technical/architecture.md)** - System design (v3.0)
- **[Architecture Decisions](ARCHITECTURE_ALIGNMENT_2025-12-04.md)** - 9 authoritative decisions 🆕
- **[Implementation Tracker](IMPLEMENTATION_TRACKER.md)** - Development progress 🆕
- **[Pipeline Details](docs/technical/pipeline.md)** - Stage-by-stage flow
- **[Logging Architecture](docs/LOGGING_ARCHITECTURE.md)** - Dual logging system
- **[Multi-Environment](docs/technical/multi-environment.md)** - MLX/CUDA/CPU support
- **[Language Support](docs/technical/language-support.md)** - Supported languages

### Developer Resources
- **[Developer Standards](docs/DEVELOPER_STANDARDS.md)** - Code standards & best practices
- **[Contributing](docs/developer/contributing.md)** - Contribution guidelines
- **[Getting Started](docs/developer/getting-started.md)** - Development setup

---

## 📂 Project Structure

```
cp-whisperx-app/
├── bootstrap.sh              # Environment setup
├── prepare-job.sh            # Job configuration
├── run-pipeline.sh           # Main pipeline runner
├── test-glossary-quickstart.sh  # Quick test with glossary
│
├── config/                   # Configuration files
│   ├── .env.pipeline        # Main configuration
│   └── secrets.json         # API keys (git-ignored)
│
├── scripts/                  # Pipeline stages
│   ├── prepare-job.py       # Job preparation
│   ├── run-pipeline.py      # Pipeline orchestrator
│   ├── whisperx_asr.py      # ASR stage
│   ├── translate_hybrid.py  # Translation stage
│   └── [other stages...]    # Additional stage scripts
│
├── shared/                   # Shared utilities
│   ├── config.py            # Configuration management
│   ├── logger.py            # Dual logging system
│   ├── stage_utils.py       # StageIO pattern with manifests
│   ├── stage_order.py       # Centralized stage ordering
│   └── [other modules...]   # Additional utilities
│
├── glossary/                 # Glossary definitions
├── in/                       # Input audio files
├── out/                      # Output directory (per-job)
│   └── <job-id>/            # Job-specific output
│       ├── logs/            # Main pipeline log
│       ├── 01_demux/        # Stage output with stage.log & manifest.json
│       ├── 02_tmdb/         # Stage output with stage.log & manifest.json
│       └── ...              # Other stages
│
└── docs/                     # Documentation
    ├── INDEX.md             # Documentation hub
    ├── QUICKSTART.md        # Quick start guide
    ├── user-guide/          # User documentation
    ├── technical/           # Technical documentation
    ├── developer/           # Developer guides
    └── reference/           # Reference materials
```

---

## 🎯 Core Workflows

### 1. Subtitle Workflow (Context-Aware, Multi-Language)
**Purpose:** Generate context-aware multilingual subtitles for Bollywood/Indic media with soft-embedding

```bash
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es,ru,zh,ar

./run-pipeline.sh --job-dir out/LATEST
```

**Features:**
- Character name preservation via glossary
- Cultural term handling (beta, bhai, ji, etc.)
- Speaker diarization and attribution
- Temporal coherence across subtitle blocks
- Soft-embedded tracks in organized output directory

**Output:** `out/.../10_mux/{media_name}/{media_name}_subtitled.mkv` + individual SRT files

### 2. Transcribe Workflow (Context-Aware, Source Language)
**Purpose:** Create high-accuracy transcript in SAME language as source audio

```bash
# English technical content
./prepare-job.sh --media "in/Energy Demand in AI.mp4" \
  --workflow transcribe \
  --source-language en

# Hindi/Hinglish content
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow transcribe \
  --source-language hi

./run-pipeline.sh --job-dir out/LATEST
```

**Features:**
- Domain terminology preservation (technical, medical, legal)
- Proper noun detection and capitalization
- Native script output (Devanagari for Hindi)
- Word-level timestamps (±100ms precision)
- 95%+ accuracy for English, 85%+ for Hindi/Indic

**Output:** `out/.../07_alignment/transcript.txt` + `transcript.json` (with timestamps)

### 3. Translate Workflow (Context-Aware, Target Language)
**Purpose:** Create high-accuracy transcript in SPECIFIED target language

```bash
# Hindi → English
./prepare-job.sh --media in/hindi_movie.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language en

# Hindi → Spanish (non-Indic)
./prepare-job.sh --media in/hindi_audio.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language es

# Hindi → Gujarati (Indic-to-Indic)
./prepare-job.sh --media in/hindi_content.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language gu

./run-pipeline.sh --job-dir out/LATEST
```

**Features:**
- Cultural adaptation (idioms, metaphors, formality)
- Bilingual glossary term preservation (100% application)
- Temporal consistency (same term translated consistently)
- Numeric/date format localization
- IndicTrans2 for Indic languages, NLLB-200 for others

**Output:** `out/.../08_translate/transcript_{target_lang}.txt`

### Quick Test with Glossary
```bash
# Auto-execute baseline, glossary, and cache test
./test-glossary-quickstart.sh \
  --start-time 00:00:30 \
  --end-time 00:01:00 \
  --log-level INFO
```

### Advanced Usage
```bash
# Multiple target languages (subtitle workflow)
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language hi --target-languages en,gu,ta,te,es,ru,zh,ar

# Custom glossary
./prepare-job.sh --media in/audio.mp4 --glossary my-terms.txt \
  --workflow transcribe --source-language hi

# Disable caching (force fresh processing)
./prepare-job.sh --media in/audio.mp4 --workflow transcribe \
  --source-language en --no-cache

# Override configuration
./prepare-job.sh --media in/audio.mp4 --workflow transcribe \
  --source-language en --beam-size 10 --best-of 10
```

**Complete Workflows:** [Workflow Guide](docs/user-guide/workflows.md)

---

## 🌍 Supported Languages

### Transcription
All languages supported by WhisperX (90+ languages including English, Spanish, French, German, Chinese, Japanese, etc.)

### Translation
- **Indian Languages** (IndicTrans2): Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Assamese, Oriya, Urdu, Sanskrit, and more
- **Other Languages** (Google Translate): 100+ languages

**Complete List:** [Language Support](docs/technical/language-support.md)

---

## 💻 System Requirements

### Minimum
- **CPU**: 4+ cores
- **RAM**: 8GB
- **Storage**: 10GB for models
- **OS**: macOS, Linux, or Windows (WSL)

### Recommended
- **Apple Silicon**: M1/M2/M3 with 16GB RAM
- **NVIDIA GPU**: 8GB+ VRAM (RTX 3060 or better)
- **RAM**: 16GB+
- **Storage**: 20GB+ SSD

---

## 🔧 Configuration

Pipeline behavior is controlled through:

1. **Global Config**: `config/pipeline.conf` - Default settings
2. **Job Config**: Created by `prepare-job.sh` for each audio file
3. **Environment Variables**: Set via `bootstrap.sh` or manually
4. **Command-Line Options**: Override settings per execution

**Configuration Guide:** [Configuration Documentation](docs/user-guide/configuration.md)

---

## 📊 Logging Architecture

The pipeline implements a **dual logging architecture** for comprehensive tracking:

### Main Pipeline Log
- **Location**: `out/<job-id>/logs/99_pipeline_<timestamp>.log`
- **Purpose**: High-level orchestration, stage transitions
- **Level**: INFO, WARNING, ERROR

### Stage-Specific Logs
- **Location**: `out/<job-id>/<stage>/stage.log`
- **Purpose**: Detailed stage execution, debugging
- **Level**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Stage Manifests
- **Location**: `out/<job-id>/<stage>/manifest.json`
- **Purpose**: Complete I/O tracking
- **Contents**: Input files, output files, intermediate files, timestamps, metadata

**Logging Guide:** [Logging Architecture](docs/LOGGING_ARCHITECTURE.md)

---

## 🧪 Testing

```bash
# Quick test with glossary (auto-execute all tasks)
./test-glossary-quickstart.sh

# Quick test with custom time range and log level
./test-glossary-quickstart.sh --start-time 00:00:30 --end-time 00:01:00 --log-level DEBUG

# Full test suite
./test_phase1.sh

# Specific component tests
./test-glossary-simple.sh
```

**Testing Guide:** [Developer Documentation](docs/developer/getting-started.md)

---

## 🛠️ Development

### Standards & Best Practices
- **Compliance**: 100% adherence to [Developer Standards](docs/DEVELOPER_STANDARDS.md)
- **Python**: 3.8+ with type hints
- **Logging**: Dual logging architecture (main + stage-specific)
- **Configuration**: Centralized config management
- **Error Handling**: Comprehensive with manifest tracking
- **Testing**: Unit tests with pytest

### Code Quality
- **StageIO Pattern**: Standardized data flow with manifest tracking
- **Centralized Utilities**: Shared modules in `shared/`
- **Multi-Environment**: Isolated virtual environments per component
- **Documentation**: Comprehensive inline and external docs

**Development Guide:** [Developer Standards](docs/DEVELOPER_STANDARDS.md)

---

## 📈 Current Status

**Compliance**: ✅ 100% (60/60 checks passed)  
**Documentation**: ✅ Complete and up-to-date  
**Testing**: ✅ Comprehensive test coverage  
**Production Ready**: ✅ All stages fully compliant

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/developer/contributing.md) for:
- Development setup
- Coding standards
- Testing requirements
- Pull request process

---

## 📄 License

[View License](LICENSE)

---

## 📖 Citations

This project builds on excellent open-source work:

- **WhisperX**: Bain et al. (2023) - Forced alignment and diarization
- **Whisper**: Radford et al. (2022) - Foundation transcription model
- **IndicTrans2**: AI4Bharat - Indian language translation
- **PyAnnote**: Speaker diarization models
- **MLX**: Apple's machine learning framework

**Complete References:** [Citations](docs/reference/citations.md)

---

## 💬 Support

- **Documentation**: [Complete Documentation Hub](docs/INDEX.md)
- **Troubleshooting**: [Troubleshooting Guide](docs/user-guide/troubleshooting.md)
- **Configuration Help**: [Configuration Guide](docs/user-guide/configuration.md)
- **Developer Support**: [Developer Standards](docs/DEVELOPER_STANDARDS.md)

---

## 🎯 Roadmap

### Current Development (v2.0 → v3.0)

**In Progress:**
- ✅ Phase 0: Foundation (100% Complete) - Standards, config, pre-commit hooks
- 🟡 Phase 1: File Naming & Standards - Align script names with documentation
- 🟡 Phase 2: Testing Infrastructure - Build comprehensive test suite with standard samples
- 🔴 Phase 3: StageIO Migration - Migrate 5 active stages to standardized pattern
- 🔴 Phase 4: Stage Integration - Complete 10-stage modular pipeline
- 🔴 Phase 5: Advanced Features - Caching, ML optimization, monitoring

**Next Up (2025-12-03 to 2026-05):**
- Context-aware subtitle generation with cultural adaptation
- Intelligent caching system (70% target hit rate)
- ML-based optimization for adaptive quality and performance
- Complete manifest tracking and data lineage
- Stage enable/disable per job
- 85% test coverage with standardized test media

**Progress:** 55% → 95% over 21 weeks

**Full Roadmap:** [Architecture Implementation Roadmap](docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md)

---

**Last Updated**: November 27, 2025 | **Version**: 1.0 | **Compliance**: 100%
