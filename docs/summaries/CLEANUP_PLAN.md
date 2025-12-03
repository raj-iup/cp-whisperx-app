# Repository Cleanup Plan

**Date:** December 3, 2025  
**Purpose:** Remove redundant code/docs, rebuild documentation aligned with ARCHITECTURE_IMPLEMENTATION_ROADMAP.md  
**Status:** 🔴 DRAFT - Review before execution

---

## 📊 Current State Analysis

### Root Level Markdown Files (48 files)
**Redundant/Historical (36 files to remove):**
- ✅ Keep: README.md, LICENSE, Makefile
- ✅ Keep: TEST_MEDIA_QUICKSTART.md, ARCHITECTURE_UPDATE_SUMMARY.md
- ❌ Remove: All PHASE*_COMPLETION*.md (12 files) - Historical, not needed
- ❌ Remove: All COMPLIANCE_*.md (11 files) - Redundant with current docs
- ❌ Remove: All 100_PERCENT_*.md (2 files) - Historical achievement docs
- ❌ Remove: COMPLETE_*.md (3 files) - Redundant completion reports
- ❌ Remove: IMPLEMENTATION_SESSION_SUMMARY.txt - Historical
- ❌ Remove: PRIORITIZED_ACTION_PLAN_STATUS.md, QUICK_REFERENCE.md - Outdated
- ❌ Remove: TMDB_INTEGRATION_STATUS.md - Covered in architecture docs

### Documentation Directory (37 files + subdirs)
**Keep (Core Architecture - 8 files):**
- ✅ ARCHITECTURE_IMPLEMENTATION_ROADMAP.md (v3.0 - THE MASTER)
- ✅ AI_MODEL_ROUTING.md
- ✅ CODE_EXAMPLES.md
- ✅ SUBTITLE_ACCURACY_ROADMAP.md
- ✅ PRE_COMMIT_HOOK_GUIDE.md
- ✅ README.md
- ✅ INDEX.md (update to reflect new structure)
- ✅ developer/DEVELOPER_STANDARDS.md (v5.0)

**Remove (Redundant - 29+ files):**
- ❌ ARCHITECTURE_IMPLEMENTATION_ROADMAP.md.backup (2 backups)
- ❌ All PHASE_*_COMPLETION.md (6 files) - Historical
- ❌ All PHASE*_IMPLEMENTATION_PROGRESS.md - Historical
- ❌ ARCHITECTURE_*_ANALYSIS.md (3 files) - Analysis done, not needed
- ❌ ARCHITECTURE_IMPROVEMENTS_COMPLETE.md - Historical
- ❌ COPILOT_INTEGRATION_PLAN.md - Completed, covered in standards
- ❌ BASELINE_COMPLIANCE_METRICS.md - Historical baseline
- ❌ CODEBASE_REVIEW_COMPLIANCE_REPORT.md - Point-in-time, outdated
- ❌ PROJECT_COMPLETE.md - Historical
- ❌ IMPLEMENTATION_STATUS.md - Covered in roadmap
- ❌ TASK_4_1_COMPLETION.md - Historical task
- ❌ QUICKSTART.md, developer-guide.md - Rebuild from scratch
- ❌ CONTRIBUTING.md - Rebuild focused on core workflows
- ❌ optimization-roadmap.md - Covered in architecture roadmap

**Subdirectories to Remove:**
- ❌ docs/archive/ - Historical documents
- ❌ docs/archives/ - Historical documents  
- ❌ docs/implementation/ - Historical implementation notes
- ❌ docs/logging/ - May keep if still relevant, review
- ❌ docs/planning/ - Historical planning
- ❌ docs/reference/ - Historical reference

**Subdirectories to Keep/Rebuild:**
- ✅ docs/developer/ - Keep DEVELOPER_STANDARDS.md, rebuild others

### Scripts Directory (43 Python files)

**Core Stage Scripts (Keep - 10 files):**
According to roadmap, we need 10 stages:
- ✅ 01_demux.py (rename from demux.py)
- ✅ 02_tmdb_enrichment.py (rename from tmdb_enrichment_stage.py)
- ✅ 03_glossary_loader.py (rename from glossary_builder.py)
- ✅ 04_source_separation.py (keep)
- ✅ 05_pyannote_vad.py (keep)
- ✅ 06_whisperx_asr.py (keep)
- ✅ 07_mlx_alignment.py (keep, or create if missing)
- ✅ 08_indictrans2_translation.py (rename from indictrans2_translator.py)
- ✅ 09_subtitle_generation.py (create from subtitle_gen.py)
- ✅ 10_mux.py (keep)

**Core Utility Scripts (Keep - 5 files):**
- ✅ prepare-job.py
- ✅ run-pipeline.py
- ✅ config_loader.py
- ✅ validate-compliance.py
- ✅ device_selector.py

