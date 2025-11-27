# Bias Prompt Implementation Strategy

## Overview
This document outlines the best strategy to implement **active bias prompting** in the ASR stage, moving from the current metadata-only approach to actually influencing Whisper's transcription.

## Current State

### What We Have
✅ Bias terms collected from TMDB (cast/crew names)  
✅ Bias terms collected from Pre-NER (entities)  
✅ Rolling windows created (45s size, 15s stride)  
✅ Bias windows saved to files  
✅ Bias metadata added to segments  

### What's Missing
❌ Bias prompts NOT passed to Whisper during transcription  
❌ No influence on actual recognition accuracy  
❌ Only used as post-processing metadata  

## Discovery: faster-whisper Supports Bias!

The underlying `faster-whisper` library (used by WhisperX) **already supports** bias prompting through these parameters:

```python
WhisperModel.transcribe(
    audio,
    initial_prompt: str = None,     # ← Text prompt to guide recognition
    hotwords: str = None,           # ← Comma-separated important words
    condition_on_previous_text: bool = True  # Use previous segment as context
)
```

### Key Parameters

| Parameter | Type | Purpose | Example |
|-----------|------|---------|---------|
| `initial_prompt` | `str` | Text prefix to guide Whisper | "Shah Rukh Khan, Kajol, Simran" |
| `hotwords` | `str` | Comma-separated terms to boost | "Shah Rukh Khan,Kajol,Amrish Puri" |
| `condition_on_previous_text` | `bool` | Use previous segment as context | `True` |

## Recommended Strategy: Hybrid Approach

### Strategy 1: Global Initial Prompt (Simplest - RECOMMENDED)

Use a **single global prompt** with all top terms for the entire transcription.

#### Implementation

**File**: `scripts/whisper_backends.py`  
**Method**: `WhisperXBackend.transcribe()`

```python
def transcribe(
    self,
    audio_file: str,
    language: Optional[str] = None,
    task: str = "transcribe",
    batch_size: int = 16,
    initial_prompt: Optional[str] = None,  # ADD THIS
    hotwords: Optional[str] = None         # ADD THIS
) -> Dict[str, Any]:
    """Transcribe using WhisperX with bias prompts"""
    import whisperx
    
    if not self.model:
        raise RuntimeError("Model not loaded")
    
    audio = whisperx.load_audio(audio_file)
    
    # Pass bias prompts to model
    result = self.model.transcribe(
        audio,
        language=language,
        task=task,
        batch_size=batch_size,
        initial_prompt=initial_prompt,     # ADD THIS
        hotwords=hotwords                  # ADD THIS
    )
    
    return result
```

**File**: `scripts/whisperx_integration.py`  
**Method**: `transcribe_with_bias()`

```python
def transcribe_with_bias(
    self,
    audio_file: str,
    source_lang: str,
    target_lang: str,
    bias_windows: Optional[List[BiasWindow]] = None,
    batch_size: int = 16
) -> Dict[str, Any]:
    # Create global bias prompt from all unique terms
    initial_prompt = None
    hotwords = None
    
    if bias_windows:
        # Collect all unique bias terms across windows
        all_terms = set()
        for window in bias_windows:
            all_terms.update(window.bias_terms)
        
        # Create comma-separated list (limit to top 50 terms)
        top_terms = list(all_terms)[:50]
        initial_prompt = ", ".join(top_terms[:20])  # First 20 as context
        hotwords = ",".join(top_terms)              # All 50 as hotwords
        
        self.logger.info(f"  Using {len(top_terms)} bias terms")
    
    # Transcribe with bias
    result = self.backend.transcribe(
        audio_file,
        language=source_lang,
        task=task,
        batch_size=batch_size,
        initial_prompt=initial_prompt,  # Pass bias here
        hotwords=hotwords               # Pass hotwords here
    )
    
    # Still add bias metadata for reference
    if bias_windows:
        result = self._apply_bias_context(result, bias_windows)
    
    return result
```

