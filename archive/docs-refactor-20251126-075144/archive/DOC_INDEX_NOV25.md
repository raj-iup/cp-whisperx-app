# Documentation Index - November 25, 2025

## Quick Access

| Document | Purpose | Size | Read Time |
|----------|---------|------|-----------|
| [QUICK_REFERENCE_NOV25.sh](QUICK_REFERENCE_NOV25.sh) | Quick command reference | 11KB | 5 min |
| [CHANGES_SUMMARY_NOV25_FINAL.md](CHANGES_SUMMARY_NOV25_FINAL.md) | What changed summary | 6KB | 3 min |
| [IMPLEMENTATION_COMPLETE_NOV25.md](IMPLEMENTATION_COMPLETE_NOV25.md) | Implementation details | 15KB | 10 min |
| [COMPREHENSIVE_ANALYSIS_AND_FIXES.md](COMPREHENSIVE_ANALYSIS_AND_FIXES.md) | Complete analysis | 18KB | 15 min |

## Start Here

**New to the project?**
→ Read: [QUICK_REFERENCE_NOV25.sh](QUICK_REFERENCE_NOV25.sh)

**Want to know what changed?**
→ Read: [CHANGES_SUMMARY_NOV25_FINAL.md](CHANGES_SUMMARY_NOV25_FINAL.md)

**Need implementation details?**
→ Read: [IMPLEMENTATION_COMPLETE_NOV25.md](IMPLEMENTATION_COMPLETE_NOV25.md)

**Want complete analysis?**
→ Read: [COMPREHENSIVE_ANALYSIS_AND_FIXES.md](COMPREHENSIVE_ANALYSIS_AND_FIXES.md)

## What's New (November 25, 2025)

### ✅ Implemented
1. **Indic→Indic Auto-Caching**
   - Bootstrap now prompts to cache cross-Indic translation model
   - File: `scripts/bootstrap.sh` (lines 227-248)

2. **Log Level CLI Options** (Already Present)
   - All main scripts support `--log-level DEBUG|INFO|WARN|ERROR|CRITICAL`
   - Scripts: bootstrap.sh, prepare-job.sh, run-pipeline.sh

3. **MLX Model Loading** (Already Fixed)
   - Correct import in `scripts/bootstrap.sh` (lines 191-192)

### 📋 Documented
1. **Empty Alignment Directory Issue**
   - MLX backend skips alignment (only verifies)
   - Enhancement plan provided

2. **Beam Comparison Failures**
   - Analysis and debug steps documented
   - Needs test data for full resolution

3. **Codebase Dependency Map**
   - Complete visual map of all dependencies
   - Shows relationship between scripts and modules

## Documentation Overview

### QUICK_REFERENCE_NOV25.sh
**Purpose:** Daily reference for common tasks

**Contents:**
- Bootstrap usage examples
- Prepare-job command syntax
- Run-pipeline options
- Beam comparison usage
- Log levels explained
- Troubleshooting tips
- Directory structure
- Supported languages

**Use When:** You need to remember command syntax

**View:** `./QUICK_REFERENCE_NOV25.sh`

---

### CHANGES_SUMMARY_NOV25_FINAL.md
**Purpose:** Executive summary of changes

**Contents:**
- Files modified/created
- Key findings
- Verification commands
- Usage examples
- Answers summary table
- Next steps

**Use When:** You want a quick overview of what changed

**View:** `cat CHANGES_SUMMARY_NOV25_FINAL.md`

---

### IMPLEMENTATION_COMPLETE_NOV25.md
**Purpose:** Detailed implementation documentation

**Contents:**
- Completed tasks with status
- Issues identified with solutions
- Codebase dependency graph
- Logging standards compliance
- Commands reference
- Verification checklist
- Future enhancements

**Use When:** You need implementation details or troubleshooting

**View:** `cat IMPLEMENTATION_COMPLETE_NOV25.md`

---

### COMPREHENSIVE_ANALYSIS_AND_FIXES.md
**Purpose:** Complete technical analysis

**Contents:**
- Root cause analysis for all issues
- MLX alignment enhancement plan
- Beam comparison debugging
- Complete dependency mapping
- Implementation tasks with time estimates
- Answers to all specific questions

**Use When:** You need deep technical understanding

**View:** `cat COMPREHENSIVE_ANALYSIS_AND_FIXES.md`

---

## Key Questions Answered

### Q1: MLX Model Loading
**Q:** Does the bootstrap fix make sense?  
**A:** ✅ YES - Already fixed with correct import  
**Location:** `scripts/bootstrap.sh` lines 191-192

### Q2: Empty Alignment
**Q:** Why is 05_alignment empty?  
**A:** MLX backend skips alignment (only verifies)  
**Details:** COMPREHENSIVE_ANALYSIS_AND_FIXES.md section 2

### Q3: Alignment Order
**Q:** Is alignment running in correct order?  
**A:** ✅ YES - Order is correct (demux → asr → alignment)  
**Details:** Pipeline runs stages in correct sequence

