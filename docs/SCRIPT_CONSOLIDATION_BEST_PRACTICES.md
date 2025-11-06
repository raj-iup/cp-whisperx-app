# Script Consolidation & Best Practices Recommendations

**Analysis Date:** 2024-11-06  
**Purpose:** Eliminate duplication, optimize workflow, reduce Docker image sizes

---

## 🎯 Executive Summary

**Current State:** Significant duplication across bootstrap, preflight, and prepare-job scripts  
**Recommendation:** Consolidate into 3-script workflow with clear responsibilities  
**Impact:** 40-60% reduction in execution time, 2-3 GB savings in Docker images

---

## 📊 Current Script Analysis

### Duplication Identified

| Task | bootstrap | preflight | prepare-job-venv | Docker Images |
|------|-----------|-----------|------------------|---------------|
| **Python discovery** | ✅ | ✅ | ✅ | ❌ |
| **Python version check** | ✅ | ✅ | ✅ | ❌ |
| **Venv creation** | ✅ (.bollyenv) | ❌ | ✅ (temp) | ❌ |
| **PyTorch install** | ✅ | ❌ | ✅ | ✅ (base-ml) |
| **GPU detection** | ✅ (basic) | ✅ (full) | ✅ (nvidia-smi) | ❌ |
| **Hardware detection** | ❌ | ✅ (CPU/RAM/GPU) | ✅ (via prepare-job.py) | ❌ |
| **pip upgrade** | ✅ | ❌ | ❌ | ✅ (base) |
| **Package install** | ✅ (70+) | ❌ | ✅ (torch+psutil) | ✅ (stage-specific) |
| **FFmpeg check** | ❌ | ✅ | ❌ | N/A (in Docker) |
| **Docker check** | ❌ | ✅ | ❌ | N/A |
| **Directory creation** | ❌ | ✅ (validate) | ❌ | ✅ (in base) |

**Total Duplication:** 7 out of 11 tasks duplicated across 2+ scripts

---

## 🏗️ Recommended Architecture

### New 3-Script Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ BOOTSTRAP (One-Time Setup)                                      │
│ Duration: 5-15 minutes                                           │
└─────────────────────────────────────────────────────────────────┘
    │
    ├─ Install ALL dependencies ONCE in .bollyenv/
    ├─ PyTorch with appropriate CUDA/MPS/CPU
    ├─ All Python packages (whisperx, pyannote, etc.)
    ├─ No Docker image builds (moved to separate workflow)
    └─ Hardware detection and cache results
    
┌─────────────────────────────────────────────────────────────────┐
│ PREPARE-JOB (Job-Specific Setup)                                │
│ Duration: 5-30 seconds                                           │
└─────────────────────────────────────────────────────────────────┘
    │
    ├─ Use existing .bollyenv/ (no venv creation)
    ├─ Validate input file
    ├─ Quick hardware check (from cache if <1h old)
    ├─ Create job structure
    ├─ Prepare media (clip/copy)
    ├─ Generate optimized config
    └─ NO preflight checks (moved to run_pipeline)
    
┌─────────────────────────────────────────────────────────────────┐
│ RUN-PIPELINE (Execution with Validation)                        │
│ Duration: Variable (depends on media)                           │
└─────────────────────────────────────────────────────────────────┘
    │
    ├─ Quick preflight check (from cache if <24h)
    ├─ Validate Docker/Docker Compose
    ├─ Check required services
    ├─ Execute pipeline stages
    └─ Monitor and report progress
```

---

## 📝 Detailed Recommendations

### 1. Bootstrap Script Consolidation

**Responsibility:** One-time environment setup (5-15 minutes)

#### ✅ Keep in Bootstrap

| Task | Reason | Current Location |
|------|--------|------------------|
| **Python discovery & version** | One-time validation | bootstrap.ps1 |
| **Virtual environment creation** | .bollyenv/ permanent | bootstrap.ps1 |
| **PyTorch installation** | Large download (~2GB), detect GPU once | bootstrap.ps1 |
| **All Python packages** | 70+ packages, one-time install | bootstrap.ps1 |
| **Hardware detection (full)** | Cache results for 1 hour | **NEW** |
| **Directory creation** | in/, out/, logs/, etc. | **MOVE from preflight** |
| **FFmpeg installation check** | One-time validation | **MOVE from preflight** |

#### ❌ Remove from Bootstrap

| Task | Reason | Move To |
|------|--------|---------|
| Basic torch.cuda check | Redundant, full detection better | Hardware cache |
| Quick CUDA verification | Will be done in full detection | Hardware cache |

#### 🆕 Add to Bootstrap

```powershell
# NEW: Comprehensive hardware detection with caching
Write-LogSection "HARDWARE DETECTION & CACHING"

