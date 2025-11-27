# Bootstrap Debug Mode Guide

## Overview

The bootstrap script now supports **debug mode** for detailed logging and troubleshooting. This captures all INFO, WARNING, ERROR, and DEBUG messages to a log file for analysis.

## Usage

### Basic Bootstrap (No Debug)

```bash
# Standard bootstrap - minimal console output
./scripts/bootstrap.sh
```

### Debug Mode

```bash
# Enable debug mode with automatic timestamped log
./scripts/bootstrap.sh --debug

# Specify custom log file
./scripts/bootstrap.sh --debug --log-file logs/my_bootstrap.log

# Help
./scripts/bootstrap.sh --help
```

## Features

### 1. Dual Logging

All messages are written to:
- **Console**: Standard user-friendly output
- **Log File**: Detailed timestamped entries

### 2. Log Levels

The system captures multiple log levels:

- **INFO**: General informational messages
- **SUCCESS**: Successful operations
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors
- **DEBUG**: Detailed diagnostic information (only in debug mode)
- **SECTION**: Major section headers

### 3. Automatic Log File

If no log file is specified, one is automatically created:

```
logs/bootstrap_YYYYMMDD_HHMMSS.log
```

Example: `logs/bootstrap_20241117_152430.log`

## Log File Format

```
════════════════════════════════════════════════════════════════════════
CP-WHISPERX-APP BOOTSTRAP LOG
════════════════════════════════════════════════════════════════════════
Start Time: 2024-11-17 15:24:30
Debug Mode: true
Log File: logs/bootstrap_20241117_152430.log
════════════════════════════════════════════════════════════════════════

[2024-11-17 15:24:30] [INFO] One-time environment setup...
[2024-11-17 15:24:30] [INFO] Platform: Darwin (arm64)
[2024-11-17 15:24:30] [DEBUG] Debug mode enabled - verbose logging to: logs/bootstrap_20241117_152430.log
[2024-11-17 15:24:31] [INFO] Using python: /usr/local/bin/python3
[2024-11-17 15:24:31] [DEBUG] Python binary path: /usr/local/bin/python3
[2024-11-17 15:24:32] [INFO] Python version: 3.11.5
[2024-11-17 15:24:32] [DEBUG] Python version info: 3.11.5
[2024-11-17 15:24:33] [INFO] Found existing virtualenv in .bollyenv
[2024-11-17 15:24:33] [DEBUG] Virtualenv directory: /Users/rpatel/Projects/cp-whisperx-app/.bollyenv
[2024-11-17 15:24:35] [SUCCESS] Optional dependencies installed
...

════════════════════════════════════════════════════════════════════════
BOOTSTRAP COMPLETION SUMMARY
════════════════════════════════════════════════════════════════════════
End Time: 2024-11-17 15:35:45
Duration: 675 seconds

Environment Configuration:
  • Python: 3.11.5
  • Virtual Environment: .bollyenv
  • Platform: Darwin (arm64)
  • Log File: logs/bootstrap_20241117_152430.log

Installed Components:
  ✓ Python packages from requirements.txt
  ✓ Optional enhancements (jellyfish, sentence-transformers)
  ✓ IndicTrans2 dependencies
  ✓ torch 2.8.0 / torchaudio 2.8.0
  ✓ numpy 2.0.2

Status: SUCCESS
════════════════════════════════════════════════════════════════════════
```

## Analyzing Logs

### Check for Errors

```bash
# Find all errors
grep "\[ERROR\]" logs/bootstrap_*.log

# Find all warnings
grep "\[WARNING\]" logs/bootstrap_*.log

# Find specific issues
grep -i "failed\|error\|exception" logs/bootstrap_*.log
```

### View Debug Information

```bash
# View all debug messages (only present with --debug)
grep "\[DEBUG\]" logs/bootstrap_*.log

# View specific component installation
grep "IndicTrans2" logs/bootstrap_*.log
```

### Full Log Analysis

```bash
# View entire log with timestamps
cat logs/bootstrap_YYYYMMDD_HHMMSS.log

# Tail last 50 lines
tail -50 logs/bootstrap_YYYYMMDD_HHMMSS.log

# Follow log in real-time (in another terminal)
tail -f logs/bootstrap_YYYYMMDD_HHMMSS.log
```

