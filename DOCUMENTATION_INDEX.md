# CP-WhisperX-App Documentation Index

**Last Updated:** November 4, 2025

## Quick Start

- **[README.md](README.md)** - Main project documentation and overview
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide for new users

---

## Setup & Configuration

### Platform-Specific Setup
- **[WINDOWS_11_SETUP_GUIDE.md](WINDOWS_11_SETUP_GUIDE.md)** - Complete Windows 11 setup guide
  - Docker Desktop configuration
  - WSL2 setup
  - CUDA support
  - Prerequisites and troubleshooting

### API Configuration
- **[docs/TMDB_API_SETUP.md](docs/TMDB_API_SETUP.md)** - TMDB API key setup
  - Account creation
  - API key generation
  - Configuration placement

---

## Docker

### Core Documentation
- **[docker/README.md](docker/README.md)** - Complete Docker image documentation
  - All 14 images documented
  - Base images: cpu, cuda
  - CPU-only stages (6)
  - GPU stages (4-6)
  - Build instructions
  - Volume mounts
  - Environment variables

### Build & Optimization
- **[DOCKER_BUILD_OPTIMIZATION.md](DOCKER_BUILD_OPTIMIZATION.md)** - Build order and caching strategy
  - Phase-based build sequence
  - Layer caching benefits
  - 50% time/space savings
  - Error handling
  - Best practices

- **[DOCKER_REFACTORING_SUMMARY.md](DOCKER_REFACTORING_SUMMARY.md)** - Docker tagging refactoring
  - CPU-only stages: :cpu tag
  - GPU stages: :cuda tag
  - Migration guide
  - Breaking changes
  - Benefits

### GPU & Performance
- **[GPU_FALLBACK_GUIDE.md](GPU_FALLBACK_GUIDE.md)** - Automatic GPU-to-CPU fallback
  - Dual-variant architecture (:cuda + :cpu)
  - Fallback decision tree
  - Usage examples
  - Performance comparison
  - Troubleshooting

- **[CUDA_ACCELERATION_GUIDE.md](CUDA_ACCELERATION_GUIDE.md)** - GPU acceleration performance
  - Stage-by-stage benchmarks
  - 12-25x speedup metrics
  - CUDA requirements
  - GPU memory usage

- **[MPS_ACCELERATION_GUIDE.md](MPS_ACCELERATION_GUIDE.md)** - Apple Silicon GPU support
  - MPS (Metal Performance Shaders) acceleration
  - M1/M2/M3 Mac support
  - Setup and configuration

---

## Pipeline & Workflow

