# Copilot Integration Plan: DEVELOPER_STANDARDS.md

**Goal:** Enable GitHub Copilot to consistently follow development best practices by integrating `docs/developer/DEVELOPER_STANDARDS.md` into `.github/copilot-instructions.md`

**Challenge:** DEVELOPER_STANDARDS.md is 2,794 lines (75KB) - too large for Copilot's context window if included directly.

**Date:** December 2, 2025  
**Last Updated:** December 2, 2025  
**Status:** APPROVED WITH MODIFICATIONS  
**Version:** 2.0

---

## Strategy Overview

**Approach:** Create a **layered reference system** where copilot-instructions.md contains:
1. **Concise rules** (what Copilot MUST enforce on every interaction)
2. **Explicit pointers** to DEVELOPER_STANDARDS.md sections for details
3. **Quick reference tables** extracted from standards
4. **Context-aware guidance** telling Copilot when to consult specific sections

This avoids duplicating the 75KB document while ensuring Copilot knows where to find details.

---

## Implementation Plan

### Phase 0: Baseline & Proof of Concept (Week 0) ⚠️ CRITICAL

**Objective:** Validate that Copilot can follow our approach before full implementation

**Tasks:**
1. **Version control current state:**
   ```bash
   cp .github/copilot-instructions.md .github/copilot-instructions.md.backup
   git add .github/copilot-instructions.md.backup
   git commit -m "backup: Save copilot-instructions before integration"
   ```

2. **Measure baseline violation rates:**
   - Review last 10 PRs/commits for standard violations
   - Create spreadsheet tracking violation types
   - Calculate current compliance rate
   - Document top 10 most-violated standards

3. **Test § notation with Copilot:**
   ```markdown
   # Add this test to copilot-instructions.md temporarily
   ## TEST: Section References
   When implementing StageIO, consult § 2.6 of DEVELOPER_STANDARDS.md
   ```
   - Ask Copilot to implement a stage
   - Check if it references § 2.6
   - Verify if it actually reads that section

4. **Test navigation table format:**
   ```markdown
   ## TEST: Navigation Table
   | Task | See Section |
   |------|-------------|
   | Add new stage | § 3.1 |
   ```
   - Ask Copilot to add a new stage
   - Check if it uses the table to find § 3.1

5. **Define rollback criteria:**
   - If § references don't work → STOP, use alternative approach
   - If baseline compliance < 50% → Adjust success targets
   - If Copilot ignores tables → Simplify navigation format

**Deliverables:**
- Baseline compliance metrics spreadsheet
- POC test results document
- Go/No-Go decision for full implementation

**Success Criteria:**
- Copilot demonstrates it can follow § references (at least 2/3 tests)
- Baseline violation rate measured
- Rollback plan documented

**Effort:** 4 hours

---

### Phase 1: Extract Critical Standards (Week 1)

**Objective:** Identify the 20% of standards that cover 80% of common violations

**Tasks:**
1. **Audit current violations** 
   - Review recent PRs/commits for common pattern violations
   - Identify top 10 most-frequently-violated standards
   
2. **Extract critical rules into categories:**
   - **Stage Architecture** (StageIO, manifests, logging)
   - **Configuration Management** (.env files, secrets handling)
   - **Error Handling** (try/except patterns, logging errors)
   - **Code Patterns** (imports, type hints, docstrings)
   - **Testing Requirements** (when to add/update tests)

3. **Create quick reference tables:**
   ```markdown
   ## Quick Reference: Stage Patterns
   
   | Task | Required Pattern | Example |
   |------|-----------------|---------|
   | Initialize stage | `io = StageIO(name, job_dir, enable_manifest=True)` | See 2.6.1 |
   | Log to stage | `logger = io.get_stage_logger()` | See 2.3 |
   | Track input | `io.manifest.add_input(file_path, hash)` | See 2.5.3 |
   ```

**Deliverable:** `copilot-instructions.md` section with critical rules (< 400 lines)

