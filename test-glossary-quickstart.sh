#!/usr/bin/env bash
set -euo pipefail

# Quickstart test script - streamlined
# Determine a robust PROJECT_ROOT by walking upward until a repo indicator is found
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_project_root_find() {
  local dir="$1"
  while [[ "$dir" != "/" && "$dir" != "" ]]; do
    # repo indicators: top-level scripts expected to exist here
    if [[ -f "$dir/prepare-job.sh" ]] || [[ -f "$dir/run-pipeline.sh" ]] || [[ -d "$dir/.git" ]] || [[ -f "$dir/README.md" ]]; then
      echo "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  # fallback: use script dir
  echo "$SCRIPT_DIR"
}
PROJECT_ROOT="$(_project_root_find "$SCRIPT_DIR")"

# Set tool locations early so checks can use them
PYTHON_BIN_SYSTEM="$(command -v python3 || command -v python || true)"
PREPARE_BIN="$PROJECT_ROOT/prepare-job.sh"
RUN_PIPELINE_BIN="$PROJECT_ROOT/run-pipeline.sh"

# New: helper to detect python inside a venv
venv_has_python() {
  local venv_path="$1"
  if [[ -z "$venv_path" ]]; then
    return 1
  fi
  local py="$venv_path/bin/python"
  [[ -x "$py" ]]
}

