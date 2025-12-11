# CP-WhisperX-App Documentation

**Last Updated:** December 3, 2025  
**Version:** 3.0  
**Status:** ✅ **Phase 1 Complete | Architecture v3.0 in Progress**

---

## 🎯 Quick Start

**New to this project?** Start here:

1. **[../README.md](../README.md)** ⭐ **30-Second Overview** (2 min)
   - What is CP-WhisperX-App?
   - Quick installation and first run
   - Core capabilities

2. **[ARCHITECTURE_IMPLEMENTATION_ROADMAP.md](ARCHITECTURE_IMPLEMENTATION_ROADMAP.md)** 🗺️ **Master Roadmap** (15 min)
   - System architecture (v2.0 → v3.0)
   - Implementation phases and progress
   - Testing infrastructure with standard samples
   - Core workflows: Subtitle, Transcribe, Translate

3. **[developer/DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md)** 📖 **Code Standards** (30 min)
   - StageIO pattern and best practices
   - Configuration management
   - Logging, error handling, testing
   - Pre-commit hook enforcement

---

## 📚 Documentation Structure

### 🗺️ Architecture & Planning

| Document | Purpose | Audience | Time |
|----------|---------|----------|------|
| **[ARCHITECTURE_IMPLEMENTATION_ROADMAP.md](ARCHITECTURE_IMPLEMENTATION_ROADMAP.md)** | Master roadmap: v2.0 → v3.0 | Everyone | 15 min |
| **[CODE_EXAMPLES.md](CODE_EXAMPLES.md)** | Good vs bad code patterns | Developers | 20 min |
| **[AI_MODEL_ROUTING.md](AI_MODEL_ROUTING.md)** | Model selection guide | Developers | 10 min |
| **[SUBTITLE_ACCURACY_ROADMAP.md](SUBTITLE_ACCURACY_ROADMAP.md)** | Quality improvement plan | Tech leads | 15 min |
| **[INDEX.md](INDEX.md)** | Legacy documentation index | Reference | 5 min |

### 👨‍💻 Developer Documentation

| Document | Purpose | Audience | Time |
|----------|---------|----------|------|
| **[developer/DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md)** | Code standards & patterns | Developers | 30 min |
| **[developer/getting-started.md](developer/getting-started.md)** | Development setup | New devs | 15 min |
| **[developer/contributing.md](developer/contributing.md)** | How to contribute | Contributors | 10 min |
| **[developer/MIGRATION_GUIDE.md](developer/MIGRATION_GUIDE.md)** | StageIO migration guide | Developers | 15 min |
| **[PRE_COMMIT_HOOK_GUIDE.md](PRE_COMMIT_HOOK_GUIDE.md)** | Pre-commit hook usage | Developers | 5 min |

### 📖 User Guides

Located in `user-guide/` directory:

| Document | Purpose | Time |
|----------|---------|------|
| **[README.md](user-guide/README.md)** | User guide index | 2 min |
| **[BOOTSTRAP.md](user-guide/BOOTSTRAP.md)** | Environment setup | 10 min |
| **[prepare-job.md](user-guide/prepare-job.md)** | Job preparation | 5 min |
| **[workflows.md](user-guide/workflows.md)** | Subtitle/Transcribe/Translate workflows | 10 min |
| **[configuration.md](user-guide/configuration.md)** | Configuration guide | 15 min |
| **[glossary-builder.md](user-guide/glossary-builder.md)** | Glossary creation | 10 min |
| **[troubleshooting.md](user-guide/troubleshooting.md)** | Common issues | As needed |

### 🔧 Technical Documentation

Located in `technical/` directory:

| Document | Purpose | Time |
|----------|---------|------|
| **[README.md](technical/README.md)** | Technical docs index | 2 min |
| **[architecture.md](technical/architecture.md)** | System architecture | 20 min |
| **[pipeline.md](technical/pipeline.md)** | Pipeline internals | 15 min |
| **[multi-environment.md](technical/multi-environment.md)** | MLX/CUDA/CPU support | 10 min |
| **[language-support.md](technical/language-support.md)** | Language routing | 10 min |
| **[debug-logging.md](technical/debug-logging.md)** | Debugging guide | 10 min |

