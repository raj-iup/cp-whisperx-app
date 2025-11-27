# Developer Standards Compliance Guide

**Document Version:** 2.0  
**Date:** November 26, 2025  
**Based On:** Current implementation (bootstrap.sh v2.0, prepare-job.sh v2.0, run-pipeline.py)

---

## 📋 Executive Summary

This document defines development standards for the CP-WhisperX-App project based on the current implementation. All new code and modifications must follow these patterns to ensure consistency, maintainability, and reliability.

**Core Principles:**
- **Multi-Environment Architecture** - Isolated virtual environments per component
- **Configuration-Driven** - All parameters in config/.env.pipeline
- **Stage-Based Workflow** - Standardized StageIO pattern for data flow
- **Centralized Utilities** - Shared modules in shared/ directory
- **Structured Logging** - PipelineLogger with stage identification
- **Job-Based Execution** - prepare-job.sh → run-pipeline.py workflow

---

## 1. PROJECT STRUCTURE

### 1.1 Directory Layout

```
cp-whisperx-app/
├── bootstrap.sh                    # Multi-environment setup
├── prepare-job.sh                  # Job preparation wrapper
├── config/
│   ├── .env.pipeline              # Global configuration
│   ├── secrets.json               # API keys & tokens
│   └── hardware_cache.json        # Hardware detection cache
├── scripts/
│   ├── prepare-job.py             # Job creation logic
│   ├── run-pipeline.py            # Pipeline orchestrator
│   ├── whisperx_asr.py           # ASR stage script
│   ├── whisperx_integration.py    # WhisperX backend
│   └── [stage scripts...]         # Individual stage implementations
├── shared/
│   ├── stage_utils.py             # StageIO pattern
│   ├── stage_order.py             # Centralized stage numbering
│   ├── logger.py                  # PipelineLogger
│   ├── environment_manager.py     # venv management
│   ├── config.py                  # Configuration loading
│   ├── glossary_manager.py        # Glossary system
│   └── [utility modules...]       # Shared functionality
├── venv/                          # Virtual environments (8 total)
│   ├── common/                    # Core utilities
│   ├── whisperx/                  # WhisperX ASR
│   ├── mlx/                       # MLX Whisper (Apple Silicon)
│   ├── pyannote/                  # PyAnnote VAD
│   ├── demucs/                    # Audio source separation
│   ├── indictrans2/               # IndicTrans2 translation
│   ├── nllb/                      # NLLB translation
│   └── llm/                       # LLM integration
├── out/                           # Job output
│   └── YYYY/MM/DD/user/N/         # Job directory structure
├── in/                            # Input media files
├── glossary/                      # Term glossaries
├── docs/                          # Documentation
└── tests/                         # Test suite
```

---

## 2. MULTI-ENVIRONMENT ARCHITECTURE

### 2.1 Virtual Environment Strategy

**Rule:** Each ML/Translation component MUST have its own isolated virtual environment to prevent dependency conflicts.

**Current Environments (8 total):**

```python
ENVIRONMENTS = {
    "common": "venv/common",          # Core: job mgmt, logging, muxing
    "whisperx": "venv/whisperx",      # WhisperX ASR (CUDA/CPU)
    "mlx": "venv/mlx",                # MLX Whisper (Apple Silicon)
    "pyannote": "venv/pyannote",      # PyAnnote VAD
    "demucs": "venv/demucs",          # Demucs source separation
    "indictrans2": "venv/indictrans2",# IndicTrans2 (22 Indic languages)
    "nllb": "venv/nllb",              # NLLB (200+ languages)
    "llm": "venv/llm",                # LLM integration
}
```

### 2.2 Environment Assignment

Stages are mapped to environments in `EnvironmentManager`:

```python
# In shared/environment_manager.py
STAGE_TO_ENV = {
    "demux": "common",
    "tmdb": "common",
    "glossary_load": "common",
    "source_separation": "demucs",
    "pyannote_vad": "pyannote",
    "asr": "whisperx",           # or "mlx" for Apple Silicon
    "alignment": "whisperx",
    "lyrics_detection": "demucs",
    "indictrans2_en_translation": "indictrans2",
    "indictrans2_indic_translation": "indictrans2",
    "nllb_translation": "nllb",
    "subtitle_generation": "common",
    "mux": "common",
}
```