## Use Cases

### 1. Installation Issues

If bootstrap fails, re-run with debug mode:

```bash
./scripts/bootstrap.sh --debug --log-file logs/debug_bootstrap.log

# Then analyze the log
grep -E "\[ERROR\]|\[WARNING\]" logs/debug_bootstrap.log
```

### 2. Share Logs for Support

```bash
# Create debug log for support team
./scripts/bootstrap.sh --debug --log-file logs/support_bootstrap.log

# Share logs/support_bootstrap.log with support team
```

### 3. CI/CD Integration

```bash
# Always use debug mode in CI/CD for detailed logs
./scripts/bootstrap.sh --debug --log-file artifacts/bootstrap.log
```

### 4. Performance Analysis

```bash
# Run with debug to see timing information
./scripts/bootstrap.sh --debug

# Check duration at the end of log
grep "Duration:" logs/bootstrap_*.log
```

## Troubleshooting

### Issue: Log File Not Created

**Check:**
```bash
# Ensure logs directory exists
ls -la logs/

# Check permissions
ls -ld logs/
```

**Fix:**
```bash
mkdir -p logs
chmod 755 logs
```

### Issue: Too Much Output

Debug mode can be verbose. Use without `--debug` for cleaner console output:

```bash
# Clean console, log still created
./scripts/bootstrap.sh --log-file logs/bootstrap.log
```

### Issue: Want Both Debug and Clean Console

```bash
# Debug to file only, clean console
./scripts/bootstrap.sh --debug --log-file logs/debug.log 2>&1 | grep -v "DEBUG:"
```

## Log Retention

### Manual Cleanup

```bash
# Remove old logs (older than 30 days)
find logs/ -name "bootstrap_*.log" -mtime +30 -delete

# Keep only last 10 logs
ls -t logs/bootstrap_*.log | tail -n +11 | xargs rm -f
```

### Automated Cleanup Script

Create `scripts/cleanup_old_logs.sh`:

```bash
#!/bin/bash
# Keep last 10 bootstrap logs
cd /path/to/cp-whisperx-app
ls -t logs/bootstrap_*.log | tail -n +11 | xargs rm -f
echo "Cleaned up old bootstrap logs"
```

## Examples

### Example 1: First-Time Setup

```bash
# Run bootstrap with debug for first-time setup
./scripts/bootstrap.sh --debug --log-file logs/initial_setup.log

# If successful, you'll see:
# 📋 Bootstrap log saved to: logs/initial_setup.log
# 🔍 Debug mode was enabled - detailed logs available
```

### Example 2: Debugging IndicTrans2 Installation

```bash
# Focus on IndicTrans2 setup
./scripts/bootstrap.sh --debug 2>&1 | tee logs/indictrans2_debug.log

# Then analyze
grep -A 10 "INDICTRANS2" logs/indictrans2_debug.log
```

### Example 3: CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Bootstrap Environment
  run: |
    ./scripts/bootstrap.sh --debug --log-file artifacts/bootstrap.log
  
- name: Upload Bootstrap Log
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: bootstrap-log
    path: artifacts/bootstrap.log
```

## Summary

**Benefits:**
- ✅ Comprehensive logging for troubleshooting
- ✅ Timestamped entries for chronological analysis
- ✅ Multiple log levels (INFO, WARNING, ERROR, DEBUG)
- ✅ Automatic log file creation
- ✅ Completion summary with statistics
- ✅ Easy to share for support

**Usage:**
```bash
# Standard
./scripts/bootstrap.sh

# With Debug
./scripts/bootstrap.sh --debug

# Custom Log
./scripts/bootstrap.sh --debug --log-file logs/my_log.log
```

**Analysis:**
```bash
# View log
cat logs/bootstrap_*.log

# Find errors
grep "\[ERROR\]" logs/bootstrap_*.log

# Check completion
tail -20 logs/bootstrap_*.log
```

---

*Last Updated: November 17, 2024*  
*Version: 2.0*
