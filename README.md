# WhisperX Speech Processing Pipeline

Professional-grade speech transcription, translation, and subtitle generation pipeline powered by WhisperX, MLX, and IndicTrans2.

## Overview

This pipeline provides production-ready speech processing with:

- **High-Accuracy Transcription**: WhisperX with alignment and diarization
- **Multi-Environment Support**: MLX (Apple Silicon), CUDA (NVIDIA), CPU fallback
- **Smart Translation**: Hybrid pipeline with IndicTrans2 for Indian languages
- **Professional Subtitles**: SRT/VTT with speaker labels and metadata
- **Glossary Support**: Custom terminology enforcement
- **Lyrics Detection**: Music and repetitive pattern filtering

## Quick Start

```bash
# 1. Bootstrap environment
./bootstrap.sh

# 2. Prepare a job
./prepare-job.sh /path/to/audio.mp3

# 3. Run pipeline
./run-pipeline.sh /path/to/audio.mp3
```

**Output**: Transcripts, translations, and subtitles in `out/<filename>/`

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get running in 5 minutes
- **[Documentation Index](docs/INDEX.md)** - Complete documentation hub
- **[User Guide](docs/user-guide/)** - Usage, workflows, configuration
- **[Technical Docs](docs/technical/)** - Architecture, pipeline details
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Development standards

## Key Features

### 🎯 Accurate Transcription
- WhisperX large-v3 with forced alignment
- Multi-speaker diarization
- Hallucination removal and lyrics detection
- Configurable beam search and best-of parameters

### 🌍 Smart Translation
- Hybrid pipeline: IndicTrans2 → Google Translate fallback
- 22 Indian languages with specialized models
- Glossary-based terminology enforcement
- Context-aware retranslation

### 🎬 Professional Subtitles
- SRT and VTT formats with metadata
- Speaker-aware segmentation
- Configurable line length and timing
- Auto-generated glossary from translations

### ⚡ Multi-Environment
- **MLX**: Optimized for Apple Silicon (M1/M2/M3)
- **CUDA**: NVIDIA GPU acceleration
- **CPU**: Universal fallback mode

## System Requirements

### Minimum
- **CPU**: 4+ cores
- **RAM**: 8GB
- **Storage**: 10GB for models

### Recommended
- **Apple Silicon**: M1/M2/M3 with 16GB RAM
- **NVIDIA GPU**: 8GB+ VRAM (RTX 3060 or better)
- **RAM**: 16GB+

## Project Structure

```
cp-whisperx-app/
├── bootstrap.sh              # Environment setup
├── prepare-job.sh            # Job configuration
├── run-pipeline.sh           # Main pipeline runner
├── config/                   # Configuration files
├── glossary/                 # Glossary definitions
├── scripts/                  # Pipeline stages
│   ├── transcribe/          # Transcription
│   ├── translate/           # Translation
│   ├── subtitles/           # Subtitle generation
│   └── shared/              # Shared utilities
├── in/                       # Input audio files
├── out/                      # Output directory
└── docs/                     # Documentation
```

## Configuration

Pipeline behavior is controlled through:

1. **Global Config**: `config/pipeline.conf` - Default settings
2. **Job Config**: Created by `prepare-job.sh` for each audio file
3. **Environment**: Set via `bootstrap.sh` or manually

See [Configuration Guide](docs/user-guide/configuration.md) for details.

## Workflows

### Standard Workflow
```bash
./bootstrap.sh              # One-time setup
./prepare-job.sh audio.mp3  # Configure job
./run-pipeline.sh audio.mp3 # Run processing
```

### Advanced Workflow
```bash
# Use glossary
./prepare-job.sh --glossary my-terms.txt audio.mp3

# Process specific stages
./run-pipeline.sh --stage transcribe audio.mp3
./run-pipeline.sh --stage translate audio.mp3

# Override configuration
./prepare-job.sh --beam-size 10 --best-of 10 audio.mp3
```

See [Workflows Guide](docs/user-guide/workflows.md) for more examples.

## Supported Languages

### Transcription
All languages supported by WhisperX (90+ languages)

### Translation
- **Indian Languages** (IndicTrans2): Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Assamese, Oriya, Urdu, Sanskrit, and more
- **Other Languages** (Google Translate): 100+ languages

See [Language Support](docs/technical/language-support.md) for complete list.

## Troubleshooting

Common issues and solutions:

- **Model Loading Errors**: Check `bootstrap.sh` ran successfully
- **Memory Issues**: Reduce `beam_size` and `best_of` in job config
- **Translation Failures**: Check language code and glossary format
- **Subtitle Timing**: Adjust `max_line_length` in config

See [Troubleshooting Guide](docs/user-guide/troubleshooting.md) for detailed help.

## Development

### Standards
- Python 3.8+ with type hints
- Comprehensive logging via shared logger
- Configuration-driven behavior
- Extensive error handling

### Testing
```bash
# Run test suite
./test_phase1.sh

# Test specific components
./test-glossary-simple.sh
```

See [Developer Guide](docs/DEVELOPER_GUIDE.md) for contribution guidelines.

## License

[View License](LICENSE)

## Citations

This project builds on excellent open-source work:

- **WhisperX**: Bain et al. (2023) - Forced alignment and diarization
- **Whisper**: Radford et al. (2022) - Foundation transcription model
- **IndicTrans2**: AI4Bharat - Indian language translation
- **PyAnnote**: Speaker diarization models
- **MLX**: Apple's machine learning framework

See [Citations](docs/reference/citations.md) for complete references.

## Support

- **Documentation**: [docs/INDEX.md](docs/INDEX.md)
- **Issues**: Check [Troubleshooting Guide](docs/user-guide/troubleshooting.md)
- **Configuration**: See [Configuration Guide](docs/user-guide/configuration.md)

---

**Last Updated**: November 2024 | **Version**: 1.0
