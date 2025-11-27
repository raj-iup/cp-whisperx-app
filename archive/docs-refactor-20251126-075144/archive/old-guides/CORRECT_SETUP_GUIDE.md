# Correct Setup & Usage Guide

**Last Updated:** 2025-11-19  
**Status:** ✅ AUTHORITATIVE - Source of Truth

---

## ⚠️ IMPORTANT: Correct Information

This document provides the **CORRECT** setup instructions. Some older documentation may contain outdated information.

### Common Mistakes to Avoid

❌ **WRONG:** `pip install -r requirements.txt` then `./scripts/bootstrap.sh`  
✅ **RIGHT:** Just run `./bootstrap.sh` (it does everything)

❌ **WRONG:** `./scripts/bootstrap.sh`  
✅ **RIGHT:** `./bootstrap.sh` (run from project root)

❌ **WRONG:** Running scripts from `scripts/` directory  
✅ **RIGHT:** Run all commands from project root directory

---

## Correct Setup Instructions

### macOS / Linux

```bash
# 1. Clone repository
git clone <repository-url>
cd cp-whisperx-app

# 2. Run bootstrap (ONE command does everything)
./bootstrap.sh

# Bootstrap automatically:
#  - Creates .bollyenv virtual environment
#  - Installs ALL Python dependencies
#  - Installs MLX-Whisper (if Apple Silicon detected)
#  - Detects hardware and configures pipeline

# That's it! You're ready to use the pipeline.
```

#### Optional: Manual MLX Installation (Apple Silicon)

If bootstrap didn't install MLX, or you want to add it later:

```bash
# 1. Install MLX manually
./install-mlx.sh

# 2. IMPORTANT: Re-run bootstrap to detect MLX and update config
./bootstrap.sh

# Now MLX GPU acceleration is enabled!
```

**Note:** `install-mlx.sh` uses the **existing** `.bollyenv` virtual environment - it does NOT create a separate environment.

### Windows

```powershell
# 1. Clone repository  
git clone <repository-url>
cd cp-whisperx-app

# 2. Run bootstrap (ONE command does everything)
.\bootstrap.ps1

# That's it! You're ready to use the pipeline.
```

---

## What Bootstrap Does (Automatically)

When you run `./bootstrap.sh` or `.\bootstrap.ps1`, it:

1. ✅ Creates `.bollyenv` virtual environment
2. ✅ Installs **ALL** Python dependencies from `requirements.txt`
3. ✅ Detects your hardware (MPS/CUDA/CPU)
4. ✅ Downloads necessary ML models
5. ✅ Validates FFmpeg installation
6. ✅ Creates directory structure (`in/`, `out/`, `logs/`)
7. ✅ Generates hardware cache (`out/hardware_cache.json`)
8. ✅ Creates configuration templates

**You do NOT need to:**
- ❌ Manually create virtual environment
- ❌ Run `pip install -r requirements.txt`
- ❌ Manually download models
- ❌ Configure hardware settings

**Bootstrap handles EVERYTHING!**

---

## MLX Installation (Apple Silicon)

### How MLX Works

MLX provides **6-8x faster** transcription on Apple Silicon (M1/M2/M3) by using the Metal Performance Shaders (MPS) GPU framework.

### Virtual Environment

**IMPORTANT:** MLX uses the **SAME** `.bollyenv` virtual environment as the rest of the pipeline.

- ✅ **No separate environment needed**
- ✅ All packages coexist in `.bollyenv`
- ✅ No environment switching required

### Installation Options

#### Option 1: Automatic (Recommended)

```bash
./bootstrap.sh
```

Bootstrap automatically detects Apple Silicon and installs MLX-Whisper. **No additional steps needed!**

#### Option 2: Manual Installation

If bootstrap skipped MLX or you want to add it later:

```bash
# Step 1: Install MLX into existing .bollyenv
./install-mlx.sh

# Step 2: Re-run bootstrap to detect MLX and update config
./bootstrap.sh

# Done! MLX GPU acceleration is now enabled
```

**Why re-run bootstrap?**
Bootstrap updates `out/hardware_cache.json` with MPS/MLX detection. This file tells the pipeline to use GPU acceleration.

### Verification

After installation, verify MLX is working:

