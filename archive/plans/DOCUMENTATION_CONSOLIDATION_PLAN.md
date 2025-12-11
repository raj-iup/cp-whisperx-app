# Documentation Consolidation Plan

**Created:** 2025-12-06  
**Status:** ⏳ PENDING APPROVAL  
**Priority:** 🔴 HIGH (90 markdown files in project root)  
**Estimated Effort:** 6-8 hours  
**Target:** Clean project root, organized docs/ structure

---

## Executive Summary

**Problem:** 90 markdown files in project root + scattered documentation in docs/

**Impact:**
- Difficult navigation and discovery
- Redundant/outdated content
- No clear documentation hierarchy
- Poor user experience

**Solution:** Consolidate, archive, and restructure documentation

**Expected Outcome:**
- ≤10 markdown files in project root (essential only)
- Clear docs/ hierarchy with single source of truth
- All historical documents archived
- 100% up-to-date documentation

---

## Current State Analysis

### Project Root (90 files)

**Category Breakdown:**

| Category | Count | Action |
|----------|-------|--------|
| **Essential (Keep)** | 6 | Maintain in root |
| **Completion Reports** | 25 | Archive to archive/completion-reports/ |
| **Test Reports** | 12 | Archive to archive/test-reports/ |
| **Session Documents** | 0 | Already archived ✅ |
| **AD Documentation** | 11 | Consolidate + archive |
| **Phase Reports** | 5 | Archive to archive/phase-reports/ |
| **Implementation Plans** | 8 | Archive to archive/plans/ |
| **Fix/Bug Reports** | 10 | Archive to archive/fixes/ |
| **Status Reports** | 6 | Archive to archive/status/ |
| **Duplicates/Outdated** | 7 | Delete or consolidate |

### Docs Directory (52 files)

**Structure Analysis:**

```
docs/
├── developer/          (4 files)  ✅ Keep (essential)
├── user-guide/         (7 files)  ✅ Keep (essential)
├── stages/             (2 files)  ⚠️  Incomplete
├── technical/          (8 files)  ✅ Keep (essential)
├── logging/            (1 file)   ✅ Keep
├── phase3/             (6 files)  📦 Archive (historical)
├── phase4/             (1 file)   📦 Archive (historical)
├── summaries/          (9 files)  📦 Archive or consolidate
└── root files          (14 files) ⚠️  Review/consolidate
```

---

## Target Structure

### Project Root (≤10 files)

```
cp-whisperx-app/
├── README.md                           # ✅ Project overview
├── ARCHITECTURE.md                     # ✅ Authoritative architecture
├── IMPLEMENTATION_TRACKER.md           # ✅ Current progress
├── CANONICAL_PIPELINE.md               # ✅ Pipeline reference
├── TROUBLESHOOTING.md                  # ✅ User troubleshooting
├── LICENSE                             # ✅ Legal
├── Makefile                            # ✅ Build automation
├── pytest.ini                          # ✅ Test config
└── (scripts, config, etc.)             # Directories only
```

### Docs Directory (Organized)

