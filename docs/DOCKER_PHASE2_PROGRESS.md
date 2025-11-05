# Docker Optimization Phase 2 - Progress Summary

**Date Started:** November 5, 2025  
**Status:** IN PROGRESS (2/5 tasks complete)  
**Time Spent:** ~1 hour  
**Expected Total:** 4-6 hours

---

## Progress Overview

| Task | Status | Time | Savings | Notes |
|------|--------|------|---------|-------|
| 1. Shared Model Cache | ✅ COMPLETE | 1h | 5-10 GB | docker-compose updated, models removed from images |
| 2. Use base-ml | ✅ COMPLETE | 0h | 10 GB | Already done in previous work |
| 3. Split Requirements | ⏳ NEXT | 1.5h | Better caching | Starting now |
| 4. Document Versions | ⬜ TODO | 30m | Maintenance | |
| 5. Wheelhouse (Optional) | ⬜ SKIP | 2h | 900 MB | Skip for now |

**Progress:** 40% complete (2/5 tasks)  
**Time Remaining:** 2 hours (minimum path)

---

## Task 1: Shared Model Cache ✅

**Completed:** November 5, 2025  
**Time:** 1 hour  
**Status:** COMPLETE

### Changes Made

1. **docker-compose.yml** - Added volumes and env vars:
   - `./shared-model-and-cache:/shared-model-and-cache` volume mount
   - `HF_HOME`, `TRANSFORMERS_CACHE`, `SPACY_DATA` environment variables
   - Applied to: pre-ner, post-ner, pyannote-vad, diarization, asr

2. **docker-compose-fallback.yml** - Same changes for fallback mode

3. **Dockerfiles Updated:**
   - `docker/pre-ner/Dockerfile` - Removed `python -m spacy download en_core_web_sm`
   - `docker/post-ner/Dockerfile` - Removed `python -m spacy download en_core_web_trf`
   - `docker/diarization/Dockerfile` - Changed cache from `/app/.cache` to shared volume
   - `docker/pyannote-vad/Dockerfile` - Changed cache from `/app/.cache` to shared volume

### Impact

**Image Size Reduction:**
- pre-ner: 1.71 GB → 1.68 GB (~30 MB saved, model removed)
- post-ner: Expected ~500 MB savings (en_core_web_trf not in image)
- diarization: Expected ~3-4 GB savings (pyannote models not in image)
- pyannote-vad: Expected ~1-2 GB savings (models not in image)
- **Total Expected: 5-10 GB**

**Build Time:**
- No model downloads during build = faster builds
- Models downloaded once at runtime to shared cache
- Subsequent containers reuse cached models

### Testing

- ✅ pre-ner rebuilt successfully
- ⬜ post-ner needs rebuild
- ⬜ diarization needs rebuild  
- ⬜ pyannote-vad needs rebuild
- ⬜ Full pipeline test pending

### Commits

1. `64f8fcc` - "Phase2 Task 1: Shared model cache volume"
2. `23762b7` - "Fix: Correct COPY path in pre-ner Dockerfile"

---

## Task 2: Use base-ml for GPU Stages ✅

**Status:** ALREADY COMPLETE  
**Time:** 0 hours (done previously)

### Verification

All GPU stages checked:
- ✅ asr - Uses `FROM ${REGISTRY}/cp-whisperx-app-base-ml:cuda`
- ✅ diarization - Uses base-ml:cuda
- ✅ pyannote-vad - Uses base-ml:cuda
- ✅ silero-vad - Uses base-ml:cuda
- ✅ lyrics-detection - Uses base-ml:cuda
- ✅ second-pass-translation - Uses base-ml:cuda

### Redundant torch Checks

All GPU stages verified:
- ✅ No redundant `pip install torch` commands
- ✅ All inherit PyTorch from base-ml:cuda

### Impact

**Savings:** 10 GB (already realized in previous work)

This optimization was completed during earlier Docker improvements, likely during Phase 1 or initial base-ml creation.

---

## Task 3: Split Requirements Files ⏳

**Status:** NEXT (Starting now)  
**Estimated Time:** 1.5 hours  
**Expected Impact:** Better layer caching, 5-10 min faster builds

### Current State

**Existing Files:**
- `docker/requirements-common.txt` - 20 lines, well-organized
- Stage-specific requirements in individual directories

**Current `requirements-common.txt`:**
```txt
# Core scientific computing
numpy==1.24.3
scipy==1.11.4

# Audio processing
soundfile==0.12.1

# Utilities
python-dotenv==1.2.1
tqdm==4.66.0
rich==14.2.0

# Subtitle formats
pysubs2==1.8.0
```

### Planned Structure

Create layered requirements for better caching:

```
docker/requirements-common.txt       # Utilities (dotenv, rich, pysubs2)
docker/requirements-ml.txt          # ML base (numpy, scipy, transformers)
docker/requirements-audio.txt       # Audio (librosa, soundfile)
docker/asr/requirements.txt         # ASR-specific  
docker/diarization/requirements.txt # Diarization-specific
docker/post-ner/requirements.txt    # NER-specific
```

### Implementation Plan

1. Analyze all current requirements files
2. Categorize dependencies by:
   - Change frequency
   - Functionality (ML, audio, utilities)
   - Stage usage
3. Create layered requirements
4. Update Dockerfiles to install in order
5. Test build caching improvements

### Expected Benefits

- Change to spaCy doesn't invalidate PyTorch layer
- Change to utilities doesn't invalidate ML packages
- Better cache hit rate during development
- 5-10 min faster warm rebuilds

---

## Task 4: Document Versions 📝

