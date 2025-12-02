# Copilot Model Routing & Developer Guide (in-repo playbook)

**Goal:** Help GitHub Copilot (and you) consistently pick the *right* chat model for the task—balancing **speed**, **premium-request cost**, and **correctness**—while keeping changes safe for this repo’s **multi-stage pipeline** architecture.

**Recommended location in repo:** `docs/COPILOT_MODEL_ROUTING_GUIDE.md`  
*(Copilot can read this file during work; reference it from `.github/copilot-instructions.md`.)*

---

## 0) Quick start (the default workflow)

### The 3‑step loop (Plan → Patch → Review)
1) **Plan** with a strong reasoning model (cheap if possible).
2) **Patch** with a code-specialist model when changes span multiple files.
3) **Review** with a careful reviewer model before merging.

### Default routing (safe + economical)
- **Default chat:** **OpenAI GPT‑4.1** (general purpose)
- **Fast iteration / boilerplate:** **OpenAI GPT‑5 mini** or **Raptor mini**
- **Large multi-file patch:** **OpenAI GPT‑5‑Codex** (or **GPT‑5.1‑Codex**)  
- **Hard reasoning / tricky bugs:** **OpenAI GPT‑5** or **Claude Sonnet 4.5**
- **Largest refactor / architecture:** **Claude Opus** (use sparingly)

> **Premium-request hygiene:** Use the lowest-cost model that can do the job. Escalate only when stuck or risk increases.

---

## 1) Repo-specific constraints Copilot must respect

This repository behaves like a **staged pipeline** (Python + Bash) with **stage directories, per-stage logs, and manifests**. The highest-risk mistakes are **invariant breaks** across stages.

### Non‑negotiable repo rules
- **Never write outputs outside the stage directory.**
- **Stages must be idempotent** (safe to re-run) or clearly guarded.
- **Update manifests consistently** when inputs/outputs change.
- **Avoid dependency drift:** do not “just add packages.” Update the correct file under `requirements/`.
- **Avoid breaking bootstrap:** `bootstrap.sh` creates multiple venvs; do not assume a single environment.
- **No secrets:** never print sensitive config/tokens in logs.

**Add these constraints to prompts** (copy/paste):
> “Do not write outputs outside the stage directory. Use StageIO + stage manifests. Write logs to `stage.log`. Update tests + docs.”

---

## 2) Model catalog (what each model is best at)

### OpenAI
**OpenAI GPT‑4.1**
- Best for: day-to-day Q&A, small edits, reading/understanding unfamiliar code, explaining errors.
- Avoid for: giant refactors where you need a single coherent multi-file patch.

**OpenAI GPT‑5 mini**
- Best for: fast iteration, boilerplate, small functions, test scaffolding, doc edits.
- Avoid for: subtle pipeline correctness (resume logic, manifest invariants, multi-env issues).

**OpenAI GPT‑5**
- Best for: hardest bugs, pipeline invariants, deep debugging across stages, “why is this flaky?”
- Avoid for: low-value chores.

**OpenAI GPT‑5‑Codex (Preview)**
- Best for: multi-file implementation work (feature + tests + refactor), CI fixes, repetitive edits.
- Works best when you provide: file list + acceptance criteria + “do not change” constraints.

**OpenAI GPT‑5.1 (Preview)**
- Best for: second opinion on complex reasoning; careful review of big diffs.

**OpenAI GPT‑5.1‑Codex (Preview)**
- Best for: large migrations/refactors across many modules.

**OpenAI GPT‑5.1‑Codex‑Mini (Preview)**
- Best for: medium refactors and “batch edits” while conserving premium usage.

**Raptor mini (Preview)**
- Best for: quick low-stakes edits, fast drafts, lightweight code generation.

### Anthropic Claude
**Claude Haiku 4.5**
- Best for: docs/PR summaries, turning notes into checklists, quick narrative explanations.

**Claude Sonnet 4**
- Best for: careful code review, refactor guidance, test strategy improvements.

**Claude Sonnet 4.5**
- Best for: higher-accuracy planning/reasoning, nuanced review, safer refactor design.

**Claude Opus 4.1 / Opus 4.5 (Preview)**
- Best for: toughest architecture work and cohesive plans for major changes.
- Use sparingly (expensive).

### Google Gemini
**Gemini 2.5 Pro**
- Best for: alternative perspective on architecture and tradeoffs; structured specs.

**Gemini 3 Pro (Preview)**
- Best for: experimentation and second opinions (treat as draft).

### xAI
**Grok Code Fast 1**
- Best for: very fast patch generation, repetitive edits, quick CI/script fixes.
- Avoid for: subtle correctness changes unless followed by a stronger review model.

---

## 3) Routing algorithm (how to pick a model)

### Step A — Classify the task
Pick ONE category:

1) **Small change** (≤ 1 file, ≤ 50 LOC, low risk)  
2) **Medium change** (2–5 files OR 50–300 LOC OR medium risk)  
3) **Large change** (≥ 6 files OR > 300 LOC OR high risk)  
4) **Investigation** (debugging, analysis, understanding a failure)  
5) **Documentation / comms** (README/docs/PR narrative)