```
docs/
├── README.md                           # Documentation index
├── INDEX.md                            # Navigation guide
│
├── developer/                          # Developer documentation
│   ├── DEVELOPER_STANDARDS.md          # ✅ Authoritative standards
│   ├── getting-started.md              # ✅ Onboarding
│   ├── contributing.md                 # ✅ Contribution guide
│   └── MIGRATION_GUIDE.md              # ✅ Migration help
│
├── user-guide/                         # User documentation
│   ├── README.md                       # User guide index
│   ├── workflows.md                    # ✅ Workflow guide
│   ├── configuration.md                # ✅ Config reference
│   ├── troubleshooting.md              # ✅ User troubleshooting
│   ├── prepare-job.md                  # ✅ Job preparation
│   ├── glossary-builder.md             # ✅ Glossary guide
│   └── BOOTSTRAP.md                    # ✅ Setup guide
│
├── technical/                          # Technical documentation
│   ├── README.md                       # Technical index
│   ├── architecture.md                 # ✅ System architecture
│   ├── pipeline.md                     # ✅ Pipeline details
│   ├── multi-environment.md            # ✅ Environment setup
│   ├── language-support.md             # ✅ Language features
│   ├── caching-ml-optimization.md      # ✅ Optimization
│   └── debug-logging.md                # ✅ Debugging
│
├── stages/                             # Stage documentation
│   ├── README.md                       # Stage index
│   ├── 01_demux.md                     # NEW: Stage 01 guide
│   ├── 02_tmdb.md                      # ✅ TMDB integration
│   ├── ...                             # NEW: All 12 stages
│   └── 12_mux.md                       # NEW: Stage 12 guide
│
├── decisions/                          # NEW: Architectural decisions
│   ├── README.md                       # AD index
│   ├── AD-001_12-stage-architecture.md # Extracted from ARCHITECTURE.md
│   ├── AD-002_asr-modularization.md
│   ├── AD-003_translation-stage.md
│   ├── AD-004_venv-structure.md
│   ├── AD-005_hybrid-mlx-backend.md
│   ├── AD-006_job-parameters.md
│   ├── AD-007_shared-imports.md
│   ├── AD-008_hybrid-alignment.md
│   ├── AD-009_quality-first.md
│   └── AD-010_workflow-outputs.md
│
├── testing/                            # NEW: Testing documentation
│   ├── README.md                       # Testing index
│   ├── test-media.md                   # Standard test media
│   ├── e2e-testing.md                  # E2E test guide
│   ├── unit-testing.md                 # Unit test guide
│   └── quality-baselines.md            # Quality metrics
│
├── guides/                             # NEW: How-to guides
│   ├── README.md                       # Guides index
│   ├── context-aware-subtitles.md      # Context-aware guide
│   ├── hybrid-translation.md           # Hybrid translator
│   └── model-routing.md                # AI model routing
│
├── reference/                          # NEW: Reference documentation
│   ├── README.md                       # Reference index
│   ├── code-examples.md                # ✅ Code examples
│   ├── ai-model-routing.md             # ✅ Model routing
│   ├── quality-baselines.md            # ✅ Quality metrics
│   └── pre-commit-hook.md              # ✅ Hook guide
│
└── (legacy directories removed)
    phase3/                             # ❌ Archive
    phase4/                             # ❌ Archive
    summaries/                          # ❌ Archive
```

### Archive Directory (Historical)

```
archive/
├── completion-reports/                 # 25 completion documents
├── test-reports/                       # 12 test reports
├── phase-reports/                      # 5 phase reports
├── plans/                              # 8 implementation plans
├── fixes/                              # 10 fix reports
├── status/                             # 6 status updates
├── ad-documents/                       # 11 AD-specific docs
├── phase3/                             # ✅ Already exists
├── phase4/                             # From docs/phase4/
├── summaries/                          # From docs/summaries/
├── sessions/                           # ✅ Already exists
├── architecture/                       # ✅ Already exists
└── implementation-tracker/             # ✅ Already exists
```

---

## Implementation Phases

### Phase 1: Analysis & Planning (1 hour)

**Tasks:**
1. Categorize all 90 root markdown files
2. Identify duplicates and redundancies
3. Create mapping of content to target locations
4. Identify essential vs archivable content
5. Create consolidation script

**Deliverables:**
- File categorization spreadsheet
- Consolidation mapping document
- Archive strategy

---

### Phase 2: Essential Documentation Update (2 hours)

**Priority:** 🔴 HIGH

**Tasks:**
1. **Update README.md (30 min)**
   - Project overview
   - Quick start guide
   - Link to documentation
   - Status badges

2. **Verify ARCHITECTURE.md (15 min)**
   - Ensure all 10 ADs documented
   - Update version history
   - Add navigation links

3. **Update TROUBLESHOOTING.md (30 min)**
   - Consolidate troubleshooting content from scattered docs
   - Add common issues from test reports
   - Add debugging workflows

4. **Create docs/INDEX.md (30 min)**
   - Complete documentation navigation
   - Category-based organization
   - Search-friendly structure

5. **Update IMPLEMENTATION_TRACKER.md (15 min)**
   - Add consolidation task tracking
   - Update documentation status

**Deliverables:**
- Updated essential docs
- Clear documentation index

---

### Phase 3: Archive Historical Documents (1.5 hours)

**Priority:** 🔴 HIGH

**Tasks:**

1. **Completion Reports (25 files → archive/completion-reports/)**
   ```
   - AD-006_IMPLEMENTATION_COMPLETE.md
   - AD-010_IMPLEMENTATION_COMPLETE.md
   - ASR_PHASE*_COMPLETION_SUMMARY.md
   - HYBRID_ARCHITECTURE_IMPLEMENTATION_COMPLETE.md
   - IMPLEMENTATION_COMPLETE_2025-12-04.md
   - PHASE*_COMPLETION_REPORT.md
   - SUBTITLE_WORKFLOW_INTEGRATION_COMPLETION_REPORT.md
   - TEST*_FINAL_VALIDATION.md
   - *_COMPLETE*.md
   ```

