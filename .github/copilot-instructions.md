# Copilot Instructions — CP-WhisperX-App

**Version:** 3.0 | **Baseline:** 56.4% → **Target:** 90%+

---

## 📍 Model Routing

**Consult:** `docs/AI_MODEL_ROUTING.md` before choosing models

---

## 🗺️ Navigation: When to Consult DEVELOPER_STANDARDS.md

| Task | Section | Topics |
|------|---------|--------|
| Add new stage | § 3.1 | StageIO, manifests, logging |
| Modify config | § 4.2 | .env.pipeline, load_config() |
| Add logging | § 2.3 | Logger usage, log levels |
| Error handling | § 5 | Try/except, error logging |
| Manifest tracking | § 2.5 | Input/output tracking |
| Organize imports | § 6.1 | Standard/Third-party/Local |
| Type hints | § 6.2 | Function signatures |
| Docstrings | § 6.3 | Documentation |

**Full standards:** `docs/developer/DEVELOPER_STANDARDS.md`

---

## 🚨 Critical Rules (NEVER Violate)

### 1. Logger Usage - NOT Print (§ 2.3)

**60% of files violate this - Priority #1 fix**

❌ **DON'T:** `print("message")`

✅ **DO:**
```python
# Stages
io = StageIO("stage", job_dir, enable_manifest=True)
logger = io.get_stage_logger()

# Non-stages
from shared.logger import get_logger
logger = get_logger(__name__)

# Usage
logger.debug("Diagnostic info")
logger.info("General info")
logger.warning("Unexpected situation")
logger.error("Error occurred", exc_info=True)  # Include traceback
logger.critical("Severe error")
```

---

### 2. Import Organization (§ 6.1)

**100% of files violate this - Priority #2 fix**

❌ **DON'T:** Mix import groups

✅ **DO:**
```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import numpy as np

# Local
from shared.config import load_config
```

**Order:** Standard → Third-party → Local (blank lines between)

---

### 3. StageIO Pattern (§ 2.6)

**Every stage MUST:**

```python
#!/usr/bin/env python3
# Standard library
import sys
from pathlib import Path

# Local
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config_loader import load_config
from shared.stage_utils import StageIO

def run_stage(job_dir: Path, stage_name: str = "stage") -> int:
    # 1. Initialize with manifest
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        # 2. Load config
        config = load_config()
        
        # 3. Find input
        input_file = io.job_dir / "prev_stage" / "input.ext"
        io.manifest.add_input(input_file, io.compute_hash(input_file))
        
        # 4. Define output in stage dir ONLY
        output_file = io.stage_dir / "output.ext"
        
        # 5. Process
        logger.info("Processing...")
        # your logic here
        
        # 6. Track output
        io.manifest.add_output(output_file, io.compute_hash(output_file))
        
        # 7. Finalize
        io.finalize_stage_manifest(exit_code=0)
        return 0
        
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1
```

**Must have:**
- `enable_manifest=True`
- `io.get_stage_logger()` (not print)
- Track inputs: `io.manifest.add_input()`
- Track outputs: `io.manifest.add_output()`
- Write to `io.stage_dir` ONLY
- Finalize: `io.finalize_stage_manifest()`

---

### 4. Configuration (§ 4)

❌ **DON'T:** `os.getenv()` or `os.environ[]`

✅ **DO:**
```python
from shared.config_loader import load_config

config = load_config()
value = int(config.get("PARAM_NAME", default))  # Always provide default
```

**Steps:**
1. Add to `config/.env.pipeline`
2. Use `load_config()`
3. Provide default with `.get(key, default)`
4. Convert types: int(), float(), bool()

---

### 5. Error Handling (§ 5)

```python
try:
    risky_operation()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}", exc_info=True)
    raise
except PermissionError as e:
    logger.error(f"Permission denied: {e}", exc_info=True)
    raise
except Exception as e:
    logger.error(f"Unexpected: {e}", exc_info=True)
    raise RuntimeError(f"Failed: {e}")
```

**Key:** Specific exceptions first, always `exc_info=True`

---

### 6. Stage Directory Containment (§ 1.1)

❌ **DON'T:**
```python
output = job_dir / "file.ext"  # Wrong: job root
output = Path("/tmp/file.ext")  # Wrong: /tmp
```

✅ **DO:**
```python
output = io.stage_dir / "file.ext"  # Correct: stage dir only
```

---

## 📋 Pre-Commit Checklist

**ALL code:**
- [ ] Logger, not print (§ 2.3)
- [ ] Imports organized (§ 6.1)
- [ ] Type hints (§ 6.2)
- [ ] Docstrings (§ 6.3)
- [ ] Error handling (§ 5)

**STAGE code:**
- [ ] `enable_manifest=True` (§ 2.6)
- [ ] `io.get_stage_logger()` (§ 2.3)
- [ ] Track inputs (§ 2.5)
- [ ] Track outputs (§ 2.5)
- [ ] Write to `io.stage_dir` only (§ 1.1)
- [ ] Finalize manifest (§ 2.6)

**CONFIG changes:**
- [ ] Added to `.env.pipeline` (§ 4.1)
- [ ] Uses `load_config()` (§ 4.2)
- [ ] Has default value (§ 4.3)

**Dependencies:**
- [ ] Added to `requirements/*.txt` (§ 1.3)

---

## 🎯 Common Patterns

### Multiple Inputs
```python
for f in input_dir.glob("*.wav"):
    io.manifest.add_input(f, io.compute_hash(f))
```

### Config Types
```python
config = load_config()
int_val = int(config.get("MAX_DURATION", 3600))
float_val = float(config.get("THRESHOLD", 0.85))
bool_val = config.get("ENABLED", "true").lower() == "true"
list_val = config.get("LANGS", "en,hi").split(",")
```

### Progress Logging
```python
for i, item in enumerate(items):
    if i % 100 == 0:
        logger.info(f"Progress: {i}/{len(items)} ({i/len(items)*100:.0f}%)")
```

### Performance Logging
```python
import time
start = time.time()
result = expensive_op()
logger.info(f"Completed in {time.time()-start:.2f}s")
```

---

## 🏗️ Tech Stack

- **Python:** 3.11+
- **Stages:** 01_demux, 02_tmdb, etc.
- **I/O:** `shared/stage_utils.py`
- **Config:** `config/.env.pipeline`
- **Logging:** Main + stage logs

---

## 🔗 References

**Complete standards:** `docs/developer/DEVELOPER_STANDARDS.md`

**Sections:**
- § 1: Project structure
- § 2: Logging
- § 3: Stages
- § 4: Configuration
- § 5: Error handling
- § 6: Code style
- § 7: Testing

**Guides:**
- `docs/developer-guide.md` - Onboarding
- `docs/BASELINE_COMPLIANCE_METRICS.md` - Current state
- `docs/AI_MODEL_ROUTING.md` - Model selection

---

## 📊 Status

**Baseline:** 56.4% compliance

**Strong (100%):** Type hints, docstrings, config usage, error handling

**Needs work:**
- Logger usage: 40% → 100%
- Import org: 0% → 80%

**Target:** 90%+

---

## 🚀 Testing

- Tests in `tests/`
- Run: `pytest tests/`
- Unit tests: fast (no GPU)
- Coverage: `pytest --cov`

---

**When in doubt, check § reference in DEVELOPER_STANDARDS.md**

**Version:** 3.0 (Phase 1) | **Lines:** 290
