# Docker Optimization Phase 2 - Implementation Plan

**Date:** November 5, 2025  
**Status:** READY TO START  
**Estimated Time:** 4-6 hours  
**Risk Level:** MEDIUM ⚠️

---

## Executive Summary

Phase 1 achieved quick wins with **zero risk** optimizations (`.dockerignore`, BuildKit cache mounts, image pinning). Phase 2 focuses on **structural changes** that require careful implementation but deliver significant benefits:

- **15-20 GB** image size reduction
- **10-15 min** build time savings
- Better layer caching strategy
- Cleaner dependency management

---

## Phase 2 Objectives

From `DOCKER_OPTIMIZATION_RECOMMENDATIONS.md`:

### 1. Create `base-ml` Image with PyTorch ✅ (Already Exists!)
**Status:** ✅ ALREADY IMPLEMENTED  
**Location:** `docker/base-ml/Dockerfile`

**Current Implementation:**
```dockerfile
FROM rajiup/cp-whisperx-app-base:cuda

RUN --mount=type=cache,id=pip-cache-base-ml,target=/root/.cache/pip \
    pip install --no-cache-dir \
    torch==2.1.0+cu121 \
    torchaudio==2.1.0+cu121 \
    --index-url https://download.pytorch.org/whl/cu121
```

**Verification Needed:**
- Check if all GPU stages use `base-ml:cuda` as base
- Verify PyTorch version consistency (2.1.0)

---

### 2. Update GPU Stages to Use `base-ml`
**Status:** ❌ NOT STARTED  
**Estimated Time:** 1 hour  
**Risk:** MEDIUM

**Current Problem:**
Many GPU stages reinstall PyTorch independently:
```dockerfile
# docker/asr/Dockerfile
FROM rajiup/cp-whisperx-app-base:cuda   # ❌ Should be base-ml:cuda
RUN pip install torch==2.2.1            # ❌ Redundant
```

**Target Stages:**
1. `docker/asr/Dockerfile` - Change base + remove torch install
2. `docker/diarization/Dockerfile` - Change base + remove torch install
3. `docker/pyannote-vad/Dockerfile` - Change base + remove torch install
4. `docker/silero-vad/Dockerfile` - Change base + remove torch install
5. `docker/lyrics-detection/Dockerfile` - Change base + remove torch install
6. `docker/second-pass-translation/Dockerfile` - Change base + remove torch install

**Expected Savings:** 12-18 GB total (2-3 GB per stage × 6 stages)

---

### 3. Enable BuildKit Cache Mounts (More Stages)
**Status:** ✅ PARTIALLY DONE  
**Estimated Time:** 30 min  
**Risk:** LOW

**Completed:**
- ✅ `base/Dockerfile`
- ✅ `base-cuda/Dockerfile`
- ✅ `base-ml/Dockerfile`

**Need to Add:**
- Stage Dockerfiles that install additional packages
- Check all `RUN pip install` lines
- Check all `RUN apt-get` lines

---

### 4. Split Requirements Files (Better Caching)
**Status:** ❌ NOT STARTED  
**Estimated Time:** 1.5 hours  
**Risk:** MEDIUM

**Current State:**
```
docker/requirements-common.txt  (single file for everything)
```

**Proposed Structure:**
```
docker/requirements-common.txt       # Utilities (dotenv, rich, pysubs2)
docker/requirements-ml.txt          # ML packages (numpy, scipy, transformers)
docker/requirements-audio.txt       # Audio packages (librosa, soundfile)
docker/asr/requirements.txt         # ASR-specific (whisperx, faster-whisper)
docker/diarization/requirements.txt # Diarization-specific (pyannote.audio)
docker/post-ner/requirements.txt    # NER-specific (spacy, transformers)
```

**Benefits:**
- Change to spaCy doesn't invalidate PyTorch layer
- Change to common utils doesn't invalidate ML packages
- Better cache hit rate during development

