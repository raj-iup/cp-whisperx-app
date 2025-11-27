# Logging Troubleshooting Guide

**Last Updated:** 2025-11-19  
**Audience:** Developers and Advanced Users

---

## Quick Diagnosis

### Problem: No log files created

**Symptoms:**
- Running scripts but no files appear in `logs/` directory
- Cannot find pipeline logs in job directory

**Solutions:**

1. **Check write permissions:**
   ```bash
   ls -ld logs/
   # Should show: drwxr-xr-x
   
   # If missing, create directory
   mkdir -p logs
   chmod 755 logs
   ```

2. **Verify scripts source common logging:**
   ```bash
   # Bash scripts should have:
   source "$(dirname "$0")/scripts/common-logging.sh"
   
   # PowerShell scripts should have:
   . "$PSScriptRoot\scripts\common-logging.ps1"
   ```

3. **Check if LOG_FILE is set to invalid path:**
   ```bash
   # Unset if problematic
   unset LOG_FILE
   ```

---

### Problem: Debug messages not appearing

**Symptoms:**
- Running with `LOG_LEVEL=DEBUG` but still only seeing INFO messages
- Need more verbose output

**Solutions:**

1. **Bash - Export LOG_LEVEL before running:**
   ```bash
   export LOG_LEVEL=DEBUG
   ./prepare-job.sh movie.mp4 --transcribe -s hi
   ```

2. **PowerShell - Set environment variable:**
   ```powershell
   $env:LOG_LEVEL = "DEBUG"
   .\prepare-job.ps1 movie.mp4 -Transcribe -SourceLanguage hi
   ```

3. **Python scripts - Edit config/.env.pipeline:**
   ```bash
   # Add or modify:
   LOG_LEVEL=DEBUG
   ```

4. **Verify LOG_LEVEL is being read:**
   ```bash
   # Bash
   echo $LOG_LEVEL
   
   # PowerShell
   echo $env:LOG_LEVEL
   ```

---

### Problem: Logs are missing timestamps

**Symptoms:**
- Log messages appear but without `[YYYY-MM-DD HH:MM:SS]` prefix
- Logs lack structure

**Solutions:**

1. **Verify common logging is sourced:**
   ```bash
   # Check script has this line near the top:
   source "$SCRIPT_DIR/scripts/common-logging.sh"
   ```

2. **Check for custom echo statements:**
   - Scripts should use `log_info` not `echo`
   - Replace `echo "message"` with `log_info "message"`

3. **Verify common logging file exists:**
   ```bash
   ls -l scripts/common-logging.sh
   ls -l scripts/common-logging.ps1
   ```

---

### Problem: Colors not working in terminal

**Symptoms:**
- Log messages appear but no colors
- All text is same color

**Solutions:**

1. **Terminal doesn't support colors:**
   ```bash
   # Check if terminal supports ANSI colors
   echo -e "\033[0;31mRed Text\033[0m"
   # Should display "Red Text" in red
   ```

2. **Colors disabled when piping:**
   ```bash
   # Colors are automatically disabled when output is piped
   ./bootstrap.sh | tee output.log  # No colors (expected)
   ./bootstrap.sh                   # Colors enabled
   ```

3. **Force color output:**
   - Colors are detected automatically based on terminal capability
   - Bash: Uses `[ -t 1 ]` to detect TTY
   - PowerShell: Always attempts color output

---

### Problem: Log files are too large

**Symptoms:**
- Log files growing to several GB
- Disk space running low

**Solutions:**

1. **Use DEBUG mode only when needed:**
   ```bash
   # Default INFO level creates smaller logs
   unset LOG_LEVEL
   ./prepare-job.sh movie.mp4 --transcribe -s hi
   ```

2. **Clean old log files:**
   ```bash
   # Remove logs older than 7 days
   find logs/ -name "*.log" -mtime +7 -delete
   
   # Archive old logs
   tar -czf logs-archive-$(date +%Y%m%d).tar.gz logs/*.log
   rm logs/*.log
   ```

3. **Implement log rotation (advanced):**
   ```bash
   # Add to crontab (edit with: crontab -e)
   0 0 * * * find /path/to/cp-whisperx-app/logs -name "*.log" -mtime +7 -delete
   ```

---

### Problem: Cannot find pipeline logs

**Symptoms:**
- Job completed but cannot find stage logs
- Looking in wrong directory

**Solutions:**

1. **Pipeline logs are in job directory:**
   ```bash
   # Structure: out/YYYY/MM/DD/UserID/counter/logs/
   ls out/2025/11/19/user01/0001/logs/
   
   # Stage-ordered files:
   # 01_demux_20251119_143000.log
   # 06_asr_20251119_143500.log
   # etc.
   ```

2. **Find job directory by job ID:**
   ```bash
   # Search for job.json with matching job_id
   find out -name "job.json" -exec grep -l "job-20251119-user01-0001" {} \;
   ```

3. **Use pipeline-status script:**
   ```bash
   # Bash
   ./scripts/pipeline-status.sh job-20251119-user01-0001
   
   # PowerShell
   .\scripts\pipeline-status.ps1 job-20251119-user01-0001
   ```

---

### Problem: Logs show UTF-8 encoding errors (Windows)

**Symptoms:**
- Log files display garbled characters on Windows
- Non-English text appears as `???` or boxes

**Solutions:**

1. **Python scripts automatically handle UTF-8:**
   - `shared/logger.py` sets UTF-8 encoding automatically
   - No action needed for Python logs

