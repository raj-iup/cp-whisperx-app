# Architecture Implementation Roadmap

**Date:** 2025-12-03  
**Status:** Ready for Implementation  
**Compliance:** 🎊 100% Perfect Compliance  
**Pre-commit Hook:** ✅ Active

**Based On:** [ARCHITECTURE_GAP_ANALYSIS.md](ARCHITECTURE_GAP_ANALYSIS.md)

---

## Executive Summary

**Goal:** Align code implementation with documented architecture over 5 phases spanning 21 weeks.

**Current State:** 55% aligned (gaps in stage modularity, testing, manifest adoption)  
**Target State:** 95%+ aligned (fully modular pipeline with comprehensive testing)

**Total Effort:** 250 hours (6.25 person-weeks)  
**Timeline:** 21 weeks (5 months with part-time effort)

### Quick Status

| Phase | Duration | Effort | Status | Priority |
|-------|----------|--------|--------|----------|
| Phase 1: Documentation Sync | 2 weeks | 25 hours | 🟢 Ready | P0 Critical |
| Phase 2: Testing Infrastructure | 3 weeks | 40 hours | 🟡 Blocked by P1 | P1 High |
| Phase 3: Stage Pattern Adoption | 4 weeks | 60 hours | 🟡 Blocked by P1 | P0 Critical |
| Phase 4: Full Pipeline Implementation | 8 weeks | 95 hours | 🔴 Blocked by P3 | P2 Medium |
| Phase 5: Advanced Features | 4 weeks | 30 hours | 🔴 Blocked by P4 | P3 Low |

---

## Phase 1: Documentation Sync (2 Weeks)

**Goal:** Make documentation accurately reflect current implementation while planning future state.

**Priority:** 🔴 P0 Critical  
**Effort:** 25 hours  
**Dependencies:** None  
**Blocking:** Phases 2, 3

### Why This Matters

Current mismatch between docs and code causes:
- New developers get confused
- Standards document describes ideal, not reality
- AI assistants generate code that doesn't match codebase
- Wasted time debugging "missing" features

### Tasks

#### 1.1 Update Pipeline Documentation (8 hours)

**Files:**
- `docs/technical/pipeline.md`
- `docs/technical/architecture.md`
- `README.md`

**Changes:**

```markdown
# Add to docs/technical/pipeline.md

## Current Implementation (v2.0)

### Active Stages (3-6 stages)

**Transcribe Workflow:**
1. ✅ Demux - Audio extraction (scripts/demux.py)
2. ✅ ASR - Speech recognition (scripts/whisperx_asr.py)
3. ✅ Alignment - Word-level timestamps (inline in ASR)

**Translate Workflow:**
1. ✅ Demux - Audio extraction
2. ✅ ASR - Speech recognition
3. ✅ Alignment - Word-level timestamps
4. ✅ Translation - IndicTrans2 (scripts/indictrans2_translator.py)
5. ✅ Subtitle Gen - SRT generation (inline function)

**Subtitle Workflow:**
1-5. (Same as Translate)
6. ✅ Mux - Video embedding (scripts/mux.py)

### Future Architecture (v3.0)

**Planned 10-Stage Pipeline:**

1. ✅ 01_demux - Audio extraction (implemented)
2. ⏳ 02_tmdb - TMDB metadata enrichment (script exists, not integrated)
3. ⏳ 03_glossary_load - Glossary loading (partial implementation)
4. ✅ 04_asr - Speech recognition (implemented as scripts/whisperx_asr.py)
5. ⏳ 05_ner - Named entity recognition (scripts exist, not integrated)
6. ⏳ 06_lyrics_detection - Lyrics detection (standalone, needs integration)
7. ⏳ 07_hallucination_removal - Remove hallucinations (standalone)
8. ⏳ 08_translation - IndicTrans2 translation (partially integrated)
9. ⏳ 09_subtitle_gen - Professional SRT/VTT (inline, needs module)
10. ✅ 10_mux - Video embedding (implemented)

**Legend:**
- ✅ Implemented and integrated
- ⏳ Implemented but not integrated as stage
- ❌ Not implemented yet

**Migration Path:** See [ARCHITECTURE_IMPLEMENTATION_ROADMAP.md](../ARCHITECTURE_IMPLEMENTATION_ROADMAP.md)
```

**Deliverables:**
- ✅ Updated pipeline.md with current vs future sections
- ✅ Updated architecture.md with implementation status
- ✅ Updated README.md with accurate stage list
- ✅ Added "Future Architecture" section to all relevant docs

#### 1.2 Document Stage Module Pattern Reality (5 hours)

**Files:**
- `docs/developer/DEVELOPER_STANDARDS.md`
- `docs/CODE_EXAMPLES.md`

**Changes:**