### 📋 Stage Documentation

Located in `stages/` directory:

| Stage | Document | Status |
|-------|----------|--------|
| 02 TMDB | **[02_TMDB_INTEGRATION.md](stages/02_TMDB_INTEGRATION.md)** | ✅ Complete |
| 01-10 | Individual stage docs | ⏳ Planned (Phase 4) |

### 📊 Logging & Monitoring

| Document | Purpose | Time |
|----------|---------|------|
| **[logging/LOGGING_ARCHITECTURE.md](logging/LOGGING_ARCHITECTURE.md)** | Logging system design | 15 min |

### 📦 Summaries & Reports

Located in `summaries/` directory - Historical status updates and completion reports.

---

## 🎓 Learning Paths

### Path 1: New User (30 minutes)

**Goal:** Run your first transcription/translation job

1. Read: [../README.md](../README.md) - Quick overview (5 min)
2. Setup: [user-guide/BOOTSTRAP.md](user-guide/BOOTSTRAP.md) - Install dependencies (10 min)
3. Run: [user-guide/workflows.md](user-guide/workflows.md) - Your first workflow (10 min)
4. Explore: Review output files and logs (5 min)

### Path 2: New Developer (Day 1)

**Goal:** Understand architecture and start contributing

1. Read: [ARCHITECTURE_IMPLEMENTATION_ROADMAP.md](ARCHITECTURE_IMPLEMENTATION_ROADMAP.md) - System overview (15 min)
2. Read: [developer/DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md) - Code standards (30 min)
3. Setup: [developer/getting-started.md](developer/getting-started.md) - Dev environment (30 min)
4. Explore: [CODE_EXAMPLES.md](CODE_EXAMPLES.md) - Good/bad patterns (20 min)
5. Practice: Run tests and compliance checker (30 min)

**Total:** ~2 hours

### Path 3: Implementing a New Stage

**Goal:** Create a production-ready pipeline stage

1. Template: [developer/DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md) § 3 - StageIO pattern
2. Examples: Review `../scripts/02_tmdb_enrichment.py`, `../scripts/10_mux.py`
3. Create: Write your stage following StageIO pattern
4. Test: Write unit tests and integration tests
5. Verify: Run `python3 ../scripts/validate-compliance.py your_stage.py`
6. Commit: Pre-commit hook will validate automatically

**Resources:**
- [CODE_EXAMPLES.md](CODE_EXAMPLES.md) - Pattern examples
- [developer/MIGRATION_GUIDE.md](developer/MIGRATION_GUIDE.md) - Migration tips
- [PRE_COMMIT_HOOK_GUIDE.md](PRE_COMMIT_HOOK_GUIDE.md) - Validation

### Path 4: Contributing Translations/Models

**Goal:** Add support for new languages or models

1. Read: [AI_MODEL_ROUTING.md](AI_MODEL_ROUTING.md) - Model selection logic
2. Read: [technical/language-support.md](technical/language-support.md) - Language routing
3. Update: Model routing configuration
4. Test: Validate with test media samples
5. Document: Update language support table

### Path 5: Troubleshooting & Debugging

**Goal:** Diagnose and fix issues

1. Check: [user-guide/troubleshooting.md](user-guide/troubleshooting.md) - Common issues
2. Enable: [technical/debug-logging.md](technical/debug-logging.md) - Debug logging
3. Review: Job logs in `out/{job}/logs/`
4. Trace: Check manifests in stage directories
5. Ask: Open GitHub issue with logs

---

## 📊 Current Status

### Implementation Progress

**Overall:** 35% Complete (Phase 0-1 done, Phase 2 foundation ready)

| Phase | Status | Progress | Description |
|-------|--------|----------|-------------|
| Phase 0: Foundation | ✅ Complete | 100% | Standards, config, pre-commit hooks |
| Phase 1: File Naming | ✅ Complete | 100% | All 10 stages renamed to standard pattern |
| Phase 2: Testing | 🟡 Ready | 0% | Test framework, standard samples, 40+ tests |
| Phase 3: StageIO | 🔴 Blocked | 0% | Migrate 5 active stages to StageIO pattern |
| Phase 4: Integration | 🔴 Blocked | 0% | Complete 10-stage modular pipeline |
| Phase 5: Advanced | 🔴 Blocked | 0% | Caching, ML optimization, monitoring |