2. **PowerShell console encoding:**
   ```powershell
   # Set console to UTF-8
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   
   # Add to PowerShell profile for persistence
   echo '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8' >> $PROFILE
   ```

3. **View logs with UTF-8 aware tools:**
   ```powershell
   # Use Get-Content with UTF-8
   Get-Content logs\bootstrap.log -Encoding UTF8
   
   # Or use modern editors (VS Code, Notepad++)
   code logs\bootstrap.log
   ```

---

## Advanced Debugging

### Enable Verbose Logging for Specific Stage

**Python Pipeline Scripts:**

1. Edit `shared/logger.py` temporarily:
   ```python
   # Change default log_level for specific stage
   logger = setup_logger("asr", log_level="DEBUG")  # Was "INFO"
   ```

2. Or pass DEBUG at runtime:
   ```bash
   # Edit job's .env file before running
   echo "LOG_LEVEL=DEBUG" >> out/YYYY/MM/DD/UserID/JobID/.job-id.env
   ```

### Trace Function Calls (Python)

```python
# Add to beginning of Python script
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use Python's trace module
python -m trace --trace scripts/whisperx_asr.py
```

### Debug Shell Scripts

```bash
# Enable bash debug mode
bash -x prepare-job.sh movie.mp4 --transcribe -s hi

# Or add to script temporarily:
set -x  # Enable debug
# ... your code ...
set +x  # Disable debug
```

### Capture All Output

```bash
# Redirect both stdout and stderr to log file
./bootstrap.sh &> bootstrap-debug.log

# Or tee to see and save simultaneously
./bootstrap.sh 2>&1 | tee bootstrap-debug.log
```

---

## Log Analysis Tips

### Search for Errors

```bash
# Find all ERROR messages
grep -r "\[ERROR\]" logs/

# Find CRITICAL messages with context
grep -A 5 -B 5 "\[CRITICAL\]" logs/*.log

# Search in pipeline logs
grep "error" out/2025/11/19/user01/0001/logs/*.log
```

### Analyze Pipeline Timing

```bash
# Extract timestamps from stage logs
grep "started\|completed" out/YYYY/MM/DD/UserID/JobID/logs/*.log

# Calculate stage duration
# Look for [timestamp] patterns and compute differences
```

### Filter by Log Level

```bash
# Show only INFO and above (exclude DEBUG)
grep -v "\[DEBUG\]" logs/bootstrap.log

# Show only errors and critical
grep -E "\[ERROR\]|\[CRITICAL\]" logs/*.log
```

---

## Common Log Messages Explained

### `[WARN] Hardware cache expired, re-detecting...`
- **Meaning:** Hardware cache is older than 1 hour
- **Action:** None needed, automatic re-detection
- **Suppress:** Delete `out/hardware_cache.json` and re-run bootstrap

### `[ERROR] Virtual environment not found`
- **Meaning:** `.bollyenv` directory missing
- **Action:** Run `./scripts/bootstrap.sh` or `.\scripts\bootstrap.ps1`

### `[INFO] Using hardware cache (cached 15 minutes ago)`
- **Meaning:** Hardware detection skipped, using cached results
- **Action:** None needed, this speeds up job preparation
- **Force re-detection:** Run bootstrap with `--no-cache`

### `[DEBUG] DEVICE_OVERRIDE=mps`
- **Meaning:** Hardware detection set device to Apple Silicon (MPS)
- **Visibility:** Only appears when `LOG_LEVEL=DEBUG`

---

## Best Practices

### 1. Use Appropriate Log Levels

```bash
# Development/Testing: DEBUG
LOG_LEVEL=DEBUG ./prepare-job.sh ...

# Production: INFO (default)
./prepare-job.sh ...

# Automated scripts: ERROR only
LOG_LEVEL=ERROR ./prepare-job.sh ...
```

### 2. Organize Logs by Date

```bash
# Logs are automatically timestamped
# Clean old logs regularly
find logs/ -name "*.log" -mtime +30 -delete  # Keep 30 days
```

### 3. Centralize Log Review

```bash
# Create log analysis script
cat > analyze-logs.sh << 'EOF'
#!/bin/bash
echo "=== Recent Errors ==="
grep -h "\[ERROR\]" logs/*.log | tail -20

echo "=== Recent Jobs ==="
find out -name "job.json" -mtime -7 | head -10
EOF

chmod +x analyze-logs.sh
./analyze-logs.sh
```

### 4. Log Rotation for Long-Running Systems

```bash
# Add to /etc/logrotate.d/cp-whisperx-app (Linux)
/path/to/cp-whisperx-app/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
```

---

## Getting Help

If logging issues persist after following this guide:

1. **Check Logging Standards:** [docs/LOGGING_STANDARDS.md](LOGGING_STANDARDS.md)
2. **Review Logging Analysis:** `LOGGING_ANALYSIS_REPORT.md`
3. **Verify Script Compliance:** Ensure scripts use `common-logging.sh/.ps1`
4. **Report Issue:** Create GitHub issue with:
   - Script name and command run
   - Expected vs actual behavior
   - Relevant log snippets
   - System information (OS, Python version)

---

## Reference

- **Logging Standards:** [docs/LOGGING_STANDARDS.md](LOGGING_STANDARDS.md)
- **Compliance Report:** `LOGGING_ANALYSIS_REPORT.md`
- **Common Logging Modules:**
  - Bash: `scripts/common-logging.sh`
  - PowerShell: `scripts/common-logging.ps1`
  - Python: `shared/logger.py`

---

**Last Updated:** 2025-11-19  
**Maintainer:** CP-WhisperX-App Team
