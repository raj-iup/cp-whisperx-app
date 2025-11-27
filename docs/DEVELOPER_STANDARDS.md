# CP-WhisperX Developer Standards & Best Practices

**Document Version:** 3.0  
**Date:** November 27, 2025  
**Status:** ACTIVE - All development must follow these standards  
**Compliance Target:** 80% minimum (Current baseline: 60%)

---

## 📋 Executive Summary

This document defines comprehensive development standards for the CP-WhisperX-App project, integrating:
- **Development Standards** - Code patterns, architecture, and implementation guidelines
- **Compliance Baseline** - Current state analysis and improvement roadmap
- **Best Practices** - Production-ready patterns for reliability and maintainability

**Core Principles:**
- **Multi-Environment Architecture** - Isolated virtual environments per component
- **Configuration-Driven** - All parameters in config/.env.pipeline
- **Stage-Based Workflow** - Standardized StageIO pattern for data flow
- **Centralized Utilities** - Shared modules in shared/ directory
- **Structured Logging** - PipelineLogger with stage identification
- **Job-Based Execution** - prepare-job.sh → run-pipeline.py workflow
- **Production Ready** - CI/CD, observability, and disaster recovery

---

## 📊 Current Compliance Status

**Overall Compliance: 60.0% (36/60 checks passed)**

### Stage Compliance Matrix

| Stage # | Stage Name | File | StageIO | Logger | Config | No HC | Error | Docs | Score |
|---------|------------|------|---------|--------|--------|-------|-------|------|-------|
| 1 | demux | demux.py | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | 5/6 |
| 2 | tmdb | tmdb_enrichment_stage.py | ✗ | ✓ | ✗ | ✗ | ✓ | ✓ | 4/6 |
| 3 | glossary_load | glossary_builder.py | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | 5/6 |
| 4 | source_separation | source_separation.py | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | 4/6 |
| 5 | pyannote_vad | pyannote_vad.py | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ | 4/6 |
| 6 | asr | whisperx_asr.py | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ | 3/6 |
| 7 | alignment | mlx_alignment.py | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | 4/6 |
| 8 | lyrics_detection | lyrics_detection.py | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | 5/6 |
| 9 | export_transcript | **MISSING** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 0/6 |
| 10 | translation | **MISSING** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 0/6 |
| 11 | subtitle_generation | subtitle_gen.py | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | 5/6 |
| 12 | mux | mux.py | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | 5/6 |

**Legend:**
- **StageIO**: Uses StageIO pattern • **Logger**: Uses get_stage_logger() • **Config**: Uses load_config()
- **No HC**: No hardcoded paths • **Error**: Proper error handling • **Docs**: Has module docstring

### Critical Issues to Address

**Priority 0 - Critical (Affects ALL stages):**
- ✗ **Config Usage**: All 10 existing stages use `os.environ.get()` instead of `load_config()`

**Priority 1 - High (Affects 6+ stages):**
- ✗ **Logger Imports**: 6 stages missing proper logger imports
- ✗ **Missing Stages**: 2 stages need implementation (export_transcript, translation)

**Priority 2 - Medium (Affects 3 stages):**
- ⚠ **StageIO Pattern**: 3 stages not using StageIO (tmdb, asr, alignment)
- ⚠ **Hardcoded Paths**: 3 stages have hardcoded stage numbers
- ⚠ **Error Handling**: 2 stages need better error handling

---

## 1. PROJECT STRUCTURE

### 1.1 Directory Layout

```
cp-whisperx-app/
├── bootstrap.sh                    # Multi-environment setup
├── prepare-job.sh                  # Job preparation wrapper
├── run-pipeline.sh                 # Pipeline execution wrapper
├── config/
│   ├── .env.pipeline              # Global configuration (version controlled)
│   ├── secrets.json               # API keys & tokens (git-ignored)
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
│   ├── common/                    # Core: job mgmt, logging, muxing
│   ├── whisperx/                  # WhisperX ASR (CUDA/CPU)
│   ├── mlx/                       # MLX Whisper (Apple Silicon)
│   ├── pyannote/                  # PyAnnote VAD
│   ├── demucs/                    # Audio source separation
│   ├── indictrans2/               # IndicTrans2 translation
│   ├── nllb/                      # NLLB translation
│   └── llm/                       # LLM integration
├── out/                           # Job output (date-organized)
│   └── YYYY/MM/DD/user/N/         # Job directory structure
├── in/                            # Input media files
├── glossary/                      # Term glossaries (user-created)
├── docs/                          # Documentation
│   ├── DEVELOPER_STANDARDS.md     # This document
│   ├── API.md                     # API documentation
│   ├── CONFIGURATION.md           # Config reference
│   └── archive/                   # Archived versions
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── fixtures/                  # Test data
└── tools/                         # Development tools
    ├── check_compliance.py        # Standards compliance checker
    └── generate_docs.py           # Documentation generator
```

