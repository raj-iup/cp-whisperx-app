# Migration Guide - Phase 1 & 2 Enhancements

**Version:** 2.0  
**Date:** 2024-11-06  
**Status:** Active

---

## 🎯 Overview

This guide helps existing users migrate to the new optimized workflow introduced in Phase 1 (Script Consolidation) and Phase 2 (Docker Optimization).

### Key Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **First-time setup** | 15-20 min | 10-15 min | 25-33% faster |
| **Prepare job** | 1-2 min | 5-30 sec | 75-85% faster |
| **Docker build** | 30-45 min | 5-10 min | 67-83% faster |
| **Docker images size** | ~50 GB | ~20 GB | 60% smaller |

---

## 📋 What Changed

### Phase 1: Script Consolidation

1. **Bootstrap Enhanced** - Now includes:
   - Hardware detection with 1-hour caching
   - Directory creation
   - FFmpeg validation
   - Optional model pre-download

2. **Prepare-Job Simplified** - Now:
   - Uses existing `.bollyenv` environment
   - No temporary venv creation
   - No PyTorch installation
   - Uses cached hardware info
   - **80-90% faster execution**

3. **Prepare-Job-Venv Deprecated** - Replaced by simplified `prepare-job.ps1/sh`

### Phase 2: Docker Optimization

1. **Slim Docker Images** - PyTorch removed from images:
   - base-ml: 4.5 GB → **1.2 GB** (3.3 GB saved)
   - asr: 5.2 GB → **1.5 GB** (3.7 GB saved)
   - diarization: 6.1 GB → **1.8 GB** (4.3 GB saved)
   - Total: ~50 GB → **~20 GB** (30 GB saved)

2. **Mode-Aware Building** - New `docker-build.ps1/sh`:
   - **native**: Build minimal images (2 GB, 2-5 min)
   - **docker-cpu**: Build all CPU images (15 GB, 10-20 min)
   - **docker-gpu**: Build all GPU images (20 GB, 15-30 min)

3. **Native Execution Default** - ML stages use `.bollyenv` for better performance

---

## 🚀 Migration Steps

### For First-Time Users

**New Workflow (Recommended):**

```powershell
# Windows
.\scripts\bootstrap.ps1                      # One-time setup (10-15 min)
.\scripts\docker-build.ps1 -Mode native      # Build minimal images (2-5 min)
.\prepare-job.ps1 input.mp4                  # Prepare job (5-30 sec)
.\run_pipeline.ps1 -Job <job-id>             # Run pipeline
```

```bash
# Linux/macOS
./scripts/bootstrap.sh                       # One-time setup (10-15 min)
./scripts/docker-build.sh --mode native      # Build minimal images (2-5 min)
./prepare-job.sh input.mp4                   # Prepare job (5-30 sec)
./run_pipeline.sh -j <job-id>                # Run pipeline
```

### For Existing Users

**If you already ran bootstrap before Phase 1:**

1. **Re-run bootstrap** to get enhancements:
   ```powershell
   .\scripts\bootstrap.ps1
   ```
   
   This will:
   - Create hardware cache
   - Validate directories
   - Pre-download models (if HF token available)
   - Keep existing `.bollyenv` packages

2. **Stop using `prepare-job-venv.ps1/sh`** (deprecated):
   ```powershell
   # OLD (deprecated)
   .\prepare-job-venv.ps1 input.mp4
   
   # NEW (recommended)
   .\prepare-job.ps1 input.mp4
   ```

3. **Rebuild Docker images** (optional but recommended):
   ```powershell
   # Build minimal native mode images (recommended)
   .\scripts\docker-build.ps1 -Mode native
   
   # OR build full GPU images if needed
   .\scripts\docker-build.ps1 -Mode docker-gpu
   ```

---

## 🔧 Execution Modes

### Native Mode (Default, Recommended)

**When to use:** Most users, best performance

**Characteristics:**
- ML stages run in `.bollyenv` environment
- Docker only for FFmpeg (demux, mux)
- Fastest execution
- Smallest disk footprint (~2 GB images)

**Setup:**
```powershell
.\scripts\bootstrap.ps1
.\scripts\docker-build.ps1 -Mode native
```

**Execution:**
```powershell
.\prepare-job.ps1 input.mp4
.\run_pipeline.ps1 -Job <job-id>  # Auto-detects native mode
```

### Docker CPU Mode

**When to use:** No GPU, want isolation, or testing

**Characteristics:**
- All stages run in Docker containers
- CPU-only execution
- Good isolation
- Medium disk footprint (~15 GB images)

**Setup:**
```powershell
.\scripts\bootstrap.ps1
.\scripts\docker-build.ps1 -Mode docker-cpu
```

**Execution:**
```powershell
.\prepare-job.ps1 input.mp4
.\run_pipeline.ps1 -Job <job-id> -Mode docker-cpu
```