2. **Test Reports (12 files → archive/test-reports/)**
   ```
   - E2E_TEST_*.md
   - TEST_*.md
   - test1_summary.md
   ```

3. **AD Documentation (11 files → archive/ad-documents/)**
   ```
   - AD-006_*.md (except ARCHITECTURE.md)
   - AD-009_*.md
   - AD-010_*.md
   - BUG_004_AD-007_SUMMARY.md
   ```

4. **Phase Reports (5 files → archive/phase-reports/)**
   ```
   - PHASE*_COMPLETION_SUMMARY.md
   - PHASE*_FINAL_REPORT.md
   ```

5. **Plans (8 files → archive/plans/)**
   ```
   - ASR_MODULARIZATION_PLAN.md
   - ASR_STAGE_REFACTORING_PLAN.md
   - DOCUMENTATION_MAINTENANCE_PLAN.md
   - E2E_TEST_EXECUTION_PLAN.md
   - SUBTITLE_WORKFLOW_INTEGRATION_PLAN.md
   - TASK_10_OUTPUT_DIRECTORY_CLEANUP_PLAN.md
   - TRANSLATION_STAGE_REFACTORING_PLAN_NUMERIC.md
   ```

6. **Fixes/Bugs (10 files → archive/fixes/)**
   ```
   - ALIGNMENT_LANGUAGE_FIX_COMPLETE.md
   - ASR_TASK_MODE_FIX_COMPLETE.md
   - COMPLIANCE_FIX_SUMMARY_2025-12-04.md
   - DEMUCS_FIX_PROPER.md
   - FILE_NAMING_FIX_SESSION_2025-12-05.md
   - LOG_FIXES_2025-12-05.md
   - SUBTITLE_WORKFLOW_FIXES_SUMMARY.md
   - TEST1_RERUN_SUCCESS.md
   ```

7. **Status Reports (6 files → archive/status/)**
   ```
   - QUICK_STATUS_*.md
   - SYSTEM_STATUS_REPORT.md
   - AUDIT_SUMMARY_2025-12-05.md
   ```

**Script:**
```bash
# Create archive directories
mkdir -p archive/{completion-reports,test-reports,phase-reports,plans,fixes,status,ad-documents}

# Move files (automated script)
./tools/archive-historical-docs.sh
```

**Deliverables:**
- 77 files moved to archive/
- Project root cleaned
- Archive README.md files created

---

### Phase 4: Consolidate Current Documentation (2 hours)

**Priority:** 🟡 MEDIUM

**Tasks:**

1. **Extract AD Documentation (1 hour)**
   - Create docs/decisions/ directory
   - Extract each AD from ARCHITECTURE.md to separate file
   - Add context, rationale, and references
   - Create decisions/README.md index

2. **Create Stage Documentation (30 min)**
   - docs/stages/01_demux.md through 12_mux.md
   - Extract from CANONICAL_PIPELINE.md
   - Add usage examples, inputs/outputs
   - Add troubleshooting per stage

3. **Create Testing Documentation (20 min)**
   - docs/testing/README.md
   - Consolidate TEST_MEDIA_QUICKSTART.md
   - Extract E2E testing guide
   - Add quality baselines

4. **Create Guides (10 min)**
   - docs/guides/README.md
   - Move CONTEXT_AWARE_SUBTITLE_GENERATION.md
   - Move HYBRID_TRANSLATOR_IMPLEMENTATION_SUMMARY.md
   - Create navigation structure

**Deliverables:**
- 10 AD documents in docs/decisions/
- 12 stage guides in docs/stages/
- Complete testing documentation
- User-friendly guides

---

### Phase 5: Clean Up docs/ Directory (1 hour)

**Priority:** 🟡 MEDIUM

**Tasks:**

1. **Archive Phase Documents**
   - docs/phase3/ → archive/phase3/ (merge with existing)
   - docs/phase4/ → archive/phase4/

2. **Archive Summaries**
   - docs/summaries/ → archive/summaries/

3. **Consolidate Root docs/**
   - Review 14 files in docs/ root
   - Move to appropriate subdirectory or archive
   - Keep only essential index/reference docs

4. **Create README.md files**
   - docs/README.md (main index)
   - docs/*/README.md (category indexes)