### 2.3 Adding New Environments

**When adding a new ML component:**

1. **Add to bootstrap.sh:**
```bash
# In ENVIRONMENTS array
ENVIRONMENTS=(
    "common"
    "whisperx"
    # ... existing ...
    "your_new_env"    # ADD HERE
)
```

2. **Create requirements file:**
```bash
# requirements/requirements-your_new_env.txt
your-package>=1.0.0
dependency-package>=2.0.0
```

3. **Add to EnvironmentManager:**
```python
# shared/environment_manager.py
ENVIRONMENTS = {
    # ... existing ...
    "your_new_env": "venv/your_new_env",
}

STAGE_TO_ENV = {
    # ... existing ...
    "your_stage": "your_new_env",
}
```

4. **Update bootstrap.sh environment descriptions:**
```bash
# Creates N specialized virtual environments for isolated dependency management:
#   ...
#   N. venv/your_new_env - Your component description
```

---

## 3. CONFIGURATION MANAGEMENT

### 3.1 Configuration Hierarchy

```
config/.env.pipeline        # Global defaults (REQUIRED)
  ↓
job.json                    # Job-specific config (auto-generated)
  ↓
.job-YYYYMMDD-user-NNNN.env # Job environment overrides
  ↓
Environment variables       # Runtime overrides
```

### 3.2 Mandatory Rules

**✅ DO:**
- Store ALL parameters in `config/.env.pipeline`
- Use `Config` class from `shared/config.py`
- Provide sensible defaults for optional parameters
- Document parameter purpose and valid values
- Use environment variable format: `STAGE_PARAMETER_NAME`

**❌ DON'T:**
- Use `os.environ.get()` directly in stage scripts
- Hardcode values in Python/Shell scripts
- Create stage-specific config files
- Use different config formats (stick to env vars)

### 3.3 Configuration Access Pattern

```python
# CORRECT: Use Config class
from shared.config import load_config

config = load_config()  # Loads from job.json if available
model = config.whisper_model  # Attribute access
threshold = getattr(config, 'confidence_threshold', 0.7)  # With default

# INCORRECT: Direct environment access
model = os.environ.get('WHISPER_MODEL')  # ❌ Don't do this
```

### 3.4 Configuration in config/.env.pipeline

**Format:**
```bash
# ============================================================================
# STAGE N: STAGE_NAME - Description
# ============================================================================
# Purpose: What this stage does
# Input: What files it reads
# Output: What files it creates
# Device: CPU/MPS/CUDA
# ============================================================================

# PARAMETER_NAME: Description
#   Values: Valid options
#   Default: Default value
#   Note: Additional context
PARAMETER_NAME=value

# Example with documentation:
# WHISPER_TEMPERATURE: Sampling temperature
#   Values: Comma-separated floats, default: 0.0,0.2,0.4
#   Note: 0.0 = deterministic, higher = more creative
WHISPER_TEMPERATURE=0.0,0.1,0.2
```

---

## 4. STAGE PATTERN (StageIO)

### 4.1 Stage Implementation Template

**Every stage script MUST follow this pattern:**

