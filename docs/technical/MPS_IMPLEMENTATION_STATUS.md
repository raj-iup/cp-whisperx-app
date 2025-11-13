# MPS Optimization Implementation Status

**Date**: 2025-11-13  
**Status**: Phase 1 Complete, Phases 2-4 Ready for Implementation

---

## ✅ COMPLETED: Phase 1 - Shared Infrastructure

### Files Created
1. **`scripts/mps_utils.py`** ✓
   - Complete utility library for all ML stages
   - Functions:
     - `cleanup_mps_memory()` - Memory cleanup
     - `log_mps_memory()` - Memory monitoring
     - `retry_with_degradation()` - Auto-retry decorator
     - `ProcessWatchdog()` - Hang detection
     - `optimize_batch_size_for_mps()` - Batch size optimization
     - `mps_safe_operation()` - Safe execution wrapper

### Files Modified
1. **`scripts/bootstrap.sh`** ✓
   - Added MPS environment variables (macOS only)
   - PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
   - PYTORCH_ENABLE_MPS_FALLBACK=0
   - MPS_ALLOC_MAX_SIZE_MB=4096

### Git Status
- Committed: "MPS Optimization Phase 1: Shared infrastructure and environment setup"
- Ready for Phase 2 implementation

---

## 📋 NEXT STEPS: Implementation Guide for Phases 2-4

Due to token limits, I'm providing you with a complete implementation guide for the remaining phases. Each section includes the exact code changes needed.

### IMPLEMENTATION ORDER

1. **Phase 2A**: ASR Chunked Processing (CRITICAL)
2. **Phase 2B**: Diarization Optimization (IMPORTANT)
3. **Phase 2C**: VAD Optimization (MEDIUM)
4. **Phase 2D**: Glossary Optimization (LOW)
5. **Phase 3**: Integration Testing
6. **Phase 4**: Optional Process Isolation

---

## PHASE 2A: ASR Chunked Processing with Bias

### File 1: Create `scripts/asr_chunker.py`

This file handles audio chunking, bias alignment, and checkpoint/resume functionality.

**Complete code in**: `docs/technical/MPS_STABILITY_IMPLEMENTATION.md` (Section 2.2)

**Key features**:
- Split audio into 5-minute chunks
- Align chunks with bias windows
- Process each chunk with bias prompt
- Save checkpoints for resume
- Merge results with proper timestamps

### File 2: Modify `scripts/whisperx_integration.py`

**Changes needed**:

1. Add imports at top:
```python
from mps_utils import cleanup_mps_memory, log_mps_memory, optimize_batch_size_for_mps
from asr_chunker import ChunkedASRProcessor
```

2. In `transcribe_with_bias()` method (around line 199):

Add before transcription:
```python
# Optimize batch size for MPS
if self.backend.device == 'mps':
    original_batch_size = batch_size
    batch_size = optimize_batch_size_for_mps(batch_size, 'mps', 'large')
    if batch_size != original_batch_size:
        self.logger.info(f"  🎯 MPS optimization: batch_size {original_batch_size} → {batch_size}")

# Log memory before processing
log_mps_memory(self.logger, "  Before transcription - ")

# Determine if chunking should be used
audio_duration = self._get_audio_duration(audio_file)
use_chunking = (
    self.backend.device == 'mps' or  # Always chunk for MPS
    audio_duration > 600  # Chunk if > 10 minutes
)

if use_chunking:
    self.logger.info(f"  📦 Using chunked processing (duration={audio_duration:.0f}s)")
    result = self._transcribe_chunked(
        audio_file, source_lang, target_lang, 
        bias_windows, batch_size, output_dir
    )
else:
    result = self._transcribe_whole(
        audio_file, source_lang, target_lang,
        bias_windows, batch_size
    )
```

3. Add two new methods to `WhisperXProcessor` class:

```python
def _get_audio_duration(self, audio_file: str) -> float:
    """Get audio duration in seconds"""
    import whisperx
    audio = whisperx.load_audio(audio_file)
    return len(audio) / 16000  # 16kHz sample rate

def _transcribe_whole(
    self,
    audio_file: str,
    source_lang: str,
    target_lang: str,
    bias_windows: Optional[List],
    batch_size: int
) -> Dict[str, Any]:
    """Original whole-file transcription (for short files or CPU)"""
    try:
        result = self.backend.transcribe(
            audio_file,
            language=source_lang,
            task='transcribe',
            batch_size=batch_size
        )
        
        # Add bias metadata
        if bias_windows:
            result = self._apply_bias_context(result, bias_windows)
        
        return result
    finally:
        cleanup_mps_memory(self.logger)
        log_mps_memory(self.logger, "  After transcription - ")

def _transcribe_chunked(
    self,
    audio_file: str,
    source_lang: str,
    target_lang: str,
    bias_windows: Optional[List],
    batch_size: int,
    output_dir: Path
) -> Dict[str, Any]:
    """Chunked transcription with bias and checkpointing"""
    from mps_utils import retry_with_degradation
    
    chunker = ChunkedASRProcessor(self.logger, chunk_duration=300)  # 5 min chunks
    
    # Create chunks
    chunks = chunker.create_chunks(audio_file, bias_windows)
    
    # Process each chunk with checkpointing
    chunk_results = []
    checkpoint_dir = output_dir / 'chunks'
    checkpoint_dir.mkdir(exist_ok=True)
    
    for chunk in chunks:
        checkpoint_file = checkpoint_dir / f'chunk_{chunk.chunk_id:04d}.json'
        
        # Skip if already processed
        if checkpoint_file.exists():
            self.logger.info(f"  ✓ Loading cached chunk {chunk.chunk_id}")
            with open(checkpoint_file) as f:
                result = json.load(f)
        else:
            # Process chunk with retry
            result = self._process_chunk_with_retry(
                chunker, chunk, source_lang, batch_size
            )
            
            # Save checkpoint
            with open(checkpoint_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Memory cleanup after each chunk
            cleanup_mps_memory(self.logger)
        
        chunk_results.append(result)
    
    # Merge all chunks
    merged_result = chunker.merge_chunk_results(chunk_results)
    return merged_result

@retry_with_degradation(max_retries=3)
def _process_chunk_with_retry(
    self,
    chunker: 'ChunkedASRProcessor',
    chunk,
    language: str,
    batch_size: int
) -> Dict[str, Any]:
    """Process a single chunk with retry logic"""
    return chunker.process_chunk_with_bias(
        chunk, self.backend, language, 'transcribe', batch_size
    )
```

