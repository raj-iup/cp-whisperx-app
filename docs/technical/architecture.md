# Architecture Blueprint

**CP-WhisperX-App v2.0.0** | Multi-Environment Architecture

**Document Version:** 2.0  
**Last Updated:** December 3, 2025  
**Compliance Status:** 🎊 100% Perfect Compliance  
**Pre-commit Hook:** ✅ Active

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Decisions](#architecture-decisions)
3. [Multi-Environment Strategy](#multi-environment-strategy)
4. [Translation Routing](#translation-routing)
5. [Workflow Orchestration](#workflow-orchestration)
6. [Data Flow](#data-flow)
7. [Error Handling](#error-handling)

---

## System Overview

CP-WhisperX-App is a multi-stage pipeline for transcription, translation, and subtitle generation with specialized virtual environments to avoid dependency conflicts.

```
┌─────────────────────────────────────────────────────────────┐
│                     CP-WhisperX-App                          │
│                 Multi-Environment Pipeline                   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │Transcribe│         │Translate│          │Subtitle │
   │Workflow │          │Workflow │          │Workflow │
   └─────────┘          └─────────┘          └─────────┘
        │                     │                     │
   ┌────▼─────────────────────▼─────────────────────▼────┐
   │              Pipeline Orchestrator                   │
   │         (Environment-Aware Stage Execution)          │
   └─────────────────────────┬──────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐          ┌───▼────┐          ┌───▼────┐
   │.venv-   │          │.venv-  │          │.venv-  │
   │common   │          │whisperx│          │indic-* │
   │         │          │        │          │        │
   │Core     │          │ASR     │          │Trans-  │
   │Utils    │          │Engine  │          │lation  │
   └─────────┘          └────────┘          └────────┘
```

---

## ⚠️ Implementation Status

**Current Architecture:** v2.0 (Simplified 3-6 Stage Pipeline)  
**Target Architecture:** v3.0 (Modular 10-Stage Pipeline)  
**Migration Progress:** 55% Complete

### Architecture Component Status

| Component | Documented | Implemented | Tested | Status |
|-----------|------------|-------------|--------|--------|
| Stage Architecture | ✅ | ⚠️ 30% | ⚠️ 20% | 🟡 Partial |
| Logging System | ✅ | ✅ 90% | ⚠️ 40% | 🟢 Good |
| Manifest Tracking | ✅ | ⚠️ 40% | ⚠️ 30% | 🟡 Partial |
| Configuration | ✅ | ✅ 100% | ✅ 80% | 🟢 Excellent |
| Error Handling | ✅ | ✅ 70% | ⚠️ 30% | 🟢 Good |
| Multi-Environment | ✅ | ✅ 95% | ⚠️ 50% | 🟢 Good |
| Stage Isolation | ✅ | ⚠️ 60% | ⚠️ 25% | 🟡 Partial |

### Current vs Target

**What Works Now (v2.0):**
- ✅ Multi-environment architecture (fully implemented)
- ✅ Translation engine routing (fully implemented)
- ✅ Hardware-aware compute selection (fully implemented)
- ✅ Configuration system (100% compliant)
- ✅ Logging infrastructure (90% compliant)
- ⚠️ Simplified 3-6 stage workflows (functional but not modular)

**What's Coming (v3.0):**
- ⏳ Modular 10-stage pipeline with enable/disable per stage
- ⏳ Universal StageIO pattern adoption (currently 5%)
- ⏳ Complete manifest tracking (currently 40%)
- ⏳ Stage-level testing infrastructure
- ⏳ Stage dependency validation
- ⏳ Advanced features (retry logic, circuit breakers, caching)

**See:** [Architecture Implementation Roadmap](../ARCHITECTURE_IMPLEMENTATION_ROADMAP.md) for 21-week migration plan.

---

## Architecture Decisions

### AD-001: Multi-Environment Architecture

**Decision**: Use separate virtual environments for each major component instead of a monolithic environment.

**Rationale**:
- **Dependency Isolation**: WhisperX, IndicTrans2, and NLLB have conflicting PyTorch/transformers versions
- **Selective Installation**: Users only install components they need
- **Stability**: Issues in one environment don't affect others
- **Upgradability**: Can upgrade individual components independently

**Environments**:
1. `venv/common` - Core utilities (FFmpeg, logging, job management)
2. `venv/whisperx` - WhisperX + faster-whisper (ASR)
3. `venv/mlx` - MLX-Whisper (macOS GPU acceleration)
4. `venv/indictrans2` - IndicTrans2 Indic→English
5. `.venv-indic-indic` - IndicTrans2 Indic→Indic
6. `venv/nllb` - NLLB-200 universal translation

### AD-002: Translation Engine Routing

**Decision**: Route translation requests to specialized engines based on language pair.

**Rationale**:
- **Quality**: IndicTrans2 provides superior quality for Indic languages
- **Coverage**: NLLB-200 covers 200+ languages not in IndicTrans2
- **Efficiency**: Use best tool for each language pair

**Routing Logic**:
```python
if source in INDIC_LANGS and target == "en":
    engine = "indictrans2-en"
    environment = "venv/indictrans2"
elif source in INDIC_LANGS and target in INDIC_LANGS:
    engine = "indictrans2-indic"
    environment = ".venv-indic-indic"
else:
    engine = "nllb-200"
    environment = "venv/nllb"
```

### AD-003: Hardware-Aware Compute Type Selection

**Decision**: Automatically select compute type based on available hardware.

**Rationale**:
- **Error Prevention**: CPU cannot use float16 efficiently
- **Performance**: CUDA benefits from float16
- **Stability**: MPS needs float32 for reliability

**Selection Matrix**:
| Hardware | Backend | Compute Type | Reason |
|----------|---------|--------------|--------|
| CPU | WhisperX | int8 | float16 not supported |
| CUDA | WhisperX | float16 | Faster inference |
| MPS (Intel) | WhisperX | float32 | Stability |
| Apple Silicon | MLX | float16 | Native acceleration |

### AD-004: Workflow Composition

**Decision**: Workflows can auto-execute prerequisite workflows.

**Rationale**:
- **User Experience**: Subtitle workflow auto-runs transcribe and translate if needed
- **Flexibility**: Users can run stages independently or as complete pipeline
- **Idempotency**: Pipeline skips already-completed stages

**Workflow Dependencies**:
```
transcribe: (no dependencies)
translate: requires transcribe
subtitle: requires transcribe + translate
```

---

## Multi-Environment Strategy

### Environment Isolation

Each environment has isolated:
- Python interpreter
- Dependency versions
- Model caches
- Configuration

### Environment Activation

Pipeline orchestrator activates correct environment for each stage:

```bash
# Stage: ASR (transcription)
source venv/whisperx/bin/activate
python scripts/whisperx_asr.py

# Stage: Translation (Indic→English)
source venv/indictrans2/bin/activate
python scripts/indictrans2_translator.py

# Stage: Muxing (video processing)
source venv/common/bin/activate  
python scripts/mux.py
```

### Shared Resources

Some resources shared across environments:
- Job configuration (`job.json`)
- Manifest tracking (`manifest.json`)
- Media files (audio, video)
- Transcript files (segments.json)

---

## Translation Routing

### Supported Language Pairs

#### IndicTrans2-En (`venv/indictrans2`)
- **Source**: 22 Indic languages
- **Target**: English only
- **Model**: AI4Bharat/indictrans2-en-1B

#### IndicTrans2-Indic (`.venv-indic-indic`)
- **Source**: 22 Indic languages
- **Target**: 22 Indic languages
- **Model**: AI4Bharat/indictrans2-indic-1B
- **Note**: Requires separate model installation

#### NLLB-200 (`venv/nllb`)
- **Source**: 200+ languages
- **Target**: 200+ languages
- **Model**: facebook/nllb-200-distilled-600M
- **Use Cases**: English→Spanish, English→Arabic, French→German

### One-to-Many Translation

Pipeline supports generating multiple target languages in single run:

```bash
# Generates: Hindi→English + Hindi→Gujarati + Hindi→Spanish
./prepare-job.sh movie.mp4 --subtitle -s hi -t en,gu,es
```

**Execution**:
1. Transcribe: Hindi audio → Hindi text
2. Translate to English: `venv/indictrans2`
3. Translate to Gujarati: `.venv-indic-indic`
4. Translate Hindi→English→Spanish: `venv/nllb` (pivot translation)
5. Generate 3 SRT files
6. Soft-embed all 3 subtitles in video

---

## Workflow Orchestration

### Three Main Workflows

#### 1. Transcribe Workflow
```
┌──────┐    ┌─────┐    ┌───────────┐    ┌────────┐
│Demux │───▶│ ASR │───▶│Alignment  │───▶│Export  │
│      │    │     │    │           │    │        │
└──────┘    └─────┘    └───────────┘    └────────┘
  common    whisperx      whisperx        common
```

**Output**: `segments.json`, `transcript.txt`

#### 2. Translate Workflow
```
┌──────────┐    ┌─────────────┐    ┌────────┐
│Load      │───▶│Translation  │───▶│Export  │
│Transcript│    │(routed)     │    │        │
└──────────┘    └─────────────┘    └────────┘
   common        indic*/nllb         common
```

**Output**: `transcript_{target}.txt`, `subtitle_{target}.srt`

#### 3. Subtitle Workflow
```
┌──────────┐    ┌─────────┐    ┌────────────┐    ┌─────┐
│Transcribe│───▶│Translate│───▶│Generate SRT│───▶│ Mux │
│(if needed│    │(all tgt)│    │            │    │     │
└──────────┘    └─────────┘    └────────────┘    └─────┘
   (above)       (above)           common          common
```

**Output**: Video file with soft-embedded subtitles

### Stage-to-Environment Mapping

| Stage | Environment | Purpose |
|-------|-------------|---------|
| demux | `venv/common` | Extract audio with FFmpeg |
| asr | `venv/whisperx` or `venv/mlx` | Transcribe audio |
| alignment | `venv/whisperx` | Word-level timestamps |
| export_transcript | `venv/common` | Save transcript files |
| indictrans2_en_translation | `venv/indictrans2` | Indic→English |
| indictrans2_indic_translation | `.venv-indic-indic` | Indic→Indic |
| nllb_translation | `venv/nllb` | Universal translation |
| subtitle_gen | `venv/common` | Generate SRT files |
| mux | `venv/common` | Embed subtitles in video |

---

## Data Flow

### File Organization

```
out/
└── 2025/
    └── 11/
        └── 20/
            └── username/
                └── job-id/
                    ├── job.json              # Job configuration
                    ├── manifest.json         # Stage tracking
                    ├── media/
                    │   ├── video.mp4         # Original or clipped video
                    │   └── audio.wav         # Extracted audio
                    ├── transcripts/
                    │   ├── segments.json     # WhisperX output
                    │   ├── transcript.txt    # Source transcript
                    │   ├── transcript_en.txt # English translation
                    │   └── transcript_gu.txt # Gujarati translation
                    ├── subtitles/
                    │   ├── subtitle_en.srt   # English subtitles
                    │   └── subtitle_gu.srt   # Gujarati subtitles
                    └── logs/
                        ├── 99_pipeline.log   # Main pipeline log
                        ├── 01_demux.log      # Stage logs
                        ├── 02_asr.log
                        └── 03_indictrans2_en.log
```

### Stage Artifacts

Each stage produces specific artifacts tracked in `manifest.json`:

```json
{
  "stages": {
    "demux": {
      "status": "completed",
      "artifacts": ["media/audio.wav"]
    },
    "asr": {
      "status": "completed",
      "artifacts": ["transcripts/segments.json"]
    },
    "indictrans2_en_translation": {
      "status": "completed",
      "artifacts": ["transcripts/transcript_en.txt", "subtitles/subtitle_en.srt"]
    }
  }
}
```

---

## Error Handling

### Environment Activation Failures

```python
try:
    env_manager.activate_environment("whisperx")
except EnvironmentNotFoundError:
    logger.error("WhisperX environment not found. Run ./bootstrap.sh")
    sys.exit(1)
```

### Unsupported Language Pairs

```python
if source == "hi" and target == "gu":
    if not env_manager.has_environment("indic-indic"):
        logger.error("Indic→Indic translation requires .venv-indic-indic")
        logger.info("Install: AI4Bharat/indictrans2-indic-1B model")
        sys.exit(1)
```

### Compute Type Mismatch

```python
if device == "cpu" and compute_type == "float16":
    logger.warning("CPU does not support float16, using int8")
    compute_type = "int8"
```

### Stage Failure Recovery

```bash
# Resume from last successful stage
./run-pipeline.sh -j job-id --resume
```

---

## Performance Considerations

### Model Caching

Models cached in `shared/model-cache/`:
- WhisperX: `~/.cache/whisperx/`
- IndicTrans2: `~/.cache/huggingface/`
- NLLB: `~/.cache/huggingface/`

### Batch Processing

ASR batch size auto-selected based on hardware:
- CPU: batch_size = 1
- CUDA: batch_size = 8
- MPS: batch_size = 4

### GPU Memory Management

```python
# Clear GPU cache between stages
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```

---

## Security Considerations

### API Keys

Store in `config/secrets.json` (gitignored):
```json
{
  "hf_token": "hf_...",
  "tmdb_api_key": "..."
}
```

### Model Provenance

All models from trusted sources:
- OpenAI (Whisper models)
- AI4Bharat (IndicTrans2)
- Meta (NLLB-200)

---

## Future Enhancements

1. **Streaming Translation**: Real-time subtitle generation
2. **Custom Models**: Support user-provided fine-tuned models
3. **Cloud Deployment**: Docker containers for cloud execution
4. **Web UI**: Browser-based job management interface
5. **Distributed Processing**: Multi-machine pipeline execution

---

## Related Documents

### Core Architecture
- **[Pipeline Architecture](pipeline.md)** - Detailed stage-by-stage processing flow
- **[Multi-Environment Setup](multi-environment.md)** - Virtual environment isolation strategy
- **[Architecture Index](../ARCHITECTURE_INDEX.md)** - Complete architecture documentation index

### Development & Standards
- **[Developer Standards](../developer/DEVELOPER_STANDARDS.md)** - Code patterns and best practices
- **[Code Examples](../CODE_EXAMPLES.md)** - Practical implementation examples
- **[Copilot Instructions](../../.github/copilot-instructions.md)** - Quick development reference

### Logging & Monitoring
- **[Logging Architecture](../logging/LOGGING_ARCHITECTURE.md)** - Main logging design
- **[Stage Logging Architecture](../logging/STAGE_LOGGING_ARCHITECTURE.md)** - Per-stage logging patterns

### Component Architecture
- **[Glossary Architecture](../../shared/GLOSSARY_ARCHITECTURE.md)** - Translation and terminology system

### Quality & Automation
- **[Pre-commit Hook Guide](../PRE_COMMIT_HOOK_GUIDE.md)** - Automated compliance enforcement

---

**Version**: 2.0.0  
**Last Updated**: December 3, 2025