```bash
source .bollyenv/bin/activate
python -c "import mlx_whisper; print('✓ MLX-Whisper installed')"
```

Check hardware cache:
```bash
cat out/hardware_cache.json
# Should show: "gpu_type": "mps", "whisper_backend": "mlx"
```

---

## Script Locations & Usage

### User-Facing Scripts (Run from Project Root)

```
cp-whisperx-app/
├── bootstrap.sh              # Setup script (Bash)
├── bootstrap.ps1             # Setup script (PowerShell)
├── prepare-job.sh            # Job preparation (Bash)
├── prepare-job.ps1           # Job preparation (PowerShell)
├── run-pipeline.sh           # Pipeline runner (Bash)
├── run-pipeline.ps1          # Pipeline runner (PowerShell)
├── install-mlx.sh            # Optional: MLX for Apple Silicon
└── install-indictrans2.sh    # Optional: IndicTrans2 installation
```

**All these scripts are run from the project root directory.**

### Implementation Scripts (Called Automatically)

```
scripts/
├── bootstrap.sh              # Actual bootstrap implementation
├── bootstrap.ps1             # PowerShell bootstrap implementation
├── prepare-job.py            # Python job preparation logic
├── run-pipeline.py           # Python pipeline orchestrator
├── common-logging.sh         # Bash logging framework
├── common-logging.ps1        # PowerShell logging framework
└── [other Python scripts]    # Pipeline stages
```

**You should NOT run scripts from the `scripts/` directory directly.**

### Utility Modules (Used by Scripts)

```
shared/
├── logger.py                 # Python logging framework
├── manifest.py               # Job manifest management
├── job_manager.py            # Job directory management
└── [other utilities]         # Shared functions

tools/
├── rotate-logs.sh            # Log rotation (Bash)
├── rotate-logs.ps1           # Log rotation (PowerShell)
├── analyze-logs.py           # Log analyzer
└── validate-compliance.py    # Logging validator
```

---

## Correct Workflow Usage

### Transcribe Workflow

```bash
# macOS/Linux
./prepare-job.sh movie.mp4 --transcribe -s hi
./run-pipeline.sh -j <job-id>

# Windows
.\prepare-job.ps1 movie.mp4 -Transcribe -SourceLanguage hi
.\run-pipeline.ps1 -JobId <job-id>
```

### Translate Workflow

```bash
# macOS/Linux
./prepare-job.sh movie.mp4 --translate -s hi -t en
./run-pipeline.sh -j <job-id>

# Windows
.\prepare-job.ps1 movie.mp4 -Translate -SourceLanguage hi -TargetLanguage en
.\run-pipeline.ps1 -JobId <job-id>
```

### Subtitle Workflow

```bash
# macOS/Linux
./prepare-job.sh movie.mp4 --subtitle -s hi -t en
./run-pipeline.sh -j <job-id>

# Windows
.\prepare-job.ps1 movie.mp4 -Subtitle -SourceLanguage hi -TargetLanguage en
.\run-pipeline.ps1 -JobId <job-id>
```

---

## How Scripts Work Together

### Bootstrap Phase

```
User runs: ./bootstrap.sh
           │
           ├─> Root script: bootstrap.sh
           │   └─> (standalone, not a wrapper)
           │
           └─> Creates:
               ├─> .bollyenv/
               ├─> out/hardware_cache.json
               ├─> logs/
               └─> Configuration files
```

### Job Preparation Phase

```
User runs: ./prepare-job.sh movie.mp4 --transcribe -s hi
           │
           ├─> Root script: prepare-job.sh
           │   ├─> Validates arguments
           │   ├─> Loads common-logging.sh
           │   └─> Calls: python scripts/prepare-job.py
           │       │
           │       └─> Creates:
           │           ├─> out/YYYY/MM/DD/USER/ID/
           │           ├─> job.json
           │           ├─> manifest.json
           │           └─> .job-id.env
           │
           └─> Returns: job-YYYYMMDD-USER-ID
```

### Pipeline Execution Phase