# Detect all hardware
$hwInfo = Detect-Hardware-Full  # CPU, RAM, GPU, CUDA, MPS

# Save to cache (1 hour validity)
$cacheFile = "out/hardware_cache.json"
$hwInfo | ConvertTo-Json | Set-Content $cacheFile

# Display recommendations
Write-LogInfo "Hardware Profile:"
Write-LogInfo "  CPU: $($hwInfo.cpu_cores) cores"
Write-LogInfo "  RAM: $($hwInfo.memory_gb) GB"
Write-LogInfo "  GPU: $($hwInfo.gpu_name) ($($hwInfo.gpu_type))"
Write-LogInfo "  Recommended Whisper Model: $($hwInfo.recommended_whisper_model)"
```

#### 📦 Bootstrap Duration Optimization

**Before:** 5-15 minutes  
**After:** 5-15 minutes (no change, but only run once)

**Key Changes:**
- Remove redundant torch verification (save 10-20 seconds)
- Add comprehensive hardware caching (add 5-10 seconds, save time later)
- Create all directories (add 2 seconds)

---

### 2. Prepare-Job Script Simplification

**Responsibility:** Job-specific setup (5-30 seconds)

#### ✅ Keep in Prepare-Job

| Task | Reason | Current Location |
|------|--------|------------------|
| **Input file validation** | Job-specific | prepare-job-venv.ps1 |
| **Job directory creation** | Job-specific | prepare-job.py |
| **Media preparation** | Clip or copy media | prepare-job.py |
| **Config generation** | Job-specific .env | prepare-job.py |
| **Quick hardware check** | Use cache if <1h old | prepare-job.py |

#### ❌ Remove from Prepare-Job

| Task | Reason | Move To |
|------|--------|---------|
| **Venv creation (.venv-prepare-job-temp)** | Redundant, use .bollyenv | Bootstrap |
| **PyTorch installation** | Already in .bollyenv | Bootstrap |
| **psutil installation** | Already in .bollyenv | Bootstrap |
| **nvidia-smi detection** | Use cached hardware info | Hardware cache |
| **Python discovery** | Already done in bootstrap | Bootstrap validation |
| **Python version check** | Already done in bootstrap | Bootstrap validation |

#### 🔄 Simplified Workflow

**Before (prepare-job-venv.ps1):**
```
1. Parse args (4 steps)
2. Python discovery (2 steps)
3. Create venv (2 steps)
4. Hardware detection (2 steps)
5. Install PyTorch (1 step)
6. Verify PyTorch (1 step)
7. Install psutil (1 step)
8. Execute prepare-job.py (2 steps)
9. Cleanup venv (2 steps)
Total: 17 steps, 1-2 minutes
```

**After (prepare-job.ps1 - SIMPLIFIED):**
```
1. Parse args (1 step)
2. Activate .bollyenv (1 step)
3. Load hardware cache (1 step)
4. Execute prepare-job.py with --native (1 step)
Total: 4 steps, 5-30 seconds
```

#### 💾 Hardware Cache Usage

```python
# prepare-job.py - Use cached hardware info

def load_hardware_cache(max_age_hours=1):
    """Load hardware info from cache if fresh."""
    cache_file = Path("out/hardware_cache.json")
    
    if not cache_file.exists():
        return None
    
    # Check age
    age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
    if age_hours > max_age_hours:
        return None
    
    # Load cached info
    with open(cache_file) as f:
        return json.load(f)