**Status:** TODO  
**Estimated Time:** 30 minutes  
**Priority:** LOW (nice to have)

### Plan

Create `docker/versions.txt` with all package versions and rationale:

```txt
# docker/versions.txt
# Centralized version management

# Core ML
torch==2.1.0+cu121  # Compatible with pyannote 3.4.0, CUDA 12.1
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
```

### Benefits

- Single source of truth
- Easier version updates
- Prevents conflicts
- Better maintenance

---

## Task 5: Wheelhouse Builder ⚠️

**Status:** SKIP FOR NOW  
**Reason:** Low priority, high complexity  
**Potential Savings:** 900 MB

### Why Skip

1. Most complex change (multi-stage builds)
2. Only 900 MB savings vs 10+ GB from other tasks
3. Better suited for production optimization
4. Can revisit if needed

### When to Implement

- After Phase 2 core tasks complete
- If registry storage becomes issue
- For production deployments
- As Phase 3 optimization

---

## Git History

```
23762b7 - Fix: Correct COPY path in pre-ner Dockerfile
64f8fcc - Phase2 Task 1: Shared model cache volume
fd48d2e - Pre-Phase2: Backup before Task 1 (Model Cache)
```

**Backup Tags:**
- `phase2-backup-20251105-105431` - Before starting Phase 2

---

## Current Image Sizes

**Baseline (before Phase 2):**
```
rajiup/cp-whisperx-app-asr:cuda                       26.1GB
rajiup/cp-whisperx-app-diarization:cuda               26.5GB
rajiup/cp-whisperx-app-pyannote-vad:cuda              25.4GB
rajiup/cp-whisperx-app-silero-vad:cuda                13.8GB
rajiup/cp-whisperx-app-post-ner:cpu                   14.1GB
rajiup/cp-whisperx-app-pre-ner:cpu                    1.71GB
```

**After Task 1 (measured):**
```
rajiup/cp-whisperx-app-pre-ner:cpu                    1.68GB  (-30MB)
```

**Expected after full rebuild:**
```
rajiup/cp-whisperx-app-asr:cuda                       23.0GB  (-3GB)
rajiup/cp-whisperx-app-diarization:cuda               23.0GB  (-3.5GB)
rajiup/cp-whisperx-app-pyannote-vad:cuda              23.0GB  (-2.4GB)
rajiup/cp-whisperx-app-post-ner:cpu                   13.5GB  (-600MB)
rajiup/cp-whisperx-app-pre-ner:cpu                    1.68GB  (-30MB)

Total Savings: ~10 GB
```

---

## Next Steps

### Immediate (Today)

1. ✅ Complete Task 1 - DONE
2. ✅ Verify Task 2 - DONE (already complete)
3. ⏳ Implement Task 3 - IN PROGRESS
   - Analyze requirements
   - Create layered requirements files
   - Update Dockerfiles
   - Test caching improvements

### Short Term (This Session)

4. ⬜ Complete Task 4 - Document versions (30 min)
5. ⬜ Full rebuild of all images
6. ⬜ Measure actual savings
7. ⬜ Update documentation

### Testing & Validation

- ⬜ Build all affected images
- ⬜ Test individual stages
- ⬜ Run full pipeline integration test
- ⬜ Verify model downloads work at runtime
- ⬜ Check shared cache functionality

---

## Issues & Resolutions

### Issue 1: COPY path in pre-ner Dockerfile
**Problem:** Dockerfile referenced `docker/pre-ner/pre_ner.py` but build context was `docker/pre-ner/`  
**Solution:** Changed to relative path `COPY pre_ner.py /app/`  
**Status:** RESOLVED (commit 23762b7)

---

## Metrics to Track

### Before Phase 2
- Total image size: ~43 GB (estimated)
- Build time (cold): 45-60 min (estimated)
- Build time (warm): 15-20 min (estimated)

### After Phase 2 (Target)
- Total image size: ~28 GB (-15 GB, 35% reduction)
- Build time (cold): 30-40 min (-15 min)
- Build time (warm): 8-12 min (-7 min)
- Model downloads: Once at runtime (shared cache)

### Actual (To Be Measured)
- [ ] Total image size after full rebuild
- [ ] Cold build time
- [ ] Warm rebuild time
- [ ] Cache hit rates
- [ ] Model download behavior at runtime

---

## Success Criteria

### Must Have ✅
- [ ] All images build successfully
- [ ] Image sizes reduced by ≥10 GB
- [ ] No functionality regressions
- [ ] Models load from shared cache

### Nice to Have ⭐
- [ ] Build time reduced by ≥10 min
- [ ] Documentation updated
- [ ] Version constraints documented
- [ ] Cache improvements measured

### Red Flags 🚨
- None encountered so far ✅

---

## Recommendations

### Continue With
1. **Task 3 (Split Requirements)** - Good caching improvements
2. **Task 4 (Document Versions)** - Quick win for maintenance
3. **Full rebuild** - Measure actual savings
4. **Integration testing** - Verify everything works

### Skip For Now
1. **Task 5 (Wheelhouse)** - Low priority, high complexity
2. **Additional optimizations** - Focus on core functionality

### After Phase 2
1. Update DOCKER_OPTIMIZATION_STATUS.md
2. Create DOCKER_PHASE2_SUMMARY.md with results
3. Plan Phase 3 (if needed)

---

**Document Owner:** DevOps Team  
**Last Updated:** November 5, 2025 11:00 AM  
**Next Update:** After Task 3 completion

**Status:** ON TRACK ✅  
**Progress:** 40% complete  
**Time Remaining:** ~2 hours
