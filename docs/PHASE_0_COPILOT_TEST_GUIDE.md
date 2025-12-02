# Phase 0: Copilot POC Testing Guide

**Purpose:** Test if GitHub Copilot can follow § notation and navigation tables  
**Duration:** ~1 hour (30 min testing + 30 min analysis)  
**Status:** READY TO EXECUTE

---

## Prerequisites

✅ Before you begin, ensure:
- [ ] GitHub Copilot is active in your IDE/GitHub UI
- [ ] You have access to Copilot Chat
- [ ] You're in the `cp-whisperx-app` repository
- [ ] You've read `docs/BASELINE_COMPLIANCE_METRICS.md`

---

## Test Setup (5 minutes)

### Step 1: Add Test Sections to copilot-instructions.md

Open `.github/copilot-instructions.md` and add this at the end:

```markdown
---

## 🧪 POC TEST: Section References

When implementing stages, consult § 2.6 of `docs/developer/DEVELOPER_STANDARDS.md`

Key patterns:
- Stage initialization: See § 2.6.1
- Logging: See § 2.3
- Manifest tracking: See § 2.5
- Error handling: See § 5

## 🧪 POC TEST: Navigation Table

Use this table to find the right section for your task:

| Task | Consult Section | Key Topic |
|------|----------------|-----------|
| Add new stage | § 3.1 | Stage implementation pattern |
| Modify config | § 4.2 | Configuration management |
| Add logging | § 2.3 | Logger usage |
| Error handling | § 5.1 | Try/except patterns |
| Manifest tracking | § 2.5 | Input/output tracking |

**Example:** If adding a new stage, reference § 3.1 for the complete pattern.
```

**Save the file** but don't commit yet (this is temporary for testing).

---

## Task 3: Test § Notation (30 minutes)

### Test 3.1: Stage Implementation with § Reference

**Objective:** See if Copilot references § 2.6 when implementing a stage

**Instructions:**
1. Open Copilot Chat (in your IDE or GitHub UI)
2. Make sure you're in the `cp-whisperx-app` directory
3. Copy and paste this exact prompt:

```
I need to implement a new pipeline stage for audio normalization. 
The stage should:
- Normalize audio levels to -23 LUFS
- Accept input audio file from previous stage
- Output normalized audio to stage directory
- Track inputs/outputs properly

Please help me implement this following our project standards.
```

**What to observe:**
- [ ] Does Copilot mention § 2.6 in its response?
- [ ] Does it reference `DEVELOPER_STANDARDS.md`?
- [ ] Does it use the correct StageIO pattern?
- [ ] Does it mention `enable_manifest=True`?

**Record the results:**
```
Test 3.1 Results:
- Prompt given: [✅]
- Copilot mentioned § 2.6: [YES/NO]
- Copilot used StageIO pattern: [YES/NO]
- Copilot mentioned enable_manifest: [YES/NO]
- Quality of response (1-5): [_____]
- Notes: _________________________________
```

---

### Test 3.2: Error Handling with § Reference

**Instructions:**
1. Copy and paste this prompt in Copilot Chat:

```
I need to add error handling to the glossary_builder.py file.
It should handle file not found errors and permission errors.
Follow our project's error handling standards.
```

**What to observe:**
- [ ] Does Copilot mention § 5 (error handling)?
- [ ] Does it use logger instead of print?
- [ ] Does it show proper try/except pattern?

**Record the results:**
```
Test 3.2 Results:
- Prompt given: [✅]
- Copilot mentioned § 5: [YES/NO]
- Copilot used logger (not print): [YES/NO]
- Copilot showed try/except: [YES/NO]
- Quality of response (1-5): [_____]
- Notes: _________________________________
```

---

### Test 3.3: Configuration Change with § Reference

**Instructions:**
1. Copy and paste this prompt in Copilot Chat:

```
I need to add a new configuration parameter for the maximum audio duration.
It should be read from the config and have a default value of 3600 seconds.
How should I implement this following our standards?
```

**What to observe:**
- [ ] Does Copilot mention § 4 (configuration)?
- [ ] Does it suggest using `load_config()`?
- [ ] Does it reference `.env.pipeline`?

**Record the results:**
```
Test 3.3 Results:
- Prompt given: [✅]
- Copilot mentioned § 4: [YES/NO]
- Copilot suggested load_config(): [YES/NO]
- Copilot mentioned .env.pipeline: [YES/NO]
- Quality of response (1-5): [_____]
- Notes: _________________________________
```

---

## Task 4: Test Navigation Table (30 minutes)

### Test 4.1: New Stage via Navigation Table

**Objective:** See if Copilot uses the navigation table

**Instructions:**
1. Open Copilot Chat
2. Copy and paste this prompt:

```
I need to add a new stage to the pipeline. 
What's the best way to do this in our project?
```

