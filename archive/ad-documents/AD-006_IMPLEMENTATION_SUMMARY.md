# Architectural Decision AD-006: Implementation Summary

**Date:** 2025-12-04 13:40 UTC  
**Decision:** Job-Specific Parameters Override System Defaults  
**Status:** ✅ **MANDATORY** - All stages must comply  
**Triggered By:** Bug #3 (Language detection issue in E2E Test 1)  
**Impact:** All 12 stages + future stages

---

## 🎯 Executive Summary

**What Changed:**
- Bug fix elevated to architectural standard
- All stages now MUST read job.json parameters before using system defaults
- 4-tier configuration hierarchy established
- Standard implementation pattern documented

**Why It Matters:**
- Respects user's explicit CLI choices
- Enables per-job customization
- Ensures reproducibility
- Fixes inconsistent parameter handling

**Compliance Required:**
- ✅ Fixed: Stage 06 (whisperx_integration.py)
- ⏳ TODO: Audit 11 remaining stages
- ⏳ TODO: Add compliance check to validate-compliance.py

---

## 📋 The Decision (AD-006)

### Full Text

**ALL stages MUST honor job-specific parameters over system defaults.**

**Priority Order (Highest to Lowest):**
1. **job.json** - User's explicit CLI choices (--source-language, --workflow, etc.)
2. **Job .env file** - Job-specific overrides (optional)
3. **System config/.env.pipeline** - Global defaults (version controlled)
4. **Code defaults** - Hardcoded fallbacks (last resort)

### Rationale

1. **User Intent:** User explicitly chooses parameters via CLI
2. **Reproducibility:** Same job.json always produces same results
3. **Flexibility:** Per-job customization without global config changes
4. **Bug Fix:** Inconsistent parameter handling caused language detection failure

### Mandatory For

- ✅ **ALL 12 stages** that read configuration parameters
- ✅ Language parameters (source_language, target_languages)
- ✅ Model settings (model size, compute type, batch size)
- ✅ Quality settings (beam size, temperature, thresholds)
- ✅ Workflow flags (source_separation_enabled, tmdb_enabled)
- ✅ Output preferences (subtitle format, translation engines)

---

## 🐛 The Bug That Started It All

### Bug #3: Language Detection

**Observed in:** E2E Test 1 (job-20251204-rpatel-0001)

**Symptom:**
```
User specified:     --source-language en
job.json shows:     "source_language": "en"
ASR detected:       "hi" (Hindi)
Pipeline log shows: "Source: hi, Target: hi"
```

**Root Cause:**
```python
# whisperx_integration.py line 1406 (before fix)
source_lang = getattr(config, 'whisper_language', 'hi')  # System default 'hi'

# The script never read job.json for source_language
# It only read job.json for 'workflow' parameter
```

**Impact:**
- Wrong language model loaded
- Potentially lower accuracy
- User's explicit choice ignored

---

## ✅ The Fix

### Code Change

**File:** `scripts/whisperx_integration.py`  
**Lines:** 1415-1429

```python
# BEFORE (old pattern - WRONG)
config = load_config()
source_lang = getattr(config, 'whisper_language', 'hi')
target_lang = getattr(config, 'target_language', 'en')

# Read workflow but NOT languages from job.json
job_json_path = stage_io.output_base / "job.json"
if job_json_path.exists():
    with open(job_json_path) as f:
        job_data = json.load(f)
        workflow_mode = job_data.get('workflow', 'transcribe')  # Only workflow!

# AFTER (new pattern - CORRECT, MANDATORY)
config = load_config()
source_lang = getattr(config, 'whisper_language', 'hi')
target_lang = getattr(config, 'target_language', 'en')

# Read workflow AND languages from job.json
job_json_path = stage_io.output_base / "job.json"
if job_json_path.exists():
    with open(job_json_path) as f:
        job_data = json.load(f)
        workflow_mode = job_data.get('workflow', 'transcribe')
        
        # Override with job-specific parameters (MANDATORY)
        if 'source_language' in job_data and job_data['source_language']:
            source_lang = job_data['source_language']  # Job takes priority!
        
        if 'target_languages' in job_data and job_data['target_languages']:
            target_lang = job_data['target_languages'][0]
```