### 1.2 File Naming Conventions

**Python Files:**
```python
# Modules: snake_case
stage_utils.py
environment_manager.py

# Stage scripts: {name}.py or {name}_stage.py
demux.py
whisperx_asr.py
tmdb_enrichment_stage.py

# Test files: test_{module}.py
test_stage_utils.py
test_config.py
```

**Shell Scripts:**
```bash
# Scripts: kebab-case.sh
bootstrap.sh
prepare-job.sh
run-pipeline.sh
```

**Configuration:**
```bash
# Environment files: .env.{name}
.env.pipeline
.env.local

# JSON configs: lowercase with underscores
secrets.json
hardware_cache.json
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
    "translation": "indictrans2",  # or "nllb" based on config
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
# Pin exact versions for production stability
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

### 2.4 Dependency Security

**Audit dependencies regularly:**

```bash
# Check for known vulnerabilities
pip install pip-audit
pip-audit --requirement requirements/requirements-common.txt

# Check for outdated packages
pip list --outdated

# Update safely (test thoroughly)
pip install --upgrade package==version

# Pin exact versions for production
pip freeze > requirements-lock.txt
```

**Dependency update policy:**
- **Security patches**: Apply immediately
- **Minor updates**: Monthly review
- **Major updates**: Quarterly evaluation with testing

---

## 3. CONFIGURATION MANAGEMENT

### 3.1 Configuration Hierarchy

```
config/.env.pipeline        # Global defaults (REQUIRED, version controlled)
  ↓
job.json                    # Job-specific config (auto-generated)
  ↓
.job-YYYYMMDD-user-NNNN.env # Job environment overrides (optional)
  ↓
Environment variables       # Runtime overrides (highest priority)
```

### 3.2 Mandatory Rules

**✅ DO:**
- Store ALL parameters in `config/.env.pipeline`
- Use `Config` class from `shared/config.py`
- Provide sensible defaults for optional parameters
- Document parameter purpose and valid values
- Use environment variable format: `STAGE_PARAMETER_NAME`
- Validate configuration on load

**❌ DON'T:**
- Use `os.environ.get()` directly in stage scripts
- Hardcode values in Python/Shell scripts
- Create stage-specific config files
- Use different config formats (stick to env vars)
- Commit secrets to version control

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

### 3.4 Configuration Validation

**Add validation layer using Pydantic:**

```python
from pydantic import BaseModel, Field, validator
from typing import Literal

class PipelineConfig(BaseModel):
    """Validated pipeline configuration with automatic type checking"""
    
    # Whisper Configuration
    whisper_model: Literal["tiny", "base", "small", "medium", "large", "large-v3"] = "large-v3"
    batch_size: int = Field(8, gt=0, le=128, description="Processing batch size")
    device: Literal["cpu", "cuda", "mps"] = Field("mps", description="Compute device")
    
    # Performance Configuration
    num_workers: int = Field(4, gt=0, le=32)
    max_memory_mb: int = Field(8192, gt=512)
    
    # Feature Flags
    glossary_enabled: bool = True
    source_separation_enabled: bool = False
    
    @validator('whisper_model')
    def validate_model_availability(cls, v):
        """Check if model exists or is downloadable"""
        # Add validation logic
        return v
    
    @validator('device')
    def validate_device_availability(cls, v):
        """Check if device is available on system"""
        import torch
        if v == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but not available")
        if v == "mps" and not torch.backends.mps.is_available():
            raise ValueError("MPS requested but not available")
        return v
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True

# Usage
try:
    config = PipelineConfig(**config_dict)
except ValidationError as e:
    logger.error(f"Configuration validation failed: {e}")
    sys.exit(2)