**Script:**
```bash
# Archive phase docs
mv docs/phase3/* archive/phase3/
mv docs/phase4/* archive/phase4/
rm -rf docs/phase3 docs/phase4

# Archive summaries
mv docs/summaries archive/
```

**Deliverables:**
- Clean docs/ structure
- All historical docs archived
- Clear navigation

---

### Phase 6: Update Documentation Links (30 min)

**Priority:** 🟢 LOW

**Tasks:**
1. Update README.md links
2. Update ARCHITECTURE.md references
3. Update DEVELOPER_STANDARDS.md links
4. Update copilot-instructions.md references
5. Update IMPLEMENTATION_TRACKER.md links

**Validation:**
```bash
# Check for broken links
./tools/validate-markdown-links.sh
```

**Deliverables:**
- All internal links working
- No broken references

---

### Phase 7: Create Archive Indexes (30 min)

**Priority:** 🟢 LOW

**Tasks:**
1. Create archive/README.md (master index)
2. Create archive/*/README.md (category indexes)
3. Add search tips
4. Add timeline references

**Deliverables:**
- Complete archive navigation
- Searchable historical docs

---

## File Mapping Reference

### Essential Files (Keep in Root)

| File | Keep? | Reason |
|------|-------|--------|
| README.md | ✅ Yes | Project overview |
| ARCHITECTURE.md | ✅ Yes | Authoritative architecture (AD-001 to AD-010) |
| IMPLEMENTATION_TRACKER.md | ✅ Yes | Current progress tracking |
| CANONICAL_PIPELINE.md | ✅ Yes | Pipeline reference |
| TROUBLESHOOTING.md | ✅ Yes | User troubleshooting |
| LICENSE | ✅ Yes | Legal requirement |

### Files to Archive

#### Completion Reports (25 files)
- AD-006_IMPLEMENTATION_COMPLETE.md
- AD-006_VALIDATION_COMPLETE.md
- AD-010_IMPLEMENTATION_COMPLETE.md
- ALL_HIGH_PRIORITY_FIXES_COMPLETE_2025-12-05.md
- ASR_PHASE4_COMPLETION_SUMMARY.md
- ASR_PHASE5_COMPLETION_SUMMARY.md
- ASR_PHASE7_COMPLETION_SUMMARY.md
- COMPLIANCE_AUDIT_2025-12-04.md
- DOCUMENTATION_CONSISTENCY_COMPLETE.md
- HIGH_PRIORITY_FIXES_COMPLETE_2025-12-05.md
- HYBRID_ARCHITECTURE_IMPLEMENTATION_COMPLETE.md
- IMPLEMENTATION_COMPLETE_2025-12-04.md
- NEXT_STEPS_COMPLETE_2025-12-05.md
- OPTIONAL_WORK_COMPLETE_2025-12-05.md
- OUTPUT_DIRECTORY_RESTRUCTURE_SUMMARY.md
- PHASE1_COMPLETION_REPORT.md
- PHASE2_COMPLETION_REPORT.md
- PHASE4_COMPLETION_SUMMARY.md
- PHASE4_FINAL_REPORT.md
- SUBTITLE_WORKFLOW_INTEGRATION_COMPLETION_REPORT.md
- TASK_10_OUTPUT_DIRECTORY_CLEANUP_COMPLETE.md
- TEST_1_FINAL_VALIDATION.md
- TEST_2_FINAL_VALIDATION.md
- TEST_3_SUBTITLE_WORKFLOW_SUCCESS.md
- M-001_COMPLETION_SUMMARY.md

#### Test Reports (12 files)
- E2E_TEST_ANALYSIS_2025-12-05.md
- E2E_TEST_EXECUTION_PLAN.md
- E2E_TEST_SESSION_2025-12-05.md
- E2E_TEST_SUCCESS_2025-12-05.md
- E2E_TESTING_SESSION_2025-12-04.md
- JOB_13_FAILURE_ANALYSIS.md
- TEST_2A_SPANISH_TRANSLATION_SUMMARY.md
- TEST_2_ANALYSIS_2025-12-05.md
- TEST_2_EXECUTION_SUMMARY_2025-12-05.md
- TEST_3_SUBTITLE_WORKFLOW_SUMMARY.md
- TEST1_RERUN_SUCCESS.md
- test1_summary.md

#### AD Documentation (11 files)
- AD-006_IMPLEMENTATION_GUIDE.md
- AD-006_IMPLEMENTATION_SESSION_2025-12-04.md
- AD-006_IMPLEMENTATION_SUMMARY.md
- AD-006_PRECOMMIT_HOOK_COMPLETE.md
- AD-006_PROGRESS_REPORT_2025-12-04.md
- AD-009_DEVELOPMENT_PHILOSOPHY.md
- AD-009_DOCUMENTATION_UPDATE.md
- BUG_004_AD-007_SUMMARY.md
- M-001_ALIGNMENT_AUDIT_2025-12-06.md

#### Phase Reports (5 files)
- IMPLEMENTATION_SESSION_FINAL_2025-12-04.md
- ASR_MODULARIZATION_SESSION_2025-12-05.md
- FILE_NAMING_FIX_SESSION_2025-12-05.md

#### Plans (8 files)
- ASR_MODULARIZATION_PLAN.md
- ASR_STAGE_REFACTORING_PLAN.md
- DOCUMENTATION_MAINTENANCE_PLAN.md
- SUBTITLE_WORKFLOW_INTEGRATION_PLAN.md
- TASK_10_OUTPUT_DIRECTORY_CLEANUP_PLAN.md
- TRANSLATION_STAGE_REFACTORING_PLAN_NUMERIC.md

#### Fixes (10 files)
- ALIGNMENT_LANGUAGE_FIX_COMPLETE.md
- ASR_TASK_MODE_FIX_COMPLETE.md
- COMPLIANCE_FIX_SUMMARY_2025-12-04.md
- DEMUCS_FIX_PROPER.md
- FILE_NAMING_FIX_SESSION_2025-12-05.md
- LOG_FIXES_2025-12-05.md
- SUBTITLE_WORKFLOW_FIXES_SUMMARY.md

#### Status (6 files)
- AUDIT_SUMMARY_2025-12-05.md
- QUICK_STATUS_2025-12-04.md
- QUICK_STATUS_UPDATE_2025-12-04.md
- SYSTEM_STATUS_REPORT.md

#### Analysis/Strategy (8 files)
- BACKEND_INVESTIGATION.md
- CODEBASE_AUDIT_2025-12-05.md
- DOCUMENTATION_ALIGNMENT_ANALYSIS.md
- DOCUMENTATION_ALIGNMENT_SUMMARY.md
- DOCUMENTATION_FIX_PROGRESS.md
- DOCUMENTATION_INCONSISTENCY_ANALYSIS.md
- DOCUMENTATION_STRATEGY.md
- DOCUMENTATION_UPDATES_SUMMARY_2025-12-05.md

### Files to Consolidate/Extract

#### Extract to docs/guides/
- CONTEXT_AWARE_SUBTITLE_GENERATION.md → docs/guides/context-aware-subtitles.md
- HYBRID_TRANSLATOR_IMPLEMENTATION_SUMMARY.md → docs/guides/hybrid-translation.md
- TRANSLATION_QUALITY_ISSUES.md → docs/guides/translation-quality.md

#### Extract to docs/decisions/
- Extract all 10 ADs from ARCHITECTURE.md to separate files

#### Extract to docs/testing/
- TEST_MEDIA_QUICKSTART.md → docs/testing/test-media.md

#### Extract to docs/reference/
- MLX_ARCHITECTURE_DECISION.md → docs/decisions/AD-005_hybrid-mlx-backend.md
- FINAL_OUTPUT_LOCATIONS.md → Consolidate into docs/user-guide/workflows.md

#### Keep as Reference
- NUMERIC_STAGE_ARCHITECTURE.md → docs/technical/numeric-stages.md
- STAGE_COMPLEXITY_ANALYSIS.md → archive/analysis/

---

## Scripts to Create

### 1. archive-historical-docs.sh
```bash
#!/bin/bash
# Archive historical documentation
# Usage: ./tools/archive-historical-docs.sh

set -e

echo "📦 Archiving historical documentation..."

# Create archive directories
mkdir -p archive/{completion-reports,test-reports,phase-reports,plans,fixes,status,ad-documents,analysis}

# Move completion reports (25 files)
mv AD-006_IMPLEMENTATION_COMPLETE.md archive/completion-reports/ 2>/dev/null || true
mv AD-010_IMPLEMENTATION_COMPLETE.md archive/completion-reports/ 2>/dev/null || true
# ... (all completion reports)

# Move test reports (12 files)
mv E2E_TEST_*.md archive/test-reports/ 2>/dev/null || true
mv TEST_*.md archive/test-reports/ 2>/dev/null || true
# ... (all test reports)

# Create README files
./tools/create-archive-readme.sh

echo "✅ Archiving complete"
```

### 2. create-archive-readme.sh
```bash
#!/bin/bash
# Create README.md files for archive directories

for dir in archive/*/; do
  cat > "$dir/README.md" << EOF
