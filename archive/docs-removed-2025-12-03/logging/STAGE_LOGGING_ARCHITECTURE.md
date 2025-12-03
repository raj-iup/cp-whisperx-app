# Stage Logging & Manifest Architecture

**Version:** 1.0  
**Date:** November 27, 2025  
**Last Updated:** December 3, 2025  
**Status:** ACTIVE - New architectural standard  
**Compliance Status:** 🎊 100% Perfect Compliance  
**Pre-commit Hook:** ✅ Active

---

## 📋 Overview

This document defines the enhanced logging and manifest architecture for the CP-WhisperX pipeline, implementing a dual-logging system with per-stage manifests.

### Key Features

1. **Dual Logging System**
   - Main pipeline log: `logs/99_pipeline_YYYYMMDD_HHMMSS.log`
   - Per-stage logs: `{stage_dir}/stage.log`

2. **Per-Stage Manifests**
   - Input tracking
   - Output tracking
   - Intermediate file tracking
   - Execution metadata

3. **Centralized + Distributed**
   - Central pipeline log for orchestration
   - Stage-specific logs for detailed execution
   - Stage manifests for I/O lineage

---

## 🏗️ Directory Structure

```
out/2025/11/27/baseline/1/
├── logs/
│   ├── 99_pipeline_20251127_065030.log    # Main orchestration log
│   ├── 01_demux_20251127_065031.log       # Legacy: backward compat
│   ├── 02_tmdb_20251127_065032.log
│   └── ...
├── 01_demux/
│   ├── stage.log                           # NEW: Detailed stage log
│   ├── manifest.json                       # NEW: I/O tracking
│   ├── audio.wav                          # Output file
│   └── metadata.json                      # Stage metadata
├── 02_tmdb/
│   ├── stage.log
│   ├── manifest.json
│   ├── tmdb_data.json
│   └── metadata.json
├── 06_asr/
│   ├── stage.log
│   ├── manifest.json
│   ├── segments.json                      # Output
│   ├── transcript.json                    # Output
│   ├── .cache/                           # Intermediate files
│   │   ├── model_download.tmp
│   │   └── vad_output.json
│   └── metadata.json
└── manifest.json                          # Job-level manifest
```

---

## 📝 Logging Specification

### 1. Main Pipeline Log

**Location:** `{job_dir}/logs/99_pipeline_YYYYMMDD_HHMMSS.log`

**Purpose:** 
- Orchestration events
- Stage transitions
- High-level success/failure
- Overall pipeline progress

**Content:**
```
[2025-11-27 13:30:00] [pipeline] [INFO] ═══════════════════════════════════════
[2025-11-27 13:30:00] [pipeline] [INFO] STARTING PIPELINE
[2025-11-27 13:30:00] [pipeline] [INFO] Job: baseline/1
[2025-11-27 13:30:00] [pipeline] [INFO] ═══════════════════════════════════════
[2025-11-27 13:30:01] [pipeline] [INFO] ▶ Stage 1/12: demux
[2025-11-27 13:30:05] [pipeline] [INFO] ✓ Stage demux: SUCCESS (4.2s)
[2025-11-27 13:30:05] [pipeline] [INFO] ▶ Stage 2/12: tmdb
[2025-11-27 13:30:08] [pipeline] [INFO] ✓ Stage tmdb: SUCCESS (3.1s)
...
```

### 2. Stage Log

**Location:** `{job_dir}/{stage_dir}/stage.log`

**Purpose:**
- Detailed stage execution
- Processing steps
- Warnings and recoverable errors
- Debug information