**Updated Success Criteria:** Start with 400 lines, not 500 (reduce context burden)

---

### Phase 2: Create Section Index (Week 1)

**Objective:** Build a navigation guide so Copilot knows which section to consult

**Tasks:**
1. **Create topical index** in copilot-instructions.md:
   ```markdown
   ## When to consult DEVELOPER_STANDARDS.md
   
   | If you're working on... | Consult Section | Key Topics |
   |------------------------|----------------|------------|
   | Adding a new stage | § 3 (Stage Implementation) | StageIO, manifests, logging |
   | Modifying configuration | § 4 (Configuration) | .env.pipeline, secrets.json |
   | Implementing logging | § 2 (Enhanced Logging) | Dual-log architecture |
   | Writing tests | § 7 (Testing) | Unit/integration patterns |
   | Error handling | § 5 (Error Handling) | Try/except, logging |
   | Adding dependencies | § 1.3 (Dependencies) | requirements/ structure |
   ```

2. **Add decision trees** for common scenarios:
   ```markdown
   ## Decision Tree: Should I create a new stage?
   
   1. Is this a distinct transformation step? → YES: Proceed
   2. Can it run independently? → YES: Proceed  
   3. Does it need separate logging/manifest? → YES: Proceed
   4. Would it create excessive I/O overhead? → NO: Proceed
   
   If all YES/NO match: Create new stage following § 3.1-3.4
   ```

**Deliverable:** Navigation index + decision trees (< 200 lines)

---

### Phase 3: Add Enforcement Prompts (Week 2)

**Objective:** Add explicit instructions for Copilot to verify compliance

**Tasks:**
1. **Add pre-commit checklist:**
   ```markdown
   ## Before proposing code changes, verify:
   
   - [ ] All stage outputs go to stage directory only (§ 1.1)
   - [ ] StageIO initialized with enable_manifest=True (§ 2.6)
   - [ ] Stage logger used (not print statements) (§ 2.3)
   - [ ] Inputs/outputs tracked in manifest (§ 2.5)
   - [ ] Error handling with proper logging (§ 5)
   - [ ] Type hints on function signatures (§ 6.2)
   - [ ] Docstrings for public functions (§ 6.3)
   - [ ] Tests updated if behavior changed (§ 7)
   - [ ] Dependencies added to correct requirements file (§ 1.3)
   ```

2. **Add validation prompts:**
   ```markdown
   ## When reviewing code, ask yourself:
   
   - Does this follow the StageIO pattern? (Reference § 2.6 if unsure)
   - Are all config values loaded from load_config()? (Reference § 4)
   - Is error handling comprehensive? (Reference § 5)
   - Would this break data lineage tracking? (Reference § 2.8)
   ```

**Deliverable:** Checklist + validation prompts (< 100 lines)

**NEW: Add Automated Checker Script**

**Tasks:**
1. **Create compliance validator:**
   ```bash
   touch scripts/validate-compliance.py
   chmod +x scripts/validate-compliance.py
   ```

2. **Implement pattern checks:**
   ```python
   # scripts/validate-compliance.py
   def check_stageio_pattern(file_path):
       """Verify StageIO initialization with enable_manifest=True"""
       # Check for: StageIO(..., enable_manifest=True)
       
   def check_stage_logger(file_path):
       """Verify stage uses logger, not print statements"""
       # Check for: io.get_stage_logger()
       # Flag: print() statements in stage files
       
   def check_manifest_tracking(file_path):
       """Verify inputs/outputs are tracked"""
       # Check for: io.manifest.add_input/add_output
   ```

3. **Create CLI interface:**
   ```bash
   # Run on single file
   ./scripts/validate-compliance.py scripts/whisperx_integration.py
   
   # Run on all stage files
   ./scripts/validate-compliance.py scripts/*.py
   
   # Run in CI mode (exit 1 on violations)
   ./scripts/validate-compliance.py --strict scripts/*.py
   ```