# New: find best python binary (prefer venvs). Priority:
# 1) DEMUS_VENV if set and exists
# 2) PROJECT_ROOT/venv/common/bin/python
# 3) PROJECT_ROOT/venv/whisperx/bin/python
# 4) any venv under PROJECT_ROOT/venv/*/bin/python
# 5) fallback to system python (PYTHON_BIN_SYSTEM)
detect_and_set_python() {
  local preferred=""
  # If DEMUS_VENV explicitly set and has python, prefer it when relevant
  if [[ -n "${DEMUS_VENV:-}" ]] && venv_has_python "${DEMUS_VENV}"; then
    preferred="${DEMUS_VENV}/bin/python"
    qs_log "Using DEMUS venv python: ${preferred}"
  fi

  if [[ -z "${preferred}" ]] && venv_has_python "${PROJECT_ROOT}/venv/common"; then
    preferred="${PROJECT_ROOT}/venv/common/bin/python"
    qs_log "Using common venv python: ${preferred}"
  fi

  if [[ -z "${preferred}" ]] && venv_has_python "${PROJECT_ROOT}/venv/whisperx"; then
    preferred="${PROJECT_ROOT}/venv/whisperx/bin/python"
    qs_log "Using whisperx venv python: ${preferred}"
  fi

  if [[ -z "${preferred}" ]]; then
    # pick the first python in venv/* if exists
    for d in "${PROJECT_ROOT}/venv"/*; do
      if venv_has_python "$d"; then
        preferred="$d/bin/python"
        qs_log "Auto-detected venv python: ${preferred}"
        break
      fi
    done
  fi

  if [[ -z "${preferred}" ]]; then
    if [[ -n "$PYTHON_BIN_SYSTEM" ]]; then
      preferred="$PYTHON_BIN_SYSTEM"
      qs_log "Falling back to system python: ${preferred}"
    else
      qs_log "ERROR: No python (venv or system) found; install Python 3 and retry."
      exit 1
    fi
  fi
  PYTHON_BIN="${preferred}"
}

# New: ensure demucs venv is set if present; if none and auto-install requested, bootstrap will create it
detect_demucs_venv() {
  # If user explicitly set DEMUS_VENV and it's a dir, prefer it
  if [[ -n "${DEMUS_VENV:-}" ]] && [[ -d "${DEMUS_VENV}" ]]; then
    qs_log "Using provided demucs venv: ${DEMUS_VENV}"
    return 0
  fi

  # Otherwise prefer existing venv/demucs under project
  if [[ -d "${PROJECT_ROOT}/venv/demucs" ]]; then
    DEMUS_VENV="${PROJECT_ROOT}/venv/demucs"
    qs_log "Detected demucs venv at: ${DEMUS_VENV}"
    return 0
  fi

  # No venv found; if AUTO_INSTALL_DEMUCS requested, it will be created by bootstrap script later
  if [[ "${AUTO_INSTALL_DEMUCS}" == "true" ]]; then
    qs_log "Demucs venv not found; will attempt to create at ${DEMUS_VENV} when auto-install is enabled."
    return 0
  fi

  qs_log "No demucs venv found under project. You can create one with scripts/bootstrap.sh or set --demucs-venv explicitly."
  return 1
}

# Call detection routines before using $PYTHON_BIN or demucs venv values
detect_and_set_python
detect_demucs_venv

# Initialize run-pipeline flags variables so they are safe when referenced
RUN_PIPELINE_DEVICE_FLAG=""
RUN_PIPELINE_DEMUCS_FLAG=""
RUN_PIPELINE_AUTO_INSTALL_FLAG=""

# Default example source media (sample supplied in repo)
DEFAULT_VIDEO="${PROJECT_ROOT}/in/Jaane Tu Ya Jaane Na 2008.mp4"

# Define logging helper early to avoid name collisions with macOS `log` tool
qs_log() { echo "[$(date +%F' '%T)] $*"; }

# Show detected project root for debugging if the script is invoked incorrectly
qs_log "Detected PROJECT_ROOT: $PROJECT_ROOT"
qs_log "Default sample media path: $DEFAULT_VIDEO"

# Fallback suggestions for sample media if default not present (don't exit yet - we'll error later if missing)
POSSIBLE_SAMPLE_PATHS=(
  "${PROJECT_ROOT}/in/Jaane Tu Ya Jaane Na 2008.mp4"
  "${PROJECT_ROOT}/media/Jaane Tu Ya Jaane Na 2008.mp4"
  "${PROJECT_ROOT}/samples/Jaane Tu Ya Jaane Na 2008.mp4"
  "/Users/rpatel/Projects/cp-whisperx-app/in/Jaane Tu Ya Jaane Na 2008.mp4"  # explicit fallback
)

# Choose default if present among possibilities
for p in "${POSSIBLE_SAMPLE_PATHS[@]}"; do
  if [[ -f "$p" ]]; then
    DEFAULT_VIDEO="$p"
    break
  fi
done

# Defaults
VIDEO_PATH=""
# Remove hard-coded film title defaults; populate via TMDB fetch later
FILM_TITLE=""
FILM_YEAR=""

START_TIME="00:00:00"
END_TIME="00:05:00"
LOG_LEVEL="DEBUG"
AUTO_EXECUTE=false
SKIP_BASELINE=false
SKIP_GLOSSARY=false
SKIP_CACHE=false
STAGES=""
CI_MODE=false
DEVICE=""  # 'mps'|'cpu' or empty for auto-detection
AUTO_INSTALL_DEMUCS=false
DEMUS_VENV="venv/demucs"

HEAVY_STAGES=(source_separation)  # stages to verify caching (timestamps + SKIPPED message)

# New: chunk size parsing (default 15 minutes)
CHUNK_SIZE=900  # seconds

parse_chunk_size() {
  local raw="$1"
  if [[ -z "$raw" ]]; then
    echo "$CHUNK_SIZE"
    return 0
  fi
  # Accept formats: 15m, 900s, 900
  if [[ "$raw" =~ ^([0-9]+)m$ ]]; then
    echo $((${BASH_REMATCH[1]} * 60))
  elif [[ "$raw" =~ ^([0-9]+)s$ ]]; then
    echo "${BASH_REMATCH[1]}"
  elif [[ "$raw" =~ ^[0-9]+$ ]]; then
    echo "$raw"
  else
    qs_log "Invalid chunk size format: $raw"
    exit 2
  fi
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] [VIDEO_PATH]
Example: ./test-glossary-quickstart.sh --auto

Options:
  --video PATH              Input media path (default: $DEFAULT_VIDEO)
  --title TITLE             Film title for TMDB lookup
  --year YEAR               Film year for TMDB lookup
  --start-time HH:MM:SS     Start time for clip extraction (default: $START_TIME)
  --end-time HH:MM:SS       End time for clip extraction (default: $END_TIME)
  --log-level LEVEL         Log level: DEBUG|INFO|WARN|ERROR (default: $LOG_LEVEL)
  --auto                    Auto-execute non-interactive
  --skip-baseline           Skip baseline run
  --skip-glossary           Skip glossary run
  --skip-cache              Skip cache run
  --stages ST1,ST2          Comma-separated explicit stages to run
  --device DEVICE           'mps' or 'cpu' (auto if not set)
  --auto-install-demucs     Auto-install Demucs into venv via scripts/bootstrap.sh
  --demucs-venv PATH        Path to Demucs venv (default: $DEMUS_VENV)
  --ci                      CI mode: exit non-zero on cache verification failure
  --chunk-size SIZE         Chunk size for processing (default: 15m)
  -h                        Show help
EOF
  exit 1
}

# Simple helpers
find_stage_manifest() {
  # find manifest for a stage under a job dir
  local jobd="$1"
  local stage="$2"
  find "$jobd" -type f -name "manifest.json" -path "*/${stage}/*" -print -quit || true
}

get_manifest_ts() {
  local mf="$1"
  if [[ -z "$mf" || ! -f "$mf" ]]; then
    echo "MISSING"
    return 0
  fi
  # parse with python for portability
  "$PYTHON_BIN" - <<PY
import json,sys
try:
    m=json.load(open(sys.argv[1]))
    print(m.get("timestamp","MISSING"))
except Exception:
    print("MISSING")
PY
}

# CLI parsing
POSITIONAL=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --video) VIDEO_PATH="$2"; shift 2;;
    --title) FILM_TITLE="$2"; shift 2;;
    --year)  FILM_YEAR="$2"; shift 2;;
    --start-time) START_TIME="$2"; shift 2;;
    --end-time) END_TIME="$2"; shift 2;;
    --log-level) LOG_LEVEL="$2"; shift 2;;
    --auto) AUTO_EXECUTE=true; shift;;
    --skip-baseline) SKIP_BASELINE=true; shift;;
    --skip-glossary) SKIP_GLOSSARY=true; shift;;
    --skip-cache) SKIP_CACHE=true; shift;;
    --stages) STAGES="$2"; shift 2;;
    --device) DEVICE="$2"; shift 2;;
    --auto-install-demucs) AUTO_INSTALL_DEMUCS=true; shift;;
    --demucs-venv) DEMUS_VENV="$2"; shift 2;;
    --ci) CI_MODE=true; shift;;
    --chunk-size) CHUNK_SIZE_RAW="$2"; shift 2;;
    -h|--help) usage;;
    *) POSITIONAL="$1"; shift;;
  esac
done

# positional overrides --video
if [[ -n "$POSITIONAL" ]]; then
  VIDEO_PATH="$POSITIONAL"
fi

VIDEO_PATH="${VIDEO_PATH:-$DEFAULT_VIDEO}"

# Auto-detect device if not provided
if [[ -z "$DEVICE" ]]; then
  if [[ "$(uname -m)" == "arm64" ]]; then
    if [[ -n "$PYTHON_BIN" ]]; then
      MPS_AVAILABLE=$("$PYTHON_BIN" - <<PY 2>/dev/null || true
import sys
try:
    import torch
    print("True" if (torch.backends.mps.is_available() and torch.backends.mps.is_built()) else "False")
except Exception:
    print("False")
PY
)
    else
      MPS_AVAILABLE="False"
    fi
    if [[ "${MPS_AVAILABLE}" == "True" ]]; then
      DEVICE="mps"
    else
      DEVICE="cpu"
    fi
  else
    DEVICE="cpu"
  fi
fi

# Decide how to pass device to run-pipeline.sh: prefer explicit --device if supported; else export PIPELINE_DEVICE env var
RUN_PIPELINE_DEVICE_FLAG=""
if [[ -x "${RUN_PIPELINE_BIN}" ]] && "${RUN_PIPELINE_BIN}" --help 2>/dev/null | grep -q -- '--device'; then
  RUN_PIPELINE_DEVICE_FLAG="--device ${DEVICE}"
else
  export PIPELINE_DEVICE="${DEVICE}"
fi

# Detect which flags run-pipeline.sh supports so we don't pass unsupported options
SUPPORTS_FROM=0
SUPPORTS_TO=0
SUPPORTS_STAGES=0
SUPPORTS_FORCE=0
SUPPORTS_DEMUCS_VENV=0
SUPPORTS_AUTO_INSTALL_DEMUCS=0
if [[ -x "${RUN_PIPELINE_BIN}" ]]; then
  if "${RUN_PIPELINE_BIN}" --help 2>/dev/null | grep -q -- '--from'; then SUPPORTS_FROM=1; fi
  if "${RUN_PIPELINE_BIN}" --help 2>/dev/null | grep -q -- '--to'; then SUPPORTS_TO=1; fi
  if "${RUN_PIPELINE_BIN}" --help 2>/dev/null | grep -q -- '--stages'; then SUPPORTS_STAGES=1; fi
  if "${RUN_PIPELINE_BIN}" --help 2>/dev/null | grep -q -- '--force'; then SUPPORTS_FORCE=1; fi
  if "${RUN_PIPELINE_BIN}" --help 2>/dev/null | grep -q -- '--demucs-venv'; then SUPPORTS_DEMUCS_VENV=1; fi
  if "${RUN_PIPELINE_BIN}" --help 2>/dev/null | grep -q -- '--auto-install-demucs'; then SUPPORTS_AUTO_INSTALL_DEMUCS=1; fi
fi

# If run-pipeline supports demucs flags, prepare them
if [[ $SUPPORTS_DEMUCS_VENV -eq 1 ]]; then
  RUN_PIPELINE_DEMUCS_FLAG="--demucs-venv ${DEMUS_VENV}"
fi
if [[ $SUPPORTS_AUTO_INSTALL_DEMUCS -eq 1 && "${AUTO_INSTALL_DEMUCS}" == "true" ]]; then
  RUN_PIPELINE_AUTO_INSTALL_FLAG="--auto-install-demucs"
fi

# Helper: sanitize run_flags for command and set fallback env vars if needed
_prepare_run_flags() {
  # Accepts a single string arg with run flags
  local run_flags_raw="$1"
  local run_flags_cmd="$run_flags_raw"

  # Helper to extract both "--flag value" and "--flag=value"
  _extract_flag_val() {
    local raw="$1"; local flag="$2"
    # try --flag=value
    local val
    val=$(echo "$raw" | sed -n -E "s/.*${flag}[=[:space:]]*([^ ]+).*/\\1/p" || true)
    echo "$val"
  }

  # parse --from value (both --from tmdb and --from=tmdb)
  if echo "$run_flags_raw" | grep -q -- '--from'; then
    local from_val
    from_val=$(_extract_flag_val "$run_flags_raw" --from)
    if [[ -n "$from_val" && $SUPPORTS_FROM -eq 0 ]]; then
      export PIPELINE_FROM="$from_val"
      # Remove both forms: '--from tmdb' and '--from=tmdb'
      run_flags_cmd=$(echo "$run_flags_cmd" | sed -E 's/--from[=[:space:]]*[^ ]+//g')
      qs_log "run-pipeline does not accept --from; falling back to PIPELINE_FROM env='$PIPELINE_FROM'"
    fi
  fi

  # parse --to value
  if echo "$run_flags_raw" | grep -q -- '--to'; then
    local to_val
    to_val=$(_extract_flag_val "$run_flags_raw" --to)
    if [[ -n "$to_val" && $SUPPORTS_TO -eq 0 ]]; then
      export PIPELINE_TO="$to_val"
      run_flags_cmd=$(echo "$run_flags_cmd" | sed -E 's/--to[=[:space:]]*[^ ]+//g')
      qs_log "run-pipeline does not accept --to; falling back to PIPELINE_TO env='$PIPELINE_TO'"
    fi
  fi

  # parse --stages value
  if echo "$run_flags_raw" | grep -q -- '--stages'; then
    local stages_val
    stages_val=$(_extract_flag_val "$run_flags_raw" --stages)
    if [[ -n "$stages_val" && $SUPPORTS_STAGES -eq 0 ]]; then
      export PIPELINE_STAGES="$stages_val"
      run_flags_cmd=$(echo "$run_flags_cmd" | sed -E 's/--stages[=[:space:]]*[^ ]+//g')
      qs_log "run-pipeline does not accept --stages; falling back to PIPELINE_STAGES env='$PIPELINE_STAGES'"
    fi
  fi

  # parse --force value (accept true|false or presence only)
  if echo "$run_flags_raw" | grep -q -- '--force'; then
    # If --force present with value: --force true / --force=true
    local force_val
    force_val=$(_extract_flag_val "$run_flags_raw" --force)
    if [[ -n "$force_val" && $SUPPORTS_FORCE -eq 0 ]]; then
      export PIPELINE_FORCE="$force_val"
      run_flags_cmd=$(echo "$run_flags_cmd" | sed -E 's/--force[=[:space:]]*[^ ]+//g')
      qs_log "run-pipeline does not accept --force with value; falling back to PIPELINE_FORCE env='$PIPELINE_FORCE'"
    elif [[ -z "$force_val" && $SUPPORTS_FORCE -eq 0 ]]; then
      # Handle presence-only --force
      export PIPELINE_FORCE="true"
      run_flags_cmd=$(echo "$run_flags_cmd" | sed -E 's/--force//g')
      qs_log "run-pipeline does not accept --force flag; falling back to PIPELINE_FORCE env='true'"
    fi
  fi

  # Trim whitespace
  run_flags_cmd=$(echo "$run_flags_cmd" | xargs || true)
  echo "$run_flags_cmd"
}