# $(basename $dir | tr '-' ' ' | sed 's/.*/\u&/')

Archived documentation from CP-WhisperX project.

**Archive Date:** $(date +%Y-%m-%d)  
**Category:** $(basename $dir)

## Files

$(ls -1 $dir/*.md 2>/dev/null | grep -v README | sed 's/^/- /')

---

**Note:** These are historical documents. For current documentation, see the main docs/ directory.
EOF
done
```

### 3. validate-markdown-links.sh
```bash
#!/bin/bash
# Validate all markdown links
# Check for broken internal references

echo "🔍 Validating markdown links..."

find . -name "*.md" -not -path "./archive/*" -not -path "./venv/*" | while read file; do
  # Extract markdown links
  grep -oP '\[.*?\]\(\K[^)]+' "$file" | while read link; do
    # Check if internal link exists
    if [[ $link != http* ]]; then
      target="${file%/*}/$link"
      if [ ! -f "$target" ]; then
        echo "❌ Broken link in $file: $link"
      fi
    fi
  done
done

echo "✅ Link validation complete"
```

---

## Success Criteria

### Phase Completion
- [ ] Phase 1: Analysis complete, mapping created
- [ ] Phase 2: Essential docs updated
- [ ] Phase 3: 77 files archived
- [ ] Phase 4: New docs structure created
- [ ] Phase 5: docs/ directory cleaned
- [ ] Phase 6: All links updated and validated
- [ ] Phase 7: Archive indexes created

### Quality Metrics
- [ ] Project root: ≤10 markdown files
- [ ] docs/: Clear category structure
- [ ] Archive: All historical docs preserved
- [ ] Links: 100% working internal links
- [ ] Navigation: Clear documentation index
- [ ] Compliance: No redundant content
- [ ] Currency: All docs reflect current state

### Documentation Quality
- [ ] Single source of truth per topic
- [ ] No duplicate content
- [ ] Clear navigation paths
- [ ] Up-to-date references
- [ ] Complete archive indexes
- [ ] Searchable structure

---

## Risk Mitigation

### Risks

1. **Risk:** Accidentally delete important documentation
   - **Mitigation:** Archive first, never delete
   - **Recovery:** Git history preserves everything

2. **Risk:** Broken links after reorganization
   - **Mitigation:** Automated link validation
   - **Recovery:** Find-replace with correct paths

3. **Risk:** Lost historical context
   - **Mitigation:** Comprehensive archive with indexes
   - **Recovery:** Archive README.md provides navigation

4. **Risk:** Time overrun
   - **Mitigation:** Phased approach, can pause between phases
   - **Recovery:** Continue in next session

---

## Timeline

| Phase | Duration | Start | End | Priority |
|-------|----------|-------|-----|----------|
| Phase 1: Analysis | 1 hour | TBD | TBD | 🔴 HIGH |
| Phase 2: Essential Docs | 2 hours | TBD | TBD | 🔴 HIGH |
| Phase 3: Archive | 1.5 hours | TBD | TBD | 🔴 HIGH |
| Phase 4: Consolidate | 2 hours | TBD | TBD | 🟡 MEDIUM |
| Phase 5: Clean docs/ | 1 hour | TBD | TBD | 🟡 MEDIUM |
| Phase 6: Update Links | 30 min | TBD | TBD | 🟢 LOW |
| Phase 7: Archive Index | 30 min | TBD | TBD | 🟢 LOW |
| **Total** | **8.5 hours** | - | - | - |

**Recommendation:** Execute in 2-3 sessions
- Session 1: Phases 1-3 (4.5 hours) - Core cleanup
- Session 2: Phases 4-5 (3 hours) - Consolidation
- Session 3: Phases 6-7 (1 hour) - Finalization

---

## Approval Required

**Decision Points:**
1. ✅ Approve overall structure?
2. ✅ Approve file categorization?
3. ✅ Approve archiving strategy?
4. ✅ Approve timeline?

**To Proceed:**
- [ ] Review this plan
- [ ] Approve or request changes
- [ ] Schedule execution sessions
- [ ] Execute phases in order

---

**Plan Created:** 2025-12-06  
**Last Updated:** 2025-12-06  
**Status:** ⏳ Awaiting Approval  
**Next Step:** User approval → Begin Phase 1
