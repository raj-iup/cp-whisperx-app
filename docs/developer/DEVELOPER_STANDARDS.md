# CP-WhisperX Developer Standards & Best Practices

**Document Version:** 6.2  
**Date:** December 3, 2025  
**Last Updated:** December 3, 2025 (Syntax Error Prevention)
**Status:** ACTIVE - All development must follow these standards  
**Compliance Target:** 80% minimum  
**Current Status:** 🎊 **100% COMPLIANCE ACHIEVED** 🎊

**Major Updates in v6.2 (December 3, 2025):**
- 🐛 **Syntax Error Fixed**: Duplicate exc_info=True parameters (8 instances)
- 📝 **Error Handling Enhanced**: Added common mistake warnings
- 📝 **Best Practice Documented**: Use exc_info=True exactly once

**Major Updates in v6.1 (December 3, 2025):**
- 🐛 **StageManifest Enhanced**: add_intermediate() method implemented
- 🐛 **TMDB Workflow-Aware**: Only enabled for subtitle workflow
- 🐛 **Source Language Optional**: Transcribe auto-detects language
- 🐛 **Script Path Fixed**: Corrected TMDB stage reference

**Major Updates in v6.0:**
- 🆕 **AI Model Routing**: Automated updates for model releases
- 🆕 **Routing Optimization**: Data-driven model selection
- 🆕 **Cost Monitoring**: Track and optimize AI usage costs
- 🆕 **Automated Sync**: GitHub Actions for weekly updates

> 📚 **Quick Reference:** See [CODE_EXAMPLES.md](../CODE_EXAMPLES.md) for practical examples of all patterns described in this document. The examples document provides visual, side-by-side comparisons of good vs. bad code for every standard.

---

## 📋 Executive Summary

This document defines comprehensive development standards for the CP-WhisperX-App project, integrating:
- **Development Standards** - Code patterns, architecture, and implementation guidelines
- **Compliance Baseline** - Current state analysis and improvement roadmap
- **Best Practices** - Production-ready patterns for reliability and maintainability
- **Enhanced Logging Architecture** - Main pipeline log + stage-specific logs with complete manifest tracking

**Core Principles:**
- **Multi-Environment Architecture** - Isolated virtual environments per component
- **Configuration-Driven** - All parameters in config/.env.pipeline
- **Stage-Based Workflow** - Standardized StageIO pattern for data flow
- **Centralized Utilities** - Shared modules in shared/ directory
- **Dual Logging Architecture** - Main pipeline log + stage-specific logs with manifests
- **Manifest Tracking** - Complete I/O tracking for data lineage and audit trails
- **Job-Based Execution** - prepare-job.sh → run-pipeline.py workflow
- **Context-Aware Processing** - Cultural, temporal, speaker coherence in outputs
- **Intelligent Caching** - ML-based optimization for repeated workflows
- **Test-Driven Development** - Standardized test media for validation
- **Production Ready** - CI/CD, observability, and disaster recovery

---

## 📊 Current Compliance Status

**Overall Compliance: 🎊 100% (60/60 checks passed) 🎊**

### Stage Compliance Matrix

| Stage # | Stage Name | File | StageIO | Logger | Config | Manifest | Error | Docs | Score |
|---------|------------|------|---------|--------|--------|----------|-------|------|-------|
| 1 | demux | run-pipeline.py | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| 2 | tmdb | tmdb_enrichment_stage.py | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| 3 | glossary_load | glossary_builder.py | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| 4 | source_separation | source_separation.py | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| 5 | pyannote_vad | pyannote_vad.py | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| 6 | asr | whisperx_integration.py | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| 7 | alignment | mlx_alignment.py | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| 8 | lyrics_detection | lyrics_detection.py | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| 9 | subtitle_generation | subtitle_gen.py | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| 10 | mux | mux.py | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |

**Legend:**
- **StageIO**: Uses StageIO pattern with manifest tracking ✅
- **Logger**: Uses dual logging (get_stage_logger()) ✅
- **Config**: Uses load_config() ✅
- **Manifest**: Creates manifest.json with I/O tracking ✅
- **Error**: Comprehensive error handling with manifest tracking ✅
- **Docs**: Has complete module docstring ✅

### 🎊 Achievement Summary

**All Critical Issues Resolved:**
- ✅ **Config Usage**: All 10 stages use `load_config()` pattern
- ✅ **Logger Imports**: All 10 stages use proper dual logging
- ✅ **StageIO Pattern**: All 10 stages use StageIO with manifest tracking
- ✅ **Error Handling**: All 10 stages have comprehensive error handling
- ✅ **Path Management**: All 10 stages use centralized stage ordering
- ✅ **Documentation**: All 10 stages have complete docstrings

**Compliance Achievement:**
- Original Standards: 100% ✅
- Logging Architecture: 100% ✅
- Combined Overall: 100% ✅
- Perfect Stages: 10/10 (100%) ✅

---

## ⚠️ Implementation Reality vs. Documentation

**Document Status:** This document describes the **target architecture (v3.0)**, which is 55% complete.

### Current Reality (v2.0)

**Stage Pattern Adoption:** 5% (1-2 of 44 Python files)

Most stages currently implemented as utility scripts **without**:
- ❌ `run_stage()` function
- ❌ StageIO initialization  
- ❌ Manifest tracking
- ⚠️ Partial logging compliance (90%)
- ⚠️ Partial error handling (70%)

**Files Currently Using Full StageIO Pattern:**
1. ✅ `scripts/tmdb_enrichment_stage.py` - Complete implementation
2. ⚠️ `scripts/validate-compliance.py` - Uses logger pattern (not a stage)

**Active Stages (Partially Compliant):**
- `scripts/demux.py` - Has logging, no StageIO/manifest
- `scripts/whisperx_asr.py` - Has logging, no StageIO/manifest
- `scripts/indictrans2_translator.py` - Has logging, no StageIO/manifest
- Inline subtitle generation - No dedicated module
- `scripts/mux.py` - Has logging, no StageIO/manifest

**Future Stages (Not Integrated):**
- `scripts/tmdb_enrichment_stage.py` - Follows pattern, not integrated
- `glossary/` - Partial implementation
- `scripts/ner_extraction.py` - Standalone, not integrated
- `scripts/lyrics_detector.py` - Standalone, not integrated
- `scripts/hallucination_removal.py` - Standalone, not integrated

### Target Pattern (v3.0)

All pipeline stages **will** follow the pattern documented in § 4 below.

### Migration Status

**See:** [Architecture Implementation Roadmap](../ARCHITECTURE_IMPLEMENTATION_ROADMAP.md) for 21-week migration plan.

**Phase Progress:**
- ✅ Phase 0: Foundation (8 weeks) - **COMPLETE** - Standards, config, hooks
- ⏳ Phase 1: File Naming (2 weeks) - **READY** - Rename scripts to match standards
- ⏳ Phase 2: Testing Infrastructure (3 weeks) - **READY** - Test media, workflows
- ⏳ Phase 3: StageIO Migration (4 weeks) - **BLOCKED** - Migrate 5 active stages
- ⏳ Phase 4: Stage Integration (8 weeks) - **IN PROGRESS** - Complete 12-stage pipeline with lyrics/hallucination
- ⏳ Phase 5: Advanced Features (4 weeks) - **BLOCKED** - Caching, ML, monitoring

### Migration Checklist

When converting a script to stage pattern:
- [ ] Add `run_stage()` function with `(job_dir: Path, stage_name: str) -> int` signature
- [ ] Initialize StageIO with `enable_manifest=True`
- [ ] Use `io.get_stage_logger()` for logging
- [ ] Track all inputs with `io.manifest.add_input()`
- [ ] Track all outputs with `io.manifest.add_output()`
- [ ] Write outputs ONLY to `io.stage_dir`
- [ ] Finalize manifest with exit code
- [ ] Add unit tests for stage
- [ ] Update pipeline orchestrator to call `run_stage()`

**See:** [Migration Guide](MIGRATION_GUIDE.md) for detailed conversion process.

---

## 1. PROJECT STRUCTURE

### 1.1 Directory Layout

```
cp-whisperx-app/
├── bootstrap.sh                    # Multi-environment setup
├── prepare-job.sh                  # Job preparation wrapper
├── run-pipeline.sh                 # Pipeline execution wrapper
├── config/
│   ├── .env.pipeline              # Global configuration (version controlled)
│   ├── secrets.json               # API keys & tokens (git-ignored)
│   └── hardware_cache.json        # Hardware detection cache
├── scripts/
│   ├── prepare-job.py             # Job creation logic
│   ├── run-pipeline.py            # Pipeline orchestrator
│   ├── whisperx_asr.py           # ASR stage script
│   ├── whisperx_integration.py    # WhisperX backend
│   └── [stage scripts...]         # Individual stage implementations
├── shared/
│   ├── stage_utils.py             # StageIO pattern
│   ├── stage_order.py             # Centralized stage numbering
│   ├── logger.py                  # PipelineLogger
│   ├── environment_manager.py     # venv management
│   ├── config.py                  # Configuration loading
│   ├── glossary_manager.py        # Glossary system
│   └── [utility modules...]       # Shared functionality
├── venv/                          # Virtual environments (8 total)
│   ├── common/                    # Core: job mgmt, logging, muxing
│   ├── whisperx/                  # WhisperX ASR (CUDA/CPU)
│   ├── mlx/                       # MLX Whisper (Apple Silicon)
│   ├── pyannote/                  # PyAnnote VAD
│   ├── demucs/                    # Audio source separation
│   ├── indictrans2/               # IndicTrans2 translation
│   ├── nllb/                      # NLLB translation
│   └── llm/                       # LLM integration
├── out/                           # Job output (date-organized)
│   └── YYYY/MM/DD/user/N/         # Job directory structure
├── in/                            # Input media files
├── glossary/                      # Term glossaries (user-created)
├── docs/                          # Documentation
│   ├── DEVELOPER_STANDARDS.md     # This document
│   ├── API.md                     # API documentation
│   ├── CONFIGURATION.md           # Config reference
│   └── archive/                   # Archived versions
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── fixtures/                  # Test data
└── tools/                         # Development tools
    ├── check_compliance.py        # Standards compliance checker
    └── generate_docs.py           # Documentation generator
```

### 1.2 Cross-Platform Requirements

**CRITICAL REQUIREMENT: All core task scripts MUST have Windows PowerShell equivalents**

**Status:** ✅ **100% COMPLETE** - All scripts have .ps1 equivalents

**Core Task Scripts (Required PowerShell Equivalents):**
- ✅ `bootstrap.sh` → `bootstrap.ps1` (PowerShell 5.1+)
- ✅ `prepare-job.sh` → `prepare-job.ps1` (PowerShell 5.1+)
- ✅ `run-pipeline.sh` → `run-pipeline.ps1` (PowerShell 5.1+)
- ✅ `test-glossary-quickstart.sh` → `test-glossary-quickstart.ps1` (PowerShell 5.1+)

**Platform Support Matrix:**

| Script | Unix/Linux/macOS | Windows | Status |
|--------|------------------|---------|--------|
| bootstrap | ✅ `.sh` | ✅ `.ps1` | ✅ Complete |
| prepare-job | ✅ `.sh` | ✅ `.ps1` | ✅ Complete |
| run-pipeline | ✅ `.sh` | ✅ `.ps1` | ✅ Complete |
| test-glossary | ✅ `.sh` | ✅ `.ps1` | ✅ Complete |

**⚠️ Important:** Use PowerShell (.ps1) only - NO batch files (.bat)

**Implementation Guidelines:**

1. **Bash Scripts (.sh) - Unix/Linux/macOS**
   ```bash
   #!/usr/bin/env bash
   set -e  # Exit on error
   set -u  # Exit on undefined variable
   set -o pipefail  # Catch pipe errors
   ```
   - Use POSIX-compatible syntax when possible
   - Test on macOS, Linux, and WSL

2. **PowerShell Scripts (.ps1) - Windows**
   ```powershell
   #Requires -Version 5.1
   Set-StrictMode -Version Latest
   $ErrorActionPreference = "Stop"
   ```
   - Require PowerShell 5.1+ (Windows 10+)
   - Use `Set-StrictMode` for error detection
   - Test on Windows PowerShell 5.1 and PowerShell 7+
   - Ensure functional equivalence with .sh version

