# Docker Build Optimization Guide

**Date:** November 4, 2025  
**Topic:** Build Order and Layer Caching Strategy

## Build Order Strategy

The `build-all-images` scripts follow a carefully optimized build order to maximize Docker layer caching and minimize total build time.

### Phase-Based Build Sequence

```
Phase 1: Base Images (CRITICAL - MUST SUCCEED)
├── base:cpu (1.34 GB)
└── base:cuda (13.9 GB)
    ↓
Phase 2: CPU-Only Stages (depend on base:cpu)
├── demux:cpu
├── tmdb:cpu
├── pre-ner:cpu
├── post-ner:cpu
├── subtitle-gen:cpu
└── mux:cpu
    ↓
Phase 3: GPU CUDA Stages (depend on base:cuda)
├── silero-vad:cuda
├── pyannote-vad:cuda
├── diarization:cuda
├── asr:cuda
├── second-pass-translation:cuda
└── lyrics-detection:cuda
    ↓
Phase 4: GPU CPU Fallbacks (depend on base:cpu)
├── silero-vad:cpu
├── pyannote-vad:cpu
├── diarization:cpu
├── asr:cpu
├── second-pass-translation:cpu
└── lyrics-detection:cpu
```

---

## Why This Order?

### 1. Base Images First (Phase 1)

**Critical Requirement:** All subsequent images depend on base images.

**Benefits:**
- ✅ Base layers are cached and reused by all stage images
- ✅ Prevents build failures due to missing base images
- ✅ Reduces total build time by 40-60%
- ✅ Reduces total image size due to layer sharing

**Example:**
```dockerfile
# Stage image references base image
FROM rajiup/cp-whisperx-app-base:cpu
# ↑ This must exist before building stage image
```

**If base images fail:**
- 🛑 Build process stops immediately
- 📋 Clear error message with dependencies listed
- ⚠️ Prevents wasted time building stages that will fail

### 2. CPU-Only Stages (Phase 2)

**Dependencies:** `base:cpu`

**Why second:**
- Smaller images (~1.3-1.8 GB each)
- Faster to build (no PyTorch compilation)
- Don't block GPU builds

**Parallel opportunity:** Could potentially build in parallel with Phase 3

### 3. GPU CUDA Stages (Phase 3)

**Dependencies:** `base:cuda`

**Why third:**
- Larger images (~1.5-3 GB each)
- PyTorch CUDA installation takes time
- Base:cuda is 13.9 GB and needs to be pulled/cached first

**Build time:** Longest phase due to PyTorch CUDA

### 4. GPU CPU Fallbacks (Phase 4)

**Dependencies:** `base:cpu` (already cached from Phase 1)

**Why last:**
- Reuses base:cpu layers (cache hit!)
- Generated automatically from CUDA Dockerfiles
- Quick to build since base:cpu already cached
- Optional safety net (can skip if time-limited)

---

## Layer Caching Benefits

### How Docker Layer Caching Works

Docker caches each instruction in a Dockerfile as a layer:

```dockerfile
FROM base:cpu              # Layer 1 (cached after base build)
RUN apt-get update         # Layer 2 (cached if apt-get unchanged)
RUN pip install numpy      # Layer 3 (cached if requirements unchanged)
COPY scripts/ /app/        # Layer 4 (rebuilt if scripts changed)
```

### Optimization Impact

**Without proper order:**
```
Build base:cpu         → 15 min
Build demux:cpu        → 10 min (+ 3 min waiting for base)
Build tmdb:cpu         → 10 min (+ 3 min waiting for base)
Total: 41 minutes
```

**With optimized order (base first):**
```
Build base:cpu         → 15 min
Build demux:cpu        → 2 min (layers cached from base!)
Build tmdb:cpu         → 2 min (layers cached from base!)
Total: 19 minutes
```

**Savings: ~50% reduction in build time**

---

## Build Time Estimates

### First Build (No Cache)

| Phase | Images | Time per Image | Total Time |
|-------|--------|----------------|------------|
| Phase 1 | 2 base | 15-30 min | 30-60 min |
| Phase 2 | 6 CPU | 2-5 min | 12-30 min |
| Phase 3 | 4-6 GPU CUDA | 5-15 min | 20-90 min |
| Phase 4 | 4-6 CPU fallback | 2-5 min | 8-30 min |
| **Total** | ~20 images | | **70-210 min** |

### Rebuild (With Cache)

| Phase | Images | Time per Image | Total Time |
|-------|--------|----------------|------------|
| Phase 1 | 2 base | <1 min (cached) | <2 min |
| Phase 2 | 6 CPU | <1 min (cached) | <6 min |
| Phase 3 | 4-6 GPU CUDA | 2-5 min | 8-30 min |
| Phase 4 | 4-6 CPU fallback | <1 min (cached) | <6 min |
| **Total** | ~20 images | | **16-44 min** |

**Note:** Rebuild time assumes only CUDA-specific code changed.

---

## Error Handling

### Base Image Build Failure

If a base image fails to build, the script:

1. **Stops immediately** ✋
2. **Shows clear error message** 📋
3. **Lists affected dependencies** 📊
4. **Exits with error code** ⛔

**Example error output:**
```
[FAILED] base:cpu
[ERROR] Cannot proceed without base:cpu image!
[ERROR] All CPU stages require base:cpu
[INFO] Required by: demux, tmdb, pre-ner, post-ner, subtitle-gen, mux
[INFO] Also required for GPU stage CPU fallbacks
```

### Stage Image Build Failure

If a stage image fails:

1. **Continues with other stages** ⏭️
2. **Tracks failed builds** 📝
3. **Shows summary at end** 📊
4. **Exits with error code** ⛔

