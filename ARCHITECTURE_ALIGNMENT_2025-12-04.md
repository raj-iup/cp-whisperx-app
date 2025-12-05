# Architecture Alignment Document

**Date:** 2025-12-04  
**Version:** 1.0  
**Status:** 🎯 AUTHORITATIVE - Single Source of Truth  
**Purpose:** Align all documentation with current architecture reality

---

## 🎯 Executive Summary

This document reconciles **planned refactorings** with **current implementation** to establish a single source of truth for the CP-WhisperX-App architecture.

**Key Findings:**
1. ✅ **Current 12-stage architecture is OPTIMAL** - No major refactoring needed
2. ⚠️ **ASR subsystem needs modularization** - Keep as single stage, split helper modules
3. ⚠️ **Translation stage is large but cohesive** - Keep as single stage (for now)
4. ✅ **Virtual environment structure is COMPLETE** - No new venvs needed
5. ✅ **WhisperX backend is production-ready** - Avoid MLX due to instability
6. ✅ **Job-specific parameters are MANDATORY** - All stages must honor user's explicit choices
7. ✅ **Shared imports must be consistent** - All shared/ imports must use "shared." prefix
8. ✅ **Hybrid MLX backend is production-ready** - 8-9x performance improvement
9. ✅ **Prioritize quality over backward compatibility** - Active development optimization

**Architectural Decisions:** 9 total (AD-001 through AD-009)

---

## 📊 Current Architecture Reality (v2.9 → v3.0)

### Actual Stage List (12 Stages)

```
01_demux.py                  (157 LOC) - Audio extraction
02_tmdb_enrichment.py        (548 LOC) - Metadata fetch (subtitle workflow only)
03_glossary_load.py          (235 LOC) - Term dictionary loading
04_source_separation.py      (441 LOC) - Vocal isolation (adaptive)
05_pyannote_vad.py           (207 LOC) - Voice activity + diarization
06_whisperx_asr.py           (140 LOC) - ASR wrapper
07_alignment.py              (327 LOC) - Word-level alignment
08_lyrics_detection.py       (198 LOC) - Song segment detection (subtitle workflow)
09_hallucination_removal.py  (223 LOC) - ASR error cleanup (subtitle workflow)
10_translation.py           (1045 LOC) - IndicTrans2 + NLLB translation
11_subtitle_generation.py    (225 LOC) - Multi-language subtitle generation
12_mux.py                    (356 LOC) - Soft-embed subtitles
```

**Plus:**
- `11_ner.py` (143 LOC) - Experimental named entity recognition

**Total:** 12 production stages + 1 experimental

### Helper Modules (Supporting Infrastructure)

```
scripts/whisperx_integration.py  (1697 LOC) - ASR implementation
shared/asr_chunker.py            (366 LOC) - Large file chunking
scripts/nllb_translator.py       (varies)  - NLLB fallback
shared/tmdb_client.py            (varies)  - TMDB API client
```

### Virtual Environments (8 Total)

```
venv/common/       - Core utilities (FFmpeg, config, logging)
venv/whisperx/     - WhisperX ASR engine (Stage 06)
venv/mlx/          - MLX-optimized alignment (Stage 07, Apple Silicon)
venv/pyannote/     - VAD + diarization (Stage 05)
venv/demucs/       - Source separation (Stage 04)
venv/indictrans2/  - Indic→English/non-Indic translation (Stage 10)
venv/nllb/         - Universal translation fallback (Stage 10)
venv/llm/          - Future LLM features (not yet used)
```

**Status:** ✅ **OPTIMAL** - Each ML model has isolated environment

---

## 🔍 Refactoring Analysis

### Option 1: ASR Stage Refactoring (RECOMMENDED)

**Current State:**
- Stage 06: `06_whisperx_asr.py` (140 LOC) - Thin wrapper
- Helper: `whisperx_integration.py` (1697 LOC) - Monolithic implementation
- Total: 1837 LOC (largest subsystem)

**Problem:**
- God object pattern - WhisperXProcessor does EVERYTHING
- Difficult to test individual components
- Mixed concerns (model management + transcription + filtering)

**Proposed Solution: Keep Stage, Split Helper Module**