# Helper: run pipeline & capture logs/manifest timestamps
run_pipeline_job() {
  local jobid="$1"
  local jobdir="$2"
  local run_flags_raw="${3:-}"

  # Prepare run flags (sanitized for command + possibly exported env fallbacks)
  local run_flags_cmd
  run_flags_cmd="$(_prepare_run_flags "$run_flags_raw")"

  # Export device variable always for backward compatibility
  export PIPELINE_DEVICE="${DEVICE}"

  # Build base cmd
  local cmd=( "${RUN_PIPELINE_BIN}" -j "${jobid}" --log-level "${LOG_LEVEL}" )

  # Append run flags (if present)
  if [[ -n "${run_flags_cmd}" ]]; then
    # Split run_flags_cmd into array - rely on eval style for simplicity
    # We pass them as words; keep simple:
    eval "set -- ${run_flags_cmd}"
    for arg in "$@"; do
      cmd+=( "${arg}" )
    done
  fi

  # Append device flag if present
  if [[ -n "${RUN_PIPELINE_DEVICE_FLAG}" ]]; then
    cmd+=( ${RUN_PIPELINE_DEVICE_FLAG} )
  fi

  # Append demucs flags if present
  if [[ -n "${RUN_PIPELINE_DEMUCS_FLAG}" ]]; then
    cmd+=( ${RUN_PIPELINE_DEMUCS_FLAG} )
  fi
  if [[ -n "${RUN_PIPELINE_AUTO_INSTALL_FLAG}" ]]; then
    cmd+=( ${RUN_PIPELINE_AUTO_INSTALL_FLAG} )
  fi

  # Run the command
  "${cmd[@]}"

  echo "Logs saved to: $jobdir/logs"
}

