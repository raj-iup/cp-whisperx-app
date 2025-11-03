# CP-WhisperX-App Documentation Index

**Complete guide to all documentation - organized by topic**

Last Updated: November 3, 2025

---

## 🚀 Quick Start

Start here if you're new to the project:

| Document | Description | Audience |
|----------|-------------|----------|
| [QUICKSTART.md](QUICKSTART.md) | Get started in 5 minutes | All Users |
| [README.md](README.md) | Project overview and main documentation | All Users |
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

## 🔌 Stage-Specific Documentation

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
1. [QUICKSTART.md](QUICKSTART.md)
2. [README.md](README.md)
3. [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)

### "I'm setting up on Windows"
1. [WINDOWS_11_SETUP_GUIDE.md](WINDOWS_11_SETUP_GUIDE.md)
2. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) → Windows section
3. [CUDA_ACCELERATION_GUIDE.md](CUDA_ACCELERATION_GUIDE.md)
4. [DOCKER_BUILD_GUIDE.md](DOCKER_BUILD_GUIDE.md)

### "I'm setting up on Linux"
1. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) → Linux section
2. [CUDA_ACCELERATION_GUIDE.md](CUDA_ACCELERATION_GUIDE.md)
3. [DOCKER_BUILD_GUIDE.md](DOCKER_BUILD_GUIDE.md)

### "I'm setting up on macOS"
1. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) → macOS section
2. [MPS_ACCELERATION_GUIDE.md](MPS_ACCELERATION_GUIDE.md)
3. [DEVICE_SELECTION_GUIDE.md](DEVICE_SELECTION_GUIDE.md)

### "I need to build Docker images"
1. [DOCKER_BUILD_GUIDE.md](DOCKER_BUILD_GUIDE.md)
2. [docs/README.DOCKER.md](docs/README.DOCKER.md)
3. [docs/README-CUDA.md](docs/README-CUDA.md) (for GPU)

### "I'm testing the pipeline"
1. [TEST_PLAN.md](TEST_PLAN.md)
2. [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)
3. [PIPELINE_RESUME_GUIDE.md](PIPELINE_RESUME_GUIDE.md)

### "I need to understand the architecture"
1. [IMPLEMENTATION_UNIFORMITY.md](IMPLEMENTATION_UNIFORMITY.md)
2. [PROJECT_STATUS.md](PROJECT_STATUS.md)
3. [docs/JOB_ORCHESTRATION.md](docs/JOB_ORCHESTRATION.md)
4. [docs/MANIFEST_SYSTEM_GUIDE.md](docs/MANIFEST_SYSTEM_GUIDE.md)

### "I'm debugging an issue"
1. [PIPELINE_RESUME_GUIDE.md](PIPELINE_RESUME_GUIDE.md)
2. [docs/LOGGING_STANDARD.md](docs/LOGGING_STANDARD.md)
3. [docs/PIPELINE_BEST_PRACTICES.md](docs/PIPELINE_BEST_PRACTICES.md)

### "I'm contributing to the project"
1. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
2. [IMPLEMENTATION_UNIFORMITY.md](IMPLEMENTATION_UNIFORMITY.md)
3. [docs/LOGGING_STANDARD.md](docs/LOGGING_STANDARD.md)
4. [docs/PIPELINE_BEST_PRACTICES.md](docs/PIPELINE_BEST_PRACTICES.md)

---

## 🗂️ Complete File List

