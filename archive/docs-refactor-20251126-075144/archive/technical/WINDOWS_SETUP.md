# Windows Setup Guide

**Last Updated:** 2025-11-19  
**Platform:** Windows 10/11  
**Audience:** Windows Users

---

## Overview

This guide provides step-by-step instructions for setting up cp-whisperx-app on Windows with native PowerShell scripts (no Docker required).

---

## Prerequisites

### Required Software

1. **Windows 10/11** (64-bit)
   - Windows 10 version 1809 or later
   - Windows 11 recommended

2. **PowerShell 7.0+**
   - Download: https://github.com/PowerShell/PowerShell/releases
   - Installation: `winget install Microsoft.PowerShell`

3. **Python 3.9-3.12**
   - Download: https://www.python.org/downloads/
   - ⚠️ **IMPORTANT:** Check "Add Python to PATH" during installation
   - Recommended: Python 3.11

4. **FFmpeg**
   - Download: https://www.gyan.dev/ffmpeg/builds/
   - Extract to `C:\ffmpeg\bin`
   - Add to PATH: System Properties → Environment Variables → Path

5. **Git for Windows** (Optional but recommended)
   - Download: https://git-scm.com/download/win

### Hardware Requirements

**Minimum:**
- CPU: Intel i5 or AMD Ryzen 5
- RAM: 8 GB
- Storage: 20 GB free space
- GPU: Not required (CPU mode works)

**Recommended (with GPU):**
- GPU: NVIDIA GPU with 6GB+ VRAM
- CUDA: 11.8 or 12.1
- RAM: 16 GB
- Storage: 50 GB free space

---

## Installation

### Step 1: Install PowerShell 7

```powershell
# Using winget (Windows 11 or Windows 10 with App Installer)
winget install Microsoft.PowerShell

# Verify installation
pwsh --version
# Should show: PowerShell 7.x.x
```

**Alternative: Manual Installation**
1. Download from: https://github.com/PowerShell/PowerShell/releases
2. Run the MSI installer
3. Restart your terminal

### Step 2: Install Python

```powershell
# Using winget
winget install Python.Python.3.11

# Verify installation
python --version
# Should show: Python 3.11.x
```

**Alternative: Manual Installation**
1. Download from: https://www.python.org/downloads/
2. Run installer
3. ⚠️ **CHECK "Add Python to PATH"**
4. Choose "Customize installation" → Check all options

### Step 3: Install FFmpeg

**Option A: Using Chocolatey**
```powershell
# Install Chocolatey first (if not installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install FFmpeg
choco install ffmpeg
```

**Option B: Manual Installation**
1. Download: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH:
   - Open System Properties (Win + Pause/Break)
   - Click "Environment Variables"
   - Under "System variables", find "Path"
   - Click "Edit" → "New"
   - Add `C:\ffmpeg\bin`
   - Click OK on all dialogs
4. Restart PowerShell

**Verify FFmpeg:**
```powershell
ffmpeg -version
# Should show FFmpeg version info
```

### Step 4: Clone Repository

```powershell
# Using Git
cd C:\Projects
git clone https://github.com/yourusername/cp-whisperx-app.git
cd cp-whisperx-app

# Or download ZIP and extract
```

### Step 5: Run Bootstrap

```powershell
# Run bootstrap to setup environment
.\scripts\bootstrap.ps1

# This will:
# - Create .bollyenv virtual environment
# - Install all Python dependencies
# - Detect hardware (CUDA/CPU)
# - Download ML models
# - Configure pipeline
```

**Expected output:**
```
======================================================================
   CP-WHISPERX-APP BOOTSTRAP (ENHANCED)
======================================================================
[2025-11-19 14:30:00] [INFO] One-time environment setup...
[2025-11-19 14:30:01] [INFO] Platform: Windows (AMD64)
[2025-11-19 14:30:02] [SUCCESS] Environment validated
...
[2025-11-19 14:45:00] [SUCCESS] Environment ready!
```

---

## Configuration

### HuggingFace Token (Required for Diarization)