# Save manifest timestamps mapping
# replace associative arrays (unsupported on macOS bash v3) with indexed arrays
baseline_ts_values=()
post_ts_values=()

# Helper: run prepare-job.sh and return job id & dir
run_prepare_job() {
  local user_tag="$1"
  local prepare_bin="$PROJECT_ROOT/prepare-job.sh"

  if [[ ! -x "${prepare_bin}" ]]; then
    qs_log "ERROR: prepare-job.sh not found or not executable at ${prepare_bin}"
    qs_log "Please ensure you are running the script from the repository or that ${prepare_bin} exists."
    exit 4
  fi

  local job_json
  job_json=$("${prepare_bin}" \
    --media "$VIDEO_PATH" \
    --workflow translate \
    --source-language hi \
    --target-language en \
    --start-time "$START_TIME" \
    --end-time "$END_TIME" \
    --log-level "$LOG_LEVEL" \
    --user-id "$user_tag" 2>&1)

  echo "$job_json"
}

# New helper: extract job id & job dir from prepare-job output (inline, robust)
get_job_info() {
  local out="$1"
  local jobid=""
  local jobdir=""
  jobid=$(echo "$out" | grep -E "Job created:|Job ID:" | head -1 | awk '{print $3}' | tr -d '\r ' || true)
  if [[ -z "$jobid" ]]; then
    jobid=$(echo "$out" | grep -E "Job ID:" | head -1 | awk '{print $NF}' | tr -d '\r ' || true)
  fi
  jobdir=$(echo "$out" | grep -m1 "Job directory:" | sed 's/^.*Job directory:[[:space:]]*//' | tr -d '\r' | awk '{$1=$1};1' || true)
  printf "%s|%s" "$jobid" "$jobdir"
}

