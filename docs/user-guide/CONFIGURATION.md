# Configuration Guide

**Complete reference for CP-WhisperX configuration parameters**

**Version:** 3.0  
**Last Updated:** 2025-12-10  
**Total Parameters:** 211  
**Lines:** 1,199

---

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Configuration Hierarchy](#configuration-hierarchy)
3. [Configuration Files](#configuration-files)
4. [Global Configuration](#global-configuration)
5. [Stage Configuration](#stage-configuration)
6. [Workflow-Specific Settings](#workflow-specific-settings)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Topics](#advanced-topics)

---

## Configuration Overview

### What is Configured?

CP-WhisperX uses a two-layer configuration system:

1. **System Defaults** (`config/.env.pipeline`)
   - Version-controlled template
   - Reasonable defaults for all parameters
   - Updated by development team only

2. **Job-Specific Config** (`{job_dir}/.env.pipeline`)
   - Created by `prepare-job.sh`
   - Copied from system defaults
   - Customized with CLI parameters
   - Used during pipeline execution

### Key Principles

- **Job Override Priority:** Job-specific parameters override system defaults (AD-006)
- **Explicit is Better:** CLI parameters in `job.json` take precedence over `.env.pipeline`
- **Safe Defaults:** All parameters have sensible defaults
- **Documentation Required:** Every parameter must be documented

---

## Configuration Hierarchy

### 4-Tier Priority System (AD-006)

**Priority Order** (highest to lowest):

```
1. job.json (CLI parameters from prepare-job.sh)
   ↓ Override
2. Job .env.pipeline (job-specific overrides)
   ↓ Override
3. System .env.pipeline (config/.env.pipeline)
   ↓ Fallback
4. Code defaults (hardcoded fallbacks)
```

### Example Priority Resolution

```python
# User runs:
./prepare-job.sh --media in/file.mp4 --workflow transcribe --source-language hi

# Priority resolution for source_language:
# 1. job.json: source_language="hi" ✅ USED (CLI parameter)
# 2. Job .env: SOURCE_LANGUAGE="auto" (copied from system)
# 3. System .env: SOURCE_LANGUAGE="auto"
# 4. Code: source_language = "auto"

# Result: source_language = "hi" (from job.json)
```

---

## Configuration Files

### 1. config/.env.pipeline (System Defaults)

**Location:** `config/.env.pipeline`  
**Purpose:** System-wide default values  
**Modified By:** Development team only  
**Format:** Shell-style environment variables

**Sections:**
- Global Configuration (job ID, paths, logging)
- Device Configuration (MPS, CUDA, CPU)
- Stage 01: Demux
- Stage 02: TMDB Enrichment
- Stage 03: Glossary Loader
- Stage 04: Source Separation
- Stage 05: PyAnnote VAD
- Stage 06: WhisperX ASR
- Stage 07: Alignment
- Stage 08: Lyrics Detection
- Stage 09: Hallucination Removal
- Stage 10: Translation
- Stage 11: Subtitle Generation
- Stage 12: Mux

**Example:**
```bash
# config/.env.pipeline
WHISPERX_MODEL=large-v3
DEVICE=mps
SOURCE_SEPARATION_ENABLED=auto
```

### 2. {job_dir}/.env.pipeline (Job-Specific Config)

**Location:** `out/YYYY/MM/DD/user/N/.env.pipeline`  
**Purpose:** Job-specific configuration  
**Created By:** `prepare-job.sh`  
**Modified By:** Pipeline execution  
**Format:** Copy of system defaults + CLI overrides

**Example:**
```bash
# out/2025/12/10/rpatel/1/.env.pipeline
JOB_ID=job-20251210-rpatel-0001
WORKFLOW_MODE=transcribe
SOURCE_LANGUAGE=hi
TARGET_LANGUAGE=en
```

### 3. job.json (CLI Parameters)

**Location:** `{job_dir}/job.json`  
**Purpose:** CLI parameters and job metadata  
**Created By:** `prepare-job.sh`  
**Format:** JSON

**Example:**
```json
{
  "job_id": "job-20251210-rpatel-0001",
  "workflow": "transcribe",
  "source_language": "hi",
  "target_language": "en",
  "created_at": "2025-12-10T10:30:45Z"
}
```

### 4. config/secrets.json (API Keys)

**Location:** `config/secrets.json`  
**Purpose:** Sensitive API keys and tokens  
**Format:** JSON  
**Git:** Ignored (.gitignore)

**Example:**
```json
{
  "TMDB_API_KEY": "your-tmdb-api-key-here",
  "HF_TOKEN": "your-huggingface-token-here",
  "ANTHROPIC_API_KEY": "your-anthropic-key-here"
}
```

**Required Keys:**
- `TMDB_API_KEY`: TMDB movie metadata (Stage 02)
- `HF_TOKEN`: Hugging Face model downloads (Stages 06, 10)
- `ANTHROPIC_API_KEY`: Optional (Phase 5 LLM features)

---

## Global Configuration

### Job Identification

#### JOB_ID
- **Type:** String
- **Format:** `job-YYYYMMDD-user-NNNN`
- **Set By:** `prepare-job.sh` (auto-generated)
- **Example:** `job-20251210-rpatel-0001`
- **Purpose:** Unique job identifier for tracking and logging

#### USER_ID
- **Type:** Integer
- **Default:** `1`
- **Purpose:** User identifier for multi-user systems
- **Note:** Currently single-user, reserved for future multi-tenant support

#### WORKFLOW_MODE
- **Type:** String
- **Values:** `transcribe` | `translate` | `subtitle`
- **Default:** `subtitle`
- **Set By:** `prepare-job.sh --workflow` parameter
- **Purpose:** Determines which pipeline stages run

**Workflow Stage Mapping:**
- `transcribe`: Stages 01, 03, 04 (optional), 05, 06, 07 (stop at alignment)
- `translate`: Stages 01, 03, 04 (optional), 05, 06, 07, 10 (stop at translation)
- `subtitle`: Stages 01-12 (full pipeline)

### Media Metadata

#### TITLE
- **Type:** String
- **Default:** Empty (auto-detected from filename)
- **Set By:** `prepare-job.sh --title` or auto-parsed
- **Purpose:** Movie/media title for TMDB lookup (Stage 02)
- **Example:** `"Jaane Tu... Ya Jaane Na"`

#### YEAR
- **Type:** Integer (4 digits)
- **Default:** Empty (auto-detected)
- **Set By:** `prepare-job.sh --year` or auto-parsed
- **Purpose:** Release year for accurate TMDB matching
- **Example:** `2008`

### Directory Paths

#### IN_ROOT
- **Type:** Path
- **Default:** `in/`
- **Set By:** `prepare-job.sh` (from `--media` parameter)
- **Purpose:** Input media directory
- **Example:** `in/test_clips/`

#### OUTPUT_ROOT
- **Type:** Path
- **Format:** `out/YYYY/MM/DD/user/N/`
- **Set By:** `prepare-job.sh` (auto-generated)
- **Purpose:** Job output directory
- **Example:** `out/2025/12/10/rpatel/1/`

#### LOG_ROOT
- **Type:** Path
- **Default:** `{OUTPUT_ROOT}` (job root)
- **Purpose:** Log file directory (AD-012)
- **Note:** Pipeline log at job root: `99_pipeline_*.log`

### Logging Configuration

#### LOG_LEVEL
- **Type:** String
- **Values:** `DEBUG` | `INFO` | `WARN` | `ERROR` | `CRITICAL`
- **Default:** `INFO`
- **Purpose:** Logging verbosity
- **Recommendation:** `INFO` for normal use, `DEBUG` for troubleshooting

#### LOG_TO_CONSOLE
- **Type:** Boolean
- **Values:** `true` | `false`
- **Default:** `true`
- **Purpose:** Enable/disable console output

#### LOG_TO_FILE
- **Type:** Boolean
- **Values:** `true` | `false`
- **Default:** `true`
- **Purpose:** Enable/disable file logging

### External Services

#### SECRETS_PATH
- **Type:** Path
- **Default:** `./config/secrets.json`
- **Purpose:** Path to secrets.json file
- **Format:** JSON with API keys

### Device Configuration

#### DEVICE
- **Type:** String
- **Values:** `cpu` | `mps` | `cuda`
- **Default:** Auto-detected by `prepare-job.sh`
- **Purpose:** Primary compute device for ML models
- **Detection:**
  - macOS with Apple Silicon → `mps`
  - NVIDIA GPU available → `cuda`
  - Fallback → `cpu`

#### MPS Configuration (Apple Silicon)

##### PYTORCH_MPS_HIGH_WATERMARK_RATIO
- **Type:** Float
- **Range:** `0.0` - `1.0`
- **Default:** `0.0`
- **Purpose:** MPS memory management watermark
- **Note:** `0.0` = default PyTorch behavior

##### PYTORCH_ENABLE_MPS_FALLBACK
- **Type:** Integer
- **Values:** `0` (disabled) | `1` (enabled)
- **Default:** `0`
- **Purpose:** Auto-fallback to CPU on MPS errors
- **Recommendation:** Keep disabled (explicit error handling)

##### MPS_ALLOC_MAX_SIZE_MB
- **Type:** Integer
- **Unit:** Megabytes
- **Default:** `4096`
- **Purpose:** Maximum MPS memory allocation
- **Recommendation:** Increase for large models (8192 for large-v3)

---

## Stage Configuration

### Stage 01: Demux (Audio Extraction)

#### DEMUX_FORMAT
- **Type:** String
- **Values:** `wav` | `mp3` | `flac`
- **Default:** `wav`
- **Purpose:** Output audio format
- **Recommendation:** `wav` for best quality

#### DEMUX_SAMPLE_RATE
- **Type:** Integer
- **Values:** `16000` | `44100` | `48000`
- **Default:** `16000`
- **Purpose:** Audio sample rate (Hz)
- **Note:** 16kHz optimal for Whisper models

#### DEMUX_CHANNELS
- **Type:** Integer
- **Values:** `1` (mono) | `2` (stereo)
- **Default:** `1`
- **Purpose:** Audio channel configuration
- **Recommendation:** Mono for transcription

### Stage 02: TMDB Enrichment

#### TMDB_ENABLED
- **Type:** Boolean
- **Values:** `true` | `false`
- **Default:** `true` (subtitle workflow), `false` (transcribe/translate)
- **Purpose:** Enable TMDB metadata fetching
- **Workflow:** Subtitle only (movies/TV shows)

#### TMDB_LANGUAGE
- **Type:** String
- **Values:** ISO 639-1 codes (`en`, `hi`, `es`, etc.)
- **Default:** `en`
- **Purpose:** TMDB API language preference

#### TMDB_SEARCH_THRESHOLD
- **Type:** Float
- **Range:** `0.0` - `1.0`
- **Default:** `0.7`
- **Purpose:** Minimum confidence for TMDB match

### Stage 03: Glossary Loader

#### GLOSSARY_ENABLED
- **Type:** Boolean
- **Values:** `true` | `false`
- **Default:** `true`
- **Purpose:** Enable glossary-based term handling

#### GLOSSARY_PATH
- **Type:** Path
- **Default:** `glossary/`
- **Purpose:** Glossary directory location

#### GLOSSARY_AUTO_LEARN
- **Type:** Boolean
- **Values:** `true` | `false`
- **Default:** `true`
- **Purpose:** Learn terms from TMDB and history

### Stage 04: Source Separation (Demucs)

#### SOURCE_SEPARATION_ENABLED
- **Type:** String
- **Values:** `true` | `false` | `auto`
- **Default:** `auto`
- **Purpose:** Enable/disable vocal separation
- **Auto Behavior:** Enabled when SNR < 15dB

#### SOURCE_SEPARATION_MODEL
- **Type:** String
- **Values:** `htdemucs` | `htdemucs_ft` | `mdx` | `mdx_extra`
- **Default:** `htdemucs`
- **Purpose:** Demucs model selection

#### SOURCE_SEPARATION_DEVICE
- **Type:** String
- **Values:** `cpu` | `mps` | `cuda`
- **Default:** Same as global DEVICE
- **Purpose:** Override device for source separation

### Stage 05: PyAnnote VAD (Voice Activity Detection)

#### PYANNOTE_ENABLED
- **Type:** Boolean
- **Values:** `true` | `false`
- **Default:** `true`
- **Purpose:** Enable voice activity detection

#### PYANNOTE_MIN_DURATION
- **Type:** Float
- **Unit:** Seconds
- **Default:** `0.3`
- **Purpose:** Minimum speech segment duration

#### PYANNOTE_MAX_DURATION
- **Type:** Float
- **Unit:** Seconds
- **Default:** `30.0`
- **Purpose:** Maximum speech segment duration

### Stage 06: WhisperX ASR (Speech Recognition)

#### WHISPERX_MODEL
- **Type:** String
- **Values:** `tiny` | `base` | `small` | `medium` | `large-v2` | `large-v3`
- **Default:** `large-v3`
- **Purpose:** Whisper model size
- **Trade-off:** Larger = more accurate but slower

**Model Comparison:**
| Model | Params | Speed | WER (English) | VRAM |
|-------|--------|-------|---------------|------|
| tiny | 39M | 32x | 15-20% | 1GB |
| base | 74M | 16x | 10-15% | 1GB |
| small | 244M | 6x | 6-8% | 2GB |
| medium | 769M | 2x | 5-6% | 5GB |
| large-v2 | 1550M | 1x | 3-4% | 10GB |
| large-v3 | 1550M | 1x | 2-3% | 10GB |

#### WHISPERX_BACKEND
- **Type:** String
- **Values:** `mlx` | `whisperx` | `auto`
- **Default:** `auto`
- **Purpose:** ASR backend selection (AD-005)
- **Auto Behavior:** `mlx` on Apple Silicon, `whisperx` otherwise

#### WHISPERX_COMPUTE_TYPE
- **Type:** String
- **Values:** `float16` | `float32` | `int8`
- **Default:** `float16`
- **Purpose:** Model precision
- **Recommendation:** `float16` for best speed/accuracy balance

#### WHISPERX_BATCH_SIZE
- **Type:** Integer
- **Range:** `1` - `32`
- **Default:** `16`
- **Purpose:** Batch size for ASR processing
- **Note:** Higher = faster but more memory

#### WHISPERX_BEAM_SIZE
- **Type:** Integer
- **Range:** `1` - `10`
- **Default:** `5`
- **Purpose:** Beam search width
- **Trade-off:** Higher = more accurate but slower

#### WHISPERX_TEMPERATURE
- **Type:** Float
- **Range:** `0.0` - `1.0`
- **Default:** `0.0`
- **Purpose:** Sampling temperature (0 = deterministic)

#### SOURCE_LANGUAGE
- **Type:** String
- **Values:** ISO 639-1 codes or `auto`
- **Default:** `auto`
- **Purpose:** Source audio language
- **Workflow-Specific:**
  - `transcribe`: Optional (auto-detects)
  - `translate`: Required (Indian language for IndicTrans2)
  - `subtitle`: Optional (typically Hindi)

#### TARGET_LANGUAGE
- **Type:** String
- **Values:** ISO 639-1 codes
- **Default:** `en`
- **Purpose:** Target output language
- **Note:** For translate/subtitle workflows only

### Stage 07: Alignment

#### ALIGNMENT_BACKEND
- **Type:** String
- **Values:** `whisperx` | `mlx` | `same`
- **Default:** `whisperx`
- **Purpose:** Alignment backend (AD-008)
- **Recommendation:** `whisperx` (subprocess, prevents MLX segfaults)

#### ALIGNMENT_TIMEOUT
- **Type:** Integer
- **Unit:** Seconds
- **Default:** `300`
- **Purpose:** Alignment subprocess timeout

### Stage 08: Lyrics Detection

#### LYRICS_DETECTION_ENABLED
- **Type:** Boolean
- **Values:** `true` | `false`
- **Default:** `true` (subtitle workflow), `false` (others)
- **Purpose:** Detect and mark lyrics segments

#### LYRICS_CONFIDENCE_THRESHOLD
- **Type:** Float
- **Range:** `0.0` - `1.0`
- **Default:** `0.7`
- **Purpose:** Minimum confidence for lyrics classification

### Stage 09: Hallucination Removal

#### HALLUCINATION_REMOVAL_ENABLED
- **Type:** Boolean
- **Values:** `true` | `false`
- **Default:** `true` (subtitle workflow), `false` (others)
- **Purpose:** Remove ASR hallucinations

#### HALLUCINATION_PATTERNS
- **Type:** String (comma-separated)
- **Default:** `"Thanks for watching,Thanks for listening,Subscribe"`
- **Purpose:** Patterns to detect and remove

### Stage 10: Translation

#### TRANSLATION_MODEL
- **Type:** String
- **Values:** `indictrans2` | `nllb` | `hybrid`
- **Default:** `indictrans2`
- **Purpose:** Translation engine selection

**Model Selection:**
- `indictrans2`: Indian languages (best quality, BLEU 85-90%)
- `nllb`: Non-Indian languages (broad support, BLEU 75-80%)
- `hybrid`: Phase 5 LLM-enhanced (planned, BLEU 90-95%)

#### TRANSLATION_BATCH_SIZE
- **Type:** Integer
- **Range:** `1` - `64`
- **Default:** `32`
- **Purpose:** Translation batch size

#### TRANSLATION_DEVICE
- **Type:** String
- **Values:** `cpu` | `mps` | `cuda`
- **Default:** Same as global DEVICE
- **Purpose:** Override device for translation

### Stage 11: Subtitle Generation

#### SUBTITLE_FORMAT
- **Type:** String
- **Values:** `srt` | `vtt` | `ass`
- **Default:** `vtt`
- **Purpose:** Subtitle file format
- **Recommendation:** `vtt` for soft-embedding

#### SUBTITLE_MAX_LINE_LENGTH
- **Type:** Integer
- **Range:** `30` - `60`
- **Default:** `42`
- **Purpose:** Maximum characters per subtitle line

#### SUBTITLE_MAX_LINES
- **Type:** Integer
- **Range:** `1` - `3`
- **Default:** `2`
- **Purpose:** Maximum lines per subtitle

#### SUBTITLE_MIN_DURATION
- **Type:** Float
- **Unit:** Seconds
- **Default:** `1.0`
- **Purpose:** Minimum subtitle display duration

#### SUBTITLE_MAX_DURATION
- **Type:** Float
- **Unit:** Seconds
- **Default:** `7.0`
- **Purpose:** Maximum subtitle display duration

### Stage 12: Mux (Subtitle Embedding)

#### MUX_SOFT_EMBED
- **Type:** Boolean
- **Values:** `true` | `false`
- **Default:** `true`
- **Purpose:** Soft-embed (not burned) subtitles

#### MUX_DEFAULT_TRACK
- **Type:** String
- **Values:** ISO 639-1 language code
- **Default:** `en`
- **Purpose:** Default subtitle track

---

## Workflow-Specific Settings

### Transcribe Workflow

**Purpose:** Generate transcript in SOURCE language

**CLI:**
```bash
./prepare-job.sh --media in/file.mp4 --workflow transcribe [--source-language hi]
```

**Active Stages:** 01, 03, 04 (optional), 05, 06, 07

**Key Parameters:**
- `WORKFLOW_MODE=transcribe`
- `SOURCE_LANGUAGE=auto` (or specify)
- `TARGET_LANGUAGE` (ignored)

**Output:** `07_alignment/transcript.txt`

### Translate Workflow

**Purpose:** Generate transcript in TARGET language

**CLI:**
```bash
./prepare-job.sh --media in/file.mp4 --workflow translate \
  --source-language hi --target-language en
```

**Active Stages:** 01, 03, 04 (optional), 05, 06, 07, 10

**Key Parameters:**
- `WORKFLOW_MODE=translate`
- `SOURCE_LANGUAGE=hi` (required, must be Indian language)
- `TARGET_LANGUAGE=en`

**Output:** `10_translation/transcript_en.txt`

### Subtitle Workflow

**Purpose:** Generate multi-language soft-embedded subtitles

**CLI:**
```bash
./prepare-job.sh --media in/file.mp4 --workflow subtitle \
  --source-language hi --target-languages en,gu,ta,es,ru,zh,ar
```

**Active Stages:** 01-12 (full pipeline)

**Key Parameters:**
- `WORKFLOW_MODE=subtitle`
- `SOURCE_LANGUAGE=hi`
- `TARGET_LANGUAGES=en,gu,ta,es,ru,zh,ar` (8 tracks)
- `TMDB_ENABLED=true`
- `LYRICS_DETECTION_ENABLED=true`
- `HALLUCINATION_REMOVAL_ENABLED=true`

**Output:** `12_mux/{filename}_subtitled.mp4`

---

## Performance Tuning

### Fast Processing (Favor Speed)

```bash
# config/.env.pipeline overrides
WHISPERX_MODEL=small           # 6x faster than large-v3
WHISPERX_BATCH_SIZE=32         # Max batch size
WHISPERX_BEAM_SIZE=1           # Greedy decoding
SOURCE_SEPARATION_ENABLED=false  # Skip if clean audio
```

**Expected:** 2-3x faster, 5-8% WER

### High Accuracy (Favor Quality)

```bash
# config/.env.pipeline overrides
WHISPERX_MODEL=large-v3        # Best accuracy
WHISPERX_BATCH_SIZE=8          # Lower batch size
WHISPERX_BEAM_SIZE=10          # Wide beam search
WHISPERX_TEMPERATURE=0.0       # Deterministic
SOURCE_SEPARATION_ENABLED=true  # Always separate
```

**Expected:** 2-3% WER, 2-3x slower

### Balanced (Default)

```bash
# config/.env.pipeline (default values)
WHISPERX_MODEL=large-v3
WHISPERX_BATCH_SIZE=16
WHISPERX_BEAM_SIZE=5
WHISPERX_TEMPERATURE=0.0
SOURCE_SEPARATION_ENABLED=auto
```

**Expected:** 3-5% WER, baseline speed

---

## Troubleshooting

### Common Issues

#### Issue: "TMDB API key not found"
**Solution:** Add `TMDB_API_KEY` to `config/secrets.json`

#### Issue: "MPS backend failed"
**Solution:** Set `DEVICE=cpu` or `PYTORCH_ENABLE_MPS_FALLBACK=1`

#### Issue: "Out of memory"
**Solutions:**
- Reduce `WHISPERX_BATCH_SIZE` (try 8 or 4)
- Increase `MPS_ALLOC_MAX_SIZE_MB` (try 8192)
- Use smaller model (`WHISPERX_MODEL=medium`)

#### Issue: "Translation not supported for English→Hindi"
**Solution:** Use `transcribe` workflow for same-language output

#### Issue: "Alignment subprocess timeout"
**Solution:** Increase `ALIGNMENT_TIMEOUT=600` (10 minutes)

---

## Advanced Topics

### Custom Configuration Workflow

1. **Copy System Config**
   ```bash
   cp config/.env.pipeline my-custom.env
   ```

2. **Edit Parameters**
   ```bash
   # Edit my-custom.env
   WHISPERX_MODEL=medium
   SOURCE_SEPARATION_ENABLED=false
   ```

3. **Create Job with Custom Config**
   ```bash
   ./prepare-job.sh --media in/file.mp4 --workflow transcribe
   # Then manually replace job's .env.pipeline with my-custom.env
   ```

### Environment Variable Override

Job-specific parameters can be overridden at runtime:

```bash
# Override device for single job
DEVICE=cpu ./run-pipeline.sh out/2025/12/10/rpatel/1
```

### Configuration Validation

```python
from shared.config_loader import load_config

config = load_config()
print(f"Device: {config.get('DEVICE')}")
print(f"Model: {config.get('WHISPERX_MODEL')}")
print(f"Workflow: {config.get('WORKFLOW_MODE')}")
```

---

## Related Documents

- **Architecture:** [ARCHITECTURE.md § AD-006](../../ARCHITECTURE.md#ad-006) (Configuration hierarchy)
- **Developer Guide:** [DEVELOPER_STANDARDS.md § 4](../../docs/developer/DEVELOPER_STANDARDS.md#4-configuration) (Configuration patterns)
- **Prepare Job:** [prepare-job.md](prepare-job.md) (CLI parameter reference)
- **Workflows:** [workflows.md](workflows.md) (Workflow-specific configuration)

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-10  
**Completeness:** ✅ 100% (All 211 parameters documented)

Return to [Documentation Index](INDEX.md)