**Content:**
```
[2025-11-27 13:30:01] [demux] [INFO] Starting demux stage
[2025-11-27 13:30:01] [demux] [INFO] Input: media/input.mp4
[2025-11-27 13:30:01] [demux] [INFO] Output: 01_demux/audio.wav
[2025-11-27 13:30:01] [demux] [DEBUG] FFmpeg command: ffmpeg -i ...
[2025-11-27 13:30:02] [demux] [INFO] Extracting audio stream
[2025-11-27 13:30:03] [demux] [INFO] Audio extracted: 48000Hz, 2ch
[2025-11-27 13:30:04] [demux] [INFO] Writing metadata
[2025-11-27 13:30:05] [demux] [INFO] Stage complete
```

---

## 📊 Manifest Specification

### 1. Stage Manifest

**Location:** `{job_dir}/{stage_dir}/manifest.json`

**Schema:**
```json
{
  "stage": "demux",
  "stage_number": 1,
  "timestamp": "2025-11-27T13:30:01Z",
  "duration_seconds": 4.2,
  "status": "success",
  
  "inputs": [
    {
      "type": "media",
      "path": "media/input.mp4",
      "size_bytes": 52428800,
      "checksum": "sha256:abc123..."
    }
  ],
  
  "outputs": [
    {
      "type": "audio",
      "path": "01_demux/audio.wav",
      "size_bytes": 48000000,
      "format": "wav",
      "sample_rate": 48000,
      "channels": 2,
      "duration_seconds": 300.5
    },
    {
      "type": "metadata",
      "path": "01_demux/metadata.json",
      "size_bytes": 1024
    }
  ],
  
  "intermediate_files": [
    {
      "type": "cache",
      "path": "01_demux/.cache/temp_audio.raw",
      "size_bytes": 72000000,
      "retained": false,
      "reason": "Temporary processing buffer"
    }
  ],
  
  "config": {
    "sample_rate": 48000,
    "channels": 2,
    "format": "wav"
  },
  
  "resources": {
    "cpu_percent": 45.2,
    "memory_mb": 512,
    "gpu_used": false
  },
  
  "errors": [],
  "warnings": [
    "Input file is low quality (128kbps)"
  ]
}
```

### 2. Job Manifest

**Location:** `{job_dir}/manifest.json`

**Enhanced Schema:**
```json
{
  "version": "0.2.0",
  "timestamp": "2025-11-27T13:30:00Z",
  "job_id": "baseline/1",
  
  "input": {
    "file": "media/input.mp4",
    "title": "Movie Title",
    "year": 2020,
    "duration_seconds": 300.5
  },
  
  "output": {
    "directory": "out/2025/11/27/baseline/1",
    "files": {
      "transcript": "transcripts/transcript.json",
      "subtitles": "subtitles/output.srt",
      "video": "media/output.mp4"
    }
  },
  
  "pipeline": {
    "status": "running",
    "current_stage": "asr",
    "next_stage": "alignment",
    "completed_stages": ["demux", "tmdb", "glossary_load", "source_separation", "pyannote_vad"],
    "failed_stages": [],
    "skipped_stages": ["export_transcript"]
  },
  
  "stages": {
    "demux": {
      "status": "success",
      "duration_seconds": 4.2,
      "manifest": "01_demux/manifest.json",
      "log": "01_demux/stage.log"
    },
    "asr": {
      "status": "running",
      "started_at": "2025-11-27T13:30:30Z",
      "manifest": "06_asr/manifest.json",
      "log": "06_asr/stage.log"
    }
  },
  
  "timing": {
    "started_at": "2025-11-27T13:30:00Z",
    "total_seconds": 45.8
  },
  
  "devices": {
    "asr": {"requested": "cuda", "actual": "cuda"},
    "alignment": {"requested": "mps", "actual": "mps"}
  }
}
```

---

## 🔧 Implementation

### 1. Enhanced StageIO Class

