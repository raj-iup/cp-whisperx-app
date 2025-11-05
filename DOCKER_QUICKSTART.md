# 🚀 Docker Quick Start Guide

**For**: CP-WhisperX-App  
**Updated**: 2025-01-04

---

## ⚡ Quick Commands

### Build Everything
```batch
scripts\build-all-images.bat
```
⏱️ **Time**: 60-90 minutes | **Disk**: ~50-60 GB

### Pull Everything
```batch
scripts\pull-all-images.bat
```
⏱️ **Time**: 5-10 minutes | **Disk**: ~50-60 GB

### Push to Registry
```batch
docker login
scripts\push-all-images.bat
```

---

## 🏷️ Image Tags Quick Reference

| Stage | CPU Tag | CUDA Tag | Required? |
|-------|---------|----------|-----------|
| **Base Images** | | | |
| Base | `:cpu` | `:cuda` | ✅ Always |
| ML Base | - | `:cuda` | ✅ For GPU stages |
| **CPU-Only Stages** | | | |
| Demux | `:cpu` | - | ✅ Always |
| TMDB | `:cpu` | - | ✅ Always |
| Pre-NER | `:cpu` | - | ✅ Always |
| Post-NER | `:cpu` | - | ✅ Always |
| Subtitle Gen | `:cpu` | - | ✅ Always |
| Mux | `:cpu` | - | ✅ Always |
| **GPU Stages** | | | |
| Silero VAD | `:cpu` | `:cuda` | ⚠️ If using VAD |
| PyAnnote VAD | `:cpu` | `:cuda` | ⚠️ If using VAD |
| Diarization | `:cpu` | `:cuda` | ✅ Always |
| ASR | `:cpu` | `:cuda` | ✅ Always |
| 2nd Pass Trans | `:cpu` | `:cuda` | ⚠️ Optional |
| Lyrics Detect | `:cpu` | `:cuda` | ⚠️ Optional |

---

## 🎯 Minimal Image Set

### For CPU-Only Systems
```batch
REM Pull just what you need (9 images)
docker pull rajiup/cp-whisperx-app-base:cpu
docker pull rajiup/cp-whisperx-app-demux:cpu
docker pull rajiup/cp-whisperx-app-tmdb:cpu
docker pull rajiup/cp-whisperx-app-pre-ner:cpu
docker pull rajiup/cp-whisperx-app-diarization:cpu
docker pull rajiup/cp-whisperx-app-asr:cpu
docker pull rajiup/cp-whisperx-app-post-ner:cpu
docker pull rajiup/cp-whisperx-app-subtitle-gen:cpu
docker pull rajiup/cp-whisperx-app-mux:cpu
```

### For CUDA/GPU Systems
```batch
REM Pull GPU + CPU fallbacks (15 images)
scripts\pull-all-images.bat
```

---

## 🔥 Common Workflows

### 1. First Time Setup (Build)
```batch
cd C:\Users\rpate\Projects\cp-whisperx-app
scripts\build-all-images.bat
```

### 2. Update from Registry
```batch
scripts\pull-all-images.bat
```

### 3. Test Single Stage
```batch
REM CPU test
docker run --rm rajiup/cp-whisperx-app-demux:cpu --help

REM CUDA test
docker run --rm --gpus all rajiup/cp-whisperx-app-asr:cuda --help
```

### 4. Clean Up Old Images
```batch
REM Remove all old cp-whisperx-app images
docker images | findstr "rajiup/cp-whisperx-app" | ForEach-Object { docker rmi $_.Split()[2] }

REM Or full cleanup
docker system prune -a
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Build fails on base:cuda | Wait longer (15-20 min), or pull instead |
| Out of disk space | Run `docker system prune -a` |
| Can't find GPU | Use `:cpu` tagged images instead |
| Pull fails | Check Docker login: `docker login` |
| Wrong registry | Set `DOCKER_REGISTRY` env var |

---

## 📦 Image Size Reference

| Image Type | Approximate Size |
|------------|------------------|
| base:cpu | ~1-2 GB |
| base:cuda | ~8-10 GB |
| base-ml:cuda | ~15-18 GB |
| CPU stage | ~1.5-2.5 GB |
| CUDA stage | ~16-20 GB |
| **Total (all 21)** | **~50-60 GB** |

---

## 🔗 Script Locations

| Script | Windows | Linux/Mac |
|--------|---------|-----------|
| Build All | `scripts\build-all-images.bat` | `scripts/build-all-images.sh` |
| Pull All | `scripts\pull-all-images.bat` | `scripts/pull-all-images.sh` |
| Push All | `scripts\push-all-images.bat` | `scripts/push-all-images.sh` |

---

## 📋 Pre-Build Checklist

- [ ] Docker Desktop running
- [ ] ~60 GB free disk space
- [ ] GPU drivers installed (for CUDA images)
- [ ] Internet connection (for pulling base images)
- [ ] Time available (60-90 min for full build)

---

## ✅ Post-Build Validation

```batch
REM Count images
docker images | findstr "rajiup/cp-whisperx-app" | find /c /v ""

REM Should show: 21

REM Test CPU stage
docker run --rm rajiup/cp-whisperx-app-base:cpu python3 --version

REM Test CUDA stage (requires GPU)
docker run --rm --gpus all rajiup/cp-whisperx-app-base:cuda python3 --version
```

---

## 🎓 Need More Info?

See comprehensive documentation:
- `DOCKER_BUILD_SUMMARY.md` - Complete overview
- `DOCKER_BUILD_STATUS.md` - Current status
- `DOCKER_BUILD_FIXES.md` - Technical fixes
- `docs/DOCKER_OPTIMIZATION_RECOMMENDATIONS.md` - Optimization guide

---

**Happy Building!** 🎉
