# test-glossary-quickstart.sh Refactoring Documentation

**Date:** November 27, 2025  
**Version:** 2.0  
**Status:** ✅ IMPLEMENTED AND DOCUMENTED

---

## 📋 Executive Summary

The `test-glossary-quickstart.sh` script has been **refactored** to support:

1. ✅ **Configurable time range** (`--start-time`, `--end-time`)
2. ✅ **Configurable log level** (`--log-level DEBUG|INFO|WARN|ERROR|CRITICAL`)
3. ✅ **Log level propagation** to prepare-job.sh and run-pipeline.sh
4. ✅ **Non-interactive auto-execution** (`--auto` flag)
5. ✅ **Selective test execution** (`--skip-*` flags)
6. ✅ **Comprehensive help documentation** (`--help`)

---

## 🎯 Features

### 1. Configurable Time Range

Extract specific segments from input video for testing.

```bash
# Use default time range (00:00:00 to 00:05:00)
./test-glossary-quickstart.sh --auto

# Extract 10:00 to 15:00 segment
./test-glossary-quickstart.sh \
    --start-time 00:10:00 \
    --end-time 00:15:00 \
    --auto

# Extract first minute only
./test-glossary-quickstart.sh \
    --start-time 00:00:00 \
    --end-time 00:01:00 \
    --auto
```

**Parameters:**
- `--start-time HH:MM:SS` - Start time for extraction (default: 00:00:00)
- `--end-time HH:MM:SS` - End time for extraction (default: 00:05:00)

**Use Cases:**
- Quick testing with short clips
- Focus on specific scenes
- Consistent test durations
- CI/CD pipeline optimization

### 2. Configurable Log Level

Control verbosity of logging throughout the pipeline.

```bash
# DEBUG level - Maximum verbosity for troubleshooting
./test-glossary-quickstart.sh --log-level DEBUG --auto

# INFO level - Balanced output (default)
./test-glossary-quickstart.sh --log-level INFO --auto

# WARN level - Only warnings and errors
./test-glossary-quickstart.sh --log-level WARN --auto

# ERROR level - Only errors
./test-glossary-quickstart.sh --log-level ERROR --auto

# CRITICAL level - Only critical failures
./test-glossary-quickstart.sh --log-level CRITICAL --auto
```

**Parameters:**
- `--log-level LEVEL` - One of: DEBUG, INFO, WARN, ERROR, CRITICAL (default: INFO)

**Propagation:**
The log level is exported as `LOG_LEVEL` environment variable and propagates to:
- `prepare-job.sh` execution
- `run-pipeline.sh` execution
- All stage scripts (demux, tmdb, asr, etc.)
- All Python modules (via shared.logger)

**Implementation:**
```bash
# In test-glossary-quickstart.sh
export LOG_LEVEL="$LOG_LEVEL"

# When calling prepare-job.sh
./prepare-job.sh \
    --media "$VIDEO_PATH" \
    --workflow translate \
    --log-level "$LOG_LEVEL" \
    # ... other params

# When calling run-pipeline.sh
./run-pipeline.sh -j "$JOB_ID" --log-level "$LOG_LEVEL"
```

**Log Level Guide:**

| Level | Use Case | Output |
|-------|----------|--------|
| **DEBUG** | Development, troubleshooting | All details including debug messages, tool commands |
| **INFO** | Normal operation, testing | Progress updates, stage completion, key metrics |
| **WARN** | Production monitoring | Warnings and above, less verbose |
| **ERROR** | Production, CI/CD | Only errors and critical issues |
| **CRITICAL** | Emergency debugging | Only catastrophic failures |

### 3. Non-Interactive Auto-Execution

Run all tests automatically without manual prompts.

```bash
# Auto-execute all three tests (baseline, glossary, cache)
./test-glossary-quickstart.sh --auto

# Auto-execute with custom parameters
./test-glossary-quickstart.sh \
    --auto \
    --start-time 00:05:00 \
    --end-time 00:10:00 \
    --log-level DEBUG
```

**Parameters:**
- `--auto` - Execute all tests without prompting

**Behavior:**
- No `read -p` prompts for user input
- Automatically runs baseline test
- Automatically runs glossary test
- Automatically runs cache test
- Perfect for CI/CD pipelines
- Perfect for batch testing

**Without --auto flag:**
```bash
# Interactive mode (default)
./test-glossary-quickstart.sh

# Script prompts:
# "Run baseline test? (y/n): "
# "Run glossary test? (y/n): "
# "Run cache test? (y/n): "
```

**With --auto flag:**
```bash
# Non-interactive mode
./test-glossary-quickstart.sh --auto

# No prompts, automatic execution
# Output: "Auto-executing baseline test..."
#         "Auto-executing glossary test..."
#         "Auto-executing cache test..."
```

### 4. Selective Test Execution

Skip specific tests to focus on others.

```bash
# Run only glossary test (skip baseline and cache)
./test-glossary-quickstart.sh \
    --auto \
    --skip-baseline \
    --skip-cache

# Run only baseline test
./test-glossary-quickstart.sh \
    --auto \
    --skip-glossary \
    --skip-cache

# Run baseline and glossary, skip cache
./test-glossary-quickstart.sh \
    --auto \
    --skip-cache
```