```

### 3.5 Configuration Documentation

**Every parameter in config/.env.pipeline MUST have:**

```bash
# PARAMETER_NAME: Purpose/description
#   Values: Valid values or range
#   Default: Default value
#   Note: Additional context, constraints, or recommendations
PARAMETER_NAME=value

# Example with full documentation:
# WHISPER_TEMPERATURE: Sampling temperature for inference
#   Values: Comma-separated floats (e.g., "0.0,0.2,0.4")
#   Default: 0.0,0.1,0.2
#   Note: 0.0 = deterministic, higher = more creative but less accurate
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

Purpose: Detailed purpose of this stage
Input: Expected input files and their sources
Output: Generated output files and their formats
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
    
    logger.info(f"Processing with parameter: {param}")
    
    # Process
    # ... stage-specific logic ...
    
    # Save output
    output_file = output_dir / "output.json"
    # ... save results ...
    
    logger.info(f"Output saved to: {output_file}")
    
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
STAGE_ORDER = [
    "demux",                    # 1
    "tmdb",                     # 2
    "glossary_load",            # 3
    "source_separation",        # 4
    "pyannote_vad",             # 5
    "asr",                      # 6
    "alignment",                # 7
    "lyrics_detection",         # 8
    "export_transcript",        # 9
    "translation",              # 10
    "subtitle_generation",      # 11
    "mux",                      # 12
]
```

**Rules:**
- **NEVER** hardcode stage numbers
- Use `get_stage_number(name)` from `shared/stage_order.py`
- Use `get_stage_dir(name)` for directory names
- Stage directories: `{number:02d}_{name}/` (e.g., `06_asr/`)

```python
# CORRECT
from shared.stage_order import get_stage_dir, get_stage_number

stage_dir = get_stage_dir("asr")  # Returns "06_asr"
stage_num = get_stage_number("asr")  # Returns 6

# INCORRECT
stage_dir = "06_asr"  # ❌ Hardcoded
stage_num = 6         # ❌ Hardcoded
```

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
logger.info(f"Step 1 of 3: Loading data")

# Success/Failure
logger.info("✓ Stage completed successfully")
logger.error("✗ Stage failed: reason")

# Debug information (only if debug mode)
if config.debug:
    logger.debug(f"Detailed debug information")
    logger.debug(f"Variable state: {variable}")

# Error handling with context
try:
    result = operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    if config.debug:
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    return 1
```

### 5.3 Structured Logging

**For better observability, use structured fields:**

```python
# Instead of plain strings
logger.info(f"Processing {file} took {duration}s")

# Use structured fields (better for log aggregation)
logger.info("Processing complete", extra={
    "file": file,
    "duration_seconds": duration,
    "segments_count": len(segments),
    "stage": "asr",
    "job_id": job_id
})
```

### 5.4 Log Levels

```python
# DEBUG: Detailed diagnostic information
logger.debug(f"Processing chunk {i}/{total}")

# INFO: General informational messages (default)
logger.info(f"Loaded {count} items")

# WARNING: Warning messages (potential issues)
logger.warning(f"Parameter X not set, using default: {default}")

# ERROR: Error messages (recoverable errors)
logger.error(f"Failed to load file: {filename}")

# CRITICAL: Critical errors (unrecoverable)
logger.critical(f"System resource exhausted, aborting")
```

### 5.5 Log Aggregation

**For production deployments:**
- Use JSON format for machine parsing
- Configure log rotation (size/time based)
- Setup centralized logging (ELK Stack, Grafana Loki, CloudWatch)
- Add correlation IDs for request tracing across stages

```python
# Configure JSON logging
import logging
import json_logging

json_logging.init_non_web(enable_json=True)

# Add correlation ID to all logs
import contextvars

correlation_id = contextvars.ContextVar('correlation_id', default=None)

class CorrelationFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id.get() or "unknown"
        return True

logger.addFilter(CorrelationFilter())
```

---

## 6. ERROR HANDLING

### 6.1 Error Handling Pattern

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

### 6.2 Graceful Degradation

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

### 6.3 Retry Logic with Exponential Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError))
)
def download_model(model_name: str):
    """Download model with automatic retry on transient failures"""
    response = requests.get(f"https://models.example.com/{model_name}")
    response.raise_for_status()
    return response.content
```

### 6.4 Circuit Breaker Pattern

**For external service calls:**

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_tmdb_api(query: str):
    """Call TMDB API with circuit breaker protection"""
    response = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params={"query": query, "api_key": config.tmdb_api_key},
        timeout=10
    )
    response.raise_for_status()
    return response.json()
```

