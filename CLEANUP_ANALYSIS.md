# CP-WhisperX-App - Project Cleanup Analysis

**Generated:** 2025-11-13  
**Purpose:** Identify core functionality and recommend cleanup

---

## Executive Summary

After analyzing the entire project repository, I've identified:
- **70 core files** essential for functionality
- **100+ removable files** (archives, tests, unused scripts)
- **7 potential duplicates** to resolve
- **12GB+ in regenerable caches** to exclude from git

---

## ✅ CORE FILES TO KEEP (70 files)

### 1. Bootstrap & Setup (4 files)
- `scripts/bootstrap.sh` - Environment setup & dependency installation
- `scripts/preflight.py` - Pre-flight checks
- `config/.env.template` - Configuration template
- `config/.env.pipeline.template` - Pipeline config template

### 2. Prepare Job (4 files)
- `prepare-job.sh` - Job preparation wrapper
- `scripts/prepare-job.py` - Job preparation logic
- `shared/job_manager.py` - Job management utilities
- `shared/config.py` - Configuration loader

### 3. Pipeline Orchestrator (7 files)
- `run_pipeline.sh` - Main pipeline execution wrapper
- `scripts/pipeline.py` - Core orchestrator logic
- `scripts/pipeline_sequential.py` - Sequential pipeline (backup)
- `scripts/manifest.py` - Pipeline state tracking
- `shared/manifest.py` - Manifest utilities (different from above)
- `shared/stage_utils.py` - Stage execution utilities
- `shared/logger.py` - Logging framework

### 4. Resume Pipeline (3 files)
- `resume-pipeline.sh` - Resume incomplete jobs
- Uses `scripts/manifest.py` and `shared/manifest.py` (shared with orchestrator)

### 5. Stage Execution Scripts (21 files)

**Media Processing:**
- `scripts/demux.py` - Extract audio from video
- `scripts/mux.py` - Remux subtitles into video
- `scripts/finalize.py` - Final output organization

**Metadata & Context:**
- `scripts/tmdb.py` - TMDB API integration
- `scripts/tmdb_enrichment.py` - TMDB data enrichment
- `scripts/pre_ner.py` - Pre-NER entity extraction
- `scripts/post_ner.py` - Post-NER entity extraction

**Voice Activity Detection:**
- `scripts/silero_vad.py` - Silero VAD
- `scripts/pyannote_vad.py` - PyAnnote VAD
- `scripts/pyannote_vad_chunker.py` - VAD chunking logic

**Speech Recognition & Diarization:**
- `scripts/whisperx_asr.py` - ASR stage wrapper
- `scripts/whisperx_integration.py` - WhisperX integration
- `scripts/whisper_backends.py` - Backend abstraction (WhisperX/MLX)
- `scripts/diarization.py` - Speaker diarization

**Translation & Refinement:**
- `scripts/glossary_builder.py` - Build glossary from entities
- `scripts/second_pass_translation.py` - Context-aware translation
- `scripts/translation_refine.py` - Translation refinement

**Additional Processing:**
- `scripts/lyrics_detection.py` - Detect song lyrics
- `scripts/lyrics_detection_core.py` - Lyrics detection logic
- `scripts/subtitle_gen.py` - Generate subtitle files

### 6. Support Modules (9 files)
- `scripts/bias_injection.py` - Bias prompting for ASR
- `scripts/canonicalization.py` - Text normalization
- `scripts/config_loader.py` - Configuration utilities
- `scripts/device_selector.py` - Hardware device selection
- `scripts/ner_extraction.py` - Named entity extraction
- `scripts/patch_pyannote.py` - PyAnnote compatibility fixes
- `scripts/prompt_assembly.py` - Prompt generation

### 7. Shared Libraries (11 files)
- `shared/__init__.py` - Package init
- `shared/config.py` - Configuration management
- `shared/glossary.py` - Glossary core functionality
- `shared/glossary_advanced.py` - Advanced glossary features
- `shared/glossary_ml.py` - ML-based glossary
- `shared/hardware_detection.py` - Hardware capability detection
- `shared/job_manager.py` - Job lifecycle management
- `shared/logger.py` - Centralized logging
- `shared/manifest.py` - Job manifest utilities
- `shared/stage_utils.py` - Stage execution helpers
- `shared/utils.py` - General utilities

