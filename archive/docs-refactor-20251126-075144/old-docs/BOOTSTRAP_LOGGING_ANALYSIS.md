# Bootstrap Logging Standards Compliance Analysis

**Date**: 2025-11-25  
**Script**: `scripts/bootstrap.sh`  
**Standard**: `scripts/common-logging.sh`

## Executive Summary

The bootstrap script has **partial compliance** with the common logging standard:

- **55% compliance** - Using common-logging functions
- **45% non-compliance** - Using plain `echo` statements
- **53 violations** - Plain echo with messages that should use logging functions

## Detailed Analysis

### Logging Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| **Total output statements** | 186 | 100% |
| **Using common-logging** | 103 | **55%** ✅ |
| **Plain echo statements** | 83 | **45%** ⚠️ |

### Breakdown by Function

| Function | Usage Count | Status |
|----------|-------------|--------|
| `log_info` | 55 | ✅ Good |
| `log_success` | 20 | ✅ Good |
| `log_section` | 17 | ✅ Good |
| `log_warn` | 6 | ✅ Good |
| `log_error` | 5 | ✅ Good |
| `echo ""` (blank lines) | 33 | ✅ Acceptable |
| `echo "message"` | 53 | ❌ **Should use logging** |

## Common Logging Standard

According to `scripts/common-logging.sh`, scripts should use:

### Available Functions

```bash
log_debug()    # Debug messages (LOG_LEVEL=DEBUG only)
log_info()     # Info messages [TIMESTAMP] [INFO]
log_warn()     # Warnings [TIMESTAMP] [WARN]
log_error()    # Errors [TIMESTAMP] [ERROR]
log_success()  # Success [TIMESTAMP] [SUCCESS] ✓
log_failure()  # Failure [TIMESTAMP] [FAILURE] ✗
log_section()  # Section headers (====)
```

### Benefits of Standard

1. **Consistent Timestamps** - All output includes `[YYYY-MM-DD HH:MM:SS]`
2. **Log Levels** - Clear categorization `[INFO]`, `[ERROR]`, etc.
3. **File Logging** - Automatic logging to `logs/YYYYMMDD-HHMMSS-bootstrap.log`
4. **Color Coding** - Visual distinction in terminal
5. **Structured Output** - Easy to parse and search

## Violations Found

### High Priority (User-Facing Messages)

**Lines 657-666** - Environment summary:
```bash
echo "✅ Environments created:"
echo "   venv/common      - Core utilities"
echo "   venv/whisperx    - WhisperX ASR"
# ... etc
```

**Should be**:
```bash
log_success "Environments created:"
log_info "  venv/common      - Core utilities"
log_info "  venv/whisperx    - WhisperX ASR"
# ... etc
```

**Lines 688-702** - Model caching prompt:
```bash
echo "⚠️  IMPORTANT: Models will download on first pipeline run if not cached now."
echo ""
echo "Pre-caching models enables:"
echo "  ✅ Fully offline pipeline execution"
# ... etc
```

**Should be**:
```bash
log_warn "IMPORTANT: Models will download on first pipeline run if not cached now."
echo ""
log_info "Pre-caching models enables:"
log_info "  ✅ Fully offline pipeline execution"
# ... etc
```

**Lines 728-737** - Next steps:
```bash
echo "📖 Next steps:"
echo "   1. Place media files in: in/"
echo "   2. Prepare a job: ./prepare-job.sh in/video.mp4 --subtitle -s hi -t en"
# ... etc
```

**Should be**:
```bash
log_info "📖 Next steps:"
log_info "   1. Place media files in: in/"
log_info "   2. Prepare a job: ./prepare-job.sh in/video.mp4 --subtitle -s hi -t en"
# ... etc
```

### Medium Priority (File Logging Only)

**Lines 350-355** - Log file header:
```bash
echo "========================================" >> "$LOG_FILE"
echo "Bootstrap started: $(date)" >> "$LOG_FILE"
echo "Platform: $OS_TYPE ($ARCH_TYPE)" >> "$LOG_FILE"
```

**Should be**:
```bash
# These are already logged via common-logging's automatic file logging
# Consider removing or using log_info which logs to both console and file
```

### Low Priority (Acceptable)

**Blank lines** - `echo ""` (33 occurrences)
- **Status**: ✅ Acceptable
- **Reason**: Used for spacing/formatting
- **Note**: Not a violation

## Recommendations

### 1. High Priority Fixes (User-Facing)

**Convert user-facing echo to logging functions**:

```bash
# Before:
echo "✅ Environments created:"
echo "   venv/common      - Core utilities"

# After:
log_success "Environments created:"
log_info "  venv/common      - Core utilities"
```

**Impact**: ~30 lines to convert
**Benefit**: Consistent timestamps, better logging, structured output

### 2. Medium Priority Fixes (File Logging)