```python
#!/usr/bin/env python3
"""
Stage Name: Brief description

Purpose: Detailed purpose
Input: Expected input files
Output: Generated output files
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config


def main():
    """Main entry point for stage"""
    
    # 1. Initialize StageIO (determines paths automatically)
    stage_io = StageIO("stage_name")
    
    # 2. Setup logging
    logger = get_stage_logger("stage_name", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("STAGE NAME: Description")
    logger.info("=" * 60)
    
    # 3. Load configuration
    config = load_config()
    
    # 4. Get input files from previous stage
    input_file = stage_io.get_input_path("filename.ext", from_stage="previous_stage")
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return 1
    
    # 5. Get output directory
    output_dir = stage_io.output_base
    
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_dir}")
    
    # 6. Execute stage logic
    try:
        result = process_stage(input_file, output_dir, config, logger)
        
        if result:
            logger.info("✓ Stage completed successfully")
            return 0
        else:
            logger.error("✗ Stage failed")
            return 1
            
    except Exception as e:
        logger.error(f"Stage error: {e}")
        if config.debug:
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        return 1


def process_stage(input_file, output_dir, config, logger):
    """Stage-specific processing logic"""
    
    # Get parameters from config
    param = getattr(config, 'parameter_name', 'default_value')
    
    # Process
    # ...
    
    # Save output
    output_file = output_dir / "output.json"
    # ...
    
    return True


if __name__ == "__main__":
    sys.exit(main())
```

### 4.2 StageIO Methods

```python
# Initialize
stage_io = StageIO("stage_name")

# Get input from specific stage
input_path = stage_io.get_input_path("file.ext", from_stage="previous_stage")

# Get input from previous stage (automatic)
input_path = stage_io.get_input_path("file.ext")

# Get output path
output_file = stage_io.get_output_path("file.ext")

# Access directories
stage_io.stage_dir    # Current stage directory
stage_io.output_base  # Job directory root
stage_io.logs_dir     # Logs directory
```

### 4.3 Stage Numbering

**Centralized in `shared/stage_order.py`:**

```python
STAGE_NUMBERS = {
    "demux": 1,
    "tmdb": 2,
    "glossary_load": 3,
    "source_separation": 4,
    "pyannote_vad": 5,
    "asr": 6,
    "alignment": 7,
    "lyrics_detection": 8,
    "export_transcript": 9,
    "translation": 10,
    "subtitle_generation": 11,
    "mux": 12,
}
```

**Rules:**
- **NEVER** hardcode stage numbers
- Use `get_stage_number(name)` from `shared/stage_order.py`
- Use `get_stage_dir(name)` for directory names
- Stage directories: `{number:02d}_{name}/` (e.g., `06_asr/`)

---

## 5. LOGGING STANDARDS

### 5.1 Logger Initialization

```python
from shared.stage_utils import get_stage_logger

# In stage scripts
logger = get_stage_logger("stage_name", stage_io=stage_io)

# In utility modules
from shared.logger import PipelineLogger
logger = PipelineLogger("module_name", log_level="INFO")
```

### 5.2 Logging Patterns

```python
# Stage header (required at start of every stage)
logger.info("=" * 60)
logger.info("STAGE NAME: Brief Description")
logger.info("=" * 60)

# Configuration logging
logger.info(f"Configuration:")
logger.info(f"  Parameter 1: {value1}")
logger.info(f"  Parameter 2: {value2}")

# Progress logging
logger.info(f"Processing {filename}...")
logger.info(f"Step 1 completed")

# Success/Failure
logger.info("✓ Stage completed successfully")
logger.error("✗ Stage failed: reason")

# Debug information (only if debug mode)
if config.debug:
    logger.debug(f"Detailed debug information")
    logger.debug(f"Variable state: {variable}")

# Error handling
try:
    result = operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    if config.debug:
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    return 1
```

### 5.3 Log Levels

```python
# DEBUG: Detailed diagnostic information
logger.debug(f"Processing chunk {i}/{total}")

# INFO: General informational messages (default)
logger.info(f"Loaded {count} items")

# WARNING: Warning messages (potential issues)
logger.warning(f"Parameter X not set, using default")

# ERROR: Error messages (recoverable errors)
logger.error(f"Failed to load file: {filename}")

# CRITICAL: Critical errors (unrecoverable)
logger.critical(f"System resource exhausted")
```

---

## 6. JOB WORKFLOW

### 6.1 Job Preparation (prepare-job.sh)

**User Interface:**

```bash
./prepare-job.sh \
  --media "path/to/file.mp4" \
  --workflow {transcribe|translate|subtitle} \
  --source-language LANG_CODE \
  --target-language LANG_CODE[,LANG_CODE,...] \
  [--start-time HH:MM:SS] \
  [--end-time HH:MM:SS] \
  [--user-id USER] \
  [--debug]
```

