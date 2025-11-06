# prepare-job-venv Scripts Documentation

**Isolated Python environment for job preparation with automatic GPU detection**

---

## Overview

The `prepare-job-venv` scripts provide a complete, isolated workflow for job preparation:

1. **Create temporary Python virtual environment**
2. **Detect hardware** (CUDA/MPS/CPU)
3. **Install PyTorch** with matching GPU support
4. **Verify GPU detection** in PyTorch
5. **Run job preparation** with optimal settings
6. **Clean up** virtual environment automatically

These scripts solve the PyTorch GPU detection issue by ensuring the correct PyTorch version is installed in an isolated environment.

---

## Why Use These Scripts?

### Problem Solved

If you have:
- ✅ NVIDIA GPU with working drivers (`nvidia-smi` works)
- ❌ PyTorch CPU-only version installed
- ❌ `prepare-job.py` fails to detect GPU

**Solution:** These scripts create a fresh environment with the correct PyTorch version for your GPU.

### Benefits

- **Isolated environment**: Won't interfere with system Python or other projects
- **Automatic GPU detection**: CUDA version matched from `nvidia-smi`
- **Fallback to CPU**: If GPU setup fails, automatically uses CPU mode
- **Clean execution**: Virtual environment removed after completion
- **Logging compliance**: Uses same logging as other pipeline scripts

---

## Platform Support

| Platform | Script | Python Command |
|----------|--------|----------------|
| **Windows** | `prepare-job-venv.ps1` | `python` or `python3` |
| **Linux** | `prepare-job-venv.sh` | `python3` |
| **macOS** | `prepare-job-venv.sh` | `python3` |

---

## Usage

### Windows (PowerShell)

```powershell
# Basic usage
.\prepare-job-venv.ps1 movie.mp4

# Transcribe only
.\prepare-job-venv.ps1 movie.mp4 -Transcribe

# Process clip
.\prepare-job-venv.ps1 movie.mp4 -StartTime "00:10:00" -EndTime "00:15:00"

# Keep venv for debugging
.\prepare-job-venv.ps1 movie.mp4 -KeepVenv
```

### Linux/macOS (Bash)

```bash
# Basic usage
./prepare-job-venv.sh movie.mp4

# Transcribe only
./prepare-job-venv.sh movie.mp4 --transcribe

# Process clip
./prepare-job-venv.sh movie.mp4 --start-time 00:10:00 --end-time 00:15:00

# Keep venv for debugging
./prepare-job-venv.sh movie.mp4 --keep-venv
```

---

## Options

### Common Options (All Platforms)

| Option | Description | Example |
|--------|-------------|---------|
| `input_media` | Path to video/audio file (required) | `movie.mp4` |
| `--start-time` | Clip start time (HH:MM:SS) | `00:10:00` |
| `--end-time` | Clip end time (HH:MM:SS) | `00:15:00` |
| `--transcribe` | Transcribe-only workflow | - |
| `--subtitle-gen` | Full subtitle workflow (default) | - |
| `--keep-venv` | Keep virtual environment after completion | - |

### PowerShell-Specific Syntax

```powershell
-InputMedia "movie.mp4"    # Positional or named
-StartTime "00:10:00"      # Named parameter
-EndTime "00:15:00"        # Named parameter
-Transcribe                # Switch parameter
-KeepVenv                  # Switch parameter
```

### Bash-Specific Syntax

```bash
movie.mp4                  # Positional argument
--start-time 00:10:00      # Named argument
--end-time 00:15:00        # Named argument
--transcribe               # Flag
--keep-venv                # Flag
```

---

## Workflow Details

### Step 1: Python Validation

```
[INFO] Validating Python installation...
[INFO] Found: Python 3.11.5
[SUCCESS] Python version check passed
```

- Checks for Python 3.9+
- Validates version meets requirements
- Exits if Python not found or too old

### Step 2: Virtual Environment Creation

```
======================================================================
CREATING VIRTUAL ENVIRONMENT
======================================================================
[INFO] Location: .venv-prepare-job-temp
[INFO] Creating new venv...
[SUCCESS] Virtual environment created
[INFO] Activating virtual environment...
[SUCCESS] Virtual environment activated
```

- Creates temporary `.venv-prepare-job-temp` directory
- Activates virtual environment
- Isolated from system Python packages

### Step 3: Hardware Detection