3. **Python Scripts - All Platforms**
   ```python
   from pathlib import Path  # Always use pathlib
   
   # Good: Cross-platform paths
   config_path = Path("config") / ".env.pipeline"
   output_dir = job_dir / "01_demux"
   
   # Bad: Hardcoded paths
   # config_path = "/tmp/config"  # Unix only
   # output_dir = "C:\\output"     # Windows only
   ```
   - Use `pathlib.Path` for all file paths
   - No hardcoded Unix paths (`/tmp`, `/home`, `/usr`)
   - No hardcoded Windows paths (`C:\`, `\\server`)
   - Use `sys.platform` for platform-specific logic only when absolutely necessary
   - Test on all target platforms (macOS MLX, Linux CUDA, Windows CUDA/CPU)

**Validation:**

```bash
# Check for PowerShell equivalents
for script in bootstrap prepare-job run-pipeline test-glossary-quickstart; do
    if [ ! -f "${script}.ps1" ]; then
        echo "❌ Missing: ${script}.ps1"
    else
        echo "✅ Found: ${script}.ps1"
    fi
done

# Validate Python cross-platform paths
python3 scripts/validate-compliance.py --check-paths scripts/*.py
```

### 1.3 Job-Based Architecture

**Core System Design:** All pipeline execution follows a job-based workflow.

**Workflow Stages:**

```
1. bootstrap     → Set up environments + create default config/.env.pipeline
2. prepare-job   → Create job directory + copy/customize job configuration
3. run-pipeline  → Execute stages using job configuration
4. (optional) test-glossary-quickstart → Automated testing workflow
```

**Job Directory Structure:**

```
out/[Year]/[Month]/[Day]/[User]/[JobID]/
├── job.json                     # Job metadata and parameters (created by prepare-job)
├── .env.pipeline                # Job-specific config copied from config/.env.pipeline
├── logs/                        # Shared logs directory
│   └── pipeline.log
├── 01_demux/
│   ├── manifest.json
│   ├── stage.log
│   └── audio.wav
├── 02_tmdb/
│   ├── manifest.json
│   ├── stage.log
│   └── metadata.json
├── 03_glossary_load/
│   ├── manifest.json
│   ├── stage.log
│   └── glossary_terms.json
├── 04_source_separation/
│   ├── manifest.json
│   ├── stage.log
│   └── vocals.wav
├── 05_pyannote_vad/
│   ├── manifest.json
│   ├── stage.log
│   └── segments.json
├── 06_whisperx_asr/
│   ├── manifest.json
│   ├── stage.log
│   └── transcript.json
├── 07_alignment/
│   ├── manifest.json
│   ├── stage.log
│   └── segments_aligned.json
├── 08_lyrics_detection/         # Subtitle workflow only (MANDATORY)
│   ├── manifest.json
│   ├── stage.log
│   └── transcript_with_lyrics.json
├── 09_hallucination_removal/    # Subtitle workflow only (MANDATORY)
│   ├── manifest.json
│   ├── stage.log
│   └── transcript_cleaned.json
├── 10_translation/
│   ├── manifest.json
│   ├── stage.log
│   ├── transcript_en.json
│   └── transcript_gu.json
├── 11_subtitle_generation/
│   ├── manifest.json
│   ├── stage.log
│   └── subtitles/
│       ├── movie.hi.srt
│       └── movie.en.srt
└── 12_mux/
    ├── manifest.json
    ├── stage.log
    └── movie_subtitled.mkv
```

**Job Preparation Flow:**

The `prepare-job` script creates job-specific configuration through the following steps:

1. **Read System Defaults:** Load `config/.env.pipeline` as the base configuration
2. **Copy to Job Directory:** Copy `.env.pipeline` to job directory as job-specific config
3. **Apply CLI Overrides:** Update job config parameters from command-line arguments
4. **Create Job Metadata:** Generate `job.json` with job ID, workflow, languages, etc.

```bash
# Example: prepare-job command
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language hi --target-language en

# Result:
# 1. Reads: config/.env.pipeline (system defaults)
# 2. Creates: out/.../job-YYYYMMDD-user-0001/
# 3. Copies: config/.env.pipeline → job/.env.pipeline
# 4. Updates: job/.env.pipeline with CLI parameters
# 5. Creates: job/job.json with metadata
```

**Configuration Hierarchy:**

1. **System Defaults:** `config/.env.pipeline` (created by bootstrap)
   - Default values for all parameters
   - Version-controlled template
   - Shared baseline for all jobs
   - **Never modified during job execution**

2. **Job-Specific Config:** `{job_dir}/.env.pipeline` (created by prepare-job)
   - Copied from system defaults
   - Updated with CLI parameters
   - Job-specific overrides
   - Not version-controlled
   - **Used by all stages during execution**

3. **Job Metadata:** `{job_dir}/job.json` (created by prepare-job)
   - Job ID, workflow type, timestamps
   - Source/target languages
   - Media processing parameters
   - Environment mappings
   - Not loaded by stages (metadata only)

**Stage Configuration Access:**

**All stages MUST:**
- ✅ Load configuration using `load_config()`
- ✅ Automatically reads from `{job_dir}/.env.pipeline`
- ✅ Fall back to system defaults if job config not found
- ✅ Never use `os.getenv()` directly
- ✅ Never modify configuration files

**Example:**

```python
from pathlib import Path
from shared.config_loader import load_config

def run_stage(job_dir: Path, stage_name: str) -> int:
    """Stage implementation following job-based architecture"""
    # Load config - automatically reads from job_dir/.env.pipeline
    config = load_config(job_dir)
    
    # Get parameters (from job-specific config)
    enabled = config.get("SOURCE_SEPARATION_ENABLED", "true").lower() == "true"
    model = config.get("WHISPERX_MODEL", "large-v2")
    
    if not enabled:
        logger.info("Stage disabled in configuration")
        return 0
    
    # Stage logic using configuration
    result = process_with_config(config)
    return 0 if result else 1
```

**Configuration Flow Diagram:**

```
bootstrap.sh
    ↓
config/.env.pipeline (system defaults, version-controlled)
    ↓
prepare-job.sh --media file.mp4 --source-language hi
    ↓
1. Copy: config/.env.pipeline → job/.env.pipeline
2. Update job/.env.pipeline with CLI params
3. Create job/job.json with metadata
    ↓
run-pipeline.sh --job-id job-YYYYMMDD-user-0001
    ↓
Stage scripts call load_config(job_dir)
    ↓
Reads: job/.env.pipeline (job-specific config)
```

**Testing Workflow:**

The `test-glossary-quickstart` script demonstrates the complete workflow:

```bash
# 1. Prepare test job
./prepare-job.sh --input-file "test.mp4" --workflow transcribe

# 2. Run baseline test
./run-pipeline.sh --job-id <baseline-job> --test-mode baseline

# 3. Run glossary-enhanced test
./run-pipeline.sh --job-id <glossary-job> --test-mode glossary

# 4. Run cached test
./run-pipeline.sh --job-id <cached-job> --test-mode cached

# 5. Compare results and generate report
python3 tools/compare-results.py baseline glossary cached
```
```

**Example: Cross-Platform Script Calling**

```python
# ✅ GOOD - Detects platform
import sys
import subprocess

if sys.platform == "win32":
    # Use PowerShell scripts on Windows
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", 
                   "-File", "prepare-job.ps1", "-InputFile", "file.mp4"])
else:
    # Use bash scripts on Unix/Linux/macOS
    subprocess.run(["./prepare-job.sh", "--input-file", "file.mp4"])

# ❌ BAD - Unix-only
subprocess.run(["./prepare-job.sh", "arg1"])
```

**Validation Checklist:**

- [x] All `.sh` scripts have `.ps1` PowerShell equivalents
- [ ] All scripts tested on target platforms (testing pending)
- [x] Path handling is cross-platform (pathlib)
- [x] Environment variables work on all platforms
- [x] Documentation includes platform-specific notes
- [ ] CI/CD tests on Windows, macOS, Linux (pending)

**Current Status:**

| Script | Bash (.sh) | PowerShell (.ps1) | Status |
|--------|------------|-------------------|--------|
| bootstrap | ✅ | ✅ | **COMPLETE** |
| prepare-job | ✅ | ✅ | **COMPLETE** |
| run-pipeline | ✅ | ✅ | **COMPLETE** |
| test-glossary-quickstart | ✅ | ✅ | **COMPLETE** |

**Note:** PowerShell (.ps1) is the recommended Windows format. Batch files (.bat) are deprecated due to limited functionality.

**Priority: ✅ COMPLETE - All core scripts have Windows equivalents**

---

### 1.3 File Naming Conventions

**Python Files:**
```python
# Modules: snake_case
stage_utils.py
environment_manager.py
stage_manifest.py

# Stage scripts: MUST use {stage_number}_{stage_name}.py format
# Pattern: scripts/{NN}_{name}.py where NN is 01-99
01_demux.py           # Stage 1: Demux
02_tmdb_enrichment.py # Stage 2: TMDB enrichment
03_glossary_loader.py # Stage 3: Glossary loading
04_source_separation.py
05_pyannote_vad.py
06_whisperx_asr.py
07_mlx_alignment.py
08_lyrics_detection.py
09_subtitle_gen.py
10_mux.py

# Utility/helper scripts (non-stages): {name}.py
config_loader.py
device_selector.py
filename_parser.py

# Test files: test_{module}.py
test_stage_utils.py
test_config.py
test_manifest.py
```

**Stage Script Naming Rules:**
1. ✅ **DO:** Use format `{NN}_{stage_name}.py` (e.g., `01_demux.py`)
2. ✅ **DO:** Match stage directory name (e.g., `01_demux/` → `01_demux.py`)
3. ❌ **DON'T:** Use inconsistent names (e.g., `demux.py`, `tmdb_enrichment_stage.py`)
4. ❌ **DON'T:** Put stage scripts in subdirectories (e.g., `03_glossary_load/glossary_loader.py`)
5. ✅ **DO:** Place all stage scripts directly in `scripts/` directory

**Log Files:**
```
# Main pipeline log (in logs/)
99_pipeline_<timestamp>.log

# Stage logs (in each stage directory)
stage.log

# Stage manifests (in each stage directory)
manifest.json
```

**Shell Scripts:**
```bash
# Scripts: kebab-case with platform extensions
# Unix/Linux/macOS
bootstrap.sh
prepare-job.sh
run-pipeline.sh
test-glossary-quickstart.sh

# Windows PowerShell (required)
bootstrap.ps1
prepare-job.ps1
run-pipeline.ps1
test-glossary-quickstart.ps1

# Note: Batch files (.bat) are deprecated due to limited functionality
```

**Configuration:**
```bash
# Environment files: .env.{name}
.env.pipeline
.env.local

# JSON configs: lowercase with underscores
secrets.json
hardware_cache.json
```

---

## 1.4 Testing Infrastructure & Standard Test Media

**Purpose:** Establish reproducible testing baseline with diverse use cases for all three core workflows.

### Standard Test Media Samples

**Critical Requirement:** All testing MUST use these standardized samples for consistency and reproducibility.

#### Sample 1: English Technical Content
**File:** `in/Energy Demand in AI.mp4`  
**Size:** ~14 MB  
**Duration:** 2-5 minutes (estimated)  
**Language:** English  
**Content Type:** Technical/Educational  
**Primary Workflows:** Transcribe, Translate

**Characteristics:**
- Clear English audio with minimal background noise
- Technical terminology (AI, energy, demand)
- Ideal for testing ASR accuracy on technical content
- Good baseline for English-to-Indic translation
- Low complexity audio (single speaker, good quality)

**Quality Targets:**
- ASR Word Error Rate (WER): ≤5%
- Translation BLEU Score: ≥90%
- Processing Time: <2 minutes (first run)
- Processing Time: <30 seconds (cached)

**Test Use Cases:**
1. **Transcribe Workflow**: English → English transcript
   - Tests: ASR accuracy, technical term handling, timestamp precision
   
2. **Translate Workflow**: English → Hindi/Gujarati/Spanish
   - Tests: Cross-language translation, technical term preservation

#### Sample 2: Hinglish Bollywood Content
**File:** `in/test_clips/jaane_tu_test_clip.mp4`  
**Size:** ~28 MB  
**Duration:** 1-3 minutes (estimated)  
**Language:** Hindi/Hinglish (code-mixed)  
**Content Type:** Entertainment/Dialogue  
**Primary Workflows:** Subtitle, Transcribe, Translate

**Characteristics:**
- Mixed Hindi-English (Hinglish) typical of Bollywood
- Multiple speakers with emotional/casual speech
- Background music possible
- Real-world challenge for context-aware subtitle generation
- Tests code-mixing, cultural terms, speaker diarization

**Quality Targets:**
- ASR Word Error Rate (WER): ≤15% (Hinglish)
- Subtitle Quality Score: ≥88%
- Context Awareness: ≥80%
- Glossary Application Rate: 100%
- Subtitle Timing Accuracy: ±200ms

**Test Use Cases:**
1. **Subtitle Workflow**: Hindi/Hinglish → Multiple subtitle tracks
   - Output: Hindi, English, Gujarati, Tamil, Spanish, Russian, Chinese, Arabic
   - Tests: Full pipeline, glossary application, context awareness, soft-embedding
   
2. **Transcribe Workflow**: Hindi → Hindi transcript
   - Tests: Indic language ASR, code-mixing handling, Devanagari output
   
3. **Translate Workflow**: Hindi → English/Spanish/Chinese/Arabic
   - Tests: Cultural adaptation, idiom handling, formality preservation

### Test Media Index

**Location:** `in/test_media_index.json`

```json
{
  "version": "1.0",
  "last_updated": "2025-12-03",
  "test_samples": [
    {
      "id": "sample_01",
      "file": "Energy Demand in AI.mp4",
      "language": "en",
      "type": "technical",
      "duration_estimate": "2-5 min",
      "workflows": ["transcribe", "translate"],
      "quality_baseline": {
        "asr_wer": 0.05,
        "asr_confidence": 0.95,
        "translation_bleu": 0.90,
        "processing_time_first": 120,
        "processing_time_cached": 30
      },
      "test_commands": {
        "transcribe": "./prepare-job.sh --media 'in/Energy Demand in AI.mp4' --workflow transcribe --source-language en",
        "translate_hi": "./prepare-job.sh --media 'in/Energy Demand in AI.mp4' --workflow translate --source-language en --target-language hi"
      }
    },
    {
      "id": "sample_02",
      "file": "test_clips/jaane_tu_test_clip.mp4",
      "language": "hi-Hinglish",
      "type": "entertainment",
      "duration_estimate": "1-3 min",
      "workflows": ["subtitle", "transcribe", "translate"],
      "quality_baseline": {
        "asr_wer": 0.15,
        "asr_confidence": 0.85,
        "subtitle_quality": 0.88,
        "context_awareness": 0.80,
        "glossary_application": 1.00,
        "timing_accuracy_ms": 200
      },
      "test_commands": {
        "subtitle": "./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 --workflow subtitle --source-language hi --target-languages en,gu,ta,es,ru,zh,ar",
        "transcribe": "./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 --workflow transcribe --source-language hi",
        "translate_en": "./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 --workflow translate --source-language hi --target-language en"
      }
    }
  ]
}
```

### Testing Requirements

**All new features MUST:**
1. ✅ Pass tests on both standard samples
2. ✅ Meet or exceed quality baselines
3. ✅ Document any baseline deviations
4. ✅ Update test_media_index.json if quality improves

**Test Categories:**
- **Unit Tests**: Individual stage testing (target: 85% coverage)
- **Integration Tests**: Full workflow testing with standard media (target: 75% coverage)
- **Quality Baseline Tests**: Automated validation against targets
- **Caching Tests**: Cache hit/miss scenarios
- **Performance Tests**: Processing time benchmarks

**See:** [Testing Infrastructure](../ARCHITECTURE_IMPLEMENTATION_ROADMAP.md#testing-infrastructure) for complete testing framework.

---

## 1.5 Core Workflows

### Overview

CP-WhisperX supports three primary workflows, each optimized for specific use cases with context-aware processing and intelligent caching.

### Workflow 1: Subtitle (Context-Aware, Highest Accuracy)

**Purpose:** Generate multilingual subtitles for Bollywood/Indic media with soft-embedding.

**Input:** Indic/Hinglish movie media source  
**Output:** Original media + soft-embedded subtitle tracks in organized subdirectory

**Pipeline Stages:**
```
01_demux → 02_tmdb → 03_glossary_load → 04_source_sep (optional) →
05_pyannote_vad → 06_whisperx_asr → 07_alignment → 08_translate →
07_alignment → 08_lyrics_detection → 09_hallucination_removal → 10_translation → 11_subtitle_generation → 12_mux
```

**Context-Aware Features:**
1. **Character Names**: Preserved via glossary (Jai, Aditi, Meow, etc.)
2. **Cultural Terms**: Hindi idioms, relationship terms (beta, bhai, ji)
3. **Tone Adaptation**: Formal vs. casual based on context
4. **Temporal Coherence**: Consistent terminology across subtitle blocks
5. **Speaker Attribution**: Diarization for multi-speaker scenes

**Output Structure:**
```
out/{date}/{user}/{job}/12_mux/
├── {media_name}_subtitled.mkv        # Original video + all embedded subtitle tracks
└── manifest.json                     # Processing metadata

# Individual subtitle files are in stage 11:
out/{date}/{user}/{job}/11_subtitle_generation/subtitles/
├── {media_name}.hi.srt              # Hindi (native)
├── {media_name}.en.srt              # English
├── {media_name}.gu.srt              # Gujarati
├── {media_name}.ta.srt              # Tamil
├── {media_name}.es.srt              # Spanish
├── {media_name}.ru.srt              # Russian
├── {media_name}.zh.srt              # Chinese
└── {media_name}.ar.srt              # Arabic
```

**Usage Example:**
```bash
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es,ru,zh,ar

./run-pipeline.sh --job-dir out/{date}/{user}/{job_id}
```

**Quality Targets:**
- ASR Accuracy: ≥85% for Hinglish
- Subtitle Timing: ±200ms
- Translation Fluency: ≥88%
- Context Consistency: ≥80%
- Glossary Application: 100%

### Workflow 2: Transcribe (Context-Aware, Highest Accuracy)

**Purpose:** Create text transcript in SAME language as source audio.

**Input:** Any media source (English, Hindi, Indic, non-English)  
**Output:** Text transcript in source language

**Pipeline Stages:**
```
01_demux → 02_tmdb (optional) → 03_glossary_load → 04_source_sep (optional) →
05_pyannote_vad → 06_whisperx_asr → 07_alignment
```

**Language Handling:**
- English media → English transcript
- Hindi media → Hindi transcript (Devanagari script)
- Indic media → Same Indic language (native script)
- Spanish/Chinese/Arabic → Same language (native script)

**Context-Aware Features:**
1. **Domain Terminology**: Technical, medical, legal terms preserved
2. **Proper Nouns**: Names, places, organizations
3. **Language-Specific**: Native script output (Devanagari for Hindi)
4. **Punctuation**: Context-aware sentence segmentation
5. **Capitalization**: Proper noun detection (English)

**Output Structure:**
```
out/{date}/{user}/{job}/07_alignment/
├── transcript.txt                 # Plain text transcript
├── transcript.json                # With word-level timestamps
└── manifest.json                  # Processing metadata
```

**Usage Examples:**
```bash
# English technical content
./prepare-job.sh \
  --media "in/Energy Demand in AI.mp4" \
  --workflow transcribe \
  --source-language en

# Hindi content
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow transcribe \
  --source-language hi
```

**Quality Targets:**
- English Technical: ≥95% WER
- Hindi/Indic: ≥85% WER
- Other Languages: ≥90% WER
- Proper Noun Accuracy: ≥90%
- Timestamp Precision: ±100ms

### Workflow 3: Translate (Context-Aware, Highest Accuracy)

**Purpose:** Create text transcript in SPECIFIED target language.

**Input:** Any media source  
**Output:** Text transcript in target language

**Pipeline Stages:**
```
01_demux → 02_tmdb → 03_glossary_load → 04_source_sep (optional) →
05_pyannote_vad → 06_whisperx_asr → 07_alignment → 08_translate
```

**Translation Routing:**
- **Indic → Indic**: IndicTrans2 (AI4Bharat) - Highest quality for Indian languages
- **Indic → English**: IndicTrans2 optimized model
- **Any → Non-Indic**: NLLB-200 (Meta) - Broad language support
- **Fallback**: Hybrid approach if primary model fails

**Context-Aware Features:**
1. **Cultural Adaptation**: Idioms, metaphors localized
2. **Formality Levels**: Maintained across languages
3. **Named Entities**: Transliterated appropriately
4. **Glossary Terms**: Bilingual term preservation
5. **Temporal Consistency**: Same term translated consistently
6. **Numeric/Date Formats**: Localized per target culture

**Output Structure:**
```
out/{date}/{user}/{job}/08_translate/
├── transcript_{target_lang}.txt   # Translated transcript
├── transcript_{target_lang}.json  # With timestamps
├── translation_metadata.json      # Quality metrics
└── manifest.json                  # Processing metadata
```

**Usage Examples:**
```bash
# Hindi → English
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language en

# Hindi → Spanish (non-Indic)
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language es

# Hindi → Gujarati (Indic-to-Indic)
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language gu
```

**Quality Targets:**
- Hindi → English: ≥90% BLEU score
- Indic-to-Indic: ≥88% BLEU score
- Hindi → Non-Indic: ≥85% BLEU score
- Glossary Application: 100%
- Cultural Adaptation: ≥80% appropriateness

---

## 1.6 Caching & ML Optimization Strategy

**Purpose:** Enable subsequent workflows with similar media to perform optimally through intelligent caching and machine learning.

### Caching Layers

#### 1. Model Cache (Shared Across Jobs)
```
~/.cp-whisperx/cache/models/
├── whisperx/large-v2/              # ASR model weights
├── indictrans2/hi-en/              # Translation models
└── pyannote/speaker-diarization/   # Diarization models
```
**Benefit:** Avoid re-downloading models (saves 1-5 GB per run)

#### 2. Audio Fingerprint Cache
```
~/.cp-whisperx/cache/fingerprints/
├── {audio_hash}.json               # Audio characteristics
└── index.db                        # Fast lookup
```
**Benefit:** Skip demux/analysis for identical media

#### 3. ASR Results Cache
```
~/.cp-whisperx/cache/asr/
├── {audio_hash}_{model}_{lang}.json
└── index.db
```
**Cache Key:** `SHA256(audio_content + model_version + language + config_params)`
**Benefit:** Reuse ASR results (saves 2-10 minutes)

#### 4. Translation Cache (Context-Aware)
```
~/.cp-whisperx/cache/translations/
├── {source_hash}_{src_lang}_{tgt_lang}_{glossary_hash}.json
└── index.db
```
**Context Matching:**
- Exact segment match: 100% reuse
- Similar segment (>80%): Reuse with adjustment
- Different context: Fresh translation

**Benefit:** Reuse translations (saves 1-5 minutes)

#### 5. Glossary Learning Cache
```
~/.cp-whisperx/cache/glossary_learned/
├── {movie_id}/                     # Per-movie learned terms
│   ├── character_names.json
│   ├── cultural_terms.json
│   └── frequency_analysis.json
└── global/                         # Cross-movie patterns
    ├── common_names.json
    └── bollywood_terms.json
```
**Benefit:** Improve accuracy on repeated processing

### ML-Based Optimization

#### Adaptive Quality Prediction
**ML Model:** Lightweight XGBoost classifier

**Features:**
- Audio quality metrics (SNR, clarity)
- Language detected
- Speech rate
- Background noise level
- Historical processing results

**Predictions:**
- Optimal Whisper model size (base/small/medium/large)
- Source separation needed? (yes/no)
- Expected ASR confidence
- Processing time estimate

**Benefits:**
- 30% faster processing on clean audio (use smaller model)
- Better quality on noisy audio (enable source separation)
- Accurate time estimates

#### Context Learning from History
**Learning Mechanisms:**

1. **Character Name Recognition**: After processing "Jaane Tu Ya Jaane Na" once, learn character names (Jai, Aditi, Meow) with frequency and context
2. **Cultural Term Patterns**: Learn common Bollywood/Hindi patterns (beta, bhai, ji)
3. **Translation Memory**: Build memory from approved translations

#### Similarity-Based Optimization
**Similarity Metrics:**
- Audio fingerprint matching (chromaprint)
- Content-based similarity (same movie, different versions)
- Language/accent similarity
- Genre similarity

**Optimization Actions:**
```
Similarity > 95%: Reuse full pipeline config + glossary
Similarity > 80%: Reuse glossary + model selection, fresh ASR
Similarity > 60%: Reuse language settings + suggest glossaries
```

### Cache Configuration

**In config/.env.pipeline:**
```bash
# Caching Configuration
ENABLE_CACHING=true
CACHE_DIR=~/.cp-whisperx/cache
CACHE_MAX_SIZE_GB=50
CACHE_ASR_RESULTS=true
CACHE_TRANSLATIONS=true
CACHE_AUDIO_FINGERPRINTS=true
CACHE_TTL_DAYS=90
CACHE_CLEANUP_ON_START=false

# ML Optimization
ENABLE_ML_OPTIMIZATION=true
ML_MODEL_SELECTION=adaptive
ML_QUALITY_PREDICTION=true
ML_LEARNING_FROM_HISTORY=true

# Performance Tuning
SIMILAR_CONTENT_THRESHOLD=0.80
GLOSSARY_LEARNING_ENABLED=true
TRANSLATION_MEMORY_ENABLED=true
```

### Cache Management

**Commands:**
```bash
# View cache statistics
./tools/cache-manager.sh --stats

# Clear specific cache type
./tools/cache-manager.sh --clear asr
./tools/cache-manager.sh --clear translations

# Clear old cache (>90 days)
./tools/cache-manager.sh --cleanup

# Clear all cache
./tools/cache-manager.sh --clear all

# Disable caching for one job
./prepare-job.sh --media in/file.mp4 --no-cache
```

### Expected Performance Improvements

| Scenario | First Run | Subsequent Run | Improvement |
|----------|-----------|----------------|-------------|
| Identical media | 10 min | 30 sec | 95% faster |
| Same movie, different cut | 10 min | 6 min | 40% faster |
| Similar Bollywood movie | 10 min | 8 min | 20% faster |
| Similar language/genre | 10 min | 9 min | 10% faster |

**Cache Hit Rates (Target):**
- Audio fingerprint: 80% on re-processing
- ASR results: 70% on same media
- Translations: 60% on similar content
- Glossary terms: 90% on same movie/series

---



### 2.1 Overview

The pipeline implements a **dual logging architecture** with comprehensive manifest tracking to provide complete data lineage and audit trails.

**Three-Tier Logging System:**
1. **Main Pipeline Log** - High-level orchestration in `logs/99_pipeline_<timestamp>.log`
2. **Stage-Specific Logs** - Detailed execution in each `<stage_dir>/stage.log`
3. **Stage Manifests** - Structured I/O tracking in each `<stage_dir>/manifest.json`

### 2.2 Logging Directory Structure

```
out/<job-id>/
├── logs/
│   └── 99_pipeline_20251127_140915.log    # Main orchestration log
│
├── 01_demux/
│   ├── stage.log                           # Stage-specific detailed log
│   ├── manifest.json                       # I/O tracking manifest
│   ├── audio.wav                           # Output file
│   └── metadata.json                       # Stage metadata
│
├── 02_tmdb/
│   ├── stage.log
│   ├── manifest.json
│   ├── enrichment.json
│   └── metadata.json
│
├── 03_glossary_load/
│   ├── stage.log
│   ├── manifest.json
│   ├── glossary_snapshot.json
│   └── metadata.json
│
└── [other stages...]
```

### 2.3 Main Pipeline Log

**Location:** `out/<job-id>/logs/99_pipeline_<timestamp>.log`

**Purpose:** High-level orchestration, stage transitions, overall progress

**Content:**
- Workflow execution flow
- Stage start/completion status
- Overall timing and resource usage
- Critical errors and warnings
- Summary statistics

**Log Levels:**
- `INFO` - Stage transitions, progress updates
- `WARNING` - Non-fatal issues  
- `ERROR` - Stage failures, critical issues

**Example:**
```log
[2025-11-27 14:09:15] [pipeline] [INFO] ================================================================================
[2025-11-27 14:09:15] [pipeline] [INFO] PIPELINE LOGGING ARCHITECTURE
[2025-11-27 14:09:15] [pipeline] [INFO] ================================================================================
[2025-11-27 14:09:15] [pipeline] [INFO] 📋 Main pipeline log: logs/99_pipeline_20251127_140915.log
[2025-11-27 14:09:15] [pipeline] [INFO] 📋 Stage logs: Each stage writes to its own subdirectory
[2025-11-27 14:09:15] [pipeline] [INFO] 📋 Stage manifests: Track inputs/outputs/intermediate files
[2025-11-27 14:09:16] [pipeline] [INFO] ▶️  Stage demux: STARTING
[2025-11-27 14:09:20] [pipeline] [INFO] ✅ Stage demux: COMPLETED (4.2s)
```

### 2.4 Stage Logs

**Location:** `out/<job-id>/<stage_dir>/stage.log`

**Purpose:** Detailed stage execution, debugging information, tool output

**Content:**
- Detailed processing steps
- Tool command output (ffmpeg, whisperx, etc.)
- Configuration parameters
- Resource usage details
- Debug information
- File paths and sizes

**Log Levels:**
- `DEBUG` - All detailed steps (only in stage log, not pipeline log)
- `INFO` - Progress within stage
- `WARNING` - Stage-specific warnings
- `ERROR` - Stage-specific errors

**Example:**
```log
[2025-11-27 14:09:16] [demux] [INFO] Input media: /Users/user/in/sample.mp4
[2025-11-27 14:09:16] [demux] [INFO] Output directory: out/job_001/01_demux
[2025-11-27 14:09:16] [demux] [DEBUG] FFmpeg command: ffmpeg -y -loglevel error -i ...
[2025-11-27 14:09:20] [demux] [INFO] Successfully extracted audio: 45.3 MB
[2025-11-27 14:09:20] [demux] [INFO] Stage log: 01_demux/stage.log
[2025-11-27 14:09:20] [demux] [INFO] Stage manifest: 01_demux/manifest.json
```

### 2.5 Stage Manifests

**Location:** `out/<job-id>/<stage_dir>/manifest.json`

**Purpose:** Structured tracking of stage inputs, outputs, intermediate files, configuration, and resource usage

**Schema:**
```json
{
  "stage": "demux",
  "stage_number": 1,
  "timestamp": "2025-11-27T14:09:16.123456",
  "status": "success",
  "duration_seconds": 4.2,
  "completed_at": "2025-11-27T14:09:20.345678",
  
  "inputs": [
    {
      "type": "video",
      "path": "/Users/user/in/sample.mp4",
      "size_bytes": 52428800,
      "format": "mp4",
      "description": "Input video file"
    }
  ],
  
  "outputs": [
    {
      "type": "audio",
      "path": "out/job_001/01_demux/audio.wav",
      "size_bytes": 47493120,
      "format": "wav",
      "sample_rate": 16000,
      "channels": 1,
      "description": "Extracted audio track"
    }
  ],
  
  "intermediate_files": [
    {
      "path": "out/job_001/01_demux/temp_segment.wav",
      "size_bytes": 1048576,
      "retained": false,
      "reason": "Temporary processing file",
      "description": "Intermediate audio segment"
    }
  ],
  
  "config": {
    "processing_mode": "full",
    "start_time": "",
    "end_time": "",
    "sample_rate": "16000",
    "channels": "1"
  },
  
  "resources": {
    "memory_peak_mb": 256,
    "cpu_time_seconds": 3.8,
    "gpu_utilized": false
  },
  
  "errors": [],
  "warnings": []
}
```

### 2.6 StageIO Pattern Implementation

**All stages MUST use the StageIO pattern for consistent logging and manifest tracking:**

```python
from shared.stage_utils import StageIO

def main():
    stage_io = None
    logger = None
    
    try:
        # Initialize StageIO with manifest tracking
        stage_io = StageIO("stage_name", enable_manifest=True)
        logger = stage_io.get_stage_logger("INFO")
        
        logger.info("Stage starting...")
        
        # Track inputs
        stage_io.track_input(input_file, "audio", format="wav")
        
        # Set configuration (for manifest)
        stage_io.set_config({
            "model": "whisper-large-v3",
            "language": "hi",
            "batch_size": 8
        })
        
        # Process...
        result = process_stage(input_file)
        
        # Track outputs
        stage_io.track_output(output_file, "transcript", 
                            format="json",
                            segments=len(result))
        
        # Track intermediate files if needed
        if cache_file.exists():
            stage_io.track_intermediate(cache_file,
                                       retained=True,
                                       reason="Model weights cache")
        
        # Finalize with success
        stage_io.finalize(status="success",
                         segments_processed=len(result),
                         duration_seconds=3.5)
        
        logger.info("Stage complete!")
        return 0
        
    except FileNotFoundError as e:
        if logger:
            logger.error(f"File not found: {e}", exc_info=True)
        if stage_io:
            stage_io.add_error(f"File not found: {e}")
            stage_io.finalize(status="failed", error=str(e))
        return 1
        
    except Exception as e:
        if logger:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        if stage_io:
            stage_io.add_error(f"Unexpected error: {e}")
            stage_io.finalize(status="failed", error=str(e))
        return 1
```

### 2.7 Log Level Configuration

**Log levels can be configured via:**

1. **Command line:** `--log-level DEBUG|INFO|WARN|ERROR|CRITICAL`
2. **Environment variable:** `export LOG_LEVEL=DEBUG`
3. **Config file:** Set in `config/.env.pipeline`

**Log level propagates to:**
- Main pipeline log
- All stage logs
- Downstream scripts (prepare-job.sh, run-pipeline.sh)

**Usage examples:**
```bash
# Run with DEBUG logging (most verbose)
./run-pipeline.sh -j job_001 --log-level DEBUG

# Run with INFO logging (default, balanced)
./run-pipeline.sh -j job_001 --log-level INFO

# Run with ERROR logging (minimal, errors only)
./run-pipeline.sh -j job_001 --log-level ERROR
```

### 2.8 Data Lineage Tracking

**Complete pipeline data flow tracked via manifests:**

```
Input Video (in/film.mp4)
    ↓
[01_demux] → audio.wav
    ↓
[02_tmdb] → enrichment.json
    ↓
[03_glossary_load] → glossary_snapshot.json
    ↓
[04_source_separation] → vocals.wav
    ↓
[05_pyannote_vad] → vad_segments.json
    ↓
[06_asr] → segments.json
    ↓
[07_alignment] → aligned_segments.json
    ↓
[08_lyrics_detection] → transcript_with_lyrics.json
    ↓
[09_hallucination_removal] → transcript_cleaned.json
    ↓
[10_translation] → transcript_{lang}.json
    ↓
[11_subtitle_generation] → subtitles/{media}.{lang}.srt
    ↓
[12_mux] → {media}_subtitled.mkv
```

**Each manifest records:**
- Input files from previous stages
- Output files for next stages
- Intermediate files (with retention policy)
- Configuration used
- Resource usage
- Errors and warnings

**Benefits:**
1. **Complete audit trail** - Track every file through the pipeline
2. **Debugging** - Quickly identify where issues occurred
3. **Reproducibility** - Exact configuration and data flow recorded
4. **Compliance** - Audit-ready format for regulatory requirements
5. **Optimization** - Identify bottlenecks via resource tracking

### 2.9 Manifest Validation

**Validate manifests after pipeline runs:**

```bash
# Check all manifests exist
for stage in out/job_001/*/; do
    if [ ! -f "$stage/manifest.json" ]; then
        echo "❌ Missing: $stage/manifest.json"
    fi
done

# Validate JSON format
for manifest in out/job_001/*/manifest.json; do
    jq empty "$manifest" || echo "❌ Invalid JSON: $manifest"
done

# Check data lineage
python3 << 'EOF'
import json
from pathlib import Path

job_dir = Path("out/job_001")
manifests = sorted(job_dir.glob("*/manifest.json"))

print(f"Validating {len(manifests)} manifests...")
for manifest_file in manifests:
    with open(manifest_file) as f:
        manifest = json.load(f)
    
    stage = manifest['stage']
    status = manifest['status']
    inputs = len(manifest['inputs'])
    outputs = len(manifest['outputs'])
    
    icon = "✅" if status == "success" else "❌"
    print(f"{icon} {stage:20s} | {status:10s} | {inputs} inputs, {outputs} outputs")
EOF
```

### 2.10 Related Documentation

For complete details on the logging architecture, see:
- **[ENHANCED_LOGGING_IMPLEMENTATION.md](ENHANCED_LOGGING_IMPLEMENTATION.md)** - Complete implementation guide
- **[LOGGING_ARCHITECTURE.md](LOGGING_ARCHITECTURE.md)** - Detailed architecture
- **[LOGGING_QUICKREF.md](LOGGING_QUICKREF.md)** - Quick reference patterns

---

## 3. MULTI-ENVIRONMENT ARCHITECTURE

### 2.1 Virtual Environment Strategy

**Rule:** Each ML/Translation component MUST have its own isolated virtual environment to prevent dependency conflicts.

**Current Environments (8 total):**

```python
ENVIRONMENTS = {
    "common": "venv/common",          # Core: job mgmt, logging, muxing
    "whisperx": "venv/whisperx",      # WhisperX ASR (CUDA/CPU)
    "mlx": "venv/mlx",                # MLX Whisper (Apple Silicon)
    "pyannote": "venv/pyannote",      # PyAnnote VAD
    "demucs": "venv/demucs",          # Demucs source separation
    "indictrans2": "venv/indictrans2",# IndicTrans2 (22 Indic languages)
    "nllb": "venv/nllb",              # NLLB (200+ languages)
    "llm": "venv/llm",                # LLM integration
}
```

### 2.2 Environment Assignment

Stages are mapped to environments in `EnvironmentManager`:

```python
# In shared/environment_manager.py
STAGE_TO_ENV = {
    "demux": "common",
    "tmdb": "common",
    "glossary_load": "common",
    "source_separation": "demucs",
    "pyannote_vad": "pyannote",
    "asr": "whisperx",           # or "mlx" for Apple Silicon
    "alignment": "whisperx",
    "lyrics_detection": "demucs",
    "translation": "indictrans2",  # or "nllb" based on config
    "subtitle_generation": "common",
    "mux": "common",
}
```

### 2.3 Adding New Environments

**When adding a new ML component:**

1. **Add to bootstrap.sh:**
```bash
# In ENVIRONMENTS array
ENVIRONMENTS=(
    "common"
    "whisperx"
    # ... existing ...
    "your_new_env"    # ADD HERE
)
```

2. **Create requirements file:**
```bash
# requirements/requirements-your_new_env.txt
your-package>=1.0.0
dependency-package>=2.0.0
# Pin exact versions for production stability
```

3. **Add to EnvironmentManager:**
```python
# shared/environment_manager.py
ENVIRONMENTS = {
    # ... existing ...
    "your_new_env": "venv/your_new_env",
}

STAGE_TO_ENV = {
    # ... existing ...
    "your_stage": "your_new_env",
}
```

4. **Update bootstrap.sh environment descriptions:**
```bash
# Creates N specialized virtual environments for isolated dependency management:
#   ...
#   N. venv/your_new_env - Your component description
```

### 2.4 Dependency Security

**Audit dependencies regularly:**

```bash
# Check for known vulnerabilities
pip install pip-audit
pip-audit --requirement requirements/requirements-common.txt

# Check for outdated packages
pip list --outdated

# Update safely (test thoroughly)
pip install --upgrade package==version

# Pin exact versions for production
pip freeze > requirements-lock.txt
```

**Dependency update policy:**
- **Security patches**: Apply immediately
- **Minor updates**: Monthly review
- **Major updates**: Quarterly evaluation with testing

---

## 3. CONFIGURATION MANAGEMENT

### 3.1 Configuration Hierarchy

```
config/.env.pipeline        # Global defaults (REQUIRED, version controlled)
  ↓
job.json                    # Job-specific config (auto-generated)
  ↓
.job-YYYYMMDD-user-NNNN.env # Job environment overrides (optional)
  ↓
Environment variables       # Runtime overrides (highest priority)
```

### 3.2 Mandatory Rules

**✅ DO:**
- Store ALL parameters in `config/.env.pipeline`
- Use `Config` class from `shared/config.py`
- Provide sensible defaults for optional parameters
- Document parameter purpose and valid values
- Use environment variable format: `STAGE_PARAMETER_NAME`
- Validate configuration on load
- Remove unused parameters immediately
- Mark planned/future parameters with `⏳ NOT YET IMPLEMENTED`

**❌ DON'T:**
- Use `os.environ.get()` directly in stage scripts
- Hardcode values in Python/Shell scripts
- Create stage-specific config files
- Use different config formats (stick to env vars)
- Commit secrets to version control
- Leave unused parameters in config file
- Add parameters without implementation

### 3.2.1 Configuration Parameter Lifecycle

**Adding New Parameters:**

1. **Implement feature first**, then add config
2. Add parameter to `config/.env.pipeline` with documentation:
   ```bash
   # PARAMETER_NAME: Purpose and description
   #   Values: valid_value1 | valid_value2
   #   Default: default_value
   #   Impact: What this parameter affects
   PARAMETER_NAME=default_value
   ```
3. Add to `shared/config.py` if using Config class
4. Document in code where parameter is used
5. Test with different values

**Removing Parameters:**

1. **Search codebase** for usage: `grep -r "PARAM_NAME" --include="*.py" scripts/ shared/`
2. **Remove from config/.env.pipeline** if unused
3. **Update documentation** if parameter was documented elsewhere
4. **Test pipeline** to ensure no breakage

**Marking Future Parameters:**

For planned but unimplemented features, clearly mark status:
```bash
# FUTURE_PARAM: Description
#   Values: valid_values
#   Default: default_value
#   Status: ⏳ NOT YET IMPLEMENTED (Planned for Phase N)
#   Impact: Expected impact when implemented
FUTURE_PARAM=false
```

**Parameter Naming Convention:**

```bash
# Format: STAGE_COMPONENT_PROPERTY
WHISPER_MODEL=large-v3          # ✅ Clear, hierarchical
WHISPERX_DEVICE=mps             # ✅ Good
MODEL=large                     # ❌ Too generic
WHISPER_LG_V3=true              # ❌ Abbreviations unclear
```

### 3.3 Configuration Access Pattern

```python
# CORRECT: Use Config class
from shared.config import load_config

config = load_config()  # Loads from job.json if available
model = config.whisper_model  # Attribute access
threshold = getattr(config, 'confidence_threshold', 0.7)  # With default

# INCORRECT: Direct environment access
model = os.environ.get('WHISPER_MODEL')  # ❌ Don't do this
```

### 3.4 Configuration Validation

**Add validation layer using Pydantic:**

```python
from pydantic import BaseModel, Field, validator
from typing import Literal

class PipelineConfig(BaseModel):
    """Validated pipeline configuration with automatic type checking"""
    
    # Whisper Configuration
    whisper_model: Literal["tiny", "base", "small", "medium", "large", "large-v3"] = "large-v3"
    batch_size: int = Field(8, gt=0, le=128, description="Processing batch size")
    device: Literal["cpu", "cuda", "mps"] = Field("mps", description="Compute device")
    
    # Performance Configuration
    num_workers: int = Field(4, gt=0, le=32)
    max_memory_mb: int = Field(8192, gt=512)
    
    # Feature Flags
    glossary_enabled: bool = True
    source_separation_enabled: bool = False
    
    @validator('whisper_model')
    def validate_model_availability(cls, v):
        """Check if model exists or is downloadable"""
        # Add validation logic
        return v
    
    @validator('device')
    def validate_device_availability(cls, v):
        """Check if device is available on system"""
        import torch
        if v == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but not available")
        if v == "mps" and not torch.backends.mps.is_available():
            raise ValueError("MPS requested but not available")
        return v
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True

# Usage
try:
    config = PipelineConfig(**config_dict)
except ValidationError as e:
    logger.error(f"Configuration validation failed: {e}")
    sys.exit(2)
```

### 3.5 Configuration Documentation

**Every parameter in config/.env.pipeline MUST have:**

```bash
# PARAMETER_NAME: Purpose/description
#   Values: Valid values or range
#   Default: Default value
#   Note: Additional context, constraints, or recommendations
PARAMETER_NAME=value

# Example with full documentation:
# WHISPER_TEMPERATURE: Sampling temperature for inference
#   Values: Comma-separated floats (e.g., "0.0,0.2,0.4")
#   Default: 0.0,0.1,0.2
#   Note: 0.0 = deterministic, higher = more creative but less accurate
WHISPER_TEMPERATURE=0.0,0.1,0.2
```

---

## 4. STAGE PATTERN (StageIO)

### 4.1 Stage Implementation Template (with Logging Architecture)

**Every stage script MUST follow this pattern:**

```python
#!/usr/bin/env python3
"""
Stage Name: Brief description

Purpose: Detailed purpose of this stage
Input: Expected input files and their sources
Output: Generated output files and their formats
Intermediate Files: Cache/temp files created and their retention policy
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO
from shared.config import load_config


def main():
    """Main entry point for stage"""
    
    # 1. Initialize StageIO with manifest tracking
    stage_io = StageIO("stage_name", job_dir, enable_manifest=True)
    
    # 2. Setup dual logging (stage log + pipeline log)
    logger = stage_io.get_stage_logger("DEBUG" if debug else "INFO")
    
    logger.info("=" * 60)
    logger.info("STAGE NAME: Description")
    logger.info("=" * 60)
    
    # 3. Load configuration
    config = load_config()
    
    # 4. Get input files and track in manifest
    input_file = stage_io.get_input_path("filename.ext", from_stage="previous_stage")
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        stage_io.add_error(f"Input file not found: {input_file}")
        stage_io.finalize(status="failed")
        return 1
    
    # Track input in manifest
    stage_io.track_input(input_file, "file_type", format="ext")
    
    # 5. Get output path
    output_file = stage_io.get_output_path("output.ext")
    
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    
    # 6. Track configuration in manifest
    stage_io.set_config({
        "parameter1": config.param1,
        "parameter2": config.param2
    })
    
    # 7. Execute stage logic with manifest tracking
    try:
        result = process_stage(input_file, output_file, config, logger, stage_io)
        
        if result:
            # Track output in manifest
            stage_io.track_output(output_file, "file_type", 
                                 format="ext",
                                 items_count=len(result))
            
            # Finalize with success
            stage_io.finalize(status="success", 
                             items_processed=len(result))
            
            logger.info("✓ Stage completed successfully")
            logger.info(f"Stage log: {stage_io.stage_log.relative_to(job_dir)}")
            logger.info(f"Stage manifest: {stage_io.manifest_path.relative_to(job_dir)}")
            return 0
        else:
            stage_io.add_error("Processing failed")
            stage_io.finalize(status="failed")
            logger.error("✗ Stage failed")
            return 1
            
    except Exception as e:
        logger.error(f"Stage error: {e}")
        stage_io.add_error(f"Stage error: {e}", e)
        stage_io.finalize(status="failed", error=str(e))
        
        if config.debug:
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        return 1


def process_stage(input_file, output_file, config, logger, stage_io):
    """Stage-specific processing logic with manifest tracking"""
    
    # Get parameters from config
    param = getattr(config, 'parameter_name', 'default_value')
    
    logger.info(f"Processing with parameter: {param}")
    logger.debug(f"Detailed processing info...")  # Only in stage.log
    
    # Create intermediate file if needed
    cache_file = stage_io.get_output_path("cache.bin")
    if create_cache:
        # ... create cache ...
        stage_io.track_intermediate(cache_file, 
                                   retained=True,
                                   reason="Model cache for faster runs")
        logger.debug(f"Cache created: {cache_file}")
    
    # Process
    # ... stage-specific logic ...
    
    # Save output
    with open(output_file, 'w') as f:
        # ... save results ...
        pass
    
    logger.info(f"Output saved to: {output_file}")
    
    return result_data


if __name__ == "__main__":
    # Determine job directory from environment or argument
    import os
    job_dir = Path(os.environ.get('OUTPUT_DIR', Path.cwd()))
    debug = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
    
    sys.exit(main())
```

### 4.2 StageIO Methods

```python
# Initialize
stage_io = StageIO("stage_name")

# Get input from specific stage
input_path = stage_io.get_input_path("file.ext", from_stage="previous_stage")

# Get input from previous stage (automatic)
input_path = stage_io.get_input_path("file.ext")

# Get output path
output_file = stage_io.get_output_path("file.ext")

# Access directories
stage_io.stage_dir    # Current stage directory
stage_io.output_base  # Job directory root
stage_io.logs_dir     # Logs directory
```

### 4.3 Stage Numbering

**Centralized in `shared/stage_order.py`:**

```python
STAGE_ORDER = [
    "demux",                    # 1
    "tmdb",                     # 2
    "glossary_load",            # 3
    "source_separation",        # 4
    "pyannote_vad",             # 5
    "asr",                      # 6
    "alignment",                # 7
    "lyrics_detection",         # 8
    "export_transcript",        # 9
    "translation",              # 10
    "subtitle_generation",      # 11
    "mux",                      # 12
]
```

**Rules:**
- **NEVER** hardcode stage numbers
- Use `get_stage_number(name)` from `shared/stage_order.py`
- Use `get_stage_dir(name)` for directory names
- Stage directories: `{number:02d}_{name}/` (e.g., `06_asr/`)

```python
# CORRECT
from shared.stage_order import get_stage_dir, get_stage_number

stage_dir = get_stage_dir("asr")  # Returns "06_asr"
stage_num = get_stage_number("asr")  # Returns 6

# INCORRECT
stage_dir = "06_asr"  # ❌ Hardcoded
stage_num = 6         # ❌ Hardcoded
```

---

## 5. LOGGING ARCHITECTURE & STANDARDS

### 5.1 Overview

The pipeline implements a **dual logging architecture** with comprehensive manifest tracking:

1. **Main Pipeline Log** (`logs/99_pipeline_<timestamp>.log`)
   - High-level orchestration and progress tracking
   - Stage transitions and overall timing
   - INFO level and above

2. **Stage-Specific Logs** (`<stage_dir>/stage.log`)
   - Detailed execution logs with ALL levels including DEBUG
   - Tool output (ffmpeg, whisperx, etc.)
   - Stage-specific debugging information

3. **Stage Manifests** (`<stage_dir>/manifest.json`)
   - Structured I/O tracking (inputs, outputs, intermediate files)
   - Configuration recording
   - Error and warning tracking
   - Resource usage and timing

**See Also:**
- [Complete Logging Architecture Guide](LOGGING_ARCHITECTURE.md)
- [Logging Quick Reference](LOGGING_QUICKREF.md)
- [Logging Diagrams](LOGGING_DIAGRAM.md)

### 5.2 Logger Initialization

```python
from shared.stage_utils import StageIO

# Initialize StageIO with manifest tracking
stage_io = StageIO("stage_name", job_dir, enable_manifest=True)

# Get dual logger (writes to both stage log and main pipeline log)
logger = stage_io.get_stage_logger("DEBUG" if debug else "INFO")

# For utility modules (single logger)
from shared.logger import PipelineLogger
logger = PipelineLogger("module_name", log_level="INFO")
```

**Log Level Routing:**
- `logger.debug()` → stage.log ONLY
- `logger.info()` → stage.log + pipeline log
- `logger.warning()` → stage.log + pipeline log
- `logger.error()` → stage.log + pipeline log

### 5.3 Logging Patterns with Manifest Tracking

```python
# Stage header (required at start of every stage)
# Log to both pipeline logger (self.logger) and stage logger
self.logger.info("=" * 60)
self.logger.info("STAGE NAME: Brief Description")
self.logger.info("=" * 60)
logger.info("Starting stage execution")

# Track inputs in manifest
stage_io.track_input(input_file, "audio", format="wav", sample_rate=16000)
self.logger.info(f"📥 Input: {input_file.relative_to(job_dir)}")
logger.info(f"Input file: {input_file}")

# Track configuration in manifest
stage_io.set_config({
    "model": "whisper-large-v3",
    "device": "mps",
    "batch_size": 16
})
logger.info(f"Configuration:")
logger.info(f"  Model: {config.model}")
logger.info(f"  Device: {config.device}")

# Progress logging (DEBUG goes to stage log only)
logger.debug(f"Processing chunk {i}/{total}")
logger.info(f"Processing {filename}...")
self.logger.info(f"Processing stage {i}/{total}")

# Track outputs in manifest
stage_io.track_output(output_file, "transcript", 
                      format="json",
                      segments=len(segments))
self.logger.info(f"📤 Output: {output_file.relative_to(job_dir)}")
logger.info(f"Output saved: {output_file}")

# Track intermediate files
stage_io.track_intermediate(cache_file, 
                            retained=True,
                            reason="Model cache for faster subsequent runs")
logger.debug(f"Cache file created: {cache_file}")

# Success/Failure with manifest finalization
stage_io.finalize(status="success", 
                 segments_processed=len(segments),
                 duration_seconds=duration)
self.logger.info("✓ Stage completed successfully")
logger.info(f"Stage log: {stage_io.stage_log.relative_to(job_dir)}")
logger.info(f"Stage manifest: {stage_io.manifest_path.relative_to(job_dir)}")

# Error handling with manifest tracking
try:
    result = operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    stage_io.add_error(f"Operation failed: {e}", e)
    stage_io.finalize(status="failed")
    self.logger.error(f"✗ Stage failed: {e}")
    if config.debug:
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    return 1

# Warnings with manifest tracking
if not optimal_config:
    logger.warning("Using suboptimal configuration")
    stage_io.add_warning("Using default configuration")
```

### 5.4 Manifest Tracking

**Every stage MUST track its I/O operations in the manifest:**

#### Track Inputs
```python
# Track all input files
stage_io.track_input(audio_file, "audio", 
                     format="wav",
                     sample_rate=16000,
                     channels=1)

stage_io.track_input(config_file, "config", format="json")
```

#### Track Outputs
```python
# Track all output files with metadata
stage_io.track_output(segments_file, "transcript",
                      format="json",
                      segments=len(segments),
                      language="hi")

stage_io.track_output(srt_file, "subtitle",
                      format="srt",
                      language="en",
                      duration_seconds=120)
```

#### Track Intermediate Files
```python
# Track intermediate/cache files with retention policy
stage_io.track_intermediate(model_cache, 
                            retained=True,
                            reason="Model cache for faster subsequent runs")

stage_io.track_intermediate(temp_file,
                            retained=False,
                            reason="Temporary processing file, deleted after stage")
```

#### Track Configuration
```python
# Record all configuration used
stage_io.set_config({
    "model": "whisper-large-v3",
    "device": "mps",
    "batch_size": 16,
    "language": "hi",
    "compute_type": "float32"
})

# Or add individual config items
stage_io.add_config("feature_enabled", True)
```

#### Track Errors and Warnings
```python
# Add errors to manifest (with optional exception)
try:
    result = process()
except ValueError as e:
    stage_io.add_error("Invalid input value", e)

# Add warnings to manifest
if suboptimal_config:
    stage_io.add_warning("Using default configuration, may be slower")
```

#### Finalize Stage
```python
# REQUIRED: Finalize manifest before returning
# Success case
stage_io.finalize(status="success",
                 segments_processed=150,
                 model_version="1.0.0",
                 throughput_realtime=2.5)

# Failure case
stage_io.finalize(status="failed",
                 error_message="Model loading failed",
                 attempted_device="cuda")

# Skipped case
stage_io.finalize(status="skipped",
                 reason="Feature disabled by user")
```

### 5.5 Manifest Schema

The manifest.json file created by each stage contains:

```json
{
  "stage": "asr",
  "stage_number": 5,
  "timestamp": "2025-11-27T14:09:16.123456",
  "status": "success",
  "duration_seconds": 45.2,
  "completed_at": "2025-11-27T14:10:01.345678",
  
  "inputs": [
    {
      "type": "audio",
      "path": "01_demux/audio.wav",
      "size_bytes": 47493120,
      "format": "wav",
      "sample_rate": 16000
    }
  ],
  
  "outputs": [
    {
      "type": "transcript",
      "path": "05_asr/segments.json",
      "size_bytes": 12345,
      "format": "json",
      "segments": 150
    }
  ],
  
  "intermediate_files": [
    {
      "type": "intermediate",
      "path": "05_asr/model_cache.bin",
      "retained": true,
      "reason": "Model cache for faster runs",
      "size_bytes": 1048576
    }
  ],
  
  "config": {
    "model": "whisper-large-v3",
    "device": "mps",
    "batch_size": 16
  },
  
  "resources": {},
  "errors": [],
  "warnings": []
}
```

### 5.6 Structured Logging

**For better observability, use structured fields:**

```python
# Instead of plain strings
logger.info(f"Processing {file} took {duration}s")

# Use structured fields (better for log aggregation)
logger.info("Processing complete", extra={
    "file": file,
    "duration_seconds": duration,
    "segments_count": len(segments),
    "stage": "asr",
    "job_id": job_id
})
```

### 5.7 Log Levels and Routing

**Understanding where log messages go:**

```python
# DEBUG: Detailed diagnostic information → stage.log ONLY
logger.debug(f"Processing chunk {i}/{total}")
logger.debug(f"Model input shape: {shape}")
logger.debug(f"Cache hit: {cache_key}")

# INFO: General informational messages → stage.log + pipeline.log
logger.info(f"Loaded {count} items")
self.logger.info(f"📥 Input: {file}")  # Pipeline log (orchestrator)

# WARNING: Warning messages → stage.log + pipeline.log
logger.warning(f"Parameter X not set, using default: {default}")
stage_io.add_warning(f"Using default configuration")  # Also to manifest

# ERROR: Error messages → stage.log + pipeline.log
logger.error(f"Failed to load file: {filename}")
stage_io.add_error(f"File load failed: {filename}")  # Also to manifest

# CRITICAL: Critical errors → stage.log + pipeline.log
logger.critical(f"System resource exhausted, aborting")
```

**Key Rules:**
- Use `logger.debug()` for detailed trace information (stage.log only)
- Use `logger.info()` for progress updates (both logs)
- Use `logger.warning()` for non-fatal issues (both logs + manifest)
- Use `logger.error()` for failures (both logs + manifest)
- Always call `stage_io.finalize()` before returning

### 5.8 Debugging with Logs and Manifests

**Three-step debugging process:**

```bash
# 1. Check main pipeline log - which stage failed?
grep "❌" logs/99_pipeline_*.log
# Output: ❌ Stage asr: FAILED

# 2. Check stage log - what was the error?
cat 05_asr/stage.log | tail -50
# See detailed error messages, stack traces, DEBUG output

# 3. Check manifest - what inputs were used?
jq . 05_asr/manifest.json
jq '.inputs' 05_asr/manifest.json      # Verify inputs
jq '.config' 05_asr/manifest.json      # Check configuration
jq '.errors' 05_asr/manifest.json      # Review errors
```

**Validate data flow:**
```bash
# Verify output from stage N matches input to stage N+1
jq '.outputs[0].path' 05_asr/manifest.json
jq '.inputs[0].path' 06_alignment/manifest.json
```

### 5.9 Log Aggregation

**For production deployments:**
- Use JSON format for machine parsing
- Configure log rotation (size/time based)
- Setup centralized logging (ELK Stack, Grafana Loki, CloudWatch)
- Add correlation IDs for request tracing across stages
- Aggregate manifests for data lineage visualization

```python
# Configure JSON logging
import logging
import json_logging

json_logging.init_non_web(enable_json=True)

# Add correlation ID to all logs
import contextvars

correlation_id = contextvars.ContextVar('correlation_id', default=None)

class CorrelationFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id.get() or "unknown"
        return True

logger.addFilter(CorrelationFilter())
```

---

## 6. DATA LINEAGE & AUDIT TRAILS

### 6.1 Manifest-Based Data Lineage

Every stage creates a manifest that tracks complete data lineage:

```python
# Example: Tracking data flow through pipeline
# Stage 1 (demux) produces audio.wav
stage_io.track_output(audio_file, "audio", format="wav")
# → Recorded in 01_demux/manifest.json → outputs[]

# Stage 5 (asr) consumes audio.wav
stage_io.track_input(audio_file, "audio", format="wav")
# → Recorded in 05_asr/manifest.json → inputs[]

# Stage 5 (asr) produces segments.json
stage_io.track_output(segments_file, "transcript", format="json")
# → Recorded in 05_asr/manifest.json → outputs[]

# Stage 6 (alignment) consumes segments.json
stage_io.track_input(segments_file, "transcript", format="json")
# → Recorded in 06_alignment/manifest.json → inputs[]
```

**Benefits:**
- **Traceability**: Track exactly what files were used at each stage
- **Reproducibility**: Replay pipeline with same inputs
- **Debugging**: Identify where data transformation went wrong
- **Compliance**: Complete audit trail for regulatory requirements
- **Data Governance**: Document data lineage for compliance

### 6.2 Intermediate File Documentation

**Document WHY intermediate files exist:**

```python
# Model cache (retained)
stage_io.track_intermediate(model_cache, 
                            retained=True,
                            reason="Model weights cached for faster subsequent runs")

# Temporary processing file (not retained)
stage_io.track_intermediate(temp_audio, 
                            retained=False,
                            reason="Temporary resampled audio, deleted after processing")

# Debug output (conditional retention)
if config.debug:
    stage_io.track_intermediate(debug_output,
                                retained=True,
                                reason="Debug output for troubleshooting")
```

### 6.3 Validating Data Flow

**Use manifests to validate pipeline integrity:**

```bash
#!/bin/bash
# validate_pipeline.sh - Verify complete data flow

validate_data_flow() {
    local job_dir="$1"
    
    echo "Validating data flow for job: $job_dir"
    
    # Check each stage's manifest
    for manifest in "$job_dir"/*/manifest.json; do
        stage=$(jq -r '.stage' "$manifest")
        echo "Stage: $stage"
        
        # Verify all inputs exist
        jq -r '.inputs[] | .path' "$manifest" | while read -r input; do
            if [ ! -f "$input" ]; then
                echo "  ✗ Missing input: $input"
                return 1
            fi
        done
        
        # Verify all outputs exist
        jq -r '.outputs[] | .path' "$manifest" | while read -r output; do
            if [ ! -f "$output" ]; then
                echo "  ✗ Missing output: $output"
                return 1
            fi
        done
        
        # Verify status
        status=$(jq -r '.status' "$manifest")
        if [ "$status" != "success" ]; then
            echo "  ✗ Stage failed with status: $status"
            return 1
        fi
        
        echo "  ✓ Stage validated"
    done
    
    echo "✓ Pipeline data flow validated"
}
```

### 6.4 Resource Tracking (Optional)

**Track resource usage for optimization:**

```python
import time
import psutil

# At stage start
start_time = time.time()
start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

# Process...

# At stage end
duration = time.time() - start_time
memory_used = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory

stage_io.set_resources(
    duration_seconds=duration,
    memory_mb=memory_used,
    cpu_percent=psutil.cpu_percent(),
    gpu_used=torch.cuda.is_available() if config.device == "cuda" else False
)
```

---

## 7. ERROR HANDLING

### 7.1 Error Handling Pattern with Manifest Tracking

```python
def process_operation(input_data, config, logger, stage_io):
    """Template for error handling with manifest tracking"""
    try:
        # Validate inputs
        if not input_data:
            error_msg = "Input data is empty"
            logger.error(error_msg, exc_info=True)
            stage_io.add_error(error_msg)
            return None
        
        # Process
        result = perform_operation(input_data)
        
        # Validate output
        if not result:
            error_msg = "Operation produced no output"
            logger.error(error_msg, exc_info=True)
            stage_io.add_error(error_msg)
            return None
        
        return result
        
    except FileNotFoundError as e:
        error_msg = f"File not found: {e}"
        logger.error(error_msg, exc_info=True)
        stage_io.add_error(error_msg, e)
        return None
        
    except ValueError as e:
        error_msg = f"Invalid value: {e}"
        logger.error(error_msg, exc_info=True)
        stage_io.add_error(error_msg, e)
        return None
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg, exc_info=True)
        stage_io.add_error(error_msg, e)
        
        if config.debug:
            import traceback
            traceback_str = traceback.format_exc()
            logger.error(f"Traceback: {traceback_str}")
        
        return None
```

**⚠️ CRITICAL: Error Logging Best Practices**

**DO:**
```python
# ✅ CORRECT - Include exc_info=True for exception context
logger.error(f"Failed to process: {e}", exc_info=True)
```

**DON'T:**
```python
# ❌ WRONG - Duplicate parameter causes SyntaxError
logger.error(f"Failed to process: {e}", exc_info=True, exc_info=True)

# ❌ WRONG - Missing exc_info loses stack trace
logger.error(f"Failed to process: {e}")
```

**Why exc_info=True?**
- Captures full stack trace for debugging
- Essential for diagnosing production issues
- Required by development standards (§ 7.1)
- Must appear exactly once per logger.error() call

**Historical Note:** This syntax error occurred in job-20251203-rpatel-0015, affecting 8 instances across 2 files (05_pyannote_vad.py, 07_alignment.py). The duplicate parameter caused immediate SyntaxError on script load.

### 7.2 Graceful Degradation with Warnings

```python
# Feature flags for optional functionality
if config.glossary_enabled:
    try:
        glossary = load_glossary()
    except Exception as e:
        warning_msg = f"Failed to load glossary: {e}"
        logger.warning(warning_msg)
        logger.warning("Continuing without glossary")
        stage_io.add_warning(warning_msg)
        glossary = None
else:
    glossary = None

# Continue with or without optional feature
result = process(data, glossary=glossary)
```

### 6.3 Retry Logic with Exponential Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError))
)
def download_model(model_name: str):
    """Download model with automatic retry on transient failures"""
    response = requests.get(f"https://models.example.com/{model_name}")
    response.raise_for_status()
    return response.content
```

### 6.4 Circuit Breaker Pattern

**For external service calls:**

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_tmdb_api(query: str):
    """Call TMDB API with circuit breaker protection"""
    response = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params={"query": query, "api_key": config.tmdb_api_key},
        timeout=10
    )
    response.raise_for_status()
    return response.json()
```

### 6.5 Exit Codes

```python
# Stage scripts MUST return appropriate exit codes
if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)
```

**Standard Exit Codes:**
- `0` - Success
- `1` - General failure
- `2` - Invalid input/configuration
- `3` - Resource not available
- `4` - External dependency failed

---

## 8. AUTOMATED ENFORCEMENT

### 8.1 Pre-commit Hook

A pre-commit hook is **ACTIVE** in this repository and automatically enforces compliance before every commit.

#### 8.1.1 What It Does

The pre-commit hook (`scripts/validate-compliance.py`):
- ✅ **Validates all Python files** before commit
- ✅ **Blocks commits** with compliance violations
- ✅ **Maintains 100% compliance** automatically
- ✅ **Provides helpful error messages** with exact locations
- ✅ **Zero-tolerance policy** - no violations allowed

#### 8.1.2 Validation Checks

The hook validates:
1. **Type Hints** - All functions must have parameter and return type hints
2. **Docstrings** - All modules, classes, and functions must be documented
3. **Logger Usage** - Must use `logger`, never `print()`
4. **Import Organization** - Standard/Third-party/Local order with blank lines
5. **Configuration** - Must use `load_config()`, not `os.getenv()`
6. **Error Handling** - Proper try/except blocks with logging
7. **StageIO Pattern** - Stages must use StageIO with `enable_manifest=True`

#### 8.1.3 Installation

The pre-commit hook is automatically installed by:
```bash
./bootstrap.sh
```

Or manually:
```bash
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

#### 8.1.4 Usage

The hook runs automatically on every commit:
```bash
git add your_file.py
git commit -m "Your message"
# → Hook runs automatically
# → Commit blocked if violations found
# → Fix violations and try again
```

#### 8.1.5 Manual Validation

Test compliance before committing:
```bash
# Single file
./scripts/validate-compliance.py scripts/your_stage.py

# Multiple files
./scripts/validate-compliance.py scripts/*.py

# Strict mode (exit 1 on violations)
./scripts/validate-compliance.py --strict scripts/*.py

# Check staged files only
./scripts/validate-compliance.py --staged
```

#### 8.1.6 Example Output

**✅ Compliant code:**
```
🔍 Running compliance validation...

✅ All checks passed!

Summary:
  Files checked: 1
  Critical issues: 0
  Errors: 0
  Warnings: 0

Status: ✅ COMPLIANT
```

**❌ Non-compliant code:**
```
🔍 Running compliance validation...

❌ scripts/my_stage.py

CRITICAL VIOLATIONS (2):
  Line 45: print() usage detected - use logger instead
  Line 67: Missing return type hint on function 'process_data'

ERROR: Compliance check failed
Commit blocked - fix violations above
```

#### 8.1.7 Benefits

- **Automatic Quality Control** - No manual review needed for standards
- **Zero Technical Debt** - Violations caught immediately
- **Consistent Codebase** - All code follows same patterns
- **Documentation** - Enforced docstrings and type hints
- **Confidence** - 100% compliance guaranteed

#### 8.1.8 Bypassing (Not Recommended)

In rare cases, bypass with:
```bash
git commit --no-verify -m "Emergency fix"
```

**⚠️ WARNING:** Only use for emergency hotfixes. All bypassed commits must be fixed immediately.

### 8.2 Continuous Integration

The validation also runs in CI/CD:
- GitHub Actions (if configured)
- Pre-merge checks
- Automated testing
- Documentation builds

See [PRE_COMMIT_HOOK_GUIDE.md](../PRE_COMMIT_HOOK_GUIDE.md) for complete documentation.

---

## 9. TESTING STANDARDS

### 9.1 Test Organization

```
tests/
├── unit/                  # Unit tests (fast, isolated)
│   ├── test_config.py
│   ├── test_stage_io.py
│   ├── test_glossary.py
│   └── test_logger.py
├── integration/           # Integration tests (slower, multi-component)
│   ├── test_asr_pipeline.py
│   ├── test_translation.py
│   └── test_end_to_end.py
├── performance/           # Performance regression tests
│   └── test_benchmarks.py
├── fixtures/              # Test data
│   ├── audio/
│   │   ├── test_1min.wav
│   │   └── test_5min.mp3
│   ├── config/
│   │   └── test_config.json
│   └── expected/
│       └── expected_output.json
└── conftest.py           # Pytest configuration
```

### 7.2 Test Coverage Requirements

**Minimum coverage targets:**
- Unit tests: **80% coverage**
- Integration tests: Core workflows covered
- E2E tests: Happy path + critical failure paths

```bash
# Run with coverage reporting
pytest --cov=shared --cov=scripts \
       --cov-report=html \
       --cov-report=term \
       --cov-fail-under=80

# Generate coverage badge
coverage-badge -o coverage.svg
```

### 7.3 Test Naming Convention

```python
# test_module_name.py

class TestClassName:
    """Test class for ComponentName"""
    
    def test_function_does_expected_behavior(self):
        """Test that function produces expected result"""
        result = function(input_data)
        assert result == expected
        
    def test_function_handles_invalid_input(self):
        """Test that function handles invalid input gracefully"""
        with pytest.raises(ValueError):
            function(invalid_input)
        
    def test_function_with_edge_case(self):
        """Test edge case scenario"""
        result = function(edge_case_input)
        assert result is not None
```

### 7.4 Property-Based Testing

**For complex transformations:**

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=1000))
def test_sanitize_filename_never_crashes(filename):
    """Property test: sanitize should never crash on any input"""
    result = sanitize_filename(filename)
    assert isinstance(result, str)
    assert '..' not in result
    assert '/' not in result
```

### 7.5 Performance Regression Tests

```python
@pytest.mark.performance
@pytest.mark.timeout(60)
def test_asr_throughput():
    """ASR should process at least 2x realtime on GPU"""
    audio_file = fixtures / "test_audio_60s.wav"
    audio_duration = 60  # seconds
    
    start_time = time.time()
    result = run_asr(audio_file, device="cuda")
    elapsed_time = time.time() - start_time
    
    throughput = audio_duration / elapsed_time
    
    assert throughput >= 2.0, (
        f"GPU throughput {throughput:.2f}x is below "
        f"required 2.0x realtime"
    )
```

### 7.6 Contract Testing

**Test stage interfaces:**

```python
def test_stage_contract_asr():
    """ASR stage must output segments.json with required fields"""
    result = run_stage("asr", test_input)
    
    segments = json.loads((result / "segments.json").read_text())
    required_fields = ['start', 'end', 'text', 'confidence']
    
    assert all(
        all(field in segment for field in required_fields)
        for segment in segments
    ), "ASR output missing required fields"
```

---

## 9. PERFORMANCE STANDARDS

### 8.1 Performance Budgets

**Maximum acceptable processing times:**

```python
PERFORMANCE_BUDGETS = {
    # Time in seconds per minute of input media
    "demux": 10,
    "asr_cpu": 60,
    "asr_gpu": 10,
    "asr_mps": 20,
    "translation": 5,  # per 1000 words
    "subtitle_generation": 3,
    "mux": 15,
}
```

### 8.2 Memory Limits

**Per-stage memory budgets:**

| Stage | Memory Limit | Notes |
|-------|--------------|-------|
| demux | 512MB | Streaming processing |
| asr | 8GB | With large-v3 model |
| translation | 4GB | IndicTrans2/NLLB |
| mux | 2GB | FFmpeg buffering |

### 8.3 Profiling Standards

**Profile stages when optimizing:**

```python
import cProfile
import pstats
from pathlib import Path

def profile_stage(func, output_file: Path):
    """Profile a stage and save detailed statistics"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func()
    
    profiler.disable()
    
    # Save for analysis
    profiler.dump_stats(str(output_file))
    
    # Print top consumers
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    return result

# Usage
profile_stage(
    lambda: run_asr_stage(test_audio),
    Path("profiling/asr_stage.prof")
)

# Analyze with snakeviz
# snakeviz profiling/asr_stage.prof
```

### 8.4 Performance Monitoring

**Track metrics in production:**

```python
import time
from contextlib import contextmanager

@contextmanager
def track_performance(stage_name: str, logger):
    """Context manager to track stage performance"""
    start_time = time.time()
    start_memory = get_memory_usage()
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        memory_delta = get_memory_usage() - start_memory
        
        logger.info("Performance metrics", extra={
            "stage": stage_name,
            "duration_seconds": duration,
            "memory_mb": memory_delta,
            "timestamp": time.time()
        })
        
        # Alert if over budget
        budget = PERFORMANCE_BUDGETS.get(stage_name)
        if budget and duration > budget:
            logger.warning(
                f"Stage {stage_name} exceeded budget: "
                f"{duration:.1f}s > {budget}s"
            )

# Usage
with track_performance("asr", logger):
    result = run_asr_stage()
```

---

## 10. CI/CD STANDARDS

### 9.1 GitHub Actions Workflows

**Required workflows:**

#### 1. Compliance Check

```yaml
# .github/workflows/compliance-check.yml
name: Standards Compliance Check

on: 
  pull_request:
  push:
    branches: [main, develop]

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run compliance check
        run: |
          python3 tools/check_compliance.py
          SCORE=$(python3 -c "import json; print(json.load(open('compliance_result.json'))['score'])")
          
          if [ "$SCORE" -lt 80 ]; then
            echo "✗ Compliance score $SCORE% is below 80% threshold"
            exit 1
          fi
          
          echo "✓ Compliance check passed: $SCORE%"
      
      - name: Upload compliance report
        uses: actions/upload-artifact@v3
        with:
          name: compliance-report
          path: compliance_result.json
```

#### 2. Automated Testing

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements/*.txt') }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements/requirements-common.txt
          pip install pytest pytest-cov
      
      - name: Run tests with coverage
        run: |
          pytest --cov=shared --cov=scripts \
                 --cov-report=xml \
                 --cov-report=term \
                 --junitxml=test-results.xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.os }}-${{ matrix.python-version }}
          path: test-results.xml
```

#### 3. Security Audit

```yaml
# .github/workflows/security.yml
name: Security Audit

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  pull_request:
    paths:
      - 'requirements/**'

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install pip-audit
        run: pip install pip-audit
      
      - name: Audit dependencies
        run: |
          for req in requirements/*.txt; do
            echo "Auditing $req"
            pip-audit -r "$req" || true
          done
```

### 9.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-json
      - id: check-merge-conflict
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--ignore=E203,W503']
  
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile=black']
  
  - repo: local
    hooks:
      - id: compliance-check
        name: Check standards compliance
        entry: python3 tools/check_compliance.py --min-score=80
        language: system
        pass_filenames: false
        stages: [commit]
```

**Install pre-commit hooks:**
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files  # Test hooks
```

---

## 11. OBSERVABILITY & MONITORING

### 10.1 Metrics Collection

**Instrument critical operations with Prometheus:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Counters - things that only go up
stages_completed = Counter(
    'pipeline_stages_completed_total',
    'Total stages completed',
    ['stage', 'status']
)

# Usage
stages_completed.labels(stage='asr', status='success').inc()

# Histograms - distribution of values
stage_duration = Histogram(
    'pipeline_stage_duration_seconds',
    'Stage processing duration',
    ['stage'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

# Usage with context manager
with stage_duration.labels(stage='asr').time():
    run_asr_stage()

# Gauges - values that go up and down
active_jobs = Gauge('pipeline_active_jobs', 'Currently active jobs')
active_jobs.set(get_active_job_count())
```

### 10.2 Health Checks

**Implement comprehensive health endpoints:**

```python
from fastapi import FastAPI, status
from datetime import datetime
import psutil

app = FastAPI()

@app.get("/health")
def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": VERSION
    }

@app.get("/health/ready")
def readiness_check():
    """Detailed readiness check"""
    checks = {
        "models_loaded": check_models_loaded(),
        "disk_space": check_disk_space() > 10_000_000_000,  # 10GB
        "memory_available": psutil.virtual_memory().available > 2_000_000_000,  # 2GB
        "gpu_available": check_gpu_available() if config.device == "cuda" else True,
    }
    
    all_healthy = all(checks.values())
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }, status_code

@app.get("/health/live")
def liveness_check():
    """Simple liveness probe (for Kubernetes)"""
    return {"alive": True}
```

### 10.3 Distributed Tracing

**Implement OpenTelemetry tracing:**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Setup tracer
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Instrument stage execution
def run_asr_with_tracing(audio_file, config):
    with tracer.start_as_current_span("asr-stage") as span:
        span.set_attribute("audio.file", str(audio_file))
        span.set_attribute("config.model", config.whisper_model)
        
        with tracer.start_as_current_span("load-model"):
            model = load_model(config.whisper_model)
        
        with tracer.start_as_current_span("transcribe"):
            result = transcribe(audio_file, model)
        
        span.set_attribute("result.segments", len(result['segments']))
        
        return result
```

---

## 12. DISASTER RECOVERY

### 11.1 Backup Strategy

**Critical data to backup:**

1. **Configuration Files** (`config/`)
   - `.env.pipeline` - Pipeline configuration
   - `secrets.json` - API keys (encrypted)
   - `hardware_cache.json` - Hardware profiles

2. **Custom Glossaries** (`glossary/`)
   - User-created term glossaries
   - Character name mappings

3. **Job Outputs** (`out/`) - Optional
   - Can be regenerated from source media
   - Backup if regeneration is expensive

**Automated backup script:**

```bash
#!/bin/bash
# backup.sh - Daily backup script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/cp-whisperx"
BACKUP_FILE="backup-${DATE}.tar.gz"

# Create encrypted backup
tar -czf - config/ glossary/ | \
    openssl enc -aes-256-cbc -salt -pass pass:${BACKUP_PASSWORD} \
    > "${BACKUP_DIR}/${BACKUP_FILE}"

# Upload to cloud storage (AWS S3, Google Cloud Storage, etc.)
aws s3 cp "${BACKUP_DIR}/${BACKUP_FILE}" \
    "s3://backups/cp-whisperx/${BACKUP_FILE}"

# Retention: Keep last 30 days
find "${BACKUP_DIR}" -name "backup-*.tar.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}"
```

**Schedule with cron:**
```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/cp-whisperx-backup.log 2>&1
```

### 11.2 Job Recovery with Checkpoints

**Implement checkpoint system:**

```python
from pathlib import Path
import json
from datetime import datetime
from typing import Optional, Dict, Any

class CheckpointManager:
    """Manage stage checkpoints for job recovery"""
    
    def __init__(self, job_dir: Path):
        self.job_dir = job_dir
        self.checkpoint_dir = job_dir / ".checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)
    
    def save_checkpoint(self, stage: str, state: Dict[str, Any]):
        """Save checkpoint after stage completion"""
        checkpoint_file = self.checkpoint_dir / f"{stage}.json"
        
        checkpoint_data = {
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "completed": True
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        logger.info(f"Checkpoint saved for stage: {stage}")
    
    def load_checkpoint(self, stage: str) -> Optional[Dict[str, Any]]:
        """Load checkpoint for stage if exists"""
        checkpoint_file = self.checkpoint_dir / f"{stage}.json"
        
        if not checkpoint_file.exists():
            return None
        
        with open(checkpoint_file) as f:
            checkpoint_data = json.load(f)
        
        if checkpoint_data.get("completed"):
            logger.info(f"Loaded checkpoint for stage: {stage}")
            return checkpoint_data["state"]
        
        return None
    
    def get_last_completed_stage(self) -> Optional[str]:
        """Find the last completed stage"""
        checkpoints = sorted(self.checkpoint_dir.glob("*.json"))
        
        for checkpoint_file in reversed(checkpoints):
            with open(checkpoint_file) as f:
                data = json.load(f)
                if data.get("completed"):
                    return data["stage"]
        
        return None

# Usage in pipeline
checkpoint_mgr = CheckpointManager(job_dir)

# Save after each stage
result = run_stage("asr", inputs)
checkpoint_mgr.save_checkpoint("asr", {
    "segments_count": len(result),
    "duration": duration
})

# Resume from last checkpoint
last_stage = checkpoint_mgr.get_last_completed_stage()
if last_stage:
    logger.info(f"Resuming from stage: {last_stage}")
    from shared.stage_order import STAGE_ORDER
    start_index = STAGE_ORDER.index(last_stage) + 1
    start_from_stage = STAGE_ORDER[start_index]
else:
    start_from_stage = STAGE_ORDER[0]
```

---

## 13. CODE STYLE & QUALITY

### 12.1 Python Style (PEP 8)

```python
# Naming conventions
class ClassName:                    # PascalCase for classes
    pass

def function_name():                # snake_case for functions
    pass

CONSTANT_NAME = "value"             # UPPER_SNAKE_CASE for constants

variable_name = "value"             # snake_case for variables

# Type hints (required for all public APIs)
from typing import Optional, List, Dict, Any

def process_segments(
    segments: List[Dict[str, Any]],
    config: Config,
    logger: PipelineLogger
) -> Optional[List[Dict[str, Any]]]:
    """Process transcript segments with configuration"""
    pass

# Line length: 100 characters (not strict 79)
# Imports: Organize by standard library, third party, local
import os                           # Standard library
import sys

import torch                        # Third party

from shared.logger import Logger    # Local imports
```

### 12.2 Type Hints Enforcement

**Enable type checking in CI:**

```bash
# Install mypy
pip install mypy types-requests

# Run type checker (strict mode)
mypy scripts/ shared/ --strict --ignore-missing-imports

# Configure mypy
cat > mypy.ini << 'EOF'
[mypy]
python_version = 3.11
strict = True
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

[mypy-scripts.legacy.*]
ignore_errors = True
EOF
```

### 12.3 Code Quality Tools

```bash
# Black: Code formatter
black scripts/ shared/ tests/

# isort: Import sorting
isort scripts/ shared/ tests/

# flake8: Linting
flake8 scripts/ shared/ tests/ --max-line-length=100

# pylint: Additional linting
pylint scripts/ shared/
```

---

## 14. DOCUMENTATION STANDARDS

### 13.1 Docstring Format (Google Style)

```python
def function_name(param1: type, param2: type) -> return_type:
    """Brief one-line description.
    
    More detailed description if needed. Explain what the function
    does, not how it does it.
    
    Args:
        param1: Description of param1
        param2: Description of param2, including valid values
                if applicable (e.g., "must be > 0")
    
    Returns:
        Description of return value. For complex returns, use:
        Dict with keys:
            - 'segments': List of transcript segments
            - 'confidence': Overall confidence score
        
    Raises:
        ValueError: When param is invalid
        FileNotFoundError: When file doesn't exist
        
    Example:
        >>> result = function_name(10, "test")
        >>> print(result)
        'processed: test with 10'
    """
```

### 13.2 Module Documentation

**Every Python module MUST have:**

```python
#!/usr/bin/env python3
"""
Module Name: Brief description

This module provides functionality for [purpose]. It includes:
- Feature 1
- Feature 2
- Feature 3

Usage:
    from module_name import ClassName
    
    obj = ClassName(param1, param2)
    result = obj.process()

Note:
    This module requires [dependencies] to be installed.
"""
```

### 13.3 Shell Script Documentation

```bash
#!/bin/bash
# ============================================================================
# Script Name - Brief Description
# ============================================================================
# Version: X.Y.Z
# Date: YYYY-MM-DD
#
# Longer description of what the script does, its purpose,
# and any important context.
#
# Usage:
#   ./script-name.sh [OPTIONS] ARGS
#
# Options:
#   -h, --help      Show this help message
#   -v, --verbose   Enable verbose output
#
# Examples:
#   ./script-name.sh --verbose input.txt
# ============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly VERSION="1.0.0"

# Function documentation
function process_file() {
    # Brief description of what this function does
    #
    # Args:
    #   $1 - Input file path
    #   $2 - Output directory
    #
    # Returns:
    #   0 on success, 1 on failure
    
    local input_file="$1"
    local output_dir="$2"
    
    # Implementation
}
```

---

## 15. COMPLIANCE IMPROVEMENT ROADMAP

### Priority 0: Critical (2-4 hours)
**Target: 80% compliance**

1. **Config Migration** (2-3 hours)
   - Update all 10 stages to use `load_config()`
   - Remove all `os.environ.get()` calls
   - Test each stage individually

2. **Quick Wins** (1-2 hours)
   - Add logger imports to 6 stages
   - Fix hardcoded paths in 3 stages

**Expected Result:** 75-80% compliance

### Priority 1: High (4-6 hours)
**Target: 90% compliance**

1. **StageIO Migration** (3-4 hours)
   - Update tmdb, asr, alignment to use StageIO
   - Test path resolution

2. **Error Handling** (1-2 hours)
   - Add proper error handling to pyannote_vad and asr
   - Add main() functions where missing

**Expected Result:** 90-95% compliance

### Priority 2: Medium (4-6 hours)
**Target: 100% compliance**

1. **Missing Stages** (4-6 hours)
   - Implement export_transcript stage
   - Extract translation logic to separate scripts
   - Test integration

**Expected Result:** 100% compliance

---

## 16. ANTI-PATTERNS TO AVOID

### 15.1 Configuration Anti-Patterns

❌ **DON'T:**
```python
# Hardcoded values
model = "large-v3"

# Direct environment access
model = os.environ.get('WHISPER_MODEL', 'large-v3')

# Stage-specific config files
with open('asr_config.yaml') as f:
    config = yaml.load(f)
```

✅ **DO:**
```python
# Use Config class with defaults
from shared.config import load_config

config = load_config()
model = getattr(config, 'whisper_model', 'large-v3')
```

### 15.2 Stage Anti-Patterns

❌ **DON'T:**
```python
# Hardcoded paths
output_dir = Path("out/2025/11/26/user/1/06_asr")

# Direct file operations without StageIO
with open("../05_vad/segments.json") as f:
    segments = json.load(f)

# Hardcoded stage numbers
stage_dir = f"06_asr"
```

✅ **DO:**
```python
# Use StageIO
from shared.stage_utils import StageIO
from shared.stage_order import get_stage_dir

stage_io = StageIO("asr")
output_dir = stage_io.output_base

# Get input from previous stage
segments_file = stage_io.get_input_path("segments.json", from_stage="pyannote_vad")

# Use centralized stage numbering
stage_dir = get_stage_dir("asr")
```

### 15.3 Logging Anti-Patterns

❌ **DON'T:**
```python
# Print statements
print(f"Processing {filename}")

# Inconsistent formatting
logger.info("Starting...")
logger.info("===")

# No context
logger.error("Failed")

# Missing manifest tracking
output_file = process()
# No track_output() call

# No finalization
return True  # Forgot stage_io.finalize()

# Direct file operations without tracking
with open("output.json", 'w') as f:
    json.dump(data, f)
# File created but not tracked in manifest
```

✅ **DO:**
```python
# Use dual logging consistently
from shared.stage_utils import StageIO

stage_io = StageIO("stage_name", job_dir, enable_manifest=True)
logger = stage_io.get_stage_logger()

# Consistent headers to both loggers
self.logger.info("=" * 60)
self.logger.info("STAGE NAME: Description")
self.logger.info("=" * 60)
logger.info(f"Processing {filename}")

# Informative messages with context
logger.error(f"Failed to process {filename}: {error}")

# Always track I/O in manifest
stage_io.track_input(input_file, "audio", format="wav")
output_file = process()
stage_io.track_output(output_file, "transcript", format="json")

# Always finalize
stage_io.finalize(status="success", items_processed=150)
return True

# Track all file operations
output_file = stage_io.get_output_path("output.json")
with open(output_file, 'w') as f:
    json.dump(data, f)
stage_io.track_output(output_file, "data", format="json", items=len(data))
```

---

## APPENDIX A: QUICK REFERENCE

### Common Commands

```bash
# Setup environment
./bootstrap.sh

# Create job
./prepare-job.sh --media file.mp4 --workflow translate -s hi -t en

# Run pipeline
./run-pipeline.sh translate path/to/job/dir

# Check compliance
python3 tools/check_compliance.py

# Run tests with coverage
pytest --cov=shared --cov=scripts --cov-report=html

# Check logs
tail -f out/YYYY/MM/DD/user/N/logs/99_pipeline*.log
```

### Common Imports

```python
# Stage implementation with logging architecture
from shared.stage_utils import StageIO
from shared.config import load_config
from shared.stage_order import get_stage_dir, get_stage_number

# Environment management
from shared.environment_manager import EnvironmentManager

# Manifest tracking
from shared.stage_manifest import StageManifest

# Glossary system
from shared.glossary_manager import GlossaryManager

# Hardware detection
from shared.hardware_detection import detect_device
```

### Configuration Access

```python
# Load config
from shared.config import load_config

config = load_config()

# Access with default
value = getattr(config, 'param_name', 'default_value')

# Common parameters
model = config.whisper_model
device = config.device
batch_size = config.batch_size
debug = config.debug
```

---

## APPENDIX B: COMPLIANCE CHECKING

### Automated Compliance Check

Run the automated compliance checker:

```bash
# Check all stages
python3 tools/check_compliance.py

# Check specific stage
python3 tools/check_compliance.py --stage=asr

# Generate detailed report
python3 tools/check_compliance.py --output=compliance_report.html

# Set minimum score threshold
python3 tools/check_compliance.py --min-score=80
```

### Manual Compliance Checklist

**For each new stage:**

#### Core Patterns (REQUIRED)
- [ ] Uses StageIO pattern for path management
- [ ] Initializes StageIO with `enable_manifest=True`
- [ ] Uses `get_stage_logger()` for dual logging
- [ ] Loads config with `load_config()`
- [ ] Stage registered in `shared/stage_order.py`
- [ ] No hardcoded paths or stage numbers
- [ ] Proper error handling with try/except
- [ ] Returns appropriate exit codes (0 for success, >0 for failure)

#### Logging & Manifest Tracking (REQUIRED)
- [ ] Tracks all input files with `stage_io.track_input()`
- [ ] Tracks all output files with `stage_io.track_output()`
- [ ] Tracks intermediate files with `stage_io.track_intermediate()`
- [ ] Records configuration with `stage_io.set_config()`
- [ ] Adds errors to manifest with `stage_io.add_error()`
- [ ] Adds warnings to manifest with `stage_io.add_warning()`
- [ ] Calls `stage_io.finalize()` before every return
- [ ] Logs to both pipeline logger (`self.logger`) and stage logger (`logger`)
- [ ] Uses DEBUG level for detailed trace (stage log only)
- [ ] Uses INFO level for progress (both logs)

#### Documentation (REQUIRED)
- [ ] Has module docstring explaining purpose
- [ ] Documents expected inputs and outputs
- [ ] Documents intermediate files and retention policy
- [ ] Has function docstrings for public functions
- [ ] Includes example usage in docstring
- [ ] Type hints on all public functions

#### Testing (REQUIRED)
- [ ] Tests written for happy path
- [ ] Tests written for error conditions
- [ ] Tests verify manifest creation
- [ ] Tests verify log file creation

**For configuration changes:**

- [ ] Parameters in config/.env.pipeline only
- [ ] No hardcoded values in code
- [ ] Documentation includes purpose and valid values
- [ ] Sensible defaults provided
- [ ] Validation added if applicable
- [ ] Backward compatible (or migration documented)

---

## 16. AI MODEL ROUTING & AUTOMATED UPDATES

### 16.1 Overview

**Purpose:** Ensure AI_MODEL_ROUTING.md stays current with latest model releases and Copilot makes optimal routing decisions.

**Key Principle:** Models improve rapidly. Our routing decisions must be data-driven and automatically updated to leverage the best available models for each task type.

**Documents:**
- `docs/AI_MODEL_ROUTING.md` - Model selection guide (auto-updated)
- `.github/copilot-instructions.md` - Quick reference for Copilot (synced from AI_MODEL_ROUTING.md)

### 16.2 Automated Model Update System

#### Model Registry (Source of Truth)

**Location:** `config/ai_models.json`

```json
{
  "version": "1.0",
  "last_updated": "2025-12-03",
  "update_frequency": "weekly",
  "models": {
    "gpt-4-turbo": {
      "provider": "OpenAI",
      "tier": "standard",
      "cost_per_1k_tokens": 0.01,
      "capabilities": ["code", "reasoning", "planning"],
      "optimal_for": ["T1", "T2_low_risk", "T7"],
      "context_window": 128000,
      "release_date": "2024-04-09",
      "status": "active",
      "performance_score": 85
    },
    "gpt-4o": {
      "provider": "OpenAI",
      "tier": "premium",
      "cost_per_1k_tokens": 0.005,
      "capabilities": ["code", "multimodal", "fast"],
      "optimal_for": ["T2", "T5_low_risk"],
      "context_window": 128000,
      "release_date": "2024-05-13",
      "status": "active",
      "performance_score": 90
    },
    "claude-3-5-sonnet-20241022": {
      "provider": "Anthropic",
      "tier": "premium",
      "cost_per_1k_tokens": 0.003,
      "capabilities": ["code", "reasoning", "analysis", "refactoring"],
      "optimal_for": ["T3", "T4", "T7_high_risk"],
      "context_window": 200000,
      "release_date": "2024-10-22",
      "status": "active",
      "performance_score": 95
    },
    "o1-preview": {
      "provider": "OpenAI",
      "tier": "advanced",
      "cost_per_1k_tokens": 0.015,
      "capabilities": ["deep_reasoning", "architecture", "complex_logic"],
      "optimal_for": ["T4_high_risk", "T5_high_risk"],
      "context_window": 128000,
      "release_date": "2024-09-12",
      "status": "active",
      "performance_score": 92
    },
    "o1": {
      "provider": "OpenAI",
      "tier": "advanced",
      "cost_per_1k_tokens": 0.015,
      "capabilities": ["deep_reasoning", "architecture", "complex_logic"],
      "optimal_for": ["T4_high_risk", "architecture_changes"],
      "context_window": 200000,
      "release_date": "2024-12-05",
      "status": "active",
      "performance_score": 96
    }
  },
  "task_types": {
    "T1": "Read/Explain",
    "T2": "Small change (≤1 file, ≤50 LOC)",
    "T3": "Medium change (2-5 files, 50-300 LOC)",
    "T4": "Large change (≥6 files, >300 LOC)",
    "T5": "Debug/Investigate",
    "T6": "Docs/Comms",
    "T7": "Standards compliance"
  },
  "risk_levels": {
    "low": "No stage boundaries, manifests, or CI changes",
    "medium": "Touches stage logic or multiple files",
    "high": "Manifests, resume logic, CI, dependencies, >10 files"
  }
}
```

#### Update Automation Script

**Location:** `tools/update-model-routing.py`

**Purpose:** Automatically check for new models and update routing decisions based on performance data.

```python
#!/usr/bin/env python3
"""
Automated Model Routing Updater

Checks for new AI models, evaluates performance, and updates routing decisions.
Run: ./tools/update-model-routing.py [--check-only] [--force]
"""
from pathlib import Path
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ModelRoutingUpdater:
    """Updates AI model routing based on latest releases and performance."""
    
    def __init__(self, config_path: Path, dry_run: bool = False):
        self.config_path = config_path
        self.dry_run = dry_run
        self.models_file = Path("config/ai_models.json")
        self.routing_doc = Path("docs/AI_MODEL_ROUTING.md")
        self.copilot_instructions = Path(".github/copilot-instructions.md")
        
    def check_for_updates(self) -> Dict[str, any]:
        """Check OpenAI and Anthropic APIs for new models."""
        updates = {
            "new_models": [],
            "deprecated_models": [],
            "updated_capabilities": []
        }
        
        # Check OpenAI models
        try:
            openai_models = self._fetch_openai_models()
            updates["new_models"].extend(openai_models)
        except Exception as e:
            logger.error(f"Failed to fetch OpenAI models: {e}")
        
        # Check Anthropic models
        try:
            anthropic_models = self._fetch_anthropic_models()
            updates["new_models"].extend(anthropic_models)
        except Exception as e:
            logger.error(f"Failed to fetch Anthropic models: {e}")
        
        return updates
    
    def _fetch_openai_models(self) -> List[Dict]:
        """Fetch latest OpenAI models from API."""
        # Implementation would call OpenAI API
        # For now, placeholder for structure
        return []
    
    def _fetch_anthropic_models(self) -> List[Dict]:
        """Fetch latest Anthropic models from releases page."""
        # Implementation would scrape Anthropic releases
        return []
    
    def evaluate_model_performance(self, model_id: str) -> int:
        """
        Evaluate model performance score (0-100).
        
        Based on:
        - Benchmark results on standard test tasks
        - Community feedback
        - Official performance metrics
        - Cost-effectiveness ratio
        """
        # Placeholder - in production, would run actual benchmarks
        return 85
    
    def update_routing_decisions(self, updates: Dict) -> Dict[str, str]:
        """
        Update routing decisions based on new model data.
        
        Returns: Dict of task_type -> recommended_model
        """
        with open(self.models_file) as f:
            model_data = json.load(f)
        
        routing = {}
        
        # For each task type and risk level, find best model
        for task, description in model_data["task_types"].items():
            for risk in ["low", "medium", "high"]:
                key = f"{task}_{risk}"
                best_model = self._find_best_model(
                    task, risk, model_data["models"]
                )
                routing[key] = best_model
        
        return routing
    
    def _find_best_model(
        self, 
        task_type: str, 
        risk_level: str, 
        models: Dict
    ) -> str:
        """Find best model for task type and risk level."""
        candidates = []
        
        for model_id, model_info in models.items():
            if model_info["status"] != "active":
                continue
            
            # Check if model is optimal for this task type
            task_key = f"{task_type}_{risk_level}"
            if task_key in model_info["optimal_for"]:
                candidates.append({
                    "id": model_id,
                    "score": model_info["performance_score"],
                    "cost": model_info["cost_per_1k_tokens"]
                })
        
        if not candidates:
            return "gpt-4-turbo"  # Fallback
        
        # Sort by performance score, then by cost (lower is better)
        candidates.sort(
            key=lambda x: (-x["score"], x["cost"])
        )
        
        return candidates[0]["id"]
    
    def generate_routing_table(self, routing: Dict[str, str]) -> str:
        """Generate markdown table for AI_MODEL_ROUTING.md."""
        with open(self.models_file) as f:
            model_data = json.load(f)
        
        # Build routing table
        table = "| Task | Low Risk | Medium Risk | High Risk |\n"
        table += "|------|----------|-------------|------------|\n"
        
        for task, description in model_data["task_types"].items():
            low = routing.get(f"{task}_low", "gpt-4-turbo")
            med = routing.get(f"{task}_medium", "gpt-4-turbo")
            high = routing.get(f"{task}_high", "claude-3-5-sonnet")
            
            # Format model names for readability
            low_name = self._format_model_name(low)
            med_name = self._format_model_name(med)
            high_name = self._format_model_name(high)
            
            table += f"| {description} | {low_name} | {med_name} | {high_name} |\n"
        
        return table
    
    def _format_model_name(self, model_id: str) -> str:
        """Convert model ID to readable name."""
        name_map = {
            "gpt-4-turbo": "GPT-4 Turbo",
            "gpt-4o": "GPT-4o",
            "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet",
            "o1-preview": "o1-preview",
            "o1": "o1"
        }
        return name_map.get(model_id, model_id)
    
    def update_routing_doc(self, routing_table: str) -> bool:
        """Update AI_MODEL_ROUTING.md with new routing table."""
        if self.dry_run:
            logger.info("DRY RUN: Would update AI_MODEL_ROUTING.md")
            return True
        
        # Read current doc
        with open(self.routing_doc) as f:
            content = f.read()
        
        # Find and replace routing table section
        # Look for "## 3) Routing algorithm" section
        marker_start = "### Step C — pick model + workflow"
        marker_end = "---"
        
        start_idx = content.find(marker_start)
        if start_idx == -1:
            logger.error("Could not find routing table marker")
            return False
        
        # Find next section marker
        end_idx = content.find(marker_end, start_idx + 100)
        if end_idx == -1:
            logger.error("Could not find end of routing section")
            return False
        
        # Replace content
        new_content = (
            content[:start_idx + len(marker_start)] +
            "\n" + routing_table + "\n" +
            content[end_idx:]
        )
        
        # Add update timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        new_content = new_content.replace(
            "**Last Updated:**",
            f"**Last Updated:** {timestamp} (auto-updated)\n**Previous Update:**"
        )
        
        # Write back
        with open(self.routing_doc, 'w') as f:
            f.write(new_content)
        
        logger.info("✅ Updated AI_MODEL_ROUTING.md")
        return True
    
    def sync_to_copilot_instructions(self) -> bool:
        """Sync key routing decisions to copilot-instructions.md."""
        if self.dry_run:
            logger.info("DRY RUN: Would sync to copilot-instructions.md")
            return True
        
        # Read AI_MODEL_ROUTING.md
        with open(self.routing_doc) as f:
            routing_content = f.read()
        
        # Extract key guidance
        # Find "## 2) Model selection: principle + escalation ladder"
        principle_start = routing_content.find("## 2) Model selection:")
        principle_end = routing_content.find("## 3)", principle_start)
        
        if principle_start == -1 or principle_end == -1:
            logger.error("Could not extract routing principle")
            return False
        
        principle_section = routing_content[principle_start:principle_end]
        
        # Update copilot-instructions.md
        with open(self.copilot_instructions) as f:
            copilot_content = f.read()
        
        # Find "## 📍 Model Routing" section
        routing_marker = "## 📍 Model Routing"
        next_section = "## 📍 Standard Test Media"
        
        marker_idx = copilot_content.find(routing_marker)
        next_idx = copilot_content.find(next_section, marker_idx)
        
        if marker_idx == -1:
            # Section doesn't exist, add it
            logger.info("Adding model routing section to copilot-instructions.md")
            # Insert before "Standard Test Media" section
            insert_point = copilot_content.find(next_section)
            if insert_point != -1:
                new_content = (
                    copilot_content[:insert_point] +
                    f"\n{routing_marker}\n\n**Consult:** `docs/AI_MODEL_ROUTING.md` before choosing models\n\n" +
                    f"**Quick Reference:** See routing table in AI_MODEL_ROUTING.md § 3\n\n" +
                    f"**Last Synced:** {datetime.now().strftime('%Y-%m-%d')}\n\n---\n\n" +
                    copilot_content[insert_point:]
                )
            else:
                new_content = copilot_content
        else:
            # Section exists, update timestamp
            new_content = copilot_content.replace(
                "**Last Synced:**",
                f"**Last Synced:** {datetime.now().strftime('%Y-%m-%d')}\n**Previous:**"
            )
        
        with open(self.copilot_instructions, 'w') as f:
            f.write(new_content)
        
        logger.info("✅ Synced to copilot-instructions.md")
        return True
    
    def run(self, force: bool = False) -> bool:
        """Run full update process."""
        logger.info("🔍 Checking for model updates...")
        
        # Check if update is needed
        with open(self.models_file) as f:
            model_data = json.load(f)
        
        last_update = datetime.fromisoformat(model_data["last_updated"])
        days_since_update = (datetime.now() - last_update).days
        
        if not force and days_since_update < 7:
            logger.info(f"✅ No update needed (last updated {days_since_update} days ago)")
            return True
        
        # Check for new models
        updates = self.check_for_updates()
        
        if updates["new_models"]:
            logger.info(f"🆕 Found {len(updates['new_models'])} new models")
        
        # Update routing decisions
        logger.info("📊 Calculating optimal routing...")
        routing = self.update_routing_decisions(updates)
        
        # Generate new routing table
        logger.info("📝 Generating routing table...")
        routing_table = self.generate_routing_table(routing)
        
        # Update documents
        logger.info("📄 Updating documentation...")
        success = self.update_routing_doc(routing_table)
        
        if success:
            success = self.sync_to_copilot_instructions()
        
        # Update timestamp in models file
        if success and not self.dry_run:
            model_data["last_updated"] = datetime.now().isoformat()
            with open(self.models_file, 'w') as f:
                json.dump(model_data, f, indent=2)
        
        if success:
            logger.info("✅ Model routing update complete!")
        else:
            logger.error("❌ Model routing update failed")
        
        return success


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update AI model routing based on latest releases"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check for updates without applying changes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force update even if within update frequency"
    )
    
    args = parser.parse_args()
    
    updater = ModelRoutingUpdater(
        config_path=Path("config/ai_models.json"),
        dry_run=args.check_only
    )
    
    success = updater.run(force=args.force)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
```

### 16.3 Automated Update Schedule

**Frequency:** Weekly (every Monday)

**Automation:** GitHub Actions workflow

**Location:** `.github/workflows/update-model-routing.yml`

```yaml
name: Update AI Model Routing

on:
  schedule:
    # Run every Monday at 9 AM UTC
    - cron: '0 9 * * 1'
  workflow_dispatch:
    inputs:
      force:
        description: 'Force update'
        required: false
        default: 'false'

jobs:
  update-routing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install requests pyyaml
      
      - name: Check for model updates
        id: check
        run: |
          python tools/update-model-routing.py --check-only
          echo "updates_available=$?" >> $GITHUB_OUTPUT
      
      - name: Apply updates
        if: steps.check.outputs.updates_available == '0' || github.event.inputs.force == 'true'
        run: |
          python tools/update-model-routing.py --force
      
      - name: Create Pull Request
        if: steps.check.outputs.updates_available == '0'
        uses: peter-evans/create-pull-request@v5
        with:
          commit-message: 'docs: auto-update AI model routing'
          title: 'Auto-update: AI Model Routing'
          body: |
            ## Automated Model Routing Update
            
            This PR updates AI model routing based on:
            - New model releases
            - Performance benchmarks
            - Cost optimizations
            
            ### Changes
            - Updated `docs/AI_MODEL_ROUTING.md`
            - Synced `.github/copilot-instructions.md`
            - Updated model registry
            
            ### Review Checklist
            - [ ] Routing decisions are optimal
            - [ ] Cost trade-offs are acceptable
            - [ ] Documentation is clear
            
            **Auto-generated by:** `.github/workflows/update-model-routing.yml`
          branch: auto-update-model-routing
          delete-branch: true
```

### 16.4 Manual Update Process

**When to manually update:**
- Major model release (GPT-5, Claude 4, etc.)
- Significant price changes
- New capability announced
- Community feedback on model performance

**Steps:**

1. **Update Model Registry:**
   ```bash
   # Edit config/ai_models.json
   # Add new model or update existing
   ```

2. **Run Update Script:**
   ```bash
   ./tools/update-model-routing.py --force
   ```

3. **Review Changes:**
   ```bash
   git diff docs/AI_MODEL_ROUTING.md
   git diff .github/copilot-instructions.md
   ```

4. **Test Routing:**
   ```bash
   # Verify routing decisions make sense
   grep -A 20 "Step C" docs/AI_MODEL_ROUTING.md
   ```

5. **Commit & PR:**
   ```bash
   git add config/ai_models.json docs/AI_MODEL_ROUTING.md .github/copilot-instructions.md
   git commit -m "docs: update AI model routing for [MODEL_NAME]"
   git push origin update-model-routing
   ```

### 16.5 Model Performance Tracking

**Benchmarks:** Run standard tasks against each model

**Location:** `tools/benchmark-models.py`

**Test Tasks:**
1. **T2 Small Change:** Fix simple bug (≤50 LOC)
2. **T3 Medium Change:** Refactor module (2-3 files)
3. **T5 Debug:** Root cause analysis
4. **T7 Standards Fix:** Fix compliance violations

**Metrics Tracked:**
- **Correctness:** Does it solve the problem?
- **Code Quality:** Follows standards?
- **Completeness:** All edge cases covered?
- **Speed:** Time to completion
- **Cost:** Token usage × cost

**Run Monthly:**
```bash
./tools/benchmark-models.py --all-models --save-results
```

### 16.6 Copilot Integration

**Automatic Routing:** Copilot Chat reads AI_MODEL_ROUTING.md automatically

**User Override:** Developers can specify model in prompt:
```
"Use Claude 3.5 Sonnet to refactor this module..."
```

**Routing Hints in Code:**
```python
# @copilot-model: claude-3-5-sonnet
# Complex refactoring - use advanced reasoning
def refactor_complex_logic():
    pass
```

### 16.7 Cost Monitoring

**Track Monthly Costs:**
```bash
# View model usage stats
./tools/model-usage-stats.py --month 2025-12

# Output:
# GPT-4 Turbo: 1.2M tokens ($12.00)
# Claude 3.5 Sonnet: 800K tokens ($2.40)
# o1: 200K tokens ($3.00)
# Total: $17.40
```

**Cost Alerts:** Set up alerts for unusual usage:
- >$50/day → Alert
- >$500/month → Review required

### 16.8 Best Practices

**DO:**
- ✅ Start with cheapest model that can do the task
- ✅ Escalate if first attempt fails
- ✅ Use routing table in AI_MODEL_ROUTING.md § 3
- ✅ Check for updates weekly
- ✅ Benchmark new models before adopting
- ✅ Track costs and optimize

**DON'T:**
- ❌ Use expensive models for simple tasks
- ❌ Ignore routing guidance
- ❌ Forget to update after major releases
- ❌ Skip benchmarking
- ❌ Use deprecated models

### 16.9 Validation Checklist

**Before updating routing:**
- [ ] New model benchmarked on standard tasks
- [ ] Performance score calculated (0-100)
- [ ] Cost comparison with current models
- [ ] Routing table updated
- [ ] AI_MODEL_ROUTING.md updated
- [ ] copilot-instructions.md synced
- [ ] Changes reviewed by team
- [ ] PR merged and deployed

**Monthly review:**
- [ ] Check for new model releases
- [ ] Review usage statistics
- [ ] Analyze cost trends
- [ ] Update benchmarks if needed
- [ ] Optimize routing decisions

---

## 17. CACHING IMPLEMENTATION STANDARDS

### 17.1 Overview

**Purpose:** Enable intelligent caching to optimize repeated workflows with similar media.

**Architecture:** 5-layer caching system with ML-based optimization

**Reference:** See `docs/technical/caching-ml-optimization.md` for complete architecture

### 17.2 Cache Layers

**All stages SHOULD implement caching where appropriate:**

#### Layer 1: Model Weights Cache (Global)
```python
# Location: {cache_dir}/models/
# Automatically managed by model loading utilities
# No stage-specific implementation needed
```

#### Layer 2: Audio Fingerprint Cache
```python
# Stage: 01_demux
from shared.cache_manager import CacheManager

cache = CacheManager(job_dir)
audio_hash = cache.compute_audio_fingerprint(input_file)

# Check if already processed
if cache.has_fingerprint(audio_hash):
    cached_info = cache.get_fingerprint(audio_hash)
    logger.info(f"Using cached audio info: {cached_info}")
    return cached_info

# Process and cache
audio_info = extract_audio(input_file)
cache.store_fingerprint(audio_hash, audio_info)
```

#### Layer 3: ASR Results Cache (Quality-Aware)
```python
# Stage: 06_whisperx_asr
from shared.cache_manager import CacheManager

cache = CacheManager(job_dir)
cache_key = cache.compute_asr_cache_key(
    audio_file=audio_path,
    model_version=model_version,
    language=language,
    config_params=relevant_config
)

# Check cache
if cache.has_asr_result(cache_key) and not no_cache:
    logger.info("Using cached ASR results")
    return cache.get_asr_result(cache_key)

# Process and cache
result = run_asr(audio_path, model_version, language)
cache.store_asr_result(cache_key, result)
```

#### Layer 4: Translation Cache (Contextual)
```python
# Stage: 08_translate
from shared.cache_manager import CacheManager

cache = CacheManager(job_dir)

for segment in segments:
    cache_key = cache.compute_translation_cache_key(
        source_text=segment['text'],
        source_lang=source_lang,
        target_lang=target_lang,
        glossary_hash=glossary_hash,
        context=segment.get('context')
    )
    
    # Check exact match
    if cache.has_translation(cache_key):
        segment['translation'] = cache.get_translation(cache_key)
        continue
    
    # Check similar segments (>80% similarity)
    similar = cache.find_similar_translation(segment['text'], threshold=0.80)
    if similar:
        # Adjust and use
        segment['translation'] = adjust_translation(similar, segment)
    else:
        # Fresh translation
        segment['translation'] = translate(segment['text'])
        cache.store_translation(cache_key, segment['translation'])
```

#### Layer 5: Glossary Learning Cache
```python
# Stage: 03_glossary_load
from shared.cache_manager import CacheManager

cache = CacheManager(job_dir)
movie_id = get_movie_id_from_tmdb()

# Load learned terms from previous processing
learned_terms = cache.get_learned_glossary(movie_id)
if learned_terms:
    logger.info(f"Loaded {len(learned_terms)} learned terms")
    glossary.merge(learned_terms)

# After processing, update learned terms
new_terms = extract_new_terms(asr_result)
cache.update_learned_glossary(movie_id, new_terms)
```

### 17.3 Cache Configuration

**Required in config/.env.pipeline:**
```bash
# Caching Configuration (see § 4 for parameter standards)
ENABLE_CACHING=true                          # Master switch
CACHE_DIR=~/.cp-whisperx/cache              # Cache location
CACHE_MAX_SIZE_GB=50                        # Total cache size limit
CACHE_ASR_RESULTS=true                      # Cache ASR outputs
CACHE_TRANSLATIONS=true                     # Cache translations
CACHE_AUDIO_FINGERPRINTS=true              # Cache audio analysis
CACHE_TTL_DAYS=90                          # Cache expiration
CACHE_CLEANUP_ON_START=false               # Auto-cleanup old cache

# ML Optimization (see § 18)
ENABLE_ML_OPTIMIZATION=true                 # Enable ML predictions
ML_MODEL_SELECTION=adaptive                 # adaptive|fixed
ML_QUALITY_PREDICTION=true                  # Predict optimal settings
ML_LEARNING_FROM_HISTORY=true              # Learn from past jobs

# Performance Tuning
SIMILAR_CONTENT_THRESHOLD=0.80             # Similarity reuse threshold
GLOSSARY_LEARNING_ENABLED=true             # Learn terms over time
TRANSLATION_MEMORY_ENABLED=true            # Build translation memory
```

### 17.4 Cache Invalidation Rules

**Cache MUST be invalidated when:**
- Model version changes
- Configuration parameters affecting output change
- User explicitly requests fresh processing (`--no-cache` flag)
- Cache entry exceeds TTL (CACHE_TTL_DAYS)
- Cache corruption detected (checksum mismatch)

**Implementation:**
```python
def should_invalidate_cache(cache_entry: dict, current_config: dict) -> bool:
    """
    Determine if cache entry should be invalidated.
    
    Args:
        cache_entry: Cached data with metadata
        current_config: Current job configuration
        
    Returns:
        True if cache should be invalidated
    """
    # Check TTL
    if is_expired(cache_entry['timestamp'], current_config['CACHE_TTL_DAYS']):
        logger.info("Cache entry expired")
        return True
    
    # Check model version
    if cache_entry['model_version'] != current_config['model_version']:
        logger.info("Model version changed, invalidating cache")
        return True
    
    # Check relevant config parameters
    if config_params_changed(cache_entry['config'], current_config):
        logger.info("Configuration changed, invalidating cache")
        return True
    
    # Check checksum
    if not verify_checksum(cache_entry):
        logger.warning("Cache checksum mismatch, invalidating")
        return True
    
    return False
```

### 17.5 Cache Management Tools

**Required tools in tools/cache-manager.sh:**
```bash
#!/usr/bin/env bash

# View cache statistics
./tools/cache-manager.sh --stats
# Output:
#   Total cache size: 12.3 GB / 50 GB (24.6%)
#   ASR results: 450 entries, 8.2 GB
#   Translations: 1,234 entries, 2.1 GB
#   Audio fingerprints: 89 entries, 45 MB
#   Glossary learned: 34 movies, 1.8 GB
#   Cache hit rate (last 30 days): 73%

# Clear specific cache type
./tools/cache-manager.sh --clear asr

# Clear old cache (>90 days)
./tools/cache-manager.sh --cleanup

# Clear all cache
./tools/cache-manager.sh --clear all

# Validate cache integrity
./tools/cache-manager.sh --validate

# Export cache for sharing
./tools/cache-manager.sh --export cache-backup-20251203.tar.gz

# Import cache
./tools/cache-manager.sh --import cache-backup-20251203.tar.gz
```

### 17.6 Testing Requirements

**Cache functionality MUST be tested:**

```python
# tests/test_caching.py

def test_cache_identical_media():
    """Test cache hit on identical media processing."""
    # First run
    result1 = process_with_cache(test_media)
    assert result1.cache_hit is False
    first_time = result1.processing_time
    
    # Second run
    result2 = process_with_cache(test_media)
    assert result2.cache_hit is True
    assert result2.processing_time < first_time * 0.1  # 90% faster

def test_cache_invalidation_on_config_change():
    """Test cache invalidation when config changes."""
    result1 = process_with_cache(test_media, config={'model': 'large-v2'})
    assert result1.cache_hit is False
    
    result2 = process_with_cache(test_media, config={'model': 'large-v3'})
    assert result2.cache_hit is False  # Config changed, cache invalidated

def test_cache_no_cache_flag():
    """Test --no-cache flag forces fresh processing."""
    result1 = process_with_cache(test_media)
    result2 = process_with_cache(test_media, no_cache=True)
    assert result2.cache_hit is False  # Forced fresh processing
```

---

## 18. ML OPTIMIZATION INTEGRATION

### 18.1 Overview

**Purpose:** Use machine learning to adaptively optimize processing based on media characteristics and historical data.

**Components:**
1. Adaptive Quality Prediction
2. Context Learning from History
3. Similarity-Based Optimization

**Reference:** See `docs/technical/caching-ml-optimization.md` for algorithms

### 18.2 Adaptive Quality Prediction

**Lightweight ML model predicts optimal processing parameters.**

**Implementation in 01_demux stage:**
```python
from shared.ml_optimizer import MLOptimizer

def run_stage(job_dir: Path, stage_name: str = "01_demux") -> int:
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    config = load_config(job_dir)
    
    # Extract audio characteristics
    audio_info = analyze_audio(input_file)
    
    # ML prediction for optimal settings
    if config.get('ENABLE_ML_OPTIMIZATION', 'true').lower() == 'true':
        optimizer = MLOptimizer(job_dir)
        predictions = optimizer.predict_optimal_settings(audio_info)
        
        logger.info(f"ML Predictions: {predictions}")
        # predictions = {
        #     'optimal_model': 'medium',  # Use medium model for this quality
        #     'source_separation_needed': False,  # Clean audio
        #     'expected_confidence': 0.92,
        #     'estimated_time_minutes': 4.2
        # }
        
        # Update job config with predictions
        update_job_config(job_dir, predictions)
```

**ML Model Training:**
```python
# tools/train-ml-optimizer.py

from shared.ml_optimizer import MLOptimizer
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

def train_optimizer():
    """Train ML optimizer from historical job data."""
    # Load historical data
    jobs_df = load_historical_jobs()
    
    # Features: audio characteristics
    features = [
        'snr_db',           # Signal-to-noise ratio
        'sample_rate',      # Audio sample rate
        'duration_sec',     # Duration
        'speech_ratio',     # Speech vs. silence ratio
        'background_noise', # Noise level
        'language'          # Detected language
    ]
    
    # Labels: optimal settings
    labels = {
        'model_size': ['base', 'small', 'medium', 'large'],
        'source_sep_needed': [True, False]
    }
    
    # Train classifiers
    model_clf = RandomForestClassifier()
    model_clf.fit(jobs_df[features], jobs_df['optimal_model'])
    
    source_sep_clf = RandomForestClassifier()
    source_sep_clf.fit(jobs_df[features], jobs_df['source_sep_needed'])
    
    # Save models
    optimizer = MLOptimizer()
    optimizer.save_models(model_clf, source_sep_clf)
    
    print("ML optimizer trained successfully")
```

### 18.3 Context Learning from History

**Learn from previous jobs to improve context awareness.**

**Character Name Recognition:**
```python
# Stage: 03_glossary_load

from shared.ml_optimizer import MLOptimizer

def run_stage(job_dir: Path, stage_name: str = "03_glossary_load") -> int:
    optimizer = MLOptimizer(job_dir)
    
    # Get movie ID from TMDB stage
    movie_id = read_tmdb_metadata(job_dir)
    
    # Load learned character names from previous processing
    learned_names = optimizer.get_learned_character_names(movie_id)
    if learned_names:
        logger.info(f"Loaded {len(learned_names)} learned character names")
        for name, info in learned_names.items():
            glossary.add_term(
                term=name,
                context=info['contexts'],
                frequency=info['frequency'],
                speakers=info['speakers']
            )
```

**Cultural Pattern Learning:**
```python
# Stage: 08_translate

from shared.ml_optimizer import MLOptimizer

def translate_segment(segment: dict, src_lang: str, tgt_lang: str) -> dict:
    optimizer = MLOptimizer(job_dir)
    
    # Check for learned cultural patterns
    cultural_patterns = optimizer.get_cultural_patterns(src_lang, tgt_lang)
    
    # Apply patterns to translation
    for pattern in cultural_patterns:
        if pattern['source_phrase'] in segment['text']:
            segment['cultural_context'] = pattern['translation_context']
            segment['alternatives'] = pattern['alternatives']
    
    # Translate with cultural context
    translation = translate_with_context(segment, cultural_patterns)
    
    # Update learning
    optimizer.record_translation(
        source=segment['text'],
        target=translation,
        context=segment.get('cultural_context'),
        confidence=segment.get('confidence', 0.0)
    )
    
    return translation
```

### 18.4 Similarity-Based Optimization

**Detect similar media and reuse processing decisions.**

**Implementation:**
```python
from shared.ml_optimizer import MLOptimizer

def run_stage(job_dir: Path, stage_name: str) -> int:
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    config = load_config(job_dir)
    
    optimizer = MLOptimizer(job_dir)
    
    # Compute similarity with previous jobs
    similarity_results = optimizer.find_similar_jobs(
        audio_fingerprint=current_fingerprint,
        language=detected_language,
        duration=duration,
        genre=genre
    )
    
    if similarity_results:
        best_match = similarity_results[0]
        similarity_score = best_match['similarity']
        
        if similarity_score > 0.95:
            logger.info(f"Nearly identical media detected (sim={similarity_score:.2f})")
            # Reuse full pipeline config
            reuse_full_config(best_match['job_id'])
            
        elif similarity_score > 0.80:
            logger.info(f"Similar content detected (sim={similarity_score:.2f})")
            # Reuse glossary and model selection, fresh ASR
            reuse_glossary(best_match['job_id'])
            reuse_model_selection(best_match['job_id'])
            
        elif similarity_score > 0.60:
            logger.info(f"Similar genre/language (sim={similarity_score:.2f})")
            # Suggest related glossaries
            suggest_related_glossaries(best_match['job_id'])
```

### 18.5 Testing Requirements

**ML optimization MUST be tested:**

```python
# tests/test_ml_optimization.py

def test_adaptive_quality_prediction():
    """Test ML model predicts optimal settings."""
    optimizer = MLOptimizer()
    
    # Clean audio should predict smaller model
    clean_audio = {
        'snr_db': 45,
        'background_noise': 0.1,
        'speech_ratio': 0.85
    }
    predictions = optimizer.predict_optimal_settings(clean_audio)
    assert predictions['optimal_model'] in ['base', 'small', 'medium']
    assert predictions['source_separation_needed'] is False
    
    # Noisy audio should predict larger model + source separation
    noisy_audio = {
        'snr_db': 15,
        'background_noise': 0.7,
        'speech_ratio': 0.45
    }
    predictions = optimizer.predict_optimal_settings(noisy_audio)
    assert predictions['optimal_model'] in ['medium', 'large']
    assert predictions['source_separation_needed'] is True

def test_similarity_detection():
    """Test similar media detection."""
    optimizer = MLOptimizer()
    
    # Process first job
    job1_id = process_job(test_media)
    
    # Process identical media
    similar_jobs = optimizer.find_similar_jobs(
        audio_fingerprint=compute_fingerprint(test_media)
    )
    
    assert len(similar_jobs) > 0
    assert similar_jobs[0]['job_id'] == job1_id
    assert similar_jobs[0]['similarity'] > 0.95
```

---

## 19. TEST MEDIA USAGE IN DEVELOPMENT

### 19.1 Standard Test Samples

**ALL development and testing MUST use standardized test media.**

**Sample 1: English Technical Content**
- File: `in/Energy Demand in AI.mp4`
- Purpose: Transcribe and Translate workflows
- Language: English
- Type: Technical/Educational
- Duration: ~2-5 minutes

**Sample 2: Hinglish Bollywood Content**
- File: `in/test_clips/jaane_tu_test_clip.mp4`
- Purpose: Subtitle, Transcribe, Translate workflows
- Language: Hindi/Hinglish
- Type: Entertainment
- Duration: ~1-3 minutes

**Reference:** See `docs/user-guide/workflows.md` for complete sample documentation

### 19.2 Quality Baselines

**All test runs MUST validate against quality baselines:**

| Sample | Workflow | Metric | Target | Validation |
|--------|----------|--------|--------|------------|
| Sample 1 | Transcribe | ASR WER | ≤5% | Automated |
| Sample 1 | Translate | BLEU Score | ≥90% | Automated |
| Sample 2 | Subtitle | Subtitle Quality | ≥88% | Human + Auto |
| Sample 2 | Subtitle | Context Preservation | ≥80% | Human evaluation |
| Sample 2 | Subtitle | Glossary Application | 100% | Automated |
| Both | All | Subtitle Timing | ±200ms | Automated |

### 19.3 Test Media Index

**Create and maintain:** `in/test_media_index.json`

```json
{
  "test_samples": [
    {
      "id": "sample_01",
      "file": "Energy Demand in AI.mp4",
      "language": "en",
      "type": "technical",
      "duration_estimate": "2-5 min",
      "workflows": ["transcribe", "translate"],
      "quality_baseline": {
        "asr_accuracy": 0.95,
        "translation_fluency": 0.90
      }
    },
    {
      "id": "sample_02",
      "file": "test_clips/jaane_tu_test_clip.mp4",
      "language": "hi-Hinglish",
      "type": "entertainment",
      "duration_estimate": "1-3 min",
      "workflows": ["subtitle", "transcribe", "translate"],
      "quality_baseline": {
        "asr_accuracy": 0.85,
        "subtitle_quality": 0.88,
        "context_awareness": 0.80
      }
    }
  ]
}
```

### 19.4 Development Workflow with Test Media

**When developing new features:**

```bash
# 1. Develop feature
# 2. Test with Sample 1 (English)
./prepare-job.sh --media "in/Energy Demand in AI.mp4" --workflow transcribe --source-language en
./run-pipeline.sh --job-dir out/$(latest_job)

# 3. Validate quality
python3 tests/validate-quality.py --job-dir out/$(latest_job) --sample sample_01

# 4. Test with Sample 2 (Hinglish)
./prepare-job.sh --media "in/test_clips/jaane_tu_test_clip.mp4" --workflow subtitle \
  --source-language hi --target-languages en,gu,ta
./run-pipeline.sh --job-dir out/$(latest_job)

# 5. Validate quality
python3 tests/validate-quality.py --job-dir out/$(latest_job) --sample sample_02

# 6. Run full test suite
pytest tests/
```

### 19.5 CI/CD Integration

**GitHub Actions MUST test with standard media:**

```yaml
# .github/workflows/tests.yml

name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup test media
        run: |
          # Download or link to standard test media
          ./tools/setup-test-media.sh
      
      - name: Run tests with Sample 1
        run: |
          ./prepare-job.sh --media "in/Energy Demand in AI.mp4" \
            --workflow transcribe --source-language en
          ./run-pipeline.sh --job-dir out/$(ls -t out/*/*/*/*/ | head -1)
          python3 tests/validate-quality.py --sample sample_01
      
      - name: Run tests with Sample 2
        run: |
          ./prepare-job.sh --media "in/test_clips/jaane_tu_test_clip.mp4" \
            --workflow subtitle --source-language hi --target-languages en,gu
          ./run-pipeline.sh --job-dir out/$(ls -t out/*/*/*/*/ | head -1)
          python3 tests/validate-quality.py --sample sample_02
      
      - name: Validate quality baselines
        run: pytest tests/test_quality_baselines.py
```

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-15 | Initial version | Team |
| 2.0 | 2025-11-26 | Added compliance baseline | Team |
| 3.0 | 2025-11-27 | **Unified standards + best practices** | Team |
|  |  | - Integrated compliance findings |  |
|  |  | - Added CI/CD standards |  |
|  |  | - Added observability section |  |
|  |  | - Added disaster recovery |  |
|  |  | - Added performance standards |  |
|  |  | - Enhanced testing guidelines |  |
|  |  | - Added type hints enforcement |  |
| 4.0 | 2025-12-02 | **100% compliance achieved** | Team |
|  |  | - All print() statements converted to logger |  |
|  |  | - All imports organized |  |
|  |  | - Type hints and docstrings added |  |
| 5.0 | 2025-12-03 | **Testing infrastructure + workflows** | Team |
|  |  | - Standard test media samples |  |
|  |  | - Core workflows documented |  |
|  |  | - Context-aware processing |  |
|  |  | - Caching & ML optimization |  |
| 6.0 | 2025-12-03 | **AI model routing automation** | Team |
|  |  | - Automated model update system |  |
|  |  | - Model registry and tracking |  |
|  |  | - GitHub Actions integration |  |
|  |  | - Cost monitoring and optimization |  |
|  |  | - Routing decision automation |  |

---

**Document Status:** ACTIVE  
**Last Updated:** December 3, 2025  
**Compliance Target:** 80% minimum (tracked quarterly)  
**Next Review:** March 2026

---

**All development MUST follow these standards. Non-compliance will be flagged in code review.**
