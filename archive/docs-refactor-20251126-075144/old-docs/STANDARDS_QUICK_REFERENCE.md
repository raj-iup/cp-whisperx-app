# Development Standards Quick Reference
**CP-WhisperX-App - Cheat Sheet**  
**Version**: 2.0.0

---

## 🎯 Core Rules

1. ✅ **Self-contained** scripts (no external dependencies)
2. ✅ **Clean structure** (organized directories)
3. ✅ **Complete docs** (comprehensive help)
4. ✅ **Error handling** (robust validation)
5. ✅ **Backward compatible** (no breaking changes)

---

## 📂 Project Structure

```
Root: Only 5 files
  README.md, LICENSE, bootstrap.sh, prepare-job.sh, run-pipeline.sh

Directories:
  venv/         → All virtual environments (8)
  scripts/      → All implementation
  shared/       → Shared Python modules
  requirements/ → All dependencies
  docs/         → ALL documentation
  config/       → Configuration
  tests/        → Tests
  tools/        → Utilities
```

---

## 🐚 Shell Script Template

```bash
#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════
# Script Name - Description
# ═══════════════════════════════════════════════════════════
# Version: X.Y.Z
# Date: YYYY-MM-DD

# Integrated logging functions (copy from bootstrap.sh)
if [ -t 1 ]; then
    COLOR_RED='\033[0;31m'; COLOR_GREEN='\033[0;32m'
    COLOR_YELLOW='\033[1;33m'; COLOR_BLUE='\033[0;34m'
    COLOR_CYAN='\033[0;36m'; COLOR_NC='\033[0m'
else
    COLOR_RED=''; COLOR_GREEN=''; COLOR_YELLOW=''
    COLOR_BLUE=''; COLOR_CYAN=''; COLOR_NC=''
fi

LOG_LEVEL=${LOG_LEVEL:-INFO}
# ... logging functions ...

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Help text
show_usage() {
    cat << 'HELP_EOF'
Usage: ./script.sh [OPTIONS]
Description

OPTIONS:
  --option VALUE    Description
  -h, --help        Show help
HELP_EOF
}

# Argument parsing
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_usage; exit 0 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

# Main logic
log_section "SCRIPT NAME"
log_info "Starting..."
# ... implementation ...
log_success "Complete!"
```

---

## 🐍 Python Script Template

```python
#!/usr/bin/env python3
"""
Script Name - Description

Version: X.Y.Z
Date: YYYY-MM-DD
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List

# Add project to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger


def parse_arguments() -> argparse.Namespace:
    """Parse arguments."""
    parser = argparse.ArgumentParser(description="Description")
    parser.add_argument("--option", required=True, help="Help text")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_arguments()
    logger = PipelineLogger("script_name", log_level=args.log_level)
    
    try:
        logger.info("Starting...")
        # ... implementation ...
        logger.info("Complete!")
        return 0
    except Exception as e:
        logger.error(f"Failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

---

## 📝 Documentation Template

```markdown
# Feature/Fix Name
**Date**: YYYY-MM-DD  
**Status**: ✅ COMPLETE

---

## Overview
What was done

---

## Changes Made
List of changes

---

## Before/After
Comparison

---

## Testing
How to test

---

## Benefits
What improved

---

**Status**: ✅ Ready!
```

---

## 🔍 Checklist: New Shell Script

- [ ] Shebang: `#!/usr/bin/env bash`
- [ ] Options: `set -euo pipefail`
- [ ] Header with version/date
- [ ] Integrated logging functions
- [ ] Help text (`show_usage()`)
- [ ] Argument parsing
- [ ] Error handling
- [ ] Absolute paths
- [ ] Exit codes (0=success, 1=error)

---

## 🔍 Checklist: New Python Script

- [ ] Shebang: `#!/usr/bin/env python3`
- [ ] Docstring at top
- [ ] Imports organized (stdlib, 3rd-party, project)
- [ ] Type hints on functions
- [ ] Docstrings on public functions
- [ ] Argument parsing
- [ ] Logger initialized
- [ ] Try/except error handling
- [ ] `main()` function
- [ ] `if __name__ == "__main__":`

---

## 🔍 Checklist: New Documentation