### 6.5 Exit Codes

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

## 7. TESTING STANDARDS

### 7.1 Test Organization

```
tests/
├── unit/                  # Unit tests (fast, isolated)
│   ├── test_config.py
│   ├── test_stage_io.py
│   ├── test_glossary.py
│   └── test_logger.py
├── integration/           # Integration tests (slower, multi-component)
│   ├── test_asr_pipeline.py
│   ├── test_translation.py
│   └── test_end_to_end.py
├── performance/           # Performance regression tests
│   └── test_benchmarks.py
├── fixtures/              # Test data
│   ├── audio/
│   │   ├── test_1min.wav
│   │   └── test_5min.mp3
│   ├── config/
│   │   └── test_config.json
│   └── expected/
│       └── expected_output.json
└── conftest.py           # Pytest configuration
```

### 7.2 Test Coverage Requirements

**Minimum coverage targets:**
- Unit tests: **80% coverage**
- Integration tests: Core workflows covered
- E2E tests: Happy path + critical failure paths

```bash
# Run with coverage reporting
pytest --cov=shared --cov=scripts \
       --cov-report=html \
       --cov-report=term \
       --cov-fail-under=80

# Generate coverage badge
coverage-badge -o coverage.svg
```

### 7.3 Test Naming Convention

```python
# test_module_name.py

class TestClassName:
    """Test class for ComponentName"""
    
    def test_function_does_expected_behavior(self):
        """Test that function produces expected result"""
        result = function(input_data)
        assert result == expected
        
    def test_function_handles_invalid_input(self):
        """Test that function handles invalid input gracefully"""
        with pytest.raises(ValueError):
            function(invalid_input)
        
    def test_function_with_edge_case(self):
        """Test edge case scenario"""
        result = function(edge_case_input)
        assert result is not None
```

### 7.4 Property-Based Testing

**For complex transformations:**

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=1000))
def test_sanitize_filename_never_crashes(filename):
    """Property test: sanitize should never crash on any input"""
    result = sanitize_filename(filename)
    assert isinstance(result, str)
    assert '..' not in result
    assert '/' not in result
```

### 7.5 Performance Regression Tests

```python
@pytest.mark.performance
@pytest.mark.timeout(60)
def test_asr_throughput():
    """ASR should process at least 2x realtime on GPU"""
    audio_file = fixtures / "test_audio_60s.wav"
    audio_duration = 60  # seconds
    
    start_time = time.time()
    result = run_asr(audio_file, device="cuda")
    elapsed_time = time.time() - start_time
    
    throughput = audio_duration / elapsed_time
    
    assert throughput >= 2.0, (
        f"GPU throughput {throughput:.2f}x is below "
        f"required 2.0x realtime"
    )
```

### 7.6 Contract Testing

**Test stage interfaces:**

```python
def test_stage_contract_asr():
    """ASR stage must output segments.json with required fields"""
    result = run_stage("asr", test_input)
    
    segments = json.loads((result / "segments.json").read_text())
    required_fields = ['start', 'end', 'text', 'confidence']
    
    assert all(
        all(field in segment for field in required_fields)
        for segment in segments
    ), "ASR output missing required fields"
```

---

## 8. PERFORMANCE STANDARDS

### 8.1 Performance Budgets

**Maximum acceptable processing times:**

```python
PERFORMANCE_BUDGETS = {
    # Time in seconds per minute of input media
    "demux": 10,
    "asr_cpu": 60,
    "asr_gpu": 10,
    "asr_mps": 20,
    "translation": 5,  # per 1000 words
    "subtitle_generation": 3,
    "mux": 15,
}
```

### 8.2 Memory Limits

**Per-stage memory budgets:**

| Stage | Memory Limit | Notes |
|-------|--------------|-------|
| demux | 512MB | Streaming processing |
| asr | 8GB | With large-v3 model |
| translation | 4GB | IndicTrans2/NLLB |
| mux | 2GB | FFmpeg buffering |

### 8.3 Profiling Standards

**Profile stages when optimizing:**

```python
import cProfile
import pstats
from pathlib import Path

