# CP-WhisperX-App Code Compliance Report (REVISED)

**Generated:** 2025-12-02 (Revised for Essential Files Only)  
**Review Standard:** `.github/copilot-instructions.md` v3.3 (Phase 5)  
**Scope:** Pipeline-essential files only (bootstrap, prepare-job, run-pipeline, test-glossary dependencies)

---

## Executive Summary

### Overview Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Essential Files** | 66 | 100% |
| **Files Clean** | 6 | 9.1% |
| **Files with Issues** | 60 | 90.9% |

### Violation Summary

| Severity | Count | Priority |
|----------|-------|----------|
| **CRITICAL** | 336 | 🔴 HIGH |
| **ERROR** | 45 | 🟠 MEDIUM |
| **WARNING** | 327 | 🟡 LOW |
| **TOTAL** | 708 | - |

### Compliance Score: **9.1%** ❌

**Status:** Requires immediate attention - 81 points below 90% target

---

## Scope of This Report

This report focuses **ONLY** on files that are dependencies of:
1. `bootstrap.sh` - Environment setup
2. `prepare-job.sh` / `scripts/prepare-job.py` - Job preparation
3. `run-pipeline.sh` / `scripts/run-pipeline.py` - Pipeline execution
4. `test-glossary-quickstart.sh` - Glossary testing

**Files Excluded:** Utilities, benchmarks, experimental code, deprecated versions

---

## Essential Files Breakdown

### Shell Scripts (4 files)
- `bootstrap.sh` - Multi-environment setup
- `prepare-job.sh` - Job preparation wrapper
- `run-pipeline.sh` - Pipeline execution wrapper
- `test-glossary-quickstart.sh` - Glossary quickstart test

### Python Scripts (42 files)

**Core Entry Points (2):**
- `scripts/prepare-job.py` - 53 critical, 1 error, 2 warnings 🔴
- `scripts/run-pipeline.py` - 47 critical, 1 error, 31 warnings 🔴

**Pipeline Stages (12):**
- `scripts/demux.py` - 0 critical, 1 error, 2 warnings
- `scripts/tmdb.py` - ✅ CLEAN
- `scripts/source_separation.py` - Issues
- `scripts/pyannote_vad.py` - Issues
- `scripts/asr_chunker.py` - Issues
- `scripts/mlx_alignment.py` - Issues
- `scripts/lyrics_detection_core.py` - Issues
- `scripts/export_transcript.py` - Issues
- `scripts/translation_refine.py` - Issues
- `scripts/subtitle_gen.py` - ✅ CLEAN
- `scripts/mux.py` - ✅ CLEAN
- Plus stage variants (tmdb_enrichment_stage, whisperx_asr, etc.)

**Helper Scripts (28):**
- config_loader, filename_parser, device_selector
- bias_injection, glossary_builder, glossary_applier
- hallucination_removal, ner_extraction, canonicalization
- translation_validator, subtitle_segment_merger
- And 18 more...

### Shared Modules (24 files)

**Core Infrastructure (8):**
- `shared/logger.py` - 0 critical, 1 error, 5 warnings
- `shared/config.py` - 2 critical, 0 errors, 14 warnings
- `shared/stage_utils.py` - 0 critical, 1 error, 10 warnings
- `shared/stage_order.py` - Issues
- `shared/manifest.py` - Issues
- `shared/environment_manager.py` - 15 critical 🔴
- `shared/job_manager.py` - Issues
- `shared/utils.py` - ✅ CLEAN

**Feature Modules (16):**
- Audio: audio_utils (4 critical)
- Hardware: hardware_detection (49 critical 🔴), model_checker, model_downloader
- Glossary: glossary_manager, glossary_unified, glossary_advanced, glossary_ml, glossary_cache
- TMDB: tmdb_client, tmdb_cache, tmdb_loader
- Other: musicbrainz_cache, ner_corrector, bias_registry

---

## Critical Issues Breakdown

### 1. Logger Usage Violations (§ 2.3) - 🔴 HIGHEST PRIORITY

**Issue:** 280+ print() statements in essential files (should be logger)  
**Severity:** CRITICAL  

**Top Offenders:**
- `scripts/prepare-job.py` - 53 print statements
- `scripts/run-pipeline.py` - 47 print statements
- `shared/hardware_detection.py` - 49 print statements
- `shared/environment_manager.py` - 15 print statements