**Next Milestone:** Phase 2 (Testing Infrastructure) - 3 weeks

### Code Quality

**Compliance:** ✅ **100%** (GOLD Level)

| Category | Status | Details |
|----------|--------|---------|
| Type Hints | ✅ 100% | 140+ added |
| Docstrings | ✅ 100% | 80+ added |
| Logger Usage | ✅ 100% | No print() statements |
| Import Organization | ✅ 100% | Standard/Third-party/Local |
| File Naming | ✅ 100% | All stages: `{NN}_{name}.py` |
| Error Handling | ✅ 100% | Proper try/except everywhere |
| Pre-commit Hook | ✅ Active | Enforcing all standards |

### Test Coverage

| Type | Current | Target | Gap |
|------|---------|--------|-----|
| Unit Tests | 35% | 85% | +50% |
| Integration Tests | <10% | 75% | +65% |
| Stage Tests | Partial | 100% | Variable |

### Architecture Adoption

| Pattern | Adoption | Target | Gap |
|---------|----------|--------|-----|
| StageIO Pattern | 10% (1/10) | 100% | +90% |
| Manifest Tracking | 10% | 100% | +90% |
| Dual Logging | 100% | 100% | ✅ |
| Config Management | 100% | 100% | ✅ |

---

## 🔧 Common Tasks

### For Users

**Run a workflow:**
```bash
# Transcribe (English → English)
./prepare-job.sh --media in/video.mp4 --workflow transcribe --source-language en
./run-pipeline.sh --job-dir out/.../job-...

# Translate (Hindi → English)
./prepare-job.sh --media in/video.mp4 --workflow translate -s hi -t en
./run-pipeline.sh --job-dir out/.../job-...

# Subtitle (Hindi → Multiple languages)
./prepare-job.sh --media in/video.mp4 --workflow subtitle -s hi -t en,gu,ta,es
./run-pipeline.sh --job-dir out/.../job-...
```

**Test with standard samples:**
```bash
# Sample 1: English technical content
./prepare-job.sh --media "in/Energy Demand in AI.mp4" --workflow transcribe -s en

# Sample 2: Hinglish Bollywood content
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 --workflow subtitle -s hi -t en,gu
```

### For Developers

**Check code compliance:**
```bash
# Single file
python3 scripts/validate-compliance.py scripts/your_stage.py

# All staged files (pre-commit)
python3 scripts/validate-compliance.py --staged

# Strict mode (exit 1 on violations)
python3 scripts/validate-compliance.py --strict scripts/*.py
```

**Run tests:**
```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_01_demux.py

# With coverage
pytest --cov=scripts --cov=shared --cov-report=html
```

**Create a new stage:**
```bash
# 1. Copy template
cp shared/stage_template.py scripts/NN_your_stage.py

# 2. Implement stage logic following StageIO pattern

# 3. Create tests
cp tests/test_template.py tests/test_NN_your_stage.py

# 4. Validate
python3 scripts/validate-compliance.py scripts/NN_your_stage.py

# 5. Commit (pre-commit hook will validate automatically)
git add scripts/NN_your_stage.py tests/test_NN_your_stage.py
git commit -m "Add NN_your_stage"
```

**Update model routing:**
```bash
# Manual update
python3 tools/update-model-routing.py --force

# Or wait for automated weekly update (GitHub Actions)
```

---

## 📁 Directory Structure

