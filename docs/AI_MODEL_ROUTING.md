# AI Model Routing (Copilot Chat) — Subtitle Accuracy Roadmap Playbook

**Purpose:** This document is the **source of truth** for choosing a Copilot Chat model (and workflow) when working on this repository, especially tasks tied to **SUBTITLE_ACCURACY_ROADMAP.md**.

**Audience:** Developers using GitHub Copilot Chat / Agent mode / Code review in this repo.

**Primary goals**
- Improve subtitle accuracy and reduce hallucinations (see roadmap success targets).  
- Keep changes safe for a **multi-stage pipeline** (stage dirs, manifests, logs).  
- **Maintain 90%+ standards compliance** (see DEVELOPER_STANDARDS.md).
- Minimize premium-request waste while preserving correctness.

**Related docs**
- Roadmap + acceptance criteria: `SUBTITLE_ACCURACY_ROADMAP.md`
- Copilot guardrails: `.github/copilot-instructions.md`
- **Developer standards:** `docs/developer/DEVELOPER_STANDARDS.md` ⭐ NEW
- **Compliance checker:** `scripts/validate-compliance.py` ⭐ NEW
- (Optional) Model routing guide (general): `docs/COPILOT_MODEL_ROUTING_GUIDE.md`

---

## 1) Non‑negotiable repo constraints (must be enforced in every prompt)

### Pipeline Integrity
1. **Stage directory containment (§ 1.1):** stage outputs must be written **only inside the stage directory** under the job dir.
2. **Manifest correctness (§ 2.5):** any input/output contract changes must be reflected in the stage manifest.
3. **Logging (§ 2.3):** stages must log to `stage.log` with start/end markers and key params (device/model/chunking). **Use logger, not print.**
4. **Idempotency:** re-running a stage should not corrupt outputs; if not possible, guard it explicitly.
5. **Dependency discipline (§ 1.3):** do not add packages ad-hoc; update the correct file under `requirements/`.
6. **No secrets:** never print tokens/credentials or sensitive config in logs or exceptions.

### Code Quality Standards ⭐ NEW
7. **Logger usage (§ 2.3):** Use `logger.info()` / `logger.error()`, NEVER `print()` - 60% baseline violation
8. **Import organization (§ 6.1):** Standard/Third-party/Local with blank lines - 100% baseline violation
9. **StageIO pattern (§ 2.6):** All stages must use `StageIO(..., enable_manifest=True)`
10. **Config usage (§ 4.2):** Use `load_config()`, NEVER `os.getenv()` or `os.environ[]`
11. **Type hints (§ 6.2):** Add type hints to function signatures
12. **Docstrings (§ 6.3):** Document public functions

**Paste this into prompts:**
> "Follow repo constraints: stage-dir containment, manifest correctness, stage.log logging (use logger not print), idempotent stages, no dependency drift, no secrets. Follow DEVELOPER_STANDARDS.md: § 2.3 (logger), § 6.1 (imports), § 2.6 (StageIO), § 4.2 (config)."

**Before committing, run:**
```bash
./scripts/validate-compliance.py your_file.py
```

---

## 2) Model selection: principle + escalation ladder

### Principle
Start with the **cheapest/fastest model** that can do the task **correctly**, then escalate only if:
- you hit complexity,
- the change becomes multi-file,
- you enter high-risk territory (manifests/resume logic/CI/dependencies),
- **standards compliance requires deep reasoning** ⭐ NEW,
- or you tried 2 iterations and are stuck.

### Escalation ladder (recommended)
1) **GPT‑4.1** (default understanding + small edits)  
2) **GPT‑5 mini** / **Raptor mini** (fast iteration)  
3) **Grok Code Fast 1** / **GPT‑5.1‑Codex‑Mini** (rapid patching, moderate cost)  
4) **GPT‑5‑Codex** / **GPT‑5.1‑Codex** / **Claude Sonnet 4/4.5** (large coherent changes)  
5) **GPT‑5** / **Claude Sonnet 4.5** (deep reasoning)  
6) **Claude Opus** (last resort; expensive; use for architecture rework)

> Use **Codex** models when you want a single coherent patch across multiple files + tests.
> Use **Sonnet 4.5** for standards-compliant refactoring ⭐ NEW

---

