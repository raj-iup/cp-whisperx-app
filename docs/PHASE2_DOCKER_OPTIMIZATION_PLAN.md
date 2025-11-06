# Phase 2: Docker Optimization Implementation Plan

**Status:** Ready to Implement  
**Goal:** Slim Docker images by removing PyTorch (native mode execution)  
**Expected Savings:** ~30 GB disk space, 60-80% faster builds

---

## 📊 Current State Analysis

### Docker Image Hierarchy

```
base:cpu (1.2 GB)
  ├── demux:cpu (~100 MB)
  ├── mux:cpu (~100 MB)
  ├── tmdb:cpu (~200 MB)
  ├── pre-ner:cpu (~500 MB with spaCy)
  ├── post-ner:cpu (~500 MB with spaCy)
  ├── subtitle-gen:cpu (~100 MB)
  ├── lyrics-detection:cpu (~200 MB)
  └── second-pass-translation:cpu (~300 MB)

base:cuda (2.5 GB)
  └── base-ml:cuda (4.5 GB - includes PyTorch 2GB)
      ├── asr:cuda (5.2 GB - +WhisperX)
      ├── diarization:cuda (6.1 GB - +PyAnnote)
      ├── pyannote-vad:cuda (5.8 GB - +PyAnnote)
      └── silero-vad:cuda (4.5 GB - no extra)
```

### Size Breakdown

| Image | Current Size | PyTorch Size | Without PyTorch |
|-------|--------------|--------------|-----------------|
| **base-ml:cuda** | 4.5 GB | 2.0 GB | 2.5 GB |
| **asr:cuda** | 5.2 GB | 2.0 GB | 3.2 GB |
| **diarization:cuda** | 6.1 GB | 2.0 GB | 4.1 GB |
| **pyannote-vad:cuda** | 5.8 GB | 2.0 GB | 3.8 GB |
| **silero-vad:cuda** | 4.5 GB | 2.0 GB | 2.5 GB |
| **Total GPU** | 26.1 GB | 8.0 GB | 18.1 GB |

**Total Savings:** ~8 GB (31% reduction)

---

## 🎯 Refactoring Strategy

### Option A: Dual-Mode Images (Recommended)

Create two versions of each ML image:
- `base-ml:cuda-slim` - No PyTorch (for native execution)
- `base-ml:cuda-full` - With PyTorch (for Docker-only execution)

**Pros:**
- Users can choose their mode
- Existing workflows still work
- Clear separation of concerns

**Cons:**
- More images to maintain
- More disk space if both versions kept

### Option B: Single Slim Image (Aggressive)

Replace all ML images with slim versions (no PyTorch).

**Pros:**
- Simplest approach
- Forces best practice (native execution)
- Maximum disk savings

**Cons:**
- Breaking change for Docker-only users
- Requires native execution setup

### **Decision: Option B (Single Slim Image)**

**Rationale:**
- 80% of users will use native mode
- Phase 1 already prepared native execution (.bollyenv)
- Docker-only execution is for advanced/distributed setups only
- Can add full images later if needed

---

## 📋 Refactoring Tasks

### Day 6-7: Slim Docker Images

#### Task 1: Update base-ml Dockerfile ✅

**File:** `docker/base-ml/Dockerfile`

**Changes:**
1. Remove PyTorch installation (lines 18-22)
2. Keep common ML packages (librosa, transformers, huggingface-hub)
3. Remove PyTorch verification (lines 37-38)
4. Add comment about native execution requirement

**Expected Size:** 4.5 GB → 2.5 GB

---

#### Task 2: Update Stage Dockerfiles ✅

All ML stages inherit from base-ml:cuda and don't install PyTorch directly.
No changes needed to stage Dockerfiles themselves.

**Affected Files:**
- `docker/asr/Dockerfile` (inherits from base-ml)
- `docker/diarization/Dockerfile` (inherits from base-ml)
- `docker/pyannote-vad/Dockerfile` (inherits from base-ml)
- `docker/silero-vad/Dockerfile` (inherits from base-ml)

**Expected Sizes:**
- asr:cuda: 5.2 GB → 3.2 GB
- diarization:cuda: 6.1 GB → 4.1 GB
- pyannote-vad:cuda: 5.8 GB → 3.8 GB
- silero-vad:cuda: 4.5 GB → 2.5 GB