**Implementation:**
1. Analyze current `requirements-common.txt`
2. Categorize dependencies
3. Create separate files
4. Update Dockerfiles to install in order:
   ```dockerfile
   COPY docker/requirements-common.txt .
   RUN pip install -r requirements-common.txt
   
   COPY docker/requirements-ml.txt .
   RUN pip install -r requirements-ml.txt
   
   COPY docker/asr/requirements.txt .
   RUN pip install -r requirements.txt
   ```

---

### 5. Document Version Constraints Centrally
**Status:** ❌ NOT STARTED  
**Estimated Time:** 30 min  
**Risk:** LOW

**Create:** `docker/versions.txt`

**Purpose:**
- Single source of truth for all package versions
- Prevent version conflicts across stages
- Easier to update dependencies globally

**Example:**
```txt
# docker/versions.txt
# Centralized version management for all Docker images

# Core ML
torch==2.1.0+cu121
torchaudio==2.1.0+cu121
numpy==1.24.3
scipy==1.11.4

# Whisper ecosystem
whisperx==3.7.2
faster-whisper==1.2.0
ctranslate2==4.6.0

# Diarization
pyannote.audio==3.4.0
pyannote.core==5.0.0
speechbrain==1.0.1

# NER
spacy==3.8.7
transformers==4.57.1

# Common utilities
python-dotenv==1.2.1
rich==14.2.0
pysubs2==1.8.0
soundfile==0.12.1
```

**Usage:** Reference in requirements files with comments

---

### 6. Wheelhouse Builder for ML Images (Advanced)
**Status:** ❌ NOT STARTED  
**Estimated Time:** 2 hours  
**Risk:** MEDIUM-HIGH

**Problem:**
ML packages require build dependencies (gcc, g++, build-essential) during installation, but these are not needed at runtime.

**Solution:** Multi-stage build

**Before (current):**
```dockerfile
FROM rajiup/cp-whisperx-app-base:cuda
RUN apt-get install -y build-essential gcc g++  # 200+ MB
RUN pip install torch transformers pyannote.audio
# Final image: 4.5 GB (includes build tools)
```

**After (optimized):**
```dockerfile
# Stage 1: Builder
FROM rajiup/cp-whisperx-app-base:cuda AS builder

RUN apt-get install -y build-essential gcc g++
RUN pip wheel --no-cache-dir -w /wheels \
    torch==2.1.0+cu121 \
    torchaudio==2.1.0+cu121 \
    transformers==4.57.1 \
    pyannote.audio==3.4.0

# Stage 2: Runtime
FROM rajiup/cp-whisperx-app-base:cuda

COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/*.whl && \
    rm -rf /wheels

# Final image: 4.2 GB (300 MB saved)
```

**Expected Savings:** 200-300 MB per ML image (3 images × 300 MB = ~900 MB)

**Trade-offs:**
- More complex Dockerfile
- Longer initial build time (2 stages)
- Better for production, overkill for development

**Recommendation:** Implement for `base-ml` only, not per-stage

---

### 7. Shared Model Cache Volume
**Status:** ❌ NOT STARTED  
**Estimated Time:** 1 hour  
**Risk:** LOW

**Problem:**
ML models (Whisper, spaCy, pyannote) are downloaded during Docker build, baked into images.

**Impact:**
- Large images (models are 1-3 GB each)
- Slow builds (download every rebuild)
- Can't update models without rebuild

**Solution:**
Use `shared-model-and-cache/` as a mounted volume, download models at runtime.

**Implementation:**

