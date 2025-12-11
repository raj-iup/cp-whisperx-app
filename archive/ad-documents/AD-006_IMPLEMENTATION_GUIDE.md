# AD-006 Implementation Guide

**Document Version:** 1.0  
**Date:** 2025-12-04  
**Status:** MANDATORY - All stages must implement  
**Reference:** ARCHITECTURE_ALIGNMENT_2025-12-04.md (AD-006)

---

## 📋 Overview

**AD-006:** Job-specific parameters override system defaults

**Requirement:** All stages MUST read job.json parameters before using system config defaults.

**Status:** 1 of 13 stages compliant (8%)

---

## ✅ Standard Implementation Pattern

### Template Code

```python
#!/usr/bin/env python3
"""
Stage {NN}_{stage_name}.py: {Description}

Implements AD-006: Job-specific parameter overrides
"""

# Standard library
import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local
from shared.config_loader import load_config
from shared.logger import get_logger
from shared.stage_utils import StageIO

logger = get_logger(__name__)


def run_stage(job_dir: Path, stage_name: str = "{NN}_{stage_name}") -> int:
    """
    Stage {NN}: {Description}
    
    Args:
        job_dir: Job directory path
        stage_name: Stage name for logging/manifest
        
    Returns:
        0 on success, 1 on failure
    """
    # Initialize StageIO
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        logger.info("=" * 60)
        logger.info(f"STAGE {stage_name.upper()}: {Description}")
        logger.info("=" * 60)
        
        # 1. Load system defaults from config
        config = load_config()
        param1 = config.get("STAGE_{NN}_{PARAM1}", "default_value")
        param2 = config.get("STAGE_{NN}_{PARAM2}", "default_value")
        
        # 2. Override with job.json parameters (AD-006)
        job_json_path = job_dir / "job.json"
        if job_json_path.exists():
            logger.info("Reading job-specific parameters from job.json...")
            with open(job_json_path) as f:
                job_data = json.load(f)
                
                # Override param1 if specified
                if 'param1' in job_data and job_data['param1']:
                    old_value = param1
                    param1 = job_data['param1']
                    logger.info(f"  param1 override: {old_value} → {param1} (from job.json)")
                
                # Override param2 if specified
                if 'param2' in job_data and job_data['param2']:
                    old_value = param2
                    param2 = job_data['param2']
                    logger.info(f"  param2 override: {old_value} → {param2} (from job.json)")
        else:
            logger.warning(f"job.json not found at {job_json_path}, using system defaults")
        
        # 3. Log final parameter values
        logger.info(f"Using param1: {param1}")
        logger.info(f"Using param2: {param2}")
        
        # 4. Track configuration in manifest
        io.manifest.set_config({
            "param1": param1,
            "param2": param2
        })
        
        # 5. Stage processing logic here
        logger.info("Processing...")
        
        # 6. Track outputs
        output_file = io.stage_dir / "output.ext"
        io.track_output(output_file, "output_type")
        
        # 7. Finalize
        logger.info("=" * 60)
        logger.info(f"STAGE {stage_name.upper()} COMPLETED")
        logger.info("=" * 60)
        
        io.finalize_stage_manifest(exit_code=0)
        return 0
        
    except Exception as e:
        logger.error(f"Stage failed: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1


def main() -> int:
    """Main entry point"""
    import sys
    if len(sys.argv) < 2:
        print("Usage: {NN}_{stage_name}.py <job_dir>")
        return 1
    
    job_dir = Path(sys.argv[1])
    return run_stage(job_dir)


if __name__ == "__main__":
    sys.exit(main())
```

---

## 🎯 Key Implementation Points

### 1. Load System Defaults First
```python
config = load_config()
param = config.get("PARAM_NAME", "default")
```

### 2. Read job.json
```python
job_json_path = job_dir / "job.json"
if job_json_path.exists():
    with open(job_json_path) as f:
        job_data = json.load(f)
```

### 3. Override with Job Parameters
```python
if 'param_name' in job_data and job_data['param_name']:
    old_value = param
    param = job_data['param_name']
    logger.info(f"  param override: {old_value} → {param} (from job.json)")
```

