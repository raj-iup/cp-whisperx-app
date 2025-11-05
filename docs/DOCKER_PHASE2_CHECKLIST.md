# Docker Phase 2 - Quick Checklist

**Estimated Time:** 4-6 hours  
**Expected Savings:** 15 GB images, 15 min build time

---

## Pre-Flight ✈️

- [ ] Read `DOCKER_PHASE2_PLAN.md` completely
- [ ] Create git backup: `git commit -m "Pre-Phase2 backup"`
- [ ] Tag backup: `git tag phase2-backup-$(Get-Date -Format "yyyyMMdd-HHmmss")`
- [ ] Measure baseline:
  ```powershell
  docker images | grep cp-whisperx-app > before-phase2.txt
  Measure-Command { .\scripts\build-all-images.ps1 } > build-time-before.txt
  ```

---

## Task 1: Shared Model Cache (1 hour) 🎯 EASIEST WIN

### Files to Modify
- [ ] `docker-compose.yml`
- [ ] `docker-compose-fallback.yml`
- [ ] `docker/asr/transcribe.py` (runtime init)
- [ ] `docker/diarization/diarize.py` (runtime init)
- [ ] `docker/post-ner/post_ner.py` (runtime init)

### Steps
1. [ ] Update docker-compose.yml with volume mounts:
   ```yaml
   volumes:
     - ./shared-model-and-cache:/shared-model-and-cache
   environment:
     - HF_HOME=/shared-model-and-cache/huggingface
     - TRANSFORMERS_CACHE=/shared-model-and-cache/transformers
   ```

2. [ ] Remove model downloads from Dockerfiles:
   - [ ] `docker/asr/Dockerfile` - Remove whisper download
   - [ ] `docker/diarization/Dockerfile` - Remove pyannote download
   - [ ] `docker/post-ner/Dockerfile` - Remove spacy download

3. [ ] Add runtime initialization to stage scripts:
   ```python
   # Ensure cache exists
   cache_dir = Path("/shared-model-and-cache")
   cache_dir.mkdir(parents=True, exist_ok=True)
   ```

4. [ ] Test:
   ```powershell
   docker-compose build asr
   docker-compose run --rm asr --help
   ```

5. [ ] Commit: `git commit -m "Phase2: Shared model cache"`

**Expected Savings:** 5-10 GB

---

## Task 2: Use base-ml for GPU Stages (1 hour) 🎯 HIGH IMPACT

### Files to Modify (6 Dockerfiles)
- [ ] `docker/asr/Dockerfile`
- [ ] `docker/diarization/Dockerfile`
- [ ] `docker/pyannote-vad/Dockerfile`
- [ ] `docker/silero-vad/Dockerfile`
- [ ] `docker/lyrics-detection/Dockerfile`
- [ ] `docker/second-pass-translation/Dockerfile`

### Steps for EACH file

1. [ ] Change FROM line:
   ```dockerfile
   # Before
   FROM rajiup/cp-whisperx-app-base:cuda
   
   # After
   FROM rajiup/cp-whisperx-app-base-ml:cuda
   ```

2. [ ] Remove redundant PyTorch installs:
   ```dockerfile
   # REMOVE lines like:
   # RUN pip install torch==2.x.x
   # RUN pip install torchaudio==2.x.x
   ```

3. [ ] Keep stage-specific packages:
   ```dockerfile
   # KEEP lines like:
   RUN pip install whisperx==3.7.2 faster-whisper==1.2.0
   ```

4. [ ] Test each stage after modifying:
   ```powershell
   docker build -t rajiup/cp-whisperx-app-asr:cuda docker/asr/
   docker run --rm --gpus all rajiup/cp-whisperx-app-asr:cuda --help
   ```

5. [ ] Commit after ALL stages done:
   ```powershell
   git add docker/asr docker/diarization docker/pyannote-vad docker/silero-vad docker/lyrics-detection docker/second-pass-translation
   git commit -m "Phase2: Use base-ml for GPU stages"
   ```

**Expected Savings:** 10 GB (6 stages × 1.5-2 GB each)

---

## Task 3: Split Requirements Files (1.5 hours) 🎯 BETTER CACHING

### Files to Create
- [ ] `docker/requirements-ml.txt`
- [ ] `docker/requirements-audio.txt`
- [ ] `docker/asr/requirements.txt`
- [ ] `docker/diarization/requirements.txt`
- [ ] `docker/post-ner/requirements.txt`

