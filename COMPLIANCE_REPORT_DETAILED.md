# Detailed File-by-File Compliance Report

**Generated:** 2025-12-02  
**Companion to:** COMPLIANCE_REPORT.md  
**Purpose:** Detailed breakdown by file for targeted remediation

---

## Summary by Directory

| Directory | Total Files | Clean | Issues | Clean % |
|-----------|-------------|-------|--------|---------|
| scripts/  | 74 | 7 | 67 | 9.5% |
| shared/   | 30 | 2 | 28 | 6.7% |
| tests/    | 17 | 2 | 15 | 11.8% |
| pipeline/ | 1 | 0 | 1 | 0.0% |
| **TOTAL** | **122** | **11** | **111** | **9.0%** |

---

## SCRIPTS Directory (74 files)

### ✅ Clean Files (7) - Use as Templates

These files are fully compliant with all standards:

1. `__init__.py` - Empty module marker
2. `mux.py` - Video multiplexing
3. `post_ner.py` - Post-NER processing
4. `pre_ner.py` - Pre-NER processing
5. `second_pass_translation.py` - Translation refinement
6. `subtitle_gen.py` - Subtitle generation
7. `tmdb.py` - TMDB stage

---

### ❌ Top 20 Worst Offenders in scripts/

| File | Critical | Errors | Warnings | Priority |
|------|----------|--------|----------|----------|
| `fix_session3_issues.py` | 54 | 0 | 0 | 🔴 URGENT |
| `prepare-job.py` | 53 | 1 | 2 | 🔴 URGENT |
| `run-pipeline.py` | 47 | 1 | 31 | 🔴 URGENT |
| `hybrid_subtitle_merger_v2.py` | 45 | 0 | 2 | 🔴 HIGH |
| `compare_translations.py` | 42 | 0 | 4 | 🔴 HIGH |
| `hybrid_subtitle_merger.py` | 39 | 0 | 2 | 🔴 HIGH |
| `pyannote_vad_chunker.py` | 32 | 0 | 29 | 🔴 HIGH |
| `cache_manager.py` | 30 | 0 | 3 | 🟠 MEDIUM |
| `validate-compliance.py` | 26 | 1 | 14 | 🟠 MEDIUM |
| `retranslate_srt.py` | 13 | 1 | 11 | 🟠 MEDIUM |
| `config_loader.py` | 11 | 0 | 44 | 🟠 MEDIUM |
| `whisperx_integration.py` | 9 | 1 | 13 | 🟠 MEDIUM |
| `filename_parser.py` | 7 | 0 | 0 | 🟡 LOW |
| `patch_pyannote.py` | 6 | 0 | 1 | 🟡 LOW |
| `indictrans2_translator.py` | 5 | 1 | 7 | 🟡 LOW |
| `tmdb_enrichment.py` | 5 | 1 | 2 | 🟡 LOW |
| `musicbrainz_client.py` | 4 | 1 | 1 | 🟡 LOW |
| `mps_utils.py` | 3 | 1 | 11 | 🟡 LOW |
| `whisperx_translate_comparator.py` | 3 | 1 | 8 | 🟡 LOW |
| `fetch_tmdb_metadata.py` | 3 | 1 | 4 | 🟡 LOW |

**Note:** 47 additional files with issues not shown above

---

### Detailed Analysis: Top 5 Offenders

#### 1. `fix_session3_issues.py` - 54 CRITICAL violations
**Issues:**
- 54 print statements (should be logger.info/debug)
- Likely a debug/diagnostic script

**Recommendation:** 
- Convert all prints to logger.debug() since it's diagnostic
- Or move to tools/ directory if temporary

---

#### 2. `prepare-job.py` - 53 CRITICAL, 1 ERROR, 2 WARNINGS
**Issues:**
- 53 print statements
- 1 missing logger import
- 2 type hint warnings

**Recommendation:**
- This is a user-facing script, keep some prints for UX
- Convert internal prints to logger.info()
- Keep user feedback as prints (job setup messages)

---

#### 3. `run-pipeline.py` - 47 CRITICAL, 1 ERROR, 31 WARNINGS
**Issues:**
- 47 print statements
- 1 missing logger import
- 31 type hints missing

**Recommendation:**
- Critical script - HIGH PRIORITY
- Convert to proper logging immediately
- Add type hints to all functions

---

#### 4. `hybrid_subtitle_merger_v2.py` - 45 CRITICAL
**Issues:**
- 45 print statements
- Versioned file (v2) suggests v1 exists

**Recommendation:**
- Fix violations AND remove v1 if obsolete
- Consider this canonical version, delete old version

---

#### 5. `compare_translations.py` - 42 CRITICAL, 4 WARNINGS
**Issues:**
- 42 print statements
- Likely a utility/comparison tool

**Recommendation:**
- If it's a one-off tool, move to tools/
- If used in pipeline, fix all violations

---

## SHARED Directory (30 files)

### ✅ Clean Files (2)

1. `__init__.py` - Module marker
2. `utils.py` - General utilities (compliant!)

---

### ❌ Top 20 Worst Offenders in shared/

