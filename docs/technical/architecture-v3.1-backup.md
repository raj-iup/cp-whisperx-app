# Architecture Blueprint

**CP-WhisperX-App v3.0.1** | Multi-Environment Architecture

**Document Version:** 3.1  
**Last Updated:** December 4, 2025  
**Compliance Status:** 🎊 100% Perfect Compliance  
**Pre-commit Hook:** ✅ Active  
**Architecture Reference:** See ARCHITECTURE_ALIGNMENT_2025-12-04.md for decisions

**Major Updates in v3.1 (December 4, 2025 14:00 UTC):**
- 🐛 **Bug #4 Fixed**: Bias window generator import path corrected
- 🏛️ **AD-007**: Consistent shared/ import paths (MANDATORY)
- ✅ **All Imports**: Must use "shared." prefix for shared/ modules
- 📝 **Standard Pattern**: Documented for top-level and lazy imports

**Major Updates in v3.0 (December 4, 2025):**
- 🏛️ **AD-006**: Job-specific parameters override system defaults (MANDATORY)
- 📋 **Configuration Hierarchy**: 4-tier priority system documented
- ✅ **All Stages**: Must honor user's explicit choices from job.json
- 🐛 **Bug #3 Fixed**: Language detection now reads from job.json

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Decisions](#architecture-decisions)
3. [Configuration Hierarchy](#configuration-hierarchy) ⭐ NEW
4. [Multi-Environment Strategy](#multi-environment-strategy)
5. [Translation Routing](#translation-routing)
6. [Workflow Orchestration](#workflow-orchestration)
7. [Data Flow](#data-flow)
8. [Error Handling](#error-handling)

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

**Current Architecture:** v3.0 (12-Stage Context-Aware Pipeline)  
**Target Architecture:** v3.0 (Production Ready)  
**Migration Progress:** 75% Complete (Phase 4 - Stage Integration)

### Architecture Component Status

| Component | Documented | Implemented | Tested | Status |
|-----------|------------|-------------|--------|--------|
| 12-Stage Architecture | ✅ | ✅ 100% | ⚠️ 40% | 🟢 Excellent |
| Logging System | ✅ | ✅ 100% | ✅ 80% | 🟢 Excellent |
| Manifest Tracking | ✅ | ✅ 100% | ⚠️ 60% | 🟢 Excellent |
| Configuration | ✅ | ✅ 100% | ✅ 90% | 🟢 Excellent |
| Error Handling | ✅ | ✅ 90% | ⚠️ 50% | 🟢 Good |
| Multi-Environment | ✅ | ✅ 100% | ✅ 85% | 🟢 Excellent |
| Stage Isolation | ✅ | ✅ 100% | ⚠️ 60% | 🟢 Excellent |
| StageIO Pattern | ✅ | ✅ 100% | ✅ 70% | 🟢 Excellent |
| Context-Aware | ✅ | ✅ 90% | ⚠️ 40% | 🟢 Good |

### Current vs Target

**What Works Now (v3.0 - 75% Complete):**
- ✅ 12-stage modular pipeline (fully implemented)
- ✅ Multi-environment architecture (8 venvs, fully functional)
- ✅ Translation engine routing (IndicTrans2 + NLLB)
- ✅ Hardware-aware compute selection (MLX/CUDA/CPU)
- ✅ Configuration system (100% compliant)
- ✅ Logging infrastructure (dual logging + manifests)
- ✅ Universal StageIO pattern adoption (100%)
- ✅ Complete manifest tracking (100%)
- ✅ Context-aware processing (90% - subtitle workflow)
- ✅ Stage isolation enforced (100%)

**What's In Progress (Phase 4 - 75%):**
- 🔄 End-to-end testing (blocked by MLX backend issue)
- 🔄 Performance optimization (needs test baseline)
- 🔄 Error recovery improvements
- 🔄 Documentation updates (this document)

**What's Coming (Phase 5 - Advanced Features):**
- ⏳ Intelligent caching system (ML-based)
- ⏳ Adaptive quality prediction
- ⏳ Context learning from history
- ⏳ Circuit breakers and retry logic
- ⏳ Cost tracking and optimization

**See:** [IMPLEMENTATION_TRACKER.md](../../IMPLEMENTATION_TRACKER.md) for detailed progress tracking.

---

## 12-Stage Pipeline

**Current Architecture (v3.0):** 12 stages with clear separation of concerns.

### Stage Overview

```
01_demux              → Audio extraction (FFmpeg)
02_tmdb               → Metadata fetch (subtitle workflow only)
03_glossary_load      → Terminology loading
04_source_separation  → Vocal isolation (adaptive)
05_pyannote_vad       → Voice activity + diarization
06_whisperx_asr       → Speech recognition (MLX/WhisperX/CUDA)
07_alignment          → Word-level alignment
08_lyrics_detection   → Song segment detection (subtitle workflow)
09_hallucination_removal → ASR cleanup (subtitle workflow)
10_translation        → IndicTrans2 + NLLB
11_subtitle_generation → Multi-language VTT/SRT
12_mux                → Soft-embed subtitles
```

### Stage Complexity Analysis

**Most stages:** 140-450 LOC (optimal size)  
**Large stages:** 2 only
- **Stage 02 (TMDB):** 548 LOC - Cohesive API client
- **Stage 10 (Translation):** 1045 LOC - Cohesive translation engine

**Helper Modules:**
- **whisperx_integration.py:** 1697 LOC - ASR implementation (needs modularization)
- **shared/asr_chunker.py:** 366 LOC - Large file handling

**Architectural Decision:** Keep 12-stage architecture as-is. Focus refactoring on helper modules, not stages.

**See:** [ARCHITECTURE_ALIGNMENT_2025-12-04.md](../../ARCHITECTURE_ALIGNMENT_2025-12-04.md) for detailed analysis.

### Workflow-Stage Mapping

**Transcribe Workflow (7 stages):**
```
01_demux → 03_glossary_load → [04_source_separation*] 
→ 05_pyannote_vad → 06_whisperx_asr → 07_alignment
```

**Translate Workflow (8 stages):**
```
01_demux → 03_glossary_load → [04_source_separation*]
→ 05_pyannote_vad → 06_whisperx_asr → 07_alignment → 10_translation
```

**Subtitle Workflow (12 stages):**
```
01_demux → 02_tmdb → 03_glossary_load → [04_source_separation*]
→ 05_pyannote_vad → 06_whisperx_asr → 07_alignment
→ 08_lyrics_detection → 09_hallucination_removal
→ 10_translation → 11_subtitle_generation → 12_mux
```

*Optional/adaptive stages: 04_source_separation (enabled based on audio quality)

### Stage Criticality

| Stage | Transcribe | Translate | Subtitle | Adaptive |
|-------|------------|-----------|----------|----------|
| 01_demux | ✅ Required | ✅ Required | ✅ Required | No |
| 02_tmdb | ❌ Disabled | ❌ Disabled | ✅ Required | No |
| 03_glossary_load | ✅ Recommended | ✅ Recommended | ✅ Required | No |
| 04_source_separation | ⚠️ Optional | ⚠️ Optional | ⚠️ Optional | Yes (SNR<15dB) |
| 05_pyannote_vad | ✅ Required | ✅ Required | ✅ Required | No |
| 06_whisperx_asr | ✅ Required | ✅ Required | ✅ Required | No |
| 07_alignment | ✅ Required | ✅ Required | ✅ Required | No |
| 08_lyrics_detection | ❌ N/A | ❌ N/A | ✅ MANDATORY | No |
| 09_hallucination_removal | ❌ N/A | ❌ N/A | ✅ MANDATORY | No |
| 10_translation | ❌ N/A | ✅ Required | ✅ Required | No |
| 11_subtitle_generation | ❌ N/A | ❌ N/A | ✅ Required | No |
| 12_mux | ❌ N/A | ❌ N/A | ✅ Required | No |

---

## Architecture Decisions

### AD-001: Keep 12-Stage Architecture
**Status:** ✅ APPROVED  
**Decision:** No major refactoring needed

### AD-002: Modularize ASR Helper  
**Status:** ✅ APPROVED  
**Decision:** Split whisperx_integration.py into modules

### AD-003: Defer Translation Refactoring  
**Status:** ⏳ DEFERRED (Phase 5)  
**Decision:** Keep Stage 10 as single cohesive unit

### AD-004: Virtual Environment Complete  
**Status:** ✅ APPROVED  
**Decision:** Current 8 venvs are optimal

### AD-005: Use WhisperX Backend  
**Status:** ✅ APPROVED  
**Decision:** Default to WhisperX, avoid MLX

### AD-006: Job Parameters Override System Config ⭐  
**Status:** ✅ **MANDATORY** (All stages)  
**Decision:** Job-specific parameters take priority over system defaults

**Why This Matters:**
- User's explicit CLI choices must be respected
- Enables per-job customization without global changes
- Fixed Bug #3 (language detection)

**Applies To:** All 12 stages

### AD-007: Consistent Shared Import Paths ⭐ NEW  
**Status:** ✅ **MANDATORY** (All code)  
**Decision:** All imports from shared/ MUST use "shared." prefix

**Why This Matters:**
- Python requires consistent module paths
- Lazy imports were using incorrect paths
- Fixed Bug #4 (bias window generator import)
- Prevents silent feature degradation

**Pattern:**
```python
# CORRECT - Both top-level and lazy
from shared.bias_window_generator import BiasWindow

def function():
    from shared.bias_window_generator import create_bias_windows
```

**Applies To:** All scripts and stages

**See:** [ARCHITECTURE_ALIGNMENT_2025-12-04.md](../../ARCHITECTURE_ALIGNMENT_2025-12-04.md) for complete decision rationale.

---

## Configuration Hierarchy

**⭐ NEW (December 4, 2025) - Architectural Decision AD-006**

All stages must follow this priority order when loading configuration parameters:

### Priority Order (Highest to Lowest)

```
1. job.json                      ← User's explicit CLI choices
   ↓
2. job-YYYYMMDD-user-NNNN.env    ← Job-specific overrides
   ↓
3. config/.env.pipeline           ← System defaults
   ↓
4. Code defaults                  ← Hardcoded fallbacks
```

### Implementation Pattern

```python
# 1. Load system defaults
config = load_config()
source_lang = getattr(config, 'whisper_language', 'hi')

# 2. Override with job.json (MANDATORY)
job_json_path = job_dir / "job.json"
if job_json_path.exists():
    with open(job_json_path) as f:
        job_data = json.load(f)
        if 'source_language' in job_data and job_data['source_language']:
            source_lang = job_data['source_language']  # Job takes priority
```

### Parameters That Must Be Overridable

- ✅ Languages (source_language, target_languages)
- ✅ Model settings (model size, compute type, batch size)
- ✅ Quality settings (beam size, temperature)
- ✅ Workflow flags (source_separation_enabled, tmdb_enabled)
- ✅ Output preferences (subtitle format, translation engine)

### Why This Is Mandatory

1. **User Intent:** Respect explicit CLI parameters
2. **Reproducibility:** Same job.json = same results
3. **Flexibility:** Per-job customization without global changes
4. **Testing:** Isolated test configs

**Compliance:** All 12 stages must implement this pattern (Bug #3 fix elevated to architectural standard)

**Status:** ✅ MANDATORY as of 2025-12-04

---

### AD-004: Virtual Environment Structure Complete

**Decision**: Current 8 virtual environments cover all components - No new venvs needed.

**Rationale**:
- Each ML model has isolated environment
- Common utilities in shared venv
- No dependency conflicts
- Bootstrap scripts handle all environments

**Environments (8 Total - COMPLETE):**

| Environment | Purpose | Stages | Size | Status |
|-------------|---------|--------|------|--------|
| `venv/common` | Core utilities (FFmpeg, logging, config) | All stages | ~500 MB | ✅ Complete |
| `venv/whisperx` | WhisperX + faster-whisper (ASR) | 06 | ~2 GB | ✅ Complete |
| `venv/mlx` | MLX-Whisper (macOS GPU acceleration) | 06, 07 | ~1.5 GB | ✅ Complete |
| `venv/pyannote` | PyAnnote VAD + diarization | 05 | ~1 GB | ✅ Complete |
| `venv/demucs` | Demucs source separation | 04 | ~1.2 GB | ✅ Complete |
| `venv/indictrans2` | IndicTrans2 Indic→English | 10 | ~3 GB | ✅ Complete |
| `venv/nllb` | NLLB-200 universal translation | 10 | ~2.5 GB | ✅ Complete |
| `venv/llm` | Future LLM features | TBD | ~2 GB | ⏳ Reserved |

**Total Disk Space:** ~14 GB (excluding models)

**See:** [ARCHITECTURE_ALIGNMENT_2025-12-04.md](../../ARCHITECTURE_ALIGNMENT_2025-12-04.md) § AD-004

---

### AD-001: Keep 12-Stage Architecture

**Decision**: Current 12-stage architecture is optimal - No major refactoring needed.

**Rationale**:
- Clear separation of concerns
- Single responsibility per stage
- Manageable stage sizes (140-550 LOC)
- Only 2 "large" stages are cohesive units

**See:** [ARCHITECTURE_ALIGNMENT_2025-12-04.md](../../ARCHITECTURE_ALIGNMENT_2025-12-04.md) § AD-001

---

### AD-002: Modularize ASR Helper (Not Stage)

**Decision**: Split `whisperx_integration.py` into module directory, keep stage as-is.

**Problem**: whisperx_integration.py (1697 LOC) has god object pattern.

**Solution**:
```
Stage 06: whisperx_asr.py (140 LOC wrapper) ← NO CHANGE
          ↓ uses
scripts/whisperx/ (NEW MODULE)
├── __init__.py
├── model_manager.py       (~200 LOC)
├── backend_abstraction.py (~300 LOC)
├── bias_prompting.py      (~400 LOC)
├── chunking.py            (~300 LOC)
├── transcription.py       (~300 LOC)
└── postprocessing.py      (~200 LOC)
```

**Benefits:**
- Better code organization
- Easier to test components
- No workflow disruption
- Same venv (venv/whisperx)

**Timeline:** 1-2 days (waiting for E2E tests to stabilize)

**See:** [ARCHITECTURE_ALIGNMENT_2025-12-04.md](../../ARCHITECTURE_ALIGNMENT_2025-12-04.md) § AD-002

---

### AD-003: Defer Translation Stage Refactoring

**Decision**: Keep translation as single stage, defer 4-stage split indefinitely.

**Rationale**:
- Current implementation (1045 LOC) is cohesive (single responsibility)
- Splitting would require renumbering all subsequent stages (11→14, 12→15)
- Adds 3 stages for minimal benefit
- Can refactor to helper modules later if needed (like ASR)

**See:** [ARCHITECTURE_ALIGNMENT_2025-12-04.md](../../ARCHITECTURE_ALIGNMENT_2025-12-04.md) § AD-003

---

### AD-005: Multi-Environment Strategy

**Decision**: Use separate virtual environments for each major component.

**Rationale**:
- **Dependency Isolation**: WhisperX, IndicTrans2, and NLLB have conflicting PyTorch versions
- **Selective Installation**: Users only install what they need
- **Stability**: Issues in one environment don't affect others
- **Upgradability**: Can upgrade components independently

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

### Intelligent Caching System (v3.0)

**Purpose:** Enable subsequent workflows with similar media to perform optimally over time.

**Architecture:** 5-layer caching system integrated across all stages

```
┌──────────────────────────────────────────────────────┐
│         Intelligent Caching Architecture             │
└──────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
   │Layer 1  │    │Layer 2  │    │Layer 3  │
   │Model    │    │Audio    │    │ASR      │
   │Weights  │    │Finger-  │    │Results  │
   │         │    │prints   │    │         │
   └─────────┘    └─────────┘    └─────────┘
        │               │               │
   ┌────▼────┐    ┌────▼────┐
   │Layer 4  │    │Layer 5  │
   │Trans-   │    │Glossary │
   │lation   │    │Learning │
   │Memory   │    │         │
   └─────────┘    └─────────┘
```

**Caching Layers:**

1. **Model Weights Cache (Global)**
   - Location: `{cache_dir}/models/`
   - Stores: Downloaded model weights (WhisperX, IndicTrans2, PyAnnote)
   - Benefits: Avoid re-downloading 1-5 GB per run
   - Management: Automatic cleanup based on age and usage

2. **Audio Fingerprint Cache**
   - Location: `{cache_dir}/fingerprints/`
   - Stores: Audio characteristics, detected language, noise profile
   - Cache Key: Chromaprint + SHA256 of audio content
   - Benefits: Skip demux/analysis for identical media

3. **ASR Results Cache (Quality-Aware)**
   - Location: `{cache_dir}/asr/`
   - Cache Key: `SHA256(audio_content + model_version + language + config_params)`
   - Stores: Transcribed segments, word timestamps, confidence scores
   - Benefits: Reuse ASR results for same audio (saves 2-10 minutes)
   - Invalidation: Model version change, config parameter change, or `--no-cache` flag

4. **Translation Cache (Contextual)**
   - Location: `{cache_dir}/translations/`
   - Cache Key: `SHA256(source_text + src_lang + tgt_lang + glossary_hash + context)`
   - Context-Aware Matching:
     - Exact segment match: 100% reuse
     - Similar segment (>80% similarity): Reuse with adjustment
     - Different context: Fresh translation
   - Benefits: Reuse translations for similar content (saves 1-5 minutes)

5. **Glossary Learning Cache**
   - Location: `{cache_dir}/glossary_learned/`
   - Stores: Per-movie learned terms, character names, cultural terms, frequency analysis
   - Learning Mechanisms:
     - Character name recognition from previous jobs
     - Cultural term patterns
     - Translation memory from approved translations
   - Benefits: Improve accuracy on subsequent processing of same movie/genre

**Cache Configuration:**
```bash
# config/.env.pipeline
ENABLE_CACHING=true
CACHE_DIR=~/.cp-whisperx/cache
CACHE_MAX_SIZE_GB=50
CACHE_ASR_RESULTS=true
CACHE_TRANSLATIONS=true
CACHE_AUDIO_FINGERPRINTS=true
CACHE_TTL_DAYS=90
```

**Expected Performance Improvements:**

| Scenario | First Run | Subsequent Run | Improvement |
|----------|-----------|----------------|-------------|
| Identical media | 10 min | 30 sec | 95% faster |
| Same movie, different cut | 10 min | 6 min | 40% faster |
| Similar Bollywood movie | 10 min | 8 min | 20% faster |
| Similar language/genre | 10 min | 9 min | 10% faster |

**See:** `docs/technical/caching-ml-optimization.md` for complete caching architecture

### ML-Based Optimization (v3.0)

**Purpose:** Use machine learning to adaptively optimize processing based on media characteristics.

**Components:**

1. **Adaptive Quality Prediction**
   - ML Model: Lightweight XGBoost classifier
   - Features: Audio quality metrics (SNR, clarity, speech rate, noise level)
   - Predictions:
     - Optimal Whisper model size (base/small/medium/large)
     - Source separation needed? (yes/no)
     - Expected ASR confidence
     - Processing time estimate
   - Benefits: 30% faster processing on clean audio (use smaller model)

2. **Context Learning from History**
   - Character name recognition from previous jobs
   - Cultural term patterns learning
   - Translation memory from approved translations
   - Benefits: Consistent terminology, higher accuracy over time

3. **Similarity-Based Optimization**
   - Detects similar media via audio fingerprinting
   - Reuses processing decisions, glossaries, model selection
   - Similarity metrics:
     - Audio fingerprint matching (chromaprint)
     - Content-based similarity (same movie, different versions)
     - Language/accent similarity
     - Genre similarity
   - Benefits: 40-95% time reduction on similar content

**Optimization Flow:**

```
Input Media
    ↓
Analyze Characteristics (SNR, noise, duration, language)
    ↓
ML Quality Predictor
    ↓
Optimal Settings: [model: medium, source_sep: false, expected_conf: 0.92]
    ↓
Update Job Config Dynamically
    ↓
Process with Optimal Settings
    ↓
Record Results for Future Learning
```

**Configuration:**
```bash
# config/.env.pipeline
ENABLE_ML_OPTIMIZATION=true
ML_MODEL_SELECTION=adaptive
ML_QUALITY_PREDICTION=true
ML_LEARNING_FROM_HISTORY=true
SIMILAR_CONTENT_THRESHOLD=0.80
```

**See:** `docs/technical/caching-ml-optimization.md` for ML algorithms and training

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
- **[ARCHITECTURE_ALIGNMENT_2025-12-04.md](../../ARCHITECTURE_ALIGNMENT_2025-12-04.md)** - **AUTHORITATIVE** architecture decisions
- **[CANONICAL_PIPELINE.md](../../CANONICAL_PIPELINE.md)** - 12-stage pipeline definitions
- **[IMPLEMENTATION_TRACKER.md](../../IMPLEMENTATION_TRACKER.md)** - Progress tracking (75% Phase 4)
- **[Pipeline Architecture](pipeline.md)** - Detailed stage-by-stage processing flow
- **[Multi-Environment Setup](multi-environment.md)** - Virtual environment isolation strategy

### Development & Standards
- **[Developer Standards](../developer/DEVELOPER_STANDARDS.md)** - Code patterns and best practices
- **[Code Examples](../CODE_EXAMPLES.md)** - Practical implementation examples
- **[Copilot Instructions](../../.github/copilot-instructions.md)** - Quick development reference

### Refactoring Plans
- **[ASR_STAGE_REFACTORING_PLAN.md](../../ASR_STAGE_REFACTORING_PLAN.md)** - Approved (Option 2 - modularize helper)
- **[TRANSLATION_STAGE_REFACTORING_PLAN_NUMERIC.md](../../TRANSLATION_STAGE_REFACTORING_PLAN_NUMERIC.md)** - Deferred

### Logging & Monitoring
- **[Logging Architecture](../logging/LOGGING_ARCHITECTURE.md)** - Main logging design
- **[Stage Logging Architecture](../logging/STAGE_LOGGING_ARCHITECTURE.md)** - Per-stage logging patterns

### Component Architecture
- **[Glossary Architecture](../../shared/GLOSSARY_ARCHITECTURE.md)** - Translation and terminology system

### Quality & Automation
- **[Pre-commit Hook Guide](../PRE_COMMIT_HOOK_GUIDE.md)** - Automated compliance enforcement
- **[E2E_TEST_EXECUTION_PLAN.md](../../E2E_TEST_EXECUTION_PLAN.md)** - Testing roadmap

---

**Version**: 3.0  
**Last Updated**: December 4, 2025 12:36 UTC  
**Status:** ✅ ALIGNED with v3.0 architecture (75% complete, Phase 4)
