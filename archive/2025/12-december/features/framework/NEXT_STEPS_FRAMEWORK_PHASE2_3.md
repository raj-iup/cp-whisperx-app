# Next Steps: Framework Implementation - Phase 2 & 3

**Date:** 2025-12-08  
**Status:** 🔄 In Progress (Pipeline Running - Job 0004)  
**Current Task:** AD-014 Week 1 Day 3-4 Integration

---

## 📋 Framework Overview

**NEW REQUIREMENT:** All project work must follow this documentation hierarchy:

```
1. Business Requirement Document (BRD)
   └─> Why we're doing this, business value, success metrics
   
2. Technical Requirement Document (TRD)  
   └─> How we'll implement it, technical constraints, architecture
   
3. Implementation Tracker
   └─> Task breakdown, standards updates, documentation updates
   
4. Code Implementation + Documentation
   └─> Actual code, tests, guides, README, quickstart
```

---

## 🎯 Current Pipeline Status

**Job:** job-20251208-rpatel-0004  
**Workflow:** Transcribe  
**Media:** `in/Energy Demand in AI.mp4` (12.4 minutes)  
**Progress:** Stage 06 (ASR) - Transcribing with MLX backend (~1-2 minutes elapsed)

**Expected Completion:** ~5-10 minutes total

**Monitor:**
```bash
tail -f out/2025/12/08/rpatel/4/99_pipeline_*.log
```

---

## 📊 Phase 2: Backfill Framework with Existing Work

**Goal:** Create BRDs/TRDs for recently implemented ADs (AD-009 through AD-014)

### Task 2.1: AD-009 Development Philosophy (COMPLETE ✅)
**Status:** Already has comprehensive documentation  
**Documents:** 
- ✅ AD-009_DEVELOPMENT_PHILOSOPHY.md (exists)
- ⏳ BRD needed: Why quality-first approach was necessary
- ⏳ TRD needed: Technical implications of "no backward compatibility"

### Task 2.2: AD-010 Workflow-Specific Outputs (COMPLETE ✅)
**Status:** Fully implemented and documented  
**Documents:**
- ✅ Implementation complete (ARCHITECTURE.md § AD-010)
- ⏳ BRD needed: Business rationale for different output formats
- ⏳ TRD needed: Technical specification of output routing

### Task 2.3: AD-011 Robust File Path Handling (COMPLETE ✅)
**Status:** Comprehensive implementation  
**Documents:**
- ✅ ARCHITECTURE.md § AD-011 (complete)
- ⏳ BRD needed: Why file path errors were impacting users
- ⏳ TRD needed: pathlib + subprocess patterns specification

### Task 2.4: AD-012 Log Management (PARTIAL ⏳)
**Status:** Partially documented, not implemented  
**Documents:**
- ✅ ARCHITECTURE.md § AD-012 (specification exists)
- ⏳ BRD needed: Business case for centralized logs
- ⏳ TRD needed: Directory structure and helper functions
- ❌ Implementation needed: get_log_path() helper

### Task 2.5: AD-013 Test Organization (PARTIAL ⏳)
**Status:** Partially documented, not implemented  
**Documents:**
- ✅ ARCHITECTURE.md § AD-013 (specification exists)
- ⏳ BRD needed: Test discovery and CI/CD improvements
- ⏳ TRD needed: Directory categories and naming conventions
- ❌ Implementation needed: Reorganize existing tests

### Task 2.6: AD-014 Multi-Phase Subtitle Workflow (IN PROGRESS 🔄)
**Status:** Week 1 foundation complete, Day 3-4 in progress  
**Documents:**
- ✅ ARCHITECTURE.md § AD-014 (specification exists)
- ✅ AD014_WEEK1_DAY12_COMPLETE.md (foundation complete)
- ⏳ BRD needed: ROI of 70-80% speedup on iterations
- ⏳ TRD needed: Caching architecture and media identity
- 🔄 Implementation in progress: Integration with run-pipeline.py

---

## 🚀 Phase 3: High Priority Implementation

### Priority 1: AD-014 Multi-Phase Subtitle Workflow (IN PROGRESS 🔄)

**Current Status:** Week 1 Day 3-4 Integration  
**Time Estimate:** 2-4 hours remaining  
**Performance Target:** 70-80% faster iterations

#### 3.1.1 Complete Current Pipeline Run (30 min)
- [ ] Monitor job-20251208-rpatel-0004 completion
- [ ] Validate transcribe workflow output
- [ ] Measure baseline performance (first run)

#### 3.1.2 Integrate Caching (1-2 hours)
**Tasks:**
```bash
# 1. Update run-pipeline.py to use MediaCacheManager
# 2. Add media_id computation before ASR stage
# 3. Check for cached baseline before processing
# 4. Store baseline after first successful run
```

**Files to Modify:**
- `run-pipeline.py` - Add cache checks
- `scripts/06_asr.py` - Store ASR baseline
- `scripts/07_alignment.py` - Store alignment baseline