```
======================================================================
HARDWARE DETECTION
======================================================================
[INFO] Detecting available acceleration hardware...
[INFO] NVIDIA GPU detected (nvidia-smi available)
[INFO] CUDA Version: 12.6
[SUCCESS] Device mode: CUDA
```

**Detection Logic:**

| Condition | Result |
|-----------|--------|
| `nvidia-smi` available + CUDA version detected | **CUDA mode** |
| macOS + Apple Silicon CPU | **MPS mode** |
| No GPU detected | **CPU mode** |

### Step 4: PyTorch Installation

```
======================================================================
INSTALLING PYTORCH
======================================================================
[INFO] Installing PyTorch with CUDA 12.6 support...
[INFO] PyTorch index: https://download.pytorch.org/whl/cu126
[SUCCESS] PyTorch installed successfully
```

**CUDA Version Mapping:**

| CUDA Version | PyTorch Index |
|--------------|---------------|
| 12.6+ | `cu126` |
| 12.4-12.5 | `cu124` |
| 12.1-12.3 | `cu121` |
| 11.x | `cu118` |

**Fallback Strategy:**
- If CUDA PyTorch install fails → Retry with CPU version
- If MPS PyTorch install fails → Fallback to CPU mode

### Step 5: PyTorch Verification

```
======================================================================
VERIFYING PYTORCH INSTALLATION
======================================================================
[INFO] Testing PyTorch GPU detection...
PyTorch version: 2.5.1+cu126
CUDA available: True
CUDA version: 12.6
GPU: NVIDIA GeForce GTX 750 Ti
GPU memory: 2.00 GB

[SUCCESS] PyTorch verification passed
```

- Tests `torch.cuda.is_available()` (CUDA)
- Tests `torch.backends.mps.is_available()` (MPS)
- Displays GPU name and memory
- Falls back to CPU if detection fails

### Step 6: Job Preparation

```
======================================================================
RUNNING JOB PREPARATION
======================================================================
[INFO] Workflow: SUBTITLE-GEN
[INFO] Native mode: ENABLED (using venv Python with CUDA)
[INFO] Input media: movie.mp4
[INFO] Executing: python scripts\prepare-job.py movie.mp4 --subtitle-gen --native

... (prepare-job.py output) ...

[SUCCESS] Job preparation completed successfully
```

- Runs `scripts/prepare-job.py` with detected device mode
- Always uses `--native` flag (direct Python execution)
- Full hardware detection and optimization (see [PREPARE_JOB_ARCHITECTURE.md](PREPARE_JOB_ARCHITECTURE.md))

### Step 7: Cleanup

```
======================================================================
CLEANING UP
======================================================================
[INFO] Removing virtual environment...
[SUCCESS] Virtual environment removed
```

**Default behavior:** Virtual environment is removed automatically

**Keep venv option:** Use `--keep-venv` to preserve for debugging
```bash
# Kept venv can be reactivated
source .venv-prepare-job-temp/bin/activate  # Linux/macOS
.\.venv-prepare-job-temp\Scripts\Activate.ps1  # Windows
```

---

## Examples

### Example 1: Windows with NVIDIA GPU

```powershell
PS> .\prepare-job-venv.ps1 "C:\Videos\movie.mp4"

======================================================================
CP-WHISPERX-APP JOB PREPARATION (VENV MODE)
======================================================================
[INFO] Creating isolated Python environment for job preparation...

[INFO] Validating Python installation...
[INFO] Found: Python 3.11.5
[SUCCESS] Python version check passed

======================================================================
CREATING VIRTUAL ENVIRONMENT
======================================================================
[INFO] Location: C:\...\cp-whisperx-app\.venv-prepare-job-temp
[INFO] Creating new venv...
[SUCCESS] Virtual environment created

======================================================================
HARDWARE DETECTION
======================================================================
[INFO] Detecting available acceleration hardware...
[INFO] NVIDIA GPU detected (nvidia-smi available)
[INFO] CUDA Version: 12.6
[SUCCESS] Device mode: CUDA

======================================================================
INSTALLING PYTORCH
======================================================================
[INFO] Installing PyTorch with CUDA 12.6 support...
[INFO] PyTorch index: https://download.pytorch.org/whl/cu126
[SUCCESS] PyTorch installed successfully

======================================================================
VERIFYING PYTORCH INSTALLATION
======================================================================
[INFO] Testing PyTorch GPU detection...
PyTorch version: 2.5.1+cu126
CUDA available: True
CUDA version: 12.6
GPU: NVIDIA GeForce GTX 750 Ti
GPU memory: 2.00 GB

[SUCCESS] PyTorch verification passed

[INFO] Installing psutil for hardware detection...
[SUCCESS] Dependencies installed

======================================================================
RUNNING JOB PREPARATION
======================================================================
[INFO] Workflow: SUBTITLE-GEN
[INFO] Native mode: ENABLED (using venv Python with CUDA)
[INFO] Input media: C:\Videos\movie.mp4

[INFO] Executing: python scripts\prepare-job.py C:\Videos\movie.mp4 --subtitle-gen --native

... (hardware detection, job creation, media preparation) ...

[SUCCESS] Job preparation completed successfully

======================================================================
CLEANING UP
======================================================================
[INFO] Removing virtual environment...
[SUCCESS] Virtual environment removed

======================================================================
JOB PREPARATION COMPLETE
======================================================================
[INFO] Device mode used: CUDA
[SUCCESS] Ready to run pipeline
```