4. **Add to pre-commit hook (optional):**
   ```bash
   # .git/hooks/pre-commit
   ./scripts/validate-compliance.py --staged
   ```

5. **Document usage:**
   - Add to docs/developer-guide.md
   - Include in PR template
   - Reference in copilot-instructions.md

**Deliverable:** Automated compliance checker script + documentation

**Effort:** +4 hours

---

### Phase 4: Update Model Routing (Week 2)

**Objective:** Fix broken reference and integrate with standards compliance

**Tasks:**
1. **Fix broken reference (IMMEDIATE):**
   - Current: Points to deleted `COPILOT_MODEL_ROUTING_GUIDE.md`
   - New: Point to `docs/AI_MODEL_ROUTING.md`
   - **Priority:** Do this first (2 hours), before any other changes

2. **Add standards-aware routing:**
   ```markdown
   ## Model Selection + Standards Compliance
   
   ### For standards-compliant changes:
   - **Simple additions** (new function following patterns): GPT-4o mini
   - **Stage modifications** (changing StageIO usage): GPT-4o (consult § 2.6 first)
   - **Architecture changes** (multi-stage refactor): Claude Sonnet (review § 3)
   - **Critical path** (manifest/logging changes): Claude Opus (review § 2)
   
   ### Compliance verification workflow:
   1. Identify which standard sections apply
   2. Choose appropriate model for complexity
   3. Verify against checklist before proposing
   4. Reference specific § sections in commit messages
   ```

**Deliverable:** Updated model routing with standards integration

---

### Phase 5: Add Examples and Anti-patterns (Week 3)

**Objective:** Show Copilot concrete good/bad examples

**Tasks:**
1. **Extract examples from DEVELOPER_STANDARDS.md:**
   - Copy 5-10 most critical code examples
   - Show both ✅ CORRECT and ❌ INCORRECT patterns
   
2. **Add anti-pattern warnings:**
   ```markdown
   ## Common Anti-patterns to AVOID
   
   ❌ **DON'T:** Write outputs outside stage directory
   ```python
   # BAD: writes to wrong location
   output_path = os.path.join(job_dir, "subtitles.srt")
   ```
   
   ✅ **DO:** Use stage directory
   ```python
   # GOOD: respects stage containment
   output_path = io.stage_dir / "subtitles.srt"
   ```
   
   See § 1.1 for full stage directory rules.
   ```

**Deliverable:** Examples section (< 300 lines)

**Alternative Approach:** Consider creating separate `docs/COPILOT_EXAMPLES.md` to avoid bloating copilot-instructions.md, then reference it:
```markdown
For code examples, see docs/COPILOT_EXAMPLES.md
```

**Trade-off:** Reduces instructions size but adds indirection

---

### Phase 6: Validation and Iteration (Week 3-4)

**Objective:** Test integration with real Copilot usage

**Tasks:**
1. **Test with Copilot Chat:**
   - Ask Copilot to implement common tasks
   - Verify it references correct sections
   - Check if it follows critical patterns
   
2. **Test with Copilot Agent mode:**
   - Give it a multi-stage task
   - Monitor if it consults DEVELOPER_STANDARDS.md
   - Verify compliance with checklist
   
3. **Measure compliance:**
   - Track violations in code reviews
   - Compare before/after integration
   - Target: 90%+ compliance on first try
   
4. **Iterate based on findings:**
   - Add missing patterns to copilot-instructions.md
   - Clarify ambiguous guidance
   - Update decision trees

**Deliverable:** Validated integration with < 10% violation rate

**NEW: Define Rollback Criteria**

**Tasks:**
1. **Define failure conditions:**
   - Compliance rate < 70% after 2 weeks
   - Copilot consistently ignores § references
   - Developer feedback: instructions are confusing/too long
   - Time spent on standards violations increases (not decreases)