| File | Critical | Errors | Warnings | Priority |
|------|----------|--------|----------|----------|
| `hardware_detection.py` | 49 | 0 | 0 | 🔴 URGENT |
| `model_downloader.py` | 28 | 0 | 5 | 🔴 HIGH |
| `model_checker.py` | 24 | 0 | 5 | 🔴 HIGH |
| `stage_order.py` | 15 | 0 | 2 | 🟠 MEDIUM |
| `environment_manager.py` | 15 | 0 | 1 | 🟠 MEDIUM |
| `verify_pytorch.py` | 9 | 0 | 1 | 🟠 MEDIUM |
| `glossary.py` | 6 | 1 | 3 | 🟠 MEDIUM |
| `audio_utils.py` | 4 | 0 | 1 | 🟡 LOW |
| `config.py` | 2 | 0 | 14 | 🟡 LOW |
| `manifest.py` | 0 | 1 | 14 | 🟡 LOW |
| `glossary_advanced.py` | 0 | 1 | 12 | 🟡 LOW |
| `stage_utils.py` | 0 | 1 | 10 | 🟡 LOW |
| `glossary_manager.py` | 0 | 1 | 8 | 🟡 LOW |
| `glossary_ml.py` | 0 | 1 | 6 | 🟡 LOW |
| `logger.py` | 0 | 1 | 5 | 🟡 LOW |
| `glossary_cache.py` | 0 | 1 | 4 | 🟡 LOW |
| `glossary_generator.py` | 0 | 1 | 4 | 🟡 LOW |
| `glossary_unified.py` | 0 | 1 | 4 | 🟡 LOW |
| `tmdb_client.py` | 0 | 1 | 4 | 🟡 LOW |
| `ner_corrector.py` | 0 | 1 | 3 | 🟡 LOW |

---

### Detailed Analysis: Top 3 Offenders

#### 1. `hardware_detection.py` - 49 CRITICAL violations
**Issues:**
- 49 print statements
- Core system module

**Impact:** HIGH - affects all hardware detection
**Recommendation:** 
- URGENT fix - core infrastructure
- Convert all prints to logger.info() or logger.debug()
- Keep startup detection as logger.info()

---

#### 2. `model_downloader.py` - 28 CRITICAL, 5 WARNINGS
**Issues:**
- 28 print statements
- 5 type hint warnings

**Impact:** HIGH - affects model initialization
**Recommendation:**
- Convert progress prints to logger.info()
- User-facing download progress can stay as print OR use tqdm
- Add type hints

---

#### 3. `model_checker.py` - 24 CRITICAL, 5 WARNINGS
**Issues:**
- 24 print statements
- 5 type hint warnings

**Impact:** MEDIUM - model validation
**Recommendation:**
- Convert to logger.debug() for checks
- logger.info() for results
- Add type hints

---

## TESTS Directory (17 files)

### ✅ Clean Files (2)

1. `__init__.py` - Module marker
2. `conftest.py` - Pytest configuration (compliant!)

---

### ❌ All Files with Issues (15)

| File | Critical | Errors | Warnings | Priority |
|------|----------|--------|----------|----------|
| `test_indictrans2.py` | 71 | 0 | 4 | 🔴 HIGH |
| `test_source_separation_fix.py` | 71 | 0 | 4 | 🔴 HIGH |
| `test_lyrics_detection_fixes.py` | 70 | 0 | 5 | 🔴 HIGH |
| `test_glossary_system.py` | 67 | 0 | 7 | 🔴 HIGH |
| `test_enhancements.py` | 64 | 0 | 4 | 🔴 HIGH |
| `test_lyrics_enhancement.py` | 64 | 0 | 2 | 🔴 HIGH |
| `test_phase1.py` | 59 | 0 | 6 | 🔴 HIGH |
| `test_musicbrainz.py` | 59 | 0 | 5 | 🔴 HIGH |
| `test_phase1_week2.py` | 56 | 0 | 4 | 🔴 HIGH |
| `test_hybrid_translator.py` | 44 | 0 | 2 | 🟠 MEDIUM |
| `test_subtitle_enhancement.py` | 40 | 0 | 3 | 🟠 MEDIUM |
| `test_indictrans2_fixes.py` | 33 | 0 | 1 | 🟠 MEDIUM |
| `test_glossary_manager.py` | 0 | 0 | 15 | 🟡 LOW |
| `test_stage_runner_cache_behavior.py` | 0 | 0 | 6 | 🟡 LOW |
| `test_manifest_checksum.py` | 0 | 0 | 3 | 🟡 LOW |

---

### Tests Special Considerations

**Why so many violations?**
- Tests use print() for debugging/visibility
- Pytest captures output differently
- Many assertions with debug prints

**Recommendation:**
- Use pytest's `caplog` fixture instead of prints
- Convert to logger.debug() for test diagnostics
- Keep assertion messages as is
- Use `-v` flag for verbose pytest output

