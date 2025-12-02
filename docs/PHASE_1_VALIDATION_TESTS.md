# Phase 1 Validation Tests

**Purpose:** Validate that Copilot follows the enhanced copilot-instructions.md (v3.0)  
**Duration:** ~20 minutes  
**Date:** December 2, 2025

---

## Test Objective

Verify that Copilot:
1. Uses the navigation table to find § references
2. Follows the critical rules (logger, imports, StageIO, etc.)
3. Uses the pre-commit checklist
4. Applies common patterns correctly

**Success Criteria:** 4/5 tests demonstrate correct behavior

---

## Quick Test Suite (5 Tests)

### Test 1: Logger Usage Compliance ⭐ PRIORITY #1

**Baseline Problem:** 60% of files use print() instead of logger

**Prompt:**
```
I need to add logging to a utility function that processes audio files.
The function should log when processing starts, progress every 10 files, 
and any errors that occur.
```

**Expected Behavior:**
- [ ] Uses `from shared.logger import get_logger`
- [ ] Uses `logger = get_logger(__name__)`
- [ ] Uses `logger.info()` not `print()`
- [ ] Uses `logger.error(..., exc_info=True)` for errors
- [ ] Mentions § 2.3 or references logging standards

**Record Results:**
- Copilot used logger: [YES/NO]
- Copilot mentioned § 2.3: [YES/NO]
- Quality (1-5): [_____]
- Notes: _________________________________

---

### Test 2: Import Organization ⭐ PRIORITY #2

**Baseline Problem:** 100% of files have unorganized imports

**Prompt:**
```
I'm creating a new utility file that needs:
- os and sys modules
- Path from pathlib
- numpy for arrays
- our load_config from shared.config
- our get_logger from shared.logger

Show me the proper import organization.
```

**Expected Behavior:**
- [ ] Groups into Standard / Third-party / Local
- [ ] Has blank lines between groups
- [ ] Mentions § 6.1 or import organization standards
- [ ] Matches the pattern from copilot-instructions.md

**Record Results:**
- Imports organized correctly: [YES/NO]
- Has 3 groups with blank lines: [YES/NO]
- Mentioned § 6.1: [YES/NO]
- Quality (1-5): [_____]
- Notes: _________________________________

---

### Test 3: StageIO Pattern Recognition

**Test if Copilot uses the navigation table**

**Prompt:**
```
I need to create a new pipeline stage for video frame extraction.
What's the proper pattern to follow?
```

**Expected Behavior:**
- [ ] References the navigation table
- [ ] Mentions § 3.1 for stage implementation
- [ ] Uses the complete StageIO template from instructions
- [ ] Includes all 8 required steps:
  - Initialize with enable_manifest=True
  - Get stage logger
  - Load config
  - Track inputs
  - Define output in stage_dir
  - Process
  - Track outputs
  - Finalize manifest

**Record Results:**
- Used navigation table: [YES/NO]
- Referenced § 3.1: [YES/NO]
- Complete pattern (8 steps): [YES/NO]
- Quality (1-5): [_____]
- Notes: _________________________________

---

### Test 4: Pre-Commit Checklist Usage

**Test if Copilot validates against checklist**

**Prompt:**
```
I've written this stage code. Can you review it against our standards?

def run_stage(job_dir):
    io = StageIO("test", job_dir)
    print("Processing...")
    output = job_dir / "output.txt"
    with open(output, 'w') as f:
        f.write("done")
    return 0
```

**Expected Behavior:**
- [ ] Identifies missing `enable_manifest=True`
- [ ] Identifies print() instead of logger
- [ ] Identifies output not in stage_dir
- [ ] Identifies missing manifest tracking
- [ ] References the pre-commit checklist

**Record Results:**
- Caught enable_manifest issue: [YES/NO]
- Caught print() issue: [YES/NO]
- Caught stage_dir issue: [YES/NO]
- Used checklist: [YES/NO]
- Quality (1-5): [_____]
- Notes: _________________________________

---

### Test 5: Configuration Pattern

**Prompt:**
```
I need to add a configuration parameter for maximum file size (in MB).
Default should be 100 MB. Show me the proper way to do this.
```

**Expected Behavior:**
- [ ] Says to add to `config/.env.pipeline`
- [ ] Uses `load_config()` not `os.getenv()`
- [ ] Provides default with `.get()`
- [ ] Converts to int: `int(config.get(...))`
- [ ] Mentions § 4 or configuration standards

**Record Results:**
- Uses load_config(): [YES/NO]
- Has default value: [YES/NO]
- Mentioned § 4: [YES/NO]
- Quality (1-5): [_____]
- Notes: _________________________________

---

## Scoring

### Calculate Results