#### Update `docker-compose.yml`:
```yaml
services:
  asr:
    image: rajiup/cp-whisperx-app-asr:cuda
    volumes:
      - ./shared-model-and-cache:/shared-model-and-cache
    environment:
      - HF_HOME=/shared-model-and-cache/huggingface
      - TRANSFORMERS_CACHE=/shared-model-and-cache/transformers
      - TORCH_HOME=/shared-model-and-cache/torch
      - WHISPER_CACHE=/shared-model-and-cache/whisper

  diarization:
    image: rajiup/cp-whisperx-app-diarization:cuda
    volumes:
      - ./shared-model-and-cache:/shared-model-and-cache
    environment:
      - HF_HOME=/shared-model-and-cache/huggingface
      - PYANNOTE_CACHE=/shared-model-and-cache/pyannote
```

#### Remove model downloads from Dockerfiles:
```dockerfile
# REMOVE these lines from stage Dockerfiles:
# RUN python -c "import whisper; whisper.load_model('large-v3')"
# RUN python -c "from pyannote.audio import Pipeline; ..."
```

#### Add runtime model initialization:
```python
# In stage scripts (e.g., docker/asr/transcribe.py)
import os
from pathlib import Path

# Ensure model cache directories exist
cache_dir = Path("/shared-model-and-cache")
(cache_dir / "huggingface").mkdir(parents=True, exist_ok=True)
(cache_dir / "whisper").mkdir(parents=True, exist_ok=True)

# Load model (downloads to cache if not present)
model = whisper.load_model("large-v3")
```

**Benefits:**
- Smaller images (remove 1-3 GB of models per stage)
- Faster builds (no model downloads)
- Easier model updates (just delete cache, restart)
- Single model download shared across all containers

**Expected Savings:** 5-10 GB total image size

---

## Implementation Order

### Recommended Sequence:

1. **Start with #7 (Model Cache)** - 1 hour, LOW risk, HIGH impact
   - Immediate image size reduction
   - No Dockerfile changes (just docker-compose.yml)
   - Easy to test and rollback

2. **Then #2 (Use base-ml)** - 1 hour, MEDIUM risk, HIGH impact
   - Verify `base-ml:cuda` exists and works
   - Update 6 GPU stage Dockerfiles
   - Test each stage individually

3. **Then #4 (Split Requirements)** - 1.5 hours, MEDIUM risk, MEDIUM impact
   - Better caching strategy
   - Requires careful dependency analysis
   - Test build times before/after

4. **Then #5 (Document Versions)** - 30 min, LOW risk, LOW impact
   - Documentation improvement
   - Helps with maintenance

5. **Optional: #6 (Wheelhouse)** - 2 hours, MEDIUM-HIGH risk, LOW-MEDIUM impact
   - Only if you need the extra 900 MB savings
   - Most complex change
   - Best for production deployments

6. **Already Done: #3 (BuildKit Cache)** - ✅ COMPLETE

---

## Testing Strategy

### Pre-Implementation Baseline

```powershell
# 1. Measure current state
docker images | grep cp-whisperx-app | awk '{sum+=$7} END {print sum " MB total"}'

# 2. Time a full rebuild
$start = Get-Date
.\scripts\build-all-images.ps1
$duration = (Get-Date) - $start
Write-Host "Build time: $duration"

# 3. Document current sizes
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep cp-whisperx-app > before-phase2.txt
```

### Per-Change Testing

After each change:

```powershell
# 1. Build affected images
.\scripts\build-all-images.ps1

# 2. Test individual stage
docker run --rm rajiup/cp-whisperx-app-asr:cuda --help

# 3. Run integration test
python prepare-job.py in/test-short.mp4
python pipeline.py --job <job-id>
```

### Post-Implementation Validation

```powershell
# 1. Full rebuild
.\scripts\build-all-images.ps1

# 2. Measure improvements
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep cp-whisperx-app > after-phase2.txt

# 3. Compare
Write-Host "=== Before Phase 2 ==="
Get-Content before-phase2.txt

Write-Host "=== After Phase 2 ==="
Get-Content after-phase2.txt

# 4. Full pipeline test
python prepare-job.py in/test-movie.mp4 --tmdb-id 12345
python pipeline.py --workflow subtitle
```

---