**Why continue?** Some stages might still succeed and be usable.

---

## Disk Space Optimization

### Layer Sharing

All stage images share layers from base images:

```
base:cpu (1.34 GB)
├── demux:cpu           → +50 MB  (total: 1.39 GB)
├── tmdb:cpu            → +50 MB  (total: 1.39 GB)
├── pre-ner:cpu         → +400 MB (total: 1.74 GB)
└── post-ner:cpu        → +400 MB (total: 1.74 GB)

Actual disk usage: 1.34 + 0.05 + 0.05 + 0.4 + 0.4 = 2.24 GB
Without sharing:  1.39 + 1.39 + 1.74 + 1.74 = 6.26 GB
Savings: ~4 GB (64%)
```

### Total Disk Space

**All images (~20 total):**
```
Base images:    1.34 GB (cpu) + 13.9 GB (cuda)     = 15.24 GB
CPU stages:     6 × ~0.3 GB (incremental)          = ~1.8 GB
CUDA stages:    6 × ~1.0 GB (incremental)          = ~6 GB
CPU fallbacks:  6 × ~0.3 GB (incremental)          = ~1.8 GB
────────────────────────────────────────────────────────────────
Total:                                               ~25 GB
```

**Without layer sharing:** ~50-60 GB

**Savings:** ~50% reduction in disk usage

---

## Best Practices

### 1. Always Build Base Images First

✅ **DO:**
```bash
# Let script handle order
scripts\build-all-images.bat
```

❌ **DON'T:**
```bash
# Don't build stages before base
docker build -t rajiup/cp-whisperx-app-asr:cuda -f docker/asr/Dockerfile .
# ↑ This will fail if base:cuda doesn't exist!
```

### 2. Use Build Cache

✅ **DO:**
```bash
# Keep cache for faster rebuilds
docker build -t rajiup/cp-whisperx-app-base:cpu -f docker/base/Dockerfile .
```

❌ **DON'T:**
```bash
# Don't use --no-cache unless necessary
docker build --no-cache -t rajiup/cp-whisperx-app-base:cpu -f docker/base/Dockerfile .
# ↑ This throws away all cache benefits!
```

### 3. Update Base Images Sparingly

Base image changes invalidate ALL stage caches.

**When to update base:**
- Security patches required
- Python version upgrade needed
- Fundamental dependency changes

**When NOT to update base:**
- Stage-specific changes
- Configuration tweaks
- Script updates

### 4. Optimize Dockerfile Order

Put rarely-changing instructions first:

```dockerfile
# Good order
FROM base:cpu                          # Changes rarely
RUN apt-get update && apt-get install  # Changes rarely
COPY requirements.txt .                # Changes occasionally
RUN pip install -r requirements.txt    # Changes occasionally
COPY scripts/ /app/scripts/            # Changes frequently
```

---

## Troubleshooting

### "Base image not found" error

**Cause:** Tried to build stage before base

**Solution:**
```bash
# Build base first
docker build -t rajiup/cp-whisperx-app-base:cpu -f docker/base/Dockerfile .

# Or use the build script (recommended)
scripts\build-all-images.bat
```

### Slow builds despite cache

**Cause:** Base layers not cached

**Solution:**
```bash
# Ensure base images are tagged correctly
docker images | findstr "base"

# Should show:
# rajiup/cp-whisperx-app-base   cpu
# rajiup/cp-whisperx-app-base   cuda
```

### Out of disk space

**Cause:** Too many image layers

**Solution:**
```bash
# Clean up old images
docker system prune -a

# Remove unused images
docker image prune -a
```

### Build fails on specific stage

**Cause:** Missing dependencies or network issues

**Solution:**
```bash
# Check logs
docker build -t rajiup/cp-whisperx-app-asr:cuda -f docker/asr/Dockerfile .

# Try with verbose output
docker build --progress=plain -t rajiup/cp-whisperx-app-asr:cuda -f docker/asr/Dockerfile .
```

---

## Advanced Optimization

### Parallel Builds

For faster builds on multi-core systems:

```bash
# Phase 2 and 3 can run in parallel (after Phase 1)
# Terminal 1:
for stage in demux tmdb pre-ner post-ner subtitle-gen mux; do
    docker build -t rajiup/cp-whisperx-app-$stage:cpu -f docker/$stage/Dockerfile .
done

# Terminal 2 (simultaneously):
for stage in silero-vad pyannote-vad diarization asr; do
    docker build -t rajiup/cp-whisperx-app-$stage:cuda -f docker/$stage/Dockerfile .
done
```

### BuildKit Optimization

Enable Docker BuildKit for better caching:

```bash
# Windows
set DOCKER_BUILDKIT=1
scripts\build-all-images.bat

# Linux/Mac
export DOCKER_BUILDKIT=1
./scripts/build-all-images.sh
```

### Multi-Stage Builds

Already used in some Dockerfiles:

```dockerfile
# Build stage
FROM base:cpu as builder
RUN pip install --target=/install -r requirements.txt

# Runtime stage
FROM base:cpu
COPY --from=builder /install /usr/local
```

---

## Summary

**Key Points:**

1. ✅ Base images MUST be built first
2. ✅ Proper order saves 50% build time
3. ✅ Layer caching reduces disk usage by 50%
4. ✅ Scripts enforce correct build order
5. ✅ Build fails fast if base images fail

**Build Command:**
```bash
scripts\build-all-images.bat
```

**This automatically:**
- Builds base images first
- Uses layer caching
- Generates CPU fallbacks
- Handles errors properly
- Optimizes disk usage

**Ready to build efficiently!** 🚀