```markdown
# Add to DEVELOPER_STANDARDS.md § 3.1

## § 3.1 Stage Implementation Pattern

### Current Reality (v2.0)

**Stage Pattern Adoption:** 5% (2/44 files)

Most stages currently implemented as utility scripts without:
- ❌ run_stage() function
- ❌ StageIO initialization
- ❌ Manifest tracking
- ⚠️ Partial logging compliance

**Files Using Pattern:**
- ✅ scripts/tmdb_enrichment_stage.py
- ✅ scripts/validate-compliance.py (not a stage)

**Migration in Progress:** See Phase 3 roadmap.

### Target Pattern (v3.0)

All pipeline stages will follow this pattern:

[... existing pattern documentation ...]

### Migration Checklist

When converting a script to stage pattern:
- [ ] Add run_stage() function
- [ ] Initialize StageIO with enable_manifest=True
- [ ] Use io.get_stage_logger() for logging
- [ ] Track all inputs with io.manifest.add_input()
- [ ] Track all outputs with io.manifest.add_output()
- [ ] Write outputs ONLY to io.stage_dir
- [ ] Finalize manifest with exit code
- [ ] Add unit tests for stage
- [ ] Update pipeline orchestrator to call run_stage()
```

**Deliverables:**
- ✅ DEVELOPER_STANDARDS.md updated with current reality
- ✅ CODE_EXAMPLES.md updated with migration examples
- ✅ Migration checklist for stage conversion

#### 1.3 Create Implementation Status Dashboard (4 hours)

**File:** `docs/IMPLEMENTATION_STATUS.md`

**Content:**

```markdown
# Implementation Status Dashboard

**Last Updated:** 2025-12-03  
**Overall Completion:** 55%

## Architecture Components

| Component | Documented | Implemented | Tested | Status |
|-----------|------------|-------------|--------|--------|
| Stage Architecture | ✅ | ⚠️ 30% | ⚠️ 20% | 🟡 Partial |
| Logging System | ✅ | ✅ 90% | ⚠️ 40% | 🟢 Good |
| Manifest Tracking | ✅ | ⚠️ 40% | ⚠️ 30% | 🟡 Partial |
| Configuration | ✅ | ✅ 100% | ✅ 80% | 🟢 Excellent |
| Error Handling | ✅ | ✅ 70% | ⚠️ 30% | 🟢 Good |
| Multi-Environment | ✅ | ✅ 95% | ⚠️ 50% | 🟢 Good |
| Stage Isolation | ✅ | ⚠️ 60% | ⚠️ 25% | 🟡 Partial |

## Stage Implementation Status

| Stage | Module Exists | Integrated | Uses StageIO | Has Manifest | Tested | Status |
|-------|---------------|------------|--------------|--------------|--------|--------|
| 01_demux | ✅ | ✅ | ❌ | ❌ | ⚠️ | 🟡 Partial |
| 02_tmdb | ✅ | ❌ | ✅ | ✅ | ❌ | 🟡 Not Integrated |
| 03_glossary_load | ⚠️ | ⚠️ | ❌ | ❌ | ❌ | 🟡 Partial |
| 04_asr | ✅ | ✅ | ❌ | ❌ | ⚠️ | 🟡 Partial |
| 05_ner | ✅ | ❌ | ❌ | ❌ | ⚠️ | 🔴 Not Integrated |
| 06_lyrics | ✅ | ❌ | ❌ | ❌ | ✅ | 🔴 Not Integrated |
| 07_hallucination | ✅ | ❌ | ❌ | ❌ | ⚠️ | 🔴 Not Integrated |
| 08_translation | ✅ | ✅ | ❌ | ❌ | ⚠️ | 🟡 Partial |
| 09_subtitle_gen | ⚠️ | ✅ | ❌ | ❌ | ❌ | 🟡 Inline Only |
| 10_mux | ✅ | ✅ | ❌ | ❌ | ⚠️ | 🟡 Partial |

**Legend:**
- ✅ Complete
- ⚠️ Partial
- ❌ Missing
- 🟢 Good
- 🟡 Needs Work
- 🔴 Critical Gap
```

**Deliverables:**
- ✅ Implementation status dashboard created
- ✅ Per-component status tracking
- ✅ Per-stage status tracking
- ✅ Automated update script (optional)

#### 1.4 Update Copilot Instructions (4 hours)

**File:** `.github/copilot-instructions.md`

**Changes:**