```
User runs: ./run-pipeline.sh -j job-YYYYMMDD-USER-ID
           │
           ├─> Root script: run-pipeline.sh
           │   ├─> Finds job directory
           │   ├─> Loads common-logging.sh
           │   └─> Calls: python scripts/run-pipeline.py --job-dir <dir>
           │       │
           │       └─> Executes stages:
           │           ├─> demux (scripts/demux.py)
           │           ├─> asr (scripts/whisperx_asr.py)
           │           ├─> alignment
           │           └─> etc.
           │
           └─> Outputs to: out/YYYY/MM/DD/USER/ID/
               ├─> transcripts/
               ├─> subtitles/
               └─> logs/
```

---

## Troubleshooting

### "Virtual environment not found"

```bash
# Just re-run bootstrap
./bootstrap.sh        # macOS/Linux
.\bootstrap.ps1       # Windows
```

### "Python module not found"

```bash
# Re-run bootstrap (it reinstalls everything)
./bootstrap.sh        # macOS/Linux
.\bootstrap.ps1       # Windows
```

### "Command not found: prepare-job.sh"

**Problem:** You're not in the project root directory

**Solution:**
```bash
cd /path/to/cp-whisperx-app
./prepare-job.sh --help
```

### "No such file or directory: scripts/prepare-job.py"

**Problem:** You're running the script from the wrong directory

**Solution:** Always run scripts from the project root:
```bash
# Wrong:
cd scripts
../prepare-job.sh movie.mp4 --transcribe -s hi

# Right:
cd /path/to/cp-whisperx-app
./prepare-job.sh movie.mp4 --transcribe -s hi
```

---

## Directory Structure

```
cp-whisperx-app/           ← PROJECT ROOT (run all commands from here)
│
├── bootstrap.sh           ← Run this for setup (macOS/Linux)
├── bootstrap.ps1          ← Run this for setup (Windows)
├── prepare-job.sh         ← Job preparation (macOS/Linux)
├── prepare-job.ps1        ← Job preparation (Windows)
├── run-pipeline.sh        ← Pipeline runner (macOS/Linux)
├── run-pipeline.ps1       ← Pipeline runner (Windows)
│
├── scripts/               ← Implementation (called automatically)
│   ├── bootstrap.sh       ← Actual bootstrap logic
│   ├── bootstrap.ps1      ← PowerShell bootstrap
│   ├── prepare-job.py     ← Job prep Python logic
│   ├── run-pipeline.py    ← Pipeline orchestrator
│   └── [stage scripts]    ← Pipeline stages
│
├── shared/                ← Utilities (used by Python scripts)
│   ├── logger.py
│   ├── manifest.py
│   └── [other modules]
│
├── tools/                 ← Management tools
│   ├── rotate-logs.sh
│   ├── rotate-logs.ps1
│   └── analyze-logs.py
│
├── in/                    ← Input media files (created by bootstrap)
├── out/                   ← Output (transcripts, subtitles, logs)
├── logs/                  ← Script logs (created by bootstrap)
└── config/                ← Configuration files
```

---

## Quick Reference Card

### Setup (One-Time)

| Platform | Command |
|----------|---------|
| macOS | `./bootstrap.sh` |
| Linux | `./bootstrap.sh` |
| Windows | `.\bootstrap.ps1` |

### Transcribe

| Platform | Command |
|----------|---------|
| macOS/Linux | `./prepare-job.sh movie.mp4 --transcribe -s hi` |
| Windows | `.\prepare-job.ps1 movie.mp4 -Transcribe -SourceLanguage hi` |

### Run Pipeline

| Platform | Command |
|----------|---------|
| macOS/Linux | `./run-pipeline.sh -j <job-id>` |
| Windows | `.\run-pipeline.ps1 -JobId <job-id>` |

### Check Status

| Platform | Command |
|----------|---------|
| macOS/Linux | `./run-pipeline.sh -j <job-id> --status` |
| Windows | `.\run-pipeline.ps1 -JobId <job-id> -Status` |

---

## Summary

✅ **DO:**
- Run `./bootstrap.sh` or `.\bootstrap.ps1` from project root
- Run all commands from project root directory
- Trust bootstrap to handle all setup

❌ **DON'T:**
- Run `pip install -r requirements.txt` manually
- Run `./scripts/bootstrap.sh` (wrong path)
- Run scripts from subdirectories
- Manually download models or configure hardware

**Key Principle:** Bootstrap does **EVERYTHING**. Just run it once and you're ready!

---

**Last Updated:** 2025-11-19  
**Status:** ✅ Authoritative Guide  
**Version:** 1.1.0
