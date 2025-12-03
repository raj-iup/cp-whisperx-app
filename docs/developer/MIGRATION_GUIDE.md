# Migration Guide: v2.0 → v3.0

**Purpose:** Guide for migrating existing stages to v3.0 modular architecture  
**Timeline:** 21 weeks (Phases 1-5)  
**Status:** Phase 1 Complete - Ready for Phase 2

---

## Table of Contents

1. [Overview](#overview)
2. [What's Changing](#whats-changing)
3. [Migration Path](#migration-path)
4. [Stage Conversion Process](#stage-conversion-process)
5. [Testing Strategy](#testing-strategy)
6. [Rollback Plan](#rollback-plan)

---

## Overview

**Current (v2.0):** Simplified pipeline with inline stages  
**Target (v3.0):** Modular 10-stage pipeline with StageIO pattern  
**Migration Timeline:** 21 weeks across 5 phases

### Why Migrate?

**Benefits of v3.0:**
- ✅ Selective stage enable/disable per job
- ✅ Better quality control and validation  
- ✅ Modular testing and development
- ✅ Enhanced extensibility
- ✅ Complete data lineage tracking
- ✅ Stage-level dependency management

**Risks of Not Migrating:**
- ❌ Harder to add new stages
- ❌ Difficult to debug issues
- ❌ No way to skip unnecessary stages
- ❌ Limited data lineage tracking
- ❌ Testing at pipeline level only

---

## What's Changing

### 1. Stage Structure

**Before (v2.0):**
```python
# scripts/example_stage.py
"""Simple utility script"""
import os

def process(input_path, output_path):
    """Process input and write output"""
    print("Processing...")  # ❌ Uses print
    
    # Load config directly
    max_duration = int(os.getenv("MAX_DURATION", "3600"))  # ❌ Uses os.getenv
    
    # Direct processing
    result = transform(input_path)
    
    # Write to arbitrary location
    save(result, output_path)  # ❌ No manifest tracking
    
    return result

# Called directly from pipeline orchestrator
if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    process(input_file, output_file)
```

**After (v3.0):**
```python
#!/usr/bin/env python3
# Standard library
import sys
from pathlib import Path

# Local
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config_loader import load_config
from shared.stage_utils import StageIO

def run_stage(job_dir: Path, stage_name: str = "example") -> int:
    """
    Example stage: Process data with validation
    
    Args:
        job_dir: Job directory containing input from previous stage
        stage_name: Stage name for logging (default: "example")
        
    Returns:
        0 on success, 1 on failure
    """
    # 1. Initialize StageIO with manifest
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()  # ✅ Uses logger
    
    try:
        # 2. Load configuration
        config = load_config()  # ✅ Uses load_config()
        max_duration = int(config.get("MAX_DURATION", "3600"))
        
        # 3. Find and track input
        input_file = io.job_dir / "prev_stage" / "input.ext"
        if not input_file.exists():
            raise FileNotFoundError(f"Input not found: {input_file}")
        
        io.manifest.add_input(input_file, io.compute_hash(input_file))  # ✅ Track input
        logger.info(f"Processing input: {input_file.name}")
        
        # 4. Define output in stage directory ONLY
        output_file = io.stage_dir / "output.ext"  # ✅ Stage isolation
        
        # 5. Process
        logger.info("Starting transformation...")
        result = transform(input_file, max_duration)
        save(result, output_file)
        
        # 6. Track output
        io.manifest.add_output(output_file, io.compute_hash(output_file))  # ✅ Track output
        logger.info(f"Output saved: {output_file.name}")
        
        # 7. Finalize manifest
        io.finalize_stage_manifest(exit_code=0)
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1
    except Exception as e:
        logger.error(f"Stage failed: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1

# Keep existing functions for backward compatibility
def process(input_path, output_path):
    """Legacy function - deprecated, use run_stage() instead"""
    # Can keep for compatibility during migration
    pass

if __name__ == "__main__":
    # New entry point
    if len(sys.argv) < 2:
        print("Usage: example_stage.py <job_dir>")
        sys.exit(1)
    
    job_dir = Path(sys.argv[1])
    exit_code = run_stage(job_dir)
    sys.exit(exit_code)
```

### 2. Key Differences Summary

| Aspect | v2.0 (Before) | v3.0 (After) |
|--------|---------------|--------------|
| **Entry Point** | `process()` function | `run_stage()` function |
| **Logging** | `print()` statements | `logger` from StageIO |
| **Configuration** | `os.getenv()` | `load_config()` |
| **Input Tracking** | None | `io.manifest.add_input()` |
| **Output Location** | Arbitrary | `io.stage_dir` only |
| **Output Tracking** | None | `io.manifest.add_output()` |
| **Error Handling** | Basic try/except | Comprehensive with logging |
| **Manifest** | No manifest | `manifest.json` per stage |
| **Stage Log** | No stage log | `stage.log` per stage |
| **Return Value** | Arbitrary | Exit code (0=success, 1=failure) |

---

## Migration Path

### Phase Overview

| Phase | Focus | Duration | Priority |
|-------|-------|----------|----------|
| **Phase 1** | Documentation Sync | 2 weeks | P0 Critical ✅ |
| **Phase 2** | Testing Infrastructure | 3 weeks | P1 High |
| **Phase 3** | Stage Pattern Adoption | 4 weeks | P0 Critical |
| **Phase 4** | Full Pipeline Implementation | 8 weeks | P2 Medium |
| **Phase 5** | Advanced Features | 4 weeks | P3 Low |

### Stage Conversion Priority

**Phase 3 - Critical Active Stages (4 weeks):**

1. ✅ `scripts/demux.py` → Add `run_stage()`
2. ✅ `scripts/whisperx_asr.py` → Add `run_stage()` (complex)
3. ✅ `scripts/indictrans2_translator.py` → Add `run_stage()`
4. ✅ Inline subtitle generation → Create `scripts/subtitle_gen.py`
5. ✅ `scripts/mux.py` → Add `run_stage()`

**Phase 4 - Integration of Existing Stages (8 weeks):**

6. ✅ `scripts/tmdb_enrichment_stage.py` - Already follows pattern, integrate
7. ✅ Create `scripts/03_glossary_load/glossary_loader.py`
8. ✅ Unify NER scripts → `scripts/05_ner/ner_stage.py`
9. ✅ `scripts/lyrics_detector.py` → `scripts/06_lyrics_detection/lyrics_stage.py`
10. ✅ `scripts/hallucination_removal.py` → `scripts/07_hallucination_removal/hallucination_stage.py`

---

## Stage Conversion Process

### Step-by-Step Conversion Checklist

#### Pre-Conversion
- [ ] Read existing stage code thoroughly
- [ ] Document current inputs and outputs
- [ ] Document current configuration parameters
- [ ] Identify all side effects (file writes, API calls, etc.)
- [ ] Review error handling patterns
- [ ] Check for any hardcoded paths or assumptions

#### Conversion Steps

**1. Add StageIO Initialization**
```python
def run_stage(job_dir: Path, stage_name: str = "XX_stage_name") -> int:
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
```

**2. Replace print() with logger**
```python
# Before
print("Processing file...")
print(f"Error: {e}")

# After
logger.info("Processing file...")
logger.error(f"Error: {e}", exc_info=True)
```

**3. Replace os.getenv() with load_config()**
```python
# Before
import os
max_duration = int(os.getenv("MAX_DURATION", "3600"))

# After
from shared.config_loader import load_config
config = load_config()
max_duration = int(config.get("MAX_DURATION", "3600"))
```

**4. Track Input Files**
```python
# Find input from previous stage
input_file = io.job_dir / "prev_stage_dir" / "output.ext"

# Validate exists
if not input_file.exists():
    raise FileNotFoundError(f"Input not found: {input_file}")

# Track in manifest
io.manifest.add_input(input_file, io.compute_hash(input_file))
```

**5. Write Outputs to io.stage_dir ONLY**
```python
# Before
output_file = Path("/tmp/output.ext")  # ❌ Wrong location

# After
output_file = io.stage_dir / "output.ext"  # ✅ Stage isolation
```

**6. Track Output Files**
```python
# After processing
io.manifest.add_output(output_file, io.compute_hash(output_file))
```

**7. Add Error Handling**
```python
try:
    # Stage processing
    pass
except FileNotFoundError as e:
    logger.error(f"File not found: {e}", exc_info=True)
    io.finalize_stage_manifest(exit_code=1)
    return 1
except Exception as e:
    logger.error(f"Stage failed: {e}", exc_info=True)
    io.finalize_stage_manifest(exit_code=1)
    return 1
```

**8. Finalize Manifest**
```python
# On success
io.finalize_stage_manifest(exit_code=0)
return 0

# On failure (in except blocks)
io.finalize_stage_manifest(exit_code=1)
return 1
```

**9. Update Pipeline Orchestrator**
```python
# Before
from scripts.example_stage import process
result = process(input_path, output_path)

# After
from scripts.example_stage import run_stage
exit_code = run_stage(job_dir, "XX_example")
if exit_code != 0:
    raise StageExecutionError("Example stage failed")
```

**10. Add Unit Tests**
```python
# tests/stages/test_example_stage.py

def test_example_stage_success():
    """Test stage completes successfully"""
    job_dir = create_test_job()
    exit_code = run_stage(job_dir, "example")
    
    assert exit_code == 0
    assert (job_dir / "example" / "output.ext").exists()
    assert (job_dir / "example" / "manifest.json").exists()
    assert (job_dir / "example" / "stage.log").exists()

def test_example_stage_missing_input():
    """Test stage handles missing input"""
    job_dir = create_empty_job()
    exit_code = run_stage(job_dir, "example")
    
    assert exit_code == 1
```

#### Post-Conversion
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Verify manifest contains all inputs/outputs
- [ ] Verify stage.log is created
- [ ] Test error scenarios
- [ ] Update documentation
- [ ] Code review
- [ ] Merge to main

---

## Testing Strategy

### Unit Testing

**Test Coverage Requirements:**
- ✅ Happy path (successful execution)
- ✅ Missing input handling
- ✅ Invalid input handling
- ✅ Manifest creation
- ✅ Log file creation
- ✅ Output file creation
- ✅ Error scenarios

**Example Test Suite:**
```python
# tests/stages/test_example_stage.py

import pytest
from pathlib import Path
from scripts.example_stage import run_stage

def test_example_stage_creates_output():
    """Test stage creates expected output"""
    job_dir = create_test_job_with_input()
    exit_code = run_stage(job_dir, "example")
    
    assert exit_code == 0
    assert (job_dir / "example" / "output.ext").exists()

def test_example_stage_creates_manifest():
    """Test stage creates manifest.json"""
    job_dir = create_test_job_with_input()
    exit_code = run_stage(job_dir, "example")
    
    manifest_path = job_dir / "example" / "manifest.json"
    assert manifest_path.exists()
    
    manifest = load_json(manifest_path)
    assert "inputs" in manifest
    assert "outputs" in manifest
    assert len(manifest["inputs"]) > 0
    assert len(manifest["outputs"]) > 0

def test_example_stage_tracks_inputs():
    """Test stage tracks input files in manifest"""
    job_dir = create_test_job_with_input()
    exit_code = run_stage(job_dir, "example")
    
    manifest = load_manifest(job_dir / "example" / "manifest.json")
    assert any("input.ext" in inp["path"] for inp in manifest["inputs"])

def test_example_stage_creates_stage_log():
    """Test stage creates stage.log"""
    job_dir = create_test_job_with_input()
    exit_code = run_stage(job_dir, "example")
    
    log_path = job_dir / "example" / "stage.log"
    assert log_path.exists()
    
    log_content = log_path.read_text()
    assert "Processing input" in log_content

def test_example_stage_handles_missing_input():
    """Test stage handles missing input file"""
    job_dir = create_empty_job()
    exit_code = run_stage(job_dir, "example")
    
    assert exit_code == 1
    
    log_path = job_dir / "example" / "stage.log"
    log_content = log_path.read_text()
    assert "File not found" in log_content or "not found" in log_content.lower()

def test_example_stage_handles_invalid_config():
    """Test stage handles invalid configuration"""
    job_dir = create_test_job_with_input()
    # Corrupt config somehow
    
    exit_code = run_stage(job_dir, "example")
    assert exit_code == 1
```

### Integration Testing

**Test Complete Workflows:**
```python
# tests/integration/test_pipeline_with_migrated_stages.py

def test_workflow_with_migrated_stages():
    """Test complete workflow with v3.0 stages"""
    job_dir = create_test_job()
    
    # Run each stage
    assert run_stage(job_dir, "01_demux") == 0
    assert run_stage(job_dir, "04_asr") == 0
    assert run_stage(job_dir, "08_translation") == 0
    
    # Verify outputs exist
    assert (job_dir / "01_demux" / "audio.wav").exists()
    assert (job_dir / "04_asr" / "transcript.json").exists()
    assert (job_dir / "08_translation" / "transcript_hi.txt").exists()
    
    # Verify manifests exist
    for stage in ["01_demux", "04_asr", "08_translation"]:
        assert (job_dir / stage / "manifest.json").exists()
        assert (job_dir / stage / "stage.log").exists()
```

---

## Rollback Plan

### Backward Compatibility

**During Migration:**
- Keep existing `process()` functions for compatibility
- Add new `run_stage()` alongside existing code
- Pipeline orchestrator can call either version
- Gradual switchover stage by stage

**Example Dual Support:**
```python
def run_stage(job_dir: Path, stage_name: str = "example") -> int:
    """New v3.0 entry point"""
    # New implementation
    pass

def process(input_path, output_path):
    """Legacy v2.0 entry point - deprecated"""
    # Old implementation - kept for compatibility
    pass
```

### Rollback Procedure

**If migration fails:**

1. **Revert Pipeline Orchestrator**
   - Switch back to calling `process()` instead of `run_stage()`
   
2. **Keep Old Functions**
   - Don't delete old functions until migration is complete
   
3. **Feature Flags**
   - Use configuration to enable/disable v3.0 features
   ```python
   USE_V3_STAGES = config.get("USE_V3_STAGES", "false").lower() == "true"
   
   if USE_V3_STAGES:
       exit_code = run_stage(job_dir, stage_name)
   else:
       process(input_path, output_path)
   ```

---

## Troubleshooting Common Migration Issues

### Issue: Manifest not created

**Symptom:** `manifest.json` file missing after stage execution

**Solution:**
```python
# Ensure enable_manifest=True
io = StageIO(stage_name, job_dir, enable_manifest=True)  # ✅

# Not this
io = StageIO(stage_name, job_dir)  # ❌ Defaults to False
```

### Issue: Output files not found by next stage

**Symptom:** Next stage cannot find previous stage output

**Solution:**
```python
# Write to io.stage_dir
output_file = io.stage_dir / "output.ext"  # ✅

# Not arbitrary paths
output_file = Path("/tmp/output.ext")  # ❌
output_file = job_dir / "output.ext"  # ❌
```

### Issue: Logger not working

**Symptom:** No logs appearing in `stage.log`

**Solution:**
```python
# Get logger from StageIO
logger = io.get_stage_logger()  # ✅

# Not module-level logger
from shared.logger import get_logger
logger = get_logger(__name__)  # ❌ Won't write to stage.log
```

### Issue: Configuration not loading

**Symptom:** `KeyError` or wrong config values

**Solution:**
```python
# Use load_config() with defaults
from shared.config_loader import load_config
config = load_config()
value = config.get("PARAM", "default_value")  # ✅

# Not os.getenv
import os
value = os.getenv("PARAM")  # ❌
```

---

## Resources

### Reference Implementations

- ✅ **Complete Example:** `scripts/tmdb_enrichment_stage.py`
- ✅ **Code Examples:** `docs/CODE_EXAMPLES.md`
- ✅ **Developer Standards:** `docs/developer/DEVELOPER_STANDARDS.md` (§ 3.1)

### Migration Tools

- ✅ **Compliance Validator:** `scripts/validate-compliance.py`
- ✅ **Test Utilities:** `tests/utils/test_helpers.py` (to be created in Phase 2)

### Documentation

- ✅ **Implementation Status:** `docs/IMPLEMENTATION_STATUS.md`
- ✅ **Architecture Roadmap:** `docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md`
- ✅ **Developer Standards:** `docs/developer/DEVELOPER_STANDARDS.md`

---

## Questions & Support

**Q: Can I migrate stages in any order?**  
A: Follow the priority order in Phase 3 and 4. Critical active stages first.

**Q: What if I break something?**  
A: Keep old functions for compatibility. Use feature flags. Test thoroughly.

**Q: How long will migration take?**  
A: Phase 3 (critical stages) takes 4 weeks. Phase 4 (full pipeline) takes 8 weeks.

**Q: Can I use v2.0 and v3.0 stages together?**  
A: Yes! During migration, pipeline supports both patterns.

**Q: What if tests fail?**  
A: Don't merge until all tests pass. Use rollback plan if needed.

---

**Migration Guide Version:** 1.0  
**Last Updated:** 2025-12-03  
**Status:** ✅ Ready for Phase 2