```markdown
# Add to copilot-instructions.md after Quick Navigation

## 🚧 Implementation Status

**Current Architecture:** v2.0 (simplified 3-6 stage pipeline)  
**Target Architecture:** v3.0 (modular 10-stage pipeline)  
**Migration Progress:** 55% complete

### What Works Now (v2.0)

✅ **Use These:**
- Configuration loading (100% compliant)
- Logging system (90% compliant)
- Multi-environment support
- Error handling patterns

⚠️ **Partially Implemented:**
- Stage module pattern (5% adoption)
- Manifest tracking (40% adoption)
- Stage isolation (60% adoption)

### What's Coming (v3.0)

⏳ **In Development:**
- Full 10-stage modular pipeline
- Universal StageIO adoption
- Complete manifest tracking
- Stage-level testing

**See:** [IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for current progress.

### Code Generation Guidelines

When generating new stage code:
1. ✅ Follow DEVELOPER_STANDARDS.md patterns (even if not widely adopted yet)
2. ✅ Use StageIO pattern with manifests
3. ✅ Write to io.stage_dir only
4. ⚠️ Existing stages may not follow pattern (migration in progress)

When modifying existing code:
1. 🎯 Match existing patterns for consistency
2. 📝 Add TODO comment for v3.0 migration
3. 🔄 Consider gradual refactoring if time permits
```

**Deliverables:**
- ✅ Copilot instructions updated with reality
- ✅ Version awareness added
- ✅ Migration guidance added

#### 1.5 Create Migration Guide (4 hours)

**File:** `docs/developer/MIGRATION_GUIDE.md`

**Content:**

```markdown
# Migration Guide: v2.0 → v3.0

**Purpose:** Guide for migrating existing stages to v3.0 architecture.

## Overview

**Current (v2.0):** Simplified pipeline with inline stages  
**Target (v3.0):** Modular 10-stage pipeline with StageIO pattern

**Timeline:** 21 weeks (Phases 1-5)

## What's Changing

### Stage Structure

**Before (v2.0):**
```python
# scripts/example_stage.py
def process(input_path, output_path):
    # Direct processing
    print("Processing...")  # ❌ Uses print
    result = transform(input_path)
    save(result, output_path)
```

**After (v3.0):**
```python
# scripts/example_stage.py
def run_stage(job_dir: Path, stage_name: str = "example") -> int:
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    input_file = io.job_dir / "prev_stage" / "input.ext"
    io.manifest.add_input(input_file, io.compute_hash(input_file))
    
    output_file = io.stage_dir / "output.ext"
    
    logger.info("Processing...")  # ✅ Uses logger
    result = transform(input_file)
    save(result, output_file)
    
    io.manifest.add_output(output_file, io.compute_hash(output_file))
    io.finalize_stage_manifest(exit_code=0)
    return 0
```

[... detailed migration steps ...]
```

**Deliverables:**
- ✅ Migration guide created
- ✅ Before/after code examples
- ✅ Step-by-step conversion process
- ✅ Testing checklist

### Phase 1 Deliverables

- [x] Updated pipeline.md with current/future sections
- [x] Updated DEVELOPER_STANDARDS.md with reality
- [x] Created IMPLEMENTATION_STATUS.md dashboard
- [x] Updated copilot-instructions.md
- [x] Created MIGRATION_GUIDE.md

### Phase 1 Success Criteria

- ✅ All docs accurately describe current state
- ✅ Future architecture clearly documented
- ✅ Migration path defined
- ✅ No confusion between current and target state
- ✅ Developers know what to follow

---

## Phase 2: Testing Infrastructure (3 Weeks)

**Goal:** Build comprehensive testing infrastructure to enable safe refactoring.

**Priority:** 🟡 P1 High  
**Effort:** 40 hours  
**Dependencies:** Phase 1 complete  
**Blocking:** Phases 3, 4

### Why This Matters

Cannot safely refactor pipeline without tests:
- Risk breaking existing functionality
- Cannot verify stage isolation
- Cannot test error recovery
- Cannot benchmark performance

### Tasks

#### 2.1 Create Pipeline Integration Tests (16 hours)

**File:** `tests/integration/test_pipeline_end_to_end.py`

**Tests to Add:**

```python
def test_transcribe_workflow_complete():
    """Test full transcribe workflow: demux → asr → alignment"""
    # Prepare test job
    # Run pipeline
    # Verify outputs exist
    # Verify output quality
    # Verify logs created
    # Verify manifests created

def test_translate_workflow_complete():
    """Test full translate workflow: demux → asr → translation → subtitle"""
    # Similar to above

def test_subtitle_workflow_complete():
    """Test full subtitle workflow with muxing"""
    # Similar to above

def test_pipeline_resume_after_failure():
    """Test pipeline can resume from failed stage"""
    # Simulate stage failure
    # Verify resume works
    # Verify no duplicate work

def test_pipeline_stage_isolation():
    """Test stages don't interfere with each other"""
    # Run multiple jobs in parallel
    # Verify outputs don't mix
    # Verify logs don't mix
```

**Deliverables:**
- ✅ 5-10 integration tests
- ✅ Test fixtures for sample audio
- ✅ Test utilities for job creation
- ✅ CI/CD integration (GitHub Actions)