## 3) Routing algorithm (use this decision tree)

### Step A — classify task type
Choose one:
- **T1: Read/Explain** (understand code/roadmap/logs)
- **T2: Small change** (≤1 file, ≤50 LOC, low risk)
- **T3: Medium change** (2–5 files or 50–300 LOC or medium risk)
- **T4: Large change** (≥6 files or >300 LOC or high risk)
- **T5: Debug/Investigate** (root cause analysis, flake, perf)
- **T6: Docs/Comms** (PR descriptions, docs, checklists)
- **T7: Standards compliance** ⭐ NEW (fix logger/imports/StageIO violations)

### Step B — set risk (low/med/high)
High-risk if you touch:
- stage boundaries/output contracts
- manifests/resume/retry logic
- CI workflows
- dependency/venv/bootstrap logic
- **widespread standards violations (>10 files)** ⭐ NEW

### Step C — pick model + workflow
| Task | Low risk | Medium risk | High risk |
|---|---|---|---|
| T1 Read/Explain | GPT‑4.1 | Sonnet 4 | Sonnet 4.5 / GPT‑5 |
| T2 Small change | GPT‑5 mini / GPT‑4.1 | GPT‑4.1 | GPT‑4.1 + review Sonnet 4 |
| T3 Medium change | GPT‑5.1‑Codex‑Mini | GPT‑5‑Codex | Plan Sonnet 4.5 → Patch Codex → Review Sonnet 4 |
| T4 Large change | Plan Sonnet 4 → Patch Codex | Plan Sonnet 4.5 → Patch Codex | Plan GPT‑5/Sonnet 4.5 → Patch GPT‑5.1‑Codex → Final review Sonnet 4.5 (Opus only if architecture changes) |
| T5 Debug/Investigate | GPT‑4.1 | GPT‑5 / Sonnet 4.5 | GPT‑5 + Sonnet 4.5 review |
| T6 Docs/Comms | Haiku 4.5 / GPT‑4.1 | Sonnet 4 | Sonnet 4.5 |
| **T7 Standards fix** ⭐ | **GPT‑4.1** | **GPT‑5‑Codex** | **Sonnet 4.5** |

---

## 4) Roadmap-aware model playbooks (Phase 1 → Phase 5)

This section tells Copilot which models to use **by roadmap phase**, and what "done" looks like.

### Phase 1 — WhisperX configuration & confidence filtering
**Typical tasks**
- tune WhisperX params; validate configs; add confidence thresholds; reduce bad segments.

**Recommended models**
- Plan: **GPT‑4.1** (or **Sonnet 4** if designing new config structures)
- Patch: **GPT‑5.1‑Codex‑Mini** (short multi-file edits) or **GPT‑5‑Codex** (bigger refactor)
- Review: **GPT‑4.1** (plus **Sonnet 4** if stage boundaries changed)

**Definition of done**
- config validation added/updated
- a repeatable test (or smoke) proves the change improves metrics without regressions
- logs include key params; manifest captures config used
- **✅ Passes compliance checker (`./scripts/validate-compliance.py`)** ⭐ NEW
- **✅ Uses logger not print, organized imports, StageIO pattern** ⭐ NEW

### Phase 2 — Hallucination reduction (patterns + filters + tests)
**Typical tasks**
- implement/extend pattern remover; compression ratio filter; build regression suite; reduce false positives.

**Recommended models**
- Plan: **Sonnet 4.5** (pattern safety + edge cases)
- Patch: **GPT‑5‑Codex** (multi-file + tests)
- Review: **Sonnet 4** (focus on false-positive risk + test completeness)

**Definition of done**
- regression tests cover known hallucinations
- tests explicitly guard "zero false positives" for curated good cases
- metrics report shows reduction in hallucination-like segments
- **✅ Compliance checks pass** ⭐ NEW

### Phase 3 — Subtitle readability (merge + CPS + line breaking)
**Typical tasks**
- segment merging; reading speed metrics; max line length; stable output formatting.

**Recommended models**
- Plan: **GPT‑5** or **Sonnet 4.5** (tradeoffs + invariants)
- Patch: **GPT‑5.1‑Codex‑Mini** (batch edits) or **GPT‑5‑Codex** (large rewrites)
- Review: **Sonnet 4** (ensure deterministic output + tests)