### Docker GPU Mode

**When to use:** Multiple machines, distributed execution, or full isolation

**Characteristics:**
- All stages run in Docker containers
- CUDA GPU acceleration
- Maximum isolation
- Larger disk footprint (~20 GB images)

**Setup:**
```powershell
.\scripts\bootstrap.ps1
.\scripts\docker-build.ps1 -Mode docker-gpu
```

**Execution:**
```powershell
.\prepare-job.ps1 input.mp4
.\run_pipeline.ps1 -Job <job-id> -Mode docker-gpu
```

---

## 📊 Performance Comparison

### Job Preparation Time

| Workflow | Old (prepare-job-venv) | New (prepare-job) | Speedup |
|----------|------------------------|-------------------|---------|
| With GPU | 90-120 sec | 10-30 sec | **4-8x faster** |
| Without GPU | 60-90 sec | 5-20 sec | **4-12x faster** |

### Docker Build Time

| Mode | Old (docker compose build) | New (docker-build) | Speedup |
|------|----------------------------|-------------------|---------|
| Native | N/A | 2-5 min | **New capability** |
| CPU | 20-30 min | 10-20 min | **2x faster** |
| GPU | 30-45 min | 15-30 min | **2x faster** |

### Disk Space Usage

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| Docker images | ~50 GB | ~2 GB (native) | **96%** |
| Docker images | ~50 GB | ~20 GB (GPU) | **60%** |
| Python env | ~3 GB | ~3 GB | Same |
| **Total** | **~53 GB** | **~5-23 GB** | **43-91%** |

---

## 🆘 Troubleshooting

### Issue: "Bootstrap not run - virtual environment not found"

**Solution:** Run bootstrap first:
```powershell
.\scripts\bootstrap.ps1
```

### Issue: "Hardware cache not found"

**Solution:** Hardware cache expires after 1 hour. Re-run bootstrap or let prepare-job detect hardware:
```powershell
.\scripts\bootstrap.ps1  # Full detection with cache
# OR
.\prepare-job.ps1 input.mp4  # Auto-detects if cache missing
```

### Issue: Docker images still showing old sizes

**Solution:** Remove old images and rebuild:
```powershell
# Remove old images
docker rmi $(docker images rajiup/cp-whisperx-app-* -q)

# Rebuild with new mode
.\scripts\docker-build.ps1 -Mode native
```

### Issue: "prepare-job-venv.ps1" shows deprecation warning

**Solution:** Switch to new simplified script:
```powershell
# Replace this
.\prepare-job-venv.ps1 input.mp4 -StartTime 00:00:10 -EndTime 00:01:00

# With this
.\prepare-job.ps1 input.mp4 -StartTime 00:00:10 -EndTime 00:01:00
```

### Issue: PyTorch not found in Docker container

**Solution:** Use native mode (default) or rebuild with docker-gpu mode:
```powershell
# Native mode (uses .bollyenv, recommended)
.\run_pipeline.ps1 -Job <job-id>

# OR rebuild for Docker GPU mode
.\scripts\docker-build.ps1 -Mode docker-gpu
.\run_pipeline.ps1 -Job <job-id> -Mode docker-gpu
```

---

## 📚 Related Documentation

- [SCRIPT_CONSOLIDATION_BEST_PRACTICES.md](SCRIPT_CONSOLIDATION_BEST_PRACTICES.md) - Full technical details
- [PREPARE_JOB_ARCHITECTURE.md](PREPARE_JOB_ARCHITECTURE.md) - prepare-job workflow
- [README.md](../README.md) - Main project documentation
- [QUICK_START.md](QUICK_START.md) - Quick start guide

---

## ✅ Validation Checklist

After migration, verify:

- [ ] Bootstrap completed successfully
- [ ] `.bollyenv` directory exists
- [ ] `out/hardware_cache.json` exists
- [ ] Docker images built (check with `docker images rajiup/cp-whisperx-app-*`)
- [ ] prepare-job completes in < 30 seconds
- [ ] Pipeline runs successfully with test file
- [ ] GPU detected (if available): Check in hardware cache or bootstrap output

---

## 🔮 Future Deprecations

### Scheduled for Removal (v3.0)

- `prepare-job-venv.ps1` - Use `prepare-job.ps1` instead
- `prepare-job-venv.sh` - Use `prepare-job.sh` instead
- Standalone `preflight.ps1` - Integrated into `run_pipeline.ps1`

These scripts will continue to work but show deprecation warnings.

---

## 💬 Support

If you encounter issues during migration:

1. Check the troubleshooting section above
2. Review the logs in `logs/` directory
3. Validate hardware cache: `cat out/hardware_cache.json`
4. Check Docker images: `docker images rajiup/cp-whisperx-app-*`

---

**Version:** 2.0  
**Last Updated:** 2024-11-06  
**Next Review:** After Phase 3 (Advanced Optimizations)
