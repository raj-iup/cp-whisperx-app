# Documentation Index

Complete guide to CP-WhisperX-App documentation.

---

## 📖 Core Documentation

### Essential Guides

| Document | Description |
|----------|-------------|
| **[Quick Start](QUICKSTART.md)** | Get running in 5 minutes |
| **[Architecture](ARCHITECTURE.md)** | System design (v1.0 + v2.0 roadmap) |
| **[Quick Reference](QUICK_REFERENCE.md)** | Common commands |
| **[Quick Fix Reference](QUICK_FIX_REFERENCE.md)** | Troubleshooting |

### Installation & Setup

| Document | Description |
|----------|-------------|
| [Bootstrap Guide](BOOTSTRAP.md) | Install dependencies and environment |
| [Configuration](CONFIGURATION.md) | All configuration options |
| [Apple Silicon Guide](APPLE_SILICON_QUICK_REF.md) | Optimize for M1/M2/M3 Macs |

### Features

| Document | Description |
|----------|-------------|
| [Glossary Builder](GLOSSARY_BUILDER_QUICKSTART.md) | Film-specific glossary system |
| [CPS Optimization](CPS_QUICK_REFERENCE.md) | Subtitle readability |

---

## 🔬 Technical Documentation

### Implementation Details

| Document | Description |
|----------|-------------|
| [Bias Prompting](technical/BIAS_ACTIVE_IMPLEMENTATION.md) | Active bias prompting (Phase 1) |
| [Bias Strategy](technical/BIAS_IMPLEMENTATION_STRATEGY.md) | 3-phase implementation plan |
| [Bias Data Flow](technical/BIAS_PROMPT_FLOW.md) | How bias data flows |
| [ASR CPU Mode](technical/ASR_CPU_ONLY_IMPLEMENTATION.md) | CPU-only optimization |
| [Recent Fixes](technical/LOG_FIXES_IMPLEMENTATION.md) | Bug fixes (2025-11-13) |

---

## 📚 Reference Documentation

### API & Configuration

| Document | Description |
|----------|-------------|
| [API Reference](API_REFERENCE.md) | Python API documentation |
| [FAQ](FAQ.md) | Frequently asked questions |
| [Contributing](CONTRIBUTING.md) | Contribution guidelines |

---

## 🗂️ By Audience

### For End Users

**Just want to generate subtitles?**

1. **Start**: [Quick Start](QUICKSTART.md)
2. **Configure**: [Configuration](CONFIGURATION.md)
3. **Reference**: [Quick Reference](QUICK_REFERENCE.md)
4. **Help**: [Quick Fix Reference](QUICK_FIX_REFERENCE.md)

### For Developers

**Want to understand the code?**

1. **Overview**: [Architecture](ARCHITECTURE.md)
2. **Features**: [Bias System](technical/BIAS_ACTIVE_IMPLEMENTATION.md)
3. **Detailed**: [Architecture v1.0](ARCHITECTURE.md#current-architecture-v10)

### For Contributors

**Want to help improve the project?**

1. **Guidelines**: [Contributing](CONTRIBUTING.md)
2. **Architecture**: [System Design](ARCHITECTURE.md)
3. **Roadmap**: [Future Plans](ARCHITECTURE.md#future-architecture-v20)

---

## 📁 Documentation Structure

```
docs/
├── INDEX.md (this file)
│
├── Core Guides
│   ├── QUICKSTART.md
│   ├── ARCHITECTURE.md
│   ├── QUICK_REFERENCE.md
│   └── QUICK_FIX_REFERENCE.md
│
├── Installation
│   ├── BOOTSTRAP.md
│   ├── CONFIGURATION.md
│   └── APPLE_SILICON_QUICK_REF.md
│
├── Features
│   ├── GLOSSARY_BUILDER_QUICKSTART.md
│   └── CPS_QUICK_REFERENCE.md
│
├── technical/
│   ├── BIAS_ACTIVE_IMPLEMENTATION.md
│   ├── BIAS_IMPLEMENTATION_STRATEGY.md
│   ├── BIAS_PROMPT_FLOW.md
│   ├── ASR_CPU_ONLY_IMPLEMENTATION.md
│   └── LOG_FIXES_IMPLEMENTATION.md
│
├── reference/
│   ├── API_REFERENCE.md
│   ├── FAQ.md
│   └── CONTRIBUTING.md
│
└── archive/
    └── [Historical implementation notes]
```

---

## 🆕 Recent Updates

### 2025-11-13

- ✅ Documentation structure refactored
- ✅ All markdown files moved to docs/
- ✅ Only README.md in project root
- ✅ Active bias prompting implemented
- ✅ ASR CPU-only mode added
- ✅ Multiple bug fixes applied

---

## 📞 Getting Help

### Quick Answers

1. Check [Quick Fix Reference](QUICK_FIX_REFERENCE.md)
2. Check [FAQ](FAQ.md)
3. Search [GitHub Issues](https://github.com/yourusername/cp-whisperx-app/issues)

### Report Issues

1. Check existing documentation
2. Search existing issues
3. Create new issue with:
   - Environment details
   - Steps to reproduce
   - Relevant logs

---

## 🔗 External Resources

- **[WhisperX](https://github.com/m-bain/whisperX)** - Core ASR engine
- **[faster-whisper](https://github.com/guillaumekln/faster-whisper)** - CTranslate2 backend
- **[MLX](https://github.com/ml-explore/mlx)** - Apple Silicon acceleration
- **[PyAnnote](https://github.com/pyannote/pyannote-audio)** - Speaker diarization
- **[TMDB API](https://developers.themoviedb.org/)** - Movie metadata

---

**Last Updated**: 2025-11-13  
**Documentation Version**: 3.0  
**Project Version**: 1.0