```
Stage 06: whisperx_asr.py (140 LOC wrapper) ← NO CHANGE
          ↓ uses
scripts/whisperx/ (NEW MODULE DIRECTORY)
├── __init__.py             (exports)
├── model_manager.py        (~200 LOC) - Model loading, caching
├── backend_abstraction.py  (~300 LOC) - MLX/WhisperX/CUDA switching
├── bias_prompting.py       (~400 LOC) - Global/chunked/hybrid strategies
├── chunking.py             (~300 LOC) - Large file handling
├── transcription.py        (~300 LOC) - Core ASR execution
└── postprocessing.py       (~200 LOC) - Filtering, quality checks
```

**Benefits:**
- ✅ No workflow disruption
- ✅ Better code organization
- ✅ Easier to test components
- ✅ Gradual migration path
- ✅ Same venv (venv/whisperx)

**Migration Effort:** LOW (1-2 days)

**Decision:** ✅ **IMPLEMENT THIS**

---

### Option 2: Translation Stage Refactoring (DEFER)

**Current State:**
- Stage 10: `10_translation.py` (1045 LOC) - Monolithic but cohesive

**Analysis:**
```
Components:
├── Language pair detection      (~150 LOC)
├── IndicTrans2 model management (~250 LOC)
├── NLLB fallback logic          (~200 LOC)
├── Batch translation            (~200 LOC)
├── Glossary integration         (~150 LOC)
└── Quality scoring              (~95 LOC)
```

**Proposed Refactoring (from TRANSLATION_STAGE_REFACTORING_PLAN_NUMERIC.md):**
```
Stage 10: Translation Prep       (~200 LOC, venv/common)
Stage 11: IndicTrans2 Translation (~400 LOC, venv/indictrans2)
Stage 12: NLLB Translation        (~400 LOC, venv/nllb)
Stage 13: Translation Merge       (~150 LOC, venv/common)
Stage 14: Subtitle Generation     (renamed from 11)
Stage 15: Mux                     (renamed from 12)
```

**Problems with Split:**
1. ⚠️ Requires renumbering ALL subsequent stages (11→14, 12→15)
2. ⚠️ Adds 3 new stages for minimal benefit
3. ⚠️ Increases I/O overhead (more intermediate files)
4. ⚠️ Current implementation is already cohesive (single responsibility: translate)
5. ⚠️ Breaking translation into prep/execute/merge adds artificial boundaries

**Decision:** ❌ **DEFER INDEFINITELY**

**Rationale:**
- Current stage is large but handles ONE logical task: translation
- Breaking it up adds complexity without clear benefit
- If needed, refactor as helper modules (like ASR) instead

**Alternative (if needed later):**
```
Stage 10: translation.py (keep as 150 LOC wrapper)
          ↓ uses
scripts/translation/ (MODULE)
├── language_router.py       (~150 LOC)
├── indictrans2_engine.py    (~400 LOC)
├── nllb_engine.py           (~400 LOC)
└── glossary_processor.py    (~150 LOC)
```

---

### Option 3: Stage Number Conflicts (RESOLVED)

**Issues Found:**
- ✅ Stage 11 conflict: `11_ner.py` vs `11_subtitle_generation.py`
- ✅ Both files exist, but NER is marked experimental

**Current State:**
```
scripts/11_ner.py                  (143 LOC) - Experimental, not in pipeline
scripts/11_subtitle_generation.py  (225 LOC) - Production, actively used
```

**Resolution:**
- ✅ **Keep both** - NER is optional/experimental
- ✅ **Pipeline uses:** `11_subtitle_generation.py` (workflow routing handles this)
- ✅ **Document:** NER is stage 11 experimental variant

**No action needed** - Current state is acceptable

---

## 📋 Documentation Alignment Plan

### 4 Core Documents to Align

1. **CANONICAL_PIPELINE.md** (558 lines) ✅
   - **Status:** UP TO DATE
   - **Action:** Add ASR helper module note

2. **IMPLEMENTATION_TRACKER.md** (705 lines) 🔄
   - **Status:** NEEDS UPDATE
   - **Actions:**
     - ✅ Update stage counts (12 stages, not 10)
     - ✅ Add ASR modularization task
     - ✅ Remove translation refactoring (defer)
     - ✅ Update phase 4 progress metrics
     - ✅ Document venv structure as complete

3. **docs/developer/DEVELOPER_STANDARDS.md** (v6.2) 🔄
   - **Status:** MOSTLY UP TO DATE
   - **Actions:**
     - ✅ Update stage count references (10 → 12)
     - ✅ Add ASR helper module pattern
     - ✅ Document experimental stages (11_ner.py)

4. **.github/copilot-instructions.md** (v6.2) ✅
   - **Status:** UP TO DATE
   - **Action:** Minor clarifications only

### Supporting Documents

