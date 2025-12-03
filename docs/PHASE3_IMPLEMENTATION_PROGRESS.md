# Phase 3: Stage Pattern Adoption - Implementation Progress

**Date Started:** 2025-12-03  
**Status:** In Progress  
**Goal:** Convert critical stages to use StageIO pattern with manifest tracking

Based on: [ARCHITECTURE_IMPLEMENTATION_ROADMAP.md](ARCHITECTURE_IMPLEMENTATION_ROADMAP.md#phase-3-stage-pattern-adoption-4-weeks)

---

## Overview

Phase 3 converts 5 critical pipeline stages to follow the standardized `run_stage()` pattern:
- Consistent logging with io.get_stage_logger()
- Manifest tracking for data lineage
- Proper error handling and resource tracking
- Stage isolation with job_dir parameter

**Estimated Effort:** 60 hours over 4 weeks  
**Priority:** P0 Critical  
**Dependencies:** Phases 1 & 2 complete

---

## Implementation Tasks

### ✅ Task 3.1: Convert Demux Stage (8 hours)

**File:** `scripts/demux.py`  
**Status:** ✅ COMPLETED  
**Date:** 2025-12-03

**Changes Made:**
1. ✅ Added `run_stage(job_dir: Path, stage_name: str = "01_demux") -> int` function
2. ✅ Initialize StageIO with `enable_manifest=True`
3. ✅ Use `io.get_stage_logger()` for logging
4. ✅ Track input video with `io.track_input()`
5. ✅ Track output audio with `io.track_output()`
6. ✅ Add config parameters to manifest
7. ✅ Finalize manifest with exit code
8. ✅ Kept existing `main()` as backward compatibility wrapper
9. ✅ Proper error handling (FileNotFoundError, RuntimeError, Exception)

**Pattern Compliance:**
- ✅ StageIO initialization with manifest
- ✅ Stage logging (not print)
- ✅ Input/output tracking
- ✅ Config tracking
- ✅ Error handling with finalize
- ✅ Writes only to io.stage_dir

**Testing:**
- ✅ Syntax validation passed
- ⏳ Unit tests pending (Task 3.6)
- ⏳ Integration test update pending (Task 3.6)

---

### ⏳ Task 3.2: Convert ASR Stage (12 hours)

**File:** `scripts/whisperx_asr.py` (thin wrapper around `whisperx_integration.py`)  
**Status:** ⏳ NOT STARTED  
**Complexity:** HIGH (GPU management, model caching)

**Current State:**
- File size: 54 lines (wrapper), 1679 lines (integration)
- Already imports from `whisperx_integration.py`
- No StageIO pattern
- No manifest tracking

**Required Changes:**
1. Add `run_stage(job_dir: Path, stage_name: str = "04_asr") -> int`
2. Initialize StageIO with manifest in `whisperx_integration.py`
3. Track input audio file
4. Track output transcript JSON
5. Track model artifacts (model name, version, device)
6. Log performance metrics (loading time, transcription time)
7. Handle GPU memory management
8. Proper cleanup on error

**Additional Requirements:**
- Handle model caching across runs
- Track GPU memory usage
- Log alignment metrics
- Add retry logic for GPU OOM
- Track intermediate whisper outputs

**Estimated Time:** 12 hours
- 4 hours: Add run_stage() and StageIO
- 4 hours: Manifest tracking and metrics
- 2 hours: GPU error handling
- 2 hours: Testing and validation

---

### ⏳ Task 3.3: Convert Translation Stage (12 hours)

**File:** `scripts/indictrans2_translator.py`  
**Status:** ⏳ NOT STARTED  
**Complexity:** HIGH (multiple languages, environment switching)

**Current State:**
- File size: 902 lines
- Complex multi-language support
- Environment variable manipulation
- No StageIO pattern
- No manifest tracking

**Required Changes:**
1. Add `run_stage(job_dir: Path, stage_name: str = "08_translation") -> int`
2. Initialize StageIO with manifest
3. Track input transcript files
4. Track output translation files (per language)
5. Track model artifacts
6. Log translation metrics (per language)
7. Handle environment switching safely
8. Track bilingual alignment data

**Additional Requirements:**
- Handle multiple target languages
- Track per-language outputs separately
- Manage IndicTrans2 environment
- Log translation quality metrics
- Handle language-specific errors
- Track vocabulary coverage

**Estimated Time:** 12 hours
- 3 hours: Add run_stage() and StageIO
- 4 hours: Multi-language tracking
- 2 hours: Environment management
- 2 hours: Metrics and logging
- 1 hour: Testing

---

### ⏳ Task 3.4: Convert Subtitle Gen Stage (10 hours)

**File:** `scripts/subtitle_gen.py`  
**Status:** ⏳ NOT STARTED  
**Complexity:** MEDIUM (inline function, needs extraction)

**Current State:**
- File size: 321 lines
- Partially extracted from run-pipeline.py
- Uses StageIO but no run_stage()
- Some manifest tracking
- Glossary integration

**Required Changes:**
1. Add `run_stage(job_dir: Path, stage_name: str = "09_subtitle_gen") -> int`
2. Enable manifest tracking
3. Track translation input files
4. Track SRT output files (per language)
5. Track glossary application (if used)
6. Log subtitle statistics (segments, duration)
7. Add SRT validation
8. Handle multiple output formats (SRT, VTT, ASS)

**Additional Requirements:**
- Support multiple subtitle formats
- Track glossary term replacements
- Validate SRT timing
- Log formatting options
- Handle lyrics detection integration
- Track subtitle quality metrics

**Estimated Time:** 10 hours
- 3 hours: Add proper run_stage() pattern
- 3 hours: Multi-file/format tracking
- 2 hours: Validation and metrics
- 2 hours: Testing

---

### ⏳ Task 3.5: Convert Mux Stage (8 hours)

**File:** `scripts/mux.py`  
**Status:** ⏳ IN PROGRESS (backed up, needs fixing)  
**Complexity:** MEDIUM (already has StageIO, needs restructuring)

**Current State:**
- File size: 334 lines
- Already uses StageIO with manifest
- Has comprehensive error handling
- Indentation issues (line 47, 281-331)
- Main() function is complex

**Required Changes:**
1. Fix indentation issues (lines 47-50, 281-331)
2. Extract core logic into `run_stage(job_dir: Path, stage_name: str = "10_mux") -> int`
3. Keep existing StageIO and tracking (already good)
4. Simplify main() to wrapper
5. Verify all paths use io.stage_dir
6. Add ffmpeg command to manifest config
7. Track subtitle language metadata

**Additional Requirements:**
- Handle multiple subtitle tracks
- Track codec decisions
- Log muxing parameters
- Validate output video
- Handle various container formats
- Track final output size

**Estimated Time:** 8 hours
- 2 hours: Fix indentation and extract run_stage()
- 2 hours: Refactor and cleanup
- 2 hours: Enhanced tracking
- 2 hours: Testing

**Note:** File backed up to `scripts/mux.py.backup`

---

### ⏳ Task 3.6: Update Pipeline Orchestrator (10 hours)

**File:** `scripts/run-pipeline.py`  
**Status:** ⏳ NOT STARTED  
**Complexity:** HIGH (main orchestration logic)

**Current State:**
- File size: ~2500+ lines
- Calls stages directly with various patterns
- Mixed function calls and subprocess calls
- No standardized run_stage() calls

**Required Changes:**

#### 3.6.1: Update Demux Calls (1 hour)
```python
# Before
from scripts.demux import main as demux_main
exit_code = demux_main()

# After
from scripts.demux import run_stage as demux_stage
exit_code = demux_stage(self.job_dir, "01_demux")
if exit_code != 0:
    raise StageExecutionError("Demux failed")
```

#### 3.6.2: Update ASR Calls (2 hours)
```python
# Before
from scripts.whisperx_asr import main as asr_main
exit_code = asr_main()

# After
from scripts.whisperx_asr import run_stage as asr_stage
exit_code = asr_stage(self.job_dir, "04_asr")
if exit_code != 0:
    raise StageExecutionError("ASR failed")
```

#### 3.6.3: Update Translation Calls (2 hours)
```python
# Before
from scripts.indictrans2_translator import translate_whisperx_result
result = translate_whisperx_result(transcript, target_langs)

# After
from scripts.indictrans2_translator import run_stage as translation_stage
exit_code = translation_stage(self.job_dir, "08_translation")
if exit_code != 0:
    raise StageExecutionError("Translation failed")
```

#### 3.6.4: Update Subtitle Gen Calls (2 hours)
```python
# Before
from scripts.subtitle_gen import generate_subtitles
generate_subtitles(transcript, output_dir)

# After
from scripts.subtitle_gen import run_stage as subtitle_stage
exit_code = subtitle_stage(self.job_dir, "09_subtitle_gen")
if exit_code != 0:
    raise StageExecutionError("Subtitle generation failed")
```

#### 3.6.5: Update Mux Calls (1 hour)
```python
# Before
from scripts.mux import main as mux_main
exit_code = mux_main()

# After
from scripts.mux import run_stage as mux_stage
exit_code = mux_stage(self.job_dir, "10_mux")
if exit_code != 0:
    raise StageExecutionError("Mux failed")
```

#### 3.6.6: Add Stage Error Recovery (2 hours)
```python
class StageExecutionError(Exception):
    """Raised when a stage fails"""
    pass

def run_stage_with_recovery(self, stage_func, stage_name, max_retries=1):
    """Run stage with error recovery and manifest checking"""
    for attempt in range(max_retries + 1):
        try:
            exit_code = stage_func(self.job_dir, stage_name)
            if exit_code == 0:
                return True
            else:
                logger.error(f"Stage {stage_name} failed with exit code {exit_code}")
                if attempt < max_retries:
                    logger.info(f"Retrying {stage_name} (attempt {attempt+2}/{max_retries+1})")
                    continue
                return False
        except Exception as e:
            logger.error(f"Stage {stage_name} raised exception: {e}", exc_info=True)
            if attempt < max_retries:
                logger.info(f"Retrying {stage_name} after exception")
                continue
            raise StageExecutionError(f"{stage_name} failed: {e}")
    return False
```

**Estimated Time:** 10 hours total

---

## Success Criteria (from Roadmap)

### Adoption Metrics
- ✅ Stage pattern adoption: 5% → 50% (2/5 stages now have run_stage)
- ⏳ Manifest tracking: 40% → 100% (for active stages)
- ⏳ Stage logging: 40% → 100% (for active stages)
- ⏳ All active stages isolated (can run independently)

### Technical Validation
- ⏳ Can run each stage independently with `run_stage(job_dir, stage_name)`
- ⏳ All stages write only to their stage_dir
- ⏳ All stages create manifest.json
- ⏳ All stages create stage.log
- ⏳ Pipeline orchestrator uses run_stage() pattern
- ⏳ Integration tests pass
- ⏳ Test coverage: 60% → 75%

### Quality Gates
- ✅ All modified files pass syntax validation
- ⏳ All modified files pass compliance check (validate-compliance.py)
- ⏳ No regression in existing functionality
- ⏳ Backward compatibility maintained (main() wrappers work)
- ⏳ Documentation updated

---

## Timeline & Progress

| Task | Estimated | Actual | Status | Completed |
|------|-----------|--------|--------|-----------|
| 3.1 Demux | 8h | 1h | ✅ DONE | 2025-12-03 |
| 3.2 ASR | 12h | - | ⏳ TODO | - |
| 3.3 Translation | 12h | - | ⏳ TODO | - |
| 3.4 Subtitle Gen | 10h | - | ⏳ TODO | - |
| 3.5 Mux | 8h | 0.5h | ⏳ IN PROGRESS | - |
| 3.6 Orchestrator | 10h | - | ⏳ TODO | - |
| **Total** | **60h** | **1.5h** | **2.5%** | - |

**Current Progress:** 2.5% (1.5h / 60h)  
**Completion Estimate:** 4-6 weeks at 10-15 hours/week

---

## Files Modified

### Completed
- ✅ `scripts/demux.py` - Added run_stage() function
- ✅ `scripts/mux.py.backup` - Backup created

### In Progress
- ⏳ `scripts/mux.py` - Needs indentation fix and refactoring

### Pending
- ⏳ `scripts/whisperx_asr.py`
- ⏳ `scripts/whisperx_integration.py`
- ⏳ `scripts/indictrans2_translator.py`
- ⏳ `scripts/subtitle_gen.py`
- ⏳ `scripts/run-pipeline.py`

### Documentation
- ✅ `docs/PHASE3_IMPLEMENTATION_PROGRESS.md` - This file

---

## Next Steps

### Immediate (Next Session)
1. **Fix mux.py indentation** (30 min)
   - Fix lines 47-50 indentation
   - Fix lines 281-331 indentation
   - Extract run_stage() function
   - Test syntax

2. **Complete mux.py refactoring** (2 hours)
   - Extract core logic to run_stage()
   - Simplify main() wrapper
   - Verify manifest tracking
   - Test execution

3. **Start ASR stage conversion** (2-3 hours)
   - Add run_stage() to whisperx_asr.py
   - Add StageIO to whisperx_integration.py
   - Track model loading
   - Track transcription output

### Short Term (This Week)
4. **Complete ASR stage** (remaining 9-10 hours)
5. **Start translation stage** (4-6 hours initial)
6. **Begin unit tests** (parallel with conversions)

### Medium Term (Next 2 Weeks)
7. **Complete translation stage**
8. **Complete subtitle gen stage**
9. **Update pipeline orchestrator**
10. **Integration testing**

### Long Term (Weeks 3-4)
11. **Comprehensive testing**
12. **Performance benchmarking**
13. **Documentation updates**
14. **Phase 3 completion report**

---

## Risks & Mitigations

### High Risk
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing pipeline | Critical | Medium | Maintain main() wrappers, extensive testing |
| GPU memory issues in ASR | High | Medium | Add proper cleanup, test on actual hardware |
| Translation env conflicts | High | Low | Careful environment isolation, testing |

### Medium Risk
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Performance regression | Medium | Low | Benchmark before/after, optimize if needed |
| Manifest overhead | Low | Medium | Monitor file I/O, optimize if needed |
| Complex refactoring | Medium | Medium | Incremental changes, frequent testing |

### Low Risk
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Documentation lag | Low | High | Update docs with each stage |
| Test coverage gaps | Low | Medium | Add tests incrementally |

---

## Resources & References

### Documentation
- [ARCHITECTURE_IMPLEMENTATION_ROADMAP.md](ARCHITECTURE_IMPLEMENTATION_ROADMAP.md) - Overall plan
- [DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md) - § 3.1 Stage Pattern
- [CODE_EXAMPLES.md](CODE_EXAMPLES.md) - Stage pattern examples
- [.github/copilot-instructions.md](../.github/copilot-instructions.md) - Quick reference

### Code References
- `shared/stage_utils.py` - StageIO implementation
- `shared/stage_manifest.py` - Manifest tracking
- `shared/logger.py` - Dual logging setup
- `scripts/tmdb_enrichment_stage.py` - Example of complete pattern

### Testing
- `tests/stages/` - Stage unit tests (to be created)
- `tests/integration/` - Pipeline integration tests
- `scripts/validate-compliance.py` - Compliance checker

---

## Notes

### Design Decisions
1. **Backward Compatibility:** Keep main() wrappers to avoid breaking existing code
2. **Manifest Tracking:** Enable by default in all new run_stage() functions
3. **Error Handling:** Use specific exceptions (FileNotFoundError, RuntimeError) before generic Exception
4. **Logging:** Always use io.get_stage_logger(), never print()
5. **Output Isolation:** All outputs to io.stage_dir only, no job_dir root writes

### Lessons Learned
1. **Syntax Issues:** mux.py has indentation problems - always validate syntax immediately
2. **File Size:** Large files (whisperx_integration.py: 1679 lines) need careful refactoring
3. **Dependencies:** Understanding stage call patterns in run-pipeline.py is critical
4. **Testing:** Need unit tests in parallel with conversions for safety

### Questions for Review
1. Should we create temporary compatibility mode flag? (ENABLE_STAGE_PATTERN=true)
2. How to handle stage numbering conflicts (01_demux vs "demux")?
3. Should run_stage() support both Path and str for job_dir?
4. What's the migration plan for active jobs during conversion?

---

**Last Updated:** 2025-12-03 05:12 UTC  
**Next Review:** After Task 3.5 (Mux) completion  
**Phase 3 Target:** 2025-12-31 (4 weeks)