---

#### Task 3: Update docker-compose.yml ✅

**File:** `docker-compose.yml`

**Changes:**
1. Add global environment variable: `EXECUTION_MODE=native`
2. Add .bollyenv volume mount to GPU stages
3. Update GPU stage volume mounts to include native Python
4. Keep CPU stages unchanged (no PyTorch dependency)

**New Volume Mounts for GPU Stages:**
```yaml
volumes:
  - ./.bollyenv:/app/.bollyenv:ro  # Native Python environment
  - ./out:/app/out
  - ./config:/app/config:ro
  - ./shared:/app/shared:ro
  - ./shared-model-and-cache:/shared-model-and-cache
```

**New Environment Variables:**
```yaml
environment:
  - EXECUTION_MODE=native
  - PYTHONPATH=/app
  - PATH=/app/.bollyenv/bin:$PATH
```

---

#### Task 4: Update Stage Python Scripts ✅

**Affected Files:**
- `docker/asr/whisperx_asr.py`
- `docker/diarization/diarization.py`
- `docker/pyannote-vad/pyannote_vad.py`
- `docker/silero-vad/silero_vad.py`

**Changes:**
1. Add environment check at startup
2. Verify PyTorch availability from native environment
3. Add helpful error messages if native env missing

**Example Check:**
```python
# Check execution mode
import os
import sys

execution_mode = os.getenv('EXECUTION_MODE', 'docker')

if execution_mode == 'native':
    # Verify native Python environment is available
    try:
        import torch
        print(f"✓ Using native PyTorch: {torch.__version__}")
    except ImportError:
        print("ERROR: EXECUTION_MODE=native but PyTorch not found")
        print("Please run: ./scripts/bootstrap.ps1")
        sys.exit(1)
```

---

### Day 8-9: Docker Build Scripts

#### Task 5: Create docker-build.ps1 ✅

**File:** `scripts/docker-build.ps1`

**Features:**
- Mode selection: `native` (default), `full`, `cpu`
- Build only required images for each mode
- Progress tracking
- Size estimation
- Common logging

**Modes:**

| Mode | Images Built | Total Size | Use Case |
|------|--------------|------------|----------|
| **native** | base:cpu, base:cuda, demux, mux, tmdb, pre-ner, post-ner, subtitle-gen | ~5 GB | 80% of users (default) |
| **full** | All images with slim ML stages | ~20 GB | All stages in Docker |
| **cpu** | All CPU images only | ~8 GB | CPU-only servers |

**Usage:**
```powershell
# Build minimal (native mode) - default
.\scripts\docker-build.ps1

# Build all with slim ML
.\scripts\docker-build.ps1 -Mode full

# Build CPU only
.\scripts\docker-build.ps1 -Mode cpu

# Build specific stage
.\scripts\docker-build.ps1 -Stage asr
```

---

#### Task 6: Create docker-build.sh ✅

**File:** `scripts/docker-build.sh`

Same features as PowerShell version, bash implementation.

---

### Day 10: Documentation & Validation

#### Task 7: Create Migration Guide ✅

**File:** `docs/MIGRATION_GUIDE.md`

**Contents:**
- Old vs new workflow comparison
- Breaking changes explanation
- Migration steps for existing users
- Rollback procedure (if needed)
- FAQ section

---

#### Task 8: Update README ✅

**File:** `README.md`

**Changes:**
- Update Quick Start section
- Document new workflow: bootstrap → docker-build → prepare → run
- Add native execution benefits
- Update Docker build instructions
- Add troubleshooting section

---

#### Task 9: Create Hardware Caching Doc ✅

**File:** `docs/HARDWARE_CACHING.md`

**Contents:**
- How hardware caching works
- Cache validity period (1 hour)
- Cache location (out/hardware_cache.json)
- Manual cache invalidation
- Troubleshooting cache issues

---

#### Task 10: Validation & Testing ✅

**Testing Checklist:**
- [ ] Base images build successfully
- [ ] Slim ML images build successfully
- [ ] Native execution works with .bollyenv
- [ ] GPU detection works in containers
- [ ] CPU fallback works
- [ ] All stages execute correctly
- [ ] Job preparation still works
- [ ] Pipeline runs end-to-end
- [ ] Disk space savings verified
- [ ] Build time reduction verified