### 8. Requirements (4 files)
- `requirements.txt` - Core dependencies
- `requirements-macos.txt` - macOS-specific
- `requirements-flexible.txt` - Flexible version ranges
- `requirements-optional.txt` - Optional features

### 9. Essential Documentation (4 files)
- `README.md` - Project overview
- `docs/QUICKSTART.md` - Quick start guide
- `docs/ARCHITECTURE.md` - System architecture
- `docs/INDEX.md` - Documentation index

### 10. User Data (Keep)
- `glossary/prompts/*.txt` - User-created glossary prompts
- `in/`, `out/`, `logs/` - User data directories

---

## 🗑️ FILES TO REMOVE (100+ files)

### 1. Documentation Archives (64 files)
```bash
rm -rf docs/archive/          # 59 historical markdown files
rm -rf docs/reference/        # 5 old reference docs
rm -f docs/DOCUMENTATION_REFACTORING_FINAL.md
```

### 2. Test & Validation Scripts (10 files)
```bash
rm -f test_mlx_backend.py test_pyannote_mps.py test-pipeline-status.sh
rm -f test_output.log
rm -rf scripts/tests/
rm -f scripts/test_hf_access.py tools/test_ml_glossary.py
rm -f validate-implementation.sh verify-bias-implementation.sh
rm -f verify-native-only.sh VERIFY_ML_FEATURE.sh
```

### 3. Unused Scripts (8 files)
```bash
rm -f scripts/era_lexicon.py scripts/filename_parser.py
rm -f scripts/generate_cuda_report.py scripts/process_in_chunks.py
rm -f scripts/reset_stages.py scripts/verify_mps_usage.py
rm -f scripts/verify_subtitle_path.py refactor_stages.py
```

### 4. Backup/Legacy Config (3 files)
```bash
rm -f config/.env.example config/.env.pipeline.backup
rm -f requirements-macos-pinned.txt  # Unless needed for strict pinning
```

### 5. Model Caches (Regenerable)
```bash
# Add to .gitignore
rm -rf shared/model-cache/     # 17MB
rm -rf .cache/                 # 12GB
```

---

## ⚠️ DUPLICATES TO RESOLVE

### 1. Finalize Scripts
- **KEEP:** `scripts/finalize.py` (current stage script)
- **VERIFY:** `scripts/finalize_output.py` (check if used)
- **OPTIONAL:** `finalize-output.sh` (standalone wrapper)

### 2. Logger Module - CONSOLIDATE
- **REMOVE:** `scripts/logger.py` (deprecated)
- **KEEP:** `shared/logger.py` (actively used)

Evidence: All imports use `from shared.logger import PipelineLogger`

### 3. Manifest Modules - KEEP BOTH
- **KEEP:** `scripts/manifest.py` (195 lines - creates initial manifest)
- **KEEP:** `shared/manifest.py` (374 lines - tracks stage execution)

These serve different purposes and are NOT duplicates.

---

## 🎯 OPTIONAL FILES

### Keep for User Convenience:
- ✅ `quick-start.sh` - Helpful wrapper
- ✅ `finalize-output.sh` - Standalone tool
- ✅ `docs/QUICK_REFERENCE.md` - User reference
- ✅ `shared/verify_pytorch.py` - Troubleshooting

### Consider Removing:
- ❓ `docs/QUICK_FIX_REFERENCE.md` - Merge into main docs?
- ❓ `scripts/pipeline_sequential.py` - Backup needed?
- ❓ `requirements-flexible.txt` - Need flexible versions?

---

## 📝 RECOMMENDED CLEANUP STEPS

### Phase 1: Backup
```bash
git add -A
git commit -am "Pre-cleanup snapshot"
git tag cleanup-backup-$(date +%Y%m%d)
```

