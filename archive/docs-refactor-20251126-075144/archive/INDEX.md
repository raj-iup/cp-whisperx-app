# 📚 Documentation Index

**cp-whisperx-app Multi-Environment Transcription & Translation Pipeline**

Welcome! This index helps you find exactly what you need.

---

## 🚀 Getting Started (New Users)

**Start Here**: [README.md](README.md) - Complete guide with quick start

**Quick Commands**:
```bash
# Setup (one-time)
./bootstrap.sh              # macOS/Linux
.\bootstrap.ps1            # Windows

# Transcribe
./prepare-job.sh movie.mp4 --transcribe -s hi
./run-pipeline.sh -j <job-id>

# Translate  
./prepare-job.sh movie.mp4 --translate -s hi -t en
./run-pipeline.sh -j <job-id>
```

---

## 📖 Documentation Files

### Primary Documentation

| File | Size | Purpose | When to Read |
|------|------|---------|--------------|
| **[README.md](README.md)** | 16KB | Complete user guide | **START HERE** - First time setup |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | 9.3KB | Command cheat sheet | Quick command lookup |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | 17KB | Problem solutions | When something doesn't work |

### Implementation Documentation

| File | Size | Purpose | When to Read |
|------|------|---------|--------------|
| **[DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md)** | 13KB | Deployment summary | **NEW** - Complete deployment status |
| **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** | 15KB | Implementation details | **NEW** - What was changed and why |
| **[SCRIPT_PARITY_REPORT.md](SCRIPT_PARITY_REPORT.md)** | 11KB | Bash/PowerShell comparison | **NEW** - Windows/Unix parity verification |
| **[EXEC_SUMMARY.md](EXEC_SUMMARY.md)** | 11KB | Executive summary | High-level overview |
| **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** | 11KB | Implementation report | Understand what was built |
| **[COMPLETE_SUMMARY.md](COMPLETE_SUMMARY.md)** | 12KB | Architecture details | Deep dive into design |
| **[LOGGING_ANALYSIS_REPORT.md](LOGGING_ANALYSIS_REPORT.md)** | 14KB | Logging architecture | Understanding logs |
| **[multi_env_summary.md](multi_env_summary.md)** | 10KB | Multi-env design | Why 4 environments? |

---

## 🔧 Scripts

### Setup Scripts

| Script | Platform | Purpose |
|--------|----------|---------|
| `bootstrap.sh` | macOS/Linux | Creates all 4 virtual environments |
| `bootstrap.ps1` | Windows | Creates all 4 virtual environments |
| `health-check.sh` | macOS/Linux | Verifies system health |

### Workflow Scripts

| Script | Platform | Purpose |
|--------|----------|---------|
| `prepare-job.sh` | macOS/Linux | Prepare transcription/translation job |
| `prepare-job.ps1` | Windows | Prepare transcription/translation job |
| `run-pipeline.sh` | macOS/Linux | Execute pipeline for prepared job |
| `run-pipeline.ps1` | Windows | Execute pipeline for prepared job |

### Deprecated Scripts (Don't use these)

| Script | Status | Alternative |
|--------|--------|-------------|
| `install-mlx.sh` | ⚠️ Deprecated | Use `./bootstrap.sh` instead |
| `install-indictrans2.sh` | ⚠️ Deprecated | Use `./bootstrap.sh` instead |

---

## 🎯 Find What You Need

### "I want to..."