### Pattern Breakdown

**Step 1: Load System Defaults**
```python
config = load_config()
param_value = getattr(config, 'param_name', default_value)
```

**Step 2: Override with Job Parameters (MANDATORY)**
```python
job_json_path = job_dir / "job.json"
if job_json_path.exists():
    with open(job_json_path) as f:
        job_data = json.load(f)
        if 'param_name' in job_data and job_data['param_name']:
            param_value = job_data['param_name']  # Job overrides system
```

**Step 3: Use the Parameter**
```python
logger.info(f"Using parameter: {param_value}")  # Logs job value if specified
```

---

## 📝 Documentation Updates

### 1. ARCHITECTURE_ALIGNMENT_2025-12-04.md
- ✅ Added AD-006 as architectural decision #6
- ✅ Full rationale and implementation pattern
- ✅ Compliance status: Fixed in 1 stage, 11 remaining

### 2. docs/developer/DEVELOPER_STANDARDS.md
- ✅ Version: 6.3 → 6.4
- ✅ Added § 3.3 "Stage Configuration Loading (MANDATORY)"
- ✅ Standard implementation pattern
- ✅ Compliance requirements

### 3. docs/technical/architecture.md
- ✅ Version: 2.0 → 3.0
- ✅ Added "Configuration Hierarchy" section
- ✅ Added AD-006 to architecture decisions list
- ✅ 4-tier priority system documented

### 4. IMPLEMENTATION_TRACKER.md
- ✅ Version: 3.1 → 3.2
- ✅ Progress: 75% → 78%
- ✅ Added AD-006 tasks to Phase 4
- ✅ Stage audit task added

### 5. .github/copilot-instructions.md
- ✅ Version: 6.2 → 6.5
- ✅ Updated § 4 Configuration section
- ✅ Added AD-006 to mental checklist
- ✅ Mandatory pattern documented

### Summary

**Total Files Updated:** 5  
**Documentation Versions:** 4 incremented  
**New Sections:** 3 (AD-006, Configuration Hierarchy, § 3.3)

---

## 🔍 Stage Audit Status

### Compliance Check Required

**Total Stages:** 12  
**Audited:** 1 (8%)  
**Remaining:** 11 (92%)

### Stages to Audit

| # | Stage | File | Priority | Status |
|---|-------|------|----------|--------|
| 01 | demux | 01_demux.py | MEDIUM | ⏳ TODO |
| 02 | tmdb | 02_tmdb_enrichment.py | HIGH | ⏳ TODO |
| 03 | glossary_load | 03_glossary_load.py | HIGH | ⏳ TODO |
| 04 | source_separation | 04_source_separation.py | MEDIUM | ⏳ TODO |
| 05 | pyannote_vad | 05_pyannote_vad.py | MEDIUM | ⏳ TODO |
| 06 | whisperx_asr | 06_whisperx_asr.py | HIGH | ✅ FIXED |
| 07 | alignment | 07_alignment.py | MEDIUM | ⏳ TODO |
| 08 | lyrics_detection | 08_lyrics_detection.py | LOW | ⏳ TODO |
| 09 | hallucination_removal | 09_hallucination_removal.py | LOW | ⏳ TODO |
| 10 | translation | 10_translation.py | HIGH | ⏳ TODO |
| 11 | subtitle_generation | 11_subtitle_generation.py | MEDIUM | ⏳ TODO |
| 12 | mux | 12_mux.py | MEDIUM | ⏳ TODO |

**Priority:**
- **HIGH:** Stages that read language/workflow parameters
- **MEDIUM:** Stages that read model/quality settings
- **LOW:** Stages with minimal configuration

---

## ⏳ Next Steps

### Immediate (Session 5)

