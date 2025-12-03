# Multi-Environment Architecture

**Document Version:** 1.0  
**Last Updated:** December 3, 2025  
**Status:** ✅ Production-ready  
**Compliance Status:** 🎊 100% Perfect Compliance  
**Pre-commit Hook:** ✅ Active

## Overview

The cp-whisperx-app uses a sophisticated **multi-environment architecture** that allows different pipeline stages to run in isolated Python virtual environments with different dependency versions.

This architecture is what enabled us to safely upgrade whisperx to version 3.7.4 (torch 2.8.0) while keeping IndicTrans2 on torch 2.9.1 and MLX on its own version.

## Architecture Components

### 1. Environment Manager (`shared/environment_manager.py`)

The `EnvironmentManager` class provides centralized management of virtual environments:

```python
from shared.environment_manager import EnvironmentManager

env_manager = EnvironmentManager(project_root)

# Get environment for a stage
env_name = env_manager.get_environment_for_stage("asr")
# Returns: "whisperx"

# Get Python executable
python_exe = env_manager.get_python_executable("whisperx")
# Returns: /path/to/venv/whisperx/bin/python

# Check if environment is installed
is_installed = env_manager.is_environment_installed("indictrans2")
# Returns: True/False
```

**Key Methods:**
- `get_environment_for_stage(stage_name)` - Maps stage to environment
- `get_python_executable(env_name)` - Gets Python path for environment
- `get_activation_command(env_name)` - Gets activation script path
- `is_environment_installed(env_name)` - Validates environment exists
- `validate_environments_for_workflow(workflow)` - Checks all required environments

### 2. Hardware Cache (`config/hardware_cache.json`)

Central configuration file that defines:
- Available environments
- Stage-to-environment mappings
- Workflow-to-environments mappings
- Hardware capabilities

**Example structure:**

```json
{
  "version": "1.0.0",
  "hardware": {
    "platform": "darwin",
    "has_mps": true,
    "has_mlx": true
  },
  "environments": {
    "common": {
      "path": "venv/common",
      "purpose": "Core utilities"
    },
    "whisperx": {
      "path": "venv/whisperx",
      "purpose": "WhisperX ASR",
      "stages": ["demux", "asr", "alignment"]
    },
    "mlx": {
      "path": "venv/mlx",
      "purpose": "MLX acceleration",
      "stages": ["asr"]
    },
    "pyannote": {
      "path": "venv/pyannote",
      "purpose": "PyAnnote VAD",
      "stages": ["pyannote_vad"],
      "optional": true
    },
    "demucs": {
      "path": "venv/demucs",
      "purpose": "Audio source separation",
      "stages": ["source_separation"],
      "optional": true
    },
    "indictrans2": {
      "path": "venv/indictrans2",
      "purpose": "Translation",
      "stages": ["translation"]
    },
    "nllb": {
      "path": "venv/nllb",
      "purpose": "NLLB translation",
      "stages": ["nllb_translation"]
    }
  },
  "stage_to_environment_mapping": {
    "demux": "common",
    "source_separation": "demucs",
    "pyannote_vad": "pyannote",
    "asr": "whisperx",
    "alignment": "whisperx",
    "translation": "indictrans2",
    "nllb_translation": "nllb",
    "subtitle_gen": "common",
    "mux": "common"
  },
  "workflow_to_environments_mapping": {
    "transcribe": ["common", "whisperx", "pyannote", "demucs"],
    "translate": ["common", "whisperx", "indictrans2", "nllb", "pyannote", "demucs"],
    "subtitle": ["common", "whisperx", "indictrans2", "nllb", "pyannote", "demucs"]
  }
}
```

### 3. Prepare Job (`scripts/prepare-job.py`)

The prepare-job script sets up the job configuration with environment mappings:

```python
# Load environment manager
env_manager = EnvironmentManager(project_root)

# Validate required environments for workflow
all_valid, missing = env_manager.validate_environments_for_workflow(workflow)
if not all_valid:
    logger.error(f"Missing environments: {', '.join(missing)}")
    sys.exit(1)

# Build stage-to-environment mapping for this job
stage_environments = {}
stage_mapping = hardware_cache.get("stage_to_environment_mapping", {})

for stage, env in stage_mapping.items():
    if env in required_envs:
        stage_environments[stage] = env

# Save in job.json
job_config = {
    "job_id": job_id,
    "workflow": workflow,
    "stage_environments": stage_environments,
    ...
}
```

**What it does:**
1. Validates all required environments are installed
2. Creates stage-to-environment mapping for the job
3. Saves mapping in `job.json` for pipeline to use

### 4. Pipeline Orchestrator (`scripts/run-pipeline.py`)

The pipeline orchestrator executes stages in their designated environments:

```python
class IndicTrans2Pipeline:
    def __init__(self, job_dir: Path):
        self.env_manager = EnvironmentManager(project_root)
        self.job_config = self._load_config("job.json")
    
    def _get_stage_environment(self, stage_name: str) -> Optional[str]:
        """Get the required environment for a stage"""
        stage_envs = self.job_config.get("stage_environments", {})
        return stage_envs.get(stage_name)
    
    def _run_in_environment(self, stage_name: str, command: List[str], **kwargs):
        """Run a command in the appropriate environment for a stage"""
        env_name = self._get_stage_environment(stage_name)
        
        if env_name:
            # Get Python executable for this environment
            python_exe = self.env_manager.get_python_executable(env_name)
            
            # Set up environment variables
            env = os.environ.copy()
            env["VIRTUAL_ENV"] = str(self.env_manager.get_environment_path(env_name))
            env_bin = self.env_manager.get_environment_path(env_name) / "bin"
            env["PATH"] = f"{env_bin}:{env['PATH']}"
            
            # Replace python in command with environment-specific python
            if command[0] in ["python", "python3"]:
                command[0] = str(python_exe)
            
            return subprocess.run(command, env=env, **kwargs)
```

**What it does:**
1. Reads stage-environment mapping from `job.json`
2. For each stage, gets the appropriate Python executable
3. Sets up environment variables (`VIRTUAL_ENV`, `PATH`)
4. Executes stage script in the correct environment

## Environment Isolation in Action

### Example: Transcribe Workflow

```bash
./prepare-job.sh in/movie.mp4 --transcribe -s hi
./run-pipeline.sh -j job_20241120_001
```

**Stage execution:**

1. **demux** (audio extraction)
   - Environment: `venv/whisperx`
   - Python: `venv/whisperx/bin/python`
   - Dependencies: ffmpeg-python, torch 2.8.0

2. **asr** (speech recognition)
   - Environment: `venv/whisperx`
   - Python: `venv/whisperx/bin/python`
   - Dependencies: whisperx 3.7.4, torch 2.8.0, numpy 2.0.2

3. **alignment** (word timestamps)
   - Environment: `venv/whisperx`
   - Python: `venv/whisperx/bin/python`
   - Dependencies: whisperx 3.7.4, pyannote.audio 3.4.0

### Example: Translate Workflow

```bash
./prepare-job.sh in/movie.mp4 --translate -s hi -t en
./run-pipeline.sh -j job_20241120_002
```

**Stage execution:**

1. **demux** → `venv/whisperx` (torch 2.8.0)
2. **asr** → `venv/whisperx` (torch 2.8.0)
3. **alignment** → `venv/whisperx` (torch 2.8.0)
4. **translation** → `venv/indictrans2` (torch 2.9.1, numpy 2.3.5)
5. **subtitle_gen** → `venv/common` (no ML dependencies)

**Notice:** Stage 4 switches to a different environment with different PyTorch and NumPy versions!

### Example: MLX Acceleration (macOS)

On Apple Silicon, the ASR stage can optionally use MLX:

```bash
# Enable MLX for faster transcription
export USE_MLX=1
./prepare-job.sh in/movie.mp4 --transcribe -s hi
./run-pipeline.sh -j job_20241120_003
```

**Stage execution:**

1. **demux** → `venv/whisperx` (torch 2.8.0)
2. **asr** → `venv/mlx` (torch 2.9.1, mlx-whisper 0.4.3)
3. **alignment** → `venv/whisperx` (torch 2.8.0)

**Notice:** ASR stage switches to MLX environment, then switches back!

## Benefits of Multi-Environment Architecture

### 1. Dependency Isolation ✅

Different stages can use **incompatible dependency versions**:

| Environment | PyTorch | NumPy | Purpose |
|-------------|---------|-------|---------|
| venv/whisperx | 2.8.0 | 2.0.2 | WhisperX ASR |
| venv/mlx | 2.9.1 | 1.26.4 | MLX acceleration |
| venv/indictrans2 | 2.9.1 | 2.3.5 | Translation |
| venv/common | N/A | N/A | Utilities |

### 2. Safe Upgrades ✅

Upgrade one environment without affecting others:

```bash
# Upgrade whisperx to 3.7.4 (torch 2.8)
# Edit requirements-whisperx.txt
rm -rf venv/whisperx
./bootstrap.sh

# Other environments unchanged:
# - venv/indictrans2 still on torch 2.9.1
# - venv/mlx still on torch 2.9.1
```

### 3. Easy Rollback ✅

If upgrade causes issues, rollback is isolated:

```bash
# Rollback whisperx only
git checkout requirements-whisperx.txt
rm -rf venv/whisperx
./bootstrap.sh

# Other environments unaffected
```

### 4. Flexibility ✅

Add new environments for new features:

```bash
# Add new translation engine
cat > requirements-nllb.txt << EOF
transformers>=4.50.0
torch~=2.7.0
EOF

# Bootstrap will create venv/nllb
# Update hardware_cache.json to map stages
# No impact on existing environments
```

### 5. Testing ✅

Test different dependency versions side-by-side:

```bash
# Test whisperx 3.7.4 vs 3.3.1
cp requirements-whisperx.txt requirements-whisperx-3.7.4.txt
git checkout requirements-whisperx.txt  # Restore 3.3.1

# Create both environments
python -m venv venv/whisperx-3.7.4
python -m venv venv/whisperx-3.3.1

# Run same job with both
# Compare outputs
```

## Implementation Details

### Environment Switching

When the pipeline runs a stage:

```python
# 1. Pipeline reads job.json
stage_environments = {
    "asr": "whisperx",
    "translation": "indictrans2"
}

# 2. For ASR stage
env_name = "whisperx"
python_exe = "/path/to/venv/whisperx/bin/python"

# 3. Set environment variables
env = {
    "VIRTUAL_ENV": "/path/to/venv/whisperx",
    "PATH": "/path/to/venv/whisperx/bin:/usr/bin:...",
    "PYTHONPATH": "...",
}

# 4. Execute stage
subprocess.run([python_exe, "scripts/stages/asr.py"], env=env)

# 5. For translation stage (later)
env_name = "indictrans2"
python_exe = "/path/to/venv/indictrans2/bin/python"
# Different Python, different dependencies!
```

### No Cross-Contamination

Each environment has its own:
- Python executable
- Site-packages directory
- Pip cache
- Environment variables

**Result:** Zero dependency conflicts!

## Best Practices

### 1. Always Use Environment Manager

```python
# ✅ Good
from shared.environment_manager import EnvironmentManager
env_manager = EnvironmentManager()
python_exe = env_manager.get_python_executable("whisperx")

# ❌ Bad - hardcoded paths
python_exe = "/path/to/venv/whisperx/bin/python"
```

### 2. Update Hardware Cache

When adding new stages or environments:

```json
{
  "stage_to_environment_mapping": {
    "new_stage": "new_environment"
  },
  "environments": {
    "new_environment": {
      "path": ".venv-new",
      "purpose": "New feature",
      "stages": ["new_stage"]
    }
  }
}
```

### 3. Validate Environments

Before running pipeline:

```python
all_valid, missing = env_manager.validate_environments_for_workflow("subtitle")
if not all_valid:
    print(f"Missing: {missing}")
    print("Run: ./bootstrap.sh")
    sys.exit(1)
```

### 4. Log Environment Usage

Pipeline logs show which environment is used:

```
[INFO] Running stage 'asr' in environment 'whisperx'
[INFO] Python: /path/to/venv/whisperx/bin/python
```

## Troubleshooting

### Issue: Stage fails with import error

**Symptom:**
```
ModuleNotFoundError: No module named 'whisperx'
```

**Cause:** Wrong environment or environment not installed

**Solution:**
```bash
# Check environment mapping
cat config/hardware_cache.json | jq '.stage_to_environment_mapping'

# Verify environment exists
ls -la venv/whisperx/

# Recreate if needed
rm -rf venv/whisperx
./bootstrap.sh
```

### Issue: Wrong dependency version used

**Symptom:**
```
ImportError: torch 2.0 is required but 2.8 is installed
```

**Cause:** Stage running in wrong environment

**Solution:**
```bash
# Check job configuration
cat out/2024/11/20/user/001/job.json | jq '.stage_environments'

# Verify environment mapping is correct
# Update hardware_cache.json if needed
```

### Issue: Environment not found

**Symptom:**
```
ValueError: Unknown environment: whisperx
```

**Cause:** hardware_cache.json not updated after bootstrap

**Solution:**
```bash
# Regenerate hardware cache
./bootstrap.sh --force

# Or manually update config/hardware_cache.json
```

## Summary

The multi-environment architecture provides:

✅ **Isolation** - No dependency conflicts  
✅ **Flexibility** - Mix different library versions  
✅ **Safety** - Upgrade one environment at a time  
✅ **Rollback** - Easy to revert changes  
✅ **Scalability** - Add new environments easily  

This is the foundation that makes the cp-whisperx-app powerful and maintainable!

---

**Key Files:**
- `shared/environment_manager.py` - Environment management
- `config/hardware_cache.json` - Environment configuration
- `scripts/prepare-job.py` - Job setup with mappings
- `scripts/run-pipeline.py` - Stage execution with environments

**Key Concept:** Each stage runs in its own isolated Python environment with exactly the dependencies it needs.

---

## Related Documents

### Core Architecture
- **[System Architecture](architecture.md)** - Overall system design overview
- **[Pipeline Architecture](pipeline.md)** - Detailed stage-by-stage processing
- **[Architecture Index](../ARCHITECTURE_INDEX.md)** - Complete documentation index

### Development & Standards
- **[Developer Standards](../developer/DEVELOPER_STANDARDS.md)** - Code patterns and best practices
- **[Environment Manager](../../shared/environment_manager.py)** - Implementation details

### User Guides
- **[Bootstrap Guide](../user-guide/BOOTSTRAP.md)** - Environment setup instructions
- **[Configuration Guide](../user-guide/configuration.md)** - Configuration patterns

**Last Updated:** December 3, 2025