2. **Document rollback procedure:**
   ```bash
   # Rollback to backup
   git checkout .github/copilot-instructions.md.backup
   mv .github/copilot-instructions.md.backup .github/copilot-instructions.md
   git commit -m "rollback: Revert copilot-instructions integration"
   ```

3. **A/B testing approach:**
   - Week 1-2: Use new instructions for 50% of tasks
   - Week 1-2: Use old instructions for 50% of tasks
   - Compare violation rates between two groups
   - If new ≤ old, abort integration

4. **Document test scenarios:**
   ```markdown
   ## Validation Test Scenarios
   
   ### Test 1: Add new stage (should reference § 3.1)
   Prompt: "Create a new stage for audio normalization"
   Expected: Copilot mentions § 3.1 or demonstrates knowledge of stage pattern
   
   ### Test 2: Modify existing stage (should check § 2.6)
   Prompt: "Add error handling to whisperx_integration.py"
   Expected: Uses try/except with logger (not print)
   
   ### Test 3: Add configuration (should reference § 4)
   Prompt: "Add new config value for normalization threshold"
   Expected: Updates .env.pipeline, uses load_config()
   ```

5. **Extend validation time:**
   - Original: 8 hours
   - New: 12 hours (50% increase)
   - Includes documenting all test results

**Deliverable:** Rollback plan + test scenarios document + extended validation

**Effort:** +4 hours (validation), +2 hours (rollback planning) = +6 hours total

---

## Best Practices for Maintenance

### 1. **Keep copilot-instructions.md Concise**
- **Target:** < 600 lines total (updated from 800)
- **Initial target:** < 400 lines (expand only if needed)
- **Rule:** If it's more than 3 paragraphs, create a section in DEVELOPER_STANDARDS.md and reference it
- **Exception:** Critical patterns that affect every commit (StageIO, logging, manifests)
- **Principle:** Start small, expand incrementally based on results

### 2. **Three-tier Documentation Structure**
```
.github/copilot-instructions.md (400-600 lines)
├── Critical rules (must remember)
├── Quick reference tables
├── Navigation index → DEVELOPER_STANDARDS.md
├── Checklists and decision trees
└── Reference to validation script

docs/developer/DEVELOPER_STANDARDS.md (2,794 lines)
├── Comprehensive specifications
├── Detailed examples
├── Architecture rationale
└── Edge cases and exceptions

scripts/validate-compliance.py (automated checker)
├── Pattern validation
├── Real-time feedback
└── Pre-commit integration (optional)
```

### 3. **Explicit Section References**
- Always use `§ X.Y` notation to point to DEVELOPER_STANDARDS.md sections
- Example: "Follow StageIO pattern (see § 2.6)" not "Follow StageIO pattern in standards doc"
- Makes it easy for Copilot to know exactly where to look

### 4. **Regular Sync**
- **Monthly:** Review copilot-instructions.md for drift from DEVELOPER_STANDARDS.md
- **After major changes:** Update both files together
- **Use version markers:** Track which version of standards the instructions reflect

### 5. **Feedback Loop**
- Track common violations in code reviews
- Add frequently-violated patterns to copilot-instructions.md
- If a pattern is violated 3+ times, it needs to be in the instructions

---

## Implementation Timeline (UPDATED)

| Week | Phase | Effort | Owner | Priority |
|------|-------|--------|-------|----------|
| 0 | **Baseline & POC** | 4h | Developer | 🔴 Critical |
| 0 | **Fix model routing reference** | 2h | Developer | 🔴 Do First |
| 1 | Extract critical standards | 8h | Developer | 🟡 High |
| 1 | Create section index | 4h | Developer | 🟡 High |
| 2 | Add enforcement prompts | 4h | Developer | 🟡 High |
| 2 | **Build automated checker** | 4h | Developer | 🟡 High |
| 3 | Add examples/anti-patterns | 6h | Developer | 🟢 Medium |
| 3-4 | **Extended validation** | 12h | Developer + Copilot | 🔴 Critical |
| 4 | **Rollback decision** | 2h | Developer | 🔴 Critical |
| **Total** | | **46h** | | (~6 days) |