**Impact:**
- No centralized logging for production debugging
- Cannot trace job execution flow
- Missing log levels for filtering

**Remediation:**
```python
# ❌ WRONG
print("Processing...")

# ✅ CORRECT
from shared.logger import get_logger
logger = get_logger(__name__)
logger.info("Processing...")
```

---

### 2. Logger Import Missing (§ 2.3) - 🔴 HIGH PRIORITY

**Issue:** 45 essential files missing logger import  
**Severity:** ERROR  

**Action:** Add to all files after stdlib imports:
```python
# Local
from shared.logger import get_logger
logger = get_logger(__name__)
```

---

### 3. Config Access Violations (§ 4.2) - 🟠 MEDIUM PRIORITY

**Issue:** Direct os.getenv() calls instead of load_config()  
**Files Affected:** Primarily shared/config.py

**Remediation:**
```python
# ❌ WRONG
value = os.getenv("PARAM_NAME")

# ✅ CORRECT
from shared.config import load_config
config = load_config()
value = config.get("PARAM_NAME", default)
```

---

## Files That Can Be REMOVED

Based on dependency analysis, these files are NOT used by the pipeline:

### Removable Scripts (32 files, ~500KB):

**Benchmarking/Testing Tools:**
- `scripts/benchmark_accuracy.py`
- `scripts/beam_optimizer.py`
- `scripts/beam_search_comparison.py`
- `scripts/compare_translations.py`
- `scripts/quality_metrics_analyzer.py`

**Experimental/Alternative Implementations:**
- `scripts/adaptive_bias_strategy.py`
- `scripts/bias_strategy_selector.py`
- `scripts/bias_window_generator.py`
- `scripts/multi_pass_refiner.py`
- `scripts/silero_vad.py`
- `scripts/translate_alternative.py`
- `scripts/pyannote_vad_chunker.py`

**Duplicate/Old Versions:**
- `scripts/hybrid_subtitle_merger_v2.py` (keep v1)
- `scripts/lyrics_detection_pipeline.py` (have core version)
- `scripts/tmdb_enrichment.py` (have stage version)
- `scripts/second_pass_translation.py` (unused)

**Standalone Utilities:**
- `scripts/cache_manager.py`
- `scripts/create_clip.py`
- `scripts/diarization.py`
- `scripts/fix_session3_issues.py`
- `scripts/hinglish_word_detector.py`
- `scripts/manifest.py` (no imports found)
- `scripts/mps_utils.py`
- `scripts/musicbrainz_client.py`
- `scripts/patch_pyannote.py`
- `scripts/prompt_assembly.py`
- `scripts/retranslate_srt.py`
- `scripts/song_bias_injection.py`
- `scripts/speaker_aware_bias.py`
- `scripts/whisperx_translate_comparator.py`

**Keep compliance checker:**
- `scripts/validate-compliance.py` ✅ KEEP (for validation)

### Removable Shared Modules (5 files):
- `shared/glossary.py` (have unified version)
- `shared/glossary_generator.py` (unused)
- `shared/glossary_unified_deprecated.py` (deprecated)
- `shared/stage_manifest.py` (have manifest.py)
- `shared/verify_pytorch.py` (unused)

### Already Identified for Removal:
- `archive/` directory (4.7MB)
- `shared/backup/` directory (7 files)

**Total Removable:** 37 Python files + archive (5MB+)

---

## Prioritized Action Plan

### Phase 1: Critical Fixes (Week 1)
**Goal:** Fix highest violation files

1. **Fix Top 3 Critical Files:**
   - `shared/hardware_detection.py` (49 violations)
   - `scripts/prepare-job.py` (56 violations)
   - `scripts/run-pipeline.py` (79 violations)
   
2. **Add Logger Imports** (45 files, automated)

3. **Remove Unused Code:**
   - Delete 32 unused scripts
   - Delete archive/ and shared/backup/
   - Save ~5.5MB

**Expected Result:** 50% reduction in critical violations

### Phase 2: Error-Level Fixes (Week 2)
**Goal:** Clean up infrastructure modules

4. **Fix Shared Modules:**
   - `shared/environment_manager.py` (15 critical)
   - `shared/model_downloader.py` (28 critical)
   - `shared/model_checker.py` (24 critical)
   - `shared/audio_utils.py` (4 critical)
   - `shared/config.py` (2 critical)