**Parameters:**
- `--skip-baseline` - Skip the baseline (no-glossary) test
- `--skip-glossary` - Skip the glossary-enabled test
- `--skip-cache` - Skip the cache performance test

**Use Cases:**
- Focus on specific feature testing
- Reduce test execution time
- CI/CD pipeline optimization
- Iterative development workflow

### 5. Configurable Film Parameters

Test with different input videos and TMDB metadata.

```bash
# Different video file
./test-glossary-quickstart.sh \
    --video in/other-film.mp4 \
    --title "3 Idiots" \
    --year 2009 \
    --auto

# Test with another film
./test-glossary-quickstart.sh \
    --video "/path/to/video.mp4" \
    --title "Film Title" \
    --year 2020 \
    --auto
```

**Parameters:**
- `--video PATH` - Path to input video file
- `--title TITLE` - Film title for TMDB lookup
- `--year YEAR` - Film release year for TMDB lookup

**Defaults:**
- Video: `in/Jaane Tu Ya Jaane Na 2008.mp4`
- Title: `Jaane Tu Ya Jaane Na`
- Year: `2008`

### 6. Comprehensive Help Documentation

Display usage information and examples.

```bash
# Show help
./test-glossary-quickstart.sh --help
./test-glossary-quickstart.sh -h
```

**Output:**
```
Usage: ./test-glossary-quickstart.sh [OPTIONS]

Automated testing script for glossary system with configurable parameters.

OPTIONS:
  --video PATH              Input video file (default: Jaane Tu Ya Jaane Na 2008.mp4)
  --title TITLE             Film title for TMDB lookup (default: Jaane Tu Ya Jaane Na)
  --year YEAR               Film year for TMDB lookup (default: 2008)
  --start-time HH:MM:SS     Start time for clip extraction (default: 00:00:00)
  --end-time HH:MM:SS       End time for clip extraction (default: 00:05:00)
  --log-level LEVEL         Log level: DEBUG|INFO|WARN|ERROR|CRITICAL (default: INFO)
  --auto                    Auto-execute all tests without prompting
  --skip-baseline           Skip baseline test
  --skip-glossary           Skip glossary test
  --skip-cache              Skip cache test
  -h, --help                Show this help message

EXAMPLES:
  # Auto-execute all tests with defaults
  ./test-glossary-quickstart.sh --auto

  # Custom time range and debug logging
  ./test-glossary-quickstart.sh --start-time 00:10:00 --end-time 00:15:00 --log-level DEBUG --auto

  # Different film with specific parameters
  ./test-glossary-quickstart.sh --video in/other.mp4 --title "Film Name" --year 2020 --auto

  # Run only glossary test
  ./test-glossary-quickstart.sh --skip-baseline --skip-cache --auto

NOTE:
  Log level setting propagates to prepare-job.sh and run-pipeline.sh execution.
```

---

## 🔧 Implementation Details

### Argument Parsing

The script uses a robust argument parser:

```bash
# Default values
DEFAULT_START_TIME="00:00:00"
DEFAULT_END_TIME="00:05:00"
DEFAULT_LOG_LEVEL="INFO"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --start-time)
            START_TIME="$2"
            shift 2
            ;;
        --end-time)
            END_TIME="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --auto)
            AUTO_EXECUTE=true
            shift
            ;;
        --skip-baseline)
            SKIP_BASELINE=true
            shift
            ;;
        # ... other arguments
    esac
done

# Apply defaults
START_TIME="${START_TIME:-$DEFAULT_START_TIME}"
END_TIME="${END_TIME:-$DEFAULT_END_TIME}"
LOG_LEVEL="${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}"
```

### Environment Variable Export

Log level is exported for downstream scripts:

```bash
# Export log level
export LOG_LEVEL="$LOG_LEVEL"

echo "Configuration:"
echo "  Log Level: $LOG_LEVEL"
```

### Conditional Execution

Tests are conditionally executed based on flags:

```bash
# Baseline test
if [ "$SKIP_BASELINE" = true ]; then
    echo "═══ Step 1: Baseline Test - SKIPPED ═══"
else
    if [ "$AUTO_EXECUTE" = false ]; then
        read -p "Run baseline test? (y/n): " -n 1 -r
        RUN_BASELINE=$REPLY
    else
        RUN_BASELINE="y"
        echo "Auto-executing baseline test..."
    fi
    
    if [[ $RUN_BASELINE =~ ^[Yy]$ ]]; then
        # Execute baseline test with configured parameters
        ./prepare-job.sh \
            --start-time "$START_TIME" \
            --end-time "$END_TIME" \
            --log-level "$LOG_LEVEL" \
            # ... other params
    fi
fi
```

---

## 📊 Usage Examples

### Development Workflow