```
docs/
├── README.md                                    # ⭐ This file - Master index
│
├── 🗺️ Architecture & Roadmaps
│   ├── ARCHITECTURE_IMPLEMENTATION_ROADMAP.md  # Master roadmap (v2.0 → v3.0)
│   ├── SUBTITLE_ACCURACY_ROADMAP.md            # Quality improvement plan
│   ├── AI_MODEL_ROUTING.md                     # Model selection guide
│   ├── CODE_EXAMPLES.md                        # Pattern examples (good/bad)
│   └── INDEX.md                                # Legacy index
│
├── 👨‍💻 developer/                               # Developer documentation
│   ├── DEVELOPER_STANDARDS.md                  # ⭐ Code standards (§1-16)
│   ├── MIGRATION_GUIDE.md                      # StageIO migration guide
│   ├── getting-started.md                      # Dev environment setup
│   └── contributing.md                         # Contribution guidelines
│
├── 📖 user-guide/                               # User documentation
│   ├── README.md                               # User guide index
│   ├── BOOTSTRAP.md                            # Environment setup
│   ├── prepare-job.md                          # Job preparation
│   ├── workflows.md                            # Subtitle/Transcribe/Translate
│   ├── configuration.md                        # Config parameters
│   ├── glossary-builder.md                     # Glossary creation
│   └── troubleshooting.md                      # Common issues
│
├── 🔧 technical/                                # Technical specs
│   ├── README.md                               # Technical docs index
│   ├── architecture.md                         # System architecture
│   ├── pipeline.md                             # Pipeline internals
│   ├── multi-environment.md                    # MLX/CUDA/CPU support
│   ├── language-support.md                     # Language routing
│   └── debug-logging.md                        # Debugging guide
│
├── 📋 stages/                                   # Stage documentation
│   ├── 02_TMDB_INTEGRATION.md                  # TMDB stage (reference)
│   └── [01-10 individual stage docs - planned]
│
├── 📊 logging/                                  # Logging docs
│   └── LOGGING_ARCHITECTURE.md                 # Logging system design
│
├── 📦 summaries/                                # Historical reports
│   ├── AI_MODEL_ROUTING_AUTOMATION_SUMMARY.md
│   ├── GITHUB_DEPLOYMENT_COMPLETE.md
│   └── [Other status updates and completion reports]
│
├── PRE_COMMIT_HOOK_GUIDE.md                    # Pre-commit hook usage
└── pull_request_template.md                    # PR template
```

---

## 🎉 Recent Achievements

**December 3, 2025:**
- ✅ Phase 1 Complete: File naming standardization (all 10 stages)
- ✅ Code cleanup: 209 redundant files removed
- ✅ Documentation cleanup: Organized into clean structure
- ✅ Architecture updated: v3.0 roadmap with testing infrastructure
- ✅ Pre-commit hook: Active and enforcing standards

**November 27, 2025:**
- ✅ Phase 0 Complete: 100% code compliance achieved
- ✅ 140+ type hints added
- ✅ 80+ docstrings added
- ✅ All print() converted to logger
- ✅ Imports organized (Standard/Third-party/Local)

---

## 📞 Getting Help

### Quick References

| Need | See Document | Section |
|------|--------------|---------|
| **Quick start** | [../README.md](../README.md) | Quick Start |
| **First workflow** | [user-guide/workflows.md](user-guide/workflows.md) | All |
| **Code standards** | [developer/DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md) | § 1-16 |
| **StageIO pattern** | [developer/DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md) | § 3 |
| **Config management** | [developer/DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md) | § 4 |
| **Testing** | [developer/DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md) | § 7 |
| **Model routing** | [AI_MODEL_ROUTING.md](AI_MODEL_ROUTING.md) | All |
| **Troubleshooting** | [user-guide/troubleshooting.md](user-guide/troubleshooting.md) | All |
| **Architecture** | [ARCHITECTURE_IMPLEMENTATION_ROADMAP.md](ARCHITECTURE_IMPLEMENTATION_ROADMAP.md) | All |

### Tools & Commands

**Validation:**
```bash
# Compliance check
python3 scripts/validate-compliance.py <file>

# Pre-commit hook (automatic on git commit)
git commit -m "Your message"
```

**Testing:**
```bash
# Run all tests
pytest tests/

# With coverage
pytest --cov=scripts --cov=shared --cov-report=html
```

**Pipeline:**
```bash
# Prepare job
./prepare-job.sh --media <file> --workflow <subtitle|transcribe|translate>

# Run pipeline
./run-pipeline.sh --job-dir <job-directory>
```

### Support Channels