**Backend/Support Scripts (Keep - 5 files):**
- ✅ whisperx_integration.py
- ✅ whisper_backends.py
- ✅ nllb_translator.py (NLLB fallback)
- ✅ filename_parser.py
- ✅ fetch_tmdb_metadata.py

**Remove (Redundant/Legacy - 23 files):**
- ❌ asr_chunker.py - Functionality should be in 06_whisperx_asr.py
- ❌ bias_injection.py, bias_injection_core.py - Not in core design
- ❌ canonicalization.py - Should be part of stages
- ❌ export_transcript.py - Should be part of workflow output
- ❌ glossary_applier.py - Functionality in stage
- ❌ glossary_protected_translator.py - Legacy, use stage pattern
- ❌ hallucination_removal.py - Not integrated, remove for now
- ❌ hybrid_subtitle_merger.py - Legacy
- ❌ hybrid_translator.py - Use stage-based routing
- ❌ lyrics_detection.py, lyrics_detection_core.py, lyrics_detector.py - Redundant copies
- ❌ mlx_alignment.py - May need to rename to 07_alignment.py
- ❌ name_entity_correction.py - Legacy
- ❌ ner_extraction.py, ner_post_processor.py - Not integrated
- ❌ post_ner.py, pre_ner.py - Not in core design
- ❌ subtitle_segment_merger.py - Legacy
- ❌ tmdb.py - Use tmdb_enrichment_stage.py instead
- ❌ translation.py, translation_refine.py, translation_validator.py - Legacy
- ❌ metrics/ subdirectory - Not in core design yet

### Shared Directory (27 Python files)

**Core Shared Modules (Keep - 10 files):**
- ✅ __init__.py
- ✅ logger.py
- ✅ config.py
- ✅ stage_utils.py (StageIO pattern)
- ✅ stage_order.py
- ✅ environment_manager.py
- ✅ job_manager.py
- ✅ tmdb_client.py
- ✅ glossary_manager.py
- ✅ audio_utils.py

**Consider Keeping (Review - 7 files):**
- ⚠️ stage_dependencies.py - Needed for Phase 4
- ⚠️ manifest.py - Core to StageIO
- ⚠️ model_checker.py - May be useful
- ⚠️ model_downloader.py - May be useful
- ⚠️ hardware_detection.py - Used by device selector
- ⚠️ utils.py - Check if still used
- ⚠️ tmdb_cache.py, musicbrainz_cache.py - Caching infrastructure

**Remove (Redundant - 10 files):**
- ❌ glossary_unified.py, glossary_integration.py, glossary_advanced.py, glossary_ml.py, glossary_cache.py - Consolidate into glossary_manager.py
- ❌ bias_registry.py - Not in core design
- ❌ ner_corrector.py - Not in core design
- ❌ tmdb_loader.py - Use tmdb_client.py

---

## 🗑️ Files to Remove

### Root Level (36 files)
```bash
# Historical completion reports
rm 100_PERCENT_COMPLIANCE_ACHIEVEMENT.md
rm 100_PERCENT_COMPLIANCE_PLAN.md
rm COMPLETE_IMPLEMENTATION_SUMMARY.md
rm COMPLETE_SUCCESS_REPORT.md
rm ARCHITECTURE_UPDATE_COMPLETE.md
rm IMPLEMENTATION_SESSION_SUMMARY.txt

# Compliance reports (covered in current docs)
rm COMPLIANCE_FILE_CHECKLIST.md
rm COMPLIANCE_INDEX.md
rm COMPLIANCE_REPORT.md
rm COMPLIANCE_REPORTS_README.md
rm COMPLIANCE_REPORT_DETAILED.md
rm COMPLIANCE_ROADMAP.md
rm COMPLIANCE_SUMMARY.md
rm CORE_TASKS_COMPLIANCE_REPORT.md
rm FINAL_COMPLIANCE_ACHIEVEMENT.md
rm FINAL_COMPLIANCE_STATUS.md

# Phase completion reports (historical)
rm PHASE1B_COMPLETION_REPORT.md
rm PHASE1_COMPLETION_REPORT.md
rm PHASE1_VALIDATOR_COMPLETION_REPORT.md
rm PHASE2_COMPLETION_REPORT.md
rm PHASE2_COMPLETION_STATUS.md
rm PHASE2_FILE_INDEX.md
rm PHASE2_IMPLEMENTATION_SUMMARY.md
rm PHASE2_QUICKSTART.md
rm PHASE2_SUMMARY.md
rm PHASE2_TESTING_COMPLETION_REPORT.md
rm PHASE3_COMPLETION_REPORT.md
rm PHASE4_AND_PHASE5_STATUS_REPORT.md
rm PHASE4_COMPLETION_FINAL.md
rm PHASE4_COMPLETION_REPORT.md
rm PHASE4_COMPLETION_STATUS.md
rm PHASE4_COMPLIANCE_VERIFICATION.md
rm PHASE4_CROSS_PLATFORM_COMPLETE.md
rm PHASE4_FILES_INDEX.md
rm PHASE4_FINAL_COMPLETION_REPORT.md
rm PHASE4_FULL_PIPELINE_IMPLEMENTATION.md
rm PHASE4_IMPLEMENTATION_PROGRESS.md
rm PHASE4_IMPLEMENTATION_SUMMARY.md
rm PHASE4_LEGACY_WRAPPERS_COMPLETE.md
rm PHASE4_QUICK_START.md
rm PHASE4_README.md
rm PHASE4_STATUS_AND_ROADMAP.md
rm PHASE5_IMPLEMENTATION_ROADMAP.md
rm PHASE5_IMPLEMENTATION_ROADMAP.md.old

# Outdated status/reference docs
rm PRIORITIZED_ACTION_PLAN_STATUS.md
rm QUICK_REFERENCE.md
rm TMDB_INTEGRATION_STATUS.md
```

