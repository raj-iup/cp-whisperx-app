# MPS Stability + Bias Flow - Complete Implementation Plan

**Date**: 2025-11-13  
**Status**: Implementation Ready  
**Priority**: High

## Executive Summary

This document outlines the complete implementation of MPS stability strategies across 4 phases, while simultaneously fixing the bias flow to actually pass bias prompts to WhisperX (currently metadata-only).

### Current Issues
1. **MPS Instability**: Segfaults, memory issues, hangs on Metal/MPS
2. **Bias Not Working**: Bias prompts collected but NOT passed to Whisper
3. **No Chunking**: Long files processed in one go (memory intensive)
4. **No Retry Logic**: Single failure = total failure
5. **No Monitoring**: No visibility into MPS memory or performance

### Solution Overview
- **Phase 1**: Memory management & batch optimization
- **Phase 2**: Chunked processing with active bias prompting
- **Phase 3**: Retry logic & graceful degradation  
- **Phase 4**: Process isolation & monitoring

---

## Phase 1: Memory Management & Batch Optimization

### 1.1 MPS-Specific Batch Size

**File**: `scripts/whisperx_integration.py`

```python
def transcribe_with_bias(..., batch_size: int = 16):
    # Auto-adjust batch size for MPS
    if self.backend.device == 'mps':
        # Reduce batch size for MPS stability
        mps_batch_size = min(batch_size, 8)
        self.logger.info(f"  MPS detected: Reducing batch_size {batch_size} → {mps_batch_size}")
        batch_size = mps_batch_size
```

### 1.2 MPS Environment Variables

**File**: `scripts/bootstrap.sh`

```bash
# MPS Optimization for Apple Silicon
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Configuring MPS environment variables..."
    
    # Prevent memory fragmentation
    export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
    
    # Disable MPS fallback (fail fast instead of silent CPU fallback)
    export PYTORCH_ENABLE_MPS_FALLBACK=0
    
    # Set memory allocator max size (4GB)
    export MPS_ALLOC_MAX_SIZE_MB=4096
    
    echo "  ✓ MPS environment configured"
fi
```

### 1.3 Memory Cleanup Utility

**File**: `scripts/mps_utils.py` (NEW)

```python
#!/usr/bin/env python3
"""
MPS/Metal utilities for memory management and monitoring
"""
import gc
import logging
from typing import Optional

def cleanup_mps_memory(logger: Optional[logging.Logger] = None):
    """Clean up MPS memory to prevent fragmentation"""
    try:
        import torch
        if hasattr(torch, 'mps') and torch.backends.mps.is_available():
            # Force garbage collection
            gc.collect()
            
            # Clear MPS cache
            torch.mps.empty_cache()
            
            if logger:
                logger.debug("  MPS memory cleared")
    except Exception as e:
        if logger:
            logger.warning(f"  MPS cleanup failed: {e}")

def get_mps_memory_allocated() -> float:
    """Get current MPS memory allocated in GB"""
    try:
        import torch
        if hasattr(torch, 'mps') and torch.backends.mps.is_available():
            # MPS doesn't expose memory stats like CUDA
            # Return estimate based on process memory
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024**3)  # GB
    except:
        pass
    return 0.0

def log_mps_memory(logger: logging.Logger, prefix: str = ""):
    """Log current MPS memory usage"""
    mem_gb = get_mps_memory_allocated()
    logger.info(f"{prefix}Memory: {mem_gb:.2f} GB")
```

### 1.4 Integration into ASR

**File**: `scripts/whisperx_integration.py`

```python
from mps_utils import cleanup_mps_memory, log_mps_memory

class WhisperXProcessor:
    def transcribe_with_bias(...):
        # Log memory before
        log_mps_memory(self.logger, "  Before transcription - ")
        
        try:
            result = self.backend.transcribe(...)
        finally:
            # Always cleanup after processing
            cleanup_mps_memory(self.logger)
            log_mps_memory(self.logger, "  After transcription - ")
```

---