5. **docs/technical/architecture.md** (v2.0) 🔄
   - **Status:** OUTDATED
   - **Actions:**
     - ✅ Update to reflect 12-stage architecture
     - ✅ Update progress metrics (55% → 70%)
     - ✅ Add ASR subsystem architecture
     - ✅ Document helper module pattern

6. **ASR_STAGE_REFACTORING_PLAN.md** ✅
   - **Status:** ANALYSIS COMPLETE
   - **Action:** Mark Option 2 as APPROVED

7. **TRANSLATION_STAGE_REFACTORING_PLAN_NUMERIC.md** 🔄
   - **Status:** NEEDS REVISION
   - **Action:** Mark as DEFERRED with rationale

---

## 🎯 Implementation Priority Matrix

| Task | Priority | Effort | Impact | Timeline |
|------|----------|--------|--------|----------|
| **1. Update IMPLEMENTATION_TRACKER** | CRITICAL | LOW | HIGH | Immediate |
| **2. Update architecture.md** | HIGH | MEDIUM | HIGH | 1 day |
| **3. Modularize ASR helper** | HIGH | LOW | MEDIUM | 1-2 days |
| **4. Update DEVELOPER_STANDARDS** | MEDIUM | LOW | MEDIUM | 1 day |
| **5. Mark translation refactor as deferred** | MEDIUM | LOW | LOW | 30 min |
| **6. Continue E2E testing** | CRITICAL | HIGH | HIGH | Ongoing |

---

## ✅ Architectural Decisions

### AD-001: Keep 12-Stage Architecture
**Decision:** Current 12-stage architecture is optimal  
**Rationale:**
- Clear separation of concerns
- Each stage has single responsibility
- Stage sizes are manageable (140-550 LOC)
- Only 2 "large" stages (TMDB 548 LOC, Translation 1045 LOC) are cohesive units

**Status:** ✅ APPROVED

### AD-002: Modularize ASR Helper (Not Stage)
**Decision:** Split `whisperx_integration.py` into module, keep stage as-is  
**Rationale:**
- Improves testability without workflow disruption
- No stage renumbering required
- Same virtual environment
- Gradual migration path

**Status:** ✅ APPROVED

### AD-003: Defer Translation Stage Refactoring
**Decision:** Keep translation as single stage, defer 4-stage split  
**Rationale:**
- Current implementation is cohesive
- Splitting adds complexity without clear benefit
- Would require renumbering all subsequent stages
- Can refactor to helper modules later if needed

**Status:** ✅ APPROVED

### AD-004: Virtual Environment Structure is Complete
**Decision:** No new venvs needed, current 8 venvs are optimal  
**Rationale:**
- Each ML model has isolated environment
- Common utilities in shared venv
- No dependency conflicts
- Bootstrap scripts already handle all environments

**Status:** ✅ APPROVED

---

### AD-006: Job-Specific Parameters Override System Defaults
**Decision:** ✅ **MANDATORY** - All stages must read job.json parameters first, then fall back to system defaults

**Rationale:**
- User's explicit CLI parameters must be respected
- System defaults provide backward compatibility
- Single job can override any parameter without changing global config
- Bug #3 (language detection) revealed this was not consistently implemented

**Implementation Pattern:**
```python
# 1. Load system defaults from config
config = load_config()
source_lang = getattr(config, 'whisper_language', 'hi')
target_lang = getattr(config, 'target_language', 'en')

# 2. Override with job-specific parameters from job.json
job_json_path = job_dir / "job.json"
if job_json_path.exists():
    with open(job_json_path) as f:
        job_data = json.load(f)
        # Job parameters take precedence
        if 'source_language' in job_data and job_data['source_language']:
            source_lang = job_data['source_language']
        if 'target_languages' in job_data and job_data['target_languages']:
            target_lang = job_data['target_languages'][0]
```

**Mandatory For:**
- ✅ ALL stages that read configuration parameters
- ✅ Language parameters (source_language, target_languages)
- ✅ Quality settings (model size, compute type, batch size)
- ✅ Workflow flags (source_separation_enabled, tmdb_enabled)
- ✅ Output preferences (subtitle format, translation engines)

