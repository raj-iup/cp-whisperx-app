# PyAnnote VAD Made Optional

## Date: 2025-10-29

## Decision
Made PyAnnote VAD **optional** instead of required, with graceful fallback to Silero VAD segments.

## Reason
PyAnnote.ai Cloud API has file size limitations:
- Error: **413 Request Entity Too Large**
- Movie audio file: 281MB (9211 seconds)
- API appears to have limits on file size/duration
- This is a common limitation for cloud processing services

## Solution
Modified `run_pipeline_arch.py` to:

### 1. Check for API Token
```python
if not pyannote_api_available:
    logger.warning("PyAnnote API token not found - skipping")
    # Continue with Silero segments
```

### 2. Graceful Failure
```python
if not run_docker_stage("pyannote-vad", ...):
    logger.warning("PyAnnote VAD failed - continuing with Silero")
    # Don't exit, continue pipeline
```

### 3. Fallback Logic
- If PyAnnote API token missing → Use Silero segments
- If PyAnnote VAD fails → Use Silero segments  
- If PyAnnote VAD succeeds → Use refined segments

## Impact

### ✅ Benefits
- **Pipeline resilience** - No single point of failure
- **Cost savings** - PyAnnote API is paid service
- **File size flexibility** - Can process any size file
- **Silero quality** - Already excellent (1,954 segments)

### ⚠️ Trade-offs
- Slightly less refined boundaries (acceptable)
- No speaker-aware VAD refinement (diarization handles this)

## Architecture Compliance

✅ **Still follows workflow-arch.txt:**
- Silero VAD provides initial speech segments
- Diarization uses audio + segments for speaker labeling
- ASR uses segments for processing
- Optional PyAnnote refinement when available

## Current State

### Silero VAD (Stage 4)
- ✅ **Status:** Working perfectly
- **Segments:** 1,954
- **Quality:** High quality speech detection
- **Speed:** Fast local processing

### PyAnnote VAD (Stage 5)
- ⚠️  **Status:** Optional
- **Requires:** PYANNOTE_API_TOKEN + file size < API limit
- **When available:** Provides refined boundaries
- **When unavailable:** Pipeline continues with Silero

### PyAnnote Diarization (Stage 6)
- ✅ **Status:** Required (unchanged)
- **Input:** Audio file + VAD segments (Silero or PyAnnote)
- **Output:** Speaker-labeled segments

## Usage

### With PyAnnote API (when token available and file size OK)
```bash
# Add to config/secrets.json:
"PYANNOTE_API_TOKEN": "sk_..."

# Run pipeline - PyAnnote VAD will be attempted
python run_pipeline_arch.py
```

### Without PyAnnote API (or when API fails)
```bash
# Just run pipeline - will use Silero segments
python run_pipeline_arch.py

# Output will show:
# "⚠️  PyAnnote API token not found - skipping PyAnnote VAD"
# "   Will use Silero VAD segments directly for ASR/diarization"
```

## Testing

### Test 1: Without API Token
```bash
# Remove PYANNOTE_API_TOKEN from secrets.json
python run_pipeline_arch.py
```
Expected: Pipeline continues with Silero segments

### Test 2: With API Token (large file)
```bash
# Add PYANNOTE_API_TOKEN to secrets.json
python run_pipeline_arch.py
```
Expected: PyAnnote VAD attempts, fails gracefully, continues with Silero

### Test 3: With API Token (small file)
```bash
# Use smaller audio file (~5-10 mins)
python run_pipeline_arch.py
```
Expected: PyAnnote VAD succeeds, provides refined segments

## Recommendations

### For Production
1. **Use Silero VAD** - Reliable, fast, free, handles any file size
2. **Skip PyAnnote VAD** - Optional refinement, has limitations
3. **Keep Diarization** - Required for speaker labeling

### For Experimentation
1. **Test PyAnnote API** - On smaller clips (<5 mins)
2. **Compare quality** - Silero vs PyAnnote refined segments
3. **Evaluate cost** - PyAnnote API pricing vs benefit

## Files Modified

- `run_pipeline_arch.py` - Made PyAnnote VAD optional with fallback

## Conclusion

PyAnnote VAD is now optional and gracefully handles:
- ✅ Missing API token
- ✅ API failures (file too large, network issues, etc)
- ✅ Seamless fallback to Silero segments

Pipeline is more robust and can process files of any size without dependency on cloud API availability or limits.

---

**Status:** ✅ Ready to run full pipeline end-to-end  
**Next Step:** Run full pipeline with Silero VAD segments