**Remove duplicate file logging**:

```bash
# Before:
echo "========================================" >> "$LOG_FILE"
echo "Bootstrap started: $(date)" >> "$LOG_FILE"

# After:
# Remove - common-logging already handles this
```

**Impact**: ~10 lines to remove
**Benefit**: Reduce code duplication

### 3. Low Priority (Enhancement)

**Add log_debug for verbose mode**:

```bash
# Before:
if [ "$DEBUG_MODE" = true ]; then
    echo "  Checking directory: $dir"
fi

# After:
log_debug "Checking directory: $dir"
# Automatically only shows when LOG_LEVEL=DEBUG
```

**Impact**: ~5 lines to convert
**Benefit**: Cleaner debug mode handling

## Compliance Matrix

| Section | Lines | Current | Should Be | Priority |
|---------|-------|---------|-----------|----------|
| Help text | 45-60 | `echo` | `echo` | ✅ OK (help text) |
| Logging setup | 325-355 | Mixed | `log_*` | Medium |
| Environment creation | 360-650 | `log_*` | `log_*` | ✅ Good |
| Summary | 657-666 | `echo` | `log_*` | **High** |
| Model caching prompt | 688-702 | `echo` | `log_*` | **High** |
| Next steps | 728-740 | `echo` | `log_*` | **High** |
| Final summary | 745-762 | `echo` | `log_*` | Medium |

## Expected Improvements

### After Compliance

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Logging compliance | 55% | 95% | +40% |
| Plain echo (messages) | 53 | 5 | -90% |
| Timestamp coverage | 55% | 95% | +40% |
| Log file completeness | Partial | Full | Better |

### Acceptable Exceptions

These uses of `echo` are **acceptable**:

1. **Blank lines**: `echo ""` for spacing
2. **Help text**: Usage/help messages (can stay as plain echo)
3. **Read prompts**: Interactive prompts with `read -p`
4. **Piping to commands**: `echo "$data" | command`

## Implementation Plan

### Phase 1: High Priority (User-Facing)
**Estimated time**: 30 minutes

```bash
# Lines 657-666: Environment summary
- echo "✅ Environments created:"
+ log_success "Environments created:"

# Lines 688-702: Model caching info
- echo "⚠️  IMPORTANT: ..."
+ log_warn "IMPORTANT: ..."

# Lines 728-740: Next steps
- echo "📖 Next steps:"
+ log_info "📖 Next steps:"
```

### Phase 2: Medium Priority (Cleanup)
**Estimated time**: 15 minutes

```bash
# Lines 350-355: Remove duplicate file logging
- echo "========================================" >> "$LOG_FILE"
- echo "Bootstrap started: $(date)" >> "$LOG_FILE"
# Remove - already logged by common-logging
```

### Phase 3: Low Priority (Enhancement)
**Estimated time**: 10 minutes

```bash
# Add debug logging where appropriate
+ log_debug "Environment variable set: FOO=$FOO"
```

**Total estimated time**: ~1 hour

## Testing Plan

### 1. Verify Logging Functions Work
```bash
./bootstrap.sh --help
# Should still show help normally (echo is OK here)

./bootstrap.sh --skip-cache
# Should show timestamped log messages

grep "ERROR\|WARN\|INFO" logs/bootstrap_*.log
# Should show all messages with timestamps
```

### 2. Verify File Logging
```bash
./bootstrap.sh --skip-cache
tail -50 logs/bootstrap_*.log
# Should contain all user-facing messages with timestamps
```

### 3. Verify No Regressions
```bash
./bootstrap.sh --cache-models --skip-cache
# Should complete successfully
# All output should be readable and formatted
```

## Conclusion

### Current State
- **55% compliant** with common-logging standard
- **53 violations** of plain echo for user messages
- Good use of logging functions in model caching (new code)
- Inconsistent between old and new code sections

### Recommended Action

✅ **IMPLEMENT PHASE 1** (High Priority)
- Convert user-facing echo to log_* functions
- Estimated time: 30 minutes
- High impact on consistency

⚠️ **CONSIDER PHASE 2** (Medium Priority)
- Remove duplicate file logging
- Estimated time: 15 minutes
- Cleanup benefit

❓ **OPTIONAL PHASE 3** (Low Priority)
- Add debug logging enhancements
- Estimated time: 10 minutes
- Nice-to-have

### Benefits of Full Compliance

1. **Consistent Output** - All messages timestamped
2. **Better Debugging** - Full log files with context
3. **Easier Troubleshooting** - Searchable timestamps
4. **Professional Look** - Uniform formatting
5. **Maintainability** - Single logging standard

---

**Status**: Analysis Complete  
**Recommendation**: Implement Phase 1 (High Priority) fixes  
**Expected Improvement**: 55% → 95% compliance  