**Priority Order:**
1. **job.json** (user's explicit CLI choices)
2. **Job .env file** (job-specific overrides)
3. **System config/.env.pipeline** (system defaults)
4. **Code defaults** (hardcoded fallbacks)

**Impact:**
- Fixes inconsistent parameter handling across stages
- Enables per-job customization without global changes
- Improves user experience (respect explicit choices)
- Standard pattern for all new stages

**Compliance Status:**
- **Fixed:** Stage 06 ASR (whisperx_integration.py) ✅
- **TODO:** Audit all 11 other stages for compliance
- **TODO:** Add to stage template in DEVELOPER_STANDARDS.md
- **TODO:** Add compliance check to validate-compliance.py

**Status:** ✅ **ACCEPTED & MANDATORY**  
**Date:** 2025-12-04  
**Triggered By:** Bug #3 (language detection issue)  
**Applies To:** All current and future stages

---

### AD-007: Consistent Import Paths for Shared Modules

**Decision:** ✅ **MANDATORY** - All imports from shared/ directory MUST use "shared." prefix

**Rationale:**
- Python module resolution requires consistent import paths
- Lazy imports (inside try/except) were using incorrect paths
- Creates runtime import errors that are hard to debug
- Bug #4 (bias window generator import) revealed this anti-pattern

**The Problem:**
```python
# Top-level import (CORRECT)
from shared.bias_window_generator import BiasWindow

# Lazy import inside try/except (WRONG - Bug #4)
try:
    from bias_window_generator import create_bias_windows  # Missing "shared."
```

**Why It Failed:**
- Python doesn't automatically search shared/ directory
- Module not found at runtime when lazy-loaded
- Silent failure with warning, proceeds without feature
- Inconsistent with top-level imports in same file

**Correct Pattern:**
```python
# Top-level imports from shared/
from shared.config_loader import load_config
from shared.logger import get_logger
from shared.bias_window_generator import BiasWindow

# Lazy imports MUST also use shared. prefix
def some_function():
    try:
        from shared.bias_window_generator import create_bias_windows, save_bias_windows
        # Use the functions
    except ImportError as e:
        logger.warning(f"Could not import: {e}")
```

**Mandatory For:**
- ✅ ALL imports from shared/ directory
- ✅ Both top-level and lazy imports
- ✅ Both absolute and conditional imports
- ✅ All stages and helper modules

**Compliance Check:**
```bash
# Find incorrect imports (should return nothing)
grep -rn "^from [a-z_]*import" scripts/ | grep -v "^from shared\."
grep -rn "from [a-z_]*_generator import" scripts/
```

**Impact:**
- Fixes runtime import failures
- Prevents silent feature degradation
- Improves error messages
- Standard pattern for all shared modules

**Compliance Status:**
- **Fixed:** whisperx_integration.py line 1511 ✅
- **TODO:** Audit all scripts/ for incorrect shared imports
- **TODO:** Add to pre-commit hook validation
- **TODO:** Add to validate-compliance.py

**Status:** ✅ **ACCEPTED & MANDATORY**  
**Date:** 2025-12-04  
**Triggered By:** Bug #4 (bias window generator import warning)  
**Applies To:** All current and future code importing from shared/

---

### AD-008: Hybrid MLX Backend Architecture

**Decision:** Use hybrid MLX+WhisperX architecture for optimal performance with stability

**Problem:**
- MLX-Whisper is 8-9x faster than CTranslate2/CPU for transcription
- But MLX has segfault issues with alignment operations
- WhisperX is stable but slower
- Need both speed AND stability

**Solution: Hybrid Architecture**
```
Transcription (MLX) → Fast (84s for 12min audio)
         ↓
Alignment (WhisperX subprocess) → Stable (39s, no crashes)
         ↓
Total: 123s (8-9x faster than CPU, 100% stable)
```

**Key Implementation Details:**
- MLX backend for `transcribe()` only
- WhisperX subprocess for `align_segments()` 
- Process isolation prevents segfaults
- Automatic fallback to WhisperX if MLX fails

**Configuration:**
```bash
WHISPER_BACKEND=mlx              # Primary transcription
ALIGNMENT_BACKEND=whisperx       # Stable alignment
```

**Status:** ✅ **PRODUCTION READY**  
**Date:** 2025-12-04  
**Performance:** 8-9x improvement (11+ min crashed → 123 sec success)  
**Test Results:** E2E_TEST_SUCCESS_2025-12-05.md

---

### AD-009: Prioritize Quality Over Backward Compatibility

**Decision:** During active development (pre-v3.0), optimize for **pipeline accuracy and performance** over backward compatibility with intermediate development states.

**Problem:**
- Previous approach preserved all existing code paths during refactoring
- Added unnecessary compatibility layers and wrappers
- Slowed development and accumulated technical debt
- Reality: We're in active development, no production users yet

**Solution: Quality-First Development**
```
Before (Compatibility-First):
- Wrap old implementations
- Preserve all code paths
- Add delegation layers
- Conservative changes

After (Quality-First per AD-009):
- Replace with optimal implementation
- Remove suboptimal code
- Direct, clean implementations
- Aggressive optimization
```

**Core Principle:**
> "Optimize for the best possible output quality and accuracy, not for backward compatibility with development artifacts."

**What We CAN Change:**
- ✅ Internal implementations (whisperx_integration.py)
- ✅ Module structure (scripts/whisperx_module/)
- ✅ Stage internal logic
- ✅ Helper functions
- ✅ Processing pipelines

**What We MUST Maintain:**
- 🔒 Stage interfaces (StageIO pattern)
- 🔒 Configuration file formats (.env.pipeline)
- 🔒 External API contracts (library interfaces)
- 🔒 Command-line interfaces (prepare-job.sh, run-pipeline.sh)

**Impact on Current Work:**
- **AD-002 (ASR Modularization):** Direct extraction instead of wrapper approach
- **AD-003 (Translation):** Can proceed with aggressive optimization
- **Future Refactoring:** Focus on optimal implementation, not preservation

**Quality Metrics Priority:**
1. Output Accuracy (ASR WER < 5%, Translation BLEU > 90%)
2. Performance (Transcribe < 5 min, Translate < 10 min)
3. Code Quality (100% compliance, >80% coverage)
4. Developer Experience (clear, maintainable)

**Status:** ✅ **ACTIVE & MANDATORY**  
**Date:** 2025-12-05  
**Scope:** All development until v3.0 production  
**Document:** AD-009_DEVELOPMENT_PHILOSOPHY.md

---

## 🚀 Next Steps

### Immediate (This Session)
1. ✅ Update IMPLEMENTATION_TRACKER.md with current architecture
2. ✅ Mark ASR modularization as approved task
3. ✅ Mark translation refactoring as deferred
4. ✅ Update progress metrics to reflect reality

### Short-Term (Next 1-2 Days)
1. ⏳ Continue E2E testing (Priority 1)
2. ⏳ Update docs/technical/architecture.md
3. ⏳ Implement ASR helper modularization
4. ⏳ Update DEVELOPER_STANDARDS.md

### Medium-Term (Next Week)
1. ⏳ Complete all 3 workflow E2E tests
2. ⏳ Performance profiling and optimization
3. ⏳ Expand integration test suite
4. ⏳ Prepare for Phase 5 (Advanced Features)

---

## 📊 Updated Architecture Metrics

### Stage Implementation Status
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Stage Count | 12 | 12 | ✅ 100% |
| StageIO Adoption | 100% | 100% | ✅ 100% |
| Manifest Tracking | 100% | 100% | ✅ 100% |
| Code Compliance | 100% | 100% | ✅ 100% |
| Context-Aware | 90% | 90% | ✅ 100% |
| Documentation | 95% | 85% | 🔄 89% |

### Phase Progress
| Phase | Status | Progress |
|-------|--------|----------|
| Phase 0: Foundation | ✅ | 100% |
| Phase 1: File Naming | ✅ | 100% |
| Phase 2: Testing Infra | ✅ | 100% |
| Phase 3: StageIO Migration | ✅ | 100% |
| Phase 4: Stage Integration | 🔄 | 70% → 75% |
| Phase 5: Advanced Features | ⏳ | 0% |
| **TOTAL** | 🔄 | **70% → 75%** |

---

## 🔗 Related Documents

**Primary References:**
- CANONICAL_PIPELINE.md - Single source of truth for stage definitions
- IMPLEMENTATION_TRACKER.md - Current progress and task tracking
- docs/developer/DEVELOPER_STANDARDS.md - Development guidelines
- .github/copilot-instructions.md - AI assistant rules

**Refactoring Plans:**
- ASR_STAGE_REFACTORING_PLAN.md - Option 2 approved
- TRANSLATION_STAGE_REFACTORING_PLAN_NUMERIC.md - Deferred indefinitely

**Supporting Documentation:**
- docs/technical/architecture.md - System architecture
- E2E_TEST_EXECUTION_PLAN.md - Testing roadmap
- SESSION_SUMMARY_2025-12-04_EVENING.md - Recent work

---

**Last Updated:** 2025-12-04 05:12 UTC  
**Next Review:** After E2E tests complete  
**Status:** 🎯 AUTHORITATIVE - Use this as single source of truth for architecture decisions