# Use cache if available, otherwise detect
hw_info = load_hardware_cache() or detect_hardware_capabilities()
```

#### 📦 Prepare-Job Duration Optimization

**Before:** 1-2 minutes  
**After:** 5-30 seconds (80-90% reduction)

**Savings:**
- No venv creation: -15 seconds
- No PyTorch install: -30-60 seconds
- No PyTorch verification: -5 seconds
- No psutil install: -3 seconds
- Use cached hardware: -5 seconds
- **Total saved:** 58-88 seconds

---

### 3. Preflight Script Repositioning

**Responsibility:** Pre-execution validation (10-30 seconds)

#### 🔄 Move Preflight to Run-Pipeline

**Current:** Standalone preflight.ps1 → preflight.py  
**Recommended:** Integrate into run_pipeline.ps1 as first step

**Rationale:**
- Preflight checks are most relevant right before execution
- Avoids false positives (user runs preflight, then changes system)
- Reduces user confusion (one less script to remember)
- Caching still works (24-hour validity)

#### ✅ Keep in Preflight (as part of run_pipeline)

| Task | Reason | Duration |
|------|--------|----------|
| **Docker/Docker Compose check** | Execution requirement | 2-5 sec |
| **Docker daemon running** | Execution requirement | 1-2 sec |
| **docker-compose.yml validation** | Execution requirement | 1 sec |
| **Docker images check** | Execution requirement | 3-5 sec |
| **Config/.env validation** | Job-specific | 1 sec |
| **Secrets validation** | API tokens check | 1 sec |
| **Disk space check** | Execution requirement | 1 sec |
| **Cache check (24h)** | Skip if recent | 0-1 sec |

#### ❌ Remove from Preflight

| Task | Reason | Move To |
|------|--------|---------|
| **Python version check** | Already in bootstrap | Bootstrap |
| **FFmpeg check** | Already in bootstrap | Bootstrap |
| **Directory validation** | Created in bootstrap | Bootstrap |
| **Hardware detection** | Use cache from bootstrap | Hardware cache |
| **GPU/CUDA detection** | Use cache from bootstrap | Hardware cache |

#### 📦 Preflight Duration Optimization

**Before (standalone):** 10-30 seconds  
**After (integrated):** 5-15 seconds (50% reduction)

**Savings:**
- No Python check: -2 seconds
- No FFmpeg check: -2 seconds
- No directory check: -1 second
- No hardware detection: -5-10 seconds
- **Total saved:** 10-15 seconds

---

## 🐳 Docker Image Optimization

### Current Docker Structure Issues

| Issue | Impact | Files Affected |
|-------|--------|----------------|
| **PyTorch in base-ml** | 2+ GB per image | All ML stages |
| **Redundant pip installs** | Slow builds | All Dockerfiles |
| **Redundant system packages** | Wasted space | base, base-cuda |
| **Model downloads at runtime** | Slow first run | diarization, asr, VAD |

### Recommended Changes

#### 1. Model Pre-Download in Bootstrap

**Current:** Models downloaded at runtime (slow first execution)  
**Recommended:** Pre-download models during bootstrap

```powershell
# bootstrap.ps1 - Add model pre-download

Write-LogSection "PRE-DOWNLOADING ML MODELS"

# Activate venv
. .bollyenv/Scripts/Activate.ps1

# Download Whisper models
Write-LogInfo "Downloading Whisper models..."
python -c "import whisper; whisper.load_model('base')"
python -c "import whisper; whisper.load_model('medium')"
python -c "import whisper; whisper.load_model('large-v3')"

# Download PyAnnote models (if HF token available)
if (Test-Path "config/secrets.json") {
    $secrets = Get-Content "config/secrets.json" | ConvertFrom-Json
    if ($secrets.HF_TOKEN) {
        $env:HF_TOKEN = $secrets.HF_TOKEN
        Write-LogInfo "Downloading PyAnnote models..."
        python -c "from pyannote.audio import Pipeline; Pipeline.from_pretrained('pyannote/speaker-diarization-3.1')"
    }
}