**Definition of done**
- CPS targets measured; merge logic deterministic; tests for edge cases (long strings, punctuation, time gaps)
- **✅ Standards compliant code** ⭐ NEW

### Phase 4 — Glossary protection, validation, and learning
**Typical tasks**
- placeholder protection; translation validation; glossary compliance reports; suggest glossary additions.

**Recommended models**
- Plan: **Sonnet 4.5** (semantic pitfalls + false positive control)
- Patch: **GPT‑5‑Codex** (end-to-end wiring + tests)
- Review: **GPT‑5** (edge cases + correctness)

**Definition of done**
- glossary protected terms preserved through translation
- validator reports missing terms and confidence
- tests include "must preserve" examples; no regressions in translation output
- **✅ Follows § 4 (config), § 5 (error handling)** ⭐ NEW

### Phase 5 — Benchmarking and quality validation framework
**Typical tasks**
- unified benchmark harness; metrics dashboard JSON; "baseline vs branch" comparisons; CI integration.

**Recommended models**
- Plan: **GPT‑5** (system design) + optionally **Gemini 2.5 Pro** (second opinion)
- Patch: **GPT‑5.1‑Codex** (broad changes + plumbing)
- Review: **Sonnet 4.5** (architecture sanity + maintainability)

**Definition of done**
- reproducible benchmark command in docs
- stable metrics schema
- CI runs a fast subset; optional nightly full benchmark
- **✅ All code passes `validate-compliance.py --strict`** ⭐ NEW

---

## 5) Prompt templates Copilot should use (copy/paste)

### A) Plan prompt (required for medium/large/high-risk work)
> "Read `SUBTITLE_ACCURACY_ROADMAP.md` and identify the exact phase/task for {GOAL}.  
> Read `.github/copilot-instructions.md` and note the 5-question mental checklist at the top. ⭐ NEW  
> Propose a minimal plan with: files to change, exact functions/classes touched, risks, test plan, and **compliance considerations** (logger, imports, StageIO, config). ⭐ NEW  
> Constraints: stage-dir containment, manifest correctness, stage.log logging (use logger not print), idempotency, no dependency drift, no secrets.  
> Standards: § 2.3 (logger), § 6.1 (imports), § 2.6 (StageIO), § 4.2 (config)." ⭐ NEW

### B) Patch prompt (Codex / code-specialist models)
> "Implement the plan. Touch only listed files.  
> **Follow .github/copilot-instructions.md mental checklist:** use logger (not print), organize imports (Standard/Third-party/Local), use StageIO with enable_manifest=True, write to io.stage_dir only, use load_config(). ⭐ NEW  
> Preserve CLI compatibility unless explicitly asked.  
> Ensure stage outputs stay in stage dir; update manifest keys; add/extend pytest tests.  
> Provide the exact commands to run tests/smoke locally.  
> **Run compliance checker before finishing:** `./scripts/validate-compliance.py <files>`" ⭐ NEW

### C) Review prompt (Sonnet / GPT‑5)
> "Review the diff for: stage-dir containment, manifest and resume correctness, deterministic output, test completeness, and dependency drift.  
> **Also check standards compliance:** logger usage (§ 2.3), import organization (§ 6.1), StageIO pattern (§ 2.6), config usage (§ 4.2), type hints (§ 6.2), docstrings (§ 6.3). ⭐ NEW  
> Run mental check: Is print() used? Are imports organized? Is enable_manifest=True present? ⭐ NEW  
> List concrete problems and propose exact code-level fixes."

### D) Standards compliance prompt ⭐ NEW
> "Fix standards violations in {FILES}.  
> Priority #1: Replace all print() with logger.info/error (§ 2.3).  
> Priority #2: Organize imports into Standard/Third-party/Local groups with blank lines (§ 6.1).  
> Check: StageIO has enable_manifest=True (§ 2.6), config uses load_config() (§ 4.2).  
> Add type hints and docstrings if missing.  
> Verify with: `./scripts/validate-compliance.py {FILES}`"

---

