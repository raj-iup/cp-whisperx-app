# Stage Logging & Manifest - Quick Reference Card

**For:** Pipeline Stage Developers  
**Version:** 1.0  
**Updated:** November 27, 2025

---

## ⚡ Quick Start (Copy & Paste)

```python
#!/usr/bin/env python3
"""Stage: your_stage - Description"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.stage_utils import StageIO

def main():
    io = StageIO("your_stage")
    logger = io.get_stage_logger()
    
    try:
        logger.info("Starting stage")
        
        # Input
        input_file = io.get_input_path("input.json")
        io.track_input(input_file, "json")
        
        # Process
        # ... your code ...
        
        # Output
        output_file = io.get_output_path("output.json")
        io.track_output(output_file, "json")
        
        io.finalize(status="success")
        logger.info("Stage complete")
        return 0
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        io.finalize(status="failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 📝 Common Operations

### Initialize Stage
```python
from shared.stage_utils import StageIO

io = StageIO("stage_name")
logger = io.get_stage_logger()
```

### Track Files
```python
# Input
io.track_input(file_path, "audio", format="wav")

# Output
io.track_output(file_path, "transcript", segments=142)

# Cache/Temp
io.track_intermediate(cache_path, retained=True, 
                     reason="Model cache")
```

### Log Messages
```python
logger.debug("Detailed step")     # Only in stage.log
logger.info("Progress update")    # In both logs
logger.warning("Warning message") # In both logs
logger.error("Error occurred")    # In both logs
```

### Track Configuration
```python
io.set_config({
    "model": "large-v2",
    "device": "cuda",
    "batch_size": 16
})
```

### Track Issues
```python
# Warning
io.add_warning("Low quality input detected")

# Error
try:
    process()
except Exception as e:
    io.add_error(str(e), e)
```

### Finalize Stage
```python
# Success
io.finalize(status="success")

# Failure
io.finalize(status="failed")

# Skipped
io.finalize(status="skipped", reason="Feature disabled")
```

---

## 📂 Where Things Go

```
out/job/
├── logs/
│   └── 99_pipeline_*.log          # Main log (INFO+)
├── 06_asr/
│   ├── stage.log                  # Stage log (ALL levels)
│   ├── manifest.json              # I/O tracking
│   ├── output.json                # Your outputs
│   └── .cache/                    # Intermediate files
└── manifest.json                  # Job manifest
```

---

## 🔍 What Gets Logged Where

| Level | stage.log | pipeline.log | Console |
|-------|-----------|--------------|---------|
| DEBUG | ✅ | ❌ | ❌ |
| INFO  | ✅ | ✅ | ✅ |
| WARNING | ✅ | ✅ | ✅ |
| ERROR | ✅ | ✅ | ✅ |

---

## 📊 Manifest Structure

```json
{
  "stage": "asr",
  "stage_number": 6,
  "status": "success",
  "duration_seconds": 44.8,
  
  "inputs": [
    {"type": "audio", "path": "...", "size_bytes": 123}
  ],
  
  "outputs": [
    {"type": "transcript", "path": "...", "size_bytes": 456}
  ],
  
  "intermediate_files": [
    {"path": "...", "retained": true, "reason": "..."}
  ],
  
  "config": {"model": "large-v2", ...},
  "resources": {"cpu_percent": 45.2, ...},
  "warnings": ["..."],
  "errors": []
}
```

---

## ✅ Migration Checklist

- [ ] Import `StageIO`
- [ ] Replace logger: `io = StageIO()`, `logger = io.get_stage_logger()`
- [ ] Add `io.track_input()` for inputs
- [ ] Add `io.track_output()` for outputs
- [ ] Add `io.track_intermediate()` for cache/temp
- [ ] Add `io.set_config()` for config
- [ ] Add `io.add_warning()/add_error()` for issues
- [ ] Add `io.finalize()` at end
- [ ] Test: Check `stage.log` exists
- [ ] Test: Check `manifest.json` exists

---

## 🐛 Troubleshooting

**No stage.log?**
→ Call `io.get_stage_logger()`

**Empty manifest?**
→ Call `io.track_*()` methods and `io.finalize()`

**Logs duplicated?**
→ Only call `io.get_stage_logger()` once

---

## 📚 Full Documentation

- **Architecture:** `docs/STAGE_LOGGING_ARCHITECTURE.md`
- **Guide:** `docs/STAGE_LOGGING_IMPLEMENTATION_GUIDE.md`
- **Summary:** `docs/STAGE_LOGGING_SUMMARY.md`
- **Test:** `test_stage_logging.py`

---

## 🎯 Key Benefits

✅ Separate detailed logs per stage  
✅ Complete I/O lineage tracking  
✅ Better debugging capabilities  
✅ Full audit trail  
✅ Resource usage monitoring  
✅ Backward compatible  

---

**Need Help?** Run `python3 test_stage_logging.py` to see working example