### Steps

1. [ ] Analyze current `docker/requirements-common.txt`
2. [ ] Create `docker/requirements-ml.txt`:
   ```txt
   numpy==1.24.3
   scipy==1.11.4
   transformers==4.57.1
   huggingface-hub==0.20.3
   ```

3. [ ] Create `docker/requirements-audio.txt`:
   ```txt
   soundfile==0.12.1
   librosa==0.10.1
   pysubs2==1.8.0
   ```

4. [ ] Move stage-specific to per-stage files:
   ```txt
   # docker/asr/requirements.txt
   whisperx==3.7.2
   faster-whisper==1.2.0
   ctranslate2==4.6.0
   ```

5. [ ] Update Dockerfiles to install in layers:
   ```dockerfile
   # Install in order: common → ML → audio → stage
   COPY docker/requirements-common.txt .
   RUN --mount=type=cache,target=/root/.cache/pip \
       pip install -r requirements-common.txt
   
   COPY docker/requirements-ml.txt .
   RUN --mount=type=cache,target=/root/.cache/pip \
       pip install -r requirements-ml.txt
   
   COPY docker/asr/requirements.txt .
   RUN --mount=type=cache,target=/root/.cache/pip \
       pip install -r requirements.txt
   ```

6. [ ] Test build with cache:
   ```powershell
   # First build
   docker build -t test docker/asr/
   
   # Change common.txt, rebuild - should use ML cache
   docker build -t test docker/asr/
   ```

7. [ ] Commit:
   ```powershell
   git add docker/requirements-*.txt docker/*/requirements.txt docker/*/Dockerfile
   git commit -m "Phase2: Split requirements for better caching"
   ```

**Expected Savings:** 5-10 min build time (better cache hits)

---

## Task 4: Document Versions (30 min) 📝 MAINTENANCE

### Files to Create
- [ ] `docker/versions.txt`

### Steps

1. [ ] Create central version file:
   ```txt
   # docker/versions.txt
   # Central version management
   
   # Core ML
   torch==2.1.0+cu121
   torchaudio==2.1.0+cu121
   numpy==1.24.3
   
   # Whisper
   whisperx==3.7.2
   faster-whisper==1.2.0
   
   # Diarization
   pyannote.audio==3.4.0
   speechbrain==1.0.1
   
   # NER
   spacy==3.8.7
   transformers==4.57.1
   ```

2. [ ] Add comments to requirements files:
   ```txt
   # See docker/versions.txt for version rationale
   torch==2.1.0+cu121  # Compatible with pyannote 3.4.0
   ```

3. [ ] Update README if needed

4. [ ] Commit:
   ```powershell
   git add docker/versions.txt
   git commit -m "Phase2: Central version documentation"
   ```

**Expected Savings:** Easier maintenance, prevents future conflicts

---

## Task 5: Wheelhouse Builder (2 hours) ⚠️ OPTIONAL

**Skip this unless you need the extra 900 MB savings**

### File to Modify
- [ ] `docker/base-ml/Dockerfile`

### Steps

1. [ ] Convert to multi-stage build:
   ```dockerfile
   # Stage 1: Builder
   FROM rajiup/cp-whisperx-app-base:cuda AS builder
   
   RUN apt-get update && apt-get install -y build-essential
   RUN pip wheel --no-cache-dir -w /wheels \
       torch==2.1.0+cu121 \
       torchaudio==2.1.0+cu121
   
   # Stage 2: Runtime
   FROM rajiup/cp-whisperx-app-base:cuda
   
   COPY --from=builder /wheels /wheels
   RUN pip install --no-index --find-links=/wheels /wheels/*.whl
   ```

2. [ ] Test build:
   ```powershell
   docker build -t rajiup/cp-whisperx-app-base-ml:cuda docker/base-ml/
   docker history rajiup/cp-whisperx-app-base-ml:cuda  # Check size
   ```

3. [ ] Test dependent stages:
   ```powershell
   docker build -t rajiup/cp-whisperx-app-asr:cuda docker/asr/
   ```

4. [ ] If successful, commit. If issues, revert:
   ```powershell
   # Success
   git commit -m "Phase2: Wheelhouse builder for base-ml"
   
   # Failure
   git checkout docker/base-ml/Dockerfile
   ```

**Expected Savings:** 200-300 MB per ML image (~900 MB total)

