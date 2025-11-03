# CP-WhisperX-App Documentation Index

**Complete guide to all documentation - organized by topic**

Last Updated: November 03, 2025

> **📚 Quick Access:** Start with [README.md](README.md) for overview, then [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for setup.

---

## 🚀 Quick Start

Start here if you're new to the project:

| Document | Description | Audience |
|----------|-------------|----------|
| [README.md](README.md) | Project overview and main documentation | All Users |
| [QUICKSTART.md](QUICKSTART.md) | Get started in 5 minutes | New Users |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | Complete setup for all platforms | Developers |

---

## 📋 Platform Setup Guides

Platform-specific setup instructions:

| Platform | Document | Key Topics |
|----------|----------|------------|
| **Windows** | [WINDOWS_11_SETUP_GUIDE.md](WINDOWS_11_SETUP_GUIDE.md) | WSL2, Docker Desktop, CUDA setup |
| **Linux** | [CUDA_ACCELERATION_GUIDE.md](CUDA_ACCELERATION_GUIDE.md) | NVIDIA drivers, Container Toolkit |
| **macOS** | [MPS_ACCELERATION_GUIDE.md](MPS_ACCELERATION_GUIDE.md) | Apple Silicon, native execution |
| **All** | [DEVICE_SELECTION_GUIDE.md](DEVICE_SELECTION_GUIDE.md) | GPU detection, device selection |

---

## 🐳 Docker & Deployment

Docker building, deployment, and registry:

| Document | Purpose | Use When |
|----------|---------|----------|
| [DOCKER_BUILD_GUIDE.md](DOCKER_BUILD_GUIDE.md) | Building and pushing Docker images | Building images locally |
| [docs/README.DOCKER.md](docs/README.DOCKER.md) | Docker architecture and usage | Understanding Docker setup |
| [docs/README-CUDA.md](docs/README-CUDA.md) | CUDA-specific Docker configuration | Setting up GPU containers |
| [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) | Current deployment status | Checking build progress |

---

## 🔧 Pipeline & Workflow

Pipeline operation, configuration, and workflows:

| Document | Purpose | Use When |
|----------|---------|----------|
| [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) | Available workflows and modes | Choosing workflow |
| [PIPELINE_RESUME_GUIDE.md](PIPELINE_RESUME_GUIDE.md) | Resume failed pipelines | Pipeline interrupted |
| [docs/JOB_ORCHESTRATION.md](docs/JOB_ORCHESTRATION.md) | Job creation and management | Understanding job system |
| [docs/PIPELINE_BEST_PRACTICES.md](docs/PIPELINE_BEST_PRACTICES.md) | Best practices and tips | Optimizing pipeline |

---

## 📊 Testing & Quality

Testing procedures and checklists:

| Document | Purpose | Use When |
|----------|---------|----------|
| [TEST_PLAN.md](TEST_PLAN.md) | Comprehensive test plan with checklists | Testing all modes |
| [docs/TEST_PLAN.md](docs/TEST_PLAN.md) | Additional testing procedures | Extended testing |

---

## 🏗️ Architecture & Design

System architecture and implementation details:

| Document | Purpose | Use When |
|----------|---------|----------|
| [IMPLEMENTATION_UNIFORMITY.md](IMPLEMENTATION_UNIFORMITY.md) | Uniform implementation across modes | Understanding consistency |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Current project status and features | Getting overview |
| [docs/MANIFEST_SYSTEM_GUIDE.md](docs/MANIFEST_SYSTEM_GUIDE.md) | Manifest tracking system | Understanding job tracking |
| [docs/MANIFEST_TRACKING.md](docs/MANIFEST_TRACKING.md) | Manifest implementation details | Deep dive on tracking |

---

## 📝 Logging & Monitoring

Logging standards and monitoring:

| Document | Purpose | Use When |
|----------|---------|----------|
| [docs/LOGGING_STANDARD.md](docs/LOGGING_STANDARD.md) | Logging format and conventions | Understanding logs |
| [docs/LOGGING.md](docs/LOGGING.md) | Logging implementation | Implementing logging |

---

## �� Stage-Specific Documentation

Individual pipeline stage documentation:

| Stage | Document | Purpose |
|-------|----------|---------|
| **VAD** | [docs/README-SILERO-PYANNOTE-VAD.md](docs/README-SILERO-PYANNOTE-VAD.md) | Voice Activity Detection stages |
| **TMDB** | [docs/TMDB_API_SETUP.md](docs/TMDB_API_SETUP.md) | TMDB API configuration |

---

## 📦 Status & Summary Documents

Project status and completion summaries:

| Document | Purpose | Current Status |
|----------|---------|----------------|
| [FINAL_STATUS.md](FINAL_STATUS.md) | Final deployment status | Complete |
| [COMPLETE_SUMMARY.md](COMPLETE_SUMMARY.md) | Implementation summary | Complete |
| [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) | Deployment tracking | In Progress |

---

## 📚 Documentation by Use Case

### "I want to get started quickly"
1. [README.md](README.md) - Project overview
2. [QUICKSTART.md](QUICKSTART.md) - 5-minute setup
3. [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Choose your workflow

### "I'm setting up on Windows"
1. [WINDOWS_11_SETUP_GUIDE.md](WINDOWS_11_SETUP_GUIDE.md) - Windows-specific setup
2. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - General developer guide
3. [CUDA_ACCELERATION_GUIDE.md](CUDA_ACCELERATION_GUIDE.md) - GPU acceleration
4. [DOCKER_BUILD_GUIDE.md](DOCKER_BUILD_GUIDE.md) - Build Docker images

### "I'm setting up on Linux"
1. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Developer setup
2. [CUDA_ACCELERATION_GUIDE.md](CUDA_ACCELERATION_GUIDE.md) - NVIDIA GPU setup
3. [DOCKER_BUILD_GUIDE.md](DOCKER_BUILD_GUIDE.md) - Docker images

### "I'm setting up on macOS"
1. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Developer setup
2. [MPS_ACCELERATION_GUIDE.md](MPS_ACCELERATION_GUIDE.md) - Apple Silicon acceleration
3. [DEVICE_SELECTION_GUIDE.md](DEVICE_SELECTION_GUIDE.md) - Device configuration

### "I need to build Docker images"
1. [DOCKER_BUILD_GUIDE.md](DOCKER_BUILD_GUIDE.md) - Build guide
2. [docs/README.DOCKER.md](docs/README.DOCKER.md) - Docker architecture
3. [docs/README-CUDA.md](docs/README-CUDA.md) - GPU containers

### "I'm testing the pipeline"
1. [TEST_PLAN.md](TEST_PLAN.md) - Testing procedures
2. [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Workflow selection
3. [PIPELINE_RESUME_GUIDE.md](PIPELINE_RESUME_GUIDE.md) - Error recovery

### "I need to understand the architecture"
1. [IMPLEMENTATION_UNIFORMITY.md](IMPLEMENTATION_UNIFORMITY.md) - Design principles
2. [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current state
3. [docs/JOB_ORCHESTRATION.md](docs/JOB_ORCHESTRATION.md) - Job system
4. [docs/MANIFEST_SYSTEM_GUIDE.md](docs/MANIFEST_SYSTEM_GUIDE.md) - Tracking system

### "I'm debugging an issue"
1. [PIPELINE_RESUME_GUIDE.md](PIPELINE_RESUME_GUIDE.md) - Resume guide
2. [docs/LOGGING_STANDARD.md](docs/LOGGING_STANDARD.md) - Log format
3. [docs/PIPELINE_BEST_PRACTICES.md](docs/PIPELINE_BEST_PRACTICES.md) - Best practices

### "I'm contributing to the project"
1. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Setup guide
2. [IMPLEMENTATION_UNIFORMITY.md](IMPLEMENTATION_UNIFORMITY.md) - Code standards
3. [docs/LOGGING_STANDARD.md](docs/LOGGING_STANDARD.md) - Logging standards
4. [docs/PIPELINE_BEST_PRACTICES.md](docs/PIPELINE_BEST_PRACTICES.md) - Best practices

---

## 🗂️ Complete File List

### Root Directory (16 files)
- **[COMPLETE_SUMMARY.md](COMPLETE_SUMMARY.md)** - Complete Summary
- **[CUDA_ACCELERATION_GUIDE.md](CUDA_ACCELERATION_GUIDE.md)** - Cuda Acceleration Guide
- **[DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)** - Deployment Status
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Developer Guide
- **[DEVICE_SELECTION_GUIDE.md](DEVICE_SELECTION_GUIDE.md)** - Device Selection Guide
- **[DOCKER_BUILD_GUIDE.md](DOCKER_BUILD_GUIDE.md)** - Docker Build Guide
- **[FINAL_STATUS.md](FINAL_STATUS.md)** - Final Status
- **[IMPLEMENTATION_UNIFORMITY.md](IMPLEMENTATION_UNIFORMITY.md)** - Implementation Uniformity
- **[MPS_ACCELERATION_GUIDE.md](MPS_ACCELERATION_GUIDE.md)** - Mps Acceleration Guide
- **[PIPELINE_RESUME_GUIDE.md](PIPELINE_RESUME_GUIDE.md)** - Pipeline Resume Guide
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Project Status
- **[QUICKSTART.md](QUICKSTART.md)** - Quickstart
- **[README.md](README.md)** - Readme
- **[TEST_PLAN.md](TEST_PLAN.md)** - Test Plan
- **[WINDOWS_11_SETUP_GUIDE.md](WINDOWS_11_SETUP_GUIDE.md)** - Windows 11 Setup Guide
- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Workflow Guide

### docs/ Directory (11 files)
- **[docs/JOB_ORCHESTRATION.md](docs/JOB_ORCHESTRATION.md)** - Job Orchestration
- **[docs/LOGGING.md](docs/LOGGING.md)** - Logging
- **[docs/LOGGING_STANDARD.md](docs/LOGGING_STANDARD.md)** - Logging Standard
- **[docs/MANIFEST_SYSTEM_GUIDE.md](docs/MANIFEST_SYSTEM_GUIDE.md)** - Manifest System Guide
- **[docs/MANIFEST_TRACKING.md](docs/MANIFEST_TRACKING.md)** - Manifest Tracking
- **[docs/PIPELINE_BEST_PRACTICES.md](docs/PIPELINE_BEST_PRACTICES.md)** - Pipeline Best Practices
- **[docs/README-CUDA.md](docs/README-CUDA.md)** - Readme Cuda
- **[docs/README-SILERO-PYANNOTE-VAD.md](docs/README-SILERO-PYANNOTE-VAD.md)** - Readme Silero Pyannote Vad
- **[docs/README.DOCKER.md](docs/README.DOCKER.md)** - Readme.Docker
- **[docs/TEST_PLAN.md](docs/TEST_PLAN.md)** - Test Plan
- **[docs/TMDB_API_SETUP.md](docs/TMDB_API_SETUP.md)** - Tmdb Api Setup

---

## 📖 Reading Order Recommendations

### For New Users (First Time)
1. **[README.md](README.md)** - Understand what the project does
2. **[QUICKSTART.md](QUICKSTART.md)** - Get up and running quickly
3. **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Learn available workflows
4. **[TEST_PLAN.md](TEST_PLAN.md)** - Test your setup

### For Developers (Contributing)
1. **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Complete development setup
2. **[IMPLEMENTATION_UNIFORMITY.md](IMPLEMENTATION_UNIFORMITY.md)** - Architecture and standards
3. **[docs/JOB_ORCHESTRATION.md](docs/JOB_ORCHESTRATION.md)** - Job management system
4. **[docs/LOGGING_STANDARD.md](docs/LOGGING_STANDARD.md)** - Logging conventions
5. **[docs/PIPELINE_BEST_PRACTICES.md](docs/PIPELINE_BEST_PRACTICES.md)** - Development best practices

### For System Administrators (Deployment)
1. **[DOCKER_BUILD_GUIDE.md](DOCKER_BUILD_GUIDE.md)** - Build container images
2. **[DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)** - Current deployment state
3. **[docs/README.DOCKER.md](docs/README.DOCKER.md)** - Docker architecture
4. **[TEST_PLAN.md](TEST_PLAN.md)** - Verify deployment

### For Testers (QA)
1. **[TEST_PLAN.md](TEST_PLAN.md)** - Complete test procedures
2. **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Test all workflows
3. **[PIPELINE_RESUME_GUIDE.md](PIPELINE_RESUME_GUIDE.md)** - Error recovery testing
4. **[docs/PIPELINE_BEST_PRACTICES.md](docs/PIPELINE_BEST_PRACTICES.md)** - Testing best practices

---

## 🔍 Quick Reference

### Configuration Files
- **config/.env.pipeline** - Pipeline configuration template
- **config/secrets.example.json** - Secrets template
- **canon_map.yaml** - Name canonicalization rules

### Key Commands
```bash
# Prepare a job
python prepare-job.py video.mp4 --native

# Run pipeline
python pipeline.py --job <job-id>

# Resume from failure
python pipeline.py --job <job-id> --resume

# Test with clip
python prepare-job.py video.mp4 --start-time 00:00:00 --end-time 00:01:00

# Build Docker images
./scripts/build-all-images.sh

# Push to registry
./scripts/push-all-images.sh
```

### Key Directories
```
out/                 - All outputs (organized by date/user/job)
  └── YYYY/MM/DD/
      └── <user-id>/
          └── <job-id>/
              ├── logs/           - Stage logs
              ├── manifest.json   - Job tracking
              └── ...             - Stage outputs

config/              - Configuration templates
docker/              - Docker stage definitions
native/              - Native execution scripts
scripts/             - Build and utility scripts
shared/              - Shared utilities
```

### Docker Tags
- **:cpu** - CPU-optimized images (all platforms)
- **:cuda** - CUDA-accelerated images (NVIDIA GPU)

All images use `:cpu` tag by default. CUDA variants coming soon for GPU acceleration.

---

## 🆘 Getting Help

### 1. Check Documentation
Use this index to find relevant documentation:
- Browse by **topic** (Quick Start, Docker, Pipeline, etc.)
- Find by **use case** ("I'm setting up on Windows")
- Follow **reading order** recommendations

### 2. View Logs
```bash
# Orchestrator logs
cat out/<job-id>/logs/orchestrator_<timestamp>.log

# Stage logs (sequential numbering)
cat out/<job-id>/logs/01_demux_<timestamp>.log
cat out/<job-id>/logs/02_tmdb_<timestamp>.log
```

### 3. Check Job Status
```bash
# View manifest
cat out/<job-id>/manifest.json

# Check what stages completed
python -m json.tool out/<job-id>/manifest.json | grep completed_at
```

### 4. Resume Pipeline
```bash
# Automatically resume from last successful stage
python pipeline.py --job <job-id> --resume
```

### 5. Test with Clips
```bash
# Test on 1-minute clip before processing full video
python prepare-job.py video.mp4 \
  --start-time 00:05:00 \
  --end-time 00:06:00 \
  --native
```

---

## 🔄 Recent Updates

### November 3, 2025
- ✅ Switched to `:cpu` Docker tags exclusively (removed `:latest` duplicates)
- ✅ Updated docker-compose.yml to use registry images only
- ✅ Created comprehensive documentation index
- ✅ Verified all documentation links
- ✅ Saved ~22GB disk space by removing duplicate tags

### Project Status
- **Documentation:** Complete (27 files)
- **Docker Images:** Ready (13 CPU images)
- **Platform Support:** Windows, Linux, macOS
- **Execution Modes:** Native + Docker

---

## 📅 Documentation Maintenance

**Last Review:** November 03, 2025  
**Version:** 1.1.0  
**Status:** ✅ Complete and Verified

### Contributing to Documentation
- Keep documents focused and concise
- Update this index when adding new docs
- Follow existing formatting conventions
- Include practical examples
- Test all links before committing

### Link Verification
All 27 documentation files verified and accessible.
No broken links as of last update.

---

## 🔗 Quick Navigation

**Main Documentation:**
- [📚 README](README.md) - Project overview
- [🚀 Quick Start](QUICKSTART.md) - 5-minute setup
- [👨‍💻 Developer Guide](DEVELOPER_GUIDE.md) - Complete setup
- [🧪 Test Plan](TEST_PLAN.md) - Testing procedures

**Platform Setup:**
- [🪟 Windows Guide](WINDOWS_11_SETUP_GUIDE.md)
- [🐧 Linux/CUDA Guide](CUDA_ACCELERATION_GUIDE.md)
- [🍎 macOS/MPS Guide](MPS_ACCELERATION_GUIDE.md)

**Architecture:**
- [🏗️ Uniformity Guide](IMPLEMENTATION_UNIFORMITY.md)
- [📊 Project Status](PROJECT_STATUS.md)
- [🔧 Job Orchestration](docs/JOB_ORCHESTRATION.md)

---

**📌 Tip:** Bookmark this page for easy access to all documentation!

**Repository:** https://github.com/raj-iup/cp-whisperx-app  
**Documentation Index:** [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