def profile_stage(func, output_file: Path):
    """Profile a stage and save detailed statistics"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func()
    
    profiler.disable()
    
    # Save for analysis
    profiler.dump_stats(str(output_file))
    
    # Print top consumers
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    return result

# Usage
profile_stage(
    lambda: run_asr_stage(test_audio),
    Path("profiling/asr_stage.prof")
)

# Analyze with snakeviz
# snakeviz profiling/asr_stage.prof
```

### 8.4 Performance Monitoring

**Track metrics in production:**

```python
import time
from contextlib import contextmanager

@contextmanager
def track_performance(stage_name: str, logger):
    """Context manager to track stage performance"""
    start_time = time.time()
    start_memory = get_memory_usage()
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        memory_delta = get_memory_usage() - start_memory
        
        logger.info("Performance metrics", extra={
            "stage": stage_name,
            "duration_seconds": duration,
            "memory_mb": memory_delta,
            "timestamp": time.time()
        })
        
        # Alert if over budget
        budget = PERFORMANCE_BUDGETS.get(stage_name)
        if budget and duration > budget:
            logger.warning(
                f"Stage {stage_name} exceeded budget: "
                f"{duration:.1f}s > {budget}s"
            )

# Usage
with track_performance("asr", logger):
    result = run_asr_stage()
```

---

## 9. CI/CD STANDARDS

### 9.1 GitHub Actions Workflows

**Required workflows:**

#### 1. Compliance Check

```yaml
# .github/workflows/compliance-check.yml
name: Standards Compliance Check

on: 
  pull_request:
  push:
    branches: [main, develop]

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run compliance check
        run: |
          python3 tools/check_compliance.py
          SCORE=$(python3 -c "import json; print(json.load(open('compliance_result.json'))['score'])")
          
          if [ "$SCORE" -lt 80 ]; then
            echo "✗ Compliance score $SCORE% is below 80% threshold"
            exit 1
          fi
          
          echo "✓ Compliance check passed: $SCORE%"
      
      - name: Upload compliance report
        uses: actions/upload-artifact@v3
        with:
          name: compliance-report
          path: compliance_result.json
```

#### 2. Automated Testing

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements/*.txt') }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements/requirements-common.txt
          pip install pytest pytest-cov
      
      - name: Run tests with coverage
        run: |
          pytest --cov=shared --cov=scripts \
                 --cov-report=xml \
                 --cov-report=term \
                 --junitxml=test-results.xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.os }}-${{ matrix.python-version }}
          path: test-results.xml
```

#### 3. Security Audit

```yaml
# .github/workflows/security.yml
name: Security Audit

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  pull_request:
    paths:
      - 'requirements/**'

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install pip-audit
        run: pip install pip-audit
      
      - name: Audit dependencies
        run: |
          for req in requirements/*.txt; do
            echo "Auditing $req"
            pip-audit -r "$req" || true
          done
```

### 9.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-json
      - id: check-merge-conflict
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--ignore=E203,W503']
  
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile=black']
  
  - repo: local
    hooks:
      - id: compliance-check
        name: Check standards compliance
        entry: python3 tools/check_compliance.py --min-score=80
        language: system
        pass_filenames: false
        stages: [commit]
```

**Install pre-commit hooks:**
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files  # Test hooks
```

---

## 10. OBSERVABILITY & MONITORING

### 10.1 Metrics Collection

**Instrument critical operations with Prometheus:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Counters - things that only go up
stages_completed = Counter(
    'pipeline_stages_completed_total',
    'Total stages completed',
    ['stage', 'status']
)

# Usage
stages_completed.labels(stage='asr', status='success').inc()

# Histograms - distribution of values
stage_duration = Histogram(
    'pipeline_stage_duration_seconds',
    'Stage processing duration',
    ['stage'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

# Usage with context manager
with stage_duration.labels(stage='asr').time():
    run_asr_stage()

# Gauges - values that go up and down
active_jobs = Gauge('pipeline_active_jobs', 'Currently active jobs')
active_jobs.set(get_active_job_count())
```

### 10.2 Health Checks

**Implement comprehensive health endpoints:**

```python
from fastapi import FastAPI, status
from datetime import datetime
import psutil

app = FastAPI()

@app.get("/health")
def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": VERSION
    }

@app.get("/health/ready")
def readiness_check():
    """Detailed readiness check"""
    checks = {
        "models_loaded": check_models_loaded(),
        "disk_space": check_disk_space() > 10_000_000_000,  # 10GB
        "memory_available": psutil.virtual_memory().available > 2_000_000_000,  # 2GB
        "gpu_available": check_gpu_available() if config.device == "cuda" else True,
    }
    
    all_healthy = all(checks.values())
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }, status_code

@app.get("/health/live")
def liveness_check():
    """Simple liveness probe (for Kubernetes)"""
    return {"alive": True}
```

### 10.3 Distributed Tracing

**Implement OpenTelemetry tracing:**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Setup tracer
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Instrument stage execution
def run_asr_with_tracing(audio_file, config):
    with tracer.start_as_current_span("asr-stage") as span:
        span.set_attribute("audio.file", str(audio_file))
        span.set_attribute("config.model", config.whisper_model)
        
        with tracer.start_as_current_span("load-model"):
            model = load_model(config.whisper_model)
        
        with tracer.start_as_current_span("transcribe"):
            result = transcribe(audio_file, model)
        
        span.set_attribute("result.segments", len(result['segments']))
        
        return result
```

---

## 11. DISASTER RECOVERY

### 11.1 Backup Strategy

**Critical data to backup:**

1. **Configuration Files** (`config/`)
   - `.env.pipeline` - Pipeline configuration
   - `secrets.json` - API keys (encrypted)
   - `hardware_cache.json` - Hardware profiles

2. **Custom Glossaries** (`glossary/`)
   - User-created term glossaries
   - Character name mappings

3. **Job Outputs** (`out/`) - Optional
   - Can be regenerated from source media
   - Backup if regeneration is expensive

**Automated backup script:**

```bash
#!/bin/bash
# backup.sh - Daily backup script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/cp-whisperx"
BACKUP_FILE="backup-${DATE}.tar.gz"

# Create encrypted backup
tar -czf - config/ glossary/ | \
    openssl enc -aes-256-cbc -salt -pass pass:${BACKUP_PASSWORD} \
    > "${BACKUP_DIR}/${BACKUP_FILE}"

# Upload to cloud storage (AWS S3, Google Cloud Storage, etc.)
aws s3 cp "${BACKUP_DIR}/${BACKUP_FILE}" \
    "s3://backups/cp-whisperx/${BACKUP_FILE}"

# Retention: Keep last 30 days
find "${BACKUP_DIR}" -name "backup-*.tar.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}"
```

**Schedule with cron:**
```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/cp-whisperx-backup.log 2>&1
```

### 11.2 Job Recovery with Checkpoints

**Implement checkpoint system:**

```python
from pathlib import Path
import json
from datetime import datetime
from typing import Optional, Dict, Any

class CheckpointManager:
    """Manage stage checkpoints for job recovery"""
    
    def __init__(self, job_dir: Path):
        self.job_dir = job_dir
        self.checkpoint_dir = job_dir / ".checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)
    
    def save_checkpoint(self, stage: str, state: Dict[str, Any]):
        """Save checkpoint after stage completion"""
        checkpoint_file = self.checkpoint_dir / f"{stage}.json"
        
        checkpoint_data = {
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "completed": True
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        logger.info(f"Checkpoint saved for stage: {stage}")
    
    def load_checkpoint(self, stage: str) -> Optional[Dict[str, Any]]:
        """Load checkpoint for stage if exists"""
        checkpoint_file = self.checkpoint_dir / f"{stage}.json"
        
        if not checkpoint_file.exists():
            return None
        
        with open(checkpoint_file) as f:
            checkpoint_data = json.load(f)
        
        if checkpoint_data.get("completed"):
            logger.info(f"Loaded checkpoint for stage: {stage}")
            return checkpoint_data["state"]
        
        return None
    
    def get_last_completed_stage(self) -> Optional[str]:
        """Find the last completed stage"""
        checkpoints = sorted(self.checkpoint_dir.glob("*.json"))
        
        for checkpoint_file in reversed(checkpoints):
            with open(checkpoint_file) as f:
                data = json.load(f)
                if data.get("completed"):
                    return data["stage"]
        
        return None

# Usage in pipeline
checkpoint_mgr = CheckpointManager(job_dir)

# Save after each stage
result = run_stage("asr", inputs)
checkpoint_mgr.save_checkpoint("asr", {
    "segments_count": len(result),
    "duration": duration
})

# Resume from last checkpoint
last_stage = checkpoint_mgr.get_last_completed_stage()
if last_stage:
    logger.info(f"Resuming from stage: {last_stage}")
    from shared.stage_order import STAGE_ORDER
    start_index = STAGE_ORDER.index(last_stage) + 1
    start_from_stage = STAGE_ORDER[start_index]
else:
    start_from_stage = STAGE_ORDER[0]
```

---

## 12. CODE STYLE & QUALITY

### 12.1 Python Style (PEP 8)

```python
# Naming conventions
class ClassName:                    # PascalCase for classes
    pass

def function_name():                # snake_case for functions
    pass

CONSTANT_NAME = "value"             # UPPER_SNAKE_CASE for constants

variable_name = "value"             # snake_case for variables

# Type hints (required for all public APIs)
from typing import Optional, List, Dict, Any

def process_segments(
    segments: List[Dict[str, Any]],
    config: Config,
    logger: PipelineLogger
) -> Optional[List[Dict[str, Any]]]:
    """Process transcript segments with configuration"""
    pass

# Line length: 100 characters (not strict 79)
# Imports: Organize by standard library, third party, local
import os                           # Standard library
import sys

import torch                        # Third party

from shared.logger import Logger    # Local imports
```

### 12.2 Type Hints Enforcement

**Enable type checking in CI:**

```bash
# Install mypy
pip install mypy types-requests

# Run type checker (strict mode)
mypy scripts/ shared/ --strict --ignore-missing-imports

# Configure mypy
cat > mypy.ini << 'EOF'
[mypy]
python_version = 3.11
strict = True
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

[mypy-scripts.legacy.*]
ignore_errors = True
EOF
```

### 12.3 Code Quality Tools

```bash
# Black: Code formatter
black scripts/ shared/ tests/

# isort: Import sorting
isort scripts/ shared/ tests/

# flake8: Linting
flake8 scripts/ shared/ tests/ --max-line-length=100

# pylint: Additional linting
pylint scripts/ shared/
```

---

## 13. DOCUMENTATION STANDARDS

### 13.1 Docstring Format (Google Style)

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
        Description of return value. For complex returns, use:
        Dict with keys:
            - 'segments': List of transcript segments
            - 'confidence': Overall confidence score
        
    Raises:
        ValueError: When param is invalid
        FileNotFoundError: When file doesn't exist
        
    Example:
        >>> result = function_name(10, "test")
        >>> print(result)
        'processed: test with 10'
    """