### Example 2: macOS with Apple Silicon

```bash
$ ./prepare-job-venv.sh movie.mp4

======================================================================
CP-WHISPERX-APP JOB PREPARATION (VENV MODE)
======================================================================
[INFO] Creating isolated Python environment for job preparation...

[INFO] Validating Python installation...
[INFO] Found: Python 3.11.7
[SUCCESS] Python version check passed

======================================================================
HARDWARE DETECTION
======================================================================
[INFO] Detecting available acceleration hardware...
[INFO] No NVIDIA GPU detected (nvidia-smi not found)
[INFO] Apple Silicon detected
[SUCCESS] Device mode: MPS

======================================================================
INSTALLING PYTORCH
======================================================================
[INFO] Installing PyTorch with MPS support (macOS)...
[SUCCESS] PyTorch installed successfully

======================================================================
VERIFYING PYTORCH INSTALLATION
======================================================================
[INFO] Testing PyTorch GPU detection...
PyTorch version: 2.5.1
MPS available: True
Device: Apple Silicon

[SUCCESS] PyTorch verification passed

... (rest of workflow) ...

[SUCCESS] Ready to run pipeline
```

### Example 3: Linux CPU-only

```bash
$ ./prepare-job-venv.sh movie.mp4 --transcribe

======================================================================
CP-WHISPERX-APP JOB PREPARATION (VENV MODE)
======================================================================

======================================================================
HARDWARE DETECTION
======================================================================
[INFO] Detecting available acceleration hardware...
[INFO] No NVIDIA GPU detected (nvidia-smi not found)
[SUCCESS] Device mode: CPU

======================================================================
INSTALLING PYTORCH
======================================================================
[INFO] Installing PyTorch (CPU-only mode)...
[SUCCESS] PyTorch installed successfully

... (continues with CPU mode) ...
```

---

## Troubleshooting

### Issue: Python not found

**Error:**
```
[ERROR] Python not found. Please install Python 3.9+
```

**Solution:**
```bash
# Install Python 3.9+
# Windows: Download from python.org
# Linux: sudo apt install python3.9 python3.9-venv
# macOS: brew install python@3.11
```

### Issue: Virtual environment creation fails

**Error:**
```
[ERROR] Failed to create virtual environment
```

**Solution:**
```bash
# Install venv module (Linux)
sudo apt install python3-venv

# Or use virtualenv
pip install virtualenv
```

### Issue: PyTorch installation fails

**Error:**
```
[ERROR] Failed to install PyTorch
```

**Solutions:**
1. Check internet connection
2. Try with `--keep-venv` flag to inspect logs
3. Manually install in kept venv:
   ```bash
   source .venv-prepare-job-temp/bin/activate
   pip install torch --index-url https://download.pytorch.org/whl/cu126
   ```

### Issue: GPU not detected in PyTorch

**Warning:**
```
[WARN] PyTorch GPU detection failed, continuing with CPU mode
```

**Causes:**
1. CUDA drivers not installed
2. CUDA version mismatch
3. GPU not supported by PyTorch

**Solution:**
- Check NVIDIA drivers: `nvidia-smi`
- Update CUDA drivers if needed
- CPU mode will work as fallback

### Issue: Cannot remove virtual environment

**Warning:**
```
[WARN] Could not remove virtual environment (may be in use)
```

