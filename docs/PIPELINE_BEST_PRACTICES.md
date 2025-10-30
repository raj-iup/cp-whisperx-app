# Pipeline Best Practices for Reliable End-to-End Execution

## Overview

This document outlines best practices to ensure:
1. ✅ Complete manifest tracking for every stage
2. ✅ End-to-end execution without premature stopping
3. ✅ Verification that each stage completes successfully before proceeding
4. ✅ Proper error handling and recovery

---

## 1. Manifest Integration Best Practices

### 1.1 Initialize Manifest at Pipeline Start

```python
from scripts.manifest import ManifestBuilder
from pathlib import Path

# Initialize with file path for auto-save
manifest_file = movie_dir / "manifest.json"
manifest = ManifestBuilder(manifest_file)

# Set input/output metadata
manifest.set_input(str(input_path), title, year, duration)
manifest.set_output_dir(str(movie_dir))

# Check for resume
if manifest_file.exists():
    completed = manifest.data["pipeline"]["completed_stages"]
    logger.info(f"Resuming - already completed: {', '.join(completed)}")
```

### 1.2 Check Before Running Each Stage

```python
# Define stage order globally
STAGE_ORDER = [
    "demux", "tmdb", "pre_ner", "silero_vad", "pyannote_vad",
    "diarization", "asr", "post_ner", "srt_generation", "mux"
]

def should_skip_stage(stage_name: str, manifest: ManifestBuilder) -> bool:
    """Check if stage already completed successfully."""
    completed = manifest.data["pipeline"].get("completed_stages", [])
    return stage_name in completed

# Before each stage
if should_skip_stage("demux", manifest):
    logger.info("⏭️ Skipping demux - already completed")
else:
    # Run the stage
    run_stage("demux")
```

### 1.3 Record Stage Completion Properly

**For Successful Stages:**
```python
try:
    # Run stage
    result = run_docker_stage("stage_name", args, logger)
    
    if result:
        manifest.set_pipeline_step(
            "stage_name",
            True,                           # enabled
            completed=True,
            next_stage="next_stage_name",   # ALWAYS set this
            status="success",
            duration=duration_seconds
        )
        logger.info("✓ Stage completed successfully")
    else:
        raise Exception("Stage failed")
        
except Exception as e:
    # Handle failure (see section 2)
```

**For Optional/Skipped Stages:**
```python
if not hf_token_available:
    manifest.set_pipeline_step(
        "pyannote_vad",
        False,                           # not enabled
        completed=True,
        next_stage="diarization",        # CRITICAL: Set next stage!
        status="skipped",
        notes="HuggingFace token not found"
    )
    logger.info("⏭️ Skipping PyAnnote VAD - token not found")
else:
    # Run the stage normally
```

### 1.4 Finalize Manifest at End

```python
# On successful completion
manifest.finalize(status="completed")
logger.info("✓ Pipeline completed successfully")

# On critical failure
manifest.finalize(status="failed")
logger.error("✗ Pipeline failed")
```

---

## 2. Error Handling and Recovery

### 2.1 Wrap Each Stage in Try-Except

```python
def run_stage_with_manifest(stage_name: str, next_stage: str, 
                            run_func, manifest: ManifestBuilder):
    """
    Run a stage with proper error handling and manifest tracking.
    """
    if should_skip_stage(stage_name, manifest):
        logger.info(f"⏭️ Skipping {stage_name} - already completed")
        return True
    
    logger.info(f"Running stage: {stage_name}")
    start_time = time.time()
    
    try:
        # Run the stage
        success = run_func()
        
        if not success:
            raise Exception(f"{stage_name} returned failure")
        
        # Record success
        duration = time.time() - start_time
        manifest.set_pipeline_step(
            stage_name,
            True,
            completed=True,
            next_stage=next_stage,
            status="success",
            duration=duration
        )
        
        logger.info(f"✓ {stage_name} completed in {duration:.1f}s")
        return True
        
    except Exception as e:
        # Record failure
        duration = time.time() - start_time
        manifest.set_pipeline_step(
            stage_name,
            False,
            completed=True,
            next_stage=None,  # Stop pipeline on critical failure
            status="failed",
            error=str(e),
            duration=duration
        )
        
        logger.error(f"✗ {stage_name} failed: {e}")
        manifest.finalize(status="failed")
        raise  # Re-raise to stop pipeline
```

### 2.2 Distinguish Between Critical and Optional Failures

```python
# Critical failure - stop pipeline
try:
    run_stage("demux")
except Exception as e:
    manifest.finalize(status="failed")
    sys.exit(1)  # Critical stage, must exit

# Optional failure - continue pipeline
try:
    run_stage("pyannote_vad")
except Exception as e:
    logger.warning(f"PyAnnote VAD failed, continuing with Silero VAD")
    manifest.set_pipeline_step(
        "pyannote_vad",
        False,
        completed=True,
        next_stage="diarization",  # CONTINUE to next stage
        status="skipped",
        notes=f"Failed: {str(e)}"
    )
    # Don't exit - continue pipeline
```

