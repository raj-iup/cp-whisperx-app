# Copilot Instructions — CP-WhisperX-App

## Model routing policy (READ FIRST)
Before choosing a Copilot Chat model or starting Agent mode, consult:
- `docs/AI_MODEL_ROUTING.md`

Follow that document’s routing algorithm (task size + risk) to select the model and workflow (Plan → Patch → Review).
If there’s any conflict, `docs/AI_MODEL_ROUTING.md` is the source of truth.

## Tech stack
- Python 3.11+, Bash
- Pipeline stages write into stage dirs (e.g., 01_demux/, 02_tmdb/, etc.)
- Stage I/O + manifests are handled via shared/stage_utils.py (StageIO) and shared/stage_manifest.py

## Non-negotiable rules
- Never write outputs outside the current stage directory.
- Every stage must:
  - use StageIO(stage_name, job_dir, enable_manifest=True)
  - track inputs/outputs in the stage manifest
  - write logs to stage.log via StageIO.get_stage_logger()
- Keep CLI flags consistent with existing scripts (don’t invent new flags without updating docs).
- Do not introduce new dependencies without updating the correct requirements/requirements-*.txt file.
- Never print or commit secrets. Secrets come from config/secrets.json or env vars.

## Code style
- Prefer small pure functions + type hints
- Add docstrings for public functions
- Add/extend pytest tests when changing behavior

## Testing expectations
- Update/extend tests under tests/
- Ensure quick “unit-only” test path exists (avoid GPU-heavy steps in CI)