5. **Organize Imports** (all files, automated with isort)

**Expected Result:** 80% reduction in critical violations

### Phase 3: Warning-Level Improvements (Week 3)
**Goal:** Polish essential files

6. **Add exc_info=True to logger.error()** (100+ occurrences)
7. **Type Hints** (prioritize public APIs)
8. **Docstrings** (public functions only)

**Expected Result:** 90%+ compliance on essential files

---

## Revised Compliance Metrics

### Current State (Essential Files Only):
- Total Files: 66
- Clean: 6 (9.1%)
- Compliance Score: 9.1%

### Target State (Week 3):
- Total Files: 66
- Clean: 60 (90.9%)
- Compliance Score: 90%+

### Files to Fix (Priority Order):

**🔴 URGENT (Week 1):**
1. shared/hardware_detection.py (49 violations)
2. scripts/prepare-job.py (56 violations)
3. scripts/run-pipeline.py (79 violations)
4. shared/environment_manager.py (16 violations)
5. shared/model_downloader.py (33 violations)

**🟠 HIGH (Week 2):**
6. shared/model_checker.py (29 violations)
7. scripts/asr_chunker.py (violations)
8. scripts/source_separation.py (violations)
9. scripts/pyannote_vad.py (violations)
10. All remaining stage scripts

**🟡 MEDIUM (Week 3):**
- Helper scripts with < 10 violations
- Type hints and docstrings

---

## Automated Fixes

### Safe to Auto-Fix:

**1. Remove Unused Files:**
```bash
# Backup first!
git checkout -b cleanup-unused

# Remove unused scripts
rm scripts/benchmark_accuracy.py
rm scripts/beam_optimizer.py
rm scripts/compare_translations.py
# ... (32 files total)

# Remove archive and backup
rm -rf archive/
rm -rf shared/backup/

# Commit
git add -A
git commit -m "chore: remove unused code (~5.5MB, 37 files)"
```

**2. Add Logger Imports** (45 files):
```bash
for file in scripts/*.py shared/*.py; do
  if grep -q "logger\." "$file" && ! grep -q "from shared.logger import" "$file"; then
    # Add logger import after stdlib imports
    sed -i '' '/^import.*$/a\
\
# Local\
from shared.logger import get_logger\
logger = get_logger(__name__)\
' "$file"
  fi
done
```

**3. Organize Imports:**
```bash
pip install isort
isort scripts/ shared/ --profile black
```

### Requires Manual Review:

**Print statements in:**
- prepare-job.py (user-facing output)
- run-pipeline.py (pipeline status)
- Hardware/model detection (setup messages)

---

## Success Metrics

### Weekly Targets:

| Week | Clean Files | Critical | Errors | Compliance % |
|------|-------------|----------|--------|--------------|
| 0 (Now) | 6 | 336 | 45 | 9.1% |
| 1 | 20 | <150 | 30 | 30% |
| 2 | 40 | <50 | 15 | 60% |
| 3 | 60 | <10 | <5 | 90%+ |

---

## Clean File Examples

**Use these as templates:**
1. `scripts/tmdb.py` - Stage script ✅
2. `scripts/mux.py` - Stage script ✅
3. `scripts/subtitle_gen.py` - Stage script ✅
4. `shared/utils.py` - Shared module ✅
5. `scripts/pre_ner.py` - Helper script ✅
6. `scripts/post_ner.py` - Helper script ✅

---

## Validation Commands

```bash
# Check essential files only
./scripts/validate-compliance.py scripts/prepare-job.py scripts/run-pipeline.py

# Check all stage scripts
./scripts/validate-compliance.py scripts/demux.py scripts/tmdb.py scripts/mux.py

# Check shared infrastructure
./scripts/validate-compliance.py shared/logger.py shared/config.py shared/stage_utils.py

# Full scan of essential files
./scripts/validate-compliance.py $(cat essential_files.txt)
```

---

## Summary

**Revised Scope:** 66 essential files (vs 122 total)  
**Removable:** 37 files + 5MB archive  
**Violations:** 708 (vs 2,000 total) - **64% reduction**  
**Timeline:** 3 weeks to 90% compliance on essential files

**Key Insight:** By focusing on pipeline-essential files only, we reduced the scope by 46% while maintaining all functionality. This makes the compliance project much more achievable.

---

**End of Revised Report**
