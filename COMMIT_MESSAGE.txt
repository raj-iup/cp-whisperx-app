feat: Complete platform-aware pipeline with uniform implementation

Major Features:
- Directory structure with USER_ID support (out/YYYY/MM/DD/<user-id>/<job-id>/)
- Platform-aware execution (macOS native, Linux/Windows CUDA containers)
- Template-based job configuration (config/.env.pipeline)
- Unified logging standard across all execution modes
- Docker registry preparation with build/push scripts
- Comprehensive testing and documentation

Changes:
- Refactored prepare-job.py for template-based config
- Enhanced pipeline.py with platform detection and CUDA support
- Updated docker-compose.yml (removed stale mounts)
- Created CUDA base Dockerfile for Linux/Windows
- Fixed all Dockerfiles for consistency
- Unified output directory structure across all modes

Documentation:
- QUICKSTART.md - 5-minute quick start guide
- TEST_PLAN.md - Comprehensive test plan with checklists
- IMPLEMENTATION_UNIFORMITY.md - Uniformity verification
- DOCKER_BUILD_GUIDE.md - Docker build and registry guide
- DEVELOPER_GUIDE.md - Complete developer setup guide

Platform Support:
- macOS: Native MPS execution for ML stages
- Linux: CUDA Docker containers with --gpus all
- Windows: CUDA Docker containers with --gpus all
- All platforms: CPU fallback mode

Breaking Changes:
- Jobs now stored in out/ structure instead of jobs/ directory
- Logs now inside job output directory (out/.../logs/)
- Config template changed to config/.env.pipeline

Migration:
- Old jobs still supported (backwards compatible)
- New jobs use new structure exclusively
- No action required for existing deployments

Tested:
- macOS MPS native mode
- macOS Docker CPU mode
- Docker image builds (13 images)
- Job creation and configuration
- Pipeline orchestration

Pending Tests:
- Linux CUDA mode
- Windows CUDA mode
- Performance benchmarking

Files: 161 changed
Lines: ~5000+ additions, ~2000 deletions