```python
# shared/stage_utils.py

class StageIO:
    """Enhanced stage I/O with logging and manifest support"""
    
    def __init__(self, stage_name: str, output_base: Optional[Path] = None):
        self.stage_name = stage_name
        self.stage_number = get_stage_number(stage_name)
        self.output_base = Path(output_base or os.environ.get('OUTPUT_DIR', 'out'))
        
        # Stage directory
        stage_dir_name = get_stage_dir(stage_name).split('/')[-1]
        self.stage_dir = self.output_base / stage_dir_name
        self.stage_dir.mkdir(parents=True, exist_ok=True)
        
        # Stage log
        self.stage_log = self.stage_dir / "stage.log"
        
        # Stage manifest
        self.manifest_path = self.stage_dir / "manifest.json"
        self.manifest = StageManifest(stage_name, self.stage_number)
        
        # Logs directory (for backward compat)
        self.logs_dir = self.output_base / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def get_stage_logger(self) -> logging.Logger:
        """Get logger that writes to both main log and stage log"""
        from shared.logger import setup_dual_logger
        return setup_dual_logger(
            self.stage_name,
            stage_log_file=self.stage_log,
            main_log_dir=self.logs_dir
        )
    
    def track_input(self, file_path: Path, file_type: str = "file", **metadata):
        """Track input file in manifest"""
        self.manifest.add_input(file_path, file_type, **metadata)
    
    def track_output(self, file_path: Path, file_type: str = "file", **metadata):
        """Track output file in manifest"""
        self.manifest.add_output(file_path, file_type, **metadata)
    
    def track_intermediate(self, file_path: Path, retained: bool = False, reason: str = ""):
        """Track intermediate/cache file in manifest"""
        self.manifest.add_intermediate(file_path, retained, reason)
    
    def finalize(self, status: str = "success", **kwargs):
        """Finalize stage execution and save manifest"""
        self.manifest.finalize(status, **kwargs)
        self.manifest.save(self.manifest_path)
```

### 2. StageManifest Class

```python
# shared/stage_manifest.py

class StageManifest:
    """Manages per-stage manifest"""
    
    def __init__(self, stage_name: str, stage_number: int):
        self.data = {
            "stage": stage_name,
            "stage_number": stage_number,
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "inputs": [],
            "outputs": [],
            "intermediate_files": [],
            "config": {},
            "resources": {},
            "errors": [],
            "warnings": []
        }
        self.start_time = datetime.now()
    
    def add_input(self, file_path: Path, file_type: str, **metadata):
        """Add input file to manifest"""
        entry = {
            "type": file_type,
            "path": str(file_path),
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            **metadata
        }
        self.data["inputs"].append(entry)
    
    def add_output(self, file_path: Path, file_type: str, **metadata):
        """Add output file to manifest"""
        entry = {
            "type": file_type,
            "path": str(file_path),
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            **metadata
        }
        self.data["outputs"].append(entry)
    
    def add_intermediate(self, file_path: Path, retained: bool, reason: str):
        """Add intermediate file to manifest"""
        entry = {
            "type": "intermediate",
            "path": str(file_path),
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "retained": retained,
            "reason": reason
        }
        self.data["intermediate_files"].append(entry)
    
    def add_warning(self, message: str):
        """Add warning to manifest"""
        self.data["warnings"].append(message)
    
    def add_error(self, message: str):
        """Add error to manifest"""
        self.data["errors"].append(message)
    
    def finalize(self, status: str, **kwargs):
        """Finalize manifest"""
        duration = (datetime.now() - self.start_time).total_seconds()
        self.data.update({
            "duration_seconds": duration,
            "status": status,
            **kwargs
        })
    
    def save(self, path: Path):
        """Save manifest to JSON file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)
```

### 3. Dual Logger Setup

