# CP-WhisperX-App - Complete Project Documentation

**Version:** 2.0.0  
**Last Updated:** 2025-11-19  
**Status:** Production Ready

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Multi-Environment System](#multi-environment-system)
4. [Workflows](#workflows)
5. [Installation](#installation)
6. [Usage](#usage)
7. [Logging Standards](#logging-standards)
8. [Development](#development)
9. [Troubleshooting](#troubleshooting)

---

## Overview

CP-WhisperX-App is a comprehensive audio/video processing pipeline that combines:
- **WhisperX**: State-of-the-art speech recognition with word-level timestamps
- **IndicTrans2**: Advanced Indian language translation
- **Multi-language subtitling**: Generate subtitles in multiple languages simultaneously

### Key Features

✅ **Multi-Environment Architecture**
- Isolated Python environments resolve dependency conflicts
- Automatic environment switching per pipeline stage
- No manual activation required

✅ **Three Workflows**
- **Transcribe**: Audio → Text with timestamps
- **Translate**: Text → Translated text
- **Subtitle**: Complete pipeline with soft-embedded subtitles

✅ **Multi-Language Support**
- Source: 23+ Indian languages (Hindi, Tamil, Telugu, Bengali, etc.)
- Target: English + up to 5 Indian languages simultaneously
- Automatic subtitle generation and video muxing

✅ **Cross-Platform**
- Bash scripts for Linux/macOS
- PowerShell scripts for Windows (coming soon)
- Consistent logging across all platforms

---

## Architecture

### System Components

```
cp-whisperx-app/
├── venv/whisperx/              # WhisperX environment (torch 2.0, numpy <2.1)
├── venv/indictrans2/           # IndicTrans2 environment (torch 2.5+, numpy 2.1+)
├── venv/common/                # Utilities environment (no ML dependencies)
├── config/
│   ├── hardware_cache.json      # Environment configuration
│   └── .env.pipeline            # Pipeline configuration template
├── scripts/
│   ├── prepare-job.py           # Job preparation (Python)
│   ├── run-pipeline.py          # Pipeline orchestrator (Python)
│   ├── common-logging.sh        # Bash logging module
│   ├── common-logging.ps1       # PowerShell logging module
│   └── indictrans2_translator.py # Translation engine
├── shared/
│   ├── environment_manager.py   # Environment manager API
│   └── logger.py                # Python logging module
├── bootstrap.sh                 # Environment setup
├── prepare-job.sh               # Job preparation (Bash)
├── run-pipeline.sh              # Pipeline execution (Bash)
├── in/                          # Input media files
├── out/                         # Output directory (organized by date/user/job)
└── logs/                        # Centralized logs
```

### Data Flow

```
Input Media → Prepare Job → Run Pipeline → Output Media + Subtitles
                   ↓              ↓
              job.json       Environment
                          Auto-Switching
```

---

## Multi-Environment System

### The Problem

WhisperX and IndicTrans2 have **conflicting dependencies**:

| Component | PyTorch | NumPy |
|-----------|---------|-------|
| WhisperX | ~2.0.0 | <2.1 |
| IndicTrans2 | >=2.5.0 | >=2.1 |

**Solution:** Three isolated virtual environments

### Environments

#### 1. WhisperX Environment (`venv/whisperx`)
**Purpose:** Speech-to-text transcription  
**Dependencies:**
- whisperx 3.1.1
- torch ~2.0.0
- numpy <2.1
- mlx-whisper (Apple Silicon)

**Stages:**
- `demux` - Audio extraction
- `asr` - Automatic speech recognition
- `alignment` - Word-level timestamps
- `export_transcript` - Export formatted transcripts

#### 2. IndicTrans2 Environment (`venv/indictrans2`)
**Purpose:** Indian language translation  
**Dependencies:**
- IndicTransToolkit latest
- torch >=2.5.0
- numpy >=2.1
- transformers >=4.51.0

**Stages:**
- `load_transcript` - Load source transcripts
- `indictrans2_translation_*` - Translation to target languages

#### 3. Common Environment (`venv/common`)
**Purpose:** Lightweight utilities  
**Dependencies:**
- ffmpeg-python
- pydantic
- python-dotenv

**Stages:**
- `subtitle_generation_*` - SRT file generation
- `mux` - Video muxing with soft subtitles

### Environment Switching

**Automatic and Transparent:**

```
Stage: demux
  → Activate venv/whisperx
  → Run audio extraction
  → Deactivate

Stage: asr
  → Already in whisperx
  → Run transcription

Stage: indictrans2_translation_en
  → Switch to venv/indictrans2
  → Run translation

Stage: subtitle_generation_en
  → Switch to venv/common
  → Generate SRT file

Stage: mux
  → Already in common
  → Embed subtitles in video
```

---

## Workflows

### 1. Transcribe Workflow

**Purpose:** Convert audio to text with timestamps

```bash
./prepare-job.sh movie.mp4 --transcribe -s hi
./run-pipeline.sh -j <job-id>
```

**Stages:**
1. **Demux** - Extract audio from video
2. **ASR** - Transcribe using WhisperX
3. **Alignment** - Generate word-level timestamps
4. **Export** - Save formatted transcript

**Output:**
- `transcripts/segments.json` - Timestamped segments
- `transcripts/transcript.txt` - Plain text transcript
- `transcripts/transcript.srt` - SRT format

**Environment:** `whisperx` only

### 2. Translate Workflow

**Purpose:** Translate text to target language(s)

```bash
./prepare-job.sh movie.mp4 --translate -s hi -t en
./run-pipeline.sh -j <job-id>
```

**Stages:**
1. **Load Transcript** - Load source segments
2. **Translation** - Translate using IndicTrans2
3. **Subtitle Generation** - Create SRT files

**Output:**
- `transcripts/segments_translated_en.json` - Translated segments
- `subtitles/movie_en.srt` - English subtitles

**Environments:** `indictrans2`, `common`

### 3. Subtitle Workflow

**Purpose:** Complete pipeline with multiple subtitle tracks

```bash
./prepare-job.sh movie.mp4 --subtitle -s hi -t en,gu,ta \
  --start-time 00:06:00 --end-time 00:08:30
./run-pipeline.sh -j <job-id>
```

**Stages:**
1. **Demux** - Extract audio
2. **ASR** - Transcribe
3. **Translation (×N)** - Translate to N languages
4. **Subtitle Generation (×N+1)** - Generate source + N target SRTs
5. **Mux** - Soft-embed all subtitles in video

**Output:**
- `transcripts/` - All transcripts and translations
- `subtitles/` - Source + target SRT files
- `media/movie_subtitled.mp4` - Video with embedded subtitles

**Environments:** `whisperx`, `indictrans2`, `common`

**Media Processing:**
- **Full Mode**: Process entire video
- **Clip Mode**: Process specific time range (with `--start-time` and `--end-time`)

---

## Installation

### Prerequisites

- Python 3.10, 3.11, or 3.12
- FFmpeg
- jq (for JSON processing)
- Git

**macOS:**
```bash
brew install ffmpeg jq python@3.11
```

**Linux:**
```bash
sudo apt install ffmpeg jq python3.11 python3.11-venv
```

### Setup

**1. Clone Repository**
```bash
git clone <repository-url>
cd cp-whisperx-app
```

**2. Create Environments**
```bash
./bootstrap.sh
```

This creates three environments:
- `venv/whisperx` - WhisperX (torch 2.0, numpy <2.1)
- `venv/indictrans2` - IndicTrans2 (torch 2.5+, numpy 2.1+)
- `venv/common` - Utilities (no ML)

**3. Verify Installation**
```bash
./bootstrap.sh --check
```

Expected output:
```
✓ whisperx (Python 3.11.x)
✓ indictrans2 (Python 3.11.x)
✓ common (Python 3.11.x)
```

---

## Usage

### Basic Workflow

**Step 1: Prepare Media**

Place input files in `in/` directory:
```bash
cp /path/to/movie.mp4 in/
```

**Step 2: Prepare Job**

```bash
# Transcribe only
./prepare-job.sh in/movie.mp4 --transcribe -s hi

# Translate
./prepare-job.sh in/movie.mp4 --translate -s hi -t en

# Full subtitle workflow
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en,gu,ta

# With time range
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en \
  --start-time 00:06:00 --end-time 00:08:30
```

**Step 3: Run Pipeline**

```bash
./run-pipeline.sh -j <job-id>
```

**Step 4: Check Output**

```bash
# Output structure
out/YYYY/MM/DD/username/job-number/
├── media/
│   ├── audio.wav          # Extracted audio
│   └── movie_subtitled.mp4  # Final video with subtitles
├── transcripts/
│   ├── segments.json      # Source segments
│   ├── segments_translated_en.json
│   ├── segments_translated_gu.json
│   └── transcript.txt
├── subtitles/
│   ├── movie_hi.srt       # Source subtitles
│   ├── movie_en.srt       # English subtitles
│   ├── movie_gu.srt       # Gujarati subtitles
│   └── movie_ta.srt       # Tamil subtitles
├── logs/                  # Pipeline logs
├── job.json              # Job configuration
└── manifest.json         # Stage tracking
```

### Advanced Options

**Debug Mode:**
```bash
./prepare-job.sh movie.mp4 --subtitle -s hi -t en --debug
```
- Enables verbose logging
- Keeps intermediate files
- Shows detailed progress

**Resume Failed Jobs:**
```bash
./run-pipeline.sh -j <job-id> --resume
```

**Check Job Status:**
```bash
./run-pipeline.sh -j <job-id> --status
```

---

## Logging Standards

### Logging Modules

**Bash:** `scripts/common-logging.sh`
**PowerShell:** `scripts/common-logging.ps1`
**Python:** `shared/logger.py`

### Log Levels

| Level | Function | Usage |
|-------|----------|-------|
| DEBUG | `log_debug` / `Write-LogDebug` | Detailed diagnostics |
| INFO | `log_info` / `Write-LogInfo` | General information |
| WARN | `log_warn` / `Write-LogWarn` | Warnings |
| ERROR | `log_error` / `Write-LogError` | Errors |
| SUCCESS | `log_success` / `Write-LogSuccess` | Success messages |
| FAILURE | `log_failure` / `Write-LogFailure` | Failure messages |

### Log Format

**Format:** `[YYYY-MM-DD HH:MM:SS] [LEVEL] message`  
**Example:** `[2025-11-19 13:45:23] [INFO] Starting process...`

### Log Files

**Location:** `logs/` directory  
**Format:** `YYYYMMDD-HHMMSS-scriptname.log`  
**Example:** `20251119-134523-prepare-job.log`

**Auto-Creation:**
- All scripts automatically create log files
- No manual configuration required
- Organized by timestamp

### Environment Variables

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Custom log file
export LOG_FILE=/path/to/custom.log
```

---

## Development

### Project Structure

**Core Scripts:**
- `prepare-job.sh` / `prepare-job.py` - Job preparation
- `run-pipeline.sh` / `run-pipeline.py` - Pipeline execution
- `bootstrap.sh` - Environment setup

**Supporting Scripts:**
- `indictrans2_translator.py` - Translation engine
- `environment_manager.py` - Environment management
- `common-logging.sh` - Bash logging
- `common-logging.ps1` - PowerShell logging

**Configuration:**
- `config/hardware_cache.json` - Environment definitions
- `config/.env.pipeline` - Pipeline configuration
- `requirements-*.txt` - Dependency specifications

### Adding a New Environment

**1. Update hardware_cache.json:**
```json
{
  "environments": {
    "my_new_env": {
      "name": "my_new_env",
      "path": ".venv-my_new_env",
      "stages": ["my_stage"],
      "requirements_file": "requirements-my_new_env.txt"
    }
  },
  "stage_to_environment_mapping": {
    "my_stage": "my_new_env"
  }
}
```

**2. Create requirements file:**
```bash
cat > requirements-my_new_env.txt << EOF
# My New Environment Dependencies
my-package>=1.0.0
EOF
```

**3. Install:**
```bash
./bootstrap.sh --env my_new_env
```

### Coding Standards

**Bash Scripts:**
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/common-logging.sh"

log_info "Starting process..."
```

**Python Scripts:**
```python
from shared.logger import PipelineLogger

logger = PipelineLogger(
    module_name="script_name",
    log_file=Path("logs/script.log"),
    log_level="INFO"
)

logger.info("Starting process...")
```

---

## Troubleshooting

### Environment Issues

**Problem:** Missing environment
```
❌ Error: Missing required environments: indictrans2
```

**Solution:**
```bash
./bootstrap.sh --env indictrans2
```

**Problem:** Dependency conflicts
```
WARNING: whisperx 3.1.1 requires numpy<2.1...
```

**Solution:** Environments prevent this. If you see it, reinstall:
```bash
./bootstrap.sh --clean
./bootstrap.sh
```

### Pipeline Failures

**Problem:** Stage fails

**Solution:** Check logs:
```bash
# View specific stage log
tail -f out/.../logs/indictrans2_translation_en.log

# View main pipeline log
tail -f out/.../logs/pipeline.log
```

**Problem:** Translation quality issues

**Solution:** The IndicTransToolkit has known issues with certain text patterns. Consider:
```python
# In job config, disable toolkit:
use_toolkit=False
```

### Performance Issues

**Problem:** Slow transcription

**Solution:** Use MLX backend on Apple Silicon:
```bash
# Already enabled by default on macOS
# Check in logs for "Using MLX backend"
```

**Problem:** Out of memory

**Solution:** Process in clips:
```bash
./prepare-job.sh movie.mp4 --subtitle -s hi -t en \
  --start-time 00:00:00 --end-time 00:10:00
```

---

## Support

### Documentation

- **Multi-Environment Architecture:** `docs/MULTI_ENVIRONMENT_ARCHITECTURE.md`
- **Integration Guide:** `docs/MULTI_ENVIRONMENT_INTEGRATION.md`
- **Logging Standards:** `docs/LOGGING_STANDARDS.md`
- **Quick Reference:** `docs/MULTI_ENVIRONMENT_QUICK_REF.md`

### Common Commands

```bash
# Setup
./bootstrap.sh
./bootstrap.sh --check

# Workflows
./prepare-job.sh movie.mp4 --subtitle -s hi -t en
./run-pipeline.sh -j <job-id>

# Maintenance
./bootstrap.sh --clean
./bootstrap.sh --env whisperx

# Debugging
export LOG_LEVEL=DEBUG
./prepare-job.sh movie.mp4 --subtitle -s hi -t en --debug
```

### Getting Help

1. Check logs in `logs/` directory
2. Review documentation in `docs/`
3. Enable debug mode with `--debug`
4. Check GitHub issues

---

## License

See LICENSE file for details.

---

## Changelog

### Version 2.0.0 (2025-11-19)

**Major Changes:**
- ✅ Multi-environment architecture implemented
- ✅ Automatic environment switching
- ✅ Support for up to 5 target languages
- ✅ Standardized logging across all scripts
- ✅ Comprehensive documentation

**New Features:**
- Multi-language subtitle generation
- Soft subtitle embedding
- Clip processing support
- Debug mode
- Resume capability

**Improvements:**
- No more dependency conflicts
- Faster pipeline execution
- Better error handling
- Clear logging
- Cross-platform support (coming soon)

### Version 1.0.0 (2024-11-01)

**Initial Release:**
- Basic transcription workflow
- Single environment
- Limited language support

---

**Status:** Production Ready ✅  
**Last Updated:** 2025-11-19  
**Next:** PowerShell script parity