**What to observe:**
- [ ] Does Copilot reference the navigation table?
- [ ] Does it mention "consult § 3.1"?
- [ ] Does it list the steps from § 3.1?

**Record the results:**
```
Test 4.1 Results:
- Prompt given: [✅]
- Copilot referenced the table: [YES/NO]
- Copilot mentioned § 3.1: [YES/NO]
- Copilot provided stage pattern: [YES/NO]
- Quality of response (1-5): [_____]
- Notes: _________________________________
```

---

### Test 4.2: Config Modification via Navigation Table

**Instructions:**
1. Copy and paste this prompt in Copilot Chat:

```
I need to modify a configuration value. 
What's the proper way to do this in our codebase?
```

**What to observe:**
- [ ] Does Copilot reference the navigation table?
- [ ] Does it mention "consult § 4.2"?
- [ ] Does it explain the config pattern?

**Record the results:**
```
Test 4.2 Results:
- Prompt given: [✅]
- Copilot referenced the table: [YES/NO]
- Copilot mentioned § 4.2: [YES/NO]
- Copilot explained config pattern: [YES/NO]
- Quality of response (1-5): [_____]
- Notes: _________________________________
```

---

### Test 4.3: Logging Addition via Navigation Table

**Instructions:**
1. Copy and paste this prompt in Copilot Chat:

```
I want to add more detailed logging to a function.
What's our logging standard?
```

**What to observe:**
- [ ] Does Copilot reference the navigation table?
- [ ] Does it mention "consult § 2.3"?
- [ ] Does it say "use logger not print"?

**Record the results:**
```
Test 4.3 Results:
- Prompt given: [✅]
- Copilot referenced the table: [YES/NO]
- Copilot mentioned § 2.3: [YES/NO]
- Copilot said use logger: [YES/NO]
- Quality of response (1-5): [_____]
- Notes: _________________________________
```

---

## Task 5: Analyze Results & Make Decision (30 minutes)

### Step 1: Calculate Success Rate

Fill in your results:

```
§ Notation Tests (Test 3):
- Test 3.1 (Stage): § 2.6 referenced? [YES/NO]
- Test 3.2 (Error): § 5 referenced? [YES/NO]
- Test 3.3 (Config): § 4 referenced? [YES/NO]

Success rate: [X/3] = _____%

Navigation Table Tests (Test 4):
- Test 4.1 (New stage): Table used? [YES/NO]
- Test 4.2 (Config mod): Table used? [YES/NO]
- Test 4.3 (Logging): Table used? [YES/NO]

Success rate: [X/3] = _____%

Overall Success Rate: [X/6] = _____%
```

---

### Step 2: Apply Decision Criteria

**Decision Matrix:**

| Overall Success Rate | Decision | Action |
|---------------------|----------|---------|
| ≥ 67% (4/6 or better) | ✅ GO | Proceed to Phase 1 with layered approach |
| 50-66% (3/6) | 🟡 CONDITIONAL | Simplify § notation, use more examples |
| < 50% (< 3/6) | ❌ NO-GO | Use alternative: embed all rules inline |

**Your Decision:** [PENDING]

---

### Step 3: Document Your Decision

#### If GO ✅ (Success rate ≥ 67%)

**Findings:**
- Copilot successfully followed § references: [X/3] times
- Copilot successfully used navigation table: [X/3] times
- Overall success rate: [____%]

**Recommendation:**
Proceed to Phase 1 with the layered reference approach. The POC validates that:
1. Copilot can follow § notation to look up sections
2. Navigation tables are effective for routing
3. The two-tier approach (instructions + standards) will work

**Next steps:**
1. Remove POC test sections from copilot-instructions.md
2. Begin Phase 1: Extract critical standards (Week 1)
3. Target: 400 lines with § references

---

#### If CONDITIONAL 🟡 (Success rate 50-66%)

**Findings:**
- Copilot partially followed § references: [X/3] times
- Copilot partially used navigation table: [X/3] times
- Overall success rate: [____%]

**Recommendation:**
Modify the approach before proceeding:
1. Simplify § notation (make it more explicit)
2. Add inline examples alongside § references
3. Reduce reliance on navigation tables
4. Target: 500 lines (was 400)

**Modifications needed:**
- Instead of: "Consult § 2.6"
- Use: "Consult § 2.6 (StageIO Pattern) in DEVELOPER_STANDARDS.md"
- Add 2-3 line example inline

**Next steps:**
1. Update copilot-instructions.md with modified format
2. Re-test with 2 prompts to validate improvement
3. If improved: proceed to Phase 1
4. If not improved: switch to NO-GO approach

---

#### If NO-GO ❌ (Success rate < 50%)

**Findings:**
- Copilot rarely followed § references: [X/3] times
- Copilot rarely used navigation table: [X/3] times
- Overall success rate: [____%]