**What it does:**
1. Validates input parameters
2. Parses filename for metadata (title, year)
3. Creates job directory: `out/YYYY/MM/DD/user/N/`
4. Copies media file to `media/`
5. Generates `job.json` configuration
6. Creates `manifest.json` for tracking
7. Saves `.job-YYYYMMDD-user-NNNN.env` file
8. Prints job directory path

**Output Structure:**
```
out/2025/11/26/rpatel/1/
├── .job-20251126-rpatel-0001.env   # Job environment
├── job.json                         # Job configuration
├── manifest.json                    # Execution tracking
├── media/                           # Input media
│   └── movie.mp4
├── logs/                            # Execution logs
├── 01_demux/                        # Stage outputs
├── 02_tmdb/
└── [other stages...]
```

### 6.2 Pipeline Execution (run-pipeline.py)

**Invocation:**

```bash
./run-pipeline.sh {transcribe|translate|subtitle} path/to/job/dir
```

**Workflow Execution:**

```python
class IndicTrans2Pipeline:
    def run_transcribe_workflow(self):
        """
        Stages: demux → asr → alignment
        Output: Transcript in source language
        """
        
    def run_translate_workflow(self):
        """
        Stages: load_transcript → translation → subtitle_generation
        Input: Existing transcript
        Output: Translated subtitles
        """
        
    def run_subtitle_workflow(self):
        """
        Full pipeline: demux → tmdb → glossary → separation → 
                       vad → asr → alignment → translation → 
                       subtitle_generation → mux
        Output: Video with embedded subtitles
        """
```

**Stage Execution Pattern:**

```python
def _run_stage(self, stage_name: str, env_name: str) -> bool:
    """
    Execute stage in specified environment
    
    Args:
        stage_name: Stage identifier (e.g., "asr")
        env_name: Environment name (e.g., "whisperx")
    
    Returns:
        True if stage succeeded, False otherwise
    """
    # 1. Get Python executable from environment
    python_exe = self.env_manager.get_python_executable(env_name)
    
    # 2. Get stage script path
    stage_script = self.scripts_dir / f"{stage_name}_stage.py"
    
    # 3. Set environment variables
    env = os.environ.copy()
    env['OUTPUT_DIR'] = str(self.job_dir)
    env['CONFIG_PATH'] = str(self.job_dir / 'job.json')
    env['DEBUG_MODE'] = 'true' if self.debug else 'false'
    
    # 4. Execute stage
    result = subprocess.run(
        [str(python_exe), str(stage_script)],
        env=env,
        capture_output=True,
        text=True
    )
    
    return result.returncode == 0
```

---

## 7. ERROR HANDLING

### 7.1 Error Handling Pattern

```python
def process_operation(input_data, config, logger):
    """Template for error handling"""
    try:
        # Validate inputs
        if not input_data:
            logger.error("Input data is empty")
            return None
        
        # Process
        result = perform_operation(input_data)
        
        # Validate output
        if not result:
            logger.error("Operation produced no output")
            return None
        
        return result
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return None
        
    except ValueError as e:
        logger.error(f"Invalid value: {e}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if config.debug:
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        return None
```

### 7.2 Graceful Degradation

```python
# Feature flags for optional functionality
if config.glossary_enabled:
    try:
        glossary = load_glossary()
    except Exception as e:
        logger.warning(f"Failed to load glossary: {e}")
        logger.warning("Continuing without glossary")
        glossary = None
else:
    glossary = None

# Continue with or without optional feature
result = process(data, glossary=glossary)
```

### 7.3 Exit Codes

```python
# Stage scripts MUST return appropriate exit codes
if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)
```

**Standard Exit Codes:**
- `0` - Success
- `1` - General failure
- `2` - Invalid input/configuration
- `3` - Resource not available
- `4` - External dependency failed

---

## 8. TESTING STANDARDS

### 8.1 Test Organization