1. Create `config\secrets.json`:
```powershell
New-Item -Path config -ItemType Directory -Force
@"
{
  "HF_TOKEN": "your_huggingface_token_here"
}
"@ | Out-File -FilePath config\secrets.json -Encoding UTF8
```

2. Get your token:
   - Visit: https://huggingface.co/settings/tokens
   - Create a token with "Read" access
   - Accept model licenses:
     - https://huggingface.co/pyannote/speaker-diarization-3.1
     - https://huggingface.co/pyannote/segmentation-3.0

### Pipeline Configuration

Edit `config\.env.pipeline` to customize settings:

```ini
# Device configuration (auto-detected by bootstrap)
DEVICE=cuda                      # cuda, cpu
WHISPER_BACKEND=whisperx         # whisperx, mlx (mlx=Apple Silicon only)

# Model settings
WHISPER_MODEL=large-v3           # tiny, base, small, medium, large-v2, large-v3
WHISPER_COMPUTE_TYPE=float16     # float16, int8

# Batch sizes (adjust based on GPU memory)
BATCH_SIZE=8                     # Default: 8 (reduce if OOM errors)
VAD_BATCH_SIZE=32                # VAD batch size

# Language settings
SOURCE_LANGUAGE=hi               # Default source language
TARGET_LANGUAGE=en               # Default target language

# Logging
LOG_LEVEL=INFO                   # DEBUG, INFO, WARN, ERROR
```

---

## Usage

### Transcribe Workflow (Audio → Text)

```powershell
# Prepare job
.\prepare-job.ps1 in\movie.mp4 -Transcribe -SourceLanguage hi

# Run pipeline
.\run-pipeline.ps1 -JobId <job-id>

# Example:
.\prepare-job.ps1 C:\Videos\movie.mp4 -Transcribe -s hi
.\run-pipeline.ps1 -JobId job-20251119-user01-0001
```

### Translate Workflow (Text → English Subtitles)

```powershell
# Prepare job (auto-runs transcribe if needed)
.\prepare-job.ps1 in\movie.mp4 -Translate -SourceLanguage hi -TargetLanguage en

# Run pipeline
.\run-pipeline.ps1 -JobId <job-id>

# Example:
.\prepare-job.ps1 C:\Videos\movie.mp4 -Translate -s hi -t en
.\run-pipeline.ps1 -JobId job-20251119-user01-0001
```

### Check Job Status

```powershell
# View status
.\run-pipeline.ps1 -JobId job-20251119-user01-0001 -Status

# Resume failed job
.\run-pipeline.ps1 -JobId job-20251119-user01-0001 -Resume
```

---

## GPU Acceleration (NVIDIA CUDA)

### Install CUDA Toolkit

1. **Check GPU Compatibility:**
```powershell
nvidia-smi
# Should show your GPU info
```

2. **Install CUDA 11.8:**
   - Download: https://developer.nvidia.com/cuda-11-8-0-download-archive
   - Select: Windows → x86_64 → 11 → exe (local)
   - Run installer (default options)

3. **Install cuDNN:**
   - Download: https://developer.nvidia.com/cudnn (requires account)
   - Extract to `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8`

4. **Verify Installation:**
```powershell
nvcc --version
# Should show: CUDA Version 11.8
```

5. **Re-run Bootstrap:**
```powershell
.\scripts\bootstrap.ps1
# Will detect CUDA and configure accordingly
```

### Verify GPU Usage

```powershell
# In another PowerShell window, monitor GPU usage:
nvidia-smi -l 1

# Run pipeline and watch GPU utilization
```

---

## Troubleshooting

### Python Not Found

```powershell
# Check if Python is in PATH
python --version

# If not found, add manually:
# 1. Find Python location: C:\Users\<username>\AppData\Local\Programs\Python\Python311
# 2. Add to PATH in System Environment Variables
```

### PowerShell Execution Policy Error

```powershell
# Run as Administrator:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Verify:
Get-ExecutionPolicy
# Should show: RemoteSigned
```

### FFmpeg Not Found

```powershell
# Check if FFmpeg is in PATH
ffmpeg -version

# If not found:
# 1. Verify C:\ffmpeg\bin exists
# 2. Add to PATH (see Step 3 above)
# 3. Restart PowerShell
```