### Root Directory
```
QUICKSTART.md                    - 5-minute quick start
README.md                        - Main project documentation
DEVELOPER_GUIDE.md               - Complete developer setup
COMPLETE_SUMMARY.md              - Implementation summary
CUDA_ACCELERATION_GUIDE.md       - CUDA setup guide
DEPLOYMENT_STATUS.md             - Deployment tracking
DEVICE_SELECTION_GUIDE.md        - Device selection guide
DOCKER_BUILD_GUIDE.md            - Docker build reference
FINAL_STATUS.md                  - Final deployment status
IMPLEMENTATION_UNIFORMITY.md     - Uniformity verification
MPS_ACCELERATION_GUIDE.md        - macOS MPS setup
PIPELINE_RESUME_GUIDE.md         - Resume guide
PROJECT_STATUS.md                - Project overview
TEST_PLAN.md                     - Comprehensive test plan
WINDOWS_11_SETUP_GUIDE.md        - Windows setup guide
WORKFLOW_GUIDE.md                - Workflow documentation
```

### docs/ Directory
```
docs/JOB_ORCHESTRATION.md        - Job management
docs/LOGGING.md                  - Logging implementation
docs/LOGGING_STANDARD.md         - Logging standards
docs/MANIFEST_SYSTEM_GUIDE.md    - Manifest system
docs/MANIFEST_TRACKING.md        - Manifest tracking
docs/PIPELINE_BEST_PRACTICES.md  - Best practices
docs/README-CUDA.md              - CUDA Docker setup
docs/README-SILERO-PYANNOTE-VAD.md - VAD stages
docs/README.DOCKER.md            - Docker architecture
docs/TEST_PLAN.md                - Testing procedures
docs/TMDB_API_SETUP.md           - TMDB API setup
```

---

## 📖 Reading Order Recommendations

### For New Users (First Time)
1. QUICKSTART.md
2. README.md
3. WORKFLOW_GUIDE.md
4. TEST_PLAN.md

### For Developers (Contributing)
1. DEVELOPER_GUIDE.md
2. IMPLEMENTATION_UNIFORMITY.md
3. docs/JOB_ORCHESTRATION.md
4. docs/LOGGING_STANDARD.md
5. docs/PIPELINE_BEST_PRACTICES.md

### For System Administrators (Deployment)
1. DOCKER_BUILD_GUIDE.md
2. DEPLOYMENT_STATUS.md
3. docs/README.DOCKER.md
4. TEST_PLAN.md

### For Testers (QA)
1. TEST_PLAN.md
2. WORKFLOW_GUIDE.md
3. PIPELINE_RESUME_GUIDE.md
4. docs/PIPELINE_BEST_PRACTICES.md

---

## 🔍 Quick Reference

### Configuration
- Job preparation: `prepare-job.py --help`
- Pipeline execution: `pipeline.py --help`
- Config template: `config/.env.pipeline`

### Common Commands
```bash
# Quick start
python prepare-job.py video.mp4 --native
python pipeline.py --job <job-id>

# Build images
./scripts/build-all-images.sh

# Test
python prepare-job.py test.mp4 --start-time 00:00:00 --end-time 00:01:00
```

### Key Directories
```
out/                 - All outputs (organized by date/user/job)
config/              - Configuration templates
docker/              - Docker stage definitions
native/              - Native execution scripts (macOS)
scripts/             - Build and utility scripts
shared/              - Shared utilities
```

---

## 🆘 Getting Help

1. **Check documentation**: Use this index to find relevant docs
2. **View logs**: `out/<job-id>/logs/`
3. **Check manifest**: `out/<job-id>/manifest.json`
4. **Resume pipeline**: `python pipeline.py --job <job-id> --resume`
5. **Test with clip**: Use `--start-time` and `--end-time` for quick tests

---

## 📅 Documentation Maintenance

**Last Review:** November 3, 2025  
**Version:** 1.0.0  
**Status:** ✅ Complete

### Contributing to Documentation
- Keep documents focused and concise
- Update this index when adding new docs
- Follow existing formatting conventions
- Include examples and use cases

---

**Navigation:**
- [📚 Main Documentation](README.md)
- [🚀 Quick Start](QUICKSTART.md)
- [👨‍💻 Developer Guide](DEVELOPER_GUIDE.md)
- [🧪 Test Plan](TEST_PLAN.md)