### Core Pipeline
- **[WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** - Pipeline workflow overview
  - Stage-by-stage flow
  - Input/output specifications
  - Dependencies

- **[PIPELINE_RESUME_GUIDE.md](PIPELINE_RESUME_GUIDE.md)** - Resume interrupted pipelines
  - Checkpoint system
  - Resume from any stage
  - State recovery

- **[docs/PIPELINE_BEST_PRACTICES.md](docs/PIPELINE_BEST_PRACTICES.md)** - Pipeline best practices
  - Performance optimization
  - Error handling
  - Resource management
  - Production deployment

### Job Management
- **[docs/JOB_ORCHESTRATION.md](docs/JOB_ORCHESTRATION.md)** - Job orchestration system
  - Job structure
  - Scheduling
  - Parallel execution

- **[docs/MANIFEST_SYSTEM_GUIDE.md](docs/MANIFEST_SYSTEM_GUIDE.md)** - Manifest tracking system
  - Manifest format
  - Stage tracking
  - Resume capabilities

- **[docs/MANIFEST_TRACKING.md](docs/MANIFEST_TRACKING.md)** - Detailed manifest tracking
  - Implementation details
  - State management

---

## Development

### Developer Resources
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Developer guide
  - Project structure
  - Development workflow
  - Code standards
  - Testing

- **[docs/IMPLEMENTATION_UNIFORMITY.md](docs/IMPLEMENTATION_UNIFORMITY.md)** - Implementation standards
  - Consistent directory structure
  - Logging standards
  - Cross-platform uniformity

- **[docs/HARDWARE_OPTIMIZATION.md](docs/HARDWARE_OPTIMIZATION.md)** - Hardware detection and optimization
  - Automatic hardware detection
  - Parameter tuning logic
  - Job configuration optimization
  - Resource-based recommendations

### Testing
- **[docs/TEST_PLAN.md](docs/TEST_PLAN.md)** - Comprehensive test plan
  - Unit tests
  - Integration tests
  - End-to-end tests
  - Platform testing matrix

### Logging
- **[docs/LOGGING.md](docs/LOGGING.md)** - Logging system documentation
  - Logger configuration
  - Log levels
  - Output formats

- **[docs/LOGGING_STANDARD.md](docs/LOGGING_STANDARD.md)** - Logging standards
  - Naming conventions
  - Format specifications
  - Best practices

---

## Platform-Specific

### Windows
- **[WINDOWS_SCRIPTS.md](WINDOWS_SCRIPTS.md)** - Windows batch scripts
  - Available scripts
  - Usage examples
  - PowerShell alternatives

### Device Selection
- **[DEVICE_SELECTION_GUIDE.md](DEVICE_SELECTION_GUIDE.md)** - Device selection guide
  - CPU vs GPU
  - Device detection
  - Fallback strategies

---

## Additional Resources

### VAD Comparison
- **[docs/README-SILERO-PYANNOTE-VAD.md](docs/README-SILERO-PYANNOTE-VAD.md)** - VAD comparison
  - Silero VAD (coarse)
  - PyAnnote VAD (refined)
  - Performance trade-offs

---

## Documentation by Use Case

### 🚀 I want to get started quickly
1. [README.md](README.md) - Understand the project
2. [QUICKSTART.md](QUICKSTART.md) - Run your first pipeline
3. [WINDOWS_11_SETUP_GUIDE.md](WINDOWS_11_SETUP_GUIDE.md) - Platform setup

### 🐳 I want to use Docker
1. [docker/README.md](docker/README.md) - Understand all images
2. [DOCKER_BUILD_OPTIMIZATION.md](DOCKER_BUILD_OPTIMIZATION.md) - Build efficiently
3. [GPU_FALLBACK_GUIDE.md](GPU_FALLBACK_GUIDE.md) - Use GPU with fallback

### ⚡ I want GPU acceleration
1. [CUDA_ACCELERATION_GUIDE.md](CUDA_ACCELERATION_GUIDE.md) - GPU performance
2. [GPU_FALLBACK_GUIDE.md](GPU_FALLBACK_GUIDE.md) - Automatic fallback
3. [MPS_ACCELERATION_GUIDE.md](MPS_ACCELERATION_GUIDE.md) - Apple Silicon

### 🔧 I want to develop/contribute
1. [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Development workflow
2. [docs/PIPELINE_BEST_PRACTICES.md](docs/PIPELINE_BEST_PRACTICES.md) - Best practices
3. [docs/TEST_PLAN.md](docs/TEST_PLAN.md) - Testing strategy

### 📊 I want to understand the pipeline
1. [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Pipeline stages
2. [docs/JOB_ORCHESTRATION.md](docs/JOB_ORCHESTRATION.md) - Job system
3. [PIPELINE_RESUME_GUIDE.md](PIPELINE_RESUME_GUIDE.md) - Resume capability

---

## Document Status

### ✅ Current & Maintained
- All documents listed above are current as of November 2025
- Docker documentation reflects new tagging strategy (cpu/cuda)
- GPU fallback feature fully documented

### 🗑️ Removed (Outdated)
- `BUILD_STATUS.md` - Old build status
- `DEPLOYMENT_STATUS.md` - Old deployment status
- `FINAL_STATUS.md` - Old final status
- `PROJECT_STATUS.md` - Old project status
- `COMPLETE_SUMMARY.md` - Old summary
- `DOCKER_CUDA_TODO.md` - Completed TODO
- `DOCKER_BUILD_GUIDE.md` - Superseded by DOCKER_BUILD_OPTIMIZATION.md
- `docs/README.DOCKER.md` - Superseded by docker/README.md
- `docs/README-CUDA.md` - Superseded by CUDA_ACCELERATION_GUIDE.md
- `TEST_PLAN.md` (root) - Duplicate of docs/TEST_PLAN.md

---

## Contributing to Documentation

When adding new documentation:
1. Add entry to this index
2. Use clear, descriptive titles
3. Include last updated date
4. Cross-reference related documents
5. Update "Document Status" section

---

**Total Documents:** 23 files (organized and current)