#### ...get started quickly
→ [README.md - Quick Start](README.md#quick-start)

#### ...install on Windows
→ [README.md - Windows Support](README.md#windows-support)

#### ...understand the architecture
→ [EXEC_SUMMARY.md - Architecture](EXEC_SUMMARY.md#the-architecture-simplified)

#### ...fix a problem
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

#### ...find a specific command
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

#### ...understand logging
→ [README.md - Logging](README.md#logging) or [LOGGING_ANALYSIS_REPORT.md](LOGGING_ANALYSIS_REPORT.md)

#### ...check system health
→ Run `./health-check.sh`

#### ...understand multi-environment setup
→ [README.md - Multi-Environment Architecture](README.md#multi-environment-architecture)

#### ...see implementation status
→ [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)

#### ...understand what changed
→ [CHANGELOG.md](CHANGELOG.md) or [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)

---

## 🔍 By Topic

### Installation & Setup
- [README.md - Quick Start](README.md#quick-start)
- [README.md - Prerequisites](README.md#prerequisites)
- [TROUBLESHOOTING.md - Environment Issues](TROUBLESHOOTING.md#environment-issues)

### Multi-Environment Architecture
- [README.md - Multi-Environment Architecture](README.md#multi-environment-architecture)
- [EXEC_SUMMARY.md - Architecture](EXEC_SUMMARY.md#the-architecture-simplified)
- [multi_env_summary.md](multi_env_summary.md)
- [COMPLETE_SUMMARY.md](COMPLETE_SUMMARY.md)

### Workflows
- [README.md - Workflows](README.md#workflows)
- [README.md - Transcribe Workflow](README.md#1-transcribe-workflow)
- [README.md - Translate Workflow](README.md#2-translate-workflow)
- [README.md - Subtitle Workflow](README.md#3-subtitle-workflow)

### Windows Support
- [README.md - Windows Support](README.md#windows-support)
- [TROUBLESHOOTING.md - Windows-Specific Issues](TROUBLESHOOTING.md#windows-specific-issues)

### Logging
- [README.md - Logging](README.md#logging)
- [LOGGING_ANALYSIS_REPORT.md](LOGGING_ANALYSIS_REPORT.md)
- [QUICK_REFERENCE.md - Log Commands](QUICK_REFERENCE.md)

### Troubleshooting
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [TROUBLESHOOTING.md - Environment Issues](TROUBLESHOOTING.md#environment-issues)
- [TROUBLESHOOTING.md - MLX Issues](TROUBLESHOOTING.md#mlx-issues-apple-silicon)
- [TROUBLESHOOTING.md - IndicTrans2 Issues](TROUBLESHOOTING.md#indictrans2-issues)
- [TROUBLESHOOTING.md - Pipeline Failures](TROUBLESHOOTING.md#pipeline-failures)

### Advanced Topics
- [README.md - Advanced Configuration](README.md#advanced-configuration)
- [README.md - Supported Languages](README.md#supported-languages)
- [README.md - Environment Management](README.md#environment-management)

---

## 📊 Quick Facts

### Four Virtual Environments
1. **`venv/mlx`** - Apple Silicon GPU transcription (6-8x faster)
2. **`venv/whisperx`** - Standard transcription + alignment
3. **`venv/indictrans2`** - Indian language translation (90% faster)
4. **`venv/common`** - Lightweight utilities (no ML deps)

### Supported Platforms
- ✅ macOS (Apple Silicon + Intel)
- ✅ Linux (Ubuntu, Debian, CentOS, etc.)
- ✅ Windows 10/11 (Native PowerShell)

### Supported Languages
- **22 Indic Languages**: Hindi, Tamil, Telugu, Bengali, Gujarati, Kannada, Malayalam, Marathi, Punjabi, Urdu, Assamese, Odia, Nepali, Sindhi, Sinhala, Sanskrit, Kashmiri, Dogri, Manipuri, Konkani, Maithili, Santali
- **100+ Other Languages**: All Whisper-supported languages

### Key Features
- ✅ Multi-environment architecture (no dependency conflicts)
- ✅ Automatic environment selection per stage
- ✅ GPU acceleration (CUDA, MPS, MLX)
- ✅ Unified logging (Bash + PowerShell)
- ✅ Windows native support
- ✅ Comprehensive documentation
- ✅ One-command setup

---

## 🆘 Getting Help

### Step 1: Check Documentation
Most questions are answered in the documentation:
1. [README.md](README.md) - General questions
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problems and solutions
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command syntax

### Step 2: Run Health Check
```bash
./health-check.sh
```
This verifies your installation and identifies issues.

### Step 3: Check Logs
Logs are automatically created:
- **Script logs**: `logs/YYYYMMDD-HHMMSS-scriptname.log`
- **Job logs**: `out/YYYY/MM/DD/[UserID]/[counter]/logs/*.log`

### Step 4: Enable Debug Mode
```bash
# macOS/Linux
./prepare-job.sh movie.mp4 --transcribe -s hi --debug

# Windows
.\prepare-job.ps1 movie.mp4 -Workflow transcribe -SourceLanguage hi -Debug
```

---

## 📝 Version Information

**Current Version**: Multi-Environment v2.0  
**Implementation Date**: November 20, 2025  
**Status**: ✅ Production Ready

**Changes from v1.0**:
- ✅ Multi-environment architecture (was single `.bollyenv`)
- ✅ Native Windows support (was WSL only)
- ✅ Unified logging (was inconsistent)
- ✅ Comprehensive documentation (was scattered)
- ✅ Automatic environment selection (was manual)
- ✅ One-command setup (was multi-step)

---

## 🎯 Most Useful Commands

### First-Time Setup
```bash
./bootstrap.sh                # macOS/Linux
.\bootstrap.ps1              # Windows
./health-check.sh            # Verify installation
```

### Daily Usage
```bash
# Transcribe
./prepare-job.sh movie.mp4 --transcribe -s hi
./run-pipeline.sh -j <job-id>

# Translate
./prepare-job.sh movie.mp4 --translate -s hi -t en
./run-pipeline.sh -j <job-id>

# Check status
./run-pipeline.sh -j <job-id> --status

# View logs
cat logs/*-bootstrap.log
cat out/.../logs/pipeline.log
```

### Troubleshooting
```bash
./health-check.sh                      # System health
./bootstrap.sh                         # Recreate environments
cat logs/*-bootstrap.log               # Setup logs
grep "\[ERROR\]" out/.../logs/*.log    # Find errors
```

---

## 🏆 Summary

**What This Project Does**:  
Transcribes audio/video in 22 Indian languages and translates to English using state-of-the-art AI models (WhisperX, MLX-Whisper, IndicTrans2).

**Why It's Special**:
- Multi-environment architecture prevents dependency hell
- Automatic GPU acceleration (Apple Silicon, NVIDIA)
- 90% faster translation for Indian languages
- Cross-platform (macOS, Linux, Windows)
- Production-ready with comprehensive documentation

**How to Get Started**:  
Read [README.md](README.md), run `./bootstrap.sh`, and follow the examples.

---

**Happy transcribing! 🎬✨**

---

**Last Updated**: November 20, 2025  
**Maintained By**: Project Contributors  
**Status**: ✅ Production Ready
