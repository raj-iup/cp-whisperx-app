# Contributing — Developer Guidelines & Checklist

This document defines a short developer checklist that all contributors should follow.

Core standards
- Every stage must:
  - Write manifest.json to its stage directory with required fields:
    - stage, inputs, inputs_checksum, params, runner_version, outputs, timestamp, last_checked_ts.
  - Use StageRunner wrapper in pipeline/runner.py to run or skip stage based on the manifest.
  - Never write outside its own stage directory (use a tmp subdirectory and atomic move).

- Command line flags & environment:
  - Implement and support: --from, --to, --stages, --force, --device, --demucs-venv, --auto-install-demucs, --log-level.
  - Runner should also accept env fallback names for CI compatibility (PIPELINE_DEVICE, PIPELINE_STAGES, PIPELINE_FORCE).

- Logging:
  - Use log_event() for structured logs: stage_running, stage_skipped, stage_cache_miss, stage_completed, stage_failed.
  - Keep human readable lines for traceability.

## Committing & Pushing changes (helper)

A script is provided to standardize commits and pushes:

- Script: scripts/git-commit-push.sh
- It runs basic checks (shellcheck & pytest when available), commits your changes, and pushes to the remote branch.
- Example:
  - ./scripts/git-commit-push.sh -m "Add stage manifest and StageRunner integration"
  - To force push: ./scripts/git-commit-push.sh -m "..." -f
  - To skip checks (not recommended): ./scripts/git-commit-push.sh -m "..." --skip-checks

Pre-PR checklist (run locally)
- Run shellcheck for bash scripts:
  - shellcheck scripts/*.sh
- Run unit tests:
  - pytest -q tests
- Ensure stage-level manifest.json present for any modified stage:
  - The manifest should include stage, inputs, inputs_checksum, params, outputs, timestamp.
- For new/changed flags, update docs/QUICKSTART.md and docs/developer-guide.md as appropriate.

PR review criteria
- CI passes lint and tests (including quickstart minimal runs if applicable).
- Stage-level manifest is present and correct.
- No changes to sibling stage outputs or shared directories.
- Document any new flags / behavior in docs/INDEX.md and CONTRIBUTING.md.