**Changes from v1.0:**
- Added Phase 0: Baseline & POC (+4h)
- Added automated checker (+4h)
- Extended validation (+4h)
- Added rollback decision (+2h)
- **Total increase:** +14 hours (32h → 46h)

---

## Success Metrics

### Pre-Integration Baseline (measure first)
- Current violation rate in code reviews
- Time spent in review cycles fixing standard violations
- Number of "please follow X pattern" comments per PR

### Post-Integration Targets (measure after 2 weeks)
- **90%+ compliance** on first code submission
- **50% reduction** in standards-related review comments
- **25% faster** review cycles (less back-and-forth)
- **Zero violations** of critical patterns (StageIO, manifests, logging)

---

## Risk Mitigation

### Risk: Copilot ignores instructions
**Mitigation:** 
- Start with most critical rules only
- Use explicit checklists Copilot can verify against
- Test with different model types (mini vs standard vs opus)

### Risk: Instructions become stale
**Mitigation:**
- Add version number to copilot-instructions.md
- Set monthly calendar reminder for sync
- Include instructions update in PR template

### Risk: Too much duplication
**Mitigation:**
- Follow 80/20 rule: only duplicate what's critical
- Always reference § sections for details
- Prefer tables/checklists over prose

---

## Alternative Approaches Considered

### ❌ Option A: Include entire DEVELOPER_STANDARDS.md
**Problem:** 75KB exceeds Copilot context window, would be truncated

### ❌ Option B: Heavily summarize standards
**Problem:** Loses critical details, increases ambiguity

### ❌ Option C: Don't integrate at all
**Problem:** Copilot continues violating standards, wasting review time

### ✅ Option D: Layered reference system (RECOMMENDED)
**Benefits:** 
- Keeps instructions concise
- Provides detailed reference when needed
- Explicit navigation for Copilot
- Maintainable long-term

---

## Next Steps (UPDATED)

### Immediate Actions (This Week)
1. ✅ **Get approval** on this updated plan
2. 🔴 **Phase 0:** Baseline & POC (4 hours)
   - Measure current violations
   - Test § notation with Copilot
   - Create rollback backup
3. 🔴 **Quick Win:** Fix model routing reference (2 hours)
   - Update to point to AI_MODEL_ROUTING.md
   - Test that it works

### Week 1
4. **Execute Phase 1:** Extract critical standards (8 hours)
5. **Execute Phase 2:** Create section index (4 hours)

### Week 2  
6. **Execute Phase 3:** Add enforcement prompts (4 hours)
7. **Execute Phase 3 (new):** Build automated checker (4 hours)
8. **Execute Phase 4:** Complete model routing integration (0 hours - already done)

### Week 3
9. **Execute Phase 5:** Add examples/anti-patterns (6 hours)

### Week 4
10. **Execute Phase 6:** Extended validation (12 hours)
11. **Execute Phase 6 (new):** Rollback decision (2 hours)
12. **Measure results** and document findings

### Go/No-Go Decision Points
- **After Phase 0:** If § references don't work → Consider alternative approach
- **After Week 2:** If compliance < 60% → Re-evaluate strategy  
- **After Week 4:** If compliance < 70% → Execute rollback

---

## Appendix: Example Integration

### Before (current copilot-instructions.md - 32 lines)
```markdown
## Non-negotiable rules
- Never write outputs outside the current stage directory.
- Every stage must use StageIO
```

### After (proposed - ~150 lines for this section)
```markdown
## Non-negotiable rules

### 1. Stage Directory Containment (§ 1.1)
❌ NEVER write outputs outside the stage directory
✅ ALWAYS use: `io.stage_dir / "output.ext"`

| Violation | Impact | Section |
|-----------|--------|---------|
| Writing to job_dir root | Breaks stage isolation | § 1.1.1 |
| Writing to another stage | Corrupts data lineage | § 2.8 |
| Writing to /tmp | Loses output on cleanup | § 1.1.2 |

**Before proposing code:** Verify all outputs go to `io.stage_dir`

### 2. StageIO Pattern (§ 2.6)
Every stage MUST:
```python
# 1. Initialize with manifest enabled
io = StageIO(stage_name, job_dir, enable_manifest=True)