```

### 13.2 Module Documentation

**Every Python module MUST have:**

```python
#!/usr/bin/env python3
"""
Module Name: Brief description

This module provides functionality for [purpose]. It includes:
- Feature 1
- Feature 2
- Feature 3

Usage:
    from module_name import ClassName
    
    obj = ClassName(param1, param2)
    result = obj.process()

Note:
    This module requires [dependencies] to be installed.
"""
```

### 13.3 Shell Script Documentation

```bash
#!/bin/bash
# ============================================================================
# Script Name - Brief Description
# ============================================================================
# Version: X.Y.Z
# Date: YYYY-MM-DD
#
# Longer description of what the script does, its purpose,
# and any important context.
#
# Usage:
#   ./script-name.sh [OPTIONS] ARGS
#
# Options:
#   -h, --help      Show this help message
#   -v, --verbose   Enable verbose output
#
# Examples:
#   ./script-name.sh --verbose input.txt
# ============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly VERSION="1.0.0"

# Function documentation
function process_file() {
    # Brief description of what this function does
    #
    # Args:
    #   $1 - Input file path
    #   $2 - Output directory
    #
    # Returns:
    #   0 on success, 1 on failure
    
    local input_file="$1"
    local output_dir="$2"
    
    # Implementation
}
```

---

## 14. COMPLIANCE IMPROVEMENT ROADMAP

### Priority 0: Critical (2-4 hours)
**Target: 80% compliance**

1. **Config Migration** (2-3 hours)
   - Update all 10 stages to use `load_config()`
   - Remove all `os.environ.get()` calls
   - Test each stage individually

2. **Quick Wins** (1-2 hours)
   - Add logger imports to 6 stages
   - Fix hardcoded paths in 3 stages

**Expected Result:** 75-80% compliance

### Priority 1: High (4-6 hours)
**Target: 90% compliance**

1. **StageIO Migration** (3-4 hours)
   - Update tmdb, asr, alignment to use StageIO
   - Test path resolution

2. **Error Handling** (1-2 hours)
   - Add proper error handling to pyannote_vad and asr
   - Add main() functions where missing

**Expected Result:** 90-95% compliance

### Priority 2: Medium (4-6 hours)
**Target: 100% compliance**

1. **Missing Stages** (4-6 hours)
   - Implement export_transcript stage
   - Extract translation logic to separate scripts
   - Test integration

**Expected Result:** 100% compliance

---

## 15. ANTI-PATTERNS TO AVOID

### 15.1 Configuration Anti-Patterns

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
from shared.config import load_config

config = load_config()
model = getattr(config, 'whisper_model', 'large-v3')
```

