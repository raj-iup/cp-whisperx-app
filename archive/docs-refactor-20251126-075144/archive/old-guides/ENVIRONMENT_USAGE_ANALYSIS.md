# Environment Usage Analysis - Pipeline Scripts

**Date:** 2025-11-20  
**Status:** ⚠️ **CRITICAL ISSUE IDENTIFIED**

---

## Executive Summary

**Problem:** The pipeline scripts are **NOT utilizing the multi-environment architecture** despite having 4 separate virtual environments configured.

**Impact:**
- ❌ All stages attempt to use `.bollyenv` (which doesn't exist)
- ❌ MLX environment (`venv/mlx`) is not being used (losing 7x speedup)
- ❌ Dependency conflicts will occur
- ❌ Pipeline likely fails or uses wrong Python environment

**Root Cause:** Scripts hardcode `.bollyenv` instead of dynamically selecting environments per stage.

---

## Current Situation (Broken)

### Evidence

#### 1. prepare-job.sh
```bash
Line 178: VENV_PATH=".bollyenv"  # Hardcoded, doesn't exist!
Line 197: log_info "Activating .bollyenv..."
```

#### 2. run-pipeline.sh  
```bash
Line 178: log_info "Activating .bollyenv..."
Line 180: VENV_PATH=".bollyenv"  # Hardcoded, doesn't exist!
```

#### 3. scripts/run-pipeline.py
```python
# Has EnvironmentManager initialized but NOT USING IT!
self.env_manager = EnvironmentManager(PROJECT_ROOT)  # Line 80

# All stages use:
subprocess.run(["python", ...])  # Uses system/active Python, not specific venv!
```

### Stage-to-Environment Mapping (FROM config/hardware_cache.json)

| Stage | Required Environment | Currently Using | Status |
|-------|---------------------|-----------------|--------|
| demux | whisperx | .bollyenv (missing) | ❌ |
| asr | **mlx** | .bollyenv (missing) | ❌ |
| alignment | whisperx | .bollyenv (missing) | ❌ |
| export_transcript | whisperx | .bollyenv (missing) | ❌ |
| load_transcript | indictrans2 | .bollyenv (missing) | ❌ |
| indictrans2_translation | indictrans2 | .bollyenv (missing) | ❌ |
| subtitle_generation | common | .bollyenv (missing) | ❌ |
| mux | common | .bollyenv (missing) | ❌ |

**Status:** 0/8 stages using correct environment ❌

---

## What Should Happen (Correct Architecture)

### Workflow

```
User
  │
  ├─ ./prepare-job.sh movie.mp4 --transcribe --translate
  │   ├─ Detects hardware (Apple Silicon)
  │   ├─ Sets WHISPER_BACKEND=mlx in job .env
  │   ├─ Validates required environments exist
  │   └─ NO environment activation (orchestrator handles it)
  │
  └─ ./run-pipeline.sh -j <job-id>
      ├─ Loads job .env
      ├─ Calls: python scripts/run-pipeline.py
      └─ Python pipeline (scripts/run-pipeline.py):
          │
          ├─ Stage: demux
          │   ├─ Query: env_manager.get_environment_for_stage("demux")
          │   ├─ Returns: "whisperx"
          │   └─ BUT: Uses FFmpeg (system tool), no venv needed
          │
          ├─ Stage: asr
          │   ├─ Query: env_manager.get_environment_for_stage("asr")
          │   ├─ Returns: "mlx"
          │   ├─ Get Python: env_manager.get_python_executable("mlx")
          │   ├─ Returns: /path/venv/mlx/bin/python
          │   └─ Run: env_manager.run_in_environment("mlx", ["script.py"])
          │       └─ ✅ Uses venv/mlx with MLX-Whisper (7x faster!)
          │
          ├─ Stage: alignment
          │   └─ ✅ Uses venv/whisperx
          │
          ├─ Stage: indictrans2_translation
          │   └─ ✅ Uses venv/indictrans2 (no torch conflicts!)
          │
          └─ Stage: subtitle_generation
              └─ ✅ Uses venv/common (lightweight)
```

---

## Required Changes

### Priority 1: Fix scripts/run-pipeline.py

**Problem:** Uses `subprocess.run(["python", ...])` without env selection

**Solution:** Use `self.env_manager.run_in_environment()` for all stages

**Stages to Fix:**

#### Stage: _stage_asr_mlx (line ~540)
```python
# ❌ Current (WRONG):
result = subprocess.run(
    ["python", str(temp_script)],
    ...
)

# ✅ Fixed (CORRECT):
env_name = self.env_manager.get_environment_for_stage("asr")  # Returns "mlx"
python_exe = self.env_manager.get_python_executable(env_name)
result = subprocess.run(
    [str(python_exe), str(temp_script)],
    ...
)
```

#### Stage: _stage_asr_whisperx (line ~647)
```python
# ✅ Fixed:
env_name = "whisperx"  # Or query from env_manager
python_exe = self.env_manager.get_python_executable(env_name)
# Use python_exe in command
```

#### Stage: _stage_indictrans2_translation (line ~810)
```python
# ❌ Current (WRONG):
cmd = ["python", "-c", script_content]
result = subprocess.run(cmd, ...)

# ✅ Fixed (CORRECT):
env_name = self.env_manager.get_environment_for_stage("indictrans2_translation")
python_exe = self.env_manager.get_python_executable(env_name)
cmd = [str(python_exe), "-c", script_content]
result = subprocess.run(cmd, ...)
```

#### Stage: _stage_demux (line ~429)
```python
# ✅ Already correct - uses FFmpeg directly (no Python venv needed)
result = subprocess.run(["ffmpeg", ...], ...)
```

---

### Priority 2: Fix run-pipeline.sh

**Problem:** Hardcoded `.bollyenv` activation

**Solution:** Remove activation - Python script handles per-stage environments

```bash
# ❌ Remove these lines (178-180):
log_info "Activating .bollyenv..."
VENV_PATH=".bollyenv"
source "$VENV_PATH/bin/activate"

# ✅ Replace with:
# No activation needed - Python pipeline handles per-stage environments
```

---

### Priority 3: Fix prepare-job.sh

**Problem:** Hardcoded `.bollyenv` reference

**Solution:** Validate multi-environment setup instead

```bash
# ❌ Remove these lines (178, 197):
VENV_PATH=".bollyenv"
log_info "Activating .bollyenv..."

# ✅ Replace with:
# Validate required environments exist
python3 -m shared.environment_manager validate --workflow "$WORKFLOW"
```

---

## Detailed Stage Execution Flow (Correct)

### Stage: ASR (Transcription) - Apple Silicon

```python
# Current flow in scripts/run-pipeline.py

def _stage_asr(self) -> bool:
    backend = self.env_config.get("WHISPER_BACKEND", "whisperx")
    
    if backend == "mlx":
        return self._stage_asr_mlx(...)
    else:
        return self._stage_asr_whisperx(...)

def _stage_asr_mlx(self, ...):
    # ✅ SHOULD DO:
    env_name = self.env_manager.get_environment_for_stage("asr")
    # Returns: "mlx"
    
    python_exe = self.env_manager.get_python_executable("mlx")
    # Returns: /path/venv/mlx/bin/python
    
    # Write temp script
    temp_script = output_dir / "asr_mlx_temp.py"
    with open(temp_script, 'w') as f:
        f.write(mlx_script_content)
    
    # ✅ Run in MLX environment
    result = subprocess.run(
        [str(python_exe), str(temp_script)],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(PROJECT_ROOT)
    )
    
    # Result: Uses venv/mlx with MLX-Whisper
    # Benefit: 7x faster transcription on Apple Silicon!
```

### Stage: Translation

```python
def _stage_indictrans2_translation(self) -> bool:
    # ✅ SHOULD DO:
    env_name = self.env_manager.get_environment_for_stage("indictrans2_translation")
    # Returns: "indictrans2"
    
    python_exe = self.env_manager.get_python_executable("indictrans2")
    # Returns: /path/venv/indictrans2/bin/python
    
    cmd = [str(python_exe), "-c", translation_script]
    
    result = subprocess.run(cmd, ...)
    
    # Result: Uses venv/indictrans2
    # Benefit: Has torch>=2.5.0, numpy>=2.1.0 (no conflicts!)
```

### Stage: Subtitle Generation

```python
def _stage_subtitle_generation(self) -> bool:
    # ✅ SHOULD DO:
    env_name = self.env_manager.get_environment_for_stage("subtitle_generation")
    # Returns: "common"
    
    python_exe = self.env_manager.get_python_executable("common")
    # Returns: /path/venv/common/bin/python
    
    # Generate SRT (pure Python, no ML libraries)
    # Uses lightweight venv/common
```

---

## Environment Manager API (Already Exists!)

The `shared/environment_manager.py` class provides all needed functionality:

```python
# Get environment for a stage
env_name = env_manager.get_environment_for_stage("asr")  
# Returns: "mlx"

# Get Python executable path
python_exe = env_manager.get_python_executable("mlx")
# Returns: Path("/path/venv/mlx/bin/python")

# Run command in environment
env_manager.run_in_environment(
    "mlx",
    ["python", "script.py"],
    capture_output=True
)

# Check if environment exists
if env_manager.is_environment_installed("mlx"):
    # Use it
    pass

# Validate workflow requirements
valid, missing = env_manager.validate_environments_for_workflow("transcribe")
# Returns: (True, []) if all envs exist
#          (False, ["mlx"]) if mlx missing
```

---

## Testing Plan

### 1. Test MLX Environment Usage

```bash
# Prepare job
./prepare-job.sh test.mp4 --transcribe -s hi

# Check job .env
cat out/.../job/.env | grep WHISPER_BACKEND
# Should show: WHISPER_BACKEND=mlx (on Apple Silicon)

# Run pipeline
./run-pipeline.sh -j <job-id>

# Verify MLX was used
cat out/.../job/logs/pipeline.log | grep -i mlx
# Should see: "Using MLX-Whisper"

# Check which Python was used
ps aux | grep python
# Should see: /path/venv/mlx/bin/python (while ASR running)
```

### 2. Test Translation Environment

```bash
# Prepare translation
./prepare-job.sh test.mp4 --translate -s hi -t en

# Run pipeline
./run-pipeline.sh -j <job-id>

# Verify indictrans2 env used
cat out/.../job/logs/pipeline.log | grep -i indictrans2
# Should see correct environment

# Check Python
ps aux | grep python
# Should see: /path/venv/indictrans2/bin/python (during translation)
```

### 3. Verify No Dependency Conflicts

```bash
# Run full subtitle workflow
./prepare-job.sh test.mp4 --subtitle -s hi -t en
./run-pipeline.sh -j <job-id>

# Should complete without import errors
# Each stage uses its designated environment
```

---

## Performance Impact

### Before Fix (Current Broken State)

```
All stages use system Python or whatever is active
  ↓
Dependency conflicts likely
  ↓
Pipeline fails OR uses wrong backend
  ↓
ASR: 120 minutes (CPU) - not using MLX!
```

### After Fix (Correct Implementation)

```
Each stage uses designated environment
  ↓
No dependency conflicts
  ↓
Optimal backend for each stage
  ↓
ASR: 17 minutes (MLX GPU) - 7x faster! ✅
Translation: No torch conflicts ✅
Subtitles: Lightweight common env ✅
```

**Net Benefit:** 103 minutes saved per 2-hour movie!

---

## Implementation Checklist

### Phase 1: Update Python Pipeline
- [ ] Update `_stage_asr_mlx()` to use `env_manager.get_python_executable("mlx")`
- [ ] Update `_stage_asr_whisperx()` to use `env_manager.get_python_executable("whisperx")`
- [ ] Update `_stage_indictrans2_translation()` to use `env_manager.get_python_executable("indictrans2")`
- [ ] Update `_stage_subtitle_generation()` to use `env_manager.get_python_executable("common")`
- [ ] Keep `_stage_demux()` as-is (uses system FFmpeg)

### Phase 2: Update Bash Scripts
- [ ] Remove `.bollyenv` hardcoding from `run-pipeline.sh`
- [ ] Remove `.bollyenv` hardcoding from `prepare-job.sh`
- [ ] Add environment validation in `prepare-job.sh`

### Phase 3: Testing
- [ ] Test transcribe workflow (verify MLX env used)
- [ ] Test translate workflow (verify indictrans2 env used)
- [ ] Test subtitle workflow (verify common env used)
- [ ] Verify no dependency conflicts
- [ ] Confirm 7x speedup on Apple Silicon

### Phase 4: Documentation
- [ ] Update README.md with multi-environment info
- [ ] Update TROUBLESHOOTING.md
- [ ] Create ENVIRONMENT_USAGE.md guide

---

## Summary

**Current Status:** ❌ **BROKEN**
- Multi-environment architecture exists but NOT USED
- All stages attempt `.bollyenv` (doesn't exist)
- MLX optimization lost (7x slower!)

**Required Action:** Update 3 files
1. `scripts/run-pipeline.py` - Use env_manager for all stages
2. `run-pipeline.sh` - Remove .bollyenv hardcoding
3. `prepare-job.sh` - Add environment validation

**Expected Result:** ✅ **WORKING**
- ASR uses `venv/mlx` (7x faster on Apple Silicon)
- Translation uses `venv/indictrans2` (no conflicts)
- Subtitles uses `venv/common` (lightweight)
- Each stage runs in optimal environment

**Impact:**
- **Performance:** 7x faster transcription
- **Reliability:** Zero dependency conflicts
- **Maintainability:** Clear environment separation

---

**Next Step:** Implement fixes in scripts to properly utilize multi-environment architecture.

**Priority:** HIGH - Current implementation is broken and loses significant performance benefits.

---

**Last Updated:** 2025-11-20  
**Status:** Analysis Complete - Implementation Needed
