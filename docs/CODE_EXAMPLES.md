# Code Examples & Anti-Patterns — CP-WhisperX-App

**Purpose:** Visual examples showing correct vs incorrect patterns for DEVELOPER_STANDARDS.md compliance.

**Audience:** Developers and AI assistants (Copilot) working on this repository.

**Related docs:**
- Standards reference: `docs/developer/DEVELOPER_STANDARDS.md`
- Copilot instructions: `.github/copilot-instructions.md`
- Compliance checker: `scripts/validate-compliance.py`

---

## 🎯 Quick Navigation

| Pattern | Section | Priority |
|---------|---------|----------|
| Logger Usage | § 1 | ⭐ #1 (60% violation) |
| Import Organization | § 2 | ⭐ #2 (100% violation) |
| StageIO Pattern | § 3 | Critical |
| Config Management | § 4 | Critical |
| Error Handling | § 5 | Important |
| Stage Directory | § 6 | Critical |
| Type Hints | § 7 | Code Quality |
| Complete Stage Example | § 8 | Reference |

---

## § 1: Logger Usage (§ 2.3) ⭐ PRIORITY #1

**Baseline violation:** 60% of files use print() instead of logger

### ❌ Anti-Pattern: Using print()

```python
def process_audio(file_path):
    print("Starting audio processing...")  # WRONG
    print(f"Processing: {file_path}")      # WRONG
    
    try:
        result = process(file_path)
        print(f"Success: {result}")        # WRONG
    except Exception as e:
        print(f"Error: {e}")               # WRONG - no traceback
```

**Problems:**
- No logs go to stage.log file
- No timestamps
- No severity levels
- Can't control verbosity
- Lost in pipeline output

### ✅ Correct Pattern: Using logger

```python
# Standard library
from pathlib import Path

# Local
from shared.logger import get_logger

logger = get_logger(__name__)


def process_audio(file_path: Path) -> dict:
    """Process audio file with proper logging."""
    logger.info("=" * 60)
    logger.info("Starting audio processing")
    logger.info("=" * 60)
    logger.info(f"Processing: {file_path}")
    
    try:
        result = process(file_path)
        logger.info(f"Success: processed {file_path.name}")
        logger.debug(f"Result details: {result}")
        return result
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}", exc_info=True)
        raise
        
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
```

**Benefits:**
- ✅ Logs to stage.log with timestamps
- ✅ Severity levels (debug, info, error)
- ✅ Full tracebacks with exc_info=True
- ✅ Structured, searchable logs
- ✅ Production-ready

### For Stage Files: Use io.get_stage_logger()

```python
from shared.stage_utils import StageIO

def run_stage(job_dir: Path) -> int:
    io = StageIO("stage_name", job_dir, enable_manifest=True)
    logger = io.get_stage_logger()  # Stage-specific logger
    
    logger.info("Stage starting...")
    # ... your code ...
```

---

## § 2: Import Organization (§ 6.1) ⭐ PRIORITY #2

**Baseline violation:** 100% of files have unorganized imports

### ❌ Anti-Pattern: Mixed imports

```python
import os
from pathlib import Path
from shared.config import load_config  # WRONG: mixed with stdlib
import sys
from typing import Dict
import numpy as np                     # WRONG: mixed with stdlib
from shared.logger import get_logger   # WRONG: no grouping
```

**Problems:**
- Hard to see dependencies
- Hard to find specific imports
- Inconsistent style
- Poor maintainability

### ✅ Correct Pattern: Grouped imports

```python
#!/usr/bin/env python3
"""
Module description.
"""

# Standard library
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Third-party
import numpy as np
import pandas as pd
from transformers import pipeline

# Local
from shared.config_loader import load_config
from shared.logger import get_logger
from shared.stage_utils import StageIO
```

**Benefits:**
- ✅ Clear dependency boundaries
- ✅ Easy to find imports
- ✅ Standard Python convention
- ✅ Better organization

