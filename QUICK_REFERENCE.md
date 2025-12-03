# CP-WhisperX-App - Quick Reference Guide

**Last Updated:** 2025-12-03  
**Status:** ✅ Production Ready (100% Critical Compliance)

---

## 📊 Current Status at a Glance

| Metric | Value | Status |
|--------|-------|--------|
| **Critical Violations** | 0 | ✅ PERFECT |
| **Error Violations** | 0 | ✅ PERFECT |
| **Warning Violations** | 209 | ⚠️ Documentation only |
| **Clean Files** | 26/69 | ✅ 37.7% |
| **Production Ready** | YES | ✅ DEPLOY READY |

---

## �� Key Documentation

### Compliance Reports
- **FINAL_COMPLIANCE_STATUS.md** - Complete status overview
- **PRIORITIZED_ACTION_PLAN_STATUS.md** - Plan completion status
- **COMPLIANCE_REPORT.md** - Detailed baseline metrics
- **PHASE[1-3]_COMPLETION_REPORT.md** - Phase-specific results

### Standards & Guidelines
- **.github/copilot-instructions.md** - Coding standards (v3.3)
- **docs/developer/DEVELOPER_STANDARDS.md** - Full technical specs
- **docs/CODE_EXAMPLES.md** - Good vs Bad examples
- **docs/developer-guide.md** - Onboarding guide

---

## 🚀 Quick Commands

### Run Compliance Check
```bash
# Check all files
python3 scripts/validate-compliance.py scripts/*.py shared/*.py

# Check specific file
python3 scripts/validate-compliance.py path/to/file.py

# Check staged files
python3 scripts/validate-compliance.py --staged
```

### Expected Output
```
Files checked: 69
Total violations: 0 critical, 0 errors, 209 warnings
```

### Run Pipeline
```bash
# Full pipeline
./run-pipeline.sh

# Prepare job
./prepare-job.sh <input-file>

# Test glossary
./test-glossary-quickstart.sh
```

---

## ✅ Critical Standards Checklist

Before committing code, ensure:

- [ ] **Logger usage:** No `print()`, use `logger.info()`
- [ ] **Imports:** Organized as Standard/Third-party/Local
- [ ] **Config:** Use `load_config()`, not `os.getenv()`
- [ ] **StageIO:** Stages use `enable_manifest=True`
- [ ] **Stage logger:** Use `io.get_stage_logger()`
- [ ] **Outputs:** Write to `io.stage_dir` only
- [ ] **Track I/O:** Use `io.manifest.add_input/output()`

---

## 📝 Common Patterns

### Logger Setup
```python
# For stages
io = StageIO("stage_name", job_dir, enable_manifest=True)
logger = io.get_stage_logger()

# For other modules
from shared.logger import get_logger
logger = get_logger(__name__)
```

### Import Organization
```python
# Standard library
import os
import sys

# Third-party
import numpy as np

# Local
from shared.config import load_config
```

### Config Loading
```python
config = load_config()
value = int(config.get("PARAM_NAME", default_value))
```

---

## 🎯 Project Structure

```
cp-whisperx-app/
├── scripts/           # Pipeline stages & helpers
│   ├── prepare-job.py
│   ├── run-pipeline.py
│   └── [stage scripts]
├── shared/           # Shared modules
│   ├── logger.py
│   ├── config.py
│   ├── stage_utils.py
│   └── [other modules]
├── config/           # Configuration
│   └── .env.pipeline
├── tests/            # Test suites
└── docs/            # Documentation
```

---

## 🔧 Essential Files

### Entry Points
- `bootstrap.sh` - Environment setup
- `prepare-job.sh` / `scripts/prepare-job.py` - Job preparation
- `run-pipeline.sh` / `scripts/run-pipeline.py` - Pipeline execution
- `test-glossary-quickstart.sh` - Glossary testing

### Core Infrastructure
- `shared/logger.py` - Logging setup
- `shared/config.py` - Configuration management
- `shared/stage_utils.py` - StageIO and utilities
- `shared/manifest.py` - Data lineage tracking

---

## 🎓 Learning Resources

### For New Developers
1. Read `.github/copilot-instructions.md` (mental checklist)
2. Review `docs/CODE_EXAMPLES.md` (visual examples)
3. Check `docs/developer-guide.md` (onboarding)
4. Reference `DEVELOPER_STANDARDS.md` (detailed specs)

### For Code Review
1. Run `validate-compliance.py` on changed files
2. Check critical rules compliance
3. Verify logger usage (no print statements)
4. Ensure imports are organized

---

## ⚠️ What's Remaining?

**209 warnings** (non-blocking, documentation only):
- Type hints for internal methods (~130)
- Docstrings for private functions (~79)

**Impact:** None on functionality  
**Priority:** Low (optional improvements)  
**Effort:** 5-8 hours to reach 90% overall  
**Recommendation:** Address gradually during feature work

---

## 🏆 Achievements Unlocked

✅ Zero print() statements in production code  
✅ Zero critical violations  
✅ Zero error violations  
✅ All imports organized  
✅ All stages use manifests  
✅ 5.5MB unused code removed  
✅ 900+ violations fixed  
✅ Production ready

---

## 🚨 If You Break Compliance

### Run the validator
```bash
python3 scripts/validate-compliance.py your_file.py
```

### Fix common issues

**Print statements:**
```python
# ❌ Wrong
print("Processing...")

# ✅ Correct
logger.info("Processing...")
```

**Imports:**
```python
# ❌ Wrong
import numpy as np
import os
from shared.config import load_config

# ✅ Correct
import os

import numpy as np

from shared.config import load_config
```

**Config:**
```python
# ❌ Wrong
value = os.getenv("PARAM")

# ✅ Correct
config = load_config()
value = config.get("PARAM", default)
```

---

## 🤝 Support

**Having issues?**
1. Check the relevant § section in DEVELOPER_STANDARDS.md
2. Look for examples in CODE_EXAMPLES.md
3. Run validate-compliance.py for hints
4. Review phase completion reports for patterns

**Standards Questions?**
- See `.github/copilot-instructions.md` for quick reference
- See `docs/developer/DEVELOPER_STANDARDS.md` for details

---

## 📅 Version History

- **v3.3** (2025-12-03): 100% critical compliance achieved
- **v3.2** (2025-12-02): Phase 3 completion, import organization
- **v3.1** (2025-12-02): Phase 2 completion, infrastructure fixes
- **v3.0** (2025-12-02): Phase 1 completion, top 3 critical files fixed

---

**Remember:** The goal is production-ready code, not perfection. All critical issues are resolved. Remaining warnings can be addressed gradually. 🎉