1. ✅ Bug #3 fixed (whisperx_integration.py)
2. ✅ AD-006 documented in all standards
3. ⏳ Complete E2E Test 1 (validate fix works)
4. ⏳ Test retry with correct language detection

### Short-Term (Next 1-2 Days)

1. ⏳ Audit remaining 11 stages for AD-006 compliance
2. ⏳ Fix any non-compliant stages
3. ⏳ Add AD-006 check to validate-compliance.py
4. ⏳ Update stage template with mandatory pattern
5. ⏳ Run E2E Tests 2-3 to validate all workflows

### Medium-Term (Next Week)

1. ⏳ Ensure all new stages follow AD-006 pattern
2. ⏳ Document stage audit results
3. ⏳ Add to CI/CD pipeline validation
4. ⏳ Update onboarding documentation

---

## 📊 Impact Assessment

### User Impact

**Positive:**
- ✅ User's explicit choices respected
- ✅ Predictable behavior (same CLI = same result)
- ✅ Per-job customization enabled
- ✅ Better testing isolation

**No Negative Impact:**
- ✅ Backward compatible (system defaults still work)
- ✅ No breaking changes
- ✅ Existing jobs unaffected

### Developer Impact

**Requirements:**
- ✅ All new stages must implement AD-006 pattern
- ✅ Existing stages need audit and potential fix
- ✅ Standard pattern easy to follow

**Benefits:**
- ✅ Clear, consistent configuration loading
- ✅ Easier to debug parameter issues
- ✅ Reduced configuration bugs

### System Impact

**Performance:**
- ✅ Negligible (one JSON read per stage)
- ✅ No memory impact
- ✅ No latency increase

**Maintainability:**
- ✅ Easier to test (isolated configs)
- ✅ Clearer data flow
- ✅ Better reproducibility

---

## 🎯 Success Criteria

### Definition of Done

- [ ] All 12 stages comply with AD-006
- [ ] validate-compliance.py checks AD-006
- [ ] All E2E tests pass with job-specific parameters
- [ ] Stage template includes AD-006 pattern
- [ ] Documentation complete and synchronized
- [ ] Zero parameter-related bugs in production

### Acceptance Testing

**Test 1: Language Override**
```bash
./prepare-job.sh --media file.mp4 --workflow transcribe -s en
# Verify ASR uses 'en' not system default 'hi'
```

**Test 2: Model Override**
```bash
# System default: large-v3
./prepare-job.sh --media file.mp4 --model base
# Verify ASR uses 'base' not 'large-v3'
```

**Test 3: Workflow Flag Override**
```bash
# System default: source_separation=true
./prepare-job.sh --media file.mp4 --no-source-separation
# Verify stage 04 skipped
```

---

## 📚 Reference Documents

1. **ARCHITECTURE_ALIGNMENT_2025-12-04.md** - AD-006 full rationale
2. **docs/developer/DEVELOPER_STANDARDS.md** - § 3.3 implementation guide
3. **docs/technical/architecture.md** - Configuration hierarchy
4. **IMPLEMENTATION_TRACKER.md** - Progress tracking
5. **.github/copilot-instructions.md** - Quick reference
6. **E2E_TESTING_SESSION_2025-12-04.md** - Bug discovery context

---

## 🎊 Conclusion

**Architectural Decision AD-006** transforms a bug fix into a systemic improvement:

- ✅ **User Experience:** Explicit choices respected
- ✅ **Developer Experience:** Clear, consistent pattern
- ✅ **System Quality:** Reduced configuration bugs
- ✅ **Reproducibility:** Predictable, testable behavior

**Status:** MANDATORY for all current and future stages.

**Compliance Target:** 100% within 1-2 weeks.

**Next:** Complete stage audit and E2E testing validation.

---

**Document Status:** ✅ COMPLETE  
**AD-006 Status:** ✅ MANDATORY  
**Compliance:** 8% (1 of 12 stages)  
**Target:** 100% (12 of 12 stages)