Write-LogSuccess "Models pre-downloaded to cache"
```

**Benefits:**
- First pipeline run is 5-10 minutes faster
- No runtime downloads (except model updates)
- Models shared across all jobs

#### 2. Slim Docker Images (Remove PyTorch from Images)

**Current Approach:**
```dockerfile
# base-ml/Dockerfile
FROM base-cuda
RUN pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu121
# Size: ~2.5 GB per stage image
```

**Recommended Approach:**
```dockerfile
# base-ml/Dockerfile (SLIM VERSION)
FROM base-cuda
# NO PyTorch installation
# Size: ~500 MB per stage image
```

**Rationale:**
- PyTorch already in .bollyenv/ (native execution)
- Docker containers only for:
  1. FFmpeg operations (demux, mux)
  2. Isolation (TMDB, NER)
  3. Future: distributed execution
- Native execution is default and faster

**Image Size Comparison:**

| Image | Current Size | Recommended Size | Savings |
|-------|--------------|------------------|---------|
| base | 800 MB | 800 MB | 0 MB |
| base-cuda | 2.1 GB | 2.1 GB | 0 MB |
| base-ml | 4.5 GB | **1.2 GB** | **3.3 GB** |
| asr | 5.2 GB | **1.5 GB** | **3.7 GB** |
| diarization | 6.1 GB | **1.8 GB** | **4.3 GB** |
| pyannote-vad | 5.8 GB | **1.6 GB** | **4.2 GB** |
| **Total** | **~50 GB** | **~20 GB** | **~30 GB** |

#### 3. Consolidated Docker Build Script

**NEW:** `scripts/docker-build.ps1`

```powershell
# Consolidated Docker image builder
# Builds only images needed for current execution mode

param(
    [string]$Mode = "native"  # native, docker-cpu, docker-gpu
)

Write-LogSection "DOCKER IMAGE BUILD"