### Step B — Determine risk level
- **High risk** if it touches: stage boundaries, manifests, resume/retry logic, dependency/venv bootstrap, CI, file paths/output locations.
- **Medium risk** if it changes core scripts, CLI args, configs, or test harness.
- **Low risk** if purely docs/comments/formatting.

### Step C — Choose model (decision tree)

#### 1) Investigation / debugging
- Start: **GPT‑4.1**
- If multi-stage reasoning needed: **GPT‑5** or **Sonnet 4.5**
- If still stuck: **Opus** (sparingly)

#### 2) Small change (low risk)
- Start: **GPT‑4.1** or **GPT‑5 mini**
- If code-heavy but still small: **Raptor mini** or **Grok Code Fast 1**
- Review: **GPT‑4.1**

#### 3) Medium change (or medium risk)
- Plan: **Sonnet 4** / **Sonnet 4.5** / **GPT‑5**
- Patch: **GPT‑5.1‑Codex‑Mini** or **GPT‑5‑Codex**
- Review: **Sonnet 4** or **GPT‑5**

#### 4) Large change (high risk)
- Plan: **Sonnet 4.5** or **GPT‑5**
- Patch: **GPT‑5‑Codex** or **GPT‑5.1‑Codex**
- Final review: **Sonnet 4.5** (use **Opus** only if architecture is changing)

#### 5) Docs / comms / PR summaries
- Draft: **Haiku 4.5** or **GPT‑4.1**
- Refine: **Sonnet 4** if you need more rigor

---

## 4) Repo-aware playbooks (common tasks)

### A) Adding a new pipeline stage
**Best model sequence**
1) Plan: **Sonnet 4.5** (or **GPT‑5**)  
2) Patch: **GPT‑5‑Codex**  
3) Review: **Sonnet 4** (or **GPT‑5**)

**Acceptance criteria**
- Outputs only inside stage dir
- `stage.log` created/used
- Manifest updated with inputs/outputs/state
- Stage idempotent or guarded
- Tests validate output paths + manifest keys
- Docs updated if CLI/config changes

### B) Fixing CI workflow drift / repo hygiene
**Best model sequence**
- Patch fast: **Grok Code Fast 1** or **GPT‑5.1‑Codex‑Mini**
- Review: **Sonnet 4** or **GPT‑4.1**

### C) Debugging flaky behavior (GPU/MPS/Torch/WhisperX)
**Best model sequence**
- Investigation: **GPT‑5** or **Sonnet 4.5**
- Patch: **GPT‑5‑Codex** if multi-file
- Review: **GPT‑5** (focus on edge cases)

### D) Refactoring stage manifests / resume logic
**Best model sequence**
- Plan: **Sonnet 4.5** or **GPT‑5**
- Patch: **GPT‑5.1‑Codex**
- Final review: **Sonnet 4.5** (use **Opus** only if architecture changes materially)

---

## 5) Prompt templates (what Copilot should do)

### Plan prompt (medium/large tasks)
> “Propose a minimal change plan for {goal}.  
> Constraints: stage-dir containment, manifest correctness, no new deps unless necessary, update tests + docs.  
> Output: (1) files, (2) steps, (3) risks, (4) test plan.”

### Patch prompt (Codex models)
> “Implement the plan. Touch only the listed files.  
> Do not write outputs outside stage directories.  
> Ensure manifests/logging are correct.  
> Add/extend pytest tests.  
> Provide a concise summary of changes.”

### Review prompt (Sonnet/GPT‑5)
> “Review this diff for: path safety, manifest correctness, idempotency, dependency drift, and CI impact.  
> List concrete issues and exact fixes.”

---

## 6) Escalation rules (control premium usage)

Escalate only when:
- You tried **2 iterations** and the model is stuck/contradictory.
- The change becomes **cross-file** and needs coherent edits.
- You enter **high-risk areas** (manifests, resume logic, CI, dependencies).

Escalation ladder:
1) GPT‑4.1 / GPT‑5 mini  
2) Grok Code Fast 1 / GPT‑5.1‑Codex‑Mini  
3) GPT‑5‑Codex / Sonnet 4  
4) GPT‑5 / Sonnet 4.5  
5) Opus (last resort)

---

## 7) Definition of Done (solo dev checklist)

Before merging:
- [ ] Outputs only inside stage directories
- [ ] Manifest updated & consistent
- [ ] `stage.log` present and meaningful
- [ ] Tests updated/added; `pytest -q` passes
- [ ] Docs updated if behavior/flags/config changed
- [ ] CI workflow still matches repo structure
- [ ] No secrets printed

---

## 8) Wire it into Copilot
1) Add this file at: `docs/COPILOT_MODEL_ROUTING_GUIDE.md`
2) In `.github/copilot-instructions.md`, add a line:
   - “Consult `docs/COPILOT_MODEL_ROUTING_GUIDE.md` for model routing based on task size/risk.”

That’s it—Copilot can use this as the repo’s “policy” for model selection and safe workflow execution.
