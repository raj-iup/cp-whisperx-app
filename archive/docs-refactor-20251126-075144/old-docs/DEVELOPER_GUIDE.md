# Developer Guide

**Best practices, conventions, and guidelines for CP-WhisperX-App development**

---

## 📚 Table of Contents

1. [Getting Started](#getting-started)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Virtual Environment Management](#virtual-environment-management)
5. [Code Standards](#code-standards)
6. [Architecture Patterns](#architecture-patterns)
7. [Configuration Management](#configuration-management)
8. [Logging Standards](#logging-standards)
9. [Output Directory Structure](#output-directory-structure)
10. [Job Manifest System](#job-manifest-system)
11. [Adding New Parameters](#adding-new-parameters)
12. [Testing Guidelines](#testing-guidelines)
13. [Error Handling](#error-handling)
14. [Performance Optimization](#performance-optimization)
15. [Common Patterns](#common-patterns)
16. [Documentation Standards](#documentation-standards)
17. [Troubleshooting](#troubleshooting)

---

## 🚀 Getting Started

### Prerequisites

```bash
# Required
- Python 3.10+
- Git
- FFmpeg

# Recommended
- macOS or Linux (Windows via WSL)
- 16GB+ RAM
- Apple Silicon (MPS) or NVIDIA GPU (CUDA) for hardware acceleration
```

### Initial Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd cp-whisperx-app

# 2. Run bootstrap
./bootstrap.sh

# 3. Verify installation
./health-check.sh
```

### Development Environment

```bash
# Activate appropriate virtual environment
source venv/common/bin/activate     # For utilities
source venv/whisperx/bin/activate   # For ASR development
source venv/indictrans2/bin/activate # For translation development
```

---

## 📁 Project Structure

```
cp-whisperx-app/
├── scripts/              # Pipeline stages and utilities
│   ├── run-pipeline.py  # Main orchestrator
│   ├── prepare-job.py   # Job preparation
│   ├── source_separation.py
│   └── ...
│
├── shared/              # Shared utilities
│   ├── logger.py       # Logging infrastructure
│   ├── environment_manager.py
│   ├── config.py       # Configuration loader
│   └── stage_utils.py  # Stage helpers
│
├── config/              # Configuration files
│   ├── .env.pipeline   # Main configuration (ACTIVE - no .template)
│   ├── secrets.json
│   └── hardware_cache.json
│
├── docs/                # Documentation
│   ├── INDEX.md        # Documentation index
│   ├── PROCESS.md      # Development process
│   ├── DEVELOPER_GUIDE.md  # This file
│   ├── user-guide/     # User documentation
│   ├── technical/      # Technical documentation
│   └── reference/      # Reference documentation
│
├── in/                  # Input media
├── out/                 # Output directory
├── logs/                # Application logs
│
├── venv/common/        # Common utilities environment
├── venv/whisperx/      # WhisperX ASR environment
├── venv/indictrans2/   # IndicTrans2 translation
├── venv/nllb/          # NLLB translation
└── venv/pyannote/      # Speaker diarization

├── bootstrap.sh         # Environment setup
├── prepare-job.sh       # Job preparation wrapper
├── run-pipeline.sh      # Pipeline execution wrapper
└── health-check.sh      # System health check
```

### Key Directories

**`scripts/`** - All pipeline stages and orchestration logic
- One file per stage (e.g., `source_separation.py`, `asr.py`)
- Main orchestrator: `run-pipeline.py`
- Job preparation: `prepare-job.py`

**`shared/`** - Reusable utilities across all stages
- **logger.py** - Centralized logging (SINGLE SOURCE OF TRUTH)
- **environment_manager.py** - Virtual environment handling
- **config.py** - Configuration loading
- **stage_utils.py** - Stage I/O helpers

**`config/`** - Configuration templates and secrets
- **SINGLE SOURCE:** `config/.env.pipeline` (no .template file)
- Never commit secrets.json to git
- All parameters defined in `.env.pipeline`

---

## 🐍 Virtual Environment Management

### Why Multi-Environment Architecture?

**Problem:** Dependency conflicts between ML libraries
- WhisperX requires specific PyTorch versions
- IndicTrans2 has conflicting dependencies
- NLLB needs different transformers versions
- PyAnnote has incompatible package versions

**Solution:** Isolated virtual environments per component

```
venv/common/       # Shared utilities (no ML dependencies)
venv/whisperx/     # WhisperX ASR
venv/indictrans2/  # IndicTrans2 translation
venv/nllb/         # NLLB translation
venv/pyannote/     # PyAnnote diarization
```

### Creating New Virtual Environments

**❌ WRONG - Don't do this:**
```bash
# Installing everything in one environment
pip install whisperx indictrans2 nllb pyannote
# This will cause dependency conflicts!
```

**✅ CORRECT - Isolated environments:**

```bash
# 1. Create new environment
python3 -m venv .venv-myfeature

# 2. Activate it
source .venv-myfeature/bin/activate

# 3. Install ONLY what this feature needs
pip install <specific-packages>

# 4. Create requirements file
pip freeze > requirements-myfeature.txt

# 5. Add to EnvironmentManager
# Edit shared/environment_manager.py
```

### Adding New Environment to System

**File:** `shared/environment_manager.py`

```python
# 1. Add to AVAILABLE_ENVIRONMENTS
AVAILABLE_ENVIRONMENTS = {
    "common": "venv/common",
    "whisperx": "venv/whisperx",
    "indictrans2": "venv/indictrans2",
    "nllb": "venv/nllb",
    "pyannote": "venv/pyannote",
    "myfeature": ".venv-myfeature",  # NEW
}

# 2. Add to stage mapping (if needed)
def get_stage_environment(self, stage_name: str) -> str:
    mapping = {
        "asr": "whisperx",
        "translation": "indictrans2",
        "my_new_stage": "myfeature",  # NEW
    }
    return mapping.get(stage_name, "common")
```

### Best Practices

```bash
# ✅ GOOD - Use specific environment
source venv/whisperx/bin/activate
python scripts/asr.py

# ❌ BAD - Using system Python
python scripts/asr.py  # May use wrong dependencies

# ✅ GOOD - Let EnvironmentManager handle it
# The pipeline automatically activates correct environment per stage

# ✅ GOOD - Clean environment
source venv/common/bin/activate
pip list  # Check what's installed

# ❌ BAD - Mixing environments
source venv/whisperx/bin/activate
pip install indictrans2  # NO! Creates conflicts
```

### Testing Environment Isolation

```bash
# Verify environments are isolated
for env in .venv-*; do
    echo "=== $env ==="
    source $env/bin/activate
    pip list | grep torch
    deactivate
done
```

---

## 🔄 Development Workflow

### Before Starting

**ALWAYS read [PROCESS.md](PROCESS.md) first!**

The 6-step process:
1. **Analyze** - Understand the issue
2. **Plan** - Design the solution
3. **Implement** - Make minimal changes
4. **Test** - Verify it works
5. **Document** - Update docs
6. **Commit** - Commit with clear message

### Making Changes

```bash
# 1. Create feature branch (optional)
git checkout -b fix/source-separation-default

# 2. Make changes
# Follow code standards below

# 3. Test changes
./run-pipeline.sh -j <test-job-id>

# 4. Check logs
tail -f out/<date>/<user>/<job>/logs/*.log

# 5. Update documentation
# Always update relevant docs in docs/

# 6. Commit
git add <files>
git commit -m "fix: enable source separation by default"
```

### Commit Message Format

```bash
# Format: <type>: <description>

# Types:
fix:      Bug fix
feat:     New feature
docs:     Documentation only
refactor: Code restructuring (no behavior change)
test:     Test additions/changes
chore:    Build/tooling changes
perf:     Performance improvements

# Examples:
git commit -m "fix: source_separation stage environment mapping"
git commit -m "feat: add anti-hallucination system"
git commit -m "docs: update developer guide with logging standards"
git commit -m "refactor: simplify environment resolution logic"
```

---

## 📝 Code Standards

### Python Style

```python
# Use Python 3.10+ features
from typing import Optional, Dict, List
from pathlib import Path

# Function signatures: Type hints always
def process_audio(
    input_path: Path,
    output_dir: Path,
    quality: str = "balanced"
) -> Optional[Path]:
    """
    Process audio with source separation.
    
    Args:
        input_path: Path to input audio file
        output_dir: Directory for output files
        quality: Quality preset (fast/balanced/quality)
    
    Returns:
        Path to processed audio, or None if failed
    """
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_QUALITY = "balanced"

# Classes: PascalCase
class PipelineOrchestrator:
    pass

# Functions/variables: snake_case
def load_configuration():
    pass

user_id = 1
```

### File Organization

```python
#!/usr/bin/env python3
"""
Module docstring explaining purpose.

This module handles source separation for audio processing.
Uses Demucs model to extract vocals from background music.
"""

# Standard library imports
import sys
import os
from pathlib import Path
from typing import Optional, Dict

# Third-party imports
import torch
import numpy as np

# Local imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.logger import PipelineLogger
from shared.config import Config

# Constants
DEFAULT_QUALITY = "balanced"
MAX_RETRIES = 3

# Module-level variables
PROJECT_ROOT = Path(__file__).parent.parent

# Functions
def main():
    """Main entry point."""
    pass

# Entry point
if __name__ == "__main__":
    sys.exit(main())
```

### Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Files | snake_case.py | `source_separation.py` |
| Classes | PascalCase | `PipelineOrchestrator` |
| Functions | snake_case() | `load_configuration()` |
| Variables | snake_case | `user_id`, `input_path` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Private | _leading_underscore | `_internal_helper()` |

### Documentation

```python
def process_stage(
    input_data: Dict,
    config: Dict,
    logger: PipelineLogger
) -> bool:
    """
    Process a pipeline stage with given configuration.
    
    This function orchestrates the execution of a single pipeline stage,
    handling environment setup, execution, and error recovery.
    
    Args:
        input_data: Input data from previous stage
        config: Stage-specific configuration
        logger: Logger instance for this stage
    
    Returns:
        True if stage completed successfully, False otherwise
    
    Raises:
        ValueError: If configuration is invalid
        RuntimeError: If stage execution fails
    
    Example:
        >>> config = {"quality": "balanced"}
        >>> success = process_stage(input_data, config, logger)
        >>> if success:
        ...     print("Stage completed")
    """
    pass
```

---

## 🏗️ Architecture Patterns

### Multi-Environment Pattern

**Always use the environment manager for stage execution:**

```python
from shared.environment_manager import EnvironmentManager

# Initialize
env_manager = EnvironmentManager(PROJECT_ROOT)

# Get environment for stage
env_name = self._get_stage_environment("asr")  # Returns "whisperx"
python_exe = env_manager.get_python_executable(env_name)

# Run command in environment
result = self._run_in_environment(
    "asr",
    [python_exe, str(script_path)],
    env=env
)
```

### Stage Pattern

**Every stage should follow this pattern:**

```python
#!/usr/bin/env python3
"""Stage: Source Separation"""
import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import Config

def main():
    """Execute stage."""
    # 1. Initialize stage I/O
    stage_io = StageIO("source_separation")
    logger = get_stage_logger("source_separation", stage_io=stage_io)
    
    # 2. Log stage start
    logger.info("=" * 60)
    logger.info("SOURCE SEPARATION STAGE")
    logger.info("=" * 60)
    
    # 3. Check if stage is enabled
    enabled = os.environ.get('SOURCE_SEPARATION_ENABLED', 'false').lower() == 'true'
    if not enabled:
        logger.info("Source separation is disabled (skipping)")
        return 0
    
    # 4. Get input from previous stage
    input_audio = stage_io.get_input_path("audio.wav", from_stage="demux")
    if not input_audio.exists():
        logger.error(f"Input not found: {input_audio}")
        return 1
    
    # 5. Process
    try:
        output = process_audio(input_audio, stage_io.stage_dir, logger)
        if not output:
            logger.error("Processing failed")
            return 1
    except Exception as e:
        logger.error(f"Stage failed: {e}")
        return 1
    
    # 6. Save output
    stage_io.save_output("vocals.wav", output)
    
    # 7. Log completion
    logger.info("=" * 60)
    logger.info("✓ Stage completed successfully")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Configuration Pattern

**Never read os.environ directly. Always use Config:**

```python
# ❌ WRONG - Don't do this
quality = os.environ.get('QUALITY', 'balanced')

# ✅ CORRECT - Use Config
from shared.config import Config

config = Config(PROJECT_ROOT)
quality = config.get('SOURCE_SEPARATION_QUALITY', 'balanced')
```

### Default Values Pattern

**Important features should be enabled by default:**

```python
# ❌ WRONG - Requiring users to opt-in
def prepare_job(source_separation: bool = False):
    pass

# ✅ CORRECT - Enabled by default, opt-out if needed
def prepare_job(source_separation: bool = True):
    """
    Prepare job with source separation enabled by default.
    Use source_separation=False to disable.
    """
    pass
```

---

## 🧪 Testing Guidelines

### Manual Testing

```bash
# 1. Create test job
./prepare-job.sh \
  --media "in/test.mp4" \
  --workflow subtitle \
  --source-lang hi \
  --target-langs en \
  --start "00:00:00" \
  --end "00:01:00" \
  --debug

# 2. Run pipeline
./run-pipeline.sh -j <job-id>

# 3. Check logs
tail -f out/<date>/<user>/<job>/logs/*.log

# 4. Verify output
ls -lh out/<date>/<user>/<job>/media/
ls -lh out/<date>/<user>/<job>/subtitles/
```

### Test Cases

**Always test:**
1. ✅ Default behavior
2. ✅ Explicit enable/disable
3. ✅ Error conditions
4. ✅ Edge cases
5. ✅ Backward compatibility

### Example Test Checklist

```markdown
- [ ] Default configuration works
- [ ] Can disable feature with flag
- [ ] Handles missing input gracefully
- [ ] Logs are clear and informative
- [ ] No hardcoded paths
- [ ] Works with different languages
- [ ] Backward compatible with old jobs
- [ ] Documentation updated
```

---

## 📊 Logging Standards

### Logger Initialization

**ALWAYS use module name in logger:**

```python
# For standalone scripts
from shared.stage_utils import get_stage_logger

logger = get_stage_logger("source_separation", stage_io=stage_io)

# For classes (run-pipeline.py)
from shared.logger import PipelineLogger

self.logger = PipelineLogger(
    module_name="pipeline",
    log_file=log_file,
    log_level="DEBUG" if debug else "INFO"
)
```

### Log Format

**Standard format:** `[timestamp] [module_name] [level] message`

```python
# Examples
logger.info("Starting source separation...")
# [2025-11-21 12:00:00] [source_separation] [INFO] Starting source separation...

logger.debug(f"Processing {file_path}")
# [2025-11-21 12:00:01] [source_separation] [DEBUG] Processing /path/to/file

logger.error(f"Failed: {error}")
# [2025-11-21 12:00:02] [source_separation] [ERROR] Failed: File not found
```

### Logging Levels

| Level | Usage |
|-------|-------|
| `DEBUG` | Detailed information for debugging |
| `INFO` | General informational messages |
| `WARNING` | Warning messages (non-critical issues) |
| `ERROR` | Error messages (recoverable errors) |
| `CRITICAL` | Critical errors (unrecoverable) |

### Logging Best Practices

```python
# ✅ GOOD - Clear, actionable messages
logger.info("Starting ASR processing...")
logger.info(f"Processing audio: {audio_file}")
logger.debug(f"Using model: {model_name}, device: {device}")
logger.error(f"ASR failed: {error_message}")

# ❌ BAD - Vague or useless messages
logger.info("Processing...")
logger.debug("Debug info")
logger.error("Error occurred")

# ✅ GOOD - Log stage boundaries
logger.info("=" * 60)
logger.info("ASR STAGE: Automatic Speech Recognition")
logger.info("=" * 60)
# ... processing ...
logger.info("✓ ASR completed successfully")

# ✅ GOOD - Log important metrics
logger.info(f"Audio duration: {duration:.2f}s")
logger.info(f"Processing time: {elapsed:.1f}s")
logger.info(f"Output size: {size_mb:.1f} MB")

# ✅ GOOD - Use traceback in DEBUG mode
try:
    result = process()
except Exception as e:
    logger.error(f"Processing failed: {e}")
    if self.debug:
        logger.error(f"Traceback: {traceback.format_exc()}")
```

---

## ⚙️ Configuration Management

### Configuration Hierarchy

**CRITICAL RULES:**
1. ❌ **NEVER use hardcoded values** in code
2. ❌ **NEVER read os.environ directly**
3. ✅ **ALWAYS define parameters in config/.env.pipeline**
4. ✅ **ALWAYS use Config class to read values**
5. ✅ **ALWAYS provide sensible defaults**

### Configuration Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. config/.env.pipeline                                     │
│    - Master configuration (SINGLE SOURCE)                   │
│    - All parameters defined here                            │
│    - Committed to git                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. prepare-job.py reads config/.env.pipeline               │
│    - Loads all parameters                                   │
│    - Injects hardware detection                             │
│    - Adds job-specific values                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Creates: out/<date>/<user>/<job>/.job-<id>.env          │
│    - Job-specific configuration                             │
│    - Contains all parameters for this job                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Stage scripts read via Config class                     │
│    - config = Config(PROJECT_ROOT)                          │
│    - value = config.get('PARAM_NAME', default)              │
└─────────────────────────────────────────────────────────────┘
```

### Reading Configuration

**❌ WRONG - Hardcoded values:**
```python
# DON'T DO THIS!
quality = "balanced"  # Hardcoded
batch_size = 8        # Hardcoded
timeout = 300         # Hardcoded
```

**❌ WRONG - Reading os.environ directly:**
```python
# DON'T DO THIS!
quality = os.environ.get('QUALITY', 'balanced')
batch_size = int(os.environ.get('BATCH_SIZE', '8'))
```

**✅ CORRECT - Use Config class:**
```python
from shared.config import Config

# Initialize
config = Config(PROJECT_ROOT)

# Read with defaults
quality = config.get('SOURCE_SEPARATION_QUALITY', 'balanced')
batch_size = config.get('BATCH_SIZE', 8)
timeout = config.get('PROCESSING_TIMEOUT', 300)
device = config.get('DEVICE', 'cpu')

# Read secrets
api_key = config.get_secret('HUGGINGFACE_TOKEN')
```

### Configuration Best Practices

```python
# ✅ GOOD - Always provide defaults
quality = config.get('QUALITY', 'balanced')

# ❌ BAD - No default (could be None)
quality = config.get('QUALITY')

# ✅ GOOD - Validate configuration
if quality not in ['fast', 'balanced', 'quality']:
    logger.error(f"Invalid quality: {quality}, using 'balanced'")
    quality = 'balanced'

# ✅ GOOD - Log configuration at start
logger.info("Configuration:")
logger.info(f"  Quality: {quality}")
logger.info(f"  Batch size: {batch_size}")
logger.info(f"  Device: {device}")
logger.info(f"  Timeout: {timeout}s")

# ✅ GOOD - Type-safe reading
batch_size = int(config.get('BATCH_SIZE', 8))
enabled = config.get('FEATURE_ENABLED', 'false').lower() == 'true'
threshold = float(config.get('THRESHOLD', 0.5))
```

---

## 📁 Output Directory Structure

### Standard Structure

Every job creates a standard output structure:

```
out/
└── <year>/              # 2025
    └── <month>/         # 11
        └── <day>/       # 21
            └── <user>/  # rpatel
                └── <job_number>/  # 7
                    ├── .job-<id>.env      # Job configuration
                    ├── job.json           # Job metadata
                    ├── manifest.json      # Stage tracking
                    │
                    ├── media/             # Media files
                    │   ├── <original>.mp4
                    │   ├── audio.wav      # Extracted audio
                    │   └── <title>_subtitled.mp4  # Final output
                    │
                    ├── transcripts/       # Transcription files
                    │   ├── segments.json  # Full segments
                    │   ├── transcript.txt # Plain text
                    │   └── transcript.json # JSON format
                    │
                    ├── translations/      # Translation files (per language)
                    │   ├── en/
                    │   │   ├── segments.json
                    │   │   └── translation.txt
                    │   └── gu/
                    │       ├── segments.json
                    │       └── translation.txt
                    │
                    ├── subtitles/         # Subtitle files
                    │   ├── <title>.hi.srt  # Source language
                    │   ├── <title>.en.srt  # Target language 1
                    │   └── <title>.gu.srt  # Target language 2
                    │
                    └── logs/              # Stage logs
                        ├── 01_demux_<timestamp>.log
                        ├── 02_source_separation_<timestamp>.log
                        ├── 03_pyannote_vad_<timestamp>.log
                        └── ...
```

### Creating Output Directories

**✅ CORRECT - Use StageIO:**
```python
from shared.stage_utils import StageIO

# Initialize
stage_io = StageIO("my_stage")

# Directories are created automatically
# stage_io.stage_dir = out/<date>/<user>/<job>/my_stage/

# Get input from previous stage
input_file = stage_io.get_input_path("audio.wav", from_stage="demux")
# Looks in: out/<date>/<user>/<job>/media/audio.wav

# Save output
output_file = stage_io.stage_dir / "output.json"
process_data(input_file, output_file)
stage_io.save_output("output.json", output_file)
```

**❌ WRONG - Manual path construction:**
```python
# DON'T DO THIS!
output_dir = Path("out/2025/11/21/user/1")  # Hardcoded
output_file = output_dir / "output.json"
```

### Path Best Practices

```python
# ✅ GOOD - Use StageIO for all I/O
stage_io = StageIO("my_stage")
input_path = stage_io.get_input_path("data.json", from_stage="previous")
output_path = stage_io.stage_dir / "result.json"

# ✅ GOOD - Create directories with parents
output_path.parent.mkdir(parents=True, exist_ok=True)

# ✅ GOOD - Use Path objects, not strings
from pathlib import Path
config_path = PROJECT_ROOT / "config" / ".env.pipeline"

# ❌ BAD - String concatenation
config_path = PROJECT_ROOT + "/config/.env.pipeline"
```

---

## 📋 Job Manifest System

### Manifest Structure

Every job has a `manifest.json` tracking all stages:

```json
{
  "job_id": "job-20251121-rpatel-0007",
  "workflow": "subtitle",
  "status": "running",
  "created_at": "2025-11-21T10:30:00",
  "started_at": "2025-11-21T10:30:15",
  "completed_at": null,
  "stages": [
    {
      "name": "demux",
      "status": "completed",
      "started_at": "2025-11-21T10:30:15",
      "completed_at": "2025-11-21T10:30:17",
      "duration": 2.1
    },
    {
      "name": "source_separation",
      "status": "running",
      "started_at": "2025-11-21T10:30:17",
      "completed_at": null,
      "duration": null
    },
    {
      "name": "asr",
      "status": "pending",
      "started_at": null,
      "completed_at": null,
      "duration": null
    }
  ]
}
```

### Updating Manifest

**The pipeline orchestrator handles manifest updates automatically.**

But if you need to update manually:

```python
import json
from pathlib import Path
from datetime import datetime

def update_stage_status(job_dir: Path, stage_name: str, status: str):
    """Update stage status in manifest."""
    manifest_file = job_dir / "manifest.json"
    
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)
    
    # Find stage
    for stage in manifest['stages']:
        if stage['name'] == stage_name:
            stage['status'] = status
            if status == 'running':
                stage['started_at'] = datetime.now().isoformat()
            elif status in ['completed', 'failed']:
                stage['completed_at'] = datetime.now().isoformat()
                if stage['started_at']:
                    start = datetime.fromisoformat(stage['started_at'])
                    end = datetime.now()
                    stage['duration'] = (end - start).total_seconds()
            break
    
    # Save
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
```

### Checking Stage Status

```python
def get_stage_status(job_dir: Path, stage_name: str) -> str:
    """Get current status of a stage."""
    manifest_file = job_dir / "manifest.json"
    
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)
    
    for stage in manifest['stages']:
        if stage['name'] == stage_name:
            return stage['status']
    
    return None
```

---

## ➕ Adding New Parameters

### Process Overview

**CRITICAL: Never add command-line parameters!**
**All parameters MUST be in config/.env.pipeline**

### Step-by-Step Guide

#### 1. Add Parameter to config/.env.pipeline

```bash
# Edit config/.env.pipeline
# Add to appropriate section with documentation

# ============================================================
# [NEW FEATURE] MY FEATURE SETTINGS
# ============================================================
# Purpose: Description of what this feature does
# Input: What data it needs
# Output: What it produces
# Critical: Yes/No
# ============================================================

# Enable/disable feature
MY_FEATURE_ENABLED=true

# Feature-specific settings
MY_FEATURE_QUALITY=balanced
MY_FEATURE_THRESHOLD=0.7
MY_FEATURE_MAX_RETRIES=3
MY_FEATURE_TIMEOUT=300
```

#### 2. Read Parameter in Code

```python
from shared.config import Config

# In your stage/script
config = Config(PROJECT_ROOT)

# Read with sensible defaults
enabled = config.get('MY_FEATURE_ENABLED', 'false').lower() == 'true'
quality = config.get('MY_FEATURE_QUALITY', 'balanced')
threshold = float(config.get('MY_FEATURE_THRESHOLD', 0.7))
max_retries = int(config.get('MY_FEATURE_MAX_RETRIES', 3))
timeout = int(config.get('MY_FEATURE_TIMEOUT', 300))

# Validate
if quality not in ['fast', 'balanced', 'quality']:
    logger.warning(f"Invalid quality: {quality}, using 'balanced'")
    quality = 'balanced'
```

#### 3. Update Job Configuration (if needed)

If parameter needs to be job-specific:

**File:** `scripts/prepare-job.py`

```python
def create_job_config(...):
    job_config = {
        "job_id": job_id,
        "workflow": workflow,
        # ... existing fields ...
        
        # Add new feature config
        "my_feature": {
            "enabled": True,  # or from parameter
            "quality": "balanced",
            "threshold": 0.7
        }
    }
```

#### 4. Document the Parameter

Update documentation:
- `docs/user-guide/configuration.md` - User-facing docs
- `docs/technical/architecture.md` - Technical details
- `docs/DEVELOPER_GUIDE.md` - This file

#### 5. Test the Parameter

```bash
# Test with default
./prepare-job.sh --media test.mp4 --workflow transcribe --source-lang hi

# Verify in job config
cat out/<date>/<user>/<job>/.job-<id>.env | grep MY_FEATURE

# Test the feature
./run-pipeline.sh -j <job-id>
```

### Example: Adding a New Quality Setting

**1. Add to config/.env.pipeline:**
```bash
# ============================================================
# [STAGE X] NEW STAGE SETTINGS
# ============================================================
NEW_STAGE_ENABLED=true
NEW_STAGE_QUALITY=balanced  # Options: fast, balanced, quality
NEW_STAGE_MODEL=base
NEW_STAGE_DEVICE=auto  # auto, mps, cuda, cpu
```

**2. Read in stage script:**
```python
#!/usr/bin/env python3
"""Stage: New Stage"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import Config

def main():
    stage_io = StageIO("new_stage")
    logger = get_stage_logger("new_stage", stage_io=stage_io)
    config = Config(PROJECT_ROOT)
    
    # Read parameters (NO HARDCODED VALUES!)
    enabled = config.get('NEW_STAGE_ENABLED', 'false').lower() == 'true'
    quality = config.get('NEW_STAGE_QUALITY', 'balanced')
    model = config.get('NEW_STAGE_MODEL', 'base')
    device = config.get('NEW_STAGE_DEVICE', 'auto')
    
    # Validate
    if quality not in ['fast', 'balanced', 'quality']:
        logger.warning(f"Invalid quality: {quality}, using 'balanced'")
        quality = 'balanced'
    
    # Log configuration
    logger.info("Configuration:")
    logger.info(f"  Enabled: {enabled}")
    logger.info(f"  Quality: {quality}")
    logger.info(f"  Model: {model}")
    logger.info(f"  Device: {device}")
    
    if not enabled:
        logger.info("Stage disabled (skipping)")
        return 0
    
    # Process...
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**3. Update documentation:**
```bash
# Immediately update docs
vim docs/user-guide/features/new-feature.md
vim docs/INDEX.md  # Add link
```

### ❌ What NOT to Do

```bash
# ❌ WRONG - Don't add command-line parameters
# Don't add to prepare-job.sh:
--new-feature-quality QUALITY

# ❌ WRONG - Don't hardcode values
quality = "balanced"

# ❌ WRONG - Don't read os.environ directly
quality = os.environ.get('QUALITY', 'balanced')

# ❌ WRONG - Don't create separate config files
# Don't create: config/new_feature.json

# ✅ CORRECT - Everything in config/.env.pipeline
# Read via Config class
```

---
2. **Template** (`config/.env.pipeline.template`)
3. **Job config** (`job.json`)
4. **Job environment** (`.{job_id}.env`)

### Loading Configuration

```python
from shared.config import Config

# Initialize config loader
config = Config(PROJECT_ROOT)

# Get values with defaults
quality = config.get('SOURCE_SEPARATION_QUALITY', 'balanced')
batch_size = config.get('BATCH_SIZE', 8)
enabled = config.get('SOURCE_SEPARATION_ENABLED', True)

# Get secrets (API keys, tokens)
api_key = config.get_secret('HUGGINGFACE_TOKEN')
```

### Configuration Best Practices

```python
# ✅ GOOD - Use config with defaults
quality = config.get('QUALITY', 'balanced')

# ❌ BAD - No default
quality = config.get('QUALITY')  # Could be None

# ✅ GOOD - Validate configuration
if quality not in ['fast', 'balanced', 'quality']:
    logger.error(f"Invalid quality: {quality}")
    return 1

# ✅ GOOD - Log configuration
logger.info(f"Configuration:")
logger.info(f"  Quality: {quality}")
logger.info(f"  Batch size: {batch_size}")
logger.info(f"  Device: {device}")
```

---

## 🚨 Error Handling

### Exception Handling Pattern

```python
def process_stage():
    """Process stage with proper error handling."""
    try:
        # Main processing logic
        result = do_processing()
        return result
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return None
        
    except subprocess.TimeoutExpired:
        logger.error("Processing timed out")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if debug:
            logger.error(f"Traceback: {traceback.format_exc()}")
        return None
```

### Graceful Degradation

```python
# ✅ GOOD - Fallback to CPU if GPU fails
def get_device():
    """Get best available device with fallback."""
    if torch.cuda.is_available():
        try:
            # Test CUDA
            torch.zeros(1).cuda()
            return "cuda"
        except Exception as e:
            logger.warning(f"CUDA test failed: {e}, falling back to CPU")
    
    if torch.backends.mps.is_available():
        try:
            # Test MPS
            torch.zeros(1).to("mps")
            return "mps"
        except Exception as e:
            logger.warning(f"MPS test failed: {e}, falling back to CPU")
    
    return "cpu"
```

### Retry Pattern

```python
import time

def process_with_retry(func, max_retries=3, delay=1.0):
    """Retry function on failure."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries} attempts failed")
                raise
```

---

## ⚡ Performance Optimization

### Batch Processing

```python
# ✅ GOOD - Process in batches
def process_segments(segments, batch_size=8):
    """Process segments in batches."""
    results = []
    for i in range(0, len(segments), batch_size):
        batch = segments[i:i + batch_size]
        batch_results = model.process(batch)
        results.extend(batch_results)
    return results

# ❌ BAD - Process one by one
for segment in segments:
    result = model.process(segment)  # Inefficient
```

### Resource Management

```python
# ✅ GOOD - Use context managers
with open(file_path, 'r') as f:
    data = f.read()

# ✅ GOOD - Clean up temporary files
import tempfile
import shutil

temp_dir = tempfile.mkdtemp()
try:
    # Use temp_dir
    process_files(temp_dir)
finally:
    # Always clean up
    shutil.rmtree(temp_dir, ignore_errors=True)
```

### Caching

```python
from functools import lru_cache

# Cache expensive operations
@lru_cache(maxsize=128)
def load_model(model_name: str):
    """Load model with caching."""
    logger.info(f"Loading model: {model_name}")
    return Model.load(model_name)
```

---

## 🎯 Common Patterns

### Stage Input/Output

```python
from shared.stage_utils import StageIO

# Initialize
stage_io = StageIO("my_stage")

# Get input from previous stage
input_file = stage_io.get_input_path("audio.wav", from_stage="demux")

# Save output for next stage
output_file = stage_io.stage_dir / "processed.wav"
process_audio(input_file, output_file)
stage_io.save_output("processed.wav", output_file)
```

### Progress Indication

```python
# ✅ GOOD - Show progress for long operations
logger.info(f"Processing {total} items...")
for i, item in enumerate(items, 1):
    process(item)
    if i % 100 == 0:
        logger.info(f"Processed {i}/{total} items ({i*100//total}%)")
logger.info(f"✓ All {total} items processed")
```

### Environment Detection

```python
from shared.environment_manager import EnvironmentManager

env_manager = EnvironmentManager(PROJECT_ROOT)

# Check if environment is installed
if env_manager.is_environment_installed("whisperx"):
    # Use WhisperX
    pass
else:
    logger.error("WhisperX environment not found")
    logger.error("Run: ./install-whisperx.sh")
    return 1
```

---

## 🔧 Troubleshooting

### Common Issues

**Issue: Module not found**
```bash
# Solution: Add project root to path
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

**Issue: Environment not found**
```bash
# Solution: Check environment is installed
./health-check.sh

# Reinstall if needed
./bootstrap.sh
```

**Issue: GPU not detected**
```bash
# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Check MPS (Apple Silicon)
python -c "import torch; print(torch.backends.mps.is_available())"
```

### Debugging Tips

```bash
# 1. Enable debug mode
./prepare-job.sh --debug ...

# 2. Watch logs in real-time
tail -f out/<date>/<user>/<job>/logs/*.log

# 3. Check stage outputs
ls -lh out/<date>/<user>/<job>/media/
ls -lh out/<date>/<user>/<job>/transcripts/

# 4. Verify configuration
cat out/<date>/<user>/<job>/job.json | jq .

# 5. Check environment
cat out/<date>/<user>/<job>/.*.env
```

---

## 📖 Documentation Standards

### Documentation Rules

**CRITICAL RULES:**
1. ✅ **ALWAYS update documentation when code changes**
2. ✅ **ALWAYS update immediately, not later**
3. ✅ **ALWAYS keep README.md in project root**
4. ✅ **ALWAYS keep all other docs in docs/ directory**
5. ✅ **ALWAYS update docs/INDEX.md when adding new docs**

### Documentation Structure

```
project-root/
├── README.md                    # Project overview ONLY
│                               # Keep in root, update when needed
│
└── docs/                       # ALL documentation here
    ├── INDEX.md               # Master index (UPDATE THIS!)
    ├── PROCESS.md             # Development process
    ├── DEVELOPER_GUIDE.md     # This file
    ├── DEVELOPER_QUICK_REF.md # Quick reference
    ├── QUICKSTART.md          # User quick start
    │
    ├── user-guide/            # User documentation
    │   ├── README.md
    │   ├── <feature>.md
    │   └── features/
    │       └── <feature>.md
    │
    ├── technical/             # Technical documentation
    │   ├── README.md
    │   └── <topic>.md
    │
    ├── reference/             # Reference documentation
    │   ├── README.md
    │   ├── citations.md
    │   ├── license.md
    │   └── changelog.md
    │
    └── archive/               # Historical documentation
        └── SESSION_SUMMARY_<date>.md
```

### When to Update Documentation

**Immediately after:**

1. **Adding new feature**
   ```bash
   # Add feature
   git add scripts/my_feature.py
   
   # IMMEDIATELY create docs
   vim docs/user-guide/features/my-feature.md
   vim docs/technical/architecture.md  # Update if needed
   vim docs/INDEX.md  # Add link
   
   # Commit together
   git add docs/
   git commit -m "feat: add my feature with documentation"
   ```

2. **Adding new parameter**
   ```bash
   # Add to config/.env.pipeline
   vim config/.env.pipeline
   
   # IMMEDIATELY document it
   vim docs/user-guide/configuration.md
   vim docs/DEVELOPER_GUIDE.md  # Add example
   
   git add config/ docs/
   git commit -m "feat: add MY_NEW_PARAM configuration"
   ```

3. **Changing behavior**
   ```bash
   # Change code
   vim scripts/some_stage.py
   
   # IMMEDIATELY update docs
   vim docs/user-guide/workflows.md
   vim docs/technical/pipeline.md
   
   git add scripts/ docs/
   git commit -m "fix: update stage behavior and documentation"
   ```

4. **Fixing bug**
   ```bash
   # Fix bug
   vim scripts/buggy_code.py
   
   # Update troubleshooting if user-facing
   vim docs/user-guide/troubleshooting.md
   
   # Update technical docs if architecture changed
   vim docs/technical/architecture.md
   
   git add scripts/ docs/
   git commit -m "fix: resolve issue with documentation updates"
   ```

### Documentation Template

**For new features:**

```markdown
# Feature Name

**Purpose:** Brief description

## Overview

What this feature does...

## Configuration

Parameters in config/.env.pipeline:

\`\`\`bash
FEATURE_ENABLED=true
FEATURE_QUALITY=balanced
\`\`\`

## Usage

\`\`\`bash
# Example usage
./prepare-job.sh --media file.mp4 --workflow transcribe --source-lang hi
\`\`\`

## How It Works

1. Step 1: ...
2. Step 2: ...
3. Step 3: ...

## Examples

### Example 1: Basic Usage
\`\`\`bash
# Command
./prepare-job.sh ...

# Output
...
\`\`\`

## Troubleshooting

### Issue 1
**Problem:** ...
**Solution:** ...

## See Also

- [Related Feature](related-feature.md)
- [Configuration Guide](../configuration.md)
```

### Updating INDEX.md

**Every time you add a new document:**

```markdown
# Edit docs/INDEX.md

## 📖 Documentation Sections

### 1. User Guides

#### Features
- **[My New Feature](user-guide/features/my-new-feature.md)**  # ADD THIS
  - What it does
  - How to use it
  - Configuration
```

### Documentation Checklist

Before committing:

```
□ Code changes made
□ User documentation updated (if user-facing)
□ Technical documentation updated (if architecture changed)
□ Configuration documented (if new parameters)
□ Examples added (if new feature)
□ Troubleshooting updated (if common issue)
□ INDEX.md updated (if new file)
□ README.md updated (if major feature)
□ CHANGELOG updated (if release)
□ All links tested
□ All examples tested
```

### Documentation Best Practices

```markdown
# ✅ GOOD - Clear, specific
## Installing Dependencies

Run the bootstrap script:
\`\`\`bash
./bootstrap.sh
\`\`\`

# ❌ BAD - Vague
## Setup

Install stuff.

# ✅ GOOD - With examples
Set the quality parameter in config/.env.pipeline:
\`\`\`bash
SOURCE_SEPARATION_QUALITY=balanced  # Options: fast, balanced, quality
\`\`\`

# ❌ BAD - No examples
Configure quality in the config file.

# ✅ GOOD - Organized sections
## Configuration
## Usage
## Examples
## Troubleshooting
## See Also

# ❌ BAD - Wall of text
Everything about the feature in one paragraph...
```

### README.md Guidelines

**Project root README.md should contain:**
- Project overview
- Key features (brief)
- Quick start (single example)
- Link to full documentation
- License info
- Credits

**README.md should NOT contain:**
- Detailed feature documentation → docs/user-guide/features/
- Configuration details → docs/user-guide/configuration.md
- Architecture details → docs/technical/architecture.md
- Troubleshooting → docs/user-guide/troubleshooting.md
- Development guide → docs/DEVELOPER_GUIDE.md

### File Naming

```bash
# ✅ GOOD - Lowercase with hyphens
docs/user-guide/features/source-separation.md
docs/technical/multi-environment.md

# ❌ BAD - Mixed case
docs/user-guide/features/Source_Separation.md
docs/technical/MultiEnvironment.md

# ✅ GOOD - Descriptive
docs/user-guide/features/anti-hallucination.md

# ❌ BAD - Abbreviated
docs/user-guide/features/ah.md
```

---

## 📚 Additional Resources

### Essential Reading

1. **[PROCESS.md](PROCESS.md)** - Development process (READ FIRST)
2. **[Architecture](technical/architecture.md)** - System architecture
3. **[Pipeline](technical/pipeline.md)** - Pipeline details
4. **[Multi-Environment](technical/multi-environment.md)** - Environment system

### Code Examples

- **Stage Template**: `scripts/source_separation.py`
- **Orchestrator**: `scripts/run-pipeline.py`
- **Job Preparation**: `scripts/prepare-job.py`
- **Logging**: `shared/logger.py`
- **Configuration**: `shared/config.py`

### Getting Help

1. Check [Troubleshooting Guide](user-guide/troubleshooting.md)
2. Review logs with `--debug` enabled
3. Check recent changes in git history
4. Review architecture documentation

---

## ✅ Developer Checklist

Before committing code:

**Process:**
- [ ] Followed 6-step process from PROCESS.md
- [ ] Code follows style guide
- [ ] Commit message follows format

**Virtual Environments:**
- [ ] Used correct virtual environment
- [ ] No dependency conflicts introduced
- [ ] Environment isolation maintained

**Configuration:**
- [ ] NO hardcoded values in code
- [ ] All parameters in config/.env.pipeline
- [ ] Config class used (not os.environ)
- [ ] Sensible defaults provided
- [ ] Configuration validated

**Logging:**
- [ ] Used proper logging with module name
- [ ] Log format: [timestamp] [module_name] [level] message
- [ ] Clear, actionable log messages
- [ ] Traceback in DEBUG mode

**Output Structure:**
- [ ] Used StageIO for file I/O
- [ ] Standard directory structure followed
- [ ] No hardcoded paths

**Job Manifest:**
- [ ] Manifest updates handled by orchestrator
- [ ] Stage status properly tracked

**Documentation:**
- [ ] Documentation updated IMMEDIATELY
- [ ] User docs updated (if user-facing)
- [ ] Technical docs updated (if architecture changed)
- [ ] Configuration documented (if new parameters)
- [ ] Examples added (if new feature)
- [ ] INDEX.md updated (if new file)
- [ ] README.md kept in root only
- [ ] All other docs in docs/ directory

**Testing:**
- [ ] Tested default behavior
- [ ] Tested edge cases
- [ ] Error handling implemented
- [ ] Backward compatible

**Code Quality:**
- [ ] No debug print() statements
- [ ] No commented-out code
- [ ] Type hints used
- [ ] Docstrings provided

---

**Remember: Quality over speed. Write code others can understand and maintain.**

For detailed process, always refer to [PROCESS.md](PROCESS.md).