### 15.2 Stage Anti-Patterns

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
from shared.stage_utils import StageIO
from shared.stage_order import get_stage_dir

stage_io = StageIO("asr")
output_dir = stage_io.output_base

# Get input from previous stage
segments_file = stage_io.get_input_path("segments.json", from_stage="pyannote_vad")

# Use centralized stage numbering
stage_dir = get_stage_dir("asr")
```

### 15.3 Logging Anti-Patterns

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
# Use logger consistently
from shared.stage_utils import get_stage_logger

logger = get_stage_logger("stage_name", stage_io=stage_io)
logger.info(f"Processing {filename}")

# Consistent headers
logger.info("=" * 60)
logger.info("STAGE NAME: Description")
logger.info("=" * 60)

# Informative messages with context
logger.error(f"Failed to process {filename}: {error}")
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

# Check compliance
python3 tools/check_compliance.py

# Run tests with coverage
pytest --cov=shared --cov=scripts --cov-report=html

# Check logs
tail -f out/YYYY/MM/DD/user/N/logs/99_pipeline*.log
```

### Common Imports

```python
# Stage implementation
from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config
from shared.stage_order import get_stage_dir, get_stage_number

# Environment management
from shared.environment_manager import EnvironmentManager

# Glossary system
from shared.glossary_manager import GlossaryManager

# Hardware detection
from shared.hardware_detection import detect_device
```