#### Pros
✅ **Simplest implementation** - minimal code changes  
✅ **No chunking required** - single transcription pass  
✅ **Fast** - no overhead from processing chunks  
✅ **Works with WhisperX batching** - maintains performance  
✅ **Maintains alignment** - word-level timestamps still work  

#### Cons
❌ Not time-aware - same terms for entire audio  
❌ May dilute focus with too many terms  
❌ Can't adapt to scene changes  

#### Best For
- Movies/shows with consistent cast throughout
- Limited set of important names (< 50 terms)
- When speed is priority

---

### Strategy 2: Chunked Window Processing (Most Accurate)

Process audio in **chunks matching bias windows**, using different prompts per chunk.

#### Implementation

**File**: `scripts/whisperx_integration.py`

```python
def transcribe_with_bias_chunked(
    self,
    audio_file: str,
    source_lang: str,
    target_lang: str,
    bias_windows: Optional[List[BiasWindow]] = None,
    batch_size: int = 16
) -> Dict[str, Any]:
    """Transcribe audio in chunks with window-specific bias prompts"""
    import whisperx
    import soundfile as sf
    import numpy as np
    
    if not bias_windows:
        # Fall back to regular transcription
        return self.backend.transcribe(
            audio_file, language=source_lang, task=task, batch_size=batch_size
        )
    
    # Load full audio
    audio, sr = sf.read(audio_file)
    
    # Transcribe each bias window
    all_segments = []
    for window in bias_windows:
        # Extract audio chunk for this window
        start_sample = int(window.start_time * sr)
        end_sample = int(window.end_time * sr)
        chunk_audio = audio[start_sample:end_sample]
        
        # Transcribe chunk with window-specific bias
        chunk_result = self.backend.transcribe(
            chunk_audio,  # NumPy array supported
            language=source_lang,
            task=task,
            batch_size=batch_size,
            initial_prompt=window.bias_prompt,
            hotwords=",".join(window.bias_terms)
        )
        
        # Adjust timestamps to global timeline
        for segment in chunk_result.get('segments', []):
            segment['start'] += window.start_time
            segment['end'] += window.start_time
            # Add bias metadata
            segment['bias_window_id'] = window.window_id
            segment['bias_terms'] = window.bias_terms
            
        all_segments.extend(chunk_result.get('segments', []))
    
    # Merge overlapping segments from adjacent windows
    merged_segments = self._merge_overlapping_segments(all_segments)
    
    return {
        "segments": merged_segments,
        "language": source_lang
    }

def _merge_overlapping_segments(self, segments: List[Dict]) -> List[Dict]:
    """Merge duplicate segments from overlapping windows"""
    # Sort by start time
    sorted_segments = sorted(segments, key=lambda s: s['start'])
    
    merged = []
    for segment in sorted_segments:
        # Skip if already covered by previous segment
        if merged and segment['start'] < merged[-1]['end']:
            # Choose segment with higher confidence or better match
            continue
        merged.append(segment)
    
    return merged
```

#### Pros
✅ **Time-aware** - different terms for different scenes  
✅ **Focused** - only 10 terms per window (better than 50 global)  
✅ **Adapts** - can change terms as movie progresses  
✅ **Flexible** - can adjust window size per content  

#### Cons
❌ More complex - requires chunk processing  
❌ Slower - multiple transcription passes  
❌ May lose context at boundaries  
❌ Requires segment merging logic  

#### Best For
- Long content with scene changes
- When accuracy is more important than speed
- Content with many characters appearing at different times

---

### Strategy 3: Hybrid Global + Context (BEST BALANCE)

Combine global hotwords with dynamic initial_prompt per segment.

#### Implementation