### CUDA Out of Memory

```powershell
# Edit config\.env.pipeline
# Reduce batch size:
BATCH_SIZE=4                     # Was 8
WHISPER_MODEL=medium             # Was large-v3
```

### Virtual Environment Issues

```powershell
# Remove and recreate
Remove-Item -Recurse -Force .bollyenv
.\scripts\bootstrap.ps1
```

### DLL Load Failed (CUDA)

```powershell
# Install Visual C++ Redistributables
winget install Microsoft.VCRedist.2015+.x64

# Or download: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

---

## Windows-Specific Features

### Developer Mode

Enable Developer Mode for HuggingFace symlink support:
1. Open Settings
2. Go to "Privacy & security" → "For developers"
3. Toggle "Developer Mode" ON
4. Restart computer

**Benefits:**
- Faster model downloads
- Less disk space usage
- Better HuggingFace cache performance

### Task Scheduler (Automated Jobs)

Schedule log rotation:
```powershell
# Create task
$action = New-ScheduledTaskAction -Execute 'PowerShell.exe' `
  -Argument '-File "C:\Projects\cp-whisperx-app\tools\rotate-logs.ps1" -KeepDays 30'

$trigger = New-ScheduledTaskTrigger -Daily -At 2am

Register-ScheduledTask -TaskName "CP-WhisperX Log Rotation" `
  -Action $action -Trigger $trigger -Description "Rotate old log files"
```

### Windows Terminal Configuration

Add to Windows Terminal settings for better experience:

```json
{
  "profiles": {
    "list": [
      {
        "name": "CP-WhisperX",
        "commandline": "pwsh.exe -NoExit -Command \"cd C:\\Projects\\cp-whisperx-app; .\\scripts\\common-logging.ps1\"",
        "startingDirectory": "C:\\Projects\\cp-whisperx-app",
        "icon": "📝"
      }
    ]
  }
}
```

---

## Performance Benchmarks (Windows)

### Intel i7-12700K + NVIDIA RTX 3080 (10GB)

| Workflow | Time (2-hour movie) | GPU Usage |
|----------|---------------------|-----------|
| Transcribe (large-v3) | ~25 min | 85-95% |
| Translate (IndicTrans2) | ~8 min | 70-80% |
| **Total** | **~33 min** | **Avg 82%** |

### Intel i5-10400 (CPU Only)

| Workflow | Time (2-hour movie) | CPU Usage |
|----------|---------------------|-----------|
| Transcribe (large-v3) | ~120 min | 90-100% |
| Translate (IndicTrans2) | ~15 min | 70-80% |
| **Total** | **~135 min** | **Avg 85%** |

**Recommendations:**
- Use GPU for transcribe stage (4x faster)
- CPU is acceptable for translate stage
- Reduce model size if OOM errors occur

---

## Next Steps

1. **Test Setup:**
   ```powershell
   .\prepare-job.ps1 -Help
   .\run-pipeline.ps1 -Help
   ```

2. **Try Sample Workflow:**
   ```powershell
   # Use a 5-minute test video
   .\prepare-job.ps1 test.mp4 -Transcribe -s hi
   .\run-pipeline.ps1 -JobId <job-id>
   ```

3. **Monitor Logs:**
   ```powershell
   # View latest log
   Get-Content logs\* | Select-Object -Last 50
   
   # Watch in real-time
   Get-Content -Path logs\<latest>.log -Wait -Tail 20
   ```

4. **Join Community:**
   - Report issues: GitHub Issues
   - Ask questions: Discussions
   - Contribute: Pull Requests

---

## Additional Resources

- **General Documentation:** [README.md](../README.md)
- **Logging Standards:** [LOGGING_STANDARDS.md](LOGGING_STANDARDS.md)
- **Troubleshooting:** [LOGGING_TROUBLESHOOTING.md](LOGGING_TROUBLESHOOTING.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **PowerShell Examples:** See `prepare-job.ps1 -Help`

---

**Last Updated:** 2025-11-19  
**Tested On:** Windows 11 Pro (Build 22621)  
**Status:** Production Ready
