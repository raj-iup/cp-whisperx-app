# Preflight Script - Best Practices Compliance Report

## Current Status: ⚠️ PARTIALLY COMPLIANT

The preflight script (`preflight.py`) is functional but does not follow all the best practices we implemented for the pipeline orchestrator.

---

## ❌ Issues Found

### 1. No Manifest Integration
**Issue:** Preflight checks are not recorded in the manifest system.

**Impact:**
- No audit trail of preflight checks
- Pipeline doesn't know if preflight was run
- Can't resume/skip preflight checks

**Should Be:**
```python
manifest.set_pipeline_step(
    "preflight",
    True,
    completed=True,
    next_stage="demux",
    status="success",
    checks_passed=27,
    checks_failed=0,
    warnings=1
)
```

### 2. No Resume/Skip Capability
**Issue:** Runs all checks every time, even if they passed before.

**Impact:**
- Wastes time on static checks (directories exist, config valid)
- Re-checks Docker images that don't change between runs

**Should Have:**
```python
def should_skip_check(check_name: str, manifest: ManifestBuilder) -> bool:
    """Skip checks that don't need to be re-run."""
    # Skip static checks if they passed before
    static_checks = ["directories", "config_file", "docker_compose"]
    if check_name in static_checks:
        # Check manifest for previous pass
        return check_passed_before(check_name, manifest)
    return False
```

### 3. No Timeout Protection
**Issue:** Docker subprocess calls have no timeout.

**Impact:**
- Could hang indefinitely if Docker is unresponsive
- No way to recover from stuck checks

**Should Be:**
```python
result = subprocess.run(
    ["docker", "ps"],
    capture_output=True,
    text=True,
    timeout=30,  # Add timeout
    check=True
)
```

### 4. Results Not Persisted
**Issue:** Check results only printed to console.

**Impact:**
- Can't review what preflight found after it runs
- No record for debugging
- Can't compare results between runs

**Should Save:**
```python
preflight_results = {
    "timestamp": datetime.now().isoformat(),
    "checks_passed": self.checks_passed,
    "checks_failed": self.checks_failed,
    "warnings": self.warnings,
    "details": {
        "docker": {"status": "pass", "version": "..."},
        "disk_space": {"status": "pass", "free_gb": 38.2},
        # ... more details
    }
}
# Save to manifest or separate file
```

### 5. Incomplete Error Context
**Issue:** Errors don't include enough context for debugging.

**Should Include:**
- Timestamp of each check
- System environment details
- Retry information (if applicable)
- Suggested remediation steps

---

## ✅ What's Working Well

1. **Comprehensive Checks** - Covers Docker, images, config, secrets, resources
2. **Clear Output** - Good use of colors and formatting
3. **Warning System** - Distinguishes between failures and warnings
4. **Modularity** - Each check is a separate method
5. **User-Friendly** - Helpful error messages and suggestions

---

## 🔧 Recommended Enhancements

### Priority 1: Critical (Should Fix)

1. **Add Manifest Integration**
   ```python
   def __init__(self, manifest_file: Optional[Path] = None):
       self.manifest = ManifestBuilder(manifest_file) if manifest_file else None
       # ... rest of init
   ```

2. **Add Timeout Protection**
   ```python
   def check_docker(self) -> bool:
       try:
           result = subprocess.run(
               ["docker", "--version"],
               capture_output=True,
               text=True,
               timeout=10,  # Add this
               check=True
           )
   ```

3. **Save Results to File**
   ```python
   def save_results(self, filepath: Path):
       results = {
           "timestamp": datetime.now().isoformat(),
           "checks_passed": self.checks_passed,
           "checks_failed": self.checks_failed,
           "warnings": self.warnings,
           "details": self.check_details
       }
       with open(filepath, 'w') as f:
           json.dump(results, f, indent=2)
   ```

### Priority 2: Enhancement (Nice to Have)

1. **Skip Static Checks on Resume**
   - Check if directories/config validated before
   - Only re-check dynamic things (disk space, memory, Docker status)