if ($Mode -eq "native") {
    Write-LogInfo "Native mode: Building minimal Docker images"
    
    # Build only essential images
    docker build -t rajiup/cp-whisperx-app-base:latest -f docker/base/Dockerfile .
    docker build -t rajiup/cp-whisperx-app-demux:latest -f docker/demux/Dockerfile .
    docker build -t rajiup/cp-whisperx-app-mux:latest -f docker/mux/Dockerfile .
    
    Write-LogSuccess "Minimal Docker images built (3 images, ~2 GB)"
    
} elseif ($Mode -eq "docker-gpu") {
    Write-LogInfo "Docker GPU mode: Building all GPU images"
    
    # Build base images
    docker build -t rajiup/cp-whisperx-app-base:cuda -f docker/base-cuda/Dockerfile .
    docker build -t rajiup/cp-whisperx-app-base-ml:cuda -f docker/base-ml/Dockerfile .
    
    # Build all stage images
    docker compose build
    
    Write-LogSuccess "All GPU Docker images built (10 images, ~50 GB)"
}
```

**Benefits:**
- Users can choose: native (fast, small) or docker (isolated, large)
- Default is native (80% of users)
- Docker build only when needed

---

## 📋 Implementation Plan

### Phase 1: Script Consolidation (Week 1)

#### Day 1-2: Bootstrap Enhancement
- [ ] Add comprehensive hardware detection
- [ ] Add hardware caching (1-hour validity)
- [ ] Add directory creation
- [ ] Add FFmpeg validation
- [ ] Add model pre-download
- [ ] Remove redundant torch verification

**Files Modified:**
- `scripts/bootstrap.ps1`
- `scripts/bootstrap.sh`
- **NEW:** `shared/hardware_detection.py`

#### Day 3-4: Prepare-Job Simplification
- [ ] Remove venv creation code
- [ ] Remove PyTorch installation code
- [ ] Remove psutil installation code
- [ ] Add hardware cache loading
- [ ] Update to use .bollyenv/ directly
- [ ] Remove prepare-job-venv.* wrappers

**Files Modified:**
- `prepare-job.ps1` (simplified wrapper)
- `prepare-job.sh` (simplified wrapper)
- `scripts/prepare-job.py` (add cache loading)
- **DELETE:** `prepare-job-venv.ps1`
- **DELETE:** `prepare-job-venv.sh`

#### Day 5: Preflight Integration
- [ ] Move preflight.ps1 code into run_pipeline.ps1
- [ ] Remove Python/FFmpeg checks (in bootstrap now)
- [ ] Remove hardware detection (use cache)
- [ ] Keep Docker validation
- [ ] Keep cache check (24h)

**Files Modified:**
- `run_pipeline.ps1` (add preflight as first stage)
- `run_pipeline.sh` (add preflight as first stage)
- `scripts/preflight.py` (remove redundant checks)
- **DEPRECATE:** `preflight.ps1` (add deprecation notice)

### Phase 2: Docker Optimization (Week 2)

#### Day 1-2: Slim Docker Images
- [ ] Create base-ml-slim without PyTorch
- [ ] Update all stage Dockerfiles
- [ ] Update docker-compose.yml with native flag
- [ ] Test native execution mode

**Files Modified:**
- `docker/base-ml/Dockerfile`
- All stage Dockerfiles
- `docker-compose.yml`

#### Day 3-4: Docker Build Script
- [ ] Create scripts/docker-build.ps1
- [ ] Create scripts/docker-build.sh
- [ ] Add mode selection (native/docker-cpu/docker-gpu)
- [ ] Update quick-start to use native by default

**Files Created:**
- **NEW:** `scripts/docker-build.ps1`
- **NEW:** `scripts/docker-build.sh`

#### Day 5: Documentation & Testing
- [ ] Update README with new workflow
- [ ] Update quick-start guide
- [ ] Create migration guide
- [ ] Test all workflows

**Files Modified:**
- `README.md`
- `docs/QUICK_START.md`
- **NEW:** `docs/MIGRATION_GUIDE.md`

---

## 🎯 Expected Benefits

### Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **First-time setup** | 15-20 min | 10-15 min | 25-33% faster |
| **Prepare job** | 1-2 min | 5-30 sec | 75-85% faster |
| **Preflight check** | 10-30 sec | 5-15 sec | 50% faster |
| **Docker build time** | 30-45 min | 5-10 min | 67-83% faster |
| **Docker images size** | ~50 GB | ~20 GB | 60% smaller |
| **Total disk usage** | ~55 GB | ~25 GB | 55% smaller |

### Developer Experience

| Aspect | Before | After |
|--------|--------|-------|
| **Number of scripts** | 6 (bootstrap, preflight, prepare-job, prepare-job-venv × 2 platforms) | 3 (bootstrap, prepare-job, run_pipeline) |
| **Script duplication** | High (7 tasks duplicated) | Low (1-2 tasks duplicated) |
| **Workflow clarity** | Confusing (when to run what?) | Clear (bootstrap → prepare → run) |
| **Cache efficiency** | None | Hardware (1h), Preflight (24h) |
| **Model downloads** | At runtime (slow first run) | At bootstrap (fast always) |

### User Experience

| User Type | Before | After |
|-----------|--------|-------|
| **First-time user** | Run 4 scripts, wait 25+ min | Run 1 script, wait 15 min |
| **Daily user** | Run 2-3 scripts, wait 1-3 min | Run 1 script, wait 30 sec |
| **Developer** | Build all images (50 GB) | Build minimal (2 GB native) |
| **Advanced user** | Manual mode selection | Automatic native/docker |

---

## 📁 File Structure Changes

### Before
```
cp-whisperx-app/
├── preflight.ps1                    # Standalone preflight
├── prepare-job.ps1                  # Old wrapper
├── prepare-job-venv.ps1             # Venv wrapper (17 steps)
├── prepare-job-venv.sh              # Venv wrapper (17 steps)
├── scripts/
│   ├── bootstrap.ps1                # Bootstrap (12 steps)
│   ├── bootstrap.sh                 # Bootstrap (12 steps)
│   ├── preflight.py                 # Preflight core (18 checks)
│   ├── preflight.sh                 # Preflight wrapper
│   └── prepare-job.py               # Prepare-job core
└── docker/
    ├── base-ml/Dockerfile           # 4.5 GB (with PyTorch)
    ├── asr/Dockerfile               # 5.2 GB (with PyTorch)
    └── ...
