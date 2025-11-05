# Docker Image Scripts - Quick Reference

## 📥 Pull Images from Registry

Pull all pre-built images from Docker Hub (fastest way to get started):

**Windows:**
```batch
pull-all-images.bat
```

**Linux/macOS:**
```bash
./pull-all-images.sh
```

---

## 🔨 Build Images Locally

Build all images from source (when you need latest code changes):

**Windows:**
```batch
scripts\build-all-images.bat
```

**Linux/macOS:**
```bash
./scripts/build-all-images.sh
```

**Build order (automatic):**
1. Base images: `base:cpu`, `base:cuda`, `base-ml:cuda`
2. CPU stages: 6 images
3. GPU CUDA stages: 6 images  
4. GPU CPU fallback stages: 6 images

**Total:** 21 images (~150 GB)

---

## 📤 Push Images to Registry

Push your locally built images to Docker Hub:

**Prerequisites:**
```bash
docker login
```

**Windows:**
```batch
scripts\push-all-images.bat
```

**Linux/macOS:**
```bash
./scripts/push-all-images.sh
```

---

## 🚀 Common Workflows

### First Time Setup
```bash
# Option 1: Pull pre-built images (recommended)
./pull-all-images.sh

# Option 2: Build from source
./scripts/build-all-images.sh
```

### After Making Code Changes
```bash
# Rebuild affected image
docker build -t rajiup/cp-whisperx-app-asr:cuda docker/asr

# Or rebuild all
./scripts/build-all-images.sh

# Push to registry
./scripts/push-all-images.sh
```

### Update to Latest Images
```bash
# Pull latest from registry
./pull-all-images.sh

# Restart services
docker-compose down
docker-compose up -d
```

---

## 🏷️ Image Tags

| Image Pattern | Description |
|---------------|-------------|
| `*:cpu` | CPU-only variant (fallback) |
| `*:cuda` | CUDA-enabled variant (GPU) |

**Examples:**
```
rajiup/cp-whisperx-app-base:cpu
rajiup/cp-whisperx-app-base:cuda
rajiup/cp-whisperx-app-asr:cpu
rajiup/cp-whisperx-app-asr:cuda
```

---

## 📊 Image List

### Base Images (3)
```
base:cpu           # Python 3.11 + utilities (~1.5 GB)
base:cuda          # CUDA 12.1 + Python 3.11 (~8 GB)
base-ml:cuda       # CUDA + PyTorch + ML libs (~12 GB)
```

### CPU-Only Stages (6)
```
demux:cpu          # FFmpeg audio extraction
tmdb:cpu           # TMDB metadata fetch
pre-ner:cpu        # Pre-ASR entity extraction
post-ner:cpu       # Post-ASR entity correction
subtitle-gen:cpu   # SRT subtitle generation
mux:cpu            # FFmpeg subtitle embedding
```

### GPU Stages - CUDA (6)
```
silero-vad:cuda    # Voice activity detection
pyannote-vad:cuda  # Advanced VAD with chunking
diarization:cuda   # Speaker identification
asr:cuda           # WhisperX transcription
second-pass-translation:cuda  # Translation refinement
lyrics-detection:cuda         # Song/music detection
```

### GPU Stages - CPU Fallback (6)
```
silero-vad:cpu
pyannote-vad:cpu
diarization:cpu
asr:cpu
second-pass-translation:cpu
lyrics-detection:cpu
```

---

## 🔍 Verify Images

```bash
# List all cp-whisperx-app images
docker images | grep cp-whisperx-app

# Count images (should be 21)
docker images | grep cp-whisperx-app | wc -l

# Check specific image
docker inspect rajiup/cp-whisperx-app-base:cuda
```

---

## 🧹 Cleanup

```bash
# Remove all cp-whisperx-app images
docker images | grep cp-whisperx-app | awk '{print $3}' | xargs docker rmi -f

# Remove dangling images
docker image prune

# Full cleanup (use with caution)
docker system prune -a
```

---

## ⚙️ Environment Variables

```bash
# Windows
set DOCKER_REGISTRY=rajiup
set DOCKER_TAG=latest

# Linux/macOS
export DOCKER_REGISTRY=rajiup
export DOCKER_TAG=latest
```

---

## 📖 Documentation

- **[docs/DOCKER_IMAGE_MANAGEMENT.md](docs/DOCKER_IMAGE_MANAGEMENT.md)** - Complete guide
- **[WINDOWS_SCRIPTS.md](WINDOWS_SCRIPTS.md)** - Windows script equivalents
- **[DOCKER_BUILD_OPTIMIZATION.md](DOCKER_BUILD_OPTIMIZATION.md)** - Build optimization
- **[docker/README.md](docker/README.md)** - Docker architecture

---

## 💡 Tips

1. **First time?** Use `pull-all-images` (faster than building)
2. **Making changes?** Build locally with `build-all-images`
3. **Low disk space?** Pull only images you need
4. **Slow builds?** Enable BuildKit: `export DOCKER_BUILDKIT=1`
5. **GPU unavailable?** Pipeline auto-falls back to CPU images

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Pull fails | Check `docker login` and network |
| Build fails | Check Docker daemon: `docker info` |
| Out of disk | Run `docker system prune -a` |
| Image not found | Verify tag: `docker search rajiup/cp-whisperx` |

---

## ⏱️ Approximate Times

| Operation | Time | Network |
|-----------|------|---------|
| Pull all images | 30-60 min | Required |
| Build all images | 60-90 min | Required (downloads packages) |
| Push all images | 40-80 min | Required |

*Times vary based on hardware and network speed*
