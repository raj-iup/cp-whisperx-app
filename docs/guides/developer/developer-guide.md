# Developer Guide - CP-WhisperX-App

**Complete setup guide for all platforms: Windows, Linux, macOS**

## Table of Contents
- [Quick Setup](#quick-setup)
- [Windows Development](#windows-development)
- [Linux Development](#linux-development)
- [macOS Development](#macos-development)
- [Building Docker Images](#building-docker-images)
- [Testing](#testing)
- [Contributing](#contributing)

---

## Quick Setup

### Prerequisites (All Platforms)
- Git
- Python 3.11+
- Docker Desktop
- 20GB+ free disk space
- Good internet connection

### Clone Repository

```bash
git clone <repository-url>
cd cp-whisperx-app
```

---

## Windows Development

### Prerequisites

1. **Windows 11** (Windows 10 works but 11 recommended)
2. **WSL2** enabled
3. **Docker Desktop** with WSL2 backend
4. **Python 3.11+** (in WSL2)
5. **NVIDIA GPU** (optional, for CUDA acceleration)

### Step 1: Enable WSL2

```powershell
# Open PowerShell as Administrator
wsl --install
wsl --set-default-version 2

# Install Ubuntu
wsl --install -d Ubuntu-22.04

# Restart computer
```

### Step 2: Install Docker Desktop

1. Download from: https://www.docker.com/products/docker-desktop/
2. Install with WSL2 backend enabled
3. Open Docker Desktop → Settings:
   - Enable "Use WSL 2 based engine"
   - Enable "Ubuntu-22.04" under Resources → WSL Integration
4. Restart Docker Desktop

### Step 3: Setup WSL2 Environment

```bash
# Inside WSL2 (Ubuntu)
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Git
sudo apt install -y git

# Install build essentials
sudo apt install -y build-essential libsndfile1 ffmpeg
```

### Step 4: Setup NVIDIA GPU (Optional)

```bash
# Install NVIDIA drivers in WSL2
# Follow: https://docs.nvidia.com/cuda/wsl-user-guide/index.html

# Verify
nvidia-smi

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update
sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# Test GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Step 5: Clone and Setup Project

```bash
# Clone repository
cd ~
git clone <repository-url>
cd cp-whisperx-app

# Setup configuration
cp config/.env.example config/.env.pipeline
nano config/.env.pipeline  # Add your API keys

# Set device (auto-detects if not set)
export DEVICE=cuda  # or cpu if no GPU
```

### Step 6: Build CUDA Images (If GPU Available)

```bash
# Build CUDA base image
docker build -t rajiup/cp-whisperx-app-base:cuda \
  -f docker/base-cuda/Dockerfile .

# Build all images
./scripts/build-all-images.sh

# Or pull from registry
docker pull rajiup/cp-whisperx-app-base:cuda
docker pull rajiup/cp-whisperx-app-asr:latest
# ... etc
```

### Step 7: Test Pipeline

```bash
# Prepare test job
python prepare-job.py /path/to/test-video.mp4 --native

# Run pipeline
python pipeline.py --job <job-id>

# Check results
ls -lh out/2025/11/03/1/<job-id>/
```

### Windows-Specific Notes

- **Paths:** Use WSL2 paths (`/home/user/...`) not Windows paths (`C:\...`)
- **Performance:** WSL2 file I/O is slower, keep projects in WSL2 filesystem
- **GPU:** Requires WSL2 + NVIDIA drivers + Container Toolkit
- **Docker:** Must use WSL2 backend, Hyper-V mode won't work
- **Memory:** Allocate 8GB+ RAM to WSL2 in `.wslconfig`

**`.wslconfig` example (in `C:\Users\<YourName>\.wslconfig`):**
```ini
[wsl2]
memory=16GB
processors=8
swap=8GB
```

---

## Linux Development

### Prerequisites

1. **Ubuntu 22.04** (or similar)
2. **Python 3.11+**
3. **Docker** (with NVIDIA Container Toolkit for GPU)
4. **NVIDIA GPU** (optional, for CUDA acceleration)

### Step 1: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install -y docker-compose-plugin

# Install build tools
sudo apt install -y build-essential git ffmpeg libsndfile1
```

### Step 2: Setup NVIDIA GPU (Optional)

```bash
# Install NVIDIA drivers (if not already installed)
sudo apt install -y nvidia-driver-535
sudo reboot

# Verify
nvidia-smi

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update
sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# Test
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Step 3: Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd cp-whisperx-app

# Setup configuration
cp config/.env.example config/.env.pipeline
nano config/.env.pipeline  # Add API keys

# Device auto-detects CUDA if available
```

### Step 4: Build CUDA Images

```bash
# Build CUDA base
docker build -t rajiup/cp-whisperx-app-base:cuda \
  -f docker/base-cuda/Dockerfile .

# Build all images
./scripts/build-all-images.sh

# Or pull from registry (if already pushed)
docker login
docker pull rajiup/cp-whisperx-app-base:cuda
```

### Step 5: Test Pipeline

```bash
# Prepare job with GPU
python3 prepare-job.py /path/to/video.mp4 --native

# Run pipeline
python3 pipeline.py --job <job-id>

# Monitor
tail -f out/2025/11/03/1/<job-id>/logs/orchestrator_*.log
```

### Linux-Specific Notes

- **Permissions:** Add user to docker group: `sudo usermod -aG docker $USER`
- **GPU:** Pipeline auto-detects CUDA and uses `--gpus all`
- **Performance:** Native filesystem, best I/O performance
- **Systemd:** Docker auto-starts on boot

---

## macOS Development

### Prerequisites

1. **macOS 12+** (Monterey or later)
2. **Apple Silicon** (M1/M2/M3) for MPS acceleration
3. **Python 3.11+**
4. **Docker Desktop** for non-ML stages

### Step 1: Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Dependencies

```bash
# Install Python 3.11
brew install python@3.11

# Install ffmpeg
brew install ffmpeg

# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop/
```

### Step 3: Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd cp-whisperx-app

# Setup configuration
cp config/.env.example config/.env.pipeline
nano config/.env.pipeline  # Add API keys
```

### Step 4: Setup Native Virtual Environments

```bash
# Create venvs for native execution
./native/setup_venvs.sh

# This creates:
# - native/venvs/vad/
# - native/venvs/diarization/
# - native/venvs/asr/
```

### Step 5: Test Pipeline

```bash
# Prepare job with native MPS
python3 prepare-job.py /path/to/video.mp4 --native

# Run pipeline (ML stages run natively with MPS)
python3 pipeline.py --job <job-id>

# Check GPU usage
# Activity Monitor → GPU tab
```

### macOS-Specific Notes

- **MPS:** Apple Silicon GPUs use Metal Performance Shaders
- **Native Mode:** ML stages run in Python venvs, non-ML in Docker
- **Performance:** MPS is fast but not as fast as NVIDIA CUDA
- **Docker:** Used for non-ML stages (demux, mux, subtitle-gen)
- **CPU Mode:** Set `DEVICE=cpu` to run all stages in Docker

---

## Building Docker Images

### Build All Images

```bash
# Set registry (optional)
export DOCKERHUB_USER="your-username"

# Build all images
./scripts/build-all-images.sh

# Expected output:
# ✓ base:cpu
# ✓ demux, tmdb, pre-ner, post-ner, subtitle-gen, mux
# ✓ silero-vad, pyannote-vad, diarization, asr
# ✓ second-pass-translation, lyrics-detection
```

### Build CUDA Base (Linux/Windows Only)

```bash
# Must be on Linux or WSL2
docker build -t rajiup/cp-whisperx-app-base:cuda \
  -f docker/base-cuda/Dockerfile .

# Test
docker run --rm --gpus all rajiup/cp-whisperx-app-base:cuda \
  python -c "import torch; print(torch.cuda.is_available())"
```

### Push to Registry

```bash
# Login
docker login

# Push all images
./scripts/push-all-images.sh

# Verify on Docker Hub
# https://hub.docker.com/u/<your-username>
```

### Pull Pre-Built Images

```bash
# Pull all images
docker-compose pull

# Or specific images
docker pull rajiup/cp-whisperx-app-base:cpu
docker pull rajiup/cp-whisperx-app-asr:latest
```

---

## Testing

### Unit Tests

```bash
# Run Python tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_pipeline.py -v
```

### Integration Tests

```bash
# Test job creation
python prepare-job.py /path/to/test-video.mp4 \
  --start-time 00:00:00 \
  --end-time 00:01:00

# Expected: Job created, clip generated

# Test pipeline
python pipeline.py --job <job-id>

# Expected: All stages complete successfully
```

### Platform-Specific Tests

Follow **TEST_PLAN.md** for comprehensive testing:

**Windows:**
- [ ] Docker CPU mode
- [ ] Docker CUDA mode (with GPU)
- [ ] Job creation
- [ ] Pipeline execution
- [ ] Resume capability

**Linux:**
- [ ] Docker CPU mode
- [ ] Docker CUDA mode (with GPU)
- [ ] Native mode (future)
- [ ] Performance benchmarks

**macOS:**
- [ ] Native MPS mode
- [ ] Docker CPU mode
- [ ] Job creation
- [ ] Pipeline execution

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes

```bash
# Edit code
vim pipeline.py

# Test locally
python pipeline.py --job <test-job>

# Check logs
tail -f out/.../logs/orchestrator_*.log
```

### 3. Run Tests

```bash
# Quick test
python prepare-job.py test-video.mp4 --start-time 00:00:00 --end-time 00:01:00
python pipeline.py --job <job-id>

# Full test suite
pytest tests/
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: description of changes"
```

### 5. Push and Create PR

```bash
git push origin feature/my-feature
# Create Pull Request on GitHub
```

---

## Troubleshooting

### Docker Issues

```bash
# Check Docker
docker --version
docker compose version

# Test Docker
docker run --rm hello-world

# Check GPU (Linux/Windows)
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Clean up
docker system prune -a
```

### Python Issues

```bash
# Check Python
python --version  # Should be 3.11+

# Check pip
pip --version

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Build Issues

```bash
# Clean build
docker system prune -a
./scripts/build-all-images.sh

# Build specific stage
docker build -t test-image -f docker/asr/Dockerfile .
```

### Runtime Issues

```bash
# Check logs
ls -lh out/<job-id>/logs/
cat out/<job-id>/logs/orchestrator_*.log

# Check manifest
cat out/<job-id>/manifest.json | jq .

# Check config
cat out/<job-id>/.<job-id>.env | grep -E "DEVICE|OUTPUT"
```

---

## Project Structure

```
cp-whisperx-app/
├── config/                   # Configuration templates
│   ├── .env.pipeline        # Main template
│   └── .env.example         # Example config
├── docker/                   # Docker stage definitions
│   ├── base/                # CPU base image
│   ├── base-cuda/           # CUDA base image
│   ├── asr/                 # WhisperX transcription
│   ├── diarization/         # Speaker diarization
│   └── ...                  # Other stages
├── native/                   # Native execution (macOS)
│   ├── scripts/             # Native stage scripts
│   ├── venvs/               # Virtual environments
│   └── setup_venvs.sh       # Setup script
├── scripts/                  # Build and utility scripts
│   ├── build-all-images.sh  # Build Docker images
│   └── push-all-images.sh   # Push to registry
├── shared/                   # Shared utilities
│   ├── logger.py            # PipelineLogger
│   ├── config.py            # Config loader
│   └── manifest.py          # Manifest builder
├── out/                      # Output directory
│   └── YYYY/MM/DD/<user>/<job>/  # Job outputs
├── prepare-job.py            # Job preparation
├── pipeline.py               # Pipeline orchestrator
├── docker-compose.yml        # Docker services
└── docs/                     # Documentation
```

---

## Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Keep functions focused

### Testing

- Add tests for new features
- Ensure existing tests pass
- Test on multiple platforms

### Documentation

- Update relevant .md files
- Add examples for new features
- Keep DEVELOPER_GUIDE.md current

### Pull Requests

- Clear description
- Link to related issues
- Pass all CI checks
- Request reviews

---

## Resources

**Documentation:**
- QUICKSTART.md - Quick start guide
- TEST_PLAN.md - Testing procedures
- IMPLEMENTATION_UNIFORMITY.md - Architecture guide
- DOCKER_BUILD_GUIDE.md - Docker reference

**Platform Guides:**
- WINDOWS_11_SETUP_GUIDE.md
- CUDA_ACCELERATION_GUIDE.md
- MPS_ACCELERATION_GUIDE.md
- DEVICE_SELECTION_GUIDE.md

**External:**
- Docker: https://docs.docker.com
- NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/
- WSL2: https://docs.microsoft.com/en-us/windows/wsl/

---

## Support

**Issues:** Report on GitHub
**Questions:** Check documentation first
**Contributing:** See CONTRIBUTING.md (if available)

---

**Last Updated:** November 3, 2025
**Version:** 1.0.0