```python
def transcribe_with_bias_hybrid(
    self,
    audio_file: str,
    source_lang: str,
    target_lang: str,
    bias_windows: Optional[List[BiasWindow]] = None,
    batch_size: int = 16
) -> Dict[str, Any]:
    """Use global hotwords + update initial_prompt periodically"""
    
    if not bias_windows:
        return self.backend.transcribe(
            audio_file, language=source_lang, task=task, batch_size=batch_size
        )
    
    # Create global hotwords from all terms
    all_terms = set()
    for window in bias_windows:
        all_terms.update(window.bias_terms)
    hotwords = ",".join(list(all_terms)[:50])
    
    # Use first window's terms as initial prompt
    initial_prompt = bias_windows[0].bias_prompt if bias_windows else None
    
    # Transcribe with global bias
    result = self.backend.transcribe(
        audio_file,
        language=source_lang,
        task=task,
        batch_size=batch_size,
        initial_prompt=initial_prompt,
        hotwords=hotwords,
        condition_on_previous_text=True  # Let Whisper use context
    )
    
    # Add window-specific metadata post-processing
    if bias_windows:
        result = self._apply_bias_context(result, bias_windows)
    
    return result
```

#### Pros
✅ **Simple** - single transcription pass  
✅ **Fast** - no chunking overhead  
✅ **Comprehensive** - uses all terms as hotwords  
✅ **Context-aware** - Whisper's own context mechanism  

#### Cons
❌ Initial prompt static (only first window)  
❌ Less adaptive than full chunking  

#### Best For
- Most use cases - good balance of speed and accuracy
- When you want comprehensive coverage without complexity

---

## Comparison Matrix

| Strategy | Complexity | Speed | Accuracy | Time-Aware | Recommended For |
|----------|-----------|-------|----------|------------|-----------------|
| **Global Prompt** | ⭐ Low | ⭐⭐⭐ Fast | ⭐⭐ Good | ❌ No | Quick wins, consistent cast |
| **Chunked Windows** | ⭐⭐⭐ High | ⭐ Slow | ⭐⭐⭐ Best | ✅ Yes | Maximum accuracy, research |
| **Hybrid** | ⭐⭐ Medium | ⭐⭐⭐ Fast | ⭐⭐⭐ Best | ⚠️ Partial | **RECOMMENDED** |

## Implementation Plan

### Phase 1: Quick Win (Strategy 1 - Global Prompt)

**Estimated Time**: 2-3 hours  
**Files to Modify**: 2  
**Risk**: Low

1. Update `WhisperXBackend.transcribe()` to accept `initial_prompt` and `hotwords`
2. Update `transcribe_with_bias()` to create global prompt from all terms
3. Test on sample video
4. Measure improvement in name recognition

**Code Changes**:
```diff
# scripts/whisper_backends.py
  def transcribe(
      self,
      audio_file: str,
      language: Optional[str] = None,
      task: str = "transcribe",
-     batch_size: int = 16
+     batch_size: int = 16,
+     initial_prompt: Optional[str] = None,
+     hotwords: Optional[str] = None
  ) -> Dict[str, Any]:
      result = self.model.transcribe(
          audio,
          language=language,
          task=task,
-         batch_size=batch_size
+         batch_size=batch_size,
+         initial_prompt=initial_prompt,
+         hotwords=hotwords
      )
```

```diff
# scripts/whisperx_integration.py
  def transcribe_with_bias(...):
+     # Create global bias prompt
+     initial_prompt = None
+     hotwords = None
+     if bias_windows:
+         all_terms = set()
+         for window in bias_windows:
+             all_terms.update(window.bias_terms)
+         top_terms = list(all_terms)[:50]
+         initial_prompt = ", ".join(top_terms[:20])
+         hotwords = ",".join(top_terms)
      
      result = self.backend.transcribe(
          audio_file,
          language=source_lang,
          task=task,
-         batch_size=batch_size
+         batch_size=batch_size,
+         initial_prompt=initial_prompt,
+         hotwords=hotwords
      )
```

### Phase 2: Enhancement (Strategy 3 - Hybrid)