```
tests/
├── unit/                  # Unit tests
│   ├── test_config.py
│   ├── test_stage_io.py
│   └── test_glossary.py
├── integration/           # Integration tests
│   ├── test_asr_pipeline.py
│   └── test_translation.py
└── fixtures/              # Test data
    ├── audio/
    └── config/
```

### 8.2 Test Naming Convention

```python
# test_module_name.py

class TestClassName:
    """Test class for ComponentName"""
    
    def test_function_does_expected_behavior(self):
        """Test that function produces expected result"""
        
    def test_function_handles_invalid_input(self):
        """Test that function handles invalid input gracefully"""
        
    def test_function_with_edge_case(self):
        """Test edge case scenario"""
```

### 8.3 Configuration Testing

```python
# Always test with default config
def test_default_configuration():
    """Test that defaults work without config file"""
    config = load_config()
    assert config.whisper_model == "large-v3"
    assert config.device == "mps"

# Test config overrides
def test_config_override():
    """Test that environment variables override defaults"""
    os.environ['WHISPER_MODEL'] = 'base'
    config = load_config()
    assert config.whisper_model == "base"
```

### 8.4 Stage Testing

```python
# Test stage with minimal input
def test_stage_minimal():
    """Test stage with minimal required input"""
    stage_io = StageIO("test_stage", output_base="/tmp/test")
    result = stage_function(stage_io, config)
    assert result is not None

# Test stage error handling
def test_stage_missing_input():
    """Test stage handles missing input file"""
    stage_io = StageIO("test_stage")
    result = stage_function(stage_io, config)
    assert result is None or result == False
```

---

## 9. DOCUMENTATION STANDARDS

### 9.1 Code Documentation

**Python Docstrings (Google Style):**

```python
def function_name(param1: type, param2: type) -> return_type:
    """Brief one-line description.
    
    More detailed description if needed. Explain what the function
    does, not how it does it.
    
    Args:
        param1: Description of param1
        param2: Description of param2, including valid values
               if applicable (e.g., "must be > 0")
    
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param is invalid
        FileNotFoundError: When file doesn't exist
        
    Example:
        >>> result = function_name(10, "test")
        >>> print(result)
        'processed: test with 10'
    """
```

**Shell Script Comments:**

```bash
# ============================================================================
# Script Name - Brief Description
# ============================================================================
# Version: X.Y.Z
# Date: YYYY-MM-DD
#
# Longer description of what the script does, its purpose,
# and any important context.
# ============================================================================

# Section header for related functions
function_name() {
    # Brief description of what this function does
    local param1="$1"  # Description
    local param2="$2"  # Description
    
    # Step description
    command
    
    # Another step
    command
}
```

### 9.2 Configuration Documentation

**Every parameter in config/.env.pipeline MUST have:**

```bash
# PARAMETER_NAME: Purpose/description
#   Values: Valid values or range
#   Default: Default value
#   Note: Additional context, constraints, or recommendations
PARAMETER_NAME=value
```

### 9.3 README Files

**Project Structure:**

```markdown
# docs/
├── README.md                  # Project overview
├── DEVELOPER_GUIDE.md         # Development guidelines
├── DEVELOPER_STANDARDS_COMPLIANCE.md  # This document
├── API.md                     # API documentation
├── CONFIGURATION.md           # Configuration reference
└── TROUBLESHOOTING.md         # Common issues
```

**README Template:**

```markdown
# Component Name

Brief one-paragraph description.

## Purpose

What this component does and why it exists.

## Usage

```bash
./script.sh --param value
```

## Configuration

List of configuration parameters with defaults.

## Output

Description of output files and formats.

## Dependencies

- Python 3.11+
- Package A >= 1.0.0
- Package B >= 2.0.0

## Troubleshooting

Common issues and solutions.
```

---

## 10. CODE STYLE

### 10.1 Python Style (PEP 8)

```python
# Naming conventions
class ClassName:                    # PascalCase
    pass

def function_name():                # snake_case
    pass

CONSTANT_NAME = "value"             # UPPER_SNAKE_CASE

variable_name = "value"             # snake_case

# File naming
module_name.py                      # snake_case
stage_name_processor.py             # snake_case with suffix

# Imports
import os                           # Standard library
import sys

import third_party_package          # Third party

from shared.logger import Logger    # Local imports

# Line length: 100 characters (not strict 79)
# Type hints: Required for function signatures
# Docstrings: Required for all public functions/classes
```