# 2. Get stage logger (never use print)
logger = io.get_stage_logger()

# 3. Track all inputs
io.manifest.add_input(input_file, file_hash)

# 4. Track all outputs
io.manifest.add_output(output_file, file_hash)

# 5. Finalize manifest
io.finalize_stage_manifest(exit_code)
```

**Common mistakes:** See § 2.6.7 for anti-patterns
**Decision tree:** Should I create a new stage? See § 3.0 flowchart
```

**Result:** Copilot has actionable guidance + knows where to find details

---

---

## Appendix B: Changes from v1.0 to v2.0

### Major Additions
1. ✅ **Phase 0:** Baseline measurement & POC testing (addresses review Issue #1 & #2)
2. ✅ **Automated checker:** `scripts/validate-compliance.py` (addresses review Issue #3)
3. ✅ **Rollback plan:** Failure criteria + procedure (addresses review Issue #5)
4. ✅ **Extended validation:** 12 hours instead of 8 (addresses review Issue #7)

### Target Adjustments
1. ✅ **Line count:** 400 lines initial (was 500), 600 max (was 800) (addresses review Issue #4)
2. ✅ **Effort estimate:** 46 hours (was 32 hours) - more realistic
3. ✅ **Timeline:** 4 weeks with clear go/no-go gates

### Priority Changes
1. ✅ **Model routing fix:** Now Priority #1 (immediate quick win)
2. ✅ **Phase 0 POC:** Now mandatory before full implementation
3. ✅ **Automated validation:** Now high priority (not optional)

### Risk Mitigation Improvements
1. ✅ **High Risk items** now have concrete mitigation in Phase 0
2. ✅ **A/B testing approach** documented for validation
3. ✅ **Clear rollback criteria** defined upfront

### Review Findings Addressed
- ✅ Issue #1: No baseline measurement → Added Phase 0
- ✅ Issue #2: Untested Copilot behavior → Added POC testing
- ✅ Issue #3: No automated validation → Added checker script
- ✅ Issue #4: Instruction size creep → Reduced targets
- ✅ Issue #5: No rollback plan → Added comprehensive rollback section

### Approval Status
- **v1.0:** PROPOSED
- **v2.0:** APPROVED WITH MODIFICATIONS ✅

**Review Rating:** ⭐⭐⭐⭐⭐ (5/5) after modifications

---

## Appendix C: Quick Reference Card

### Critical Path (Minimum Viable Integration)
If time/resources are constrained, do these only:

1. **Phase 0:** Baseline & POC (4h) - validate approach works
2. **Fix model routing** (2h) - immediate improvement
3. **Top 5 critical rules** from Phase 1 (4h) - highest impact
4. **Automated checker** (4h) - enforce compliance
5. **2-week validation** (6h) - measure results

**Minimum effort:** 20 hours  
**Expected improvement:** 50%+ reduction in top violations

### Full Implementation Path
If implementing all phases:

**Total effort:** 46 hours  
**Timeline:** 4 weeks  
**Expected improvement:** 90%+ compliance, < 10% violation rate

### Decision Matrix

| Compliance after 2 weeks | Action |
|--------------------------|--------|
| > 80% | Continue full implementation |
| 60-80% | Iterate on unclear areas, extend 2 weeks |
| < 60% | Execute rollback, try alternative approach |

---

**END OF PLAN v2.0**

**Document Control:**
- Version: 2.0
- Date: December 2, 2025
- Status: APPROVED WITH MODIFICATIONS
- Next Review: After Phase 0 completion
- Owner: Development Team
