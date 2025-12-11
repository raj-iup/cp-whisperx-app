# TRD: Centralized Log File Management

**ID:** TRD-2025-12-08-03  
**Created:** 2025-12-08  
**Status:** Approved  
**Related BRD:** [BRD-2025-12-08-03](../brd/BRD-2025-12-08-03-log-management.md)

---

## Technical Overview

Create centralized log management with hierarchical structure and helper utilities.

---

## Architecture Changes

### Directory Structure
```
logs/
├── README.md              # Documentation
├── pipeline/              # Pipeline logs
│   └── YYYY-MM-DD/
├── testing/               # Test logs
│   ├── unit/
│   ├── integration/
│   └── manual/
└── debug/                 # Debug logs
```

---

## Implementation Requirements

### New Files

**`shared/log_paths.py`:**
```python
from pathlib import Path
from datetime import datetime

def get_log_path(category: str, purpose: str, detail: str = "") -> Path:
    """
    Get standardized log file path.
    
    Args:
        category: "testing", "debug", "pipeline"
        purpose: Feature/test being logged
        detail: Additional context
        
    Returns:
        Path to log file in logs/ directory
        
    Example:
        >>> get_log_path("testing", "transcribe", "mlx")
        logs/testing/manual/20251208_103045_transcribe_mlx.log
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{purpose}"
    if detail:
        filename += f"_{detail}"
    filename += ".log"
    
    log_dir = Path(__file__).parent.parent / "logs" / category
    if category == "testing":
        log_dir = log_dir / "manual"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / filename
```

**`logs/README.md`:** Documentation of structure

### Modified Files
- Test scripts: Use `get_log_path()` instead of hardcoded paths
- Documentation: Update Copilot instructions with AD-012

---

## Testing Requirements

### Unit Tests
```python
# tests/unit/test_log_paths.py

def test_get_log_path_structure():
    """Verify log path structure"""
    path = get_log_path("testing", "transcribe", "mlx")
    assert path.parent.name == "manual"
    assert path.name.endswith("_transcribe_mlx.log")
    
def test_creates_directory():
    """Verify directory creation"""
    path = get_log_path("testing", "new_test")
    assert path.parent.exists()
```

---

## Documentation Updates

- [ ] **AD-012_LOG_MANAGEMENT_SPEC.md** - Already exists
- [ ] **logs/README.md** - Structure documentation
- [ ] **Copilot Instructions** - Log placement rules
- [ ] **DEVELOPER_STANDARDS.md** - Log file guidelines

---

## Migration Plan

**Step 1:** Create structure
```bash
mkdir -p logs/{pipeline,testing/{unit,integration,manual},debug}
```

**Step 2:** Create helper
```bash
# Create shared/log_paths.py
```

**Step 3:** Move existing logs
```bash
mv test*.log logs/testing/manual/
mv task*.log logs/testing/manual/
```

**Step 4:** Update scripts to use helper

---

## Related Documents

- **BRD:** [BRD-2025-12-08-03-log-management.md](../brd/BRD-2025-12-08-03-log-management.md)
- **Specification:** AD-012_LOG_MANAGEMENT_SPEC.md
- **AD-012:** ARCHITECTURE.md § AD-012

---

**Version:** 1.0 | **Status:** Approved (Pending Implementation)  
**Effort:** 1-2 hours