### Q4: MLX Enhancement
**Q:** Can we implement MLX alignment enhancement?  
**A:** ✅ YES - Implementation plan provided  
**Details:** COMPREHENSIVE_ANALYSIS_AND_FIXES.md section 2 & Task 1

### Q5: Beam Outputs
**Q:** Can we create beam outputs 4-10?  
**A:** ✅ YES - `compare-beam-search.sh` already does this  
**Usage:** `./compare-beam-search.sh JOB_DIR --beam-range 4,10`

### Q6: IndicTransToolkit Warning
**Q:** What does the warning mean?  
**A:** ℹ️ Informational only - not an error  
**Details:** COMPREHENSIVE_ANALYSIS_AND_FIXES.md section 3

### Q7: Environment Usage
**Q:** Is compare-beam-search using right environment?  
**A:** ✅ YES - Correctly uses `venv/indictrans2`  
**Location:** `compare-beam-search.sh` line 166

### Q8: Log Level CLI
**Q:** Add log-level as command-line option?  
**A:** ✅ ALREADY DONE - All main scripts support it  
**Usage:** `./bootstrap.sh --log-level DEBUG`

### Q9: Indic→Indic Caching
**Q:** Auto-cache Indic→Indic model?  
**A:** ✅ IMPLEMENTED - Bootstrap now prompts  
**Location:** `scripts/bootstrap.sh` lines 227-248

---

## Command Reference

### Bootstrap
```bash
./bootstrap.sh --log-level DEBUG --cache-models
```

### Prepare Job
```bash
./prepare-job.sh --media file.mp4 --workflow subtitle \
    --source-language hi --target-language en --log-level DEBUG
```

### Run Pipeline
```bash
./run-pipeline.sh -j job-id --log-level DEBUG
```

### Beam Comparison
```bash
./compare-beam-search.sh out/PATH/TO/JOB --beam-range 4,10
```

---

## File Structure

```
cp-whisperx-app/
│
├── Documentation (Nov 25, 2025)
│   ├── QUICK_REFERENCE_NOV25.sh                  ← Quick command reference
│   ├── CHANGES_SUMMARY_NOV25_FINAL.md            ← What changed
│   ├── IMPLEMENTATION_COMPLETE_NOV25.md          ← Implementation details
│   ├── COMPREHENSIVE_ANALYSIS_AND_FIXES.md       ← Complete analysis
│   └── DOC_INDEX_NOV25.md                        ← This file
│
├── Main Scripts
│   ├── bootstrap.sh                               ← Modified (Indic→Indic caching)
│   ├── prepare-job.sh                             ← Has log-level support
│   ├── run-pipeline.sh                            ← Has log-level support
│   └── compare-beam-search.sh                     ← Beam comparison tool
│
├── Script Implementations
│   └── scripts/
│       ├── bootstrap.sh                           ← Actual bootstrap implementation
│       ├── common-logging.sh                      ← Common logging functions
│       ├── prepare-job.py                         ← Job preparation
│       ├── run-pipeline.py                        ← Pipeline orchestration
│       ├── indictrans2_translator.py              ← Translation engine
│       ├── beam_search_comparison.py              ← Beam comparison logic
│       └── mlx_alignment.py                       ← Alignment (needs enhancement)
│
└── Shared Modules
    └── shared/
        ├── logger.py                              ← Python logging
        ├── config.py                              ← Configuration management
        ├── manifest.py                            ← Stage tracking
        ├── job_manager.py                         ← Job management
        └── environment_manager.py                 ← Virtual env handling
```

---

## Troubleshooting Guide

### Issue: Bootstrap fails with MLX error
**Solution:** Already fixed - Update to latest bootstrap.sh

### Issue: 05_alignment directory empty
**Status:** Known limitation - MLX skips alignment  
**Workaround:** Use WhisperX backend for alignment  
**Future:** Enhancement planned (see COMPREHENSIVE_ANALYSIS)

### Issue: Beam comparison fails
**Debug:** Run with `--log-level DEBUG`  
**Check:** Ensure segments.json exists in 04_asr/  
**Details:** COMPREHENSIVE_ANALYSIS_AND_FIXES.md section 3

### Issue: IndicTransToolkit warning
**Status:** Informational only  
**Action:** None required - fallback works fine

---

## Next Steps

### Immediate
- [x] Log level CLI options
- [x] Indic→Indic auto-caching
- [x] Documentation complete
- [ ] Test with actual job data

### Future (Priority)
1. **HIGH:** Implement MLX alignment enhancement
2. **MEDIUM:** Debug beam comparison with test data
3. **LOW:** Performance profiling

---

## Support

**For command help:**
```bash
./bootstrap.sh --help
./prepare-job.sh --help
./run-pipeline.sh --help
./compare-beam-search.sh --help
```

**For quick reference:**
```bash
./QUICK_REFERENCE_NOV25.sh
```

**For complete details:**
```bash
cat COMPREHENSIVE_ANALYSIS_AND_FIXES.md
```

---

**Last Updated:** November 25, 2025  
**Status:** ✅ Complete  
**Version:** 1.0
