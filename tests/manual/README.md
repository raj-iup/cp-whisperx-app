# Manual Test Scripts

**Purpose:** Developer testing and validation scripts

---

## Overview

Manual test scripts are shell/PowerShell scripts for interactive testing, quick validation, and platform-specific testing. These are NOT automated pytest tests.

---

## Directory Structure

```
tests/manual/
├── README.md           # This file
├── glossary/           # Glossary feature tests
│   ├── test-glossary-quickstart.sh
│   └── test-glossary-quickstart.ps1
├── source-separation/  # Source separation tests
├── venv/               # Virtual environment checks
└── workflows/          # Workflow validation scripts
```

---

## Running Manual Scripts

### Unix/Linux/macOS
```bash
./tests/manual/glossary/test-glossary-quickstart.sh
```

### Windows (PowerShell)
```powershell
.\tests\manual\glossary\test-glossary-quickstart.ps1
```

---

## Writing Manual Scripts

### Shell Script Template
```bash
#!/bin/bash
# Test: Feature Name
# Purpose: Quick validation of feature X

set -e  # Exit on error

# Setup
TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"

# Log output
LOG_FILE=$(python3 -c "from shared.log_paths import get_log_path; print(get_log_path('testing', 'my-test', 'detail'))")

echo "Testing Feature X..." | tee "$LOG_FILE"

# Test execution
cd "$PROJECT_ROOT"
./prepare-job.sh --media in/sample.mp4 --workflow transcribe 2>&1 | tee -a "$LOG_FILE"

# Validation
if [ -f "out/latest/job/07_alignment/transcript.txt" ]; then
    echo "✅ Test passed" | tee -a "$LOG_FILE"
else
    echo "❌ Test failed" | tee -a "$LOG_FILE"
    exit 1
fi
```

### PowerShell Script Template
```powershell
# Test: Feature Name
# Purpose: Quick validation of feature X

$ErrorActionPreference = "Stop"

# Setup
$TestDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$TestDir\..\.."

# Log output
$LogFile = python -c "from shared.log_paths import get_log_path; print(get_log_path('testing', 'my-test', 'detail'))"

Write-Host "Testing Feature X..." | Tee-Object -FilePath $LogFile

# Test execution
Set-Location $ProjectRoot
.\prepare-job.ps1 -Media in\sample.mp4 -Workflow transcribe 2>&1 | Tee-Object -Append -FilePath $LogFile

# Validation
if (Test-Path "out\latest\job\07_alignment\transcript.txt") {
    Write-Host "✅ Test passed" | Tee-Object -Append -FilePath $LogFile
} else {
    Write-Host "❌ Test failed" | Tee-Object -Append -FilePath $LogFile
    exit 1
}
```

---

## Guidelines

### DO:
- ✅ Create both `.sh` and `.ps1` versions (cross-platform)
- ✅ Use `shared.log_paths.get_log_path()` for logs
- ✅ Provide clear success/failure messages
- ✅ Clean up temporary files
- ✅ Document purpose in script header

### DON'T:
- ❌ Write logs to project root
- ❌ Leave test output in `out/`
- ❌ Hardcode file paths
- ❌ Skip error handling

---

## Log Management

All manual test logs go to `logs/testing/manual/`:

```bash
# Get log path
LOG_FILE=$(python3 -c "from shared.log_paths import get_log_path; print(get_log_path('testing', 'my-feature', 'validation'))")

# Returns: logs/testing/manual/20251208_150045_my-feature_validation.log
```

---

## Existing Scripts

### Glossary Tests
- **`test-glossary-quickstart.sh`** - Quick glossary feature validation
- **`test-glossary-quickstart.ps1`** - Windows version

**Purpose:** Test glossary loading and application in subtitle workflow  
**Runtime:** ~5-10 minutes  
**Sample Media:** Uses test clip with known character names

---

## When to Use Manual Scripts

**Use manual scripts for:**
- Interactive testing
- Quick feature validation
- Platform-specific testing
- Debug scenarios
- Ad-hoc experiments

**Use pytest for:**
- Automated testing
- CI/CD integration
- Regression testing
- Unit/integration tests

---

**See Also:**
- **tests/README.md** - Main testing guide
- **AD-012** - Log management architecture
- **AD-013** - Test organization architecture

---

**Last Updated:** 2025-12-08