---

## 3. Ensuring Stages Complete Before Proceeding

### 3.1 Verify Output Files Exist

```python
def verify_stage_output(stage_name: str, expected_files: list) -> bool:
    """
    Verify that stage produced expected output files.
    """
    for file_path in expected_files:
        if not Path(file_path).exists():
            logger.error(f"Missing expected output: {file_path}")
            return False
        
        # Check file is not empty
        if Path(file_path).stat().st_size == 0:
            logger.error(f"Output file is empty: {file_path}")
            return False
    
    return True

# Example usage
if not verify_stage_output("demux", [audio_dir / "audio.wav"]):
    raise Exception("Demux stage did not produce valid output")

manifest.set_pipeline_step("demux", True, completed=True, 
                          next_stage="tmdb", status="success")
```

### 3.2 Wait for Docker Containers to Complete

```python
import subprocess
import time

def run_docker_stage(service: str, args: list, timeout: int = 3600) -> bool:
    """
    Run docker stage and wait for completion.
    """
    cmd = ["docker", "compose", "run", "--rm", service] + args
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        # Run with timeout
        result = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Container exited with code {result.returncode}")
            logger.error(f"Stderr: {result.stderr}")
            return False
        
        logger.info(f"Container completed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"Stage timed out after {timeout}s")
        return False
    except Exception as e:
        logger.error(f"Stage failed: {e}")
        return False
```

### 3.3 Set Appropriate Timeouts

```python
# Define stage-specific timeouts
STAGE_TIMEOUTS = {
    "demux": 600,           # 10 minutes
    "tmdb": 60,             # 1 minute
    "pre_ner": 300,         # 5 minutes
    "silero_vad": 900,      # 15 minutes for 2.5hr movie
    "pyannote_vad": 7200,   # 2 hours for local processing
    "diarization": 1800,    # 30 minutes
    "asr": 3600,            # 1 hour
    "post_ner": 600,        # 10 minutes
    "srt_generation": 300,  # 5 minutes
    "mux": 600              # 10 minutes
}

# Use when running stage
timeout = STAGE_TIMEOUTS.get(stage_name, 3600)
success = run_docker_stage(service, args, timeout=timeout)
```

---

## 4. Pipeline Orchestration Pattern

### 4.1 Sequential Stage Execution

```python
def run_pipeline(input_file: str):
    """
    Run complete pipeline with manifest tracking.
    """
    # Setup
    manifest_file = movie_dir / "manifest.json"
    manifest = ManifestBuilder(manifest_file)
    
    # Define all stages
    stages = [
        ("demux", "tmdb", lambda: run_demux()),
        ("tmdb", "pre_ner", lambda: run_tmdb()),
        ("pre_ner", "silero_vad", lambda: run_pre_ner()),
        ("silero_vad", "pyannote_vad", lambda: run_silero_vad()),
        ("pyannote_vad", "diarization", lambda: run_pyannote_vad()),
        ("diarization", "asr", lambda: run_diarization()),
        ("asr", "post_ner", lambda: run_asr()),
        ("post_ner", "srt_generation", lambda: run_post_ner()),
        ("srt_generation", "mux", lambda: run_srt_generation()),
        ("mux", None, lambda: run_mux()),
    ]
    
    # Execute stages sequentially
    for stage_name, next_stage, run_func in stages:
        try:
            success = run_stage_with_manifest(
                stage_name, next_stage, run_func, manifest
            )
            
            if not success:
                logger.error(f"Stage {stage_name} failed, stopping pipeline")
                manifest.finalize(status="failed")
                return False
                
        except Exception as e:
            logger.error(f"Critical error in {stage_name}: {e}")
            manifest.finalize(status="failed")
            return False
    
    # All stages completed
    manifest.finalize(status="completed")
    logger.info("✓ Pipeline completed successfully!")
    return True
```

### 4.2 Add Progress Logging

```python
def run_pipeline_with_progress(input_file: str):
    """
    Run pipeline with progress indicators.
    """
    total_stages = len(STAGE_ORDER)
    
    for idx, (stage_name, next_stage, run_func) in enumerate(stages, 1):
        logger.info("=" * 60)
        logger.info(f"STAGE {idx}/{total_stages}: {stage_name.upper()}")
        logger.info("=" * 60)
        
        # Run with timing
        start = time.time()
        success = run_stage_with_manifest(stage_name, next_stage, 
                                         run_func, manifest)
        elapsed = time.time() - start
        
        if success:
            logger.info(f"✓ Stage {idx}/{total_stages} completed in {elapsed:.1f}s")
            logger.info(f"Progress: {idx}/{total_stages} stages complete")
        else:
            logger.error(f"✗ Stage {idx}/{total_stages} failed")
            return False
    
    return True
```