#### 2.2 Add Stage Unit Tests (12 hours)

**Files:**
- `tests/stages/test_demux_stage.py`
- `tests/stages/test_asr_stage.py`
- `tests/stages/test_translation_stage.py`
- (more as needed)

**Tests to Add:**

```python
# tests/stages/test_demux_stage.py

def test_demux_creates_output():
    """Test demux creates audio file"""

def test_demux_handles_missing_input():
    """Test demux handles missing video file"""

def test_demux_creates_manifest():
    """Test demux creates stage manifest"""

def test_demux_tracks_inputs_outputs():
    """Test demux tracks input/output files"""

def test_demux_creates_stage_log():
    """Test demux creates stage.log"""
```

**Deliverables:**
- ✅ 30-50 stage unit tests
- ✅ Test coverage for all active stages
- ✅ Mocking utilities for expensive operations
- ✅ Performance benchmarks

#### 2.3 Add Test Utilities (8 hours)

**File:** `tests/utils/test_helpers.py`

**Utilities to Add:**

```python
# Job creation utilities
def create_test_job(workflow="transcribe", audio_file=None):
    """Create test job with sample audio"""

def cleanup_test_job(job_dir):
    """Clean up test job files"""

# Assertion utilities
def assert_stage_completed(job_dir, stage_name):
    """Assert stage completed successfully"""

def assert_manifest_valid(manifest_path):
    """Assert manifest is valid and complete"""

def assert_logs_exist(job_dir, stage_name):
    """Assert stage logs exist"""

# Mock utilities
def mock_whisperx_model():
    """Mock WhisperX model for testing"""

def mock_indictrans2_model():
    """Mock IndicTrans2 model for testing"""
```

**Deliverables:**
- ✅ Test utilities module
- ✅ Mock model fixtures
- ✅ Sample audio files (various formats, lengths)
- ✅ Test job templates

#### 2.4 Add CI/CD Pipeline (4 hours)

**File:** `.github/workflows/tests.yml`

**Workflow:**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements/requirements.txt -r requirements/requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/unit -v --cov
      - name: Run integration tests
        run: pytest tests/integration -v --cov-append
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

**Deliverables:**
- ✅ GitHub Actions workflow
- ✅ Code coverage reporting
- ✅ Test result artifacts
- ✅ Performance benchmarks

### Phase 2 Deliverables

- [x] 5-10 pipeline integration tests
- [x] 30-50 stage unit tests
- [x] Test utilities and fixtures
- [x] CI/CD pipeline
- [x] Code coverage reporting

### Phase 2 Success Criteria

- ✅ Test coverage: 60%+ (up from ~35%)
- ✅ Integration tests pass
- ✅ Can run tests in CI/CD
- ✅ Can verify stage isolation
- ✅ Can test error recovery

---

## Phase 3: Stage Pattern Adoption (4 Weeks)

**Goal:** Convert critical stages to use StageIO pattern with manifest tracking.

**Priority:** 🔴 P0 Critical  
**Effort:** 60 hours  
**Dependencies:** Phases 1, 2 complete  
**Blocking:** Phase 4

### Why This Matters

Stage pattern provides:
- Consistent logging and error handling
- Manifest tracking for data lineage
- Stage isolation for parallel execution
- Testing hooks for validation
- Foundation for modular pipeline

### Tasks

#### 3.1 Convert Demux Stage (8 hours)

**File:** `scripts/demux.py` → Add `run_stage()` function

**Changes:**

1. Add StageIO initialization
2. Add manifest tracking
3. Add stage logging
4. Ensure output only to io.stage_dir
5. Add unit tests
6. Update pipeline orchestrator to call run_stage()

**Template:**

```python
#!/usr/bin/env python3
# Standard library
import sys
from pathlib import Path

# Local
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.stage_utils import StageIO
from shared.config import load_config

def run_stage(job_dir: Path, stage_name: str = "01_demux") -> int:
    """
    Demux stage: Extract audio from video
    
    Args:
        job_dir: Job directory containing input video
        stage_name: Stage name for logging
        
    Returns:
        0 on success, 1 on failure
    """
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        config = load_config()
        
        # Find input video
        input_video = io.job_dir / "input.mp4"  # Or from manifest
        if not input_video.exists():
            raise FileNotFoundError(f"Input video not found: {input_video}")
        
        io.manifest.add_input(input_video, io.compute_hash(input_video))
        
        # Define output
        output_audio = io.stage_dir / "audio.wav"
        
        # Extract audio
        logger.info(f"Extracting audio from {input_video.name}")
        extract_audio(input_video, output_audio, config)  # Existing logic
        
        # Track output
        io.manifest.add_output(output_audio, io.compute_hash(output_audio))
        
        logger.info("Demux completed successfully")
        io.finalize_stage_manifest(exit_code=0)
        return 0
        
    except Exception as e:
        logger.error(f"Demux failed: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1

# Keep existing extract_audio() function for backward compatibility
def extract_audio(input_video, output_audio, config):
    """Existing demux logic (unchanged)"""
    pass
```

