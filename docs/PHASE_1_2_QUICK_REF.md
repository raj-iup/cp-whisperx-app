# Phase 1 & 2 Quick Reference

**Version:** 2.0 | **Date:** 2024-11-06 | **Status:** Production Ready

---

## 🚀 Quick Start (New Users)

### 1. One-Time Setup (10-15 minutes)

```powershell
# Windows
.\scripts\bootstrap.ps1
.\scripts\docker-build.ps1 -Mode native

# Linux/macOS
./scripts/bootstrap.sh
./scripts/docker-build.sh --mode native
```

### 2. Daily Usage (5-30 seconds)

```powershell
# Windows
.\prepare-job.ps1 input.mp4
.\run_pipeline.ps1 -Job <job-id>

# Linux/macOS
./prepare-job.sh input.mp4
./run_pipeline.sh -j <job-id>
```

---

## 📋 Command Reference

### Bootstrap (Run Once)

```powershell
# Windows
.\scripts\bootstrap.ps1

# Linux/macOS
./scripts/bootstrap.sh
```

**What it does:**
- Creates `.bollyenv` with all dependencies
- Detects hardware (cached for 1 hour)
- Creates required directories
- Validates FFmpeg
- Pre-downloads models (if HF token available)

**Duration:** 10-15 minutes

---

### Docker Build (Run Once or After Updates)

```powershell
# Native mode (recommended - fastest, smallest)
.\scripts\docker-build.ps1 -Mode native         # Windows
./scripts/docker-build.sh --mode native         # Linux/macOS

# Docker GPU mode (full CUDA support)
.\scripts\docker-build.ps1 -Mode docker-gpu     # Windows
./scripts/docker-build.sh --mode docker-gpu     # Linux/macOS

# Docker CPU mode (no GPU needed)
.\scripts\docker-build.ps1 -Mode docker-cpu     # Windows
./scripts/docker-build.sh --mode docker-cpu     # Linux/macOS
```

**Build Modes:**

| Mode | Size | Build Time | Use Case |
|------|------|------------|----------|
| **native** | ~2 GB | 2-5 min | Daily use, best performance |
| **docker-gpu** | ~20 GB | 15-30 min | Full isolation, CUDA |
| **docker-cpu** | ~15 GB | 10-20 min | No GPU, containers only |

---

### Prepare Job

```powershell
# Basic usage
.\prepare-job.ps1 input.mp4                     # Windows
./prepare-job.sh input.mp4                      # Linux/macOS

# With time clipping
.\prepare-job.ps1 input.mp4 -StartTime 00:00:10 -EndTime 00:01:00

# Workflow options
.\prepare-job.ps1 input.mp4 -Transcribe         # Transcribe only
.\prepare-job.ps1 input.mp4 -SubtitleGen        # Full subtitles (default)
```

**Duration:** 5-30 seconds (80-90% faster than before!)

---

### Run Pipeline

```powershell
# Auto-detect mode (uses native if available)
.\run_pipeline.ps1 -Job <job-id>                # Windows
./run_pipeline.sh -j <job-id>                   # Linux/macOS

# Force specific mode
.\run_pipeline.ps1 -Job <job-id> -Mode docker-gpu
```

---

## 🔄 Migration from Old Scripts

### ❌ Old Way (Deprecated)

```powershell
# DON'T use these anymore
.\prepare-job-venv.ps1 input.mp4
.\prepare-job-venv.sh input.mp4
```

### ✅ New Way (Recommended)

```powershell
# Use these instead
.\prepare-job.ps1 input.mp4
./prepare-job.sh input.mp4
```

**Benefits:**
- 80-90% faster (5-30 sec vs 1-2 min)
- No temporary venv creation
- Uses cached hardware info
- Simpler workflow

---

## 📊 Performance Comparison

| Operation | Before | After | Speedup |
|-----------|--------|-------|---------|
| **Job Preparation** | 1-2 min | 5-30 sec | **4-8x** |
| **Docker Build** | 30-45 min | 2-30 min | **2-15x** |
| **Disk Usage** | 50 GB | 2-20 GB | **2.5-25x** |

---

## 🗂️ File Locations

```
cp-whisperx-app/
├── scripts/
│   ├── bootstrap.ps1              # One-time setup
│   ├── bootstrap.sh               # One-time setup
│   ├── docker-build.ps1           # Build Docker images
│   ├── docker-build.sh            # Build Docker images
│   ├── prepare-job.py             # Core job preparation
│   └── ...
├── shared/
│   └── hardware_detection.py      # Hardware detection module
├── out/
│   └── hardware_cache.json        # Hardware cache (1-hour validity)
├── prepare-job.ps1                # Windows wrapper (simplified)
├── prepare-job.sh                 # Linux/macOS wrapper (simplified)
├── prepare-job-venv.ps1           # ⚠️ DEPRECATED
└── prepare-job-venv.sh            # ⚠️ DEPRECATED
```

---

## 🆘 Troubleshooting

### "Bootstrap not run"

**Solution:**
```powershell
.\scripts\bootstrap.ps1
```

### "Hardware cache not found"

**Solution:** Cache expires after 1 hour. It will be auto-detected if missing.

### Docker images too large

**Solution:** Rebuild with native mode
```powershell
.\scripts\docker-build.ps1 -Mode native
```

### prepare-job is slow

**Solution:** Make sure you're using the new script:
```powershell
.\prepare-job.ps1 input.mp4   # ✅ Fast (5-30 sec)
# NOT
.\prepare-job-venv.ps1 input.mp4   # ❌ Slow (1-2 min, deprecated)
```

---

## 📚 Documentation

- **Full Plan:** [docs/SCRIPT_CONSOLIDATION_BEST_PRACTICES.md](SCRIPT_CONSOLIDATION_BEST_PRACTICES.md)
- **Migration:** [docs/MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **Implementation:** [docs/PHASE_1_2_IMPLEMENTATION_SUMMARY.md](PHASE_1_2_IMPLEMENTATION_SUMMARY.md)
- **Main README:** [README.md](../README.md)

---

## ✅ Validation Checklist

After setup, verify:

- [ ] `.bollyenv` directory exists
- [ ] `out/hardware_cache.json` exists
- [ ] Docker images built: `docker images rajiup/cp-whisperx-app-*`
- [ ] prepare-job completes in < 30 seconds
- [ ] Pipeline runs successfully

---

## 🎯 Key Takeaways

1. **Run bootstrap once** - Creates `.bollyenv` with all dependencies
2. **Build minimal images** - Native mode is default and fastest
3. **Use new prepare-job** - 80-90% faster than prepare-job-venv
4. **Hardware caching** - Auto-detected and cached for 1 hour
5. **Backward compatible** - Old scripts still work (with warnings)

---

**Version:** 2.0  
**Last Updated:** 2024-11-06  
**Status:** ✅ Production Ready