---

## 5. Session Management for Long-Running Pipelines

### 5.1 Use Screen/Tmux for Background Execution

```bash
# Start in screen session
screen -S pipeline-session
python pipeline.py -i "in/movie.mp4"
# Detach with Ctrl+A, D

# Reattach later
screen -r pipeline-session
```

### 5.2 Use Nohup for Persistent Execution

```bash
# Run with nohup to survive SSH disconnection
nohup python pipeline.py -i "in/movie.mp4" > pipeline.log 2>&1 &

# Monitor progress
tail -f pipeline.log
```

### 5.3 Add Periodic Status Updates

```python
import threading
import time

def periodic_status_update(manifest_file: Path, interval: int = 300):
    """
    Print status every N seconds.
    """
    while True:
        time.sleep(interval)
        if manifest_file.exists():
            manifest = ManifestBuilder(manifest_file)
            completed = manifest.data["pipeline"]["completed_stages"]
            logger.info(f"[STATUS] Completed stages: {', '.join(completed)}")
            logger.info(f"[STATUS] Next: {manifest.data['pipeline'].get('next_stage')}")

# Start status thread
status_thread = threading.Thread(
    target=periodic_status_update,
    args=(manifest_file, 300),  # Update every 5 minutes
    daemon=True
)
status_thread.start()
```

---

## 6. Validation and Testing

### 6.1 Pre-flight Checks

```python
def validate_environment():
    """
    Validate environment before starting pipeline.
    """
    checks = {
        "Docker running": lambda: subprocess.run(["docker", "info"], 
                                                capture_output=True).returncode == 0,
        "Input file exists": lambda: input_path.exists(),
        "Output directory writable": lambda: os.access(output_root, os.W_OK),
        "Config file exists": lambda: (ROOT / "config" / ".env").exists(),
        "All images present": lambda: check_docker_images(),
    }
    
    for check_name, check_func in checks.items():
        if not check_func():
            logger.error(f"✗ Pre-flight check failed: {check_name}")
            return False
        logger.info(f"✓ {check_name}")
    
    return True

# Run before pipeline
if not validate_environment():
    sys.exit(1)
```

### 6.2 Post-Stage Validation

```python
def validate_stage_output(stage_name: str, movie_dir: Path) -> bool:
    """
    Validate stage produced correct output.
    """
    validations = {
        "demux": lambda: (movie_dir / "audio" / "audio.wav").exists(),
        "tmdb": lambda: (movie_dir / "metadata" / "tmdb_data.json").exists(),
        "pre_ner": lambda: (movie_dir / "entities" / "pre_ner.json").exists(),
        "silero_vad": lambda: (movie_dir / "vad" / "silero_segments.json").exists(),
        # Add more validations...
    }
    
    if stage_name in validations:
        return validations[stage_name]()
    
    return True  # No validation defined, assume OK

# Use after each stage
if not validate_stage_output(stage_name, movie_dir):
    raise Exception(f"{stage_name} validation failed")
```

---

## 7. Implementation Checklist

### For Each Pipeline Stage:

- [ ] Check if stage in `completed_stages` before running
- [ ] Set appropriate timeout for stage
- [ ] Wrap in try-except with proper error handling
- [ ] Verify output files exist after completion
- [ ] Call `manifest.set_pipeline_step()` with all parameters:
  - [ ] `enabled` (True/False)
  - [ ] `completed=True`
  - [ ] `next_stage="next_stage_name"` (ALWAYS, even on skip)
  - [ ] `status="success"` or `"skipped"` or `"failed"`
  - [ ] Optional: `duration`, `notes`, `error`
- [ ] Log completion status clearly
- [ ] On critical failure, call `manifest.finalize(status="failed")`

### For Pipeline Orchestrator:

- [ ] Initialize manifest at start
- [ ] Check for existing manifest (resume capability)
- [ ] Run stages sequentially with completion verification
- [ ] Handle both critical and optional failures appropriately
- [ ] Call `manifest.finalize(status="completed")` at end
- [ ] Add progress logging
- [ ] Implement timeout handling
- [ ] Add pre-flight validation
- [ ] Use appropriate session management for long runs

---

## 8. Example: Complete Implementation