**Testing:**

```python
# tests/stages/test_demux_stage.py

def test_demux_run_stage():
    job_dir = create_test_job()
    exit_code = run_stage(job_dir, "01_demux")
    assert exit_code == 0
    assert (job_dir / "01_demux" / "audio.wav").exists()
    assert (job_dir / "01_demux" / "manifest.json").exists()
    assert (job_dir / "01_demux" / "stage.log").exists()
```

**Deliverables:**
- ✅ scripts/demux.py converted
- ✅ Unit tests added
- ✅ Integration test updated
- ✅ Documentation updated

#### 3.2 Convert ASR Stage (12 hours)

**File:** `scripts/whisperx_asr.py` → Add `run_stage()` function

**Complexity:** Higher (model loading, GPU management)

**Additional Requirements:**
- Handle model caching
- Manage GPU memory
- Track model artifacts
- Log performance metrics

**Deliverables:**
- ✅ scripts/whisperx_asr.py converted
- ✅ Unit tests added (with model mocking)
- ✅ Performance benchmarks
- ✅ GPU memory profiling

#### 3.3 Convert Translation Stage (12 hours)

**File:** `scripts/indictrans2_translator.py` → Add `run_stage()` function

**Additional Requirements:**
- Handle multiple target languages
- Track per-language outputs
- Manage environment switching
- Log translation metrics

**Deliverables:**
- ✅ scripts/indictrans2_translator.py converted
- ✅ Unit tests added
- ✅ Multi-language test cases
- ✅ Environment switching tests

#### 3.4 Convert Subtitle Gen Stage (10 hours)

**Current:** Inline function in run-pipeline.py  
**Target:** `scripts/subtitle_gen.py` module

**New File Structure:**

```python
# scripts/subtitle_gen.py

def run_stage(job_dir: Path, stage_name: str = "09_subtitle_gen") -> int:
    """Generate SRT subtitles from translations"""
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        # Find translation files
        trans_dir = io.job_dir / "08_translation"
        trans_files = list(trans_dir.glob("transcript_*.txt"))
        
        for trans_file in trans_files:
            io.manifest.add_input(trans_file, io.compute_hash(trans_file))
            
            # Generate SRT
            lang = trans_file.stem.split("_")[-1]
            srt_file = io.stage_dir / f"subtitles_{lang}.srt"
            
            generate_srt(trans_file, srt_file)  # Existing logic
            
            io.manifest.add_output(srt_file, io.compute_hash(srt_file))
            logger.info(f"Generated subtitles: {lang}")
        
        io.finalize_stage_manifest(exit_code=0)
        return 0
        
    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1
```

**Deliverables:**
- ✅ scripts/subtitle_gen.py created
- ✅ Logic extracted from run-pipeline.py
- ✅ Unit tests added
- ✅ SRT validation tests

#### 3.5 Convert Mux Stage (8 hours)

**File:** `scripts/mux.py` → Add `run_stage()` function

**Deliverables:**
- ✅ scripts/mux.py converted
- ✅ Unit tests added
- ✅ Video validation tests

#### 3.6 Update Pipeline Orchestrator (10 hours)

**File:** `scripts/run-pipeline.py`

**Changes:**

```python
# Before
def run_demux(self):
    from scripts.demux import extract_audio
    extract_audio(input_video, output_audio, config)

# After
def run_demux(self):
    from scripts.demux import run_stage
    exit_code = run_stage(self.job_dir, "01_demux")
    if exit_code != 0:
        raise StageExecutionError("Demux failed")
```

**Deliverables:**
- ✅ Pipeline orchestrator updated for all converted stages
- ✅ Error handling improved
- ✅ Stage status tracking enhanced
- ✅ Integration tests passing

### Phase 3 Deliverables

- [x] 5 critical stages converted to StageIO pattern
- [x] 100% of active stages use manifests
- [x] 100% of active stages use stage logging
- [x] Pipeline orchestrator updated
- [x] All tests passing

### Phase 3 Success Criteria

- ✅ Stage pattern adoption: 5% → 50%
- ✅ Manifest tracking: 40% → 100% (for active stages)
- ✅ All active stages isolated
- ✅ Can run stages independently
- ✅ Test coverage: 60% → 75%

---

## Phase 4: Full Pipeline Implementation (8 Weeks)

**Goal:** Implement remaining stages to achieve full 10-stage modular pipeline.