```bash
# 1. Quick test with debug logging (1 minute clip)
./test-glossary-quickstart.sh \
    --start-time 00:00:00 \
    --end-time 00:01:00 \
    --log-level DEBUG \
    --auto \
    --skip-cache

# 2. Normal testing (5 minute clip, INFO logging)
./test-glossary-quickstart.sh --auto

# 3. Production validation (full clip, ERROR logging only)
./test-glossary-quickstart.sh \
    --end-time 00:30:00 \
    --log-level ERROR \
    --auto
```

### CI/CD Pipeline

```bash
# Fast CI test (1 minute, minimal logging)
./test-glossary-quickstart.sh \
    --start-time 00:00:00 \
    --end-time 00:01:00 \
    --log-level ERROR \
    --auto \
    --skip-cache

# Full regression test (5 minutes, all tests)
./test-glossary-quickstart.sh \
    --log-level INFO \
    --auto

# Nightly comprehensive test (30 minutes)
./test-glossary-quickstart.sh \
    --end-time 00:30:00 \
    --log-level DEBUG \
    --auto
```

### Feature Testing

```bash
# Test glossary feature only
./test-glossary-quickstart.sh \
    --auto \
    --skip-baseline \
    --skip-cache \
    --log-level DEBUG

# Test cache performance
./test-glossary-quickstart.sh \
    --auto \
    --skip-baseline \
    --skip-glossary \
    --log-level INFO

# Compare baseline vs glossary
./test-glossary-quickstart.sh \
    --auto \
    --skip-cache \
    --log-level INFO
```

### Multi-Film Testing

```bash
# Test Film 1
./test-glossary-quickstart.sh \
    --video in/film1.mp4 \
    --title "Film One" \
    --year 2020 \
    --auto

# Test Film 2
./test-glossary-quickstart.sh \
    --video in/film2.mp4 \
    --title "Film Two" \
    --year 2021 \
    --auto

# Test Film 3
./test-glossary-quickstart.sh \
    --video in/film3.mp4 \
    --title "Film Three" \
    --year 2022 \
    --auto
```

---

## 🧪 Testing the Refactored Script

### Verify Configuration

```bash
# Test with DEBUG logging (should show all details)
./test-glossary-quickstart.sh \
    --start-time 00:00:00 \
    --end-time 00:01:00 \
    --log-level DEBUG \
    --auto \
    --skip-cache

# Check that logs contain DEBUG messages
grep "DEBUG" test-results/glossary/*pipeline*.log
```

### Verify Time Range

```bash
# Extract 1-minute clip
./test-glossary-quickstart.sh \
    --start-time 00:05:00 \
    --end-time 00:06:00 \
    --auto \
    --skip-cache

# Verify audio duration (should be ~60 seconds)
ffprobe -v error -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 \
    out/*/01_demux/audio.wav
```

### Verify Auto-Execution

```bash
# Should run without prompts
time ./test-glossary-quickstart.sh --auto

# Should complete in reasonable time (no waiting for user input)
```

### Verify Selective Execution

```bash
# Should only run glossary test
./test-glossary-quickstart.sh \
    --auto \
    --skip-baseline \
    --skip-cache

# Verify: test-results/baseline/ should NOT exist
# Verify: test-results/glossary/ should exist
# Verify: test-results/cache-run.log should NOT exist
```

---

## 📚 Related Documentation

- **[ENHANCED_LOGGING_IMPLEMENTATION.md](ENHANCED_LOGGING_IMPLEMENTATION.md)** - Logging architecture
- **[DEVELOPER_STANDARDS.md](DEVELOPER_STANDARDS.md)** - Developer standards
- **[IMPLEMENTATION_STATUS_CURRENT.md](../IMPLEMENTATION_STATUS_CURRENT.md)** - Current implementation status

---

## ✅ Verification Checklist

### Functionality

- [x] Script accepts all new command-line arguments
- [x] Default values work correctly
- [x] Custom values override defaults
- [x] Log level propagates to downstream scripts
- [x] Time range parameters work correctly
- [x] Auto-execution works without prompts
- [x] Skip flags work as expected
- [x] Help documentation displays correctly

### Integration

- [x] prepare-job.sh receives correct log level
- [x] run-pipeline.sh receives correct log level
- [x] Stage scripts respect log level
- [x] Pipeline logs show correct verbosity
- [x] Stage logs show correct verbosity
- [x] Manifests created correctly

### Edge Cases

- [x] Invalid log level defaults to INFO
- [x] Missing video file handled gracefully
- [x] Invalid time format handled gracefully
- [x] Multiple skip flags work together
- [x] Unknown arguments show error

---

## 🎊 Conclusion

The `test-glossary-quickstart.sh` script has been **successfully refactored** with:

✅ Full configuration support for time range and log levels  
✅ Non-interactive auto-execution for CI/CD  
✅ Selective test execution for focused testing  
✅ Comprehensive documentation and help  
✅ Backward compatibility maintained  
✅ Production-ready implementation

**Status:** 🎊 **REFACTORING COMPLETE - FULLY DOCUMENTED** 🎊

---

**Document Version:** 1.0  
**Created:** November 27, 2025  
**Status:** COMPLETE  
**Implementation:** ALREADY DONE (v2.0 of test-glossary-quickstart.sh)
