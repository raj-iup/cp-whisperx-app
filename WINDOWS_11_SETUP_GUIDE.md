# Windows 11 Pro Setup Guide for CP-WhisperX-App

This guide covers native and Docker-based execution on **Windows 11 Pro 25H2** with NVIDIA CUDA support.

---

## System Requirements

### Hardware
- **OS:** Windows 11 Pro 25H2 (or later)
- **CPU:** Multi-core processor (Intel/AMD)
- **RAM:** 16GB minimum, 32GB recommended
- **Storage:** 50GB+ free space per movie
- **GPU:** 
  - NVIDIA GPU with CUDA support (e.g., GTX 750 Ti or newer)
  - Compute Capability 5.0+ recommended
  - 2GB+ VRAM (4GB+ recommended)

### Software Requirements
- **Python:** 3.11 or higher
- **NVIDIA Driver:** 560.94 or later (for CUDA 12.6+ support)
- **CUDA Toolkit:** 12.6+ (for native execution)
- **Docker Desktop for Windows:** Latest version (for Docker execution)
- **Git for Windows:** For repository management
- **FFmpeg:** For media processing

---

## Installation Methods

### Method 1: Native Execution (CUDA/CPU)

#### Step 1: Install NVIDIA Drivers and CUDA Toolkit

1. **Download NVIDIA Driver:**
   - Visit: https://www.nvidia.com/Download/index.aspx
   - Select your GPU model (e.g., GTX 750 Ti)
   - Download and install driver 560.94 or later

2. **Download CUDA Toolkit:**
   - Visit: https://developer.nvidia.com/cuda-downloads
   - Select: Windows → x86_64 → 11 → exe (local)
   - Download CUDA 12.6 or later
   - Run installer and follow prompts

3. **Verify Installation:**
   ```cmd
   nvidia-smi
   nvcc --version
   ```
   
   Expected output:
   ```
   CUDA Version: 12.6
   Driver Version: 560.94
   ```

#### Step 2: Install Python and Dependencies

1. **Download Python 3.11:**
   - Visit: https://www.python.org/downloads/windows/
   - Download Python 3.11.x (64-bit)
   - During installation, check "Add Python to PATH"

2. **Verify Python Installation:**
   ```cmd
   python --version
   pip --version
   ```

3. **Create Virtual Environment:**
   ```cmd
   cd C:\path\to\cp-whisperx-app
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Install PyTorch with CUDA Support:**
   ```cmd
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

5. **Install Application Dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

6. **Verify CUDA in PyTorch:**
   ```python
   python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"
   ```

#### Step 3: Install FFmpeg

1. **Download FFmpeg:**
   - Visit: https://www.gyan.dev/ffmpeg/builds/
   - Download "ffmpeg-release-essentials.zip"

2. **Extract and Add to PATH:**
   - Extract to `C:\ffmpeg`
   - Add `C:\ffmpeg\bin` to System PATH
   - Restart command prompt

3. **Verify:**
   ```cmd
   ffmpeg -version
   ```

#### Step 4: Configure Secrets

1. **Create secrets file:**
   ```cmd
   mkdir config
   echo {"HF_TOKEN": "your_huggingface_token", "TMDB_API_KEY": "your_tmdb_key"} > config\secrets.json
   ```

2. **Get HuggingFace Token:**
   - Visit: https://huggingface.co/settings/tokens
   - Accept terms: https://huggingface.co/pyannote/speaker-diarization-3.1

---

### Method 2: Docker Execution (CUDA/CPU)

#### Step 1: Install Docker Desktop for Windows

1. **Download Docker Desktop:**
   - Visit: https://www.docker.com/products/docker-desktop
   - Download Windows version
   - Install and restart computer

2. **Enable WSL 2 Backend:**
   - Docker Desktop → Settings → General
   - Enable "Use the WSL 2 based engine"

3. **Verify Installation:**
   ```cmd
   docker --version
   docker-compose --version
   ```

#### Step 2: Install NVIDIA Container Toolkit (for CUDA support)

1. **Install WSL 2:**
   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```

2. **Install NVIDIA Container Toolkit in WSL:**
   ```bash
   # Inside WSL Ubuntu
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   
   sudo apt-get update
   sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```

3. **Verify CUDA in Docker:**
   ```cmd
   docker run --rm --gpus all nvidia/cuda:12.6-runtime-ubuntu22.04 nvidia-smi
   ```

#### Step 3: Build Docker Images

1. **Build all images:**
   ```cmd
   docker-compose build
   ```

2. **Or build specific images:**
   ```cmd
   docker-compose build demux
   docker-compose build asr
   ```

#### Step 4: Configure for Docker

1. **Create secrets file:**
   ```cmd
   mkdir config
   echo {"HF_TOKEN": "your_huggingface_token", "TMDB_API_KEY": "your_tmdb_key"} > config\secrets.json
   ```

---

## Running the Pipeline

### Native Execution

#### Full Subtitle Generation Workflow

```cmd
REM Activate virtual environment
venv\Scripts\activate

REM Run preflight checks
python preflight.py

REM Prepare job
python prepare-job.py "C:\Videos\movie.mp4" --subtitle-gen --native

REM Run pipeline (replace with actual job ID)
python pipeline.py --job 20251103-0001
```

#### Transcribe-Only Workflow

```cmd
REM Prepare job for transcription only
python prepare-job.py "C:\Videos\movie.mp4" --transcribe --native

REM Run pipeline
python pipeline.py --job 20251103-0002
```

#### Clip Mode (Testing)

```cmd
REM Test with 5-minute clip
python prepare-job.py "C:\Videos\movie.mp4" --start-time 00:10:00 --end-time 00:15:00 --subtitle-gen --native

