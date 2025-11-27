# Comprehensive Pipeline Fixes Summary

## Issues Identified and Fixed

### 1. ✅ Bootstrap Integration
**Status:** ALREADY COMPLETE
- cache-models.sh is integrated into scripts/bootstrap.sh
- Flags available: --cache-models, --skip-cache
- Works as expected

### 2. ✅ MLX Whisper Model Loading  
**Status:** ALREADY FIXED IN cache-models.sh
- Line 313: Uses correct `mlx_whisper.load_model()` API
- The error mentioned was from an old version

### 3. ❌ Config Class Ambiguity (CRITICAL)
**Issue:** lyrics_detection_pipeline.py calls `Config(PROJECT_ROOT)` expecting 1 argument, but there are TWO Config classes in shared/config.py:
- Line 287: `Config.__init__(self, project_root: Path)` - Simple config loader
- Line 241: `class Config` inside `PipelineConfig` - Pydantic settings

**Fix:** lyrics_detection_pipeline.py needs to use the correct Config class (line 287)

### 4. ❌ LLM Environment Missing Dependencies
**Issue:** hybrid_translator.py fails with missing modules:
- pythonjsonlogger
- pydantic_settings

**Status:** Both ARE installed in venv/llm, but the error suggests import issues

**Fix:** Verify requirements-llm.txt is properly installed

### 5. ❌ Pipeline Stage Order - Lyrics Detection
**Issue:** lyrics_detection runs BEFORE asr stage, but needs segments.json from ASR output

**Current order** (from logs):
1. demux
2. source_separation  
3. lyrics_detection ← TOO EARLY!
4. pyannote_vad
5. asr
6. alignment
7. translation

**Correct order**:
1. demux
2. source_separation
3. pyannote_vad
4. asr
5. alignment
6. lyrics_detection ← AFTER ASR
7. translation

### 6. ❌ Pipeline Stage Input/Output Paths
**Issue:** Each stage should:
- Log input path at start
- Read from previous stage's output directory
- Write to its own numbered directory (e.g., 01_demux, 02_source_separation)

**Current structure:** ✅ Already correct in out/2025/11/24/1/1/

### 7. ❌ Output Directory Structure with USER_ID
**Issue:** Still seeing 'rpatel' instead of user_id "1"

**Expected:** `out/2025/11/24/1/1/`
**Actual:** `out/2025/11/24/rpatel/1/`

**Fix:** prepare-job.sh should use USER_ID parameter correctly

### 8. ❌ Mux Stage Media Subdirectory
**Issue:** After mux completes, create `media/[MediaName]/` subdirectory

**Expected structure:**
```
out/2025/11/24/1/1/
├── 09_mux/
│   └── Movie_subtitled.mp4
└── media/
    └── Movie/           ← Create this
        └── Movie_subtitled.mp4
```

### 9. ❓ Duplicate Audio Files
**Question:** Are these identical?
- out/2025/11/24/1/3/01_demux/audio.wav
- out/2025/11/24/1/3/02_source_separation/audio.wav

**Answer:** They SHOULD BE DIFFERENT:
- 01_demux/audio.wav = Original full audio
- 02_source_separation/audio.wav = Separated vocals only

### 10. ❌ Cache Verification in Pipeline Logs
**Issue:** Pipeline should log when using cached models

**Expected log:**
```
[INFO] Loading WhisperX model from cache: .cache/huggingface/...
[INFO] ✓ Model loaded from cache (skip download)
```

## Files That Need Changes

1. **scripts/run-pipeline.py** - Fix stage order, add input/output logging
2. **scripts/lyrics_detection_pipeline.py** - Fix Config import
3. **prepare-job.sh** - Fix USER_ID usage
4. **scripts/mux.py** - Add media subdirectory creation
5. **scripts/*.py** (all stage scripts) - Add cache usage logging
6. **venv/llm** - Verify/reinstall dependencies

## Implementation Priority

1. HIGH: Fix Config class ambiguity (breaks lyrics_detection)
2. HIGH: Fix LLM dependencies (breaks translation)
3. HIGH: Fix lyrics_detection stage order (wrong execution order)
4. MEDIUM: Fix USER_ID in output paths
5. MEDIUM: Add mux media subdirectory
6. LOW: Add cache logging
7. LOW: Verify audio file differences