**Estimated Time**: 4-6 hours  
**Files to Modify**: 3  
**Risk**: Medium

1. Implement hybrid approach with global hotwords
2. Add config option for prompt strategy
3. Comprehensive testing
4. A/B comparison with Phase 1

### Phase 3: Advanced (Strategy 2 - Chunked)

**Estimated Time**: 1-2 days  
**Files to Modify**: 5+  
**Risk**: High

1. Implement chunk processing
2. Implement segment merging logic
3. Handle edge cases (overlaps, gaps)
4. Performance optimization
5. Extensive testing

## Configuration

Add to `config/.env.pipeline`:

```bash
# Bias prompting strategy
BIAS_STRATEGY=hybrid              # Options: global, chunked, hybrid
BIAS_PROMPT_MAX_TERMS=50         # Max terms for global prompt
BIAS_HOTWORD_MAX_TERMS=50        # Max terms for hotwords
BIAS_USE_INITIAL_PROMPT=true    # Enable initial_prompt
BIAS_USE_HOTWORDS=true           # Enable hotwords parameter
```

## Testing Strategy

### 1. Baseline Measurement
Run current system (no bias) on test video:
```bash
./run_pipeline.sh --job test-001
# Measure accuracy of proper noun recognition
```

### 2. Phase 1 Test
Enable global bias prompting:
```bash
# In code, implement Phase 1 changes
./run_pipeline.sh --job test-002
# Compare accuracy improvement
```

### 3. Metrics to Track
- **Name Recognition Rate**: % of cast/crew names correctly transcribed
- **Accuracy**: Word Error Rate (WER) on names
- **Speed**: Transcription time (should be same as baseline)
- **Quality**: Manual review of 100 random segments

### 4. Success Criteria
✅ >20% improvement in name recognition  
✅ No degradation in overall WER  
✅ <5% increase in processing time  

## Expected Impact

### Before (Current)
```json
{
  "text": "शाहरुख़ was amazing in this movie",
  "translation": "Sharukh was amazing in this movie"
}
```

### After (With Bias)
```json
{
  "text": "शाहरुख़ खान was amazing in this movie",
  "translation": "Shah Rukh Khan was amazing in this movie",
  "bias_terms": ["Shah Rukh Khan", "Kajol", ...]
}
```

**Expected Improvements**:
- Names: "शाहरुख़" → "Shah Rukh Khan" (full name instead of partial)
- Locations: "पंजाब" → "Punjab" (correct transliteration)
- Character names: Consistent spelling across subtitles

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Too many terms** | Dilutes focus, poor recognition | Limit to top 50 terms |
| **Wrong terms** | Misleads Whisper | Filter by confidence, validate sources |
| **Performance hit** | Slower transcription | Use global strategy, not chunked |
| **No improvement** | Wasted effort | Test on small sample first |
| **Regression** | Worse than no bias | Keep fallback to no-bias option |

## Rollback Plan

If bias implementation causes issues:

1. **Quick Disable**: Set `BIAS_STRATEGY=none` in config
2. **Code Rollback**: Remove `initial_prompt` and `hotwords` parameters
3. **Fallback**: System continues working as before (metadata only)

## Monitoring

After deployment, monitor:

```bash
# Check bias usage in logs
grep "Using.*bias terms" out/*/logs/07_asr_*.log

# Verify hotwords applied
grep "hotwords" out/*/logs/07_asr_*.log

# Compare name accuracy
# Manual spot checks on random samples
```

## Recommendation

**Start with Phase 1 (Global Prompt Strategy)**:

✅ Fastest to implement (2-3 hours)  
✅ Lowest risk  
✅ Should provide 20-30% improvement  
✅ Easy to rollback if issues  
✅ Foundation for later enhancements  

Then measure results before deciding on Phase 2 or 3.

---

**Document Version**: 1.0  
**Date**: 2025-11-13  
**Status**: Ready for implementation  
**Recommended**: Phase 1 (Global Prompt Strategy)
