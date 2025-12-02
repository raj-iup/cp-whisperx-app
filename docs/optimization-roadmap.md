# Optimization Roadmap: Reduce Redundant Stage Runs Across Baseline, Glossary, Cache Phases

Goals:
- Avoid re-running expensive stages across repeated phases.
- Provide stage-level caching/resume behavior for reproducibility.
- Add developer and CI tests verifying cache semantics.
- Apple Silicon-specific performance and installation tips.

Phases:
1. Stage Manifest/Caching (1–2 days)
   - Implement stage manifest schema and checksum comparators.
     - Manifest schema (stage manifest.json):
       - stage: string
       - inputs: [path]
       - inputs_checksum: string (sha256 of inputs and file contents)
       - params: object (stage-specific parameters, including clip-start/clip-end)
       - runner_version: string
       - outputs: [path]
       - timestamp: number (unix ts when manifest written)
       - last_checked_ts: number (time manifest was last checked)
   - Add manifest writing to every stage (runner writes final manifest after stage completes).
   - Add skip-on-cache logic in the pipeline-runner (see pipeline/runner.py).
   - Implementation notes:
     - Use compute_inputs_checksum() that recursively walks directories and includes per-file sha256.
     - Ensure the "params" object includes CLI parameters (clip start/end, quality, etc.) to invalidate cache when user changes them.
     - Keep job-level and stage-level manifests isolated under each stage output directory.
     - Prefer to return stage outputs from the executor, otherwise stage output dir is scanned and recorded.

2. CLI Controls & Stage-Range Runs (1 day)
   - CLI flags implemented in pipeline runner:
     - --from <stage> — start running at this stage (inclusive)
     - --to <stage> — stop running at this stage (inclusive)
     - --stages <comma-list> — explicit list of stages to run (overrides --from/--to)
     - --force — re-run every selected stage bypassing manifest/cache checks
   - Behavior:
     - Default behavior (no --from/--to/--stages, no --force) runs the full workflow but each stage will check its manifest and SKIP if unchanged.
     - --stages takes precedence and will only run enumerated stages (in canonical pipeline order).
     - --from and --to define a contiguous inclusive pipeline range, validated against canonical stage ordering.
     - --force forces manifest bypass and re-execution for selected stages.

3. Update Quickstart & Tests (1 day)
   - Refactor test-glossary-quickstart.sh to perform:
     1) one full run (baseline)
     2) run limited stage list for glossary generation
     3) a final run that validates cache hits across other stages
   - Add CI job to ensure repeated runs do not re-run heavy stages (e.g., source separation) if manifests unchanged.

4. Logging & Telemetry (0.5 day)
   - Add structured log entries for cache hits / misses and skipped stages:
     - Event types emitted: stage_skipped, stage_cache_miss, stage_running, stage_completed, stage_failed.
     - These are emitted as JSON objects (single-line) for automated parsing by CI or tooling.
   - Add a `--log-level` CLI flag to control verbosity (DEBUG/INFO/WARNING/ERROR).
   - Human-readable logs are preserved to maintain backward compatibility.
   - CI & quickstart scripts should look for either the human SKIPPED messages or the structured JSON event `{"event":"stage_skipped"}`.

5. Apple Silicon-specific optimizations (0.5–1 day) - implemented
   - Add device detection & device field in manifests so runs using MPS are recorded and reproducible.
   - Detect PyTorch MPS availability (torch.backends.mps.is_available() and is_built()) and select device automatically (or accept --device override).
   - Demucs: detect if Demucs is installed (module or CLI). If installed, run with MPS device if available. If missing, try to install or inform the user.
   - Demucs install / bootstrap:
     - Provide a bootstrap script (scripts/bootstrap.sh) that prepares a venv (venv/demucs) and installs Demucs (and optionally torch for MPS) for local dev and CI.
     - The pipeline runner supports `--auto-install-demucs` and `--demucs-venv` flags to attempt a best-effort install if Demucs is missing at runtime. Use this only when you cannot guarantee pre-installed runtime dependencies.
     - Best practice: install Demucs & PyTorch in CI using bootstrap script and pip cache/hard-coded pre-built wheels—avoid on-the-fly installs during long pipelines.
   - CI: add pip cache (actions/cache for ~/.cache/pip) and prefer prebuilt wheels for PyTorch to reduce install times.
   - Runner behavior:
     - If MPS is available, the runner sets manifest param device: mps and passes it to stages.
     - If MPS is unavailable or the user requested --device cpu, runner and stages use CPU.
     - Device is recorded in per-stage manifest so caching is preserved per-device.
   - Best practices:
     - Use pre-built wheels or cached wheel caches on Apple Silicon rather than building PyTorch from source.
     - In CI, prefer macOS runners with Apple Silicon if you intend to validate MPS behavior.
     - Avoid mixing device types across runs in the same job-dir to prevent inconsistent manifests (the quickstart script appends device to job-dir).

6. Developer Guidelines & Cleanups (ongoing)
   - Add developer docs with best-practices for stage idempotence, I/O layout (output directory per stage), writing small temp files, and how to create reproducible stage manifests.
   - Add unit tests for manifest checksum behavior and stage-level skip semantics.

7. Compliance & Cleanup (ongoing)
   - Conduct a repo-wide audit to:
     - Identify stage executors missing manifest writing and update them.
     - Identify duplicate scripts or docs to deprecate (e.g., legacy scripts under scripts/ that are no longer used).
     - Identify tests that don’t assert SKIPPED behavior and add them.
   - Implement a manifest schema validator and add to CI:
     - A small Python script that checks manifest.json for required fields & deterministic checksums.
   - Add a pre-commit hook and update contributor guide:
     - Linting (ShellCheck) for bash scripts and Python lints (ruff/flake8).
     - Test check (pytest) for unit tests & StageRunner behavior.
   - Documentation cleanup:
     - Consolidate duplicate docs into INDEX.md (Quickstart → Developer Guide → Roadmap).
     - Remove outdated Quickstart variants; update/merge helpful examples found in README.
   - Timeline & ownership:
     - Audit & immediate fixes: 1 week (owner: pipeline team)
     - CI validators & PR gating: 1 week (owner: CI)
     - Doc consolidation & cleanup: 1 week (owner: docs team)
     - Long-term monitoring & enforcement: ongoing (owner: repo maintainer)

Appendix: Stage Manifest schema (v1)
- stage: string
- inputs: [path]
- inputs_checksum: string
- params: object
- runner_version: string
- outputs: [path]
- timestamp: number
- last_checked_ts: number

