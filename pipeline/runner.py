import argparse
import json
import logging
import os
import hashlib
import time
import shutil
import platform
import subprocess
import sys
from typing import Dict, List, Callable, Optional

# Runner version used to invalidate cache on major runner changes
RUNNER_VERSION = "0.1.0"

LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
}
# default
LOG_LEVEL = LOG_LEVELS["INFO"]

def set_log_level(level_str: str):
    global LOG_LEVEL
    l = level_str.upper()
    LOG_LEVEL = LOG_LEVELS.get(l, LOG_LEVELS["INFO"])

def _timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def log_event(level: str, message: str, **meta):
    """
    Print a human-friendly log and optionally a structured JSON record.
    Use 'event' in meta for structured logs (e.g., 'stage_skipped', 'stage_completed').
    Only emits when level >= configured LOG_LEVEL.
    """
    level = level.upper()
    level_num = LOG_LEVELS.get(level, LOG_LEVELS["INFO"])
    if level_num < LOG_LEVEL:
        return

    # Human readable line (keeps existing format)
    print(f"[{_timestamp()}] [pipeline] [{level}] {message}")

    # Emit a JSON structured entry only for a focused set of events to avoid noise
    structured_events = {"stage_skipped", "stage_cache_miss", "stage_cache_hit", "stage_running", "stage_completed", "stage_failed"}
    if "event" in meta and meta.get("event") in structured_events:
        j = {
            "ts": int(time.time()),
            "level": level,
            "event": meta.get("event"),
            "stage": meta.get("stage"),
            "message": message,
        }
        # Attach additional meta into the JSON entry
        for k, v in meta.items():
            if k not in ("event", "stage"):
                j[k] = v
        # Print JSON on its own line for easy grepping/parsing
        print(json.dumps(j, separators=(",", ":"), sort_keys=True))