```python
#!/usr/bin/env python3
"""
Complete pipeline with all best practices implemented.
"""
import sys
import time
from pathlib import Path
from scripts.manifest import ManifestBuilder

STAGE_ORDER = [
    "demux", "tmdb", "pre_ner", "silero_vad", "pyannote_vad",
    "diarization", "asr", "post_ner", "srt_generation", "mux"
]

def run_complete_pipeline(input_file: str) -> bool:
    """
    Run full pipeline with manifest tracking and error handling.
    """
    # 1. Validate environment
    if not validate_environment():
        return False
    
    # 2. Setup
    manifest_file = movie_dir / "manifest.json"
    manifest = ManifestBuilder(manifest_file)
    
    # 3. Check for resume
    if manifest_file.exists():
        completed = manifest.data["pipeline"]["completed_stages"]
        logger.info(f"📋 Resuming from last run")
        logger.info(f"   Completed: {', '.join(completed)}")
    
    # 4. Define stages
    stages = [
        ("demux", "tmdb", run_demux, 600, True),
        ("tmdb", "pre_ner", run_tmdb, 60, True),
        ("pre_ner", "silero_vad", run_pre_ner, 300, True),
        ("silero_vad", "pyannote_vad", run_silero_vad, 900, True),
        ("pyannote_vad", "diarization", run_pyannote_vad, 7200, False),  # Optional
        ("diarization", "asr", run_diarization, 1800, True),
        ("asr", "post_ner", run_asr, 3600, True),
        ("post_ner", "srt_generation", run_post_ner, 600, True),
        ("srt_generation", "mux", run_srt_generation, 300, True),
        ("mux", None, run_mux, 600, True),
    ]
    
    # 5. Execute stages
    for idx, (stage, next_stage, func, timeout, critical) in enumerate(stages, 1):
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"STAGE {idx}/{len(stages)}: {stage.upper()}")
        logger.info("=" * 60)
        
        # Skip if already completed
        if should_skip_stage(stage, manifest):
            logger.info(f"⏭️  Skipping - already completed")
            continue
        
        # Run stage
        start = time.time()
        try:
            success = func()
            duration = time.time() - start
            
            if success:
                # Validate output
                if not validate_stage_output(stage, movie_dir):
                    raise Exception(f"Output validation failed")
                
                # Record success
                manifest.set_pipeline_step(
                    stage, True, completed=True,
                    next_stage=next_stage, status="success",
                    duration=duration
                )
                logger.info(f"✓ Completed in {duration:.1f}s")
            else:
                raise Exception(f"Stage returned failure")
                
        except Exception as e:
            duration = time.time() - start
            
            if critical:
                # Critical failure - stop pipeline
                manifest.set_pipeline_step(
                    stage, False, completed=True,
                    next_stage=None, status="failed",
                    error=str(e), duration=duration
                )
                manifest.finalize(status="failed")
                logger.error(f"✗ Critical stage failed: {e}")
                return False
            else:
                # Optional failure - skip and continue
                manifest.set_pipeline_step(
                    stage, False, completed=True,
                    next_stage=next_stage, status="skipped",
                    notes=f"Failed: {str(e)}", duration=duration
                )
                logger.warning(f"⚠️ Optional stage failed: {e}")
                logger.info(f"   Continuing with next stage")
    
    # 6. Finalize
    manifest.finalize(status="completed")
    logger.info("")
    logger.info("=" * 60)
    logger.info("✓ PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
    return True

if __name__ == "__main__":
    success = run_complete_pipeline(sys.argv[1])
    sys.exit(0 if success else 1)
```

---

## 9. Troubleshooting Common Issues

### Issue: Pipeline stops during long-running stage
**Solution:**
- Increase timeout for that stage
- Use screen/tmux for session persistence
- Add periodic status logging
- Check container logs for crashes

### Issue: Stage appears complete but manifest not updated
**Solution:**
- Ensure manifest auto-save is enabled
- Call `manifest.set_pipeline_step()` AFTER stage completes
- Check file permissions on manifest.json
- Verify no exceptions thrown before manifest update

### Issue: Pipeline re-runs completed stages
**Solution:**
- Check `status="success"` is set (not "skipped")
- Verify stage name matches in `completed_stages`
- Implement `should_skip_stage()` check before each stage

### Issue: Can't resume after failure
**Solution:**
- Ensure `next_stage` is set even on failure/skip
- Check manifest.json is not corrupted
- Verify pipeline reads existing manifest on startup

---

## 10. Summary

**Key Principles:**
1. ✅ Initialize manifest at start with file path
2. ✅ Check `completed_stages` before each stage
3. ✅ ALWAYS set `next_stage` parameter (even on skip/fail)
4. ✅ Use `status="success"` for completed stages
5. ✅ Use `status="skipped"` for optional stages
6. ✅ Verify output files exist after each stage
7. ✅ Set appropriate timeouts for each stage
8. ✅ Wrap stages in try-except with proper error handling
9. ✅ Distinguish critical vs optional failures
10. ✅ Finalize manifest with final status

**Result:** Reliable, resumable, trackable pipeline execution with complete audit trail.