**Priority:** 🟡 P2 Medium  
**Effort:** 95 hours  
**Dependencies:** Phase 3 complete  
**Blocking:** Phase 5

### Why This Matters

Full pipeline provides:
- Selective stage enable/disable
- Better quality control
- Modular testing
- Extensibility
- Production-ready architecture

### Tasks

#### 4.1 Integrate TMDB Enrichment Stage (8 hours)

**Status:** Script exists, needs integration

**File:** `scripts/tmdb_enrichment_stage.py` (already has run_stage)

**Tasks:**
- ✅ Script already follows pattern
- Add to pipeline orchestrator
- Add stage configuration
- Add unit tests
- Add to workflows

**Deliverables:**
- ✅ 02_tmdb integrated into pipeline
- ✅ Stage can be enabled/disabled
- ✅ Tests added

#### 4.2 Implement Glossary Load Stage (12 hours)

**Status:** Partial directory exists

**File:** Create `scripts/03_glossary_load/glossary_loader.py`

**Tasks:**
- Design stage interface
- Implement run_stage()
- Load glossary files
- Track glossary terms
- Add to pipeline orchestrator
- Add tests

**Deliverables:**
- ✅ 03_glossary_load implemented
- ✅ Integrated into pipeline
- ✅ Tests added

#### 4.3 Integrate NER Stage (15 hours)

**Status:** Scripts exist (ner_extraction.py, post_ner.py, pre_ner.py)

**File:** Create `scripts/05_ner/ner_stage.py`

**Tasks:**
- Unify NER scripts into single stage
- Implement run_stage()
- Add entity tracking
- Add to pipeline orchestrator
- Add tests

**Complexity:** Higher (multiple scripts to unify)

**Deliverables:**
- ✅ 05_ner implemented
- ✅ NER scripts unified
- ✅ Tests added

#### 4.4 Integrate Lyrics Detection Stage (12 hours)

**Status:** Script exists (lyrics_detector.py)

**File:** `scripts/06_lyrics_detection/lyrics_stage.py`

**Tasks:**
- Convert to stage module
- Implement run_stage()
- Track lyrics segments
- Add to pipeline orchestrator
- Add tests

**Deliverables:**
- ✅ 06_lyrics_detection implemented
- ✅ Tests added

#### 4.5 Integrate Hallucination Removal Stage (12 hours)

**Status:** Script exists (hallucination_removal.py)

**File:** `scripts/07_hallucination_removal/hallucination_stage.py`

**Tasks:**
- Convert to stage module
- Implement run_stage()
- Track removed segments
- Add to pipeline orchestrator
- Add tests

**Deliverables:**
- ✅ 07_hallucination_removal implemented
- ✅ Tests added

#### 4.6 Implement Stage Configuration System (16 hours)

**Goal:** Allow enabling/disabling stages per job

**File:** `config/.env.pipeline`

**Add Configuration:**

```bash
# Stage Enable/Disable
STAGE_02_TMDB_ENABLED=false
STAGE_03_GLOSSARY_ENABLED=true
STAGE_05_NER_ENABLED=true
STAGE_06_LYRICS_ENABLED=true
STAGE_07_HALLUCINATION_ENABLED=true

# Stage-specific config
TMDB_API_KEY=xxx
LYRICS_DETECTION_THRESHOLD=0.8
HALLUCINATION_REMOVAL_AGGRESSIVE=false
```

**Pipeline Orchestrator Changes:**

```python
def get_enabled_stages(self, workflow):
    """Get list of enabled stages for workflow"""
    config = load_config()
    
    base_stages = WORKFLOW_STAGES[workflow]
    
    # Filter based on config
    enabled = []
    for stage in base_stages:
        stage_num = stage.split("_")[0]
        enabled_key = f"STAGE_{stage_num}_{stage.split('_')[1].upper()}_ENABLED"
        if config.get(enabled_key, "true").lower() == "true":
            enabled.append(stage)
    
    return enabled
```

**Deliverables:**
- ✅ Stage enable/disable configuration
- ✅ Pipeline respects configuration
- ✅ Tests for stage filtering
- ✅ Documentation updated

#### 4.7 Add Stage Dependencies System (12 hours)

**Goal:** Declare stage dependencies, auto-validate

**File:** `shared/stage_dependencies.py`

**Implementation:**

```python
# shared/stage_dependencies.py

STAGE_DEPENDENCIES = {
    "01_demux": [],
    "02_tmdb": ["01_demux"],
    "03_glossary_load": [],
    "04_asr": ["01_demux"],
    "05_ner": ["04_asr"],
    "06_lyrics_detection": ["04_asr"],
    "07_hallucination_removal": ["04_asr", "06_lyrics_detection"],
    "08_translation": ["04_asr", "05_ner", "07_hallucination_removal"],
    "09_subtitle_gen": ["08_translation"],
    "10_mux": ["09_subtitle_gen"],
}

def validate_stage_dependencies(enabled_stages):
    """Validate all dependencies are satisfied"""
    for stage in enabled_stages:
        deps = STAGE_DEPENDENCIES.get(stage, [])
        for dep in deps:
            if dep not in enabled_stages:
                raise ValueError(f"Stage {stage} requires {dep} but it is not enabled")
```