def sha256_of_file(path: str) -> str:
    """Compute sha256 digest for a file. Returns empty string on error."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return "MISSING"

def compute_inputs_checksum(inputs: List[str]) -> str:
    """Compute a combined checksum of provided input files/directories."""
    parts = []
    for p in sorted(inputs):
        if os.path.isdir(p):
            # include files under directory with their relative path & checksum
            for root, _, files in os.walk(p):
                for fname in sorted(files):
                    filepath = os.path.join(root, fname)
                    try:
                        rel = os.path.relpath(filepath, p)
                    except Exception:
                        rel = filepath
                    parts.append(f"{p}/{rel}:{sha256_of_file(filepath)}")
        else:
            parts.append(f"{p}:{sha256_of_file(p)}")
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()

def read_manifest(stage_output_dir: str) -> Dict:
    """Read manifest.json from stage output dir if present."""
    manifest_path = os.path.join(stage_output_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        return {}
    try:
        with open(manifest_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}

def write_manifest(stage_output_dir: str, manifest: Dict):
    """Write manifest.json (pretty printed) into the stage output dir."""
    os.makedirs(stage_output_dir, exist_ok=True)
    manifest_path = os.path.join(stage_output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)

def scan_stage_outputs(output_dir: str) -> List[str]:
    """Return a list of files under a stage output directory (used if executor doesn't declare outputs)."""
    out_files = []
    if not os.path.isdir(output_dir):
        return out_files
    for root, _, files in os.walk(output_dir):
        for fname in files:
            out_files.append(os.path.join(root, fname))
    return sorted(out_files)

class StageRunner:
    """Utility wrapper for running a pipeline stage with manifest-based caching."""

    def __init__(
        self,
        stage_name: str,
        output_dir: str,
        inputs: List[str],
        params: Dict = None,
        runner_version: str = RUNNER_VERSION,
        force: bool = False,
    ):
        self.stage_name = stage_name
        self.output_dir = output_dir
        self.inputs = inputs or []
        self.params = params or {}
        self.runner_version = runner_version
        self.force = force

    def should_run(self) -> bool:
        if self.force:
            log_event("DEBUG", f"Stage {self.stage_name}: FORCE run requested, bypassing cache checks", event="stage_cache_miss", stage=self.stage_name)
            return True
        prev = read_manifest(self.output_dir)
        if not prev:
            log_event("DEBUG", f"Stage {self.stage_name}: No manifest found", event="stage_cache_miss", stage=self.stage_name)
            return True
        prev_checksum = prev.get("inputs_checksum")
        current_checksum = compute_inputs_checksum(self.inputs)
        if prev_checksum != current_checksum:
            log_event("DEBUG", f"Stage {self.stage_name}: Inputs checksum changed ({prev_checksum}->{current_checksum})", event="stage_cache_miss", stage=self.stage_name)
            return True
        if prev.get("params") != self.params:
            log_event("DEBUG", f"Stage {self.stage_name}: Params changed", event="stage_cache_miss", stage=self.stage_name)
            return True
        if prev.get("runner_version") != self.runner_version:
            log_event("DEBUG", f"Stage {self.stage_name}: Runner version changed ({prev.get('runner_version')} -> {self.runner_version})", event="stage_cache_miss", stage=self.stage_name)
            return True
        # No change; skip stage
        log_event("INFO", f"Stage {self.stage_name}: SKIPPED (cache hit)", event="stage_skipped", stage=self.stage_name)
        return False

    def run(self, executor_callable: Callable[[str, List[str], Dict, str], Optional[List[str]]]) -> bool:
        """
        Run the stage via executor_callable if needed. Returns True if executed, False if skipped.
        - executor_callable(stage_name, inputs, params, output_dir) -> outputs (list of files) or None
        """
        if not self.should_run():
            prev = read_manifest(self.output_dir) or {}
            prev["last_checked_ts"] = int(time.time())
            write_manifest(self.output_dir, prev)
            return False

        log_event("INFO", f"Stage {self.stage_name}: RUNNING", event="stage_running", stage=self.stage_name)
        # Ensure output dir exists for logs and partial files
        os.makedirs(self.output_dir, exist_ok=True)
        outputs = None
        try:
            outputs = executor_callable(self.stage_name, self.inputs, self.params, self.output_dir)
        except Exception as e:
            log_event("ERROR", f"Stage {self.stage_name}: FAILED ({e})", event="stage_failed", stage=self.stage_name)
            raise

        outputs = outputs or scan_stage_outputs(self.output_dir)

        manifest = {
            "stage": self.stage_name,
            "inputs": self.inputs,
            "inputs_checksum": compute_inputs_checksum(self.inputs),
            "params": self.params,
            "runner_version": self.runner_version,
            "outputs": outputs,
            "timestamp": int(time.time()),
            "last_checked_ts": int(time.time()),
        }
        write_manifest(self.output_dir, manifest)
        log_event("INFO", f"Stage {self.stage_name}: COMPLETED", event="stage_completed", stage=self.stage_name)
        return True

def filter_stage_list(all_stages: List[str], from_stage: Optional[str], to_stage: Optional[str], explicit_stages: Optional[List[str]]) -> List[str]:
    """
    Returns ordered subset of all_stages based on:
    - explicit_stages (comma-separated) takes precedence if present
    - else range from 'from_stage' to 'to_stage' (inclusive).
    If none specified, return all_stages.
    """
    if explicit_stages:
        # Validate stages exist
        explicit_set = set(explicit_stages)
        filtered = [s for s in all_stages if s in explicit_set]
        return filtered

    if not from_stage and not to_stage:
        return all_stages

    try:
        start_idx = 0 if not from_stage else all_stages.index(from_stage)
    except ValueError:
        raise ValueError(f"Unknown --from stage: {from_stage}")
    try:
        end_idx = len(all_stages) - 1 if not to_stage else all_stages.index(to_stage)
    except ValueError:
        raise ValueError(f"Unknown --to stage: {to_stage}")

    if start_idx > end_idx:
        raise ValueError(f"--from stage '{from_stage}' occurs after --to stage '{to_stage}'")

    return all_stages[start_idx : end_idx + 1]

def install_demucs_env(venv_path: str, device: str = "cpu") -> bool:
    """
    Install Demucs (and best-effort torch) inside a venv.
    - venv_path can be a path like venv/demucs.
    - Returns True if install succeeded, False if not.
    """
    python_bin = os.path.join(venv_path, "bin", "python")
    pip_bin = [python_bin, "-m", "pip"] if os.path.exists(python_bin) else [sys.executable, "-m", "pip"]
    try:
        log_event("INFO", f"Attempting to install Demucs in venv: {venv_path}", event="stage_running", stage="source_separation")
        # Ensure pip/up-to-date
        subprocess.check_call(pip_bin + ["install", "--upgrade", "pip", "setuptools", "wheel"])
        # Attempt to install Torch first if device == mps: best-effort pre-flight. This may be a no-op if torch is already present.
        if device == "mps":
            # Best-effort: attempt to install CPU/MPS wheels -- recommend using cached wheels or pre-built wheel in CI
            try:
                subprocess.check_call(pip_bin + ["install", "--upgrade", "torch"])
            except subprocess.CalledProcessError:
                log_event("WARNING", "Failed to install torch automatically; continue and attempt demucs only", event="stage_failed", stage="source_separation")
        # Install demucs (extra dependencies automatically pulled)
        subprocess.check_call(pip_bin + ["install", "--upgrade", "demucs"])
        # Verify demucs import / cli
        try:
            # Try run `demucs --version` using python -c import demucs; print(demucs.__version__)
            subprocess.check_call(pip_bin + ["run", "python", "-c", "import demucs; print('DEMUX_OK')"])
        except Exception:
            # Fallback to running `demucs --help` if available on PATH (less deterministic)
            if shutil.which("demucs"):
                subprocess.check_call([shutil.which("demucs"), "--help"])
        log_event("INFO", "Demucs installed successfully", event="stage_cache_miss", stage="source_separation")
        return True
    except subprocess.CalledProcessError as e:
        log_event("ERROR", f"Demucs bootstrap failed: {e}", event="stage_failed", stage="source_separation")
        return False

def is_demucs_installed() -> bool:
    # Try to import as a Python module first; then try to detect CLI in PATH
    try:
        import demucs  # type: ignore  # noqa
        return True
    except Exception:
        return shutil.which("demucs") is not None

# Demucs executor: prefer the provided venv's python; fallback to system 'demucs' CLI
def demucs_executor(stage_name: str, inputs: list, params: Dict, output_dir: str) -> list:
    """
    Run Demucs separation.
    inputs: list with at least one audio input path.
    params: a dict that may contain 'device', 'demucs_venv', 'demucs_installed' etc.
    """
    audio_input = inputs[0] if inputs else None
    if not audio_input or not os.path.exists(audio_input):
        raise RuntimeError(f"Input audio not found for stage {stage_name}: {audio_input}")

    demucs_venv = params.get("demucs_venv")
    demucs_ok = params.get("demucs_installed", None)
    device = params.get("device", "cpu")

    # Try to prefer venv python -m demucs if possible
    python_bin = None
    if demucs_venv:
        candidate_python = os.path.join(demucs_venv, "bin", "python")
        if os.path.exists(candidate_python):
            python_bin = candidate_python

    # If python_bin points to venv python that can import demucs, use it.
    cmd = None
    if python_bin:
        # Try to check demucs import via python -c
        try:
            subprocess.check_call([python_bin, "-c", "import demucs"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            cmd = [python_bin, "-m", "demucs", "separate", "--out", output_dir, audio_input]
        except subprocess.CalledProcessError:
            # fallback to CLI path
            python_bin = None

    if cmd is None:
        # Next fallback: demucs CLI (on PATH)
        demucs_cli = shutil.which("demucs")
        if demucs_cli:
            cmd = [demucs_cli, "--out", output_dir, audio_input]

    if cmd is None:
        raise RuntimeError("Demucs not available (venv or system). Use --auto-install-demucs to attempt install or provide a venv with Demucs.")

    # If device is 'mps', try to set a sensible environment (PyTorch should set device)
    env = os.environ.copy()
    if device == "mps":
        env["TORCH_USE_MPS"] = "1"

    log_event("INFO", f"Running demucs cmd for {stage_name}: {' '.join(cmd)}", event="stage_running", stage=stage_name)

    # Ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)
    subprocess.check_call(cmd, env=env)

    # scan outputs
    outputs = scan_stage_outputs(output_dir)
    return outputs


# Example placeholder to show how to integrate StageRunner in an existing loop
def run_pipeline_workflow(workflow: str, job_dir: str, media: str, clip_start: str, clip_end: str, from_stage: Optional[str], to_stage: Optional[str], stages_list: Optional[List[str]], force: bool, device: Optional[str] = None, auto_install_demucs: bool = False, demucs_venv: Optional[str] = None):
    """
    This is an integration hook: adapt to your existing pipeline code.
    - `workflow`: the workflow name (translate/transcribe)
    - `job_dir`: job directory path
    - `media`: input media path
    - `clip_start`, `clip_end`: optional slice values
    - `from_stage`, `to_stage`: specify stage range
    - `stages_list`: explicit list of stages to run
    - `force`: bypass cache if True
    - `device`: 'mps' or 'cpu' or None (auto-detect)
    - `auto_install_demucs`: If Demucs is missing, try auto-install during the run (best-effort)
    - `demucs_venv`: Path to venv where Demucs will be installed/managed
    """
    runner_device = detect_preferred_device(device)
    log_event("INFO", f"Runner device selected: {runner_device}", event="stage_running")

    # Build list of stages in the canonical order for your workflow
    # Replace this with your pipeline's stage registry or loader
    all_stages_order = [
        "demux",
        "tmdb",
        "glossary_load",
        "source_separation",
        "transcribe",
        "align",
        "postprocess",
        "translate",
        "subtitle",
        "package",
    ]

    # Example mapping of stage name -> stage metadata (executor, inputs, params, output_dir)
    # Replace with your actual pipeline stage definitions & executors
    # TODO: integrate actual executor references instead of None
    stages_meta = {
        "demux": {
            "executor": lambda *args, **kwargs: None,  # replace with real executor function
            "inputs": [media],
            "output_dir": os.path.join(job_dir, "01_demux"),
            "params": {"clip_start": clip_start, "clip_end": clip_end, "device": runner_device},
        },
        "tmdb": {
            "executor": lambda *args, **kwargs: None,
            "inputs": [],  # e.g., metadata inputs
            "output_dir": os.path.join(job_dir, "02_tmdb"),
            "params": {"device": runner_device},
        },
        "source_separation": {
            "executor": demucs_executor,
            "inputs": [os.path.join(job_dir, "01_demux", "audio.wav")],
            "output_dir": os.path.join(job_dir, "04_source_separation"),
            "params": {"quality": "quality", "device": runner_device, "demucs_venv": demucs_venv, "demucs_installed": is_demucs_installed()},
        },
        # ... other stages ...
    }

    # Detect demucs presence and log
    if "source_separation" in stages_meta:
        demucs_ok = is_demucs_installed()
        if demucs_ok:
            log_event("INFO", "Demucs runtime found; will attempt to use device: %s" % runner_device, event="stage_running", stage="source_separation")
        else:
            log_event("WARNING", "Demucs not found; source_separation will be skipped or attempted to be installed during execution", event="stage_failed", stage="source_separation")
        # Add demucs detection status to stage params so manifests can capture it (installation influences reproducibility)
        stages_meta["source_separation"]["params"]["demucs_installed"] = demucs_ok

    # If demucs not installed but auto_install_demucs is set: attempt to install into demucs_venv
    if "source_separation" in stages_meta:
        demucs_ok = stages_meta["source_separation"]["params"].get("demucs_installed", False)
        if not demucs_ok and auto_install_demucs and demucs_venv:
            log_event("INFO", "Attempting to auto-install Demucs into venv for source_separation stage", event="stage_running", stage="source_separation")
            if install_demucs_env(demucs_venv, runner_device):
                demucs_ok = is_demucs_installed()  # recheck or set param to True
                stages_meta["source_separation"]["params"]["demucs_installed"] = demucs_ok
                stages_meta["source_separation"]["params"]["demucs_venv"] = demucs_venv

    # Determine which stages to run
    selected = filter_stage_list(all_stages_order, from_stage, to_stage, stages_list)

    print(f"[pipeline] [INFO] Selected stages: {selected}; device={runner_device}")

    for name in selected:
        meta = stages_meta.get(name)
        if not meta:
            log_event("WARNING", f"No metadata found for stage '{name}', skipping", event="stage_failed", stage=name)
            continue

        # Add demucs_venv param if stage is source_separation
        if name == "source_separation":
            meta["params"]["demucs_venv"] = demucs_venv
            meta["params"]["demucs_installed"] = is_demucs_installed()

        sr = StageRunner(stage_name=name, output_dir=meta["output_dir"], inputs=meta.get("inputs", []), params=meta.get("params", {}), force=force)
        sr.run(meta["executor"])

# CLI entrypoint: add --auto-install-demucs and --demucs-venv
def parse_args_cli():
    p = argparse.ArgumentParser(prog="pipeline-runner")
    p.add_argument("--workflow", default="translate", help="Workflow name (translate/transcribe)")
    p.add_argument("--job-dir", required=True, help="Job working dir")
    p.add_argument("--media", help="Input media path")
    p.add_argument("--clip-start", help="Clip start time (HH:MM:SS)")
    p.add_argument("--clip-end", help="Clip end time (HH:MM:SS)")
    p.add_argument("--from", dest="from_stage", help="Start stage name (inclusive)")
    p.add_argument("--to", dest="to_stage", help="End stage name (inclusive)")
    p.add_argument("--stages", help="Comma-separated list of stage names to run (overrides --from/--to)")
    p.add_argument("--force", action="store_true", help="Force stages to re-run (ignore cache)")
    p.add_argument("--log-level", default="INFO", help="Log level: DEBUG/INFO/WARNING/ERROR")
    p.add_argument("--device", default=None, help="Preferred device: 'mps' or 'cpu' (auto-detected if not set)")
    p.add_argument("--auto-install-demucs", action="store_true", help="If Demucs is missing, try auto-install during the run (best-effort)")
    p.add_argument("--demucs-venv", default="venv/demucs", help="Path to venv where Demucs will be installed/managed")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args_cli()
    set_log_level(args.log_level)
    stages_list = args.stages.split(",") if args.stages else None
    run_pipeline_workflow(
        workflow=args.workflow,
        job_dir=args.job_dir,
        media=args.media,
        clip_start=args.clip_start,
        clip_end=args.clip_end,
        from_stage=args.from_stage,
        to_stage=args.to_stage,
        stages_list=stages_list,
        force=args.force,
        device=args.device,
        auto_install_demucs=args.auto_install_demucs,
        demucs_venv=args.demucs_venv,
    )