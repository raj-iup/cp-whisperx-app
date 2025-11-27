# CP-WhisperX-App Documentation Index
**Complete Documentation for the Audio Transcription & Translation Pipeline**

---

## 📚 Getting Started

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | 5-minute quick start guide |
| [user-guide/BOOTSTRAP.md](user-guide/BOOTSTRAP.md) | Installation and setup |
| [user-guide/workflows.md](user-guide/workflows.md) | Workflow modes explained |
| [user-guide/prepare-job.md](user-guide/prepare-job.md) | Job preparation guide |

---

## 🔧 User Guides

### Setup & Configuration
- [BOOTSTRAP.md](user-guide/BOOTSTRAP.md) - Installation and environment setup
- [prepare-job.md](user-guide/prepare-job.md) - Creating jobs
- [workflows.md](user-guide/workflows.md) - Transcribe, translate, subtitle modes
- [troubleshooting.md](user-guide/troubleshooting.md) - Common issues and solutions

### Features
- [Hybrid Translation](features/) - LLM + IndicTrans2 ensemble
- [Glossary Builder](user-guide/glossary-builder.md) - Name/term glossaries
- [Apple Silicon Guide](user-guide/apple-silicon-guide.md) - MLX optimization
- [CPS Guide](user-guide/cps-guide.md) - Characters per second tuning

---

## 🏗️ Technical Documentation

### Architecture & Design
- **[CODEBASE_DEPENDENCY_MAP.md](CODEBASE_DEPENDENCY_MAP.md)** - Complete architecture reference
- [technical/architecture.md](technical/architecture.md) - System design
- [technical/pipeline.md](technical/pipeline.md) - Pipeline stages
- [technical/multi-environment.md](technical/multi-environment.md) - Virtual environment isolation

### Development
- **[DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md)** - ⭐ Official development standards
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Developer standards
- [DEVELOPER_QUICK_REF.md](DEVELOPER_QUICK_REF.md) - Quick reference
- [technical/debug-logging.md](technical/debug-logging.md) - Logging system
- [PROCESS.md](PROCESS.md) - Development process

---

## 📝 Implementation History

### Complete Project Refactoring (2025-11-25)
- **[PROJECT_REFACTORING_COMPLETE.md](PROJECT_REFACTORING_COMPLETE.md)** - Master summary of all refactoring
- [implementation-history/ALL_PHASES_COMPLETE.md](implementation-history/ALL_PHASES_COMPLETE.md) - All phases summary
- [implementation-history/VENV_REORGANIZATION_COMPLETE.md](implementation-history/VENV_REORGANIZATION_COMPLETE.md) - Venv reorganization
- [implementation-history/INTEGRATION_COMPLETE.md](implementation-history/INTEGRATION_COMPLETE.md) - Script integration
- [implementation-history/CLEANUP_COMPLETE.md](implementation-history/CLEANUP_COMPLETE.md) - Project cleanup

### Phase-Specific Documentation
- [implementation-history/PHASE1_CRITICAL_FIXES_COMPLETE.md](implementation-history/PHASE1_CRITICAL_FIXES_COMPLETE.md) - Critical fixes
- [implementation-history/PHASE2_ENHANCEMENTS_STATUS.md](implementation-history/PHASE2_ENHANCEMENTS_STATUS.md) - Feature enhancements
- [implementation-history/PHASES_1_2_COMPLETE.md](implementation-history/PHASES_1_2_COMPLETE.md) - Phases 1 & 2 summary
- [COMPREHENSIVE_FIX_PLAN.md](COMPREHENSIVE_FIX_PLAN.md) - Original fix plan

### Change History
- [implementation-history/](implementation-history/) - All implementation documentation
- [archive/](archive/) - Historical documentation

---

## 🔍 Reference

### Standards & Guidelines
- **[DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md)** - Official development standards (v2.0.0)
  - Shell script standards
  - Python script standards
  - Documentation standards
  - Code organization
  - Logging standards
  - Testing standards
  - Git standards
  - Refactoring guidelines

### Language Support
- [technical/language-support.md](technical/language-support.md) - Supported languages
- Indian Languages: 22 scheduled languages via IndicTrans2
- Global Languages: 200+ languages via NLLB

