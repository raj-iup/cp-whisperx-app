# Copilot Instructions — CP-WhisperX-App

**Version:** 3.2 (Phase 3) | **Baseline:** 56.4% → **Validated:** 100% → **Target:** 90%+

---

## ⚡ Before You Respond

**Run this mental checklist:**
1. Will I use `logger` instead of `print()`? (§ 2.3)
2. Are imports organized Standard/Third-party/Local? (§ 6.1)
3. If stage: Does it use StageIO with `enable_manifest=True`? (§ 2.6)
4. Are outputs going to `io.stage_dir` only? (§ 1.1)
5. Am I using `load_config()` not `os.getenv()`? (§ 4.2)

**If NO to any → Check the relevant § section below**

---

## 📍 Model Routing

**Consult:** `docs/AI_MODEL_ROUTING.md` before choosing models

---

## 🗺️ Quick Navigation Table

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

## 🌲 Decision Trees

### Should I Create a New Stage?

```
Start here:
├─ Is this a distinct transformation step? 
│  ├─ NO → Add to existing stage
│  └─ YES → Continue
│
├─ Can it run independently?
│  ├─ NO → Consider combining with related stage
│  └─ YES → Continue
│
├─ Does it need separate logging/manifest?
│  ├─ NO → Might be a helper function
│  └─ YES → Continue
│
├─ Would it create excessive I/O overhead?
│  ├─ YES → Consider combining stages
│  └─ NO → ✅ CREATE NEW STAGE
│
└─ If YES to all: Follow § 3.1 pattern
```

### What Type of Error Handling Do I Need?

```
Error type:
├─ File not found → FileNotFoundError + logger.error()
├─ Permission denied → PermissionError + logger.error()
├─ Invalid config → ValueError + logger.error()
├─ Network/API → OSError/RequestException + retry logic
├─ Data validation → ValueError + descriptive message
└─ Unknown → Exception + exc_info=True

Always:
├─ Log with logger.error(..., exc_info=True)
├─ Provide context in message
└─ Re-raise or return error code
```

### Where Should This Output Go?

```
Output destination:
├─ Stage processing result?
│  └─ ✅ io.stage_dir / "filename.ext"
│
├─ Temporary/scratch file?
│  └─ ✅ io.stage_dir / "temp" / "file.ext"
│
├─ Final pipeline output?
│  └─ ❌ Write to io.stage_dir, pipeline copies to out/
│
├─ Shared between stages?
│  └─ ❌ Each stage writes own copy, use manifests
│
└─ NEVER:
    ├─ job_dir / "file" (breaks isolation)
    ├─ /tmp/ (unreliable)
    └─ other_stage_dir/ (breaks data lineage)
```

---

## 📚 Topical Index

### By Component

**Configuration (§ 4)**
- Adding parameters → § 4.1, § 4.2
- Loading config → § 4.2
- Type conversion → § 4.3, § 4.4
- Secrets handling → § 4.6
- Validation → § 4.7

**Logging (§ 2)**
- Basic logging → § 2.3
- Stage logs → § 2.4
- Log levels → § 2.3.2
- Performance logging → § 2.3.4
- Error logging → § 2.3.5

**Stages (§ 3)**
- Creating new stage → § 3.1
- StageIO pattern → § 2.6
- Input handling → § 3.2
- Output tracking → § 3.3
- Dependencies → § 3.4

**Data Tracking (§ 2)**
- Manifests → § 2.5
- Input tracking → § 2.5.3
- Output tracking → § 2.5.4
- Data lineage → § 2.8
- Hash computation → § 2.5.2

**Code Quality (§ 6)**
- Import organization → § 6.1
- Type hints → § 6.2
- Docstrings → § 6.3
- Function patterns → § 6.4
- Testing → § 7

### By Task

**I need to...**
- ...add a stage → § 3.1, Decision Tree #1
- ...log something → § 2.3, Critical Rule #1
- ...handle errors → § 5, Decision Tree #2
- ...add config → § 4.1, § 4.2
- ...track files → § 2.5
- ...organize imports → § 6.1, Critical Rule #2
- ...write outputs → § 1.1, Decision Tree #3
- ...validate data → § 5, § 7.2

### By Problem

**Common Issues:**
- "Print not working" → Use logger (§ 2.3)
- "Output not found" → Check io.stage_dir (§ 1.1)
- "Manifest error" → enable_manifest=True (§ 2.6)
- "Config not loading" → Use load_config() (§ 4.2)
- "Import error" → Organize properly (§ 6.1)
- "Permission denied" → Error handling (§ 5)
- "File not tracked" → add_input/output (§ 2.5)

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
logger.error("Error occurred", exc_info=True)
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
- Track inputs/outputs
- Write to `io.stage_dir` ONLY
- Finalize manifest

---

### 4. Configuration (§ 4)

❌ **DON'T:** `os.getenv()` or `os.environ[]`

✅ **DO:**
```python
from shared.config_loader import load_config

config = load_config()
value = int(config.get("PARAM_NAME", default))
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

**Before proposing code, verify:**

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

**Run automated checker:**
```bash
./scripts/validate-compliance.py your_file.py
```

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
- § 2: Logging & manifests
- § 3: Stages
- § 4: Configuration
- § 5: Error handling
- § 6: Code style
- § 7: Testing

**Guides:**
- **`docs/CODE_EXAMPLES.md`** - ⭐ Good vs Bad code examples (941 lines)
- `docs/developer-guide.md` - Onboarding
- `docs/BASELINE_COMPLIANCE_METRICS.md` - Current state
- `docs/AI_MODEL_ROUTING.md` - Model selection

---

## 🤖 Automated Validation

**Check compliance before committing:**
```bash
# Single file
./scripts/validate-compliance.py scripts/your_stage.py

# Multiple files
./scripts/validate-compliance.py scripts/*.py

# Strict mode (exit 1 on violations)
./scripts/validate-compliance.py --strict scripts/*.py

# Check staged files
./scripts/validate-compliance.py --staged
```

**Integrates with pre-commit hooks (optional)**

---

## 📊 Status

**Baseline:** 56.4% → **Phase 1 Validated:** 100% → **Target:** 90%+

**Strong (100%):** Type hints, docstrings, config, error handling

**Improving:**
- Logger: 40% → 90%+ (validated)
- Imports: 0% → 80%+ (validated)

---

## 🚀 Testing

- Tests in `tests/`
- Run: `pytest tests/`
- Unit: fast (no GPU)
- Coverage: `pytest --cov`

---

**When in doubt:**
1. Run the mental checklist at the top
2. Use decision trees above
3. **Check CODE_EXAMPLES.md for visual examples** ⭐ NEW
4. Check § reference in DEVELOPER_STANDARDS.md
5. Run `validate-compliance.py` on your code

**Version:** 3.3 (Phase 5) | **Lines:** 487 | **Validated:** 100% | **Examples:** ✅