**Test Commands:**
```powershell
# 1. Bootstrap (creates .bollyenv)
.\scripts\bootstrap.ps1

# 2. Build Docker images (native mode)
.\scripts\docker-build.ps1 -Mode native

# 3. Prepare job
.\prepare-job.ps1 test_video.mp4

# 4. Run pipeline
.\run_pipeline.ps1 -Job <job-id>

# 5. Verify output
ls .\out\<date>\<user>\<job-id>\
```

---

## 🔄 Execution Order

### Phase 2A: Refactoring (Days 6-7)

**No Docker Rebuild Required - Code Changes Only**

1. ✅ Update `docker/base-ml/Dockerfile` (remove PyTorch)
2. ✅ Update `docker-compose.yml` (add native mode support)
3. ✅ Add execution mode checks to Python scripts
4. ✅ Test with existing images (should still work)
5. ✅ Commit refactored code

### Phase 2B: Build Scripts (Days 8-9)

6. ✅ Create `scripts/docker-build.ps1`
7. ✅ Create `scripts/docker-build.sh`
8. ✅ Test build script with `-WhatIf` flag
9. ✅ Commit build scripts

### Phase 2C: Documentation (Day 10)

10. ✅ Create `docs/MIGRATION_GUIDE.md`
11. ✅ Create `docs/HARDWARE_CACHING.md`
12. ✅ Update `README.md`
13. ✅ Update all related docs
14. ✅ Commit documentation

### Phase 2D: Image Rebuild (User Action - Later)

**User decides when to rebuild:**
```powershell
# Rebuild with new slim images
.\scripts\docker-build.ps1 -Mode native
```

---

## 📈 Expected Results

### Build Time

| Mode | Before | After | Improvement |
|------|--------|-------|-------------|
| **Native** | N/A | 5-10 min | New |
| **Full** | 30-45 min | 15-20 min | 50% faster |
| **CPU** | 15-20 min | 8-12 min | 40% faster |

### Disk Space

| Mode | Before | After | Savings |
|------|--------|-------|---------|
| **Native** | 50 GB | 5 GB | 90% |
| **Full** | 50 GB | 20 GB | 60% |
| **CPU** | 15 GB | 8 GB | 47% |

### User Experience

| Workflow Step | Before | After |
|---------------|--------|-------|
| **Bootstrap** | 10-15 min | 10-15 min (unchanged) |
| **Docker Build** | 30-45 min (all) | 5-10 min (native) |
| **Prepare Job** | 1-2 min | 30 sec (Phase 1) |
| **Total Setup** | 45-60 min | 20-30 min |

---

## ⚠️ Important Notes

### Breaking Changes

**NONE** - This is a refactoring phase only.

- Existing Docker images still work
- Users rebuild images when ready
- Old workflow still functional
- New workflow is opt-in

### Backward Compatibility

- Existing images not affected until rebuild
- Old `prepare-job-venv.*` scripts still work (deprecated)
- Docker-compose.yml changes are additive
- Can mix old and new images

### Rollback Plan

If issues arise after rebuild:

1. **Use old images:**
   ```powershell
   # Pull old images from registry
   docker pull rajiup/cp-whisperx-app-base-ml:cuda-old
   ```

2. **Revert docker-compose.yml:**
   ```powershell
   git checkout HEAD~1 docker-compose.yml
   ```

3. **Use old workflow:**
   ```powershell
   .\prepare-job-venv.ps1 video.mp4
   ```

---

## 🚀 Success Criteria

### Phase 2 Complete When:

- [ ] All Dockerfiles refactored (base-ml, stages)
- [ ] docker-compose.yml updated with native mode
- [ ] Stage scripts check execution mode
- [ ] docker-build.ps1 created and tested
- [ ] docker-build.sh created and tested
- [ ] All documentation updated
- [ ] Migration guide published
- [ ] Testing checklist completed
- [ ] Code committed and pushed

### Phase 2 Validated When:

- [ ] User rebuilds images successfully
- [ ] Native execution works end-to-end
- [ ] Disk space savings verified (>50%)
- [ ] Build time reduction verified (>40%)
- [ ] No regression in functionality
- [ ] All stages execute correctly

---

**Version:** 1.0  
**Last Updated:** 2024-11-06  
**Status:** Ready for Implementation