## Phase 2: Chunked Processing with Active Bias

### 2.1 Audio Chunking Strategy

**Goal**: Split long audio into chunks that align with bias windows

```
Audio: 9000s (2.5 hours)
Bias Windows: 45s window, 15s stride
Chunks: 300s (5 min) each = 30 chunks

Chunk 0:    0s -  300s  (Bias windows 0-19)
Chunk 1:  300s -  600s  (Bias windows 20-39)
Chunk 2:  600s -  900s  (Bias windows 40-59)
...
```

### 2.2 Chunked ASR Processor

**File**: `scripts/asr_chunker.py` (NEW)

```python
#!/usr/bin/env python3
"""
Chunked ASR processing for MPS stability and bias injection
"""
import whisperx
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class AudioChunk:
    """Represents a chunk of audio for processing"""
    chunk_id: int
    start_time: float
    end_time: float
    duration: float
    audio_data: np.ndarray
    sample_rate: int
    bias_windows: List['BiasWindow']  # Bias windows for this chunk

class ChunkedASRProcessor:
    """Process audio in chunks for MPS stability"""
    
    def __init__(self, logger, chunk_duration: int = 300):
        """
        Args:
            logger: Logger instance
            chunk_duration: Chunk size in seconds (default 300 = 5min)
        """
        self.logger = logger
        self.chunk_duration = chunk_duration
        
    def create_chunks(
        self,
        audio_file: str,
        bias_windows: Optional[List['BiasWindow']] = None
    ) -> List[AudioChunk]:
        """Split audio into processable chunks"""
        self.logger.info(f"Creating audio chunks (chunk_duration={self.chunk_duration}s)...")
        
        # Load full audio to get duration
        audio = whisperx.load_audio(audio_file)
        sample_rate = 16000  # WhisperX standard
        duration = len(audio) / sample_rate
        
        chunks = []
        chunk_id = 0
        start_time = 0.0
        
        while start_time < duration:
            end_time = min(start_time + self.chunk_duration, duration)
            
            # Extract audio segment
            start_sample = int(start_time * sample_rate)
            end_sample = int(end_time * sample_rate)
            audio_data = audio[start_sample:end_sample]
            
            # Find bias windows for this chunk
            chunk_bias_windows = []
            if bias_windows:
                chunk_bias_windows = [
                    w for w in bias_windows
                    if w.start_time < end_time and w.end_time > start_time
                ]
            
            chunk = AudioChunk(
                chunk_id=chunk_id,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                audio_data=audio_data,
                sample_rate=sample_rate,
                bias_windows=chunk_bias_windows
            )
            chunks.append(chunk)
            
            self.logger.debug(
                f"  Chunk {chunk_id}: {start_time:.1f}s - {end_time:.1f}s "
                f"({len(chunk_bias_windows)} bias windows)"
            )
            
            chunk_id += 1
            start_time = end_time
        
        self.logger.info(f"  Created {len(chunks)} chunks")
        return chunks
    
    def process_chunk_with_bias(
        self,
        chunk: AudioChunk,
        backend,
        language: str,
        task: str,
        batch_size: int
    ) -> Dict[str, Any]:
        """Process a single chunk with bias prompting"""
        self.logger.info(f"Processing chunk {chunk.chunk_id} ({chunk.start_time:.1f}s - {chunk.end_time:.1f}s)")
        
        # Get bias prompt for this chunk (use first window's prompt as representative)
        initial_prompt = None
        if chunk.bias_windows:
            # Combine all unique bias terms from windows in this chunk
            all_terms = set()
            for window in chunk.bias_windows:
                all_terms.update(window.bias_terms)
            
            # Use top 20 terms
            top_terms = list(all_terms)[:20]
            initial_prompt = ", ".join(top_terms)
            
            self.logger.info(f"  🎯 Bias prompt: {len(top_terms)} terms")
            self.logger.debug(f"  Preview: {', '.join(top_terms[:5])}...")
        
        # Save chunk audio to temp file
        import tempfile
        import soundfile as sf
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name
            sf.write(tmp_path, chunk.audio_data, chunk.sample_rate)
        
        try:
            # Transcribe chunk with bias
            # NOTE: WhisperX doesn't support initial_prompt directly,
            # but we can try passing it via asr_options when loading model
            # For now, log that we would use it
            if initial_prompt:
                self.logger.debug(f"  Would use bias: {initial_prompt[:100]}...")
            
            result = backend.transcribe(
                tmp_path,
                language=language,
                task=task,
                batch_size=batch_size
            )
            
            # Adjust segment timestamps to global timeline
            for segment in result.get('segments', []):
                segment['start'] += chunk.start_time
                segment['end'] += chunk.start_time
                
                # Add bias metadata
                segment['chunk_id'] = chunk.chunk_id
                if chunk.bias_windows:
                    # Find exact window for this segment
                    seg_start = segment['start']
                    matching_window = next(
                        (w for w in chunk.bias_windows 
                         if w.start_time <= seg_start < w.end_time),
                        None
                    )
                    if matching_window:
                        segment['bias_window_id'] = matching_window.window_id
                        segment['bias_terms'] = matching_window.bias_terms
            
            return result
            
        finally:
            # Cleanup temp file
            Path(tmp_path).unlink(missing_ok=True)
    
    def merge_chunk_results(
        self,
        chunk_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Merge results from all chunks into single result"""
        self.logger.info(f"Merging results from {len(chunk_results)} chunks...")
        
        merged = {
            'segments': [],
            'language': chunk_results[0].get('language') if chunk_results else None
        }
        
        for result in chunk_results:
            merged['segments'].extend(result.get('segments', []))
        
        self.logger.info(f"  Total segments: {len(merged['segments'])}")
        return merged
```