2. **Detailed Error Context**
   - Save full error messages
   - Include remediation steps
   - Link to documentation

3. **Performance Tracking**
   - Time each check
   - Save to manifest

4. **Retry Logic for Transient Failures**
   - Docker API calls can be flaky
   - Retry 2-3 times before failing

---

## 📋 Implementation Plan

### Phase 1: Add Manifest Integration (30 min)

```python
class PreflightCheck:
    def __init__(self, manifest_file: Optional[Path] = None):
        self.manifest = ManifestBuilder(manifest_file) if manifest_file else None
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.check_details = {}
    
    def run_all_checks(self) -> bool:
        # ... run checks ...
        
        # Save to manifest
        if self.manifest:
            self.manifest.set_pipeline_step(
                "preflight",
                True,
                completed=True,
                next_stage="demux",
                status="success" if self.checks_failed == 0 else "failed",
                checks_passed=self.checks_passed,
                checks_failed=self.checks_failed,
                warnings=self.warnings
            )
        
        return self.checks_failed == 0
```

### Phase 2: Add Timeout Protection (15 min)

Add `timeout=10` to all subprocess.run() calls:
```python
# Before
result = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=True)

# After
result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10, check=True)
```

### Phase 3: Save Results (20 min)

```python
def save_results(self):
    results_file = Path("logs") / f"preflight_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.parent.mkdir(exist_ok=True)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks_passed": self.checks_passed,
        "checks_failed": self.checks_failed,
        "warnings": self.warnings,
        "details": self.check_details
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
```

---

## 🎯 Compliance Checklist

Current compliance with best practices:

- [ ] Manifest integration
- [ ] Resume/skip capability  
- [x] Modular structure
- [ ] Timeout protection
- [x] Error handling (partial)
- [ ] Result persistence
- [x] Progress logging
- [x] User-friendly output
- [ ] Detailed error context
- [ ] Performance tracking

**Compliance Score: 4/10 (40%)**

---

## 📊 Comparison: Pipeline vs Preflight

| Feature | Pipeline | Preflight | Gap |
|---------|----------|-----------|-----|
| Manifest tracking | ✅ Yes | ❌ No | Missing |
| Resume capability | ✅ Yes | ❌ No | Missing |
| Timeout protection | ✅ Yes | ❌ No | Missing |
| Result persistence | ✅ Yes | ❌ No | Missing |
| Error handling | ✅ Full | ⚠️ Partial | Incomplete |
| Progress tracking | ✅ Yes | ✅ Yes | ✅ Good |
| Logging | ✅ Yes | ✅ Yes | ✅ Good |

---

## 🚀 Quick Wins (Can Implement Now)

### 1. Add Timeouts (5 minutes)
```bash
# Find all subprocess.run calls and add timeout=10
sed -i '' 's/subprocess.run(/subprocess.run(timeout=10, /g' preflight.py
```

### 2. Save Results (10 minutes)
Add at end of `run_all_checks()`:
```python
# Save results
results_file = Path("logs") / "preflight_last_run.json"
with open(results_file, 'w') as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "passed": self.checks_passed,
        "failed": self.checks_failed,
        "warnings": self.warnings
    }, f, indent=2)
```

### 3. Integrate with Pipeline Manifest (20 minutes)
Update `main()` to accept manifest file:
```python
def main():
    # Check if called from pipeline with manifest path
    manifest_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    
    checker = PreflightCheck(manifest_file)
    success = checker.run_all_checks()
    
    sys.exit(0 if success else 1)
```

---

## 📝 Summary

**Current State:** Functional but not compliant with best practices

**Priority Fixes:**
1. Add manifest integration (connects to pipeline tracking)
2. Add timeout protection (prevents hangs)
3. Save results to file (audit trail)

**Estimated Effort:** 1-2 hours to fully align with best practices

**Recommendation:** Implement Phase 1 (manifest integration) first, as it provides the most value by connecting preflight to the pipeline's tracking system.