#### 3.1.3 Performance Validation (1 hour)
**Test Plan:**
1. Run subtitle workflow on `in/Jaane Tu Ya Jaane Na 2008.mp4` (first time)
2. Modify glossary or translation parameters
3. Run subtitle workflow again (should reuse baseline)
4. Measure speedup:
   - First run: ~X minutes
   - Second run: ~X minutes (target: 70-80% reduction)

**Success Criteria:**
- ✅ Second run skips demux/ASR/alignment
- ✅ Second run reuses cached baseline
- ✅ Speedup ≥70% on subtitle iterations
- ✅ Output quality unchanged

---

### Priority 2: AD-010 Workflow-Specific Outputs (2-3 hours)

**Performance Gain:** 15-30% (skip unnecessary stages)  
**Status:** ⏳ Not started

#### 3.2.1 Documentation (30 min)
- [ ] Create BRD for AD-010
- [ ] Create TRD for AD-010
- [ ] Update Implementation Tracker

#### 3.2.2 Implementation (1-2 hours)
**Tasks:**
```bash
# 1. Update run-pipeline.py stage selection
# 2. Transcribe workflow: Stop at stage 07
# 3. Translate workflow: Stop at stage 10  
# 4. Subtitle workflow: Run all 12 stages
```

**Changes:**
```python
# run-pipeline.py
if workflow == "transcribe":
    stages = stages[:7]  # Stop at alignment
    logger.info("Transcribe workflow: Skipping subtitle generation")
elif workflow == "translate":
    stages = [s for s in stages if s in ["demux", "asr", "alignment", "translation"]]
    logger.info("Translate workflow: Text output only")
```

#### 3.2.3 Testing (30 min)
- [ ] Test transcribe workflow (skip subtitle stages)
- [ ] Test translate workflow (skip subtitle stages)
- [ ] Validate output formats match AD-010 spec
- [ ] Measure performance improvement

**Expected Results:**
- Transcribe: 15-20% faster (skip 5 stages)
- Translate: 10-15% faster (skip 2 stages)

---

## 🔧 Medium Priority Implementation

### Task 3.3: AD-012 Log Management (1-2 hours)

**Goal:** Clean project root by centralizing all logs  
**Status:** ⏳ Not started

#### 3.3.1 Documentation (20 min)
- [ ] Create BRD for AD-012
- [ ] Create TRD for AD-012  
- [ ] Update Implementation Tracker

#### 3.3.2 Implementation (40 min)
**Create helper function:**
```python
# shared/log_paths.py
from pathlib import Path
from datetime import datetime

def get_log_path(category: str, workflow: str, feature: str) -> Path:
    """
    Get standardized log path.
    
    Args:
        category: testing, debugging, ci, development
        workflow: transcribe, translate, subtitle
        feature: asr, alignment, translation, etc.
        
    Returns:
        Path: logs/{category}/{workflow}/YYYYMMDD_HHMMSS_{feature}.log
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("logs") / category / workflow
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{timestamp}_{feature}.log"
```

**Update test scripts:**
```bash
# Find all manual test scripts creating logs in project root
find . -name "*.sh" -o -name "*.py" | xargs grep -l "> .*\.log" | grep -v venv
# Update each to use get_log_path()
```

#### 3.3.3 Testing (20 min)
- [ ] Run test script, verify log in logs/testing/
- [ ] Verify project root has no new .log files
- [ ] Update .gitignore to ignore logs/ directory

---

### Task 3.4: AD-013 Test Organization (2-3 hours)

**Goal:** Better test discovery and CI/CD integration  
**Status:** ⏳ Not started

#### 3.4.1 Documentation (30 min)
- [ ] Create BRD for AD-013
- [ ] Create TRD for AD-013
- [ ] Update Implementation Tracker

#### 3.4.2 Implementation (90 min)
**Reorganize existing tests:**
```bash
# Current state (scattered)
ls tests/
# → test_config.py, test_stage_utils.py, ...

# Target state (organized)
tests/
├── unit/
│   ├── test_config_loader.py
│   ├── test_stage_utils.py
│   └── test_logger.py
├── integration/
│   ├── test_asr_alignment.py
│   └── test_translation_pipeline.py
├── functional/
│   ├── test_transcribe_workflow.py
│   └── test_subtitle_workflow.py
└── manual/
    ├── transcribe/
    │   └── test-mlx-transcribe.sh
    └── subtitle/
        └── test-full-pipeline.sh
```

**Migration script:**
```python
# tools/reorganize_tests.py
# 1. Categorize each test file (unit/integration/functional)
# 2. Move to appropriate directory
# 3. Update imports if needed
# 4. Update pytest.ini
```

#### 3.4.3 Testing (30 min)
- [ ] Run `pytest tests/unit/` (fast tests only)
- [ ] Run `pytest tests/integration/` (medium tests)
- [ ] Verify all tests discovered correctly
- [ ] Update CI/CD configuration

---

## 📝 BRD/TRD Template Structure