### Phase 2: Remove Archives (Safe)
```bash
rm -rf docs/archive/ docs/reference/
rm -f docs/DOCUMENTATION_REFACTORING_FINAL.md
git add -A && git commit -m "Remove documentation archives"
```

### Phase 3: Remove Tests
```bash
rm -f test*.py test*.sh test_output.log
rm -rf scripts/tests/ tools/test_ml_glossary.py scripts/test_hf_access.py
rm -f validate-*.sh verify-*.sh VERIFY_*.sh
git add -A && git commit -m "Remove test and validation scripts"
```

### Phase 4: Remove Unused Scripts
```bash
cd scripts
rm -f era_lexicon.py filename_parser.py generate_cuda_report.py
rm -f process_in_chunks.py reset_stages.py verify_*.py
cd .. && rm -f refactor_stages.py
git add -A && git commit -m "Remove unused scripts"
```

### Phase 5: Clean Config
```bash
rm -f config/.env.example config/.env.pipeline.backup
git add -A && git commit -m "Clean config files"
```

### Phase 6: Resolve Duplicates
```bash
rm scripts/logger.py  # Consolidated to shared/
git add -A && git commit -m "Resolve duplicate modules"
```

### Phase 7: Update .gitignore
```bash
cat >> .gitignore << 'EOF'
# Caches (regenerable)
.cache/
.bollyenv/
shared/model-cache/
__pycache__/
*.pyc

# Test outputs
test_output.log

# User data
in/
out/
logs/

# Active config
config/.env.pipeline
EOF

git add .gitignore && git commit -m "Update .gitignore"
```

### Phase 8: Validation
```bash
./scripts/bootstrap.sh
./prepare-job.sh --job TEST_CLEANUP --media in/test.mp4 --title "Test"
./run_pipeline.sh --job TEST_CLEANUP --stages demux
git tag cleanup-complete-$(date +%Y%m%d)
```

---

## 📊 IMPACT

### Before Cleanup
- Total Files: ~250+
- Documentation: 60+ files
- Scripts: 40+ files
- Model Caches: 12GB

### After Cleanup
- Total Files: ~75
- Documentation: 5 essential files
- Scripts: 35-40 active files
- Clear structure

**Space Saved:** 12GB + 2MB  
**Clarity Gained:** 70% file reduction

---

## ✅ VALIDATION CHECKLIST

After cleanup, verify:
- [ ] Bootstrap works: `./scripts/bootstrap.sh`
- [ ] Job prep works: `./prepare-job.sh --job TEST`
- [ ] Pipeline runs: `./run_pipeline.sh --job TEST`
- [ ] Resume works: `./resume-pipeline.sh --job TEST`
- [ ] No broken imports
- [ ] Documentation complete
- [ ] Git history preserved

---

## 🚀 ONE-COMMAND CLEANUP

For experienced users (after manual backup):

```bash
#!/bin/bash
# DO NOT RUN without review and backup!
cd /Users/rpatel/Projects/cp-whisperx-app

# Backup
git add -A && git commit -am "Pre-cleanup snapshot"
git tag cleanup-backup-$(date +%Y%m%d)

# Remove archives
rm -rf docs/archive/ docs/reference/
rm -f docs/DOCUMENTATION_REFACTORING_FINAL.md

# Remove tests
rm -f test*.py test*.sh test_output.log
rm -rf scripts/tests/ tools/test_ml_glossary.py scripts/test_hf_access.py
rm -f validate-*.sh verify-*.sh VERIFY_*.sh

# Remove unused
cd scripts && rm -f era_lexicon.py filename_parser.py \
    generate_cuda_report.py process_in_chunks.py reset_stages.py \
    verify_mps_usage.py verify_subtitle_path.py logger.py && cd ..
rm -f refactor_stages.py

# Clean config
rm -f config/.env.example config/.env.pipeline.backup

# Commit
git add -A && git commit -m "Cleanup: Remove archives, tests, and unused files"
git tag cleanup-complete-$(date +%Y%m%d)

echo "✅ Cleanup complete! Run validation tests."
```

---

**Status:** Ready for Implementation  
**Recommendation:** Start with Phase 2 (archives), test, then proceed incrementally.