### 10.2 Shell Script Style

```bash
# File naming
script-name.sh                      # kebab-case

# Variable naming
readonly CONSTANT_NAME="value"      # UPPER_SNAKE_CASE for constants
local variable_name="value"         # snake_case for locals

# Function naming
function_name() {                   # snake_case
    # ...
}

# Quoting
echo "${variable}"                  # Always quote variables
command --flag "${value}"           # Quote command arguments

# Error handling
set -euo pipefail                   # At script start
command || { echo "Error"; exit 1; }  # Explicit error handling
```

---

## 11. VERSION CONTROL

### 11.1 Commit Messages

**Format:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/modifications
- `chore`: Build process, dependencies

**Examples:**

```
feat(asr): add hybrid bias strategy for character names

Implements hybrid bias strategy that combines global coverage
with contextual adaptation for better character name recognition.

- Added BIAS_STRATEGY parameter
- Updated whisperx_integration.py
- Added documentation

Closes #123
```

```
fix(config): make pydantic_settings import optional

The shared/config.py was importing pydantic_settings unconditionally,
causing failures in environments without it. Now falls back to simple
Config class when pydantic_settings is not available.

Fixes #456
```

### 11.2 Branch Naming

```
feature/descriptive-name     # New features
fix/issue-description        # Bug fixes
docs/update-name            # Documentation
refactor/component-name     # Code refactoring
test/test-description       # Test additions
```

---

## 12. COMPLIANCE CHECKLIST

### 12.1 New Stage Implementation

- [ ] Stage follows StageIO pattern
- [ ] Uses get_stage_logger for logging
- [ ] Loads config with load_config()
- [ ] Stage registered in shared/stage_order.py
- [ ] Environment mapping added if new env needed
- [ ] Parameters added to config/.env.pipeline
- [ ] Documentation includes input/output formats
- [ ] Error handling with graceful degradation
- [ ] Returns appropriate exit codes
- [ ] Tests written for happy path and errors

### 12.2 Configuration Changes

- [ ] Parameters in config/.env.pipeline only
- [ ] No hardcoded values in code
- [ ] Documentation includes purpose and valid values
- [ ] Sensible defaults provided
- [ ] Backward compatible (or migration documented)

### 12.3 New Environment Addition

- [ ] Added to bootstrap.sh ENVIRONMENTS array
- [ ] Requirements file created: requirements/requirements-name.txt
- [ ] Added to EnvironmentManager.ENVIRONMENTS
- [ ] Stage mappings updated in STAGE_TO_ENV
- [ ] Bootstrap description updated
- [ ] Dependencies verified not to conflict with existing envs

### 12.4 Documentation Updates

- [ ] Code has docstrings
- [ ] Config parameters documented
- [ ] README updated if user-facing changes
- [ ] CHANGELOG.md entry added
- [ ] Examples updated if API changed

---

## 13. ANTI-PATTERNS TO AVOID

### 13.1 Configuration Anti-Patterns

❌ **DON'T:**
```python
# Hardcoded values
model = "large-v3"

# Direct environment access
model = os.environ.get('WHISPER_MODEL', 'large-v3')

# Stage-specific config files
with open('asr_config.yaml') as f:
    config = yaml.load(f)
```

✅ **DO:**
```python
# Use Config class with defaults
config = load_config()
model = getattr(config, 'whisper_model', 'large-v3')
```

### 13.2 Stage Anti-Patterns

❌ **DON'T:**
```python
# Hardcoded paths
output_dir = Path("out/2025/11/26/user/1/06_asr")

# Direct file operations without StageIO
with open("../05_vad/segments.json") as f:
    segments = json.load(f)

# Hardcoded stage numbers
stage_dir = f"06_asr"
```