## 6) "Stop conditions" (when to escalate models)
Escalate to a stronger (more expensive) model when:
- You cannot produce a complete plan with file-level precision.
- The change spans multiple file types (Python + Bash + docs + CI).
- You are touching manifests/resume logic or output contracts.
- You need a single coherent multi-file patch (switch to Codex).
- You have conflicting suggestions after 2 attempts.
- **You need to fix standards violations across >5 files (use Sonnet 4.5 or GPT-5-Codex)** ⭐ NEW

---

## 7) Operational checklist (enforced for every PR)
- [ ] Correct roadmap phase referenced in PR description
- [ ] Stage outputs only inside stage directories (§ 1.1)
- [ ] Manifest keys updated (inputs/outputs/config/version) (§ 2.5)
- [ ] `stage.log` includes key params
- [ ] **Uses logger, not print** (§ 2.3) ⭐ NEW
- [ ] **Imports organized properly** (§ 6.1) ⭐ NEW
- [ ] **StageIO with enable_manifest=True** (§ 2.6) ⭐ NEW
- [ ] **Config via load_config()** (§ 4.2) ⭐ NEW
- [ ] **Compliance checker passes:** `./scripts/validate-compliance.py` ⭐ NEW
- [ ] Tests added/updated; shows `pytest -q` (or `make test`) output
- [ ] Docs updated if behavior/flags changed
- [ ] No secrets or sensitive data exposed in logs

---

## 8) How to wire this into Copilot instructions

Already integrated in `.github/copilot-instructions.md` v3.2:

```md
## ⚡ Before You Respond
1. Will I use logger instead of print()? (§ 2.3)
2. Are imports organized Standard/Third-party/Local? (§ 6.1)
3. If stage: StageIO with enable_manifest=True? (§ 2.6)
4. Outputs going to io.stage_dir only? (§ 1.1)
5. Using load_config() not os.getenv()? (§ 4.2)

## 📍 Model Routing
Consult: docs/AI_MODEL_ROUTING.md before choosing models
```

---

## 9) Standards compliance metrics ⭐ NEW

**Baseline (before integration):** 56.4%
- Logger usage: 40%
- Import organization: 0%
- Type hints: 100% ✅
- Docstrings: 100% ✅
- Config usage: 100% ✅

**Target (with AI model routing + enforcement):** 90%+

**How to improve compliance:**
1. Use copilot-instructions.md mental checklist
2. Run `validate-compliance.py` before committing
3. Use Sonnet 4.5 for large-scale compliance fixes
4. Add compliance checks to CI/CD

**Track progress:**
```bash
# Check single file
./scripts/validate-compliance.py scripts/your_file.py

# Check all scripts
./scripts/validate-compliance.py scripts/*.py

# Strict mode for CI
./scripts/validate-compliance.py --strict scripts/*.py
```

---

## 10) Quick reference card ⭐ NEW

```
┌─────────────────────────────────────────────────────────┐
│ AI MODEL ROUTING + STANDARDS QUICK REFERENCE           │
├─────────────────────────────────────────────────────────┤
│ BEFORE STARTING:                                        │
│ 1. Read .github/copilot-instructions.md (5 questions)  │
│ 2. Check task type (T1-T7) + risk (low/med/high)      │
│ 3. Pick model from routing table (Section 3)          │
│                                                         │
│ WHILE CODING:                                           │
│ ✓ Use logger (not print)             - § 2.3          │
│ ✓ Organize imports (Std/3rd/Local)   - § 6.1          │
│ ✓ StageIO(enable_manifest=True)      - § 2.6          │
│ ✓ Write to io.stage_dir only         - § 1.1          │
│ ✓ Use load_config()                  - § 4.2          │
│                                                         │
│ BEFORE COMMITTING:                                      │
│ ✓ Run: ./scripts/validate-compliance.py file.py       │
│ ✓ Fix all critical violations                          │
│ ✓ Add tests if behavior changed                        │
│ ✓ Update manifest if I/O changed                       │
│                                                         │
│ MODEL SHORTCUTS:                                        │
│ • Small edits:           GPT-4.1                       │
│ • Multi-file changes:    GPT-5-Codex                   │
│ • Standards fixes:       Sonnet 4.5                    │
│ • Deep reasoning:        GPT-5 / Sonnet 4.5           │
└─────────────────────────────────────────────────────────┘
```

---

*Last updated:* 2025-12-02 (Phase 4: Standards compliance integrated)