# Ensure test-results directories exist early
mkdir -p test-results/{baseline,glossary,cache,edge-cases} 2>/dev/null || true

# After CLI parsing:
CHUNK_SIZE_RAW="${CHUNK_SIZE_RAW:-}"
CHUNK_SIZE="$(parse_chunk_size "${CHUNK_SIZE_RAW}")"

# New helpers: time conversions
time_to_seconds() {
  local t="$1"
  # Support MM:SS, HH:MM:SS
  IFS=':' read -r -a parts <<< "$t"
  if [[ ${#parts[@]} -eq 3 ]]; then
    echo $((10#${parts[0]}*3600 + 10#${parts[1]}*60 + 10#${parts[2]}))
  elif [[ ${#parts[@]} -eq 2 ]]; then
    echo $((10#${parts[0]}*60 + 10#${parts[1]}))
  else
    echo $((10#$t))
  fi
}

seconds_to_time() {
  local sec="$1"
  if [[ -z "$sec" ]]; then sec=0; fi
  local h=$((sec/3600))
  local m=$(((sec%3600)/60))
  local s=$((sec%60))
  printf "%02d:%02d:%02d" "$h" "$m" "$s"
}

# Detect media duration using ffprobe (requires ffprobe); fallback to END_TIME if provided
get_media_duration() {
  local media="$1"
  if command -v ffprobe >/dev/null 2>&1; then
    # Use ffprobe to get duration as float seconds; round down
    local dur
    dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$media" 2>/dev/null || true)
    if [[ -n "$dur" ]]; then
      # floor the duration to integer seconds
      printf "%.0f" "$dur"
      return 0
    fi
  fi
  # no ffprobe or failed: try fallback if START_TIME/END_TIME provided
  qs_log "ffprobe not available or failed; using user-provided start/end or default end time."
  if [[ -n "${END_TIME:-}" ]]; then
    local st_sec=$(time_to_seconds "${START_TIME:-00:00:00}")
    local en_sec=$(time_to_seconds "${END_TIME:-00:00:00}")
    if [[ $en_sec -gt $st_sec ]]; then
      echo "$en_sec"
      return 0
    fi
  fi
  qs_log "Cannot determine media duration without ffprobe or explicit --end-time. Please install ffmpeg or provide --end-time."
  exit 2
}

# New: run slice helper: runs baseline, glossary, cache for a slice range
run_slice() {
  local slice_idx="$1"
  local slice_start="$2"
  local slice_end="$3"

  local prev_start="$START_TIME"
  local prev_end="$END_TIME"

  # override start/end for this slice
  START_TIME="$slice_start"
  END_TIME="$slice_end"

  qs_log "Processing slice ${slice_idx}: ${START_TIME} -> ${END_TIME}"

  # Baseline
  if [[ "$SKIP_BASELINE" == "false" ]]; then
    qs_log ">>> Slice ${slice_idx} - Baseline phase"
    out=$(run_prepare_job "baseline-slice-${slice_idx}")
    IFS='|' read -r jobid jobdir <<< "$(get_job_info "$out")"
    if [[ -z "$jobid" || -z "$jobdir" ]]; then
      qs_log "ERROR: Could not determine job for baseline slice ${slice_idx}"
      exit 5
    fi
    # Disable glossary
    if [[ -d "$jobdir" ]]; then
      cat > "$jobdir/.${jobid}.env" <<EOF
TMDB_ENRICHMENT_ENABLED=false
GLOSSARY_CACHE_ENABLED=false
EOF
    fi
    run_pipeline_job "$jobid" "$jobdir" ""
    # Save per-slice baseline results: copy subtitles & logs if present
    mkdir -p test-results/baseline/slice-${slice_idx}
    files=( "$jobdir"/subtitles/*.srt )
    if [[ ${#files[@]} -gt 0 ]]; then
      cp "${files[@]}" test-results/baseline/slice-${slice_idx}/ 2>/dev/null || true
    fi
    cp "$jobdir"/logs/*pipeline*.log test-results/baseline/slice-${slice_idx}/ 2>/dev/null || true
  else
    qs_log "Slice ${slice_idx} baseline skipped"
  fi

  # Glossary
  if [[ "$SKIP_GLOSSARY" == "false" ]]; then
    qs_log ">>> Slice ${slice_idx} - Glossary phase"
    out=$(run_prepare_job "glossary-slice-${slice_idx}")
    IFS='|' read -r jobid jobdir <<< "$(get_job_info "$out")"
    if [[ -z "$jobid" || -z "$jobdir" ]]; then
      qs_log "ERROR: Could not determine job for glossary slice ${slice_idx}"
      exit 5
    fi
    # Add TMDB info and enable glossary via env
    if [[ -d "$jobdir" ]]; then
      if [[ -n "${FILM_TITLE:-}" && -n "${FILM_YEAR:-}" ]]; then
        python - <<PY
import json,sys
jobfile="$jobdir/job.json"
try:
  j=json.load(open(jobfile))
  j["title"]="${FILM_TITLE}"
  j["year"]=int("${FILM_YEAR}")
  open(jobfile,"w").write(json.dumps(j, indent=2))
  print("Updated job.json with TMDB info")
except Exception as e:
  print("Failed to update job.json:", e)
PY
      fi
      cat > "$jobdir/.${jobid}.env" <<EOF
TMDB_ENRICHMENT_ENABLED=true
GLOSSARY_CACHE_ENABLED=true
EOF
    fi

    if [[ "$AUTO_INSTALL_DEMUCS" == "true" && -x "./scripts/bootstrap.sh" ]]; then
      qs_log "Bootstrap Demucs into venv: $DEMUS_VENV"
      ./scripts/bootstrap.sh "$DEMUS_VENV" "$DEVICE" || qs_log "Bootstrap returned non-zero; proceed"
    fi

    run_pipeline_job "$jobid" "$jobdir" "--from tmdb --to glossary_load"
    mkdir -p test-results/glossary/slice-${slice_idx}
    cp "$jobdir"/logs/*pipeline*.log test-results/glossary/slice-${slice_idx}/ 2>/dev/null || true
    if [[ -f "$jobdir/02_tmdb/glossary.yaml" ]]; then
      cp "$jobdir/02_tmdb/glossary.yaml" test-results/glossary/slice-${slice_idx}/ || true
    fi
    files=( "$jobdir"/subtitles/*.srt )
    if [[ ${#files[@]} -gt 0 ]]; then
      cp "${files[@]}" test-results/glossary/slice-${slice_idx}/ 2>/dev/null || true
    fi
  else
    qs_log "Slice ${slice_idx} glossary skipped"
  fi

  # Cache phase: re-run and expect heavy stages SKIPPED (per-slice)
  if [[ "$SKIP_CACHE" == "false" ]]; then
    qs_log ">>> Slice ${slice_idx} - Cache phase (re-run)"
    out=$(run_prepare_job "cache-slice-${slice_idx}")
    IFS='|' read -r jobid jobdir <<< "$(get_job_info "$out")"
    if [[ -z "$jobid" || -z "$jobdir" ]]; then
      qs_log "ERROR: Could not determine job for cache slice ${slice_idx}"
      exit 5
    fi
    if [[ -d "$jobdir" ]]; then
      if [[ -n "${FILM_TITLE:-}" && -n "${FILM_YEAR:-}" ]]; then
        python - <<PY
import json,sys
jobfile="$jobdir/job.json"
try:
  j=json.load(open(jobfile))
  j["title"]="${FILM_TITLE}"
  j["year"]=int("${FILM_YEAR}")
  open(jobfile,"w").write(json.dumps(j, indent=2))
  print("Updated job.json with TMDB info")
except Exception as e:
  print("Failed to update job.json:", e)
PY
      fi
      cat > "$jobdir/.${jobid}.env" <<EOF
TMDB_ENRICHMENT_ENABLED=true
GLOSSARY_CACHE_ENABLED=true
EOF
    fi

    run_pipeline_job "$jobid" "$jobdir" "--force false"

    # Verification: Check for SKIPPED logs or structured JSON events and copy outputs
    cache_ok=true
    if grep -q "SKIPPED" -r "$jobdir" 2>/dev/null || grep -q '"event":"stage_skipped"' -r "$jobdir" 2>/dev/null; then
      qs_log "Slice ${slice_idx} cache verification: found SKIPPED messages / structured stage_skipped events"
    else
      qs_log "Slice ${slice_idx} cache verification: No SKIPPED messages found in $jobdir"
      cache_ok=false
    fi

    # Save artifacts & logs
    mkdir -p test-results/cache/slice-${slice_idx}
    cp "$jobdir"/logs/*pipeline*.log test-results/cache/slice-${slice_idx}/ 2>/dev/null || true
    files=( "$jobdir"/subtitles/*.srt )
    if [[ ${#files[@]} -gt 0 ]]; then
      cp "${files[@]}" test-results/cache/slice-${slice_idx}/ 2>/dev/null || true
    fi

    if [[ "$cache_ok" == "false" ]]; then
      qs_log "Slice ${slice_idx} cache verification: FAILED"
      if [[ "$CI_MODE" == "true" ]]; then
        qs_log "CI mode: failing due to cache verification failure on slice ${slice_idx}"
        exit 3
      fi
    else
      qs_log "Slice ${slice_idx} cache verification: OK"
    fi
  else
    qs_log "Slice ${slice_idx} cache skipped"
  fi

  # restore start/end
  START_TIME="$prev_start"
  END_TIME="$prev_end"
}

# New helper: derive title and optional year from filename (no extension)
derive_title_and_year() {
  local media="$1"
  local base
  base="$(basename "$media")"
  base="${base%.*}"                       # remove extension
  # Replace separators with space and trim
  base="$(echo "$base" | sed -E 's/[_\.]+/ /g' | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"

  local title="$base"
  local year=""

  # Try to extract trailing year patterns: " Title 2008", "Title (2008)", "Title [2008]"
  if [[ "$base" =~ ^(.*?)[[:space:]\(\[]*([0-9]{4})[\)\]]*$ ]]; then
    title="${BASH_REMATCH[1]}"
    year="${BASH_REMATCH[2]}"
    # trim spaces from title
    title="$(echo "$title" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
  fi

  printf "%s|%s" "$title" "$year"
}

# Ensure test-results directories exist early
mkdir -p test-results/{baseline,glossary,cache,edge-cases} 2>/dev/null || true

# After parsing CLI: if FILM_TITLE not provided, derive title & year from media filename
if [[ -z "$FILM_TITLE" || "$FILM_TITLE" == "" ]]; then
  IFS='|' read -r derived_title derived_year <<<"$(derive_title_and_year "$VIDEO_PATH")"
  FILM_TITLE="${derived_title:-$FILM_TITLE}"
  # Only set FILM_YEAR if user didn't already provide it explicitly
  if [[ -z "$FILM_YEAR" || "$FILM_YEAR" == "" ]]; then
    FILM_YEAR="${derived_year:-$FILM_YEAR}"
  fi
  qs_log "Auto-derived film title: ${FILM_TITLE} ${FILM_YEAR:+(${FILM_YEAR})}"
fi

# Add run-pipeline compatibility detection earlier (we already detect support); also detect --demucs-venv and --auto-install-demucs flags
# We already pass env vars; add to function to prefer flags if run-pipeline accepts them
# (Add detection run-pipeline accepts --demucs-venv/--auto-install-demucs)
RUN_PIPELINE_DEMUCS_FLAG=""
if "$RUN_PIPELINE_BIN" --help 2>/dev/null | grep -q -- '--demucs-venv'; then
  RUN_PIPELINE_DEMUCS_FLAG="--demucs-venv ${DEMUS_VENV}"
fi
if "$RUN_PIPELINE_BIN" --help 2>/dev/null | grep -q -- '--auto-install-demucs'; then
  # This is a boolean flag
  RUN_PIPELINE_AUTO_INSTALL_FLAG="--auto-install-demucs"
else
  RUN_PIPELINE_AUTO_INSTALL_FLAG=""
fi

# Main chunk loop
# If user provided explicit END_TIME, use that; else get media duration.
# Compute start and end seconds relative to START_TIME/END_TIME defaults
global_start_sec=$(time_to_seconds "${START_TIME:-00:00:00}")
if [[ -n "${END_TIME:-}" && "${END_TIME}" != "" ]]; then
  global_end_sec=$(time_to_seconds "${END_TIME}")
else
  global_end_sec=$(get_media_duration "$VIDEO_PATH")
fi

if [[ $global_end_sec -le $global_start_sec ]]; then
  qs_log "Invalid range: start ${START_TIME} >= end ${END_TIME:-$(seconds_to_time $global_end_sec)}"
  exit 2
fi

qs_log "Chunking range [$global_start_sec -> $global_end_sec] (chunk size ${CHUNK_SIZE}s)"

slice_idx=0
curr_start=$global_start_sec

while [[ $curr_start -lt $global_end_sec ]]; do
  slice_idx=$((slice_idx+1))
  next_end=$((curr_start + CHUNK_SIZE))
  if [[ $next_end -gt $global_end_sec ]]; then
    next_end=$global_end_sec
  fi

  slice_start_time=$(seconds_to_time "$curr_start")
  slice_end_time=$(seconds_to_time "$next_end")

  qs_log "Scheduling slice ${slice_idx}: ${slice_start_time} -> ${slice_end_time}"
  run_slice "$slice_idx" "$slice_start_time" "$slice_end_time"

  curr_start=$next_end
done

qs_log "All slices processed. Quickstart complete."
if [[ "$CI_MODE" == "true" ]]; then
  qs_log "CI mode: script finished."
fi