```

### After
```
cp-whisperx-app/
├── prepare-job.ps1                  # Simplified (4 steps)
├── prepare-job.sh                   # Simplified (4 steps)
├── run_pipeline.ps1                 # Includes preflight
├── run_pipeline.sh                  # Includes preflight
├── scripts/
│   ├── bootstrap.ps1                # Enhanced (15 steps)
│   ├── bootstrap.sh                 # Enhanced (15 steps)
│   ├── preflight.py                 # Slim (10 checks)
│   ├── prepare-job.py               # Optimized (cache-aware)
│   ├── docker-build.ps1             # NEW: Docker builder
│   └── docker-build.sh              # NEW: Docker builder
├── shared/
│   └── hardware_detection.py        # NEW: Shared hardware utils
├── out/
│   └── hardware_cache.json          # NEW: Hardware cache
└── docker/
    ├── base-ml/Dockerfile           # 1.2 GB (no PyTorch)
    ├── asr/Dockerfile               # 1.5 GB (no PyTorch)
    └── ...
```

---

## 🚀 Migration Guide for Users

### For Existing Users

**Old Workflow:**
```bash
# First time
.\scripts\bootstrap.ps1
.\preflight.ps1
docker compose build                # 30-45 min, 50 GB

# Each job
.\prepare-job-venv.ps1 movie.mp4    # 1-2 min
.\run_pipeline.ps1 -Job 20241106-0001
```

**New Workflow:**
```bash
# First time
.\scripts\bootstrap.ps1             # 10-15 min, includes models
.\scripts\docker-build.ps1 -Mode native  # 5 min, 2 GB

# Each job
.\prepare-job.ps1 movie.mp4         # 5-30 sec
.\run_pipeline.ps1 -Job 20241106-0001  # Includes preflight
```

**Benefits:**
- 60% faster first-time setup
- 80-90% faster job preparation
- 60% smaller disk usage
- Simpler workflow (4 steps → 3 steps)

---

## ✅ Validation Checklist

### Before Deployment

- [ ] Bootstrap script creates hardware cache
- [ ] Bootstrap script pre-downloads models
- [ ] Prepare-job uses hardware cache
- [ ] Prepare-job duration < 30 seconds
- [ ] Preflight integrated into run_pipeline
- [ ] Docker images use slim base
- [ ] Docker images < 2 GB each
- [ ] Native execution works with .bollyenv
- [ ] All tests pass
- [ ] Documentation updated

### After Deployment

- [ ] Monitor user feedback
- [ ] Measure actual performance gains
- [ ] Track Docker build times
- [ ] Validate disk usage reduction
- [ ] Check hardware cache hit rate
- [ ] Ensure model downloads work
- [ ] Confirm native execution stability

---

## 📚 Reference Documentation

**Created Documents:**
- `SCRIPT_CONSOLIDATION_BEST_PRACTICES.md` (this document)
- `MIGRATION_GUIDE.md` (to be created)
- `HARDWARE_CACHING.md` (to be created)

**Updated Documents:**
- `README.md`
- `docs/QUICK_START.md`
- `docs/PREPARE_JOB_ARCHITECTURE.md`
- `docs/BOOTSTRAP_VS_PREFLIGHT.md`

---

## 🔮 Future Enhancements

### Phase 3: Advanced Optimizations (Future)

1. **Parallel Model Downloads**
   - Download multiple models simultaneously
   - Reduce bootstrap time by 30-40%

2. **Incremental Docker Builds**
   - Only rebuild changed stages
   - Use BuildKit cache mounts
   - 90% faster rebuilds

3. **Cloud Model Caching**
   - Share model cache across machines
   - Download once, use everywhere
   - Save 5-10 GB per machine

4. **Smart Hardware Detection**
   - Auto-detect optimal batch size
   - Auto-tune based on workload
   - Adaptive performance optimization

---

**Version:** 1.0  
**Status:** Recommended Implementation  
**Priority:** High (significant user experience improvement)  
**Effort:** 2 weeks (1 developer)  
**Risk:** Low (backward compatible with deprecation warnings)