### Configuration
- [setup/](setup/) - Configuration files and examples
- [reference/](reference/) - API reference documentation

---

## 🎯 Quick Reference

### Common Tasks
```bash
# Setup (one-time)
./bootstrap.sh

# Create job
./prepare-job.sh --media movie.mp4 --workflow subtitle \
  --source-language hi --target-language en

# Run pipeline
./run-pipeline.sh -j <job-id>

# Compare translations
./compare-beam-search.sh <job-dir> --beam-range 4,10
```

### Project Structure
```
cp-whisperx-app/
├── bootstrap.sh       Self-contained entry point
├── prepare-job.sh     Self-contained entry point
├── run-pipeline.sh    Self-contained entry point
│
├── venv/              All virtual environments (8)
├── scripts/           Implementation (92 Python, 13 shell)
├── shared/            Shared modules (23)
├── requirements/      Dependencies (8 files)
├── docs/              All documentation (you are here)
├── config/            Configuration templates
├── glossary/          Glossary files
├── tests/             Test files
├── tools/             Utility scripts
├── in/                Input media
├── out/               Output (jobs, logs, subtitles)
└── logs/              Bootstrap and system logs
```

---

## 📖 Documentation Standards

All documentation follows these guidelines:

### Location
- **Root**: Only `README.md`
- **Details**: All in `docs/` directory

### Structure
```
docs/
├── INDEX.md (this file)              Master index
├── QUICKSTART.md                     Quick start
├── DEVELOPMENT_STANDARDS.md          ⭐ Development standards
├── CODEBASE_DEPENDENCY_MAP.md        Architecture
├── PROJECT_REFACTORING_COMPLETE.md   Refactoring summary
│
├── implementation-history/           Implementation docs
├── user-guide/                       User documentation
├── technical/                        Technical docs
├── features/                         Feature guides
└── archive/                          Historical docs
```

### Writing Style
- Clear and concise
- Examples included
- Step-by-step when needed
- Status indicators (✅ ❌ ⏭️)

---

## 🆕 For New Developers

### Start Here
1. Read [README.md](../README.md) for project overview
2. Follow [QUICKSTART.md](QUICKSTART.md) to get running
3. Review [DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md) for coding guidelines
4. Study [CODEBASE_DEPENDENCY_MAP.md](CODEBASE_DEPENDENCY_MAP.md) for architecture

### Making Changes
1. Follow [DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md)
2. Test your changes
3. Update documentation
4. Submit pull request

### Key Documents
- **Standards**: [DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md) - Follow these!
- **Architecture**: [CODEBASE_DEPENDENCY_MAP.md](CODEBASE_DEPENDENCY_MAP.md) - Understand structure
- **Refactoring**: [PROJECT_REFACTORING_COMPLETE.md](PROJECT_REFACTORING_COMPLETE.md) - Recent changes

---

## 📞 Getting Help

### Documentation
- Start with this index
- Check specific guides in sections above
- Review implementation history for recent changes

### Troubleshooting
- [user-guide/troubleshooting.md](user-guide/troubleshooting.md)
- Use `--log-level DEBUG` for verbose output
- Check `logs/` directory

### Support
- **Issues**: Use GitHub Issues for bugs
- **Discussions**: Use GitHub Discussions for questions
- **Standards**: See [DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md)

---

## 🔄 Recent Updates

### 2025-11-25 - Complete Refactoring
- ✅ Created [DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md)
- ✅ Reorganized all virtual environments to `venv/`
- ✅ Made all root scripts self-contained
- ✅ Cleaned up project structure
- ✅ Updated all documentation

See [PROJECT_REFACTORING_COMPLETE.md](PROJECT_REFACTORING_COMPLETE.md) for complete details.

---

## 📋 Documentation TODO

### High Priority
- [ ] Add more code examples to standards
- [ ] Create video tutorials
- [ ] Add architecture diagrams (visual)

### Medium Priority
- [ ] Expand troubleshooting guide
- [ ] Add performance tuning guide
- [ ] Document all pipeline stages in detail

### Low Priority
- [ ] Add FAQ section
- [ ] Create glossary of terms
- [ ] Add comparison with alternatives

---

**Need something else? Check the index above or search in the documentation!**