**Rules:**
1. Group 1: Standard library (os, sys, pathlib, typing)
2. Group 2: Third-party (numpy, pandas, transformers)
3. Group 3: Local/project (shared/*, scripts/*)
4. Blank line between each group
5. Alphabetical within each group

---

## § 3: StageIO Pattern (§ 2.6) - Complete Template

**Critical:** All stages must follow this 8-step pattern

### ❌ Anti-Pattern: Missing manifest tracking

```python
def run_stage(job_dir):
    # WRONG: No StageIO
    # WRONG: No manifest tracking
    # WRONG: No type hints
    
    print("Processing...")  # WRONG: print not logger
    
    input_file = job_dir / "input.txt"  # No tracking
    output_file = job_dir / "output.txt"  # WRONG: not in stage_dir
    
    with open(input_file) as f:
        data = f.read()
    
    with open(output_file, 'w') as f:
        f.write(data.upper())
    
    return 0
```

**Problems:**
- No data lineage tracking
- No manifest
- Output in wrong location
- No logging to stage.log
- Not idempotent
- Can't resume on failure

### ✅ Correct Pattern: Full StageIO implementation

```python
#!/usr/bin/env python3
"""
Stage description - what this stage does.
"""

# Standard library
import sys
from pathlib import Path
from typing import Optional

# Local
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config_loader import load_config
from shared.stage_utils import StageIO


def run_stage(job_dir: Path, stage_name: str = "example_stage") -> int:
    """
    Run the example stage.
    
    Args:
        job_dir: Path to job directory
        stage_name: Name of this stage
        
    Returns:
        int: Exit code (0=success, 1=failure)
    """
    # Step 1: Initialize StageIO with manifest tracking
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        logger.info("=" * 60)
        logger.info(f"STAGE: {stage_name}")
        logger.info("=" * 60)
        
        # Step 2: Load configuration
        config = load_config()
        param = config.get("PARAM_NAME", "default_value")
        logger.info(f"Configuration: param={param}")
        
        # Step 3: Find input from previous stage
        input_file = io.job_dir / "previous_stage" / "output.txt"
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input not found: {input_file}")
        
        # Step 4: Track input in manifest
        io.manifest.add_input(input_file, io.compute_hash(input_file))
        logger.info(f"Input: {input_file}")
        
        # Step 5: Define output in THIS stage's directory ONLY
        output_file = io.stage_dir / "output.txt"
        
        # Step 6: Process (your logic here)
        logger.info("Processing...")
        with open(input_file) as f:
            data = f.read()
        
        processed = data.upper()  # Your processing logic
        
        with open(output_file, 'w') as f:
            f.write(processed)
        
        # Step 7: Track output in manifest
        io.manifest.add_output(output_file, io.compute_hash(output_file))
        logger.info(f"Output: {output_file}")
        
        # Step 8: Finalize manifest
        io.finalize_stage_manifest(exit_code=0)
        logger.info("Stage completed successfully")
        logger.info("=" * 60)
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1
        
    except Exception as e:
        logger.error(f"Stage failed: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Example stage")
    parser.add_argument("--job-dir", type=Path, required=True, 
                       help="Job directory path")
    parser.add_argument("--stage-name", type=str, default="example_stage",
                       help="Stage name")
    
    args = parser.parse_args()
    sys.exit(run_stage(args.job_dir, args.stage_name))
```

**Benefits:**
- ✅ Complete data lineage
- ✅ Resumable on failure
- ✅ Proper stage isolation
- ✅ All outputs tracked
- ✅ Logs to stage.log
- ✅ Type-safe
- ✅ Production-ready

---

## § 4: Configuration Management (§ 4.2)

### ❌ Anti-Pattern: Direct environment access

```python
import os

# WRONG: Direct environment access
max_size = os.getenv("MAX_FILE_SIZE")           # Might be None
timeout = os.environ["TIMEOUT"]                  # Will crash if missing
debug = os.getenv("DEBUG_MODE", False)          # Wrong: returns string "False"

# WRONG: No type conversion
if debug:  # Always True because "False" is truthy string!
    print("Debug mode")
```

**Problems:**
- No centralized config management
- Hard to test
- Type errors (everything is string)
- Crashes on missing vars
- Not mockable

### ✅ Correct Pattern: Using load_config()

```python
# Local
from shared.config_loader import load_config

config = load_config()

# Correct: With defaults and type conversion
max_size_mb = int(config.get("MAX_FILE_SIZE_MB", 100))
timeout_sec = int(config.get("TIMEOUT_SEC", 300))
debug = config.get("DEBUG_MODE", "false").lower() == "true"

# Correct: Type-safe usage
if debug:  # Now correctly boolean
    logger.debug("Debug mode enabled")

# Correct: Validation
if max_size_mb <= 0:
    raise ValueError(f"MAX_FILE_SIZE_MB must be positive, got {max_size_mb}")
```

**Benefits:**
- ✅ Centralized config management
- ✅ Testable (can mock load_config)
- ✅ Type-safe with explicit conversion
- ✅ Always has defaults
- ✅ Validation possible

### Common Type Conversions

```python
config = load_config()

# Integer
max_count = int(config.get("MAX_COUNT", 100))

# Float
threshold = float(config.get("THRESHOLD", 0.85))

# Boolean (strings "true"/"false")
enabled = config.get("ENABLED", "false").lower() == "true"

# Path
output_dir = Path(config.get("OUTPUT_DIR", "out"))

# List (comma-separated string)
languages = config.get("LANGUAGES", "en,hi,es").split(",")

# Enum/Choice (with validation)
mode = config.get("MODE", "auto")
if mode not in ["auto", "manual", "debug"]:
    raise ValueError(f"Invalid MODE: {mode}")
```

---

## § 5: Error Handling (§ 5)

### ❌ Anti-Pattern: Generic catch-all

```python
try:
    process_file(file_path)
except:  # WRONG: catches everything including KeyboardInterrupt
    print("Error")  # WRONG: no details, no traceback
    pass  # WRONG: silently swallows error
```

**Problems:**
- Catches system exceptions (KeyboardInterrupt, SystemExit)
- No error information
- No traceback for debugging
- Silent failures

### ✅ Correct Pattern: Specific exceptions with logging

```python
from shared.logger import get_logger

logger = get_logger(__name__)

try:
    process_file(file_path)
    
except FileNotFoundError as e:
    # Specific exception first
    logger.error(f"File not found: {file_path} - {e}", exc_info=True)
    raise  # Re-raise to propagate
    
except PermissionError as e:
    # Another specific exception
    logger.error(f"Permission denied: {file_path} - {e}", exc_info=True)
    raise
    
except ValueError as e:
    # Application-specific exception
    logger.error(f"Invalid data in {file_path}: {e}", exc_info=True)
    raise RuntimeError(f"Data validation failed: {e}")
    
except Exception as e:
    # Catch-all LAST, with full traceback
    logger.error(f"Unexpected error processing {file_path}: {e}", exc_info=True)
    raise
```

**Benefits:**
- ✅ Specific error handling
- ✅ Full tracebacks with exc_info=True
- ✅ Context in error messages
- ✅ Proper error propagation
- ✅ Debuggable

---

## § 6: Stage Directory Containment (§ 1.1)

### ❌ Anti-Pattern: Writing outside stage directory

```python
def run_stage(job_dir: Path) -> int:
    io = StageIO("test", job_dir, enable_manifest=True)
    
    # WRONG: Writing to job root
    output1 = job_dir / "output.txt"
    
    # WRONG: Writing to /tmp
    output2 = Path("/tmp/output.txt")
    
    # WRONG: Writing to another stage's directory
    output3 = job_dir / "other_stage" / "output.txt"
    
    # WRONG: Absolute path outside job
    output4 = Path("/var/data/output.txt")
```

**Problems:**
- Breaks stage isolation
- Corrupts data lineage
- Not resumable
- Hard to debug
- Violates pipeline architecture

### ✅ Correct Pattern: Stage directory only

```python
def run_stage(job_dir: Path) -> int:
    io = StageIO("test", job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    # CORRECT: All outputs in stage_dir
    output_file = io.stage_dir / "output.txt"
    
    # CORRECT: Subdirectories in stage_dir
    frames_dir = io.stage_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_file = frames_dir / "frame_001.jpg"
    
    # CORRECT: Temporary files in stage_dir
    temp_dir = io.stage_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = temp_dir / "temp.dat"
    
    # Write files
    output_file.write_text("data")
    
    # Track outputs
    io.manifest.add_output(output_file, io.compute_hash(output_file))
    io.manifest.add_output(frame_file, io.compute_hash(frame_file))
```

**Benefits:**
- ✅ Perfect stage isolation
- ✅ Correct data lineage
- ✅ Resumable on failure
- ✅ Easy to debug
- ✅ Follows pipeline architecture

**Reading from other stages:**
```python
# CORRECT: Read from other stages via job_dir
input_file = io.job_dir / "previous_stage" / "output.txt"
io.manifest.add_input(input_file, io.compute_hash(input_file))

# Then read
data = input_file.read_text()
```

---

## § 7: Type Hints (§ 6.2)

### ❌ Anti-Pattern: No type hints

```python
def process_data(data, config, verbose=False):  # WRONG: No types
    if verbose:
        print(f"Processing {len(data)} items")
    return [x * 2 for x in data]
```

**Problems:**
- No IDE autocomplete
- No type checking
- Unclear API
- Hard to maintain

### ✅ Correct Pattern: Full type hints

```python
from pathlib import Path
from typing import List, Dict, Optional

def process_data(
    data: List[int], 
    config: Dict[str, any],
    verbose: bool = False
) -> List[int]:
    """
    Process data list.
    
    Args:
        data: List of integers to process
        config: Configuration dictionary
        verbose: Enable verbose logging
        
    Returns:
        List[int]: Processed data
    """
    if verbose:
        logger.info(f"Processing {len(data)} items")
    
    return [x * 2 for x in data]


def load_file(path: Path) -> Optional[str]:
    """
    Load file content.
    
    Args:
        path: File path to load
        
    Returns:
        Optional[str]: File content or None if not found
    """
    if not path.exists():
        return None
    return path.read_text()
```

**Benefits:**
- ✅ IDE autocomplete works
- ✅ Type checker catches bugs
- ✅ Clear API documentation
- ✅ Self-documenting code

---

## § 8: Complete Stage Example - Best Practices

**This example combines ALL best practices:**

```python
#!/usr/bin/env python3
"""
Audio normalization stage - normalizes audio levels to target LUFS.

This stage:
- Reads audio from previous stage
- Normalizes to configured LUFS target
- Tracks all inputs and outputs in manifest
- Logs progress and performance metrics
"""

# Standard library
import sys
import time
from pathlib import Path
from typing import Optional

# Third-party
import numpy as np
import pyloudnorm as pyln
import soundfile as sf

# Local
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config_loader import load_config
from shared.logger import get_logger
from shared.stage_utils import StageIO


def normalize_audio(
    input_path: Path, 
    output_path: Path, 
    target_lufs: float
) -> dict:
    """
    Normalize audio file to target LUFS.
    
    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        target_lufs: Target loudness in LUFS (e.g., -23.0)
        
    Returns:
        dict: Processing metrics (duration, loudness_before, loudness_after)
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If audio format is unsupported
    """
    logger = get_logger(__name__)
    
    # Load audio
    data, rate = sf.read(str(input_path))
    
    # Measure loudness
    meter = pyln.Meter(rate)
    loudness = meter.integrated_loudness(data)
    
    # Normalize
    normalized_data = pyln.normalize.loudness(data, loudness, target_lufs)
    
    # Save
    sf.write(str(output_path), normalized_data, rate)
    
    return {
        "duration_sec": len(data) / rate,
        "loudness_before": round(loudness, 2),
        "loudness_after": round(target_lufs, 2),
        "sample_rate": rate
    }


def run_audio_normalization(
    job_dir: Path, 
    stage_name: str = "audio_normalization"
) -> int:
    """
    Run audio normalization stage.
    
    Args:
        job_dir: Path to job directory
        stage_name: Name of this stage
        
    Returns:
        int: Exit code (0=success, 1=failure)
    """
    # Step 1: Initialize StageIO with manifest
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    start_time = time.time()
    
    try:
        logger.info("=" * 70)
        logger.info(f"STAGE: {stage_name.upper()}")
        logger.info("=" * 70)
        
        # Step 2: Load configuration
        config = load_config()
        target_lufs = float(config.get("AUDIO_TARGET_LUFS", -23.0))
        
        logger.info(f"Configuration:")
        logger.info(f"  Target LUFS: {target_lufs}")
        
        # Step 3: Find input from previous stage
        input_audio = io.job_dir / "01_demux" / "audio.wav"
        
        if not input_audio.exists():
            raise FileNotFoundError(f"Input audio not found: {input_audio}")
        
        # Step 4: Track input
        io.manifest.add_input(input_audio, io.compute_hash(input_audio))
        logger.info(f"Input: {input_audio}")
        logger.info(f"  Size: {input_audio.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Step 5: Define output in stage directory
        output_audio = io.stage_dir / "audio_normalized.wav"
        
        # Step 6: Process
        logger.info("Normalizing audio...")
        metrics = normalize_audio(input_audio, output_audio, target_lufs)
        
        logger.info("Normalization complete:")
        logger.info(f"  Duration: {metrics['duration_sec']:.2f}s")
        logger.info(f"  Loudness before: {metrics['loudness_before']} LUFS")
        logger.info(f"  Loudness after: {metrics['loudness_after']} LUFS")
        logger.info(f"  Sample rate: {metrics['sample_rate']} Hz")
        
        # Step 7: Track output
        io.manifest.add_output(output_audio, io.compute_hash(output_audio))
        logger.info(f"Output: {output_audio}")
        logger.info(f"  Size: {output_audio.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Step 8: Finalize manifest
        elapsed = time.time() - start_time
        logger.info(f"Stage completed in {elapsed:.2f}s")
        logger.info("=" * 70)
        
        io.finalize_stage_manifest(exit_code=0)
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1
        
    except ValueError as e:
        logger.error(f"Invalid audio format: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1
        
    except Exception as e:
        logger.error(f"Normalization failed: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Audio normalization stage"
    )
    parser.add_argument(
        "--job-dir", 
        type=Path, 
        required=True,
        help="Job directory path"
    )
    parser.add_argument(
        "--stage-name",
        type=str,
        default="audio_normalization",
        help="Stage name"
    )
    
    args = parser.parse_args()
    sys.exit(run_audio_normalization(args.job_dir, args.stage_name))
```

**This example shows:**
- ✅ Proper imports (Standard/Third-party/Local)
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings
- ✅ Logger usage (no print)
- ✅ Complete StageIO pattern
- ✅ Config via load_config()
- ✅ Specific error handling
- ✅ Stage directory containment
- ✅ Manifest tracking
- ✅ Performance logging
- ✅ CLI argument parsing

---

## 📊 Quick Reference Cheat Sheet

```
┌────────────────────────────────────────────────────────────┐
│ CODE STANDARDS QUICK REFERENCE                             │
├────────────────────────────────────────────────────────────┤
│ LOGGING:                                                   │
│   ❌ print("message")                                      │
│   ✅ logger.info("message")                                │
│   ✅ logger.error("error", exc_info=True)                  │
│                                                            │
│ IMPORTS:                                                    │
│   ✅ # Standard library                                    │
│   ✅ import os                                             │
│   ✅                                                        │
│   ✅ # Third-party                                         │
│   ✅ import numpy                                          │
│   ✅                                                        │
│   ✅ # Local                                               │
│   ✅ from shared.config import load_config                 │
│                                                            │
│ STAGEIO:                                                    │
│   ✅ io = StageIO(name, job_dir, enable_manifest=True)    │
│   ✅ logger = io.get_stage_logger()                        │
│   ✅ io.manifest.add_input(file, hash)                     │
│   ✅ output = io.stage_dir / "file"  # Not job_dir!      │
│   ✅ io.manifest.add_output(file, hash)                    │
│   ✅ io.finalize_stage_manifest(exit_code=0)              │
│                                                            │
│ CONFIG:                                                     │
│   ❌ os.getenv("VAR")                                      │
│   ✅ config = load_config()                                │
│   ✅ val = int(config.get("VAR", default))                │
│                                                            │
│ ERRORS:                                                     │
│   ✅ except FileNotFoundError as e:                        │
│   ✅     logger.error(f"Not found: {e}", exc_info=True)   │
│   ✅     raise                                             │
│                                                            │
│ TYPE HINTS:                                                 │
│   ✅ def func(x: int, y: str = "default") -> bool:        │
│                                                            │
│ VALIDATION:                                                 │
│   Run: ./scripts/validate-compliance.py file.py           │
└────────────────────────────────────────────────────────────┘
```

---

## 🔍 Common Anti-Patterns to Avoid

### 1. **Silent Failures**
```python
# ❌ DON'T
try:
    risky_operation()
except:
    pass  # WRONG: Silently swallows errors

# ✅ DO
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
```

### 2. **String Booleans**
```python
# ❌ DON'T
debug = config.get("DEBUG", False)  # Returns string "False"
if debug:  # Always True!

# ✅ DO
debug = config.get("DEBUG", "false").lower() == "true"
if debug:  # Correctly boolean
```

### 3. **Hardcoded Paths**
```python
# ❌ DON'T
output = Path("/tmp/output.txt")

# ✅ DO
output = io.stage_dir / "output.txt"
```

### 4. **Missing exc_info**
```python
# ❌ DON'T
except Exception as e:
    logger.error(f"Error: {e}")  # No traceback

# ✅ DO
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)  # Full traceback
```

### 5. **No Input Validation**
```python
# ❌ DON'T
def process(data):
    return data[0]  # Might crash

# ✅ DO
def process(data: List[str]) -> str:
    if not data:
        raise ValueError("Data list is empty")
    return data[0]
```

---

## 📚 Additional Resources

- **Full standards:** `docs/developer/DEVELOPER_STANDARDS.md`
- **Copilot instructions:** `.github/copilot-instructions.md`
- **Compliance checker:** `scripts/validate-compliance.py`
- **Model routing:** `docs/AI_MODEL_ROUTING.md`
- **Baseline metrics:** `docs/BASELINE_COMPLIANCE_METRICS.md`

---

## ✅ Validation

**Before committing, verify:**
```bash
# Run compliance checker
./scripts/validate-compliance.py your_file.py

# Run tests
pytest tests/

# Check style
flake8 your_file.py  # If available
```

---

**Last Updated:** December 2, 2025  
**Version:** 1.0 (Phase 5)  
**Examples:** 8 sections, 40+ code snippets