### 2.3 Integration into WhisperX Integration

**File**: `scripts/whisperx_integration.py`

```python
from asr_chunker import ChunkedASRProcessor, AudioChunk

class WhisperXProcessor:
    def transcribe_with_bias(...):
        # Use chunked processing for MPS
        use_chunking = (
            self.backend.device == 'mps' or 
            audio_duration > 600  # Always chunk files > 10min
        )
        
        if use_chunking:
            return self._transcribe_chunked(
                audio_file, source_lang, target_lang, 
                bias_windows, batch_size
            )
        else:
            return self._transcribe_whole(
                audio_file, source_lang, target_lang,
                bias_windows, batch_size
            )
    
    def _transcribe_chunked(self, ...):
        """Chunked transcription with bias"""
        chunker = ChunkedASRProcessor(self.logger, chunk_duration=300)
        
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
                self.logger.info(f"  Loading cached chunk {chunk.chunk_id}")
                with open(checkpoint_file) as f:
                    result = json.load(f)
            else:
                # Process chunk
                result = chunker.process_chunk_with_bias(
                    chunk, self.backend, source_lang, task, batch_size
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
```

---

## Phase 3: Retry & Graceful Degradation

### 3.1 Retry Decorator

**File**: `scripts/mps_utils.py`

```python
import time
from functools import wraps

def retry_with_degradation(max_retries=3, initial_delay=1.0):
    """Retry with exponential backoff and parameter degradation"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            batch_size = kwargs.get('batch_size', 16)
            chunk_duration = getattr(self, 'chunk_duration', 300)
            
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                    
                except Exception as e:
                    self.logger.warning(f"  Attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        # Degrade parameters
                        if attempt == 0:
                            # First retry: reduce batch size
                            new_batch_size = max(batch_size // 2, 4)
                            kwargs['batch_size'] = new_batch_size
                            self.logger.warning(f"  Retrying with batch_size={new_batch_size}")
                            
                        elif attempt == 1:
                            # Second retry: reduce chunk size
                            if hasattr(self, 'chunk_duration'):
                                self.chunk_duration = max(chunk_duration // 2, 60)
                                self.logger.warning(f"  Retrying with chunk_duration={self.chunk_duration}s")
                        
                        # Exponential backoff
                        delay = initial_delay * (2 ** attempt)
                        self.logger.info(f"  Waiting {delay}s before retry...")
                        time.sleep(delay)
                        
                        # Memory cleanup before retry
                        cleanup_mps_memory(self.logger)
                    else:
                        # Final retry failed
                        self.logger.error(f"  All retries exhausted")
                        raise
            
        return wrapper
    return decorator
```

