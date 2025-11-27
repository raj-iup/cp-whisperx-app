# Technical Documentation

In-depth technical documentation for the WhisperX Speech Processing Pipeline.

## Overview

Technical documentation covering:
- System architecture and design
- Pipeline implementation details
- Multi-environment support
- Language capabilities

## Documentation

### Core Architecture

- **[Architecture Overview](architecture.md)** - System design and components
- **[Pipeline Details](pipeline.md)** - Stage-by-stage processing flow
- **[Multi-Environment Support](multi-environment.md)** - MLX, CUDA, and CPU modes

### Capabilities

- **[Language Support](language-support.md)** - Supported languages and models
- **[Debug Logging](debug-logging.md)** - Debugging and logging utilities

## Quick Reference

### By Topic

**System Design**:
- Component architecture → [Architecture](architecture.md)
- Data flow → [Pipeline Details](pipeline.md)
- Error handling → [Architecture](architecture.md)

**Environments**:
- MLX (Apple Silicon) → [Multi-Environment](multi-environment.md)
- CUDA (NVIDIA) → [Multi-Environment](multi-environment.md)
- CPU Fallback → [Multi-Environment](multi-environment.md)

**Processing**:
- Transcription → [Pipeline Details](pipeline.md)
- Translation → [Pipeline Details](pipeline.md)
- Subtitles → [Pipeline Details](pipeline.md)

**Languages**:
- Supported languages → [Language Support](language-support.md)
- Model capabilities → [Language Support](language-support.md)

## Architecture Highlights

### Component-Based Design

```
Main Scripts
├── bootstrap.sh        # Environment setup
├── prepare-job.sh      # Job configuration
└── run-pipeline.sh     # Pipeline orchestration

Pipeline Stages
├── scripts/transcribe/ # Speech-to-text
├── scripts/translate/  # Translation
└── scripts/subtitles/  # Subtitle generation

Shared Components
├── scripts/shared/logger.py  # Logging
├── scripts/shared/config.py  # Configuration
└── scripts/shared/utils.py   # Utilities
```

### Processing Flow

1. **Input** → Audio file (MP3, WAV, M4A, FLAC)
2. **Transcribe** → WhisperX (speech-to-text + alignment)
3. **Translate** → IndicTrans2 or Google Translate
4. **Subtitles** → SRT/VTT generation
5. **Output** → Transcripts, translations, subtitles

### Key Features

- **Multi-Environment**: Automatic hardware detection and optimization
- **Hybrid Translation**: IndicTrans2 + Google Translate fallback
- **Professional Subtitles**: SRT/VTT with speaker labels
- **Glossary System**: Custom terminology enforcement
- **Robust Error Handling**: Comprehensive logging and recovery

## Multi-Environment Support

### Environment Selection

```python
# Automatic detection in bootstrap.sh
if has_apple_silicon():
    environment = "MLX"
elif has_nvidia_gpu():
    environment = "CUDA"
else:
    environment = "CPU"
```

### Performance Characteristics

| Environment | Speed | Memory | Power |
|-------------|-------|--------|-------|
| MLX (M2)    | 20x   | Low    | Low   |
| CUDA (3090) | 30x   | Medium | High  |
| CPU (8-core)| 2x    | High   | Medium|

See [Multi-Environment](multi-environment.md) for details.

## Pipeline Stages

### 1. Transcription

**Input**: Audio file
**Output**: Timestamped transcript with speaker labels

**Processing**:
- Audio loading and preprocessing
- WhisperX speech-to-text
- Forced alignment for accurate timing
- Speaker diarization
- Hallucination removal
- Lyrics detection

### 2. Translation

**Input**: Transcript segments
**Output**: Translated text

**Processing**:
- Language detection
- IndicTrans2 for Indian languages
- Google Translate for other languages
- Glossary enforcement
- Context-aware retranslation

### 3. Subtitles

**Input**: Transcript and translation
**Output**: SRT and VTT subtitle files

**Processing**:
- Segment formatting
- Speaker label insertion
- Timing adjustment
- Metadata embedding (VTT)
- Dual-format generation

See [Pipeline Details](pipeline.md) for complete flow.

## Language Support

### Transcription Languages

WhisperX supports 90+ languages including:
- All major world languages
- Regional variants
- Code-switching detection

### Translation Languages

**Indian Languages** (IndicTrans2):
- 22 languages with specialized models
- Bidirectional translation
- Cultural context preservation

**Other Languages** (Google Translate):
- 100+ languages
- Automatic language detection
- Fallback for unsupported pairs

See [Language Support](language-support.md) for complete list.

## Technical Specifications

### Model Requirements

**WhisperX**:
- Model: large-v3
- Size: ~1.5GB
- Compute: float16 or int8
- VRAM: 4-6GB (GPU) or System RAM (CPU/MLX)

**IndicTrans2**:
- Model: indic-en-v2
- Size: ~2GB per direction
- Compute: float32
- Memory: 4-8GB

**Diarization**:
- Model: pyannote/speaker-diarization
- Size: ~500MB
- Compute: float32
- Memory: 2-4GB

### Performance Tuning

**Transcription**:
- `beam_size`: 1-10 (accuracy vs speed)
- `best_of`: 1-10 (candidate selection)
- `compute_type`: float32, float16, int8

**Translation**:
- Batch size: 32-128 segments
- Context window: 3-5 segments
- Glossary matching: fuzzy or exact

**Memory Management**:
- Model caching
- Segment batching
- Garbage collection

## Development

### Code Organization

```python
# Modular design
scripts/
├── transcribe/
│   ├── transcribe.py          # Main transcription
│   ├── alignment.py           # Forced alignment
│   ├── diarization.py         # Speaker separation
│   └── lyrics_detection.py    # Music filtering
├── translate/
│   ├── translate.py           # Translation orchestration
│   ├── indictrans2.py         # Indian languages
│   ├── google_translate.py    # Other languages
│   └── retranslate.py         # Term correction
├── subtitles/
│   └── subtitles.py           # SRT/VTT generation
└── shared/
    ├── logger.py              # Centralized logging
    ├── config.py              # Configuration
    └── utils.py               # Common utilities
```

### Extension Points

Add new features by:
1. Creating stage module
2. Implementing standard interface
3. Adding configuration options
4. Updating pipeline orchestration

See [Developer Guide](../DEVELOPER_GUIDE.md) for details.

## Getting Help

### Documentation

- **[Documentation Index](../INDEX.md)** - All documentation
- **[User Guide](../user-guide/README.md)** - Usage guides
- **[Developer Guide](../DEVELOPER_GUIDE.md)** - Development

### Specific Topics

- **Architecture Questions**: [Architecture](architecture.md)
- **Pipeline Details**: [Pipeline](pipeline.md)
- **Environment Issues**: [Multi-Environment](multi-environment.md)
- **Language Support**: [Language Support](language-support.md)

---

**Navigation**: [Home](../../README.md) | [Documentation Index](../INDEX.md) | [Architecture](architecture.md)
