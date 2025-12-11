# AD-012: Centralized Log File Management

**Date:** 2025-12-08  
**Status:** ⏳ NOT STARTED (Documentation Complete)  
**Priority:** 🟡 MEDIUM  
**Effort:** 1-2 hours

---

## Problem Statement

**Issue:** 24 log files scattered in project root causing clutter and disorganization.

**Current State:**
```
.
├── task10-test1-transcribe.log
├── task10-test2-translate.log
├── test-fixed-johny.log
├── test-hybrid-architecture.log
├── test-johny-lever.log
├── test-mlx-final.log
├── test-mlx.log
├── test-translate-mlx.log
├── test-translation-en-to-hi.log
├── test1-ad010-validation.log
├── test1-final-run.log
├── test1_execution.log
├── test2-ad010-validation.log
├── test2-correct-run.log
├── test2-final-run.log
├── test2-fixed-run.log
├── test2-fixed.log
├── test2-nllb-run.log
├── test2-rerun.log
├── test2a-en-to-es.log
├── test3-asr-fix-validation.log
├── test3-hybrid-translation-test.log
├── test3-subtitle-workflow-fixed.log
└── test3-subtitle-workflow.log
```

**Root Causes:**
- No standard for log file placement
- Test/debug logs written to current directory
- No automatic organization by date/purpose
- Manual testing creates ad-hoc log files

---

## Architectural Decision: AD-012

**Decision:** All log files must be organized in the `logs/` directory with structured hierarchy.

**Rationale:**
- Clean project root
- Organized by purpose (testing, debug, pipeline)
- Easy to find historical logs
- Consistent naming convention
- Automatic cleanup possible

---

## Solution Design

### Directory Structure

```
logs/
├── README.md                   # Directory structure documentation
├── pipeline/                   # Pipeline execution logs
│   └── {YYYY-MM-DD}/          # Organized by date
│       └── job-{id}_pipeline_{timestamp}.log
├── testing/                    # Test execution logs
│   ├── README.md              # Testing log guidelines
│   ├── integration/           # Integration test logs
│   ├── unit/                  # Unit test logs
│   └── manual/                # Manual test logs (current *.log files)
│       └── {date}_{time}_{purpose}_{detail}.log
├── debug/                      # Debug/development logs
│   └── {date}_{time}_{module}_{detail}.log
├── model-usage/               # Model usage statistics (already exists)
│   └── usage_stats.json
└── errors/                     # Error-specific logs (optional)
    └── {date}_{time}_error_{detail}.log
```

### Naming Convention

**Pattern:** `{date}_{timestamp}_{purpose}_{detail}.log`

**Examples:**
- `20251208_103045_transcribe_mlx.log`
- `20251208_110230_translate_indictrans2.log`
- `20251208_120015_integration_workflow.log`
- `20251208_143520_debug_whisperx_alignment.log`

**Components:**
- `{date}`: YYYYMMDD format
- `{timestamp}`: HHMMSS format (24-hour)
- `{purpose}`: What the log is for (transcribe, translate, debug, etc.)
- `{detail}`: Additional context (mlx, indictrans2, alignment, etc.)

---

## Implementation Plan

### Phase 1: Directory Structure (15 min)

```bash
# Create directory structure
mkdir -p logs/{pipeline,testing/{integration,unit,manual},debug,errors}

# Create README files
cat > logs/README.md << 'EOF'
# Logs Directory

All log files for CP-WhisperX-App are organized here.

## Structure

- `pipeline/` - Pipeline execution logs (organized by date)
- `testing/` - Test execution logs (integration, unit, manual)
- `debug/` - Debug and development logs
- `model-usage/` - Model usage statistics
- `errors/` - Error-specific logs (optional)

## Naming Convention

Format: `{date}_{timestamp}_{purpose}_{detail}.log`

Example: `20251208_103045_transcribe_mlx.log`

## Cleanup

Logs older than 30 days are automatically archived/deleted.

## See Also

- AD-012 in ARCHITECTURE.md
- § 5.10 in DEVELOPER_STANDARDS.md
EOF

cat > logs/testing/README.md << 'EOF'
# Testing Logs

Log files from test executions.

## Categories

- `integration/` - Integration tests
- `unit/` - Unit tests  
- `manual/` - Manual test runs

## Usage

Use the helper function:

```python
from shared.log_paths import get_log_path

log_file = get_log_path("testing", "transcribe", "mlx")
# Returns: logs/testing/manual/20251208_103045_transcribe_mlx.log
```
EOF
```

### Phase 2: Helper Function (30 min)

Create `shared/log_paths.py`:

```python
"""
Log path utilities for centralized log management (AD-012).

Provides helper functions to get standardized log file paths.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

def get_log_path(
    category: str, 
    purpose: str, 
    detail: str = "",
    base_dir: Optional[Path] = None
) -> Path:
    """
    Get standardized log file path per AD-012.
    
    Args:
        category: Log category - 'testing', 'debug', 'pipeline', 'errors'
        purpose: What the log is for (e.g., 'transcribe', 'translate')
        detail: Additional detail (e.g., 'mlx', 'hybrid', 'alignment')
        base_dir: Base directory (defaults to project root)
    
    Returns:
        Path to log file in logs/ directory
    
    Example:
        >>> log_file = get_log_path("testing", "transcribe", "mlx")
        >>> print(log_file)
        logs/testing/manual/20251208_103045_transcribe_mlx.log
    """
    if base_dir is None:
        # Find project root (where logs/ directory is)
        current = Path(__file__).resolve()
        while current.parent != current:
            if (current / "logs").exists():
                base_dir = current
                break
            current = current.parent
        else:
            base_dir = Path.cwd()
    
    # Generate timestamp
    date = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Build filename
    if detail:
        filename = f"{date}_{timestamp}_{purpose}_{detail}.log"
    else:
        filename = f"{date}_{timestamp}_{purpose}.log"
    
    # Determine subdirectory
    if category == "testing":
        log_dir = base_dir / "logs" / "testing" / "manual"
    elif category == "debug":
        log_dir = base_dir / "logs" / "debug"
    elif category == "pipeline":
        log_dir = base_dir / "logs" / "pipeline" / datetime.now().strftime("%Y-%m-%d")
    elif category == "errors":
        log_dir = base_dir / "logs" / "errors"
    else:
        raise ValueError(f"Unknown category: {category}")
    
    # Ensure directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    return log_dir / filename


def get_testing_log(purpose: str, detail: str = "") -> Path:
    """Shortcut for testing logs."""
    return get_log_path("testing", purpose, detail)


def get_debug_log(module: str, detail: str = "") -> Path:
    """Shortcut for debug logs."""
    return get_log_path("debug", module, detail)


def get_pipeline_log(job_id: str) -> Path:
    """Shortcut for pipeline logs."""
    return get_log_path("pipeline", "pipeline", job_id)
```

### Phase 3: Migration (20 min)

```bash
# Move existing logs to appropriate locations
cd /Users/rpatel/Projects/Active/cp-whisperx-app

# Move test logs
git mv test*.log logs/testing/manual/ 2>/dev/null
git mv task*.log logs/testing/manual/ 2>/dev/null

# Verify
ls logs/testing/manual/*.log | wc -l  # Should show 24 files
ls *.log 2>/dev/null | wc -l  # Should show 0 files

# Commit migration
git commit -m "chore: Migrate log files to logs/ directory (AD-012)"
```

### Phase 4: Update .gitignore (5 min)

Update `.gitignore`:

```gitignore
# Logs (AD-012: Keep structure, ignore content)
logs/**/*.log
logs/**/*.log.*
!logs/README.md
!logs/**/README.md

# Keep legacy pattern for now (will be removed)
*.log
```

### Phase 5: Update Scripts (10 min)

Example updates for test scripts:

```python
# OLD - Before AD-012
with open("test-transcribe.log", "w") as f:
    subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)

# NEW - After AD-012
from shared.log_paths import get_log_path

log_file = get_log_path("testing", "transcribe", "mlx")
with open(log_file, "w") as f:
    subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
```

---

## Validation

After implementation:

```bash
# Check project root is clean
ls *.log 2>/dev/null
# Expected: No such file or directory

# Check logs were migrated
ls logs/testing/manual/*.log | wc -l
# Expected: 24 files

# Check helper function works
python3 -c "from shared.log_paths import get_log_path; print(get_log_path('testing', 'test'))"
# Expected: logs/testing/manual/20251208_HHMMSS_test.log

# Check directory structure
tree logs/ -L 2
# Expected: Structured hierarchy
```

---

## Benefits

### User Experience
- ✅ Clean project root (no clutter)
- ✅ Easy to find logs by category
- ✅ Consistent naming across all scripts
- ✅ Date-based organization for pipeline logs

### Developer Experience
- ✅ Helper function ensures consistency
- ✅ Clear documentation (README.md in each category)
- ✅ Easy to add new log categories
- ✅ Automatic directory creation

### System Maintenance
- ✅ Automatic cleanup possible (by date)
- ✅ Better .gitignore control
- ✅ Organized for log rotation
- ✅ Ready for centralized logging (ELK, Loki, etc.)

---

## Documentation

### Updated Files

1. **ARCHITECTURE.md** (+60 lines)
   - Added AD-012 section
   - Directory structure specification
   - Code patterns and examples

2. **DEVELOPER_STANDARDS.md** (+70 lines)
   - Added § 5.10 (Log File Placement)
   - Helper function documentation
   - Common mistakes to avoid

3. **copilot-instructions.md** (+20 lines)
   - Added AD-012 to approved decisions
   - Added to Quick Patterns
   - Added to pre-commit checklist

4. **IMPLEMENTATION_TRACKER.md** (+150 lines)
   - Added Task #13 with full specification
   - Detailed implementation steps
   - Validation procedures

---

## Related Tasks

- **Task #13:** Log File Organization implementation
  - Status: ⏳ Not Started
  - Priority: 🟡 MEDIUM
  - Effort: 1-2 hours
  - Tracked in: IMPLEMENTATION_TRACKER.md

---

## References

- **AD-012:** ARCHITECTURE.md § Architectural Decisions
- **§ 5.10:** DEVELOPER_STANDARDS.md § Log File Placement
- **Task #13:** IMPLEMENTATION_TRACKER.md § Active Work
- **Pattern:** copilot-instructions.md § Quick Patterns

---

**Status:** ✅ DOCUMENTED, ⏳ PENDING IMPLEMENTATION  
**Next:** Implement in 1-2 hour session  
**Commit:** 60a1880 (documentation complete)