### Configuration Access

```python
# Load config
from shared.config import load_config

config = load_config()

# Access with default
value = getattr(config, 'param_name', 'default_value')

# Common parameters
model = config.whisper_model
device = config.device
batch_size = config.batch_size
debug = config.debug
```

---

## APPENDIX B: COMPLIANCE CHECKING

### Automated Compliance Check

Run the automated compliance checker:

```bash
# Check all stages
python3 tools/check_compliance.py

# Check specific stage
python3 tools/check_compliance.py --stage=asr

# Generate detailed report
python3 tools/check_compliance.py --output=compliance_report.html

# Set minimum score threshold
python3 tools/check_compliance.py --min-score=80
```

### Manual Compliance Checklist

**For each new stage:**

- [ ] Uses StageIO pattern for path management
- [ ] Uses get_stage_logger() for logging
- [ ] Loads config with load_config()
- [ ] Stage registered in shared/stage_order.py
- [ ] No hardcoded paths or stage numbers
- [ ] Proper error handling with try/except
- [ ] Returns appropriate exit codes (0 for success, >0 for failure)
- [ ] Has module docstring explaining purpose
- [ ] Has function docstrings for public functions
- [ ] Includes example usage in docstring
- [ ] Tests written for happy path and errors
- [ ] Type hints on all public functions

**For configuration changes:**

- [ ] Parameters in config/.env.pipeline only
- [ ] No hardcoded values in code
- [ ] Documentation includes purpose and valid values
- [ ] Sensible defaults provided
- [ ] Validation added if applicable
- [ ] Backward compatible (or migration documented)

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-15 | Initial version | Team |
| 2.0 | 2025-11-26 | Added compliance baseline | Team |
| 3.0 | 2025-11-27 | **Unified standards + best practices** | Team |
|  |  | - Integrated compliance findings |  |
|  |  | - Added CI/CD standards |  |
|  |  | - Added observability section |  |
|  |  | - Added disaster recovery |  |
|  |  | - Added performance standards |  |
|  |  | - Enhanced testing guidelines |  |
|  |  | - Added type hints enforcement |  |

---

**Document Status:** ACTIVE  
**Last Updated:** November 27, 2025  
**Compliance Target:** 80% minimum (tracked quarterly)  
**Next Review:** February 2026

---

**All development MUST follow these standards. Non-compliance will be flagged in code review.**