```python
# shared/logger.py (additions)

def setup_dual_logger(
    stage_name: str,
    stage_log_file: Path,
    main_log_dir: Path,
    log_level: str = "INFO"
) -> logging.Logger:
    """
    Setup dual logger that writes to:
    1. Stage-specific log file (detailed)
    2. Main pipeline log (high-level)
    
    Args:
        stage_name: Name of the stage
        stage_log_file: Path to stage.log
        main_log_dir: Directory for main pipeline log
        log_level: Logging level
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(f"stage.{stage_name}")
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers = []
    
    # Formatter for detailed logs
    detailed_formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Formatter for main pipeline log (simplified)
    simple_formatter = logging.Formatter(
        "[%(asctime)s] [pipeline] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handler 1: Stage-specific log (all levels)
    stage_log_file.parent.mkdir(parents=True, exist_ok=True)
    stage_handler = logging.FileHandler(stage_log_file, mode='a', encoding='utf-8')
    stage_handler.setFormatter(detailed_formatter)
    stage_handler.setLevel(logging.DEBUG)  # Capture everything
    logger.addHandler(stage_handler)
    
    # Handler 2: Main pipeline log (INFO and above)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_log_file = main_log_dir / f"99_pipeline_{timestamp}.log"
    main_handler = logging.FileHandler(main_log_file, mode='a', encoding='utf-8')
    main_handler.setFormatter(simple_formatter)
    main_handler.setLevel(logging.INFO)  # Only important messages
    logger.addHandler(main_handler)
    
    # Handler 3: Console (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(detailed_formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    return logger
```

---

## 📚 Usage Examples

### Example 1: Simple Stage

```python
#!/usr/bin/env python3
"""Stage: demux - Extract audio from video"""

from pathlib import Path
from shared.stage_utils import StageIO

def main():
    # Initialize stage I/O
    io = StageIO("demux")
    logger = io.get_stage_logger()
    
    try:
        logger.info("Starting demux stage")
        
        # Track input
        input_file = Path(os.environ['INPUT_FILE'])
        io.track_input(input_file, "media", format="mp4")
        logger.info(f"Input: {input_file}")
        
        # Process
        output_file = io.get_output_path("audio.wav")
        # ... processing logic ...
        
        # Track output
        io.track_output(output_file, "audio", 
                       format="wav", sample_rate=48000, channels=2)
        logger.info(f"Output: {output_file}")
        
        # Finalize
        io.finalize(status="success")
        logger.info("Stage complete")
        
    except Exception as e:
        logger.error(f"Stage failed: {e}")
        io.finalize(status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
```

### Example 2: Stage with Intermediate Files

```python
#!/usr/bin/env python3
"""Stage: asr - Automatic Speech Recognition"""

from pathlib import Path
from shared.stage_utils import StageIO

def main():
    io = StageIO("asr")
    logger = io.get_stage_logger()
    
    try:
        logger.info("Starting ASR stage")
        
        # Track input
        audio_file = io.get_input_path("audio.wav", from_stage="source_separation")
        io.track_input(audio_file, "audio")
        
        # Create cache directory for intermediate files
        cache_dir = io.stage_dir / ".cache"
        cache_dir.mkdir(exist_ok=True)
        
        # Download model (intermediate)
        model_cache = cache_dir / "model.pt"
        logger.debug(f"Downloading model to {model_cache}")
        # ... download logic ...
        io.track_intermediate(model_cache, retained=True, 
                            reason="Model cache for future runs")
        
        # VAD preprocessing (intermediate)
        vad_output = cache_dir / "vad_segments.json"
        logger.debug("Running VAD preprocessing")
        # ... VAD logic ...
        io.track_intermediate(vad_output, retained=False,
                            reason="Temporary VAD output")
        
        # Main transcription
        segments_file = io.get_output_path("segments.json")
        transcript_file = io.get_output_path("transcript.json")
        logger.info("Transcribing audio")
        # ... transcription logic ...
        
        # Track outputs
        io.track_output(segments_file, "transcript", format="segments")
        io.track_output(transcript_file, "transcript", format="whisperx")
        
        # Finalize with resource usage
        io.finalize(status="success", 
                   resources={"gpu_used": True, "memory_mb": 4096})
        logger.info("Stage complete")
        
    except Exception as e:
        logger.error(f"Stage failed: {e}")
        io.manifest.add_error(str(e))
        io.finalize(status="failed")
        raise

if __name__ == "__main__":
    main()
```