## Risk Mitigation

### Git Backup Before Each Step

```powershell
# Before making changes
git add .
git commit -m "Pre-Phase2: Backup before optimization"
git tag phase2-backup-$(Get-Date -Format "yyyyMMdd-HHmmss")
```

### Rollback Plan

```powershell
# If something breaks
git reset --hard phase2-backup-<timestamp>
git clean -fd

# Rebuild from backup state
.\scripts\build-all-images.ps1
```

### Incremental Changes

- Implement ONE change at a time
- Test thoroughly before proceeding
- Commit after each successful change
- Keep detailed notes of issues

---

## Expected Results

### Image Size Reduction

| Stage | Before | After | Savings |
|-------|--------|-------|---------|
| base-ml:cuda | 4.5 GB | 4.5 GB | 0 GB (baseline) |
| asr:cuda | 6.8 GB | 4.8 GB | **-2.0 GB** |
| diarization:cuda | 7.2 GB | 5.0 GB | **-2.2 GB** |
| pyannote-vad:cuda | 6.5 GB | 4.8 GB | **-1.7 GB** |
| silero-vad:cuda | 5.8 GB | 4.6 GB | **-1.2 GB** |
| lyrics-detection:cuda | 6.0 GB | 4.7 GB | **-1.3 GB** |
| second-pass-translation:cuda | 6.2 GB | 4.8 GB | **-1.4 GB** |
| **Total** | **43.0 GB** | **33.2 GB** | **-9.8 GB** |

**Additional savings from model cache volume:** -5 GB  
**Grand Total Savings:** **~15 GB** (35% reduction)

### Build Time Improvement

| Scenario | Before | After | Savings |
|----------|--------|-------|---------|
| **Cold build (no cache)** | 45-60 min | 30-40 min | **15-20 min** |
| **Warm rebuild (change common deps)** | 15-20 min | 8-12 min | **7-8 min** |
| **Hot rebuild (change stage code)** | 5-8 min | 3-5 min | **2-3 min** |

### Developer Experience

- ✅ Faster iteration cycles
- ✅ Smaller registry storage costs
- ✅ Easier dependency management
- ✅ Better CI/CD performance
- ✅ Clearer image hierarchy

---

## Success Criteria

### Must Have ✅
- [ ] All images build successfully
- [ ] All stages pass functional tests
- [ ] Full pipeline completes end-to-end
- [ ] Image sizes reduced by at least 10 GB
- [ ] Build time reduced by at least 10 minutes

### Nice to Have ⭐
- [ ] Documentation updated
- [ ] Version constraints documented
- [ ] Build scripts include timing
- [ ] Automated tests for each stage

### Red Flags 🚨
- Images larger than before
- Build failures
- Pipeline errors
- Slower build times

---

## Phase 2 Checklist

### Before Starting
- [ ] Read this document completely
- [ ] Review Phase 1 results (DOCKER_OPTIMIZATION_STATUS.md)
- [ ] Create git backup
- [ ] Measure baseline (image sizes, build times)

### Implementation
- [ ] **#7: Shared Model Cache** (1 hour)
  - [ ] Update docker-compose.yml
  - [ ] Remove model downloads from Dockerfiles
  - [ ] Add runtime model init
  - [ ] Test with one stage
  - [ ] Test with full pipeline
  - [ ] Commit changes

- [ ] **#2: Use base-ml** (1 hour)
  - [ ] Verify base-ml:cuda exists
  - [ ] Update asr/Dockerfile
  - [ ] Update diarization/Dockerfile
  - [ ] Update pyannote-vad/Dockerfile
  - [ ] Update silero-vad/Dockerfile
  - [ ] Update lyrics-detection/Dockerfile
  - [ ] Update second-pass-translation/Dockerfile
  - [ ] Test each stage
  - [ ] Commit changes