### Business Requirement Document (BRD) Template
```markdown
# BRD: [Feature Name]

## 1. Executive Summary
- Problem statement
- Business impact
- Success metrics

## 2. Stakeholders
- End users
- Development team
- System operators

## 3. Requirements
- Functional requirements
- Non-functional requirements
- Constraints

## 4. Success Criteria
- Measurable outcomes
- Performance targets
- Quality gates

## 5. ROI Analysis
- Time savings
- Cost reduction
- Quality improvement
```

### Technical Requirement Document (TRD) Template
```markdown
# TRD: [Feature Name]

## 1. Technical Overview
- Architecture changes
- Technology stack
- Dependencies

## 2. Design Specifications
- Data structures
- Algorithms
- APIs

## 3. Implementation Plan
- Task breakdown
- File changes
- Test requirements

## 4. Risk Assessment
- Technical risks
- Mitigation strategies
- Rollback plan

## 5. Performance Targets
- Benchmarks
- Resource utilization
- Scalability
```

---

## 🎯 Recommended Execution Order

### Session 1 (TODAY - 2-3 hours)
1. ✅ Complete pipeline run (in progress)
2. ⏳ Validate transcribe workflow output
3. ⏳ Measure baseline performance
4. ⏳ Integrate caching into run-pipeline.py

### Session 2 (Next - 2-3 hours)
5. ⏳ Run performance tests (first vs. second run)
6. ⏳ Document speedup results
7. ⏳ Create BRDs for AD-012, AD-013, AD-014

### Session 3 (Then - 3-4 hours)
8. ⏳ Implement AD-010 (workflow-specific outputs)
9. ⏳ Test all three workflows
10. ⏳ Measure performance improvements

### Session 4 (Finally - 2-3 hours)
11. ⏳ Implement AD-012 (log management)
12. ⏳ Implement AD-013 (test organization)
13. ⏳ Update all documentation

---

## 📊 Success Metrics Dashboard

### AD-014 Multi-Phase Subtitle Workflow
- **Target:** 70-80% faster iterations
- **Current:** Foundation complete, integration in progress
- **Measurement:** Time(run 2) / Time(run 1) < 0.30

### AD-010 Workflow-Specific Outputs
- **Target:** 15-30% performance gain
- **Current:** Not started
- **Measurement:** Time saved by skipping unnecessary stages

### AD-012 Log Management
- **Target:** Zero log files in project root
- **Current:** Not started
- **Measurement:** `find . -maxdepth 1 -name "*.log" | wc -l` = 0

### AD-013 Test Organization
- **Target:** 100% test categorization
- **Current:** Not started
- **Measurement:** All tests in correct category directories

---

## 🔄 Next Immediate Actions

### RIGHT NOW (While Pipeline Runs)
1. **Monitor pipeline completion** (~5 more minutes)
   ```bash
   tail -f out/2025/12/08/rpatel/4/99_pipeline_*.log
   ```

2. **Review this document** - Confirm priorities align with goals

3. **Prepare test media:**
   - Subtitle workflow: `in/Jaane Tu Ya Jaane Na 2008.mp4`
   - Transcribe workflow: `in/Energy Demand in AI.mp4` (currently running)

### AFTER Pipeline Completes
4. **Validate output:**
   ```bash
   # Check transcript
   cat out/2025/12/08/rpatel/4/07_alignment/transcript.txt
   
   # Verify no subtitles generated (transcribe workflow)
   ls out/2025/12/08/rpatel/4/11_subtitle_generation/
   ```

5. **Measure performance:**
   ```bash
   # Extract timing from log
   grep "COMPLETED" out/2025/12/08/rpatel/4/99_pipeline_*.log
   
   # Calculate total time
   head -1 out/2025/12/08/rpatel/4/99_pipeline_*.log  # Start time
   tail -10 out/2025/12/08/rpatel/4/99_pipeline_*.log  # End time
   ```

6. **Start cache integration:**
   ```bash
   # Edit run-pipeline.py to add MediaCacheManager
   code run-pipeline.py
   ```

---

## 📚 Reference Documents

### Implementation Status
- `ARCHITECTURE.md` - All 14 ADs documented
- `DEVELOPER_STANDARDS.md` - Complete coding standards
- `AD014_WEEK1_DAY12_COMPLETE.md` - Foundation complete

### Active Work
- Job directory: `out/2025/12/08/rpatel/4/`
- Pipeline log: `99_pipeline_20251208_082631.log`
- Current stage: `06_asr/`

### Test Media
- English: `in/Energy Demand in AI.mp4` (12.4 min)
- Hinglish: `in/Jaane Tu Ya Jaane Na 2008.mp4` (2.5 hours)

---

## ❓ Questions for Clarification

1. **BRD/TRD Priority:** Should we create all BRDs/TRDs first, or create them as we implement each AD?

2. **Documentation Consolidation:** Should BRDs/TRDs be separate files or sections within existing docs?

3. **Testing Scope:** For AD-014 validation, should we test both movies or just the shorter test clip?

4. **Framework Enforcement:** Should we add pre-commit hooks to enforce BRD/TRD existence before code PRs?

---

**Last Updated:** 2025-12-08 15:10 UTC  
**Next Review:** After pipeline completion (~5-10 minutes)