**Solution:**
```bash
# Wait a few seconds and retry
rm -rf .venv-prepare-job-temp  # Linux/macOS
Remove-Item -Path .venv-prepare-job-temp -Recurse -Force  # Windows
```

---

## Comparison: Regular vs Venv Scripts

| Feature | `prepare-job.ps1`/`.sh` | `prepare-job-venv.ps1`/`.sh` |
|---------|-------------------------|------------------------------|
| **PyTorch** | Uses system PyTorch | Installs fresh PyTorch |
| **GPU Detection** | May fail if wrong PyTorch | Always correct PyTorch |
| **Isolation** | Uses system packages | Isolated virtual environment |
| **Speed** | Fast (no setup) | Slower (installs packages) |
| **Cleanup** | None | Removes venv after |
| **Use Case** | Production, working setup | Troubleshooting, fresh setup |

### When to Use Each

**Use regular scripts** when:
- ✅ PyTorch already installed correctly
- ✅ GPU detection working
- ✅ Fast execution needed
- ✅ Production environment

**Use venv scripts** when:
- ✅ GPU detection issues
- ✅ Wrong PyTorch version installed
- ✅ Fresh/clean setup needed
- ✅ Testing different configurations
- ✅ Isolated from system Python

---

## Logging

### Log File Location

Automatic log files created in `logs/` directory:

```
logs/
└── YYYYMMDD-HHMMSS-prepare-job-venv.log
```

Example: `20241106-121530-prepare-job-venv.log`

### Log Levels

Set via `LOG_LEVEL` environment variable:

```bash
# Windows
$env:LOG_LEVEL="DEBUG"
.\prepare-job-venv.ps1 movie.mp4

# Linux/macOS
LOG_LEVEL=DEBUG ./prepare-job-venv.sh movie.mp4
```

Levels: `DEBUG`, `INFO` (default), `WARN`, `ERROR`

---

## Integration with Pipeline

After job preparation completes, run the pipeline:

```bash
# Windows
.\run_pipeline.ps1 -Job 20241106-0001

# Linux/macOS
./run_pipeline.sh --job 20241106-0001
```

The pipeline will use the hardware-optimized configuration created by `prepare-job.py`.

---

## Advanced Usage

### Keep Virtual Environment for Debugging

```bash
# Keep venv to inspect installation
./prepare-job-venv.sh movie.mp4 --keep-venv

# Activate and inspect
source .venv-prepare-job-temp/bin/activate
python -c "import torch; print(torch.__version__)"
python -c "import torch; print(torch.cuda.is_available())"

# Manual cleanup when done
deactivate
rm -rf .venv-prepare-job-temp
```

### Custom PyTorch Installation

If you need a specific PyTorch version, modify the script or install manually in kept venv:

```bash
./prepare-job-venv.sh movie.mp4 --keep-venv
source .venv-prepare-job-temp/bin/activate

# Install specific version
pip install torch==2.4.0+cu121 --index-url https://download.pytorch.org/whl/cu121

# Run prepare-job manually
python scripts/prepare-job.py movie.mp4 --native
```

---

## Related Documentation

- **[PREPARE_JOB_ARCHITECTURE.md](PREPARE_JOB_ARCHITECTURE.md)** - Detailed architecture of prepare-job.py
- **[HARDWARE_OPTIMIZATION.md](docs/HARDWARE_OPTIMIZATION.md)** - Hardware detection and optimization
- **[CUDA Acceleration Guide](docs/guides/hardware/cuda-acceleration.md)** - NVIDIA GPU setup
- **[MPS Acceleration Guide](docs/guides/hardware/mps-acceleration.md)** - Apple Silicon setup

---

## Summary

The `prepare-job-venv` scripts provide a **complete, isolated, self-contained** job preparation workflow:

1. ✅ **No system conflicts** - Isolated virtual environment
2. ✅ **Automatic GPU detection** - CUDA/MPS/CPU
3. ✅ **Correct PyTorch** - Matched to GPU capabilities
4. ✅ **Clean execution** - No leftover files
5. ✅ **Logging compliance** - Standard logging format
6. ✅ **Cross-platform** - Windows, Linux, macOS

**Perfect for:**
- First-time setup
- GPU detection troubleshooting
- Isolated testing
- CI/CD pipelines
- Clean room environments

---

**Last Updated:** 2024-11-06  
**Version:** 1.0.0