---

## Post-Flight 🎉

### Verification
- [ ] Full rebuild:
  ```powershell
  .\scripts\build-all-images.ps1
  ```

- [ ] Measure results:
  ```powershell
  docker images | grep cp-whisperx-app > after-phase2.txt
  Write-Host "=== BEFORE ===" ; Get-Content before-phase2.txt
  Write-Host "=== AFTER ===" ; Get-Content after-phase2.txt
  ```

- [ ] Calculate savings:
  ```powershell
  # Manual calculation or script
  ```

### Testing
- [ ] Test each stage individually:
  ```powershell
  docker run --rm rajiup/cp-whisperx-app-demux:cpu --help
  docker run --rm --gpus all rajiup/cp-whisperx-app-asr:cuda --help
  # ... etc
  ```

- [ ] Full integration test:
  ```powershell
  python prepare-job.py in/test-movie.mp4 --tmdb-id 12345
  python pipeline.py --workflow subtitle
  ```

### Documentation
- [ ] Update `DOCKER_OPTIMIZATION_STATUS.md`:
  - Mark Phase 2 as COMPLETED
  - Document actual savings
  - Note any issues encountered

- [ ] Create `DOCKER_PHASE2_SUMMARY.md`:
  - Before/after metrics
  - Lessons learned
  - Recommendations for Phase 3

- [ ] Commit and tag:
  ```powershell
  git add docs/DOCKER_*.md
  git commit -m "Phase2: Complete - Documentation"
  git tag phase2-complete-$(Get-Date -Format "yyyyMMdd-HHmmss")
  git push --tags
  ```

---

## Rollback Plan 🔙

If something goes wrong:

```powershell
# Find your backup tag
git tag -l "phase2-backup-*"

# Rollback
git reset --hard phase2-backup-YYYYMMDD-HHMMSS
git clean -fd

# Rebuild from backup
.\scripts\build-all-images.ps1
```

---

## Expected Results 📊

### Image Sizes
- **Before:** ~43 GB total
- **After:** ~28 GB total
- **Savings:** ~15 GB (35% reduction)

### Build Times
- **Before:** 45-60 min (cold)
- **After:** 30-40 min (cold)
- **Savings:** 15-20 min (30% faster)

### By Priority
1. ✅ **Task 1 (Model Cache):** 5-10 GB, 1 hour
2. ✅ **Task 2 (Use base-ml):** 10 GB, 1 hour
3. ✅ **Task 3 (Split Requirements):** 5-10 min builds, 1.5 hours
4. ✅ **Task 4 (Document Versions):** Maintenance win, 30 min
5. ⚠️ **Task 5 (Wheelhouse):** 900 MB, 2 hours (OPTIONAL)

---

## Time Budget

| Task | Estimated | Priority | Status |
|------|-----------|----------|--------|
| Task 1: Model Cache | 1 hour | HIGH | ⬜ |
| Task 2: Use base-ml | 1 hour | HIGH | ⬜ |
| Task 3: Split Requirements | 1.5 hours | MEDIUM | ⬜ |
| Task 4: Document Versions | 30 min | LOW | ⬜ |
| Task 5: Wheelhouse (opt) | 2 hours | LOW | ⬜ |
| **TOTAL (minimum)** | **2.5 hours** | - | - |
| **TOTAL (recommended)** | **4 hours** | - | - |
| **TOTAL (maximum)** | **6 hours** | - | - |

---

## Quick Command Reference

```powershell
# Measure build time
Measure-Command { .\scripts\build-all-images.ps1 }

# Check image sizes
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep cp-whisperx-app

# Test single stage
docker run --rm --gpus all rajiup/cp-whisperx-app-asr:cuda --help

# Check layer sizes
docker history rajiup/cp-whisperx-app-asr:cuda --no-trunc

# Clean up
docker system prune -a --volumes
```

---

## Success Criteria ✅

- [ ] All images build without errors
- [ ] All stages pass smoke tests (--help)
- [ ] Full pipeline completes successfully
- [ ] Image sizes reduced by ≥10 GB
- [ ] Build time reduced by ≥10 min
- [ ] Documentation updated
- [ ] Git commit tagged

---

**Ready to start?** Begin with Task 1 (Model Cache) - it's the easiest win! 🚀

**Status:** READY TO IMPLEMENT  
**Last Updated:** November 5, 2025