- [ ] **#4: Split Requirements** (1.5 hours)
  - [ ] Analyze requirements-common.txt
  - [ ] Create requirements-ml.txt
  - [ ] Create requirements-audio.txt
  - [ ] Create stage-specific requirements.txt files
  - [ ] Update Dockerfiles to install in layers
  - [ ] Test builds
  - [ ] Measure cache improvements
  - [ ] Commit changes

- [ ] **#5: Document Versions** (30 min)
  - [ ] Create docker/versions.txt
  - [ ] Document all package versions
  - [ ] Add comments to requirements files
  - [ ] Update README if needed
  - [ ] Commit changes

- [ ] **#6: Wheelhouse (Optional)** (2 hours)
  - [ ] Convert base-ml/Dockerfile to multi-stage
  - [ ] Test build
  - [ ] Measure size reduction
  - [ ] Test all GPU stages
  - [ ] Commit if successful, revert if not

### After Completion
- [ ] Full rebuild and timing
- [ ] Measure final image sizes
- [ ] Run full integration test
- [ ] Update DOCKER_OPTIMIZATION_STATUS.md
- [ ] Create DOCKER_PHASE2_SUMMARY.md
- [ ] Git commit and tag

---

## Timeline

### Minimum (Core Changes Only)
**Time:** 3.5 hours  
**Items:** #7, #2, #5  
**Savings:** ~12 GB, ~12 min build time

### Recommended (Core + Optimization)
**Time:** 5 hours  
**Items:** #7, #2, #4, #5  
**Savings:** ~15 GB, ~15 min build time

### Maximum (Everything)
**Time:** 7 hours  
**Items:** #7, #2, #4, #5, #6  
**Savings:** ~16 GB, ~18 min build time

---

## Notes for Implementation

### Common Issues to Watch For

1. **PyTorch version compatibility**
   - Ensure all stages use same PyTorch version (2.1.0)
   - Check for version-specific API changes

2. **Model cache permissions**
   - Ensure `shared-model-and-cache/` is writable
   - Set correct ownership in containers

3. **Build context changes**
   - `.dockerignore` already configured (Phase 1)
   - Ensure necessary files not excluded

4. **Cache invalidation**
   - Keep frequently changing files in later layers
   - Test cache hit rates

### Useful Commands

```powershell
# Check image sizes
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep cp-whisperx-app

# Check layer sizes
docker history rajiup/cp-whisperx-app-asr:cuda

# Build with timing
Measure-Command { .\scripts\build-all-images.ps1 }

# Test single stage
docker run --rm -it rajiup/cp-whisperx-app-asr:cuda /bin/bash
```

---

## Questions to Resolve

1. **Should we implement wheelhouse builder (#6)?**
   - Pro: 900 MB savings, cleaner images
   - Con: 2 hours work, more complexity
   - **Recommendation:** Skip for now, revisit if needed

2. **Which requirements should go in which file?**
   - Needs analysis of current dependencies
   - Create dependency graph
   - Group by functionality and change frequency

3. **Should we keep model downloads as fallback?**
   - Pro: Works even if volume mount fails
   - Con: Larger images
   - **Recommendation:** Remove from Dockerfile, handle in runtime script

---

## Success Metrics

Track these metrics before and after:

### Image Metrics
- Total size of all images
- Size of each GPU stage
- Number of layers per image
- Base image sizes

### Build Metrics
- Cold build time (no cache)
- Warm rebuild time (cached base)
- Hot rebuild time (code change only)
- Registry push time

### Runtime Metrics
- Container startup time
- First model load time
- Pipeline completion time

---

## Next Steps

1. **Review this plan with team/stakeholder**
2. **Get approval to proceed**
3. **Set aside 4-6 hour block for implementation**
4. **Start with #7 (easiest win)**
5. **Document results as you go**

---

**Document Owner:** DevOps Team  
**Last Updated:** November 5, 2025  
**Next Review:** After Phase 2 completion

**Status:** READY TO IMPLEMENT 🚀