✅ **DO:**
```python
# Use StageIO
stage_io = StageIO("asr")
output_dir = stage_io.output_base

# Get input from previous stage
segments_file = stage_io.get_input_path("segments.json", from_stage="pyannote_vad")

# Use centralized stage numbering
stage_dir = get_stage_dir("asr")
```

### 13.3 Logging Anti-Patterns

❌ **DON'T:**
```python
# Print statements
print(f"Processing {filename}")

# Inconsistent formatting
logger.info("Starting...")
logger.info("===")

# No context
logger.error("Failed")
```

✅ **DO:**
```python
# Use logger
logger.info(f"Processing {filename}")

# Consistent headers
logger.info("=" * 60)
logger.info("STAGE NAME: Description")
logger.info("=" * 60)

# Informative messages
logger.error(f"Failed to process {filename}: {error}")
```

---

## 14. PERFORMANCE GUIDELINES

### 14.1 Resource Management

```python
# Clean up large objects
del large_model
import gc
gc.collect()

# Use context managers
with open(file, 'r') as f:
    data = f.read()

# Batch processing
for batch in chunks(data, batch_size):
    process_batch(batch)
    
# MPS optimization (Apple Silicon)
from mps_utils import optimize_batch_size_for_mps
batch_size = optimize_batch_size_for_mps(batch_size, device, 'large')
```

### 14.2 Caching

```python
# Use caching for expensive operations
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(param):
    # ...
    return result

# Disk caching for models
from shared.model_checker import check_model_cached
if not check_model_cached(model_name):
    download_model(model_name)
```

---

## 15. SECURITY GUIDELINES

### 15.1 Secrets Management

```python
# ✅ Store in config/secrets.json
{
    "tmdb_api_key": "your_key_here",
    "hf_token": "your_token_here"
}

# ✅ Load via Config
config = load_config()
api_key = config.tmdb_api_key

# ❌ Never commit secrets to git
# ❌ Never hardcode secrets in code
# ❌ Never log secrets
```

### 15.2 Input Validation

```python
# Validate user input
def validate_language(lang_code):
    if lang_code not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang_code}")

# Validate file paths
def validate_file_path(path):
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path

# Sanitize user input
def sanitize_filename(filename):
    # Remove dangerous characters
    return filename.replace('..', '').replace('/', '_')
```

---

## APPENDIX A: QUICK REFERENCE

### Common Commands

```bash
# Setup environment
./bootstrap.sh

# Create job
./prepare-job.sh --media file.mp4 --workflow translate -s hi -t en

# Run pipeline
./run-pipeline.sh translate path/to/job/dir

# Test configuration
./test_phase1.sh

# Check logs
tail -f out/YYYY/MM/DD/user/N/logs/99_pipeline*.log
```

### Common Imports

```python
# Stage implementation
from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config

# Environment management
from shared.environment_manager import EnvironmentManager

# Glossary
from shared.glossary_manager import GlossaryManager

# Hardware detection
from shared.hardware_detection import detect_device
```

### Configuration Access

```python
# Load config
config = load_config()

# Access with default
value = getattr(config, 'param_name', 'default')

# Common parameters
model = config.whisper_model
device = config.device
batch_size = config.batch_size
```

---

## APPENDIX B: MIGRATION GUIDE

### Migrating Old Code

**Old Pattern:**
```python
# Old: Hardcoded paths
output_dir = Path("out/06_asr")
input_file = Path("../05_vad/segments.json")

# Old: Direct environment access
model = os.environ.get('WHISPER_MODEL', 'large-v3')

# Old: Print statements
print("Processing...")
```

**New Pattern:**
```python
# New: StageIO
stage_io = StageIO("asr")
output_dir = stage_io.output_base
input_file = stage_io.get_input_path("segments.json", from_stage="pyannote_vad")

# New: Config class
config = load_config()
model = config.whisper_model

# New: Logger
logger = get_stage_logger("asr", stage_io=stage_io)
logger.info("Processing...")
```

---

**Document Version:** 2.0  
**Last Updated:** November 26, 2025  
**Status:** ACTIVE - All new code must follow these standards