- **Issues:** [GitHub Issues](https://github.com/raj-iup/cp-whisperx-app/issues)
- **Discussions:** [GitHub Discussions](https://github.com/raj-iup/cp-whisperx-app/discussions)
- **Standards Questions:** See [developer/DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md)
- **Workflow Questions:** See [user-guide/workflows.md](user-guide/workflows.md)

---

## 🚀 Next Steps

### Immediate Priorities (Phase 2-3: 7 weeks)

**Phase 2: Testing Infrastructure (3 weeks)**
- [ ] Create test media index (`in/test_media_index.json`)
- [ ] Build test framework with standard samples
- [ ] Write 30+ unit tests
- [ ] Write 10+ integration tests
- [ ] Add quality baseline tests
- [ ] Add caching tests
- [ ] Set up CI/CD pipeline

**Phase 3: StageIO Migration (4 weeks)**
- [ ] Migrate 5 active stages to StageIO pattern
- [ ] Add manifest tracking to all stages
- [ ] Implement context propagation
- [ ] Integrate caching layer
- [ ] Update orchestrator for stage control

### Medium-Term Goals (Phase 4-5: 12 weeks)

**Phase 4: Stage Integration (8 weeks)**
- [ ] Integrate remaining 5 stages
- [ ] Complete 10-stage modular pipeline
- [ ] Add dependency validation
- [ ] Test end-to-end workflows
- [ ] Validate quality targets with test samples

**Phase 5: Advanced Features (4 weeks)**
- [ ] Implement intelligent caching system
- [ ] Add ML-based optimization
- [ ] Add retry logic and circuit breakers
- [ ] Performance monitoring
- [ ] Production hardening

**See:** [ARCHITECTURE_IMPLEMENTATION_ROADMAP.md](ARCHITECTURE_IMPLEMENTATION_ROADMAP.md) for detailed timeline

---

## 📝 Maintenance & Quality

### Regular Tasks

**Daily (Developers):**
- Run compliance checker before commits (automatic via pre-commit hook)
- Review logs for any issues
- Follow StageIO pattern for new code

**Weekly (Team):**
- Review test coverage reports
- Check CI/CD status
- Update documentation as needed
- Review open issues and PRs

**Monthly:**
- Full compliance audit on new code
- Dependency security review
- Performance benchmarks
- Update quality baselines

**Quarterly:**
- Comprehensive system audit
- Standards document review
- Architecture review
- Training updates

### Quality Metrics

**Targets:**
- Code compliance: 100% (maintained)
- Unit test coverage: 85%
- Integration test coverage: 75%
- StageIO adoption: 100%
- Manifest tracking: 100%
- Documentation coverage: 100%

---

## 📅 Document History

| Date | Event | Phase |
|------|-------|-------|
| 2025-11-27 | Phase 0 Complete: 100% compliance | Phase 0 |
| 2025-12-03 | Phase 1 Complete: File naming standardized | Phase 1 |
| 2025-12-03 | Documentation rebuild: Master index updated | Phase 4 |
| 2025-12-03 | Architecture v3.0: Testing infrastructure defined | Phase 2 |

---

## ✨ Quick Links

### Essential Documents
- **[Master Roadmap](ARCHITECTURE_IMPLEMENTATION_ROADMAP.md)** - Where we're going
- **[Code Standards](developer/DEVELOPER_STANDARDS.md)** - How to write code
- **[Workflows Guide](user-guide/workflows.md)** - How to use the system
- **[Model Routing](AI_MODEL_ROUTING.md)** - Model selection

### Getting Started
- **[User Quick Start](../README.md)** - 30-second overview
- **[Bootstrap Guide](user-guide/BOOTSTRAP.md)** - Install dependencies
- **[Developer Setup](developer/getting-started.md)** - Dev environment
- **[First Contribution](developer/contributing.md)** - How to contribute

### Reference
- **[Code Examples](CODE_EXAMPLES.md)** - Pattern examples
- **[Architecture](technical/architecture.md)** - System design
- **[Troubleshooting](user-guide/troubleshooting.md)** - Common issues
- **[Pre-commit Hook](PRE_COMMIT_HOOK_GUIDE.md)** - Validation

---

**Status:** ✅ Phase 1 Complete | Phase 2 Ready  
**Compliance:** ✅ 100% maintained  
**Quality:** 🏆 GOLD certified  
**Progress:** 📊 35% → 95% (21 weeks remaining)

---

*Last updated: December 3, 2025*