**Recommendation:**
ABORT layered approach. Switch to embedded approach:
1. Don't use § notation at all
2. Embed all critical rules directly in copilot-instructions.md
3. Include full code examples inline
4. Target: 800 lines (more content, no references)

**Alternative Plan:**
```
Phase 1 (Revised): Embed Top 10 Critical Rules
- No § references, all rules spelled out
- Complete code examples for each pattern
- No navigation tables, flat structure
- Estimated size: 800-1000 lines
```

**Trade-off:**
- Pro: Copilot will definitely read the rules (they're right there)
- Con: Longer file, harder to maintain, duplication with DEVELOPER_STANDARDS.md

**Next steps:**
1. Document NO-GO decision in PHASE_0_PROGRESS.md
2. Update COPILOT_INTEGRATION_PLAN.md with revised approach
3. Begin embedded Phase 1 (8 hours instead of original plan)

---

## Step 4: Update Documentation

**After making your decision, update these files:**

### 1. Update PHASE_0_PROGRESS.md

Add your test results to the "Test Results" section:
- Fill in all [YES/NO] answers
- Add your notes from each test
- Calculate success rates
- Document your GO/NO-GO decision

### 2. Commit Your Decision

```bash
# Remove the POC test sections from copilot-instructions.md
# (Delete the ## 🧪 POC TEST sections you added)

# Commit the decision
git add docs/PHASE_0_PROGRESS.md .github/copilot-instructions.md
git commit -m "Phase 0: POC testing complete - [GO/CONDITIONAL/NO-GO] decision

Test Results:
- § notation success: X/3 (___%)
- Navigation table success: X/3 (___%)
- Overall: X/6 (___%)

Decision: [Your decision here]
Next: [Your next steps here]"
git push
```

---

## Troubleshooting

### Problem: Copilot doesn't seem to read copilot-instructions.md

**Solution:**
- Make sure you saved the file
- Try restarting your IDE
- Try asking "What are the project standards?" first
- Check if Copilot has the right context (repository root)

### Problem: Copilot gives generic answers

**Solution:**
- Be more specific: "According to our project's copilot-instructions.md..."
- Reference the file explicitly: "I see § 2.6 mentioned in copilot-instructions..."
- Try Copilot Agent mode instead of Chat

### Problem: Can't tell if Copilot used the § notation

**Solution:**
- Ask follow-up: "Where did you find this pattern?"
- Check if the code matches what's in the § section
- If it uses the right pattern, count it as YES even if § not mentioned

---

## Expected Time Breakdown

| Activity | Time | Total |
|----------|------|-------|
| Setup (add test sections) | 5 min | 5 min |
| Test 3.1: Stage implementation | 8 min | 13 min |
| Test 3.2: Error handling | 6 min | 19 min |
| Test 3.3: Configuration | 6 min | 25 min |
| Test 4.1: New stage navigation | 6 min | 31 min |
| Test 4.2: Config navigation | 6 min | 37 min |
| Test 4.3: Logging navigation | 6 min | 43 min |
| Analyze results | 10 min | 53 min |
| Make decision | 10 min | 63 min |
| Document & commit | 7 min | 70 min |
| **Total** | | **~1 hour 10 min** |

---

## Success Tips

### 1. **Be Patient**
- Give Copilot time to read the instructions
- First response might not reference §, but second might

### 2. **Test Consistently**
- Use the exact prompts provided
- Don't add extra context that might bias results
- Test in the same session (don't restart between tests)

### 3. **Be Objective**
- If Copilot uses the right pattern but doesn't say "§ 2.6", count it as YES
- We care about behavior, not just explicit mentions
- Focus on: Does it follow the standard? Not: Did it cite the section?

### 4. **Document Everything**
- Copy/paste Copilot's full responses into PHASE_0_PROGRESS.md
- Note any surprises (good or bad)
- This data will help improve the integration plan

---

## After Testing

### If GO ✅
Proceed to Phase 1: Extract Critical Standards (Week 1)
- Target: 400 lines
- Use § notation confidently
- Include navigation tables

### If CONDITIONAL 🟡
Modify approach and re-test:
- Make § notation more explicit
- Add inline examples
- Re-run 2 tests to validate

### If NO-GO ❌
Switch to embedded approach:
- No § notation
- All rules inline
- Larger file (800 lines)

---

## Questions?

If anything is unclear during testing:
1. Check `docs/COPILOT_INTEGRATION_PLAN.md` for context
2. Review `docs/BASELINE_COMPLIANCE_METRICS.md` for what we're trying to fix
3. Reference `docs/developer/DEVELOPER_STANDARDS.md` to see what Copilot should be reading

---

**Good luck with testing!** 🧪

**Remember:** This POC is critical - it determines whether the 46-hour integration plan will work or if we need to pivot to an alternative approach.

---

**Last Updated:** December 2, 2025 21:36 UTC  
**Status:** READY FOR EXECUTION  
**Estimated Duration:** 1 hour 10 minutes