### Documentation Directory (29+ files)
```bash
cd docs/

# Backups
rm ARCHITECTURE_IMPLEMENTATION_ROADMAP.md.backup
rm ARCHITECTURE_IMPLEMENTATION_ROADMAP.md.v2.0.backup

# Historical analysis
rm ARCHITECTURE_ANALYSIS_EXECUTIVE_SUMMARY.md
rm ARCHITECTURE_GAP_ANALYSIS.md
rm ARCHITECTURE_GAP_QUICK_REF.md
rm ARCHITECTURE_IMPROVEMENTS_COMPLETE.md
rm ARCHITECTURE_IMPROVEMENT_REPORT.md

# Historical metrics/reports
rm BASELINE_COMPLIANCE_METRICS.md
rm CODEBASE_REVIEW_COMPLIANCE_REPORT.md
rm COMPLIANCE_REPORT.md
rm PROJECT_COMPLETE.md
rm TASK_4_1_COMPLETION.md
rm IMPLEMENTATION_STATUS.md

# Phase completion docs
rm PHASE1_DOCUMENTATION_SYNC_COMPLETE.md
rm PHASE3_IMPLEMENTATION_PROGRESS.md
rm PHASE3_QUICKSTART.md
rm PHASE_0_COPILOT_TEST_GUIDE.md
rm PHASE_0_PROGRESS.md
rm PHASE_1_COMPLETION.md
rm PHASE_1_VALIDATION_TESTS.md
rm PHASE_2_COMPLETION.md
rm PHASE_3_COMPLETION.md
rm PHASE_4_COMPLETION.md
rm PHASE_5_COMPLETION.md
rm PHASE_6_COMPLETION.md

# Outdated guides (will rebuild)
rm QUICKSTART.md
rm developer-guide.md
rm CONTRIBUTING.md
rm optimization-roadmap.md
rm COPILOT_INTEGRATION_PLAN.md

# Historical directories
rm -rf archive/
rm -rf archives/
rm -rf implementation/
rm -rf planning/
rm -rf reference/
```

### Scripts Directory (23 files)
```bash
cd scripts/

# Redundant/legacy scripts
rm asr_chunker.py
rm bias_injection.py
rm bias_injection_core.py
rm canonicalization.py
rm export_transcript.py
rm glossary_applier.py
rm glossary_protected_translator.py
rm hallucination_removal.py
rm hybrid_subtitle_merger.py
rm hybrid_translator.py
rm lyrics_detection.py
rm lyrics_detection_core.py
rm lyrics_detector.py
rm name_entity_correction.py
rm ner_extraction.py
rm ner_post_processor.py
rm post_ner.py
rm pre_ner.py
rm subtitle_segment_merger.py
rm tmdb.py
rm translation.py
rm translation_refine.py
rm translation_validator.py
rm -rf metrics/
```

### Shared Directory (10 files)
```bash
cd shared/

# Redundant glossary modules
rm glossary_unified.py
rm glossary_integration.py
rm glossary_advanced.py
rm glossary_ml.py
rm glossary_cache.py

# Not in core design
rm bias_registry.py
rm ner_corrector.py
rm tmdb_loader.py

# Decide after review
# rm musicbrainz_cache.py (if not used)
# rm tmdb_cache.py (needed for Phase 5 caching)
```

---

## 📝 Documentation to Rebuild

### Root Level (Keep Clean)
```
README.md                          ✅ Rebuild - Project overview
LICENSE                            ✅ Keep
Makefile                          ✅ Keep/Update
TEST_MEDIA_QUICKSTART.md          ✅ Keep (just created)
ARCHITECTURE_UPDATE_SUMMARY.md    ✅ Keep (just created)
CHANGELOG.md                      🆕 Create - Version history
```