```
Test 1 (Logger): [PASS/FAIL]
Test 2 (Imports): [PASS/FAIL]
Test 3 (StageIO): [PASS/FAIL]
Test 4 (Checklist): [PASS/FAIL]
Test 5 (Config): [PASS/FAIL]

Success Rate: [X/5] = _____%
```

### Pass Criteria

| Success Rate | Result | Action |
|--------------|--------|--------|
| 5/5 (100%) | ⭐ Excellent | Proceed to Phase 2 immediately |
| 4/5 (80%) | ✅ Good | Proceed to Phase 2 with confidence |
| 3/5 (60%) | 🟡 Acceptable | Note issues, proceed to Phase 2 |
| 2/5 (40%) | 🟠 Concerning | Review failures, adjust instructions |
| < 2/5 (<40%) | ❌ Failed | Revise copilot-instructions.md |

**Minimum to proceed:** 3/5 (60%)

---

## Comparison Tests (Optional)

### Before vs After

If you want to see the improvement, test the OLD instructions:

1. Temporarily rename files:
   ```bash
   mv .github/copilot-instructions.md .github/copilot-instructions-v3.md
   mv .github/copilot-instructions.md.backup .github/copilot-instructions.md
   ```

2. Run Test 1 and Test 2 with old instructions

3. Restore new instructions:
   ```bash
   mv .github/copilot-instructions.md .github/copilot-instructions-v2.md
   mv .github/copilot-instructions-v3.md .github/copilot-instructions.md
   ```

4. Compare results

**Expected:** v3.0 should score significantly better than v2.0

---

## Detailed Analysis (If Needed)

### If Test 1 Fails (Logger Usage)

**Problem:** Copilot still suggests print()

**Fixes to try:**
1. Make the ❌/✅ example more prominent
2. Add "NEVER use print()" in bold at the top
3. Repeat the rule in multiple sections

### If Test 2 Fails (Import Organization)

**Problem:** Copilot doesn't organize imports

**Fixes to try:**
1. Add comment markers to the example
2. Show a before/after comparison
3. Make it the first critical rule

### If Test 3 Fails (StageIO Pattern)

**Problem:** Copilot doesn't use navigation table

**Fixes to try:**
1. Make navigation table more prominent
2. Add "Consult navigation table first" to instructions
3. Test with explicit prompt: "Check the navigation table first"

### If Test 4 Fails (Checklist)

**Problem:** Copilot doesn't validate against checklist

**Fixes to try:**
1. Add "Before responding, check the pre-commit checklist"
2. Make checklist earlier in the file
3. Test with explicit prompt: "Review against our checklist"

### If Test 5 Fails (Configuration)

**Problem:** Copilot suggests os.getenv()

**Fixes to try:**
1. Make the ❌ DON'T example more prominent
2. Add more emphasis: "NEVER use os.getenv()"
3. Show the security/testability benefits

---

## Documentation

After testing, update this file with:

```markdown
## Test Results - [DATE]

**Tester:** [Your name]
**Duration:** [Time taken]
**Overall Score:** [X/5] (___%)

### Individual Test Results:

1. Logger Usage: [PASS/FAIL] - Notes: ...
2. Import Org: [PASS/FAIL] - Notes: ...
3. StageIO: [PASS/FAIL] - Notes: ...
4. Checklist: [PASS/FAIL] - Notes: ...
5. Config: [PASS/FAIL] - Notes: ...

### Decision: [PROCEED/REVISE]

### Issues Found:
- [List any issues]

### Recommended Changes:
- [List any suggested improvements]
```

---

## Next Steps

### If Tests Pass (≥ 3/5)

✅ **Proceed to Phase 2: Create Section Index**
- Document test results
- Commit results to this file
- Continue with integration plan

### If Tests Fail (< 3/5)

❌ **Revise copilot-instructions.md**
- Analyze failure patterns
- Adjust problematic sections
- Re-test before proceeding

---

## Quick Testing Tips

1. **Test in same session:** Don't restart IDE between tests
2. **Use exact prompts:** Copy-paste from this document
3. **Be objective:** Count it as PASS if pattern is mostly right
4. **Document surprises:** Note anything unexpected (good or bad)
5. **Take screenshots:** Capture Copilot responses for reference

---

## Expected Timeline

- Setup: 2 minutes
- Test 1-5: 3-4 minutes each
- Analysis: 5 minutes
- Documentation: 3 minutes
- **Total: ~20 minutes**

---

**Good luck testing!** 🧪

These tests will validate whether Phase 1 improvements are working as designed. The results will inform whether we proceed to Phase 2 or need to iterate on Phase 1.

---

**Last Updated:** December 2, 2025 22:05 UTC  
**Status:** READY FOR TESTING  
**Next:** Run tests and document results
