# Compliance Report — Developer Guide Conformance

Summary
- This report summarizes adherence to the project’s development standards listed in docs/developer-guide.md.
- It evaluates code and docs for idempotence, per-stage manifests, CLI consistency, logging, MPS/demucs handling, testing, and CI coverage.

Methodology
- Reviewed pipeline runner and stage wrappers for manifest write + skip logic.
- Reviewed quickstart script (test-glossary-quickstart.sh) for CLI flags, device detection, demucs venv handling.
- Reviewed docs/ for clarity and discoverability.
- Reviewed CI (GH Actions) changes for caching & repeat-run tests.

Key findings
- Good: StageRunner + manifest helpers exist and included in pipeline/runner.py.
- Good: Structured logs for stage events have been added (stage_skipped, stage_running, etc.).
- Partial: Not all stage executors explicitly return outputs or write manifests (some rely on scanning).
- Partial: Script-level flag compatibility handling exists, but runner CLI inconsistent across scripts (some flags rely on env fallback).
- Actionable: Quickstart script uses venv detection and demucs venv; however, script still uses some bare 'python' invocations in places (mostly replaced).
- Improvement required: Ensure StageRunner is invoked for all stages; ensure compute_inputs_checksum is used consistently; ensure per-stage manifests are produced across all 12 stages.

Risk areas
- Cache correctness: Missing manifests or missing param entries (e.g., clip-start/clip-end, device) can produce incorrect cache hits/misses.
- CI reliability: Running heavy stages in CI (Demucs) may fail without wheels. CI must use venv caching and small slices or stub heavy steps.
- Cross-device avoidance: Must ensure job dir naming & manifest params include device so caches are device-specific.

Scorecard (high-level)
- Stage manifest presence: Partial
- StageRunner wrapping: Partial
- CLI coverage (--from/--to/stages/force): Implemented in runner; other scripts fallback to env.
- Structured logging: Implemented
- Demucs venv handling: Implemented (auto-install support) but must be validated in CI (Apple Silicon).
- Tests: Unit tests for checksum & StageRunner exist; need more integration tests.

Short-term remediation (1–2 days)
- Enforce StageRunner usage on all stages; add StageRunner wrapper in all stage executors.
- Ensure each stage writes a manifest.json with required fields and includes params: device, clip_start/clip_end, demucs_venv.
- Update quickstart script to use $PYTHON_BIN consistently.

Medium-term remediation (1–2 weeks)
- Add CI pipeline to:
  - Run quickstart for a short clip in baseline / glossary / cache to validate SKIPPED events & manifest consistency.
  - Validate demucs-venv usage and skip heavy installs in CI by using pip cache & prebuilt wheels.
- Add a manifest schema validator and unit tests for schema compliance.

Long-term remediation (2–4 weeks)
- Add pre-commit hooks, ShellCheck, Python linters, and a test that ensures no stage writes into sibling stage directories.
- Clean up deprecated scripts and old docs to reduce confusion.
- Add developer onboarding doc with a diagram and main flow.

File & Doc cleanup suggestions
- Audit repo files for deprecated scripts (e.g., outdated wrappers under scripts/), mark them as deprecated & list owners, and remove after a two-week retention policy.
- Consolidate documentation into an index with logical flow (QUICKSTART → DEVELOPER GUIDE → OPTIMIZATION ROADMAP → COMPLIANCE → CONTRIBUTING).
- Remove duplicate docs, e.g., repeated Quickstart content across README or other docs if present.

Success criteria for 100% compliance
- All pipeline stages write a manifest.json with required fields and StageRunner decides skip/run automatically.
- CLI default full-run uses StageRunner manifests to skip already completed stages.
- Quickstart verifies manifest timestamps & structured SKIPPED events every run.
- CI automatically tests a minimal end-to-end run and observes the expected SKIPPED behavior.
- Developer guidance exists (CONTRIBUTING.md, Developer Guide + Index).

Owner & Timeline
- Short-term: implement StageRunner enforcement and manifest writes — 1 week (Owner: pipeline/owner).
- Medium-term: CI tests and pip wheel caching changes — 2 weeks (Owner: CI).
- Long-term: cleanup, docs consolidation, and pre-commit — 4 weeks (Owner: docs/maintainer).