**Example Fix:**
```python
# ❌ BEFORE
def test_feature():
    print("Testing feature X...")
    result = do_something()
    print(f"Result: {result}")
    assert result == expected

# ✅ AFTER
def test_feature(caplog):
    logger.debug("Testing feature X...")
    result = do_something()
    logger.debug(f"Result: {result}")
    assert result == expected
    assert "Testing feature X" in caplog.text
```

---

## PIPELINE Directory (1 file)

### ❌ Files with Issues (1)

| File | Critical | Errors | Warnings | Priority |
|------|----------|--------|----------|----------|
| `runner.py` | 4 | 0 | 11 | 🟡 LOW |

**Issues:**
- 4 print statements (likely debug)
- 11 type hint warnings

**Recommendation:**
- Low priority - only 1 file
- Convert 4 prints to logger.info()
- Add type hints to runner functions

---

## Priority Matrix for Remediation

### 🔴 URGENT (Complete in Week 1)

**Scripts:**
- `fix_session3_issues.py` (54 violations)
- `prepare-job.py` (53 violations)
- `run-pipeline.py` (47 violations)

**Shared:**
- `hardware_detection.py` (49 violations)
- `model_downloader.py` (28 violations)
- `model_checker.py` (24 violations)

**Tests:**
- `test_enhancements.py` (64 violations) - example for others

**Total:** 7 files, ~320 violations (24% of total)

---

### 🟠 HIGH (Complete in Week 2)

**Scripts:**
- `hybrid_subtitle_merger_v2.py` (45 violations)
- `compare_translations.py` (42 violations)
- `hybrid_subtitle_merger.py` (39 violations)
- `pyannote_vad_chunker.py` (32 violations)
- `cache_manager.py` (30 violations)

**Shared:**
- `environment_manager.py` (15 violations)
- `stage_order.py` (15 violations)

**Tests:**
- Top 6 test files (400+ violations total)

**Total:** 13 files, ~620 violations (47% of total)

---

### 🟡 MEDIUM/LOW (Complete in Week 3-4)

All remaining files with < 15 violations each

---

## Automated Fix Script Targets

### Safe to Auto-Fix (Low Risk)

These files have simple violations suitable for automated fixes:

**Logger Import Addition:**
- All 69 files with missing logger imports
- Script available in COMPLIANCE_REPORT.md

**Type Hints (Semi-automated with mypy/pytype):**
- All glossary_* files (mostly warnings)
- All test files

**Import Organization (isort):**
- ALL files - can run blindly

---

### Require Manual Review (High Risk)

**Print statements in:**
- `prepare-job.py` - user-facing messages
- `run-pipeline.py` - pipeline orchestration
- All test files - pytest integration

**Config access in:**
- `config.py` itself
- Files with complex config logic

---

## Code Smell Alerts

### Duplicate Functionality Detected

**Lyrics Detection (4 files):**
```
scripts/lyrics_detection.py         - 16KB, many violations
scripts/lyrics_detection_core.py    - 27KB, many violations
scripts/lyrics_detection_pipeline.py - 7KB
scripts/lyrics_detector.py          - 15KB, many violations
```
**Recommendation:** Consolidate to 1-2 files maximum

**Hybrid Subtitle Merger (2 versions):**
```
scripts/hybrid_subtitle_merger.py    - 39 violations
scripts/hybrid_subtitle_merger_v2.py - 45 violations
```
**Recommendation:** Keep v2, delete v1 after verification

---

## Tracking Progress

### Command to Re-run This Report

```bash
python3 /tmp/detailed_report.py > COMPLIANCE_REPORT_DETAILED_NEW.md
diff COMPLIANCE_REPORT_DETAILED.md COMPLIANCE_REPORT_DETAILED_NEW.md
```

### Weekly Progress Tracking

Create this file: `compliance_progress.csv`

```csv
Week,Date,Clean_Files,Total_Critical,Total_Errors,Total_Warnings,Compliance_%
0,2025-12-02,11,1320,69,611,9.0
1,2025-12-09,TBD,TBD,TBD,TBD,TBD
2,2025-12-16,TBD,TBD,TBD,TBD,TBD
3,2025-12-23,TBD,TBD,TBD,TBD,TBD
4,2025-12-30,110,<13,<7,<100,90.0
```

---

## Appendix: File Categories

### By Function

**Pipeline Orchestration:**
- `run-pipeline.py` (47 violations) 🔴
- `prepare-job.py` (53 violations) 🔴
- `pipeline/runner.py` (15 violations) 🟠

**Audio Processing:**
- `demux.py` (clean) ✅
- `mux.py` (clean) ✅
- `source_separation.py` (violations)
- `audio_utils.py` (4 violations)

**Translation:**
- `translation.py` (violations)
- `translation_refine.py` (violations)
- `indictrans2_translator.py` (5 violations)
- `nllb_translator.py` (violations)

**Glossary System:**
- All glossary_* files (mostly ERROR + WARNING level)
- Consolidation opportunity

**Tests:**
- All have print violations (test framework issue)

---

**End of Detailed Report**

**Next Steps:**
1. Review main COMPLIANCE_REPORT.md
2. Start with URGENT priority files
3. Re-run validation after each fix
4. Track progress weekly