**Deliverables:**
- ✅ Dependency system implemented
- ✅ Validation on pipeline start
- ✅ Clear error messages
- ✅ Tests added

#### 4.8 Migration and Testing (8 hours)

**Tasks:**
- Migrate existing jobs to new pipeline
- Add compatibility layer for old jobs
- Update documentation
- Add migration scripts

**Deliverables:**
- ✅ Migration guide for users
- ✅ Compatibility maintained
- ✅ All integration tests passing

### Phase 4 Deliverables

- [x] 5 additional stages integrated (02, 03, 05, 06, 07)
- [x] Stage enable/disable configuration
- [x] Stage dependency validation
- [x] 10-stage pipeline fully functional
- [x] Migration guide and compatibility

### Phase 4 Success Criteria

- ✅ All 10 stages implemented
- ✅ Can enable/disable stages
- ✅ Dependencies validated automatically
- ✅ Test coverage: 75% → 85%
- ✅ Stage pattern adoption: 50% → 100%

---

## Phase 5: Advanced Features (4 Weeks)

**Goal:** Add advanced reliability, performance, and monitoring features.

**Priority:** 🟢 P3 Low  
**Effort:** 30 hours  
**Dependencies:** Phase 4 complete

### Why This Matters

Production features:
- Retry logic for transient failures
- Circuit breakers for external APIs
- Performance monitoring
- Graceful degradation
- Advanced caching

### Tasks

#### 5.1 Add Retry Logic (8 hours)

**File:** `shared/stage_utils.py`

**Implementation:**

```python
# shared/stage_utils.py

def with_retry(max_retries=3, backoff=2.0, exceptions=(Exception,)):
    """Decorator for retrying stage operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = backoff ** attempt
                    logger.warning(f"Retry {attempt+1}/{max_retries} after {wait_time}s: {e}")
                    time.sleep(wait_time)
        return wrapper
    return decorator
```

**Usage in Stages:**

```python
@with_retry(max_retries=3, exceptions=(APIError, NetworkError))
def fetch_tmdb_metadata(movie_id):
    """Fetch TMDB metadata with retry"""
    return tmdb_api.get_movie(movie_id)
```

**Deliverables:**
- ✅ Retry decorator implemented
- ✅ Applied to network operations
- ✅ Tests added
- ✅ Documentation updated

#### 5.2 Add Circuit Breaker (7 hours)

**File:** `shared/circuit_breaker.py`

**Implementation:**

```python
# shared/circuit_breaker.py

class CircuitBreaker:
    """Circuit breaker for external API calls"""
    
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failures = 0
        self.state = "closed"
    
    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"
```

**Deliverables:**
- ✅ Circuit breaker implemented
- ✅ Applied to TMDB API
- ✅ Applied to translation APIs
- ✅ Tests added

#### 5.3 Add Performance Monitoring (8 hours)

**File:** `shared/performance_monitor.py`

**Implementation:**

```python
# shared/performance_monitor.py

class PerformanceMonitor:
    """Monitor stage performance metrics"""
    
    def __init__(self, stage_name):
        self.stage_name = stage_name
        self.metrics = []
    
    def record_metric(self, name, value, unit):
        """Record performance metric"""
        self.metrics.append({
            "name": name,
            "value": value,
            "unit": unit,
            "timestamp": time.time()
        })
    
    def context(self, operation_name):
        """Context manager for timing operations"""
        return TimingContext(self, operation_name)

class TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, monitor, name):
        self.monitor = monitor
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        duration = time.time() - self.start_time
        self.monitor.record_metric(self.name, duration, "seconds")
```

**Usage in Stages:**

```python
monitor = PerformanceMonitor("04_asr")

with monitor.context("model_loading"):
    model = load_whisperx_model()

with monitor.context("transcription"):
    result = model.transcribe(audio)

# Save metrics to manifest
io.manifest.add_metrics(monitor.metrics)
```

**Deliverables:**
- ✅ Performance monitoring implemented
- ✅ Applied to all stages
- ✅ Metrics saved to manifests
- ✅ Reporting dashboard (optional)

#### 5.4 Add Smart Caching (7 hours)

**File:** `shared/cache_manager.py`

**Implementation:**

