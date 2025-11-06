# prepare-job-venv Quick Reference

**One-stop solution for GPU detection issues in job preparation**

---

## 🚀 Quick Start

### Windows
```powershell
.\prepare-job-venv.ps1 movie.mp4
```

### Linux/macOS
```bash
./prepare-job-venv.sh movie.mp4
```

---

## 💡 What It Does

```
1. Create temp Python venv (.venv-prepare-job-temp)
   ↓
2. Detect hardware (nvidia-smi → CUDA version)
   ↓
3. Install PyTorch (cu126/cu121/cu118/mps/cpu)
   ↓
4. Verify GPU detection (torch.cuda.is_available)
   ↓
5. Run scripts/prepare-job.py --native
   ↓
6. Remove venv (cleanup)
   ↓
7. Job ready for pipeline!
```

---

## 🎯 Problem Solved

| Before | After |
|--------|-------|
| ❌ nvidia-smi works | ✅ nvidia-smi works |
| ❌ PyTorch CPU-only (2.8.0+cpu) | ✅ PyTorch with CUDA (2.5.1+cu126) |
| ❌ prepare-job.py: GPU not detected | ✅ prepare-job.py: GPU detected! |

---

## 📋 Common Commands

### Basic Usage
```bash
# Windows
.\prepare-job-venv.ps1 movie.mp4

# Linux/macOS
./prepare-job-venv.sh movie.mp4
```

### Transcribe Only
```bash
# Windows
.\prepare-job-venv.ps1 movie.mp4 -Transcribe

# Linux/macOS
./prepare-job-venv.sh movie.mp4 --transcribe
```

### Process Clip
```bash
# Windows
.\prepare-job-venv.ps1 movie.mp4 -StartTime "00:10:00" -EndTime "00:15:00"

# Linux/macOS
./prepare-job-venv.sh movie.mp4 --start-time 00:10:00 --end-time 00:15:00
```

### Keep Venv (Debug)
```bash
# Windows
.\prepare-job-venv.ps1 movie.mp4 -KeepVenv

# Linux/macOS
./prepare-job-venv.sh movie.mp4 --keep-venv
```

---

## 🔍 Hardware Detection

| System | Detection Method | PyTorch Mode |
|--------|------------------|--------------|
| **Windows + NVIDIA** | `nvidia-smi` → CUDA 12.6 | cu126 |
| **Linux + NVIDIA** | `nvidia-smi` → CUDA 11.8 | cu118 |
| **macOS + M1/M2** | `sysctl` → Apple Silicon | mps |
| **No GPU** | None detected | cpu |

---

## 🛠️ CUDA Version Mapping

| Your CUDA | PyTorch Index | Install Command |
|-----------|---------------|-----------------|
| **12.6+** | cu126 | `--index-url .../cu126` |
| **12.4-12.5** | cu124 | `--index-url .../cu124` |
| **12.1-12.3** | cu121 | `--index-url .../cu121` |
| **11.x** | cu118 | `--index-url .../cu118` |

Check your CUDA: `nvidia-smi` (look for "CUDA Version: X.Y")

---

## 📝 Expected Output

### Successful CUDA Detection
```
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
```

### Successful MPS Detection (macOS)
```
======================================================================
HARDWARE DETECTION
======================================================================
[INFO] No NVIDIA GPU detected (nvidia-smi not found)
[INFO] Apple Silicon detected
[SUCCESS] Device mode: MPS

======================================================================
VERIFYING PYTORCH INSTALLATION
======================================================================
PyTorch version: 2.5.1
MPS available: True
Device: Apple Silicon

[SUCCESS] PyTorch verification passed
```

### CPU Fallback
```
======================================================================
HARDWARE DETECTION
======================================================================
[INFO] No NVIDIA GPU detected (nvidia-smi not found)
[SUCCESS] Device mode: CPU

======================================================================
INSTALLING PYTORCH
======================================================================
[INFO] Installing PyTorch (CPU-only mode)...
[SUCCESS] PyTorch installed successfully
```

---

## ⚡ vs Regular Scripts

| Feature | `prepare-job.ps1` | `prepare-job-venv.ps1` |
|---------|-------------------|------------------------|
| Speed | ⚡⚡⚡ Fast | ⚡⚡ Slower |
| PyTorch | System | Fresh install |
| GPU Fix | ❌ No | ✅ Yes |
| Isolation | ❌ No | ✅ Yes |
| Use When | Working setup | GPU issues |

---

## 🐛 Quick Troubleshooting

### Issue: Python not found
```bash
# Install Python 3.9+
# Windows: python.org
# Linux: sudo apt install python3.9 python3-venv
# macOS: brew install python@3.11
```

### Issue: nvidia-smi not found
```bash
# Install NVIDIA drivers
# Windows: nvidia.com/drivers
# Linux: sudo ubuntu-drivers autoinstall
```

### Issue: GPU still not detected
```bash
# Keep venv and inspect
.\prepare-job-venv.ps1 movie.mp4 -KeepVenv
.\.venv-prepare-job-temp\Scripts\Activate.ps1
python -c "import torch; print(torch.cuda.is_available())"
```

---

## 📊 Performance Impact

| Stage | Time | Note |
|-------|------|------|
| Venv creation | ~5s | One-time per run |
| PyTorch install | ~30-60s | Downloads ~2GB |
| Verification | ~2s | Tests GPU |
| Job preparation | ~5-30s | Depends on media |
| Cleanup | ~5s | Removes venv |
| **Total overhead** | **~1-2 min** | vs regular script |

**Worth it?** ✅ Yes, if GPU detection is broken!

---

## 🔗 Next Steps After Success

1. **Verify job created:**
   ```bash
   ls out/2024/11/06/1/
   # Should see: YYYYMMDD-NNNN/
   ```

2. **Check job metadata:**
   ```bash
   cat out/2024/11/06/1/20241106-0001/job.json
   # Look for: "gpu_type": "cuda"
   ```

3. **Run pipeline:**
   ```bash
   # Windows
   .\run_pipeline.ps1 -Job 20241106-0001
   
   # Linux/macOS
   ./run_pipeline.sh --job 20241106-0001
   ```

---

## 📚 Full Documentation

- **Detailed Guide:** [docs/PREPARE_JOB_VENV.md](PREPARE_JOB_VENV.md)
- **Architecture:** [docs/PREPARE_JOB_ARCHITECTURE.md](PREPARE_JOB_ARCHITECTURE.md)
- **Hardware Optimization:** [docs/HARDWARE_OPTIMIZATION.md](docs/HARDWARE_OPTIMIZATION.md)

---

## ✅ Checklist

Before running:
- [ ] Python 3.9+ installed (`python --version`)
- [ ] For GPU: NVIDIA drivers installed (`nvidia-smi`)
- [ ] Input media file exists
- [ ] Enough disk space (~3GB for venv + PyTorch)

After running:
- [ ] "Device mode: CUDA/MPS/CPU" shown
- [ ] "PyTorch verification passed" ✓
- [ ] "Job preparation completed successfully" ✓
- [ ] Job directory created in `out/YYYY/MM/DD/`

---

**Created:** 2024-11-06  
**For:** cp-whisperx-app project  
**Purpose:** Solve GPU detection issues in job preparation
