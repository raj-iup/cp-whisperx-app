# CP-WhisperX-App Development Standards
**Version**: 2.0.0  
**Date**: 2025-11-25  
**Status**: Official Standards

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure Standards](#project-structure-standards)
3. [Shell Script Standards](#shell-script-standards)
4. [Python Script Standards](#python-script-standards)
5. [Documentation Standards](#documentation-standards)
6. [Code Organization](#code-organization)
7. [Logging Standards](#logging-standards)
8. [Testing Standards](#testing-standards)
9. [Git Standards](#git-standards)
10. [Refactoring Guidelines](#refactoring-guidelines)

---

## Overview

This document defines the official development standards for the CP-WhisperX-App project. All new code, refactoring, fixes, and documentation **must** follow these guidelines.

### Core Principles

1. **Self-Contained**: Scripts should be independent with minimal external dependencies
2. **Clean Structure**: Organized, logical file hierarchy
3. **Comprehensive**: Complete documentation and error handling
4. **Maintainable**: Clear, readable code with consistent patterns
5. **User-Friendly**: Helpful messages, good UX
6. **Backward Compatible**: No breaking changes without major version bump

---

## Project Structure Standards

### Root Directory Rules

**ONLY these files allowed in root:**
```
cp-whisperx-app/
├── README.md              ← ONLY documentation file in root
├── LICENSE                ← License file
├── bootstrap.sh           ← Self-contained entry point
├── prepare-job.sh         ← Self-contained entry point
└── run-pipeline.sh        ← Self-contained entry point
```

**Rationale**: Clean, uncluttered root makes project easier to navigate.

### Directory Structure Standards

```
cp-whisperx-app/
│
├── venv/                  ← ALL virtual environments here
│   ├── common/
│   ├── whisperx/
│   ├── mlx/
│   ├── pyannote/
│   ├── demucs/
│   ├── indictrans2/
│   ├── nllb/
│   └── llm/
│
├── scripts/               ← ALL implementation scripts
│   ├── *.py               Python implementations
│   ├── *.sh               Utility shell scripts
│   └── common-logging.sh  Shared logging (for utilities)
│
├── shared/                ← Shared Python modules ONLY
│   └── *.py
│
├── requirements/          ← ALL dependency files
│   └── requirements-*.txt
│
├── config/                ← Configuration templates
│   ├── .env.pipeline
│   └── secrets.example.json
│
├── docs/                  ← ALL documentation
│   ├── INDEX.md           Master index
│   ├── QUICKSTART.md
│   ├── CODEBASE_DEPENDENCY_MAP.md
│   ├── DEVELOPMENT_STANDARDS.md (this file)
│   ├── implementation-history/
│   ├── user-guide/
│   ├── technical/
│   ├── features/
│   └── archive/
│
├── glossary/              ← Glossary files
├── tests/                 ← Test scripts
├── tools/                 ← Utility tools
├── archive/               ← Historical files
├── in/                    ← Input media
├── out/                   ← Pipeline outputs
└── logs/                  ← System logs
```

### Virtual Environment Standards

**Location**: `venv/` directory only

**Naming**: Simple names without dots or prefixes
- ✅ `venv/common`
- ✅ `venv/whisperx`
- ❌ `.venv-common`
- ❌ `environments/common-venv`

**Purpose**: Each environment is specialized:
```
venv/
├── common/        → Core utilities, shared tools
├── whisperx/      → WhisperX ASR
├── mlx/           → MLX Whisper (Apple Silicon)
├── pyannote/      → PyAnnote VAD & diarization
├── demucs/        → Demucs source separation
├── indictrans2/   → IndicTrans2 translation
├── nllb/          → NLLB-200 translation
└── llm/           → LLM integration (optional)
```

---

## Shell Script Standards

### File Headers

**REQUIRED for all shell scripts:**

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Script Name - Brief Description
# ============================================================================
# Version: X.Y.Z
# Date: YYYY-MM-DD
#
# Detailed description of what the script does, its purpose, and any
# important notes about its operation.
#
# Usage:
#   ./script.sh [OPTIONS]
#
# Examples:
#   ./script.sh --option value
# ============================================================================
```

**Explanation**:
- `#!/usr/bin/env bash` - Portable shebang
- `set -euo pipefail` - Fail fast on errors
- Header block - Clear documentation
- Version and date - Track changes

### Self-Contained Pattern

**Root scripts MUST be self-contained:**

```bash
#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════════════════
# COMMON LOGGING FUNCTIONS (Integrated)
# ═══════════════════════════════════════════════════════════════════════════

# Color codes
if [ -t 1 ]; then
    COLOR_RED='\033[0;31m'
    COLOR_GREEN='\033[0;32m'
    COLOR_YELLOW='\033[1;33m'
    COLOR_BLUE='\033[0;34m'
    COLOR_CYAN='\033[0;36m'
    COLOR_NC='\033[0m'
else
    COLOR_RED='' COLOR_GREEN='' COLOR_YELLOW=''
    COLOR_BLUE='' COLOR_CYAN='' COLOR_NC=''
fi

# Log level configuration
LOG_LEVEL=${LOG_LEVEL:-INFO}

_get_log_level_value() {
    case "$1" in
        DEBUG) echo 0 ;; INFO) echo 1 ;; WARN) echo 2 ;;
        ERROR) echo 3 ;; CRITICAL) echo 4 ;; *) echo 1 ;;
    esac
}

CURRENT_LOG_LEVEL=$(_get_log_level_value "$LOG_LEVEL")

_should_log() {
    local msg_level=$(_get_log_level_value "$1")
    [ "$msg_level" -ge "$CURRENT_LOG_LEVEL" ]
}

log_debug() {
    _should_log "DEBUG" && echo -e "${COLOR_CYAN}[DEBUG]${COLOR_NC} $*" >&2 || true
}

log_info() {
    _should_log "INFO" && echo -e "${COLOR_BLUE}[INFO]${COLOR_NC} $*" || true
}

log_warn() {
    _should_log "WARN" && echo -e "${COLOR_YELLOW}[WARN]${COLOR_NC} $*" >&2 || true
}

log_error() {
    _should_log "ERROR" && echo -e "${COLOR_RED}[ERROR]${COLOR_NC} $*" >&2 || true
}

log_critical() {
    echo -e "${COLOR_RED}[CRITICAL]${COLOR_NC} $*" >&2
}

log_success() {
    echo -e "${COLOR_GREEN}✓${COLOR_NC} $*"
}

log_section() {
    echo ""
    echo -e "${COLOR_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_NC}"
    echo -e "${COLOR_CYAN}$*${COLOR_NC}"
    echo -e "${COLOR_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_NC}"
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN SCRIPT LOGIC
# ═══════════════════════════════════════════════════════════════════════════

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ... rest of script
```

**Key Points**:
- ✅ No `source` statements for logging
- ✅ All functions integrated inline
- ✅ Self-contained, single file
- ✅ Easy to copy/share

### Argument Parsing

**Standard pattern:**

```bash
# Parse arguments
OPTION1=""
OPTION2=false
LOG_LEVEL_ARG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--option1)
            OPTION1="$2"
            shift 2
            ;;
        --option2)
            OPTION2=true
            shift
            ;;
        --log-level)
            LOG_LEVEL_ARG="$2"
            shift 2
            ;;
        --debug)
            LOG_LEVEL_ARG="DEBUG"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Set log level if provided
if [ -n "$LOG_LEVEL_ARG" ]; then
    export LOG_LEVEL="$LOG_LEVEL_ARG"
    CURRENT_LOG_LEVEL=$(_get_log_level_value "$LOG_LEVEL")
fi
```

### Help Text

**REQUIRED for all user-facing scripts:**

```bash
show_usage() {
    cat << 'USAGE_EOF'
Usage: ./script.sh [OPTIONS]

Brief description of what the script does

REQUIRED OPTIONS:
  --required VALUE          Description of required option

OPTIONAL OPTIONS:
  --optional VALUE          Description of optional option
  --log-level LEVEL         Log level: DEBUG|INFO|WARN|ERROR|CRITICAL
  --debug                   Enable debug mode (same as --log-level DEBUG)
  -h, --help                Show this help message

EXAMPLES:
  # Example 1
  ./script.sh --required value

  # Example 2
  ./script.sh --required value --optional other --log-level DEBUG

NOTES:
  Any important notes or caveats

USAGE_EOF
}
```

### Error Handling

```bash
# Validate required arguments
if [ -z "$REQUIRED_ARG" ]; then
    log_critical "Required argument missing: --required"
    show_usage
    exit 1
fi

# Check file exists
if [ ! -f "$FILE_PATH" ]; then
    log_critical "File not found: $FILE_PATH"
    exit 1
fi

# Check directory exists
if [ ! -d "$DIR_PATH" ]; then
    log_critical "Directory not found: $DIR_PATH"
    log_error "Run bootstrap first: ./bootstrap.sh"
    exit 1
fi
```

### Path Resolution

**Always use absolute paths:**

```bash
# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Build paths from root
SCRIPT_DIR="$PROJECT_ROOT/scripts"
VENV_COMMON="$PROJECT_ROOT/venv/common"
CONFIG_DIR="$PROJECT_ROOT/config"

# Use absolute paths
cd "$PROJECT_ROOT"
```

### Virtual Environment Activation

```bash
# Standard pattern for activating venv
VENV_PATH="$PROJECT_ROOT/venv/common"

# Check exists
if [ ! -d "$VENV_PATH" ]; then
    log_critical "Virtual environment not found: $VENV_PATH"
    log_error "Run bootstrap first: ./bootstrap.sh"
    exit 1
fi

# Activate
export VIRTUAL_ENV="$VENV_PATH"
export PATH="$VENV_PATH/bin:$PATH"
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"
```

---

## Python Script Standards

### File Headers

```python
#!/usr/bin/env python3
"""
Script Name - Brief Description

Version: X.Y.Z
Date: YYYY-MM-DD

Detailed description of what the script does, its purpose, and any
important implementation details.

Usage:
    python script.py --option value

Examples:
    python script.py --input file.mp4 --output result.json
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Now import project modules
from shared.logger import PipelineLogger
from shared.environment_manager import EnvironmentManager
```

### Argument Parsing

```python
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Brief description",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        "--required",
        required=True,
        help="Description of required argument"
    )
    
    # Optional arguments
    parser.add_argument(
        "--optional",
        default="default_value",
        help="Description with default: %(default)s"
    )
    
    # Choices
    parser.add_argument(
        "--mode",
        choices=["mode1", "mode2", "mode3"],
        default="mode1",
        help="Mode selection"
    )
    
    # Boolean flags
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    # Log level
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_arguments()
    
    # Initialize logger
    logger = PipelineLogger(
        module_name="script_name",
        log_level=args.log_level if hasattr(args, 'log_level') else 'INFO'
    )
    
    try:
        # Main logic here
        logger.info("Starting process...")
        
        # ... implementation ...
        
        logger.info("Process completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Process failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### Logging

```python
from shared.logger import PipelineLogger

# Initialize
logger = PipelineLogger(
    module_name="my_script",
    log_file=log_dir / "script.log",
    log_level="INFO"
)

# Use throughout
logger.debug("Debug information")
logger.info("Information message")
logger.warn("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

### Type Hints

**REQUIRED for all function signatures:**

```python
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

def process_file(
    input_path: Path,
    output_path: Path,
    options: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str]:
    """
    Process a file with given options.
    
    Args:
        input_path: Path to input file
        output_path: Path to output file
        options: Optional processing options
        
    Returns:
        Tuple of (success: bool, message: str)
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If options are invalid
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")
    
    # Implementation
    return True, "Success"
```

### Docstrings

**REQUIRED for all public functions and classes:**

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.
    
    Longer description if needed, explaining the purpose,
    behavior, and any important implementation details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
        FileNotFoundError: When file doesn't exist
        
    Examples:
        >>> function_name("test", 42)
        True
    """
    pass
```

### Error Handling

```python
try:
    result = process_data(input_data)
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    return 1
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    return 1
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    if debug:
        import traceback
        traceback.print_exc()
    return 1
```

---

## Documentation Standards

### Documentation Location

**ALL documentation in `docs/` directory:**

```
docs/
├── INDEX.md                          ← Master index (REQUIRED)
├── QUICKSTART.md                     ← Quick start guide
├── CODEBASE_DEPENDENCY_MAP.md        ← Architecture reference
├── DEVELOPMENT_STANDARDS.md          ← This file
│
├── implementation-history/           ← Implementation docs
│   ├── *_COMPLETE.md                 Completion reports
│   └── *.sh                          Quick references
│
├── user-guide/                       ← User documentation
│   ├── BOOTSTRAP.md
│   ├── workflows.md
│   └── ...
│
├── technical/                        ← Technical docs
│   ├── architecture.md
│   ├── pipeline.md
│   └── ...
│
├── features/                         ← Feature guides
└── archive/                          ← Historical docs
```

### README.md (Root Only)

**The ONLY documentation file in root:**

```markdown
# Project Name

Brief description (1-2 sentences)

Multi-line description with key features.

## Quick Start

```bash
./bootstrap.sh
./prepare-job.sh --media in/file.mp4 ...
./run-pipeline.sh -j job-id
```

## Documentation

**📚 Full Documentation:** [docs/INDEX.md](docs/INDEX.md)

### Quick Links
| Topic | Link |
|-------|------|
| Getting Started | [QUICKSTART](docs/QUICKSTART.md) |
| ... | ... |

## Key Features
- Feature 1
- Feature 2

## Usage Examples
...

## License
See [LICENSE](LICENSE)
```

**Rules**:
- Keep focused on essentials
- Link to docs/ for details
- Include quick start
- Maximum ~300 lines

### Markdown Standards

```markdown
# Main Title (H1) - Only One Per File
Brief description

## Section (H2)
Content

### Subsection (H3)
Content

#### Sub-subsection (H4)
Content

---

## Code Blocks

Use fenced code blocks with language:

```bash
./script.sh --option value
```

```python
def function():
    pass
```

## Tables

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |

## Lists

Unordered:
- Item 1
- Item 2
  - Sub-item

Ordered:
1. First
2. Second
3. Third

## Links

[Link Text](URL)
[Internal Link](relative/path.md)

## Images

![Alt Text](path/to/image.png)

## Emphasis

**Bold** for emphasis
*Italic* for light emphasis
`code` for inline code

## Status Indicators

✅ Complete
❌ Not done
⏭️ Next
🚀 Launch
⚠️ Warning
```

### Documentation Templates

**Implementation Report Template:**

```markdown
# Feature/Fix Implementation Complete
**Date**: YYYY-MM-DD  
**Status**: ✅ COMPLETE

---

## Overview
Brief description of what was implemented

---

## Changes Made

### File 1
- Change 1
- Change 2

### File 2
- Change 1

---

## Before/After
Clear comparison

---

## Testing
How to test

---

## Benefits
What was improved

---

## Next Steps
What's next

---

**Status**: ✅ Ready for use!
```

---

## Code Organization

### Import Order (Python)

```python
# 1. Standard library
import argparse
import sys
from pathlib import Path
from typing import Optional, List, Dict

# 2. Third-party
import torch
import transformers

# 3. Project modules
from shared.logger import PipelineLogger
from shared.config import Config
```

### Function Order

```python
# 1. Constants
CONSTANT_NAME = value

# 2. Helper functions (private)
def _private_helper():
    pass

# 3. Public functions
def public_function():
    pass

# 4. Argument parsing
def parse_arguments():
    pass

# 5. Main function
def main():
    pass

# 6. Entry point
if __name__ == "__main__":
    sys.exit(main())
```

### File Organization

**One responsibility per file:**

```
scripts/
├── prepare-job.py        ← Job preparation only
├── run-pipeline.py       ← Pipeline orchestration only
├── whisperx_asr.py       ← WhisperX ASR only
└── indictrans2_translator.py  ← Translation only
```

---

## Logging Standards

### Log Levels

```
DEBUG    → Detailed debugging info (verbose)
INFO     → General information (default)
WARN     → Warning messages
ERROR    → Error messages
CRITICAL → Critical failures
```

### Usage Guidelines

```python
# DEBUG: Detailed flow, variable values
logger.debug(f"Processing file: {file_path}")
logger.debug(f"Options: {options}")

# INFO: High-level progress
logger.info("Starting transcription...")
logger.info("Completed successfully")

# WARN: Issues that don't stop execution
logger.warn("Model not found, using default")
logger.warn("Low confidence score: 0.3")

# ERROR: Failures that stop current operation
logger.error("File not found: input.mp4")
logger.error("Translation failed")

# CRITICAL: Severe failures
logger.critical("Environment not found")
logger.critical("Out of memory")
```

### Success Messages

```bash
log_success "✓ Virtual environment created"
log_success "✓ Model cached successfully"
log_success "✓ Pipeline completed"
```

### Section Headers

```bash
log_section "STAGE 1: SOURCE SEPARATION"
log_section "MODEL CACHING"
log_section "BOOTSTRAP COMPLETE"
```

---

## Testing Standards

### Test Organization

```
tests/
├── test_bootstrap.sh         ← Bootstrap tests
├── test_prepare_job.sh       ← Prepare job tests
├── test_pipeline.sh          ← Pipeline tests
├── test_unit_*.py            ← Unit tests
└── test_integration_*.py     ← Integration tests
```

### Shell Script Tests

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Testing bootstrap.sh..."

# Test 1: Help message
echo "Test 1: Help message"
if ./bootstrap.sh --help > /dev/null 2>&1; then
    echo "✓ Help works"
else
    echo "✗ Help failed"
    exit 1
fi

# Test 2: Argument validation
echo "Test 2: Invalid argument"
if ./bootstrap.sh --invalid-option 2>/dev/null; then
    echo "✗ Should reject invalid option"
    exit 1
else
    echo "✓ Correctly rejects invalid option"
fi

echo "All tests passed ✓"
```

### Python Unit Tests

```python
import unittest
from pathlib import Path

class TestMyModule(unittest.TestCase):
    """Test suite for my_module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("/tmp/test")
        self.test_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up after tests."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = my_function("input")
        self.assertEqual(result, "expected")
    
    def test_error_handling(self):
        """Test error handling."""
        with self.assertRaises(ValueError):
            my_function("invalid")

if __name__ == "__main__":
    unittest.main()
```

---

## Git Standards

### Commit Messages

```
Format: <type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes bug nor adds feature
- `test`: Adding tests
- `chore`: Build process or auxiliary tool changes

**Examples**:

```
feat(bootstrap): add MLX model caching

- Implement MLX Whisper model caching
- Update bootstrap to cache mlx-community/whisper-large-v3-mlx
- Add error handling for failed downloads

Closes #123
```

```
fix(translator): fix IndicTransToolkit import path

- Add sys.path manipulation for virtual environment
- Ensure toolkit is importable from venv/indictrans2
- Fixes translation failures

Fixes #456
```

```
docs: create development standards guide

- Document shell script standards
- Document Python standards
- Document project structure
- Add examples for all patterns
```

### Branch Naming

```
feature/short-description
fix/short-description
docs/short-description
refactor/short-description
```

**Examples**:
- `feature/mlx-caching`
- `fix/indictrans-import`
- `docs/development-standards`
- `refactor/venv-organization`

---

## Refactoring Guidelines

### When to Refactor

✅ **DO refactor when**:
- Code is duplicated (DRY principle)
- Function is too long (>50 lines)
- File is too large (>500 lines for scripts)
- Names are unclear
- Structure is confusing
- Adding features becomes difficult

❌ **DON'T refactor when**:
- Code is working and clear
- No clear improvement
- Breaking changes required
- Time is limited

### Refactoring Process

1. **Understand Current Code**
   - Read and understand existing implementation
   - Identify what works well
   - Document current behavior

2. **Plan Changes**
   - Write down what will change
   - Identify impact on other code
   - Plan backward compatibility

3. **Make Changes Incrementally**
   - Small, focused changes
   - Test after each change
   - Commit frequently

4. **Test Thoroughly**
   - Test existing functionality
   - Test new functionality
   - Test edge cases

5. **Document Changes**
   - Update inline comments
   - Update documentation
   - Write migration guide if needed

### Surgical Changes

**Make minimal changes:**

```bash
# BAD: Rewriting entire function
old_function() {
    # 50 lines of code
}

# GOOD: Minimal fix
old_function() {
    # 48 lines unchanged
    fixed_line  # Only change this one line
    # 1 line unchanged
}
```

### Backward Compatibility

**Maintain for at least one major version:**

```bash
# Old way (deprecated but still works)
./script.sh --old-option value

# New way
./script.sh --new-option value

# Script handles both
if [ -n "$OLD_OPTION" ]; then
    log_warn "--old-option deprecated, use --new-option"
    NEW_OPTION="$OLD_OPTION"
fi
```

---

## Code Review Checklist

### Before Submitting

- [ ] Code follows shell/Python standards
- [ ] All functions have docstrings
- [ ] Error handling implemented
- [ ] Logging added appropriately
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Self-review completed

### Review Criteria

**Functionality**:
- [ ] Does it work as intended?
- [ ] Are edge cases handled?
- [ ] Is error handling robust?

**Code Quality**:
- [ ] Is code readable?
- [ ] Are names clear?
- [ ] Is structure logical?
- [ ] No code duplication?

**Documentation**:
- [ ] Are changes documented?
- [ ] Is help text updated?
- [ ] Are examples provided?

**Testing**:
- [ ] Are tests included?
- [ ] Do all tests pass?
- [ ] Is coverage adequate?

**Standards**:
- [ ] Follows project standards?
- [ ] Consistent with existing code?
- [ ] No style violations?

---

## Quick Reference

### Shell Script Checklist

```bash
#!/usr/bin/env bash
set -euo pipefail

# [ ] Header with description
# [ ] Integrated logging functions
# [ ] Help text (show_usage)
# [ ] Argument parsing
# [ ] Error handling
# [ ] Path resolution
# [ ] Exit codes (0=success, 1=error)
```

### Python Script Checklist

```python
#!/usr/bin/env python3
"""Docstring with description"""

# [ ] Imports organized
# [ ] Type hints on functions
# [ ] Docstrings on public functions
# [ ] Argument parsing
# [ ] Logger initialized
# [ ] Error handling
# [ ] main() function
# [ ] if __name__ == "__main__"
```

### Documentation Checklist

```markdown
# [ ] In docs/ directory
# [ ] Clear title
# [ ] Date and status
# [ ] Table of contents (if long)
# [ ] Code examples
# [ ] Before/after comparisons
# [ ] Testing instructions
# [ ] Benefits explained
# [ ] Next steps listed
```

---

## Examples

### Complete Shell Script Example

See `bootstrap.sh` in project root - 327 lines of best practices.

### Complete Python Script Example

See `scripts/prepare-job.py` - follows all standards.

### Complete Documentation Example

See `docs/CODEBASE_DEPENDENCY_MAP.md` - comprehensive reference.

---

## Enforcement

### Automated Checks (Future)

- [ ] ShellCheck for shell scripts
- [ ] pylint/flake8 for Python
- [ ] markdownlint for docs
- [ ] Pre-commit hooks

### Manual Review

- All code reviewed before merge
- Standards enforced in reviews
- Documentation checked
- Tests verified

---

## Maintenance

### Updating Standards

1. Propose change with rationale
2. Discuss with team
3. Update this document
4. Update examples
5. Communicate changes

### Version History

- **2.0.0** (2025-11-25): Complete refactoring standards
- **1.0.0** (2025-11-XX): Initial standards

---

## Questions?

For questions about these standards:
1. Check examples in codebase
2. Review `docs/CODEBASE_DEPENDENCY_MAP.md`
3. Ask in discussions
4. Create issue if unclear

---

**These standards are living guidelines. Follow them for consistency, propose improvements when beneficial.**

---

**End of Development Standards**