```python
# shared/cache_manager.py

class StageCache:
    """Cache stage outputs based on input hash"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def get(self, input_hash: str, stage_name: str) -> Optional[Path]:
        """Get cached output for input hash"""
        cache_key = f"{stage_name}_{input_hash}"
        cache_path = self.cache_dir / cache_key
        if cache_path.exists():
            return cache_path
        return None
    
    def put(self, input_hash: str, stage_name: str, output_files: List[Path]):
        """Cache stage output"""
        cache_key = f"{stage_name}_{input_hash}"
        cache_path = self.cache_dir / cache_key
        cache_path.mkdir(exist_ok=True)
        
        for file in output_files:
            shutil.copy2(file, cache_path / file.name)
```

**Deliverables:**
- ✅ Caching system implemented
- ✅ Applied to expensive stages (ASR, Translation)
- ✅ Tests added
- ✅ Cache management utilities

### Phase 5 Deliverables

- [x] Retry logic for transient failures
- [x] Circuit breakers for external APIs
- [x] Performance monitoring
- [x] Smart caching system
- [x] All tests passing

### Phase 5 Success Criteria

- ✅ Zero manual retries needed
- ✅ Graceful handling of API failures
- ✅ Performance metrics tracked
- ✅ Cache hit rate: 60%+
- ✅ Test coverage: 85% → 90%

---

## Summary Timeline

| Phase | Weeks | Hours | Status | Start | End |
|-------|-------|-------|--------|-------|-----|
| **Phase 1: Documentation Sync** | 2 | 25 | 🟢 Ready | Week 1 | Week 2 |
| **Phase 2: Testing Infrastructure** | 3 | 40 | 🟡 Blocked | Week 3 | Week 5 |
| **Phase 3: Stage Pattern Adoption** | 4 | 60 | 🟡 Blocked | Week 6 | Week 9 |
| **Phase 4: Full Pipeline** | 8 | 95 | 🔴 Blocked | Week 10 | Week 17 |
| **Phase 5: Advanced Features** | 4 | 30 | 🔴 Blocked | Week 18 | Week 21 |
| **Total** | **21** | **250** | | | |

## Resource Allocation

**Effort Breakdown:**
- Documentation: 25 hours (10%)
- Testing: 40 hours (16%)
- Stage conversion: 60 hours (24%)
- New stage implementation: 95 hours (38%)
- Advanced features: 30 hours (12%)

**Recommended Team:**
- 1 senior developer (40 hours/week) = 6 weeks full-time
- OR 2 developers (20 hours/week each) = 6 weeks part-time
- OR 1 developer (12 hours/week) = 21 weeks part-time

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Tests break during refactoring | High | High | Phase 2 first, comprehensive tests |
| Breaking existing jobs | Medium | Critical | Compatibility layer, migration guide |
| Performance regression | Low | Medium | Performance monitoring, benchmarks |
| Scope creep | Medium | High | Strict phase boundaries, clear goals |
| Resource availability | High | High | Part-time effort acceptable (21 weeks) |

## Success Metrics

### Technical Metrics

- **Stage Pattern Adoption:** 5% → 100%
- **Manifest Tracking:** 40% → 100%
- **Test Coverage:** 35% → 90%
- **Stage Isolation:** 60% → 100%
- **Documentation Accuracy:** 70% → 95%

### Quality Metrics

- **Integration Test Pass Rate:** 100%
- **Stage Independence:** Can run all stages individually
- **Error Recovery:** Automatic retry for 90% of transient failures
- **Cache Hit Rate:** 60%+ for repeated jobs

### Developer Experience

- **Onboarding Time:** 2 hours → 30 minutes
- **New Stage Time:** 8 hours → 2 hours (with template)
- **Debug Time:** 30 minutes → 5 minutes (with stage logs)
- **Confidence:** "Worried about breaking things" → "Confident in changes"

## Next Steps

1. **Review and Approve Roadmap** (1 day)
2. **Start Phase 1** (2 weeks)
3. **Weekly status updates**
4. **Monthly progress reviews**
5. **Adjust timeline as needed**

---

## Questions & Answers

**Q: Can we skip Phase 1?**  
A: No. Documentation sync prevents confusion during implementation. Critical for success.

**Q: Can we do Phase 3 before Phase 2?**  
A: Not recommended. Need tests to verify refactoring doesn't break anything.

**Q: What if we need to deliver faster?**  
A: Focus on Phases 1-3 only (9 weeks). Defer Phases 4-5 to future release.

**Q: What if something breaks?**  
A: Comprehensive tests in Phase 2 catch issues. Compatibility layer prevents user impact.

**Q: How do we track progress?**  
A: Update IMPLEMENTATION_STATUS.md weekly. Review metrics monthly.

---

**Roadmap Created:** 2025-12-03  
**Target Completion:** 2025-05-27 (21 weeks from now)  
**Status:** Ready for Implementation  
**Approver:** [Your Name]