### docs/ Directory (New Structure)
```
docs/
├── README.md                                    🆕 Documentation index
├── ARCHITECTURE_IMPLEMENTATION_ROADMAP.md      ✅ Keep (master plan)
├── AI_MODEL_ROUTING.md                         ✅ Keep
├── CODE_EXAMPLES.md                            ✅ Keep
├── SUBTITLE_ACCURACY_ROADMAP.md                ✅ Keep
├── PRE_COMMIT_HOOK_GUIDE.md                    ✅ Keep
├── INDEX.md                                    ✅ Update
│
├── guides/                                     🆕 User guides
│   ├── QUICKSTART.md                          🆕 Rebuild - Getting started
│   ├── INSTALLATION.md                        🆕 Create - Setup guide
│   ├── WORKFLOWS.md                           🆕 Create - Using 3 workflows
│   ├── TESTING.md                             🆕 Create - Running tests
│   └── TROUBLESHOOTING.md                     🆕 Create - Common issues
│
├── developer/                                  ✅ Developer documentation
│   ├── DEVELOPER_STANDARDS.md                 ✅ Keep (v5.0)
│   ├── CONTRIBUTING.md                        🆕 Rebuild - How to contribute
│   ├── ARCHITECTURE.md                        🆕 Create - System design
│   ├── STAGE_DEVELOPMENT.md                   🆕 Create - Writing stages
│   ├── TESTING_GUIDE.md                       🆕 Create - Writing tests
│   └── API_REFERENCE.md                       🆕 Create - Code APIs
│
├── workflows/                                  🆕 Workflow documentation
│   ├── SUBTITLE_WORKFLOW.md                   🆕 Create - Detailed subtitle guide
│   ├── TRANSCRIBE_WORKFLOW.md                 🆕 Create - Detailed transcribe guide
│   └── TRANSLATE_WORKFLOW.md                  🆕 Create - Detailed translate guide
│
└── technical/                                  🆕 Technical specs
    ├── CACHING_STRATEGY.md                    🆕 Create - Caching implementation
    ├── ML_OPTIMIZATION.md                     🆕 Create - ML features
    ├── CONTEXT_AWARENESS.md                   🆕 Create - Context features
    └── STAGE_SPECIFICATIONS.md                🆕 Create - Each stage spec
```

---

## 🔄 File Renaming (Stage Scripts)

### Phase 1: File Naming (Required for compliance)
```bash
# Rename stage scripts to {NN}_{stage_name}.py pattern
cd scripts/

git mv demux.py 01_demux.py
git mv tmdb_enrichment_stage.py 02_tmdb_enrichment.py
git mv glossary_builder.py 03_glossary_loader.py
# 04_source_separation.py already correct
# 05_pyannote_vad.py already correct
# 06_whisperx_asr.py already correct
git mv mlx_alignment.py 07_alignment.py
git mv indictrans2_translator.py 08_translation.py
git mv subtitle_gen.py 09_subtitle_generation.py
# 10_mux.py already correct
```

---

## ✅ Execution Plan

### Step 1: Backup
```bash
# Create full backup before cleanup
cd /Users/rpatel/Projects/Active
tar -czf cp-whisperx-app-backup-$(date +%Y%m%d-%H%M%S).tar.gz cp-whisperx-app/
```

### Step 2: Remove Root Level Files
Execute removal of 36 root-level markdown files

### Step 3: Clean Documentation Directory
Execute removal of historical docs, keep core 8 files

### Step 4: Clean Scripts Directory  
Execute removal of 23 redundant scripts

### Step 5: Clean Shared Directory
Execute removal of 10 redundant modules

### Step 6: Rename Stage Scripts
Execute file renaming for 10 core stages

### Step 7: Update Imports
Update all imports in:
- run-pipeline.py
- prepare-job.py
- Test files
- Documentation

### Step 8: Rebuild Documentation
Create new documentation structure with 20+ new files

### Step 9: Validate
- Run tests
- Verify imports
- Check documentation links
- Validate naming compliance

---

## 📊 Impact Summary

**Files to Remove:** ~100 files (36 root + 29 docs + 23 scripts + 10 shared + subdirs)
**Files to Rename:** 10 stage scripts  
**Files to Create:** ~20 new documentation files
**Files to Keep:** ~50 core files

**Total Cleanup:** Reduce from ~300 files to ~70 core files + new docs

---

**Status:** 🔴 DRAFT - Requires review and approval before execution  
**Risk:** Medium - Extensive changes, backup required  
**Rollback:** Full backup available

**Next Step:** Review this plan, approve, then execute step-by-step

---

**END OF CLEANUP PLAN**