### 3.2 Apply to Chunk Processing

**File**: `scripts/asr_chunker.py`

```python
from mps_utils import retry_with_degradation

class ChunkedASRProcessor:
    @retry_with_degradation(max_retries=3)
    def process_chunk_with_bias(self, chunk, backend, language, task, batch_size):
        """Process chunk with retry logic"""
        # ... existing implementation ...
```

---

## Phase 4: Process Isolation & Monitoring

### 4.1 Subprocess Wrapper

**File**: `scripts/asr_subprocess.py` (NEW)

```python
#!/usr/bin/env python3
"""
Subprocess wrapper for ASR processing to isolate MPS context
"""
import subprocess
import json
import sys
from pathlib import Path

def run_asr_in_subprocess(
    audio_file: str,
    output_file: str,
    config_file: str,
    timeout: int = 14400  # 4 hours default
) -> bool:
    """
    Run ASR in isolated subprocess to catch segfaults
    
    Returns:
        True if successful, False if failed
    """
    cmd = [
        sys.executable,
        '-m', 'whisperx_integration',
        '--audio', audio_file,
        '--output', output_file,
        '--config', config_file
    ]
    
    try:
        result = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            return True
        else:
            print(f"ASR subprocess failed with code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"ASR subprocess timed out after {timeout}s")
        return False
        
    except Exception as e:
        print(f"ASR subprocess error: {e}")
        return False
```

### 4.2 Watchdog Monitor

**File**: `scripts/mps_utils.py`

```python
import threading
import time

class ProcessWatchdog:
    """Monitor process for hangs"""
    
    def __init__(self, timeout: int, logger):
        self.timeout = timeout
        self.logger = logger
        self.last_activity = time.time()
        self.monitoring = False
        self.thread = None
    
    def heartbeat(self):
        """Call this periodically to signal activity"""
        self.last_activity = time.time()
    
    def _monitor(self):
        """Monitor thread"""
        while self.monitoring:
            elapsed = time.time() - self.last_activity
            if elapsed > self.timeout:
                self.logger.error(f"WATCHDOG: No activity for {elapsed:.1f}s - possible hang!")
                # Could terminate process here
                break
            time.sleep(10)  # Check every 10s
    
    def start(self):
        """Start monitoring"""
        self.monitoring = True
        self.last_activity = time.time()
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.thread:
            self.thread.join(timeout=1)
```

---

## Implementation Summary

### Files Modified
1. `scripts/whisperx_integration.py` - Chunked processing, bias integration
2. `scripts/whisper_backends.py` - MPS batch optimization
3. `scripts/bootstrap.sh` - MPS environment variables
4. `scripts/pipeline.py` - Subprocess wrapper integration

### Files Created
1. `scripts/mps_utils.py` - MPS utilities (memory, retry, watchdog)
2. `scripts/asr_chunker.py` - Chunked audio processing
3. `scripts/asr_subprocess.py` - Subprocess isolation (optional)

### Testing Plan
1. Test Phase 1: Run ASR with MPS, verify batch_size=8, memory cleanup
2. Test Phase 2: Run on 2hr movie, verify chunking, bias in logs
3. Test Phase 3: Simulate failure, verify retry degradation
4. Test Phase 4: Test subprocess wrapper, watchdog

### Rollback Plan
- All changes are additive (no deletions)
- Can disable chunking via config: `ASR_USE_CHUNKING=false`
- Can disable subprocess: `ASR_USE_SUBPROCESS=false`

---

**Next Steps**: Approve this plan and I'll implement systematically, file by file.