### 4. Log Parameter Source
```python
logger.info(f"Using param: {param} (from {'job.json' if overridden else 'config'})")
```

---

## 📊 Stage-Specific Implementation Guide

### Stage 01: Demux
**Parameters to Override:**
- media_processing.mode ('full', 'clip', 'time_range')
- media_processing.start_time
- media_processing.end_time

**job.json Fields:**
```json
{
  "media_processing": {
    "mode": "full",
    "start_time": "",
    "end_time": ""
  }
}
```

---

### Stage 02: TMDB Enrichment
**Parameters to Override:**
- tmdb_enrichment.enabled (bool)
- tmdb_enrichment.title (str)
- tmdb_enrichment.year (int or null)

**job.json Fields:**
```json
{
  "tmdb_enrichment": {
    "enabled": false,
    "title": "Movie Title",
    "year": 2023
  }
}
```

**Special Note:** TMDB only enabled for subtitle workflow

---

### Stage 03: Glossary Loader
**Parameters to Override:**
- glossary_file (Path)
- auto_load (bool)

**job.json Fields:**
```json
{
  "glossary": {
    "file": "glossary/custom.json",
    "auto_load": true
  }
}
```

---

### Stage 04: Source Separation
**Parameters to Override:**
- source_separation.enabled (bool)
- source_separation.quality ('quality', 'speed')

**job.json Fields:**
```json
{
  "source_separation": {
    "enabled": true,
    "quality": "quality"
  }
}
```

---

### Stage 05: PyAnnote VAD
**Parameters to Override:**
- vad_enabled (bool)
- vad_threshold (float)

**job.json Fields:**
```json
{
  "vad": {
    "enabled": true,
    "threshold": 0.5
  }
}
```

---

### Stage 06: WhisperX ASR ✅ COMPLIANT
**Status:** Already implemented in whisperx_integration.py

**Parameters Override:**
- source_language (str)
- target_languages (list)
- workflow (str)
- model (str)
- device (str)
- compute_type (str)
- backend (str)

**Reference Implementation:** whisperx_integration.py lines 1415-1433

---

### Stage 07: Alignment
**Parameters to Override:**
- alignment_model (str)
- language (str) - from job.json source_language

**job.json Fields:**
```json
{
  "source_language": "en",
  "alignment": {
    "model": "auto"
  }
}
```

---

### Stage 08: Lyrics Detection
**Parameters to Override:**
- lyrics_detection_enabled (bool)
- threshold (float)

**job.json Fields:**
```json
{
  "lyrics_detection": {
    "enabled": true,
    "threshold": 0.7
  }
}
```

---

### Stage 09: Hallucination Removal
**Parameters to Override:**
- hallucination_removal_enabled (bool)
- confidence_threshold (float)

**job.json Fields:**
```json
{
  "hallucination_removal": {
    "enabled": true,
    "confidence_threshold": 0.5
  }
}
```

---

### Stage 10: Translation
**Parameters to Override:**
- source_language (str)
- target_languages (list)
- translation_model ('indictrans2', 'nllb')

**job.json Fields:**
```json
{
  "source_language": "hi",
  "target_languages": ["en", "es", "fr"],
  "translation": {
    "model": "indictrans2"
  }
}
```

---

### Stage 11: Subtitle Generation
**Parameters to Override:**
- target_languages (list)
- subtitle_format ('vtt', 'srt', 'ass')

**job.json Fields:**
```json
{
  "target_languages": ["en", "hi", "es"],
  "subtitle": {
    "format": "vtt"
  }
}
```

---

### Stage 12: Mux
**Parameters to Override:**
- output_format (str)
- default_subtitle_track (str)

**job.json Fields:**
```json
{
  "mux": {
    "output_format": "mkv",
    "default_subtitle_track": "en"
  }
}
```

---

## ✅ Verification Checklist

For each stage implementation:

- [ ] Loads system defaults from config first
- [ ] Reads job.json if it exists
- [ ] Overrides parameters from job.json
- [ ] Logs parameter source (job.json vs config)
- [ ] Handles missing job.json gracefully
- [ ] Handles missing parameters in job.json
- [ ] Tracks configuration in manifest
- [ ] Has error handling
- [ ] Passes audit: `python3 tools/audit-ad-compliance.py --stage {NN}_{stage}.py`

---

## 🧪 Testing Template

```bash
# 1. Create test job
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s en

# 2. Verify job.json has correct parameters
cat out/*/job.json | python3 -m json.tool | grep -A5 'param_name'

# 3. Run stage
python3 scripts/{NN}_{stage}.py out/*/job_dir/

# 4. Check logs for parameter override messages
grep "override" out/*/logs/*_{stage}_*.log

# 5. Verify correct parameter was used
grep "Using param:" out/*/logs/*_{stage}_*.log
```

---

## 📝 Example: Stage 04 Source Separation

```python
def run_stage(job_dir: Path, stage_name: str = "04_source_separation") -> int:
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        # 1. Load system defaults
        config = load_config()
        enabled = config.get("SOURCE_SEPARATION_ENABLED", "auto") == "true"
        quality = config.get("SOURCE_SEPARATION_QUALITY", "quality")
        
        # 2. Override with job.json
        job_json_path = job_dir / "job.json"
        if job_json_path.exists():
            logger.info("Reading job-specific parameters from job.json...")
            with open(job_json_path) as f:
                job_data = json.load(f)
                
                # Override enabled flag
                if 'source_separation' in job_data:
                    sep_config = job_data['source_separation']
                    
                    if 'enabled' in sep_config and sep_config['enabled'] is not None:
                        old_enabled = enabled
                        enabled = sep_config['enabled']
                        logger.info(f"  enabled override: {old_enabled} → {enabled} (from job.json)")
                    
                    if 'quality' in sep_config and sep_config['quality']:
                        old_quality = quality
                        quality = sep_config['quality']
                        logger.info(f"  quality override: {old_quality} → {quality} (from job.json)")
        
        # 3. Log final values
        logger.info(f"Using enabled: {enabled}")
        logger.info(f"Using quality: {quality}")
        
        # 4. Check if enabled
        if not enabled:
            logger.info("Source separation disabled, skipping")
            io.finalize_stage_manifest(exit_code=0)
            return 0
        
        # 5. Process
        logger.info(f"Running source separation with quality={quality}")
        # ... processing logic ...
        
        io.finalize_stage_manifest(exit_code=0)
        return 0
        
    except Exception as e:
        logger.error(f"Stage failed: {e}", exc_info=True)
        io.finalize_stage_manifest(exit_code=1)
        return 1
```

---

## 🎯 Priority Order

**High Priority (Workflow-Critical):**
1. **Stage 02: TMDB** - Controls workflow routing
2. **Stage 04: Source Separation** - Quality critical
3. **Stage 10: Translation** - Multi-language support

**Medium Priority:**
4. **Stage 01: Demux** - Time range support
5. **Stage 07: Alignment** - Language-specific
6. **Stage 08: Lyrics** - Workflow-specific
7. **Stage 09: Hallucination** - Workflow-specific
8. **Stage 11: Subtitle Gen** - Format/language support

**Lower Priority:**
9. **Stage 03: Glossary** - Auto-load feature
10. **Stage 05: PyAnnote** - Threshold tuning
11. **Stage 12: Mux** - Output format
12. **Stage 11: NER** - Experimental

---

## 📚 References

- **ARCHITECTURE_ALIGNMENT_2025-12-04.md** - AD-006 specification
- **AD-006_IMPLEMENTATION_SUMMARY.md** - Configuration hierarchy
- **whisperx_integration.py** lines 1415-1433 - Reference implementation
- **tools/audit-ad-compliance.py** - Compliance auditing
- **DEVELOPER_STANDARDS.md** § 3.3 - Configuration patterns

---

**Last Updated:** 2025-12-04 15:30 UTC  
**Next Review:** After all stages are compliant