---

## 🔄 Migration Path

### Phase 1: Add Stage Logs (Backward Compatible)
- Add `stage.log` to each stage directory
- Keep existing `logs/*.log` files
- Both logs receive same content

### Phase 2: Add Stage Manifests
- Implement `StageManifest` class
- Add `manifest.json` to each stage
- Track inputs/outputs/intermediate files

### Phase 3: Optimize Logging
- Reduce duplication between logs
- Stage log = detailed (DEBUG level)
- Main log = summary (INFO level)

### Phase 4: Deprecate Old Logs (Optional)
- Eventually phase out `logs/NN_stage_*.log`
- Keep only `logs/99_pipeline_*.log` and per-stage logs

---

## 📊 Benefits

### 1. Improved Debugging
- Detailed stage logs for deep investigation
- Main pipeline log for high-level overview
- Clear separation of concerns

### 2. Data Lineage
- Track all inputs consumed by each stage
- Track all outputs produced by each stage
- Track intermediate/cache files
- Enable reproducibility and auditing

### 3. Resource Monitoring
- Per-stage resource usage
- Identify bottlenecks
- Optimize resource allocation

### 4. Resume Capability
- Use manifests to determine resume point
- Verify input files still exist
- Detect incomplete stages

### 5. Compliance & Audit
- Complete I/O trail for compliance
- File checksums for integrity
- Timestamped execution history

---

## 🎯 Compliance Check

This architecture addresses:

✅ **Structured Logging** - Dual-log system with proper separation  
✅ **Data Lineage** - Complete I/O tracking in manifests  
✅ **Standardization** - Consistent pattern across all stages  
✅ **Debugging** - Detailed stage logs for investigation  
✅ **Observability** - Resource usage and timing metrics  
✅ **Auditability** - Complete execution history with checksums  

---

## 📝 Next Steps

1. **Implement Core Classes**
   - [ ] `StageManifest` class in `shared/stage_manifest.py`
   - [ ] `setup_dual_logger()` in `shared/logger.py`
   - [ ] Enhanced `StageIO` with manifest support

2. **Update Stages** (Priority Order)
   - [ ] demux (stage 1)
   - [ ] asr (stage 6) 
   - [ ] alignment (stage 7)
   - [ ] All other stages

3. **Update Documentation**
   - [ ] Add manifest schema to API docs
   - [ ] Update stage development guide
   - [ ] Add troubleshooting guide using logs

4. **Testing**
   - [ ] Test dual logging
   - [ ] Test manifest generation
   - [ ] Verify backward compatibility
   - [ ] Test resume with manifests

---

## Related Documents

### Core Architecture
- **[System Architecture](../technical/architecture.md)** - Overall system design
- **[Pipeline Architecture](../technical/pipeline.md)** - Stage processing flow
- **[Architecture Index](../ARCHITECTURE_INDEX.md)** - Complete documentation index

### Logging Documentation
- **[Logging Architecture](LOGGING_ARCHITECTURE.md)** - Main logging design
- **[Stage Logging Implementation Guide](STAGE_LOGGING_IMPLEMENTATION_GUIDE.md)** - Complete guide
- **[Stage Logging Quick Reference](STAGE_LOGGING_QUICKREF.md)** - Quick lookup

### Development Standards
- **[Developer Standards](../developer/DEVELOPER_STANDARDS.md)** - All development patterns
- **[Code Examples](../CODE_EXAMPLES.md)** - Practical logging examples
- **[StageIO Implementation](../../shared/stage_utils.py)** - Source code

---

**Document Status:** APPROVED - Ready for Implementation  
**Implementation Priority:** HIGH  
**Target Completion:** November 28, 2025  
**Last Updated:** December 3, 2025