- [ ] In `docs/` directory
- [ ] Clear title (# H1)
- [ ] Date and status at top
- [ ] Table of contents (if >100 lines)
- [ ] Code examples with syntax highlighting
- [ ] Before/after comparisons
- [ ] Testing instructions
- [ ] Benefits explained
- [ ] Status indicators (✅ ❌ ⏭️)
- [ ] Updated `docs/INDEX.md`

---

## 📊 Log Levels

```
DEBUG    → Detailed debugging (--log-level DEBUG)
INFO     → General info (default)
WARN     → Warnings
ERROR    → Errors
CRITICAL → Critical failures
```

**Usage**:
```bash
log_debug "Detailed info"
log_info "General message"
log_warn "Warning"
log_error "Error"
log_critical "Critical!"
log_success "✓ Success"
log_section "SECTION HEADER"
```

---

## 🗂️ File Organization

```
One responsibility per file:
✅ prepare-job.py     → Job prep only
✅ run-pipeline.py    → Pipeline only
✅ whisperx_asr.py    → ASR only
❌ utils.py           → Too generic
```

---

## 🧪 Testing

```bash
# Shell script test
./script.sh --help     # Should work
./script.sh --invalid  # Should fail gracefully

# Python test
python script.py --help
python -m pytest tests/
```

---

## �� Git Commits

```
Format: <type>(<scope>): <subject>

Types:
  feat:     New feature
  fix:      Bug fix
  docs:     Documentation
  refactor: Code refactoring
  test:     Tests
  chore:    Maintenance

Examples:
  feat(bootstrap): add MLX caching
  fix(translator): fix import path
  docs: update development standards
```

---

## 🚫 Common Mistakes to Avoid

❌ **DON'T**:
- Put docs in root (only README.md)
- Use `.venv-*` naming (use `venv/name`)
- Source external scripts (be self-contained)
- Make long functions (>50 lines)
- Skip error handling
- Forget to update docs

✅ **DO**:
- Keep root clean (5 files only)
- Use `venv/` for all venvs
- Integrate logging inline
- Break into small functions
- Handle all errors
- Document everything

---

## 🎯 Virtual Environments

```
Location: venv/ ONLY

Names (no dots):
  venv/common
  venv/whisperx
  venv/mlx
  venv/pyannote
  venv/demucs
  venv/indictrans2
  venv/nllb
  venv/llm

Usage in code:
  VENV_PATH="$PROJECT_ROOT/venv/common"
  export VIRTUAL_ENV="$VENV_PATH"
  export PATH="$VENV_PATH/bin:$PATH"
```

---

## 📚 Reference Documents

Must-read:
- **DEVELOPMENT_STANDARDS.md** - Complete standards
- **CODEBASE_DEPENDENCY_MAP.md** - Architecture
- **PROJECT_REFACTORING_COMPLETE.md** - Recent changes

Examples:
- `bootstrap.sh` - Shell script example (327 lines)
- `scripts/prepare-job.py` - Python example
- `docs/VENV_REORGANIZATION_COMPLETE.md` - Doc example

---

## 🔧 Common Patterns

### Argument Parsing (Shell)
```bash
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--option) OPTION="$2"; shift 2 ;;
        -h|--help) show_usage; exit 0 ;;
        *) log_error "Unknown: $1"; exit 1 ;;
    esac
done
```

### Error Handling (Python)
```python
try:
    result = function()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    return 1
except Exception as e:
    logger.error(f"Failed: {e}")
    return 1
```

### Path Resolution
```bash
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$PROJECT_ROOT/venv/common"
```

---

## ⚡ Quick Commands

```bash
# Check standards compliance
grep -c "set -euo pipefail" script.sh  # Should be 1
grep -c "#!/usr/bin/env" script.sh     # Should be 1

# Verify structure
ls -1 | wc -l                          # Root should be ~20
ls -1 venv/                            # Should show 8 envs

# Test scripts
./bootstrap.sh --help
./prepare-job.sh --help
./run-pipeline.sh --help
```

---

## 📖 Full Documentation

For complete details, see:
- [DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md) - Full standards (4000+ lines)
- [INDEX.md](INDEX.md) - Documentation index
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide

---

**Print this for quick reference while coding!**