REM Run pipeline
python pipeline.py --job 20251103-0003
```

### Docker Execution

#### Full Subtitle Generation Workflow

```cmd
REM Prepare job (without --native flag)
python prepare-job.py "C:\Videos\movie.mp4" --subtitle-gen

REM Run pipeline
python pipeline.py --job 20251103-0001
```

#### Using Quick Start (Native)

```cmd
quick-start.bat "C:\Videos\movie.mp4"
```

---

## Device Selection

### Automatic Device Detection

The pipeline automatically detects and uses the best available device:

1. **CUDA** (if NVIDIA GPU available)
2. **CPU** (fallback)

### Force Specific Device

```cmd
REM Force CPU mode (native)
set WHISPERX_DEVICE=cpu
python pipeline.py --job 20251103-0001

REM Force CUDA mode (native)
set WHISPERX_DEVICE=cuda
python pipeline.py --job 20251103-0001
```

### Check Device Detection

```cmd
python -c "from prepare_job import detect_device_capability; print(detect_device_capability())"
```

---

## Performance Expectations

### GTX 750 Ti (2GB VRAM) Performance

Based on Windows 11 Pro 25H2 with CUDA 12.6:

| Stage | CPU Time | CUDA Time | Speedup |
|-------|----------|-----------|---------|
| Silero VAD | ~3.6 min | ~0.25 min | 14x |
| PyAnnote VAD | ~11.5 min | ~0.67 min | 17x |
| Diarization | ~98.6 min | ~4 min | 25x |
| ASR (WhisperX) | ~37 min | ~3 min | 12x |

**Total Pipeline:**
- **CPU Mode:** ~2.5 hours
- **CUDA Mode:** ~10 minutes
- **Speedup:** ~18x

---

## Troubleshooting

### CUDA Issues

#### Issue: `torch.cuda.is_available()` returns False

**Solutions:**
1. Verify NVIDIA driver installation: `nvidia-smi`
2. Check PyTorch CUDA version matches installed CUDA:
   ```cmd
   python -c "import torch; print(torch.version.cuda)"
   ```
3. Reinstall PyTorch with correct CUDA version:
   ```cmd
   pip uninstall torch torchvision torchaudio
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

#### Issue: CUDA Out of Memory (GTX 750 Ti with 2GB VRAM)

**Solutions:**
1. Reduce batch size in config:
   ```
   WHISPER_BATCH_SIZE=8
   ```
2. Use smaller model:
   ```
   WHISPER_MODEL=large-v2
   ```
3. Fall back to CPU for specific stage:
   ```
   WHISPERX_DEVICE=cpu
   ```

### Docker Issues

#### Issue: Docker can't access GPU

**Solutions:**
1. Verify NVIDIA Container Toolkit installed
2. Test GPU access:
   ```cmd
   docker run --rm --gpus all nvidia/cuda:12.6-runtime-ubuntu22.04 nvidia-smi
   ```
3. Restart Docker Desktop
4. Check Docker Desktop settings → Resources → WSL Integration

#### Issue: WSL 2 not available

**Solutions:**
1. Enable WSL 2:
   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```
2. Update Windows to latest version
3. Enable virtualization in BIOS

### Path Issues

#### Issue: Paths with spaces cause errors

**Solutions:**
1. Use quotes around paths:
   ```cmd
   python prepare-job.py "C:\My Videos\movie.mp4"
   ```
2. Or use short paths:
   ```cmd
   python prepare-job.py C:\Videos\movie.mp4
   ```

### Permission Issues

#### Issue: Access denied when creating directories

**Solutions:**
1. Run as Administrator
2. Check folder permissions
3. Use user directory instead of system directories

---

## Directory Structure (Windows)

```
C:\cp-whisperx-app\
├── jobs\                          # Job management
│   └── 2025\
│       └── 11\
│           └── 03\
│               └── 20251103-0001\
│                   ├── 20251103-0001.env
│                   └── movie.mp4
│
├── out\                           # Processing outputs
│   └── 2025\11\03\20251103-0001\
│       ├── audio\
│       ├── subtitles\
│       ├── final_output.mp4
│       └── manifest.json
│
├── logs\                          # Stage logs
│   └── 2025\11\03\20251103-0001\
│
├── config\
│   ├── .env
│   └── secrets.json
│
├── venv\                          # Python virtual environment (native)
│
├── prepare-job.bat                # Windows launcher scripts
├── run_pipeline.bat
├── preflight.bat
└── quick-start.bat
```

---

## Next Steps

1. **Test Installation:**
   ```cmd
   python preflight.py
   ```

2. **Run Quick Test:**
   ```cmd
   REM Create short test clip
   python prepare-job.py "C:\Videos\test.mp4" --start-time 00:00:00 --end-time 00:01:00 --subtitle-gen --native
   
   REM Run pipeline
   python pipeline.py --job <job_id>
   ```

3. **Process Full Movie:**
   ```cmd
   quick-start.bat "C:\Videos\full_movie.mp4"
   ```

4. **Review Comprehensive Test Plan:**
   - See `WINDOWS_11_COMPREHENSIVE_TEST_PLAN.md` for detailed testing checklist

---

## Support

For issues specific to Windows 11:
1. Check `logs\` directory for error messages
2. Run `python preflight.py --force` to diagnose issues
3. Review `TROUBLESHOOTING.md` for common solutions
4. Check CUDA environment: `python scripts/generate_cuda_report.py`

For CUDA version compatibility:
- Current tested: CUDA 12.6 on Windows 11 Pro 25H2
- Driver: 560.94+
- GPU: GTX 750 Ti (Compute 5.0)
- Future versions: Follow NVIDIA compatibility matrix
