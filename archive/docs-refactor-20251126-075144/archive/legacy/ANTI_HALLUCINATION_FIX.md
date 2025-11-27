# Anti-Hallucination Fix - 2025-11-21

## Problem Identified

Transcript showed clear hallucination symptoms:
- **Repeated phrase**: "प्रश्न प्रश्न" (question question) for all 11 segments
- **Empty word arrays**: No word-level alignment
- **Uniform timestamps**: 30-second intervals (0-30, 30-60, etc.)
- **VAD mismatch**: VAD detected 22 actual speech segments, but transcript only has 11 repeated entries

### Root Cause
The model was stuck in a hallucination loop, likely due to:
1. `condition_on_previous_text=True` (default) causing repetition amplification
2. No filtering of low-confidence outputs
3. Insufficient non-speech detection thresholds
4. Audio segment may contain mostly music/background noise

## Solution Implemented

### 1. **Anti-Hallucination Parameters Added**

Updated both WhisperX and MLX backends with these critical parameters:

```python
# Default anti-hallucination settings
condition_on_previous_text = False     # Prevents hallucination loops
logprob_threshold = -1.0               # Filters low-confidence outputs
no_speech_threshold = 0.6              # Better non-speech detection
compression_ratio_threshold = 2.4      # Detects repetitive text
```

### 2. **Parameter Descriptions**

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `condition_on_previous_text` | `False` | **Most Critical**: Prevents model from conditioning on previous hallucinated text, breaking the repetition loop |
| `logprob_threshold` | `-1.0` | Filters segments with log probability below threshold (unreliable transcriptions) |
| `no_speech_threshold` | `0.6` | Probability threshold for detecting non-speech (music, noise, silence) |
| `compression_ratio_threshold` | `2.4` | Detects highly repetitive text patterns typical of hallucinations |

### 3. **Code Changes**

#### Files Modified:
1. **`scripts/whisper_backends.py`**
   - Added anti-hallucination parameters to `WhisperXBackend.__init__`
   - Added anti-hallucination parameters to `MLXWhisperBackend.__init__`
   - Updated `MLXWhisperBackend.transcribe()` to pass parameters to mlx-whisper
   - Updated `create_backend()` factory to accept and pass parameters
   - Added parameter logging on model load

2. **`scripts/whisperx_integration.py`**
   - Changed default `condition_on_previous_text=False` (was True)
   - Updated `WhisperXProcessor.load_model()` to pass parameters to backend

### 4. **How It Works**

**Before (Hallucination Mode):**
```
Segment 1: "प्रश्न प्रश्न" 
↓ (condition_on_previous_text=True)
Segment 2: "प्रश्न प्रश्न" (reinforced by previous)
↓ (keeps repeating)
Segment 3: "प्रश्न प्रश्न" (stuck in loop)
```

**After (Anti-Hallucination Mode):**
```
Segment 1: transcribed independently
↓ (condition_on_previous_text=False)
Segment 2: transcribed independently (no context bleed)
↓ (each segment fresh)
Segment 3: transcribed independently
```

Additionally:
- Low confidence outputs filtered by `logprob_threshold`
- Non-speech sections detected by `no_speech_threshold`
- Repetitive patterns caught by `compression_ratio_threshold`

## Usage

### Automatic (Recommended)
The anti-hallucination settings are now **enabled by default** for all transcriptions. No configuration needed.

### Manual Override (if needed)
If you need to adjust parameters for specific use cases:

```python
processor = WhisperXProcessor(
    model_name="large-v3",
    device="mps",
    condition_on_previous_text=False,  # Keep False for anti-hallucination
    logprob_threshold=-1.0,            # Lower = more strict filtering
    no_speech_threshold=0.6,            # Higher = more aggressive non-speech detection
    compression_ratio_threshold=2.4     # Lower = catch repetition earlier
)
```

## Testing

### Before Re-running Failed Job:
The job that produced the hallucinated transcript was:
- **Job ID**: `job-20251121-rpatel-0004`
- **Media**: Jaane Tu Ya Jaane Na 2008 (clip: 01:30-05:30)
- **Language**: Hindi (hi)
- **Model**: large-v3 (MLX backend)

### To Re-test:
```bash
# Re-run the same job with new anti-hallucination settings
./run-pipeline.sh

# Or start fresh with same clip
./prepare-job.sh --media "Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:01:30" --end "00:05:30" \
                 --source-lang hi --target-langs en,gu
```

### Expected Improvements:
1. **Diverse text**: Each segment should have different, contextually appropriate text
2. **Word-level timestamps**: Non-empty `words` arrays in segments
3. **Variable segment lengths**: Not uniform 30-second blocks
4. **Proper silence handling**: Empty segments for non-speech instead of repeated text

## Additional Recommendations

### 1. **Try Different Time Range**
If the 1:30-5:30 clip still has issues, it might contain:
- Opening credits with minimal dialogue
- Background music dominating speech
- No clear speech at all

**Recommendation**: Try a scene with active dialogue, e.g.:
```bash
# Look for a scene with conversation
./prepare-job.sh --media "Jaane Tu Ya Jaane Na 2008.mp4" \
                 --start "00:15:00" --end "00:18:00"
```

### 2. **Check Audio Quality**
```bash
# Extract and listen to the audio clip
ffmpeg -i "in/Jaane Tu Ya Jaane Na 2008.mp4" \
       -ss 00:01:30 -to 00:05:30 \
       -vn test_audio.wav
       
# Play and verify there's actual clear dialogue
```

### 3. **VAD Analysis**
Review the VAD output to see where speech is actually detected:
```bash
cat out/2025/11/21/rpatel/4/vad/speech_segments.json | jq '.segments'
```

If VAD shows sparse segments (like 22 small segments over 4 minutes), it indicates:
- Mostly non-speech content (music, silence)
- Speech is intermittent
- May need different scene selection

## Technical Details

### MLX-Whisper Parameter Support
The MLX-Whisper backend supports these parameters natively:
- ✅ `condition_on_previous_text`
- ✅ `logprob_threshold`
- ✅ `no_speech_threshold`
- ✅ `compression_ratio_threshold`

### WhisperX (CTranslate2) Parameter Support
WhisperX has limited parameter support through the CTranslate2 backend. If parameters are not supported, they will be gracefully ignored with a warning.

## Monitoring

After re-running transcription, check these indicators:

### 1. **Log Output**
Look for anti-hallucination parameter confirmation:
```
[INFO] Anti-hallucination settings:
[INFO]   condition_on_previous_text: False
[INFO]   logprob_threshold: -1.0
[INFO]   no_speech_threshold: 0.6
[INFO]   compression_ratio_threshold: 2.4
```

### 2. **Segment Diversity**
```bash
# Check for unique text in segments
jq -r '.segments[].text' out/*/transcripts/segments.json | sort | uniq -c

# Should show diverse text, not repeated phrases
```

### 3. **Word-Level Timestamps**
```bash
# Check if words array is populated
jq '.segments[0].words | length' out/*/transcripts/segments.json

# Should be > 0
```

## References

- **Issue**: Transcript showing hallucination (repeated "प्रश्न प्रश्न")
- **Fix**: Anti-hallucination parameters in Whisper backends
- **Date**: 2025-11-21
- **Affected Backends**: MLX-Whisper, WhisperX (CTranslate2)

## Next Steps

1. ✅ Anti-hallucination parameters implemented
2. ⏳ Re-run failed job to verify improvement
3. ⏳ Test with different time ranges if needed
4. ⏳ Document any additional edge cases

---

**Status**: ✅ IMPLEMENTED - Ready for testing