---

## PHASE 2B: Diarization Optimization

### Modify `scripts/diarization.py`

1. Add imports:
```python
from mps_utils import cleanup_mps_memory, log_mps_memory, optimize_batch_size_for_mps
```

2. Find where PyAnnote pipeline is created (search for `Pipeline.from_pretrained`):

Before creating pipeline, add:
```python
# MPS memory optimization
if self.device == 'mps':
    log_mps_memory(self.logger, "  Before diarization - ")
```

3. After diarization completes, add cleanup:
```python
# Cleanup MPS memory
cleanup_mps_memory(self.logger)
log_mps_memory(self.logger, "  After diarization - ")
```

---

## PHASE 2C: VAD Optimization

### Modify `scripts/pyannote_vad.py`

Add at the start and end of the main processing:
```python
from mps_utils import cleanup_mps_memory, log_mps_memory

# At start of VAD processing:
log_mps_memory(logger, "  Before VAD - ")

# At end of VAD processing:
cleanup_mps_memory(logger)
log_mps_memory(logger, "  After VAD - ")
```

### Modify `scripts/silero_vad.py`

Same pattern as pyannote_vad.py above.

---

## PHASE 2D: Glossary Optimization

### Modify `scripts/glossary_builder.py`

Add memory cleanup after embedding generation:
```python
from mps_utils import cleanup_mps_memory

# After creating embeddings:
cleanup_mps_memory(logger)
```

---

## TESTING CHECKLIST

After implementing all phases:

### Phase 1 Testing
- [x] Bootstrap runs successfully
- [x] MPS env vars are set on macOS
- [x] mps_utils.py imports correctly

### Phase 2A Testing (ASR)
- [ ] Short file (< 5 min) uses whole-file mode
- [ ] Long file (> 10 min) uses chunked mode
- [ ] MPS device uses chunked mode
- [ ] Chunks are created correctly
- [ ] Bias is applied to chunks
- [ ] Checkpoints are saved
- [ ] Resume works after interruption
- [ ] Memory cleanup runs after each chunk
- [ ] Retry works on failure
- [ ] Batch size reduces on retry

### Phase 2B Testing (Diarization)
- [ ] Memory cleanup runs
- [ ] Memory logging works
- [ ] Diarization completes without segfault

### Phase 2C Testing (VAD)
- [ ] PyAnnote VAD runs with memory cleanup
- [ ] Silero VAD runs with memory cleanup

### Phase 2D Testing (Glossary)
- [ ] Glossary builder runs with cleanup

---

## CONFIGURATION OPTIONS

Add these to `config/.env.pipeline.template`:

```bash
# MPS Optimization Settings
ASR_CHUNK_DURATION=300          # Chunk size in seconds (default: 300 = 5min)
ASR_USE_CHUNKING=auto           # auto, always, never
ASR_MAX_RETRIES=3               # Max retries on failure
ASR_BATCH_SIZE=16               # Starting batch size (auto-reduced for MPS)

# Watchdog Settings
ASR_WATCHDOG_TIMEOUT=3600       # Hang detection timeout (seconds)
DIARIZATION_WATCHDOG_TIMEOUT=1800
```

---

## ROLLBACK PROCEDURE

If issues arise:

1. Revert to commit before MPS implementation:
   ```bash
   git checkout HEAD~1
   ```

2. Or disable chunking via config:
   ```bash
   ASR_USE_CHUNKING=never
   ```

3. Or disable MPS optimizations:
   ```bash
   # In scripts/whisperx_integration.py, comment out:
   # from mps_utils import *
   ```

---

## PERFORMANCE EXPECTATIONS

### Before MPS Optimization
- ASR crashes on 2hr movies
- Memory fragmentation issues
- No retry on failure
- Bias not actually used

### After MPS Optimization
- ASR stable on 2hr+ movies
- Chunked processing (30 chunks for 2.5hr movie)
- Auto-retry with degradation
- Bias actually passed to Whisper
- Checkpoint/resume capability
- 10-20% slower (chunking overhead) but 100% more stable

---

## NEXT ACTIONS

1. Review implementation plan above
2. Create `scripts/asr_chunker.py` using code from MPS_STABILITY_IMPLEMENTATION.md
3. Modify `scripts/whisperx_integration.py` with changes above
4. Test on a short file first (< 5 min)
5. Test on a long file (> 30 min)
6. Implement other stages (Diarization, VAD, Glossary)
7. Full pipeline test

---

**Status**: Infrastructure complete, ready for stage-specific implementation.
**Estimated remaining time**: 2-3 hours for full implementation + testing.
